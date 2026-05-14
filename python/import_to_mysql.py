"""MySQL data import + Power BI data export"""
import csv
import io
import subprocess
import sys
from pathlib import Path
import pandas as pd
from sqlalchemy import create_engine, text
from python.config import MYSQL_CONFIG, PROJECT_ROOT, OUTPUT_DIR, DATA_DIR, logger

POWERBI_DIR = PROJECT_ROOT / 'powerbi' / 'data'
SQL_DIR = PROJECT_ROOT / 'sql'

CONTAINER = MYSQL_CONFIG['container']
DB = MYSQL_CONFIG['database']


def _mysql_base_args() -> list:
    return [
        'docker', 'exec', '-i', CONTAINER, 'mysql',
        '-h', MYSQL_CONFIG['host'],
        '-u', MYSQL_CONFIG['user'],
        f"-p{MYSQL_CONFIG['password']}",
        '--default-character-set=utf8mb4',
    ]


def _run_mysql(description: str, sql_file: Path = None, query: str = None):
    args = _mysql_base_args()
    args.append(DB)
    print(f"  {description}...", end=' ')
    if sql_file:
        with open(sql_file, 'r', encoding='utf-8') as f:
            result = subprocess.run(args, stdin=f, capture_output=True,
                                    text=True, encoding='utf-8', errors='replace')
    elif query:
        result = subprocess.run(args, input=query, capture_output=True,
                                text=True, encoding='utf-8', errors='replace')
    else:
        raise ValueError("Must provide sql_file or query")
    if result.returncode != 0:
        print(f"FAILED\n    {result.stderr.strip()}")
    else:
        print("OK")
    return result


def _get_engine():
    pw = MYSQL_CONFIG['password']
    encoded_pw = pw.replace('@', '%40').replace(':', '%3A').replace('/', '%2F')
    url = (f"mysql+pymysql://{MYSQL_CONFIG['user']}:{encoded_pw}"
           f"@{MYSQL_CONFIG['host']}:{MYSQL_CONFIG['port']}/{DB}"
           f"?charset=utf8mb4")
    return create_engine(url)


def step1_create_tables() -> bool:
    """Create database tables (skip LOAD DATA)"""
    print("\n[1/5] Create tables...")
    result = _run_mysql('01_setup_database', sql_file=SQL_DIR / '01_setup_database.sql')
    return result.returncode == 0


def step2_load_csv_via_pandas() -> bool:
    """Load CSV directly into MySQL using pandas + sqlalchemy"""
    print("\n[2/5] Load CSV data via pandas...")
    csv_path = DATA_DIR / 'customer_journey.csv'
    if not csv_path.exists():
        print(f"  SKIP: {csv_path} not found")
        return False

    try:
        df = pd.read_csv(csv_path)
        # Rename Timestamp to EventTime for MySQL compatibility
        df = df.rename(columns={'Timestamp': 'EventTime'})
        df['EventTime'] = pd.to_datetime(df['EventTime'])

        engine = _get_engine()
        df.to_sql('user_behavior', engine, if_exists='replace', index=False,
                  method='multi', chunksize=1000)

        with engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM user_behavior"))
            count = result.scalar()
        print(f"  OK: {count:,} records loaded")

        # Grant SELECT so subsequent temp table scripts work
        engine.dispose()
        return True
    except Exception as e:
        print(f"FAILED: {e}")
        return False


def step3_run_analysis_sql() -> bool:
    """Execute analysis SQL scripts (skip load data)"""
    print("\n[3/5] Execute analysis SQL scripts...")
    scripts = [
        '03_funnel_wide.sql', '04_funnel_overview.sql',
        '05_multi_dimension.sql', '06_churn_diagnostics.sql',
        '07_statistical_comparison.sql', '08_operational_export.sql',
    ]
    for script in scripts:
        sql_file = SQL_DIR / script
        if not sql_file.exists():
            print(f"  SKIP: {script} not found")
            continue
        result = _run_mysql(script, sql_file=sql_file)
        if result.returncode != 0:
            return False
    return True


def step4_verify_data() -> bool:
    """Verify MySQL tables after import"""
    print("\n[4/5] Verify data...")
    queries = {
        'user_behavior records': 'SELECT COUNT(*) FROM user_behavior',
        'funnel_wide sessions': 'SELECT COUNT(*) FROM funnel_wide',
        'funnel_wide steps': 'SELECT SUM(step1_home), SUM(step2_product), SUM(step3_cart), SUM(step4_checkout), SUM(step5_confirm) FROM funnel_wide',
    }
    for desc, query in queries.items():
        result = _run_mysql(desc, query=query)
        if result.returncode != 0:
            return False
    return True


def step5_export_powerbi() -> None:
    """Export Power BI CSV files from MySQL"""
    print("\n[5/5] Export Power BI data...")
    POWERBI_DIR.mkdir(parents=True, exist_ok=True)

    queries = {
        'funnel_overview.csv':
            "SELECT step1_home, step2_product, step3_cart, step4_checkout, step5_confirm, is_purchased FROM funnel_wide",
        'channel_analysis.csv':
            "SELECT ReferralSource, COUNT(*) AS sessions, SUM(is_purchased) AS converted, "
            "ROUND(SUM(is_purchased)*100.0/COUNT(*),2) AS conversion_rate FROM funnel_wide "
            "GROUP BY ReferralSource",
        'device_analysis.csv':
            "SELECT DeviceType, COUNT(*) AS sessions, SUM(is_purchased) AS converted, "
            "ROUND(SUM(is_purchased)*100.0/COUNT(*),2) AS conversion_rate FROM funnel_wide "
            "GROUP BY DeviceType",
        'country_analysis.csv':
            "SELECT Country, COUNT(*) AS sessions, SUM(is_purchased) AS converted, "
            "ROUND(SUM(is_purchased)*100.0/COUNT(*),2) AS conversion_rate FROM funnel_wide "
            "GROUP BY Country ORDER BY conversion_rate DESC",
        'funnel_wide_export.csv':
            "SELECT * FROM funnel_wide",
    }

    for filename, query in queries.items():
        output_file = POWERBI_DIR / filename
        args = _mysql_base_args()
        args.extend(['--batch', '--raw', DB, '-e', query])
        result = subprocess.run(args, capture_output=True, text=True,
                                encoding='utf-8', errors='replace')
        if result.returncode != 0 or not result.stdout:
            print(f"  {filename}: FAILED - {result.stderr.strip()}")
            continue
        reader = csv.reader(io.StringIO(result.stdout), delimiter='\t')
        with open(output_file, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            for row in reader:
                writer.writerow(row)
        with open(output_file, 'r', encoding='utf-8') as f:
            lines = sum(1 for _ in f) - 1
        print(f"  {filename}: {lines} rows")

    print(f"\nPower BI data exported to: {POWERBI_DIR}")


def main() -> None:
    print("=" * 60)
    print("MySQL Import & Power BI Export")
    print("=" * 60)

    if not MYSQL_CONFIG['password']:
        print("\n[ERROR] MYSQL_PASSWORD not set. Please create .env file.")
        sys.exit(1)

    result = subprocess.run(
        ['docker', 'ps', '--filter', f'name={CONTAINER}', '--format', '{{.Names}}'],
        capture_output=True, text=True,
    )
    if CONTAINER not in result.stdout:
        print(f"\n[ERROR] Container {CONTAINER} not running.")
        sys.exit(1)
    print(f"Container {CONTAINER} is running")

    if not step1_create_tables():
        print("\n[ABORT] Table creation failed")
        sys.exit(1)
    if not step2_load_csv_via_pandas():
        print("\n[ABORT] CSV load failed")
        sys.exit(1)
    if not step3_run_analysis_sql():
        print("\n[ABORT] SQL analysis failed")
        sys.exit(1)
    step4_verify_data()
    step5_export_powerbi()
    print("\nDone!")


if __name__ == '__main__':
    main()
