"""MySQL 数据导入 + Power BI 数据导出"""
import csv
import io
import subprocess
import sys
from pathlib import Path
from python.config import MYSQL_CONFIG, PROJECT_ROOT, OUTPUT_DIR, logger

DATA_DIR = PROJECT_ROOT / 'data'
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
        '--local-infile=1',
    ]


def _run_docker_cp(local_path: str, container_path: str) -> bool:
    result = subprocess.run(
        ['docker', 'cp', str(local_path), f'{CONTAINER}:{container_path}'],
        capture_output=True, text=True, encoding='utf-8', errors='replace',
    )
    return result.returncode == 0


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


def step1_copy_csv() -> bool:
    print("\n[1/3] Copy CSV to container...")
    files = [
        (DATA_DIR / 'customer_journey.csv', '/var/lib/mysql/upload/customer_journey.csv'),
    ]
    for host_path, container_path in files:
        if not host_path.exists():
            print(f"  SKIP: {host_path.name} not found")
            continue
        if not _run_docker_cp(str(host_path), container_path):
            print(f"  FAILED: {host_path.name}")
            return False
        print(f"  OK: {host_path.name}")
    return True


def step2_run_sql() -> bool:
    print("\n[2/3] Execute SQL scripts...")
    scripts = [
        '01_setup_database.sql', '02_load_data.sql',
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


def step3_export_powerbi() -> None:
    print("\n[3/3] Export Power BI data...")
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
            print(f"  {filename}: FAILED")
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

    if not step1_copy_csv():
        print("\n[ABORT] CSV copy failed")
        sys.exit(1)
    if not step2_run_sql():
        print("\n[ABORT] SQL execution failed")
        sys.exit(1)
    step3_export_powerbi()
    print("\nDone!")


if __name__ == '__main__':
    main()
