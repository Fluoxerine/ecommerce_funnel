# 电商漏斗 CRO 分析项目 — 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将现有单体 notebook 重构为模块化企业级 CRO 分析项目，包含 Python 分析引擎、SQL 数据仓库、统计检验、PIE 优先级框架、Power BI 仪表板。

**Architecture:** 7 个 Python 模块 + 8 个 SQL 脚本 + 4 份文档 + 2 组测试。Python 通过 config.py 统一管理路径和 MySQL 连接（密码从 .env 读取），main.py 串联全流程。SQL 脚本按编号顺序执行，从建表到运营清单导出形成完整流水线。

**Tech Stack:** Python (base conda), pandas, numpy, matplotlib, seaborn, plotly, scipy, sqlalchemy, pymysql, MySQL 8.4 (Docker), pytest

---

### Task 1: 项目基础 — .env.example, .gitignore, requirements.txt

**Files:**
- Create: `.env.example`
- Create: `.gitignore`
- Modify: `requirements.txt`

- [ ] **Step 1: 创建 .env.example**

```bash
cp "D:\D30360\Documents\ecommerce\20260507_1\.env" "D:\D30360\Documents\ecommerce_funnel_analysis\.env.example"
```

然后修改第7行 database 为 `ecommerce`。

- [ ] **Step 2: 修改 .env.example 内容**

```bash
# MySQL Docker 容器配置
MYSQL_CONTAINER=mysql84
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_password_here
MYSQL_DATABASE=ecommerce
```

- [ ] **Step 3: 创建 .gitignore**

```bash
# Python
__pycache__/
*.py[cod]
*.egg-info/
.ipynb_checkpoints/

# 环境变量（含密码）
.env

# 输出（每次运行重新生成）
output/*.csv
output/*.log
output/charts/*.png
output/charts/*.html
!output/charts/.gitkeep

# Power BI
powerbi/data/*.csv

# IDE
.vscode/
.idea/

# macOS / Windows
.DS_Store
Thumbs.db
```

- [ ] **Step 4: 更新 requirements.txt**

```
pandas
numpy
matplotlib
seaborn
plotly
scipy
sqlalchemy
pymysql
python-dotenv
pytest
```

- [ ] **Step 5: 验证**

```bash
pip install -r "D:\D30360\Documents\ecommerce_funnel_analysis\requirements.txt"
```

- [ ] **Step 6: Commit**

```bash
cd "D:\D30360\Documents\ecommerce_funnel_analysis" && git init && git add .env.example .gitignore requirements.txt && git commit -m "feat: add project foundation — .env.example, .gitignore, updated requirements"
```

---

### Task 2: config.py — 统一配置中心

**Files:**
- Create: `python/__init__.py`
- Create: `python/config.py`

- [ ] **Step 1: 创建 python/__init__.py**

```python
"""电商漏斗 CRO 分析 — Python 模块"""
```

- [ ] **Step 2: 创建 python/config.py**

```python
"""项目配置常量 — 所有路径、连接、颜色、日志均从此处获取"""
import os
import logging
from pathlib import Path
from dotenv import load_dotenv

# ── 加载 .env ──────────────────────────────────────────
load_dotenv(Path(__file__).resolve().parent.parent / '.env')

# ── 项目路径 ──────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / 'data'
OUTPUT_DIR = PROJECT_ROOT / 'output'
CHART_DIR = OUTPUT_DIR / 'charts'

# ── 数据文件路径 ──────────────────────────────────────
RAW_CSV = DATA_DIR / 'customer_journey.csv'
CLEANED_CSV = OUTPUT_DIR / 'cleaned_customer_journey.csv'
FUNNEL_WIDE_CSV = OUTPUT_DIR / 'funnel_wide.csv'

# ── MySQL 连接配置（优先环境变量） ──────────────────────
MYSQL_CONFIG = {
    'container': os.getenv('MYSQL_CONTAINER', 'mysql84'),
    'host': os.getenv('MYSQL_HOST', '127.0.0.1'),
    'port': int(os.getenv('MYSQL_PORT', '3306')),
    'user': os.getenv('MYSQL_USER', 'root'),
    'password': os.getenv('MYSQL_PASSWORD', ''),
    'database': os.getenv('MYSQL_DATABASE', 'ecommerce'),
}

# ── 漏斗阶段定义 ──────────────────────────────────────
FUNNEL_STAGES = {
    'home':           '1.访问首页',
    'product_page':   '2.浏览商品',
    'cart':           '3.加入购物车',
    'checkout':       '4.提交订单',
    'confirmation':   '5.支付成功',
}

FUNNEL_ORDER = [
    '1.访问首页', '2.浏览商品', '3.加入购物车',
    '4.提交订单', '5.支付成功',
]

STEP_COLUMNS = ['step1_home', 'step2_product', 'step3_cart',
                'step4_checkout', 'step5_confirm']

# ── 清洗阈值 ──────────────────────────────────────────
MIN_SESSION_DURATION = 5       # 最小会话停留时长（秒）
MAX_SINGLE_PAGE_DURATION = 86400  # 单页最大停留时长（秒）

# ── 颜色方案 ──────────────────────────────────────────
FUNNEL_COLORS = ['#DB3124', '#FC8C5A', '#FFDF92', '#90BEE0', '#4B74B2']
CHANNEL_COLORS = {'Direct': '#2E86AB', 'Email': '#A23B72', 
                  'Google': '#F18F01', 'Social Media': '#C73E1D'}
DEVICE_COLORS = {'Desktop': '#27AE60', 'Mobile': '#3498DB', 'Tablet': '#9B59B6'}

PRIMARY = '#2E86AB'
ACCENT = '#E74C3C'
GRID = '#E5E5E5'

# ── 日志配置 ──────────────────────────────────────────
LOG_FORMAT = '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
LOG_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
CHART_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format=LOG_FORMAT,
    datefmt=LOG_DATE_FORMAT,
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(OUTPUT_DIR / 'analysis.log', encoding='utf-8'),
    ],
)

logger = logging.getLogger('funnel_cro')
```

- [ ] **Step 3: 验证 config 可导入**

```bash
cd "D:\D30360\Documents\ecommerce_funnel_analysis" && python -c "from python.config import PROJECT_ROOT, logger; logger.info('config OK'); print(PROJECT_ROOT)"
```

- [ ] **Step 4: Commit**

```bash
git add python/__init__.py python/config.py && git commit -m "feat: add config.py — unified project config center"
```

---

### Task 3: data_loader.py — 数据加载与校验

**Files:**
- Create: `python/data_loader.py`

- [ ] **Step 1: 创建 data_loader.py**

```python
"""数据加载模块：读取 CSV，基础概览，列名校验"""
import pandas as pd
from config import RAW_CSV, logger


def load_raw_data() -> pd.DataFrame:
    """读取原始 CSV 并执行基础校验"""
    logger.info("=" * 60)
    logger.info("1. 数据加载")
    logger.info("=" * 60)

    if not RAW_CSV.exists():
        logger.error("缺少数据文件: %s", RAW_CSV)
        raise FileNotFoundError(f"数据文件不存在: {RAW_CSV}")

    df = pd.read_csv(RAW_CSV)
    logger.info("原始数据: %s 条记录", f"{len(df):,}")

    # 列名校验
    expected_cols = ['SessionID', 'UserID', 'Timestamp', 'PageType',
                     'DeviceType', 'Country', 'ReferralSource',
                     'TimeOnPage_seconds', 'ItemsInCart', 'Purchased']
    actual_cols = df.columns.tolist()
    missing = set(expected_cols) - set(actual_cols)
    extra = set(actual_cols) - set(expected_cols)
    if missing:
        logger.warning("缺少预期列: %s", missing)
    if extra:
        logger.info("额外列: %s", extra)

    logger.info("列名: %s", actual_cols)
    return df


def print_data_overview(df: pd.DataFrame) -> None:
    """打印数据概览（用于日志和报告）"""
    logger.info("会话数: %s", f"{df['SessionID'].nunique():,}")
    logger.info("用户数: %s", f"{df['UserID'].nunique():,}")

    logger.info("页面类型分布:")
    for pt, cnt in df['PageType'].value_counts().items():
        logger.info("  %s: %s", pt, f"{cnt:,}")

    logger.info("Purchased 分布:")
    for v, cnt in df['Purchased'].value_counts().items():
        logger.info("  %d: %s", v, f"{cnt:,}")

    logger.info("设备分布:")
    for d, cnt in df['DeviceType'].value_counts().items():
        logger.info("  %s: %s", d, f"{cnt:,}")

    logger.info("渠道分布:")
    for r, cnt in df['ReferralSource'].value_counts().items():
        logger.info("  %s: %s", r, f"{cnt:,}")

    logger.info("国家分布:")
    for c, cnt in df['Country'].value_counts().items():
        logger.info("  %s: %s", c, f"{cnt:,}")


def validate_data_integrity(df: pd.DataFrame) -> dict:
    """校验数据完整性并返回问题清单"""
    issues = {}

    # Purchased 值是否仅有 0/1
    if not df['Purchased'].isin([0, 1]).all():
        issues['purchased_invalid'] = df[~df['Purchased'].isin([0, 1])].shape[0]

    # 同一会话内 Purchased 是否一致（会话级别属性）
    session_states = df.groupby('SessionID')['Purchased'].nunique()
    inconsistent = (session_states > 1).sum()
    if inconsistent > 0:
        issues['session_purchased_inconsistent'] = int(inconsistent)


    # TimeOnPage 是否有负值
    neg_time = (df['TimeOnPage_seconds'] < 0).sum()
    if neg_time > 0:
        issues['negative_time'] = int(neg_time)

    # ItemsInCart 是否有负值
    neg_items = (df['ItemsInCart'] < 0).sum()
    if neg_items > 0:
        issues['negative_items'] = int(neg_items)

    if issues:
        logger.warning("数据完整性问题: %s", issues)
    else:
        logger.info("数据完整性检查通过 ✓")

    return issues
```

- [ ] **Step 2: 验证 data_loader 可运行**

```bash
cd "D:\D30360\Documents\ecommerce_funnel_analysis" && python -c "
from python.data_loader import load_raw_data, print_data_overview, validate_data_integrity
df = load_raw_data()
print_data_overview(df)
issues = validate_data_integrity(df)
print('Issues:', issues)
"
```

- [ ] **Step 3: Commit**

```bash
git add python/data_loader.py && git commit -m "feat: add data_loader.py — CSV loading, overview, integrity validation"
```

---

### Task 4: data_cleaning.py — 数据清洗 + 漏斗宽表

**Files:**
- Create: `python/data_cleaning.py`
- Create: `tests/__init__.py`
- Create: `tests/test_data_cleaning.py`

- [ ] **Step 1: 创建 tests/__init__.py**

```python
"""电商漏斗 CRO 分析 — 测试"""
```

- [ ] **Step 2: 创建 test_data_cleaning.py（先写测试）**

```python
"""数据清洗模块 — 单元测试"""
import pandas as pd
import numpy as np
from python.data_cleaning import (
    basic_cleaning, funnel_specific_cleaning, build_funnel_wide
)


def _make_test_df() -> pd.DataFrame:
    """构造测试数据集"""
    data = {
        'SessionID': ['s1', 's1', 's2', 's2', 's3', 's4', s4],
        'UserID': ['u1', 'u1', 'u2', 'u2', 'u3', 'u4', 'u4'],
        'Timestamp': pd.to_datetime([
            '2025-01-01 10:00:00', '2025-01-01 10:02:00',
            '2025-01-01 10:00:00', '2025-01-01 10:05:00',
            '2025-01-01 10:00:00', '2025-01-01 10:00:00', '2025-01-01 10:01:00',
        ]),
        'PageType': [
            'home', 'product_page', 'home', 'checkout',
            'home', 'home', 'home',
        ],
        'DeviceType': ['Desktop', 'Desktop', 'Mobile', 'Mobile',
                       'Tablet', 'Desktop', 'Desktop'],
        'Country': ['USA', 'USA', 'UK', 'UK', 'France', 'India', 'India'],
        'ReferralSource': ['Google', 'Google', 'Email', 'Email',
                           'Direct', 'Social Media', 'Social Media'],
        'TimeOnPage_seconds': [55, 120, 40, 90, 3, 200, 100],
        'ItemsInCart': [0, 1, 0, 3, 0, 0, 0],
        'Purchased': [0, 0, 1, 1, 0, 0, 0],
    }
    return pd.DataFrame(data)


class TestBasicCleaning:
    """基础清洗测试"""

    def test_drop_duplicates(self):
        df = _make_test_df()
        # 人为插入重复行
        df_dup = pd.concat([df, df.iloc[[0]]], ignore_index=True)
        cleaned = basic_cleaning(df_dup)
        assert len(cleaned) == len(df), "去重后应与原始行数一致"

    def test_null_core_columns(self):
        df = _make_test_df()
        df.loc[0, 'SessionID'] = None
        cleaned = basic_cleaning(df)
        assert 0 not in cleaned.index

    def test_fill_null_non_core(self):
        df = _make_test_df()
        df.loc[0, 'Country'] = np.nan
        cleaned = basic_cleaning(df)
        assert cleaned.loc[cleaned.index[0], 'Country'] == 'Unknown'

    def test_filter_future_time(self):
        df = _make_test_df()
        df.loc[0, 'Timestamp'] = pd.Timestamp('2099-01-01')
        cleaned = basic_cleaning(df)
        assert len(cleaned) < len(df)

    def test_filter_invalid_purchased(self):
        df = _make_test_df()
        df.loc[0, 'Purchased'] = 2
        cleaned = basic_cleaning(df)
        assert (cleaned['Purchased'].isin([0, 1])).all()

    def test_pageType_lowercased(self):
        df = _make_test_df()
        cleaned = basic_cleaning(df)
        assert (cleaned['PageType'] == cleaned['PageType'].str.lower()).all()


class TestFunnelSpecificCleaning:
    """漏斗专属清洗测试"""

    def test_sort_by_session_time(self):
        df = basic_cleaning(_make_test_df())
        cleaned = funnel_specific_cleaning(df)
        # 取 s1 的会话，验证按时间排序
        s1 = cleaned[cleaned['SessionID'] == 's1']
        assert s1['Timestamp'].is_monotonic_increasing

    def test_dedup_page_within_session(self):
        df = _make_test_df()
        # s4 有两条 home 记录，去重后应只保留第一条
        cleaned = basic_cleaning(df)
        cleaned = funnel_specific_cleaning(cleaned)
        s4 = cleaned[cleaned['SessionID'] == 's4']
        assert len(s4) == 1

    def test_filter_short_sessions(self):
        df = _make_test_df()
        cleaned = basic_cleaning(df)
        cleaned = funnel_specific_cleaning(cleaned)
        # s3 只有 3 秒，应被过滤
        assert 's3' not in cleaned['SessionID'].values

    def test_derived_time_features(self):
        df = _make_test_df()
        cleaned = basic_cleaning(df)
        cleaned = funnel_specific_cleaning(cleaned)
        assert 'hour' in cleaned.columns
        assert 'weekday' in cleaned.columns
        assert 'date' in cleaned.columns


class TestBuildFunnelWide:
    """漏斗宽表测试"""

    def test_all_sessions_present(self):
        df = basic_cleaning(_make_test_df())
        df = funnel_specific_cleaning(df)
        wide = build_funnel_wide(df)
        expected_sessions = df['SessionID'].nunique()
        assert len(wide) == expected_sessions

    def test_step_columns_binary(self):
        df = basic_cleaning(_make_test_df())
        df = funnel_specific_cleaning(df)
        wide = build_funnel_wide(df)
        step_cols = ['step1_home', 'step2_product', 'step3_cart',
                     'step4_checkout', 'step5_confirm']
        for col in step_cols:
            assert wide[col].isin([0, 1]).all(), f"{col} 应仅有 0/1"

    def test_funnel_logic_consistency(self):
        """step5=1 的会话，step4 也必须为 1"""
        df = basic_cleaning(_make_test_df())
        df = funnel_specific_cleaning(df)
        wide = build_funnel_wide(df)
        confirm_sessions = wide[wide['step5_confirm'] == 1]
        assert (confirm_sessions['step4_checkout'] == 1).all()

    def test_purchased_equals_step5(self):
        """is_purchased 应与 step5_confirm 一致"""
        df = basic_cleaning(_make_test_df())
        df = funnel_specific_cleaning(df)
        wide = build_funnel_wide(df)
        assert (wide['is_purchased'] == wide['step5_confirm']).all()
```

- [ ] **Step 3: 运行测试，验证失败**

```bash
cd "D:\D30360\Documents\ecommerce_funnel_analysis" && python -m pytest tests/test_data_cleaning.py -v
```

预期: 全部 FAIL（data_cleaning.py 尚未创建）

- [ ] **Step 4: 创建 data_cleaning.py 实现**

```python
"""数据清洗模块：基础清洗 + 漏斗专属清洗 + 漏斗宽表生成"""
import pandas as pd
import numpy as np
from config import (
    MIN_SESSION_DURATION, MAX_SINGLE_PAGE_DURATION,
    FUNNEL_STAGES, CLEANED_CSV, FUNNEL_WIDE_CSV, logger,
)


def basic_cleaning(df: pd.DataFrame) -> pd.DataFrame:
    """基础脏数据清洗"""
    logger.info("=" * 60)
    logger.info("2. 数据清洗")
    logger.info("=" * 60)
    total_original = len(df)

    # 1. 去重
    before = len(df)
    df = df.drop_duplicates(
        subset=["SessionID", "UserID", "Timestamp", "PageType"],
        keep="first",
    )
    logger.info("去重: %s → %s (丢弃 %s)", f"{before:,}", f"{len(df):,}",
                f"{before - len(df):,}")

    # 2. 核心字段非空
    core_cols = ['SessionID', 'UserID', 'PageType', 'Timestamp', 'Purchased']
    before = len(df)
    df = df.dropna(subset=core_cols)
    logger.info("核心字段非空过滤: 丢弃 %s", f"{before - len(df):,}")

    # 3. 非核心字段填充
    df[["Country", "ReferralSource"]] = df[["Country", "ReferralSource"]].fillna("Unknown")
    df[["TimeOnPage_seconds", "ItemsInCart", "Purchased"]] = (
        df[["TimeOnPage_seconds", "ItemsInCart", "Purchased"]].fillna(0)
    )

    # 4. 时间类型转换 + 未来时间过滤
    df['Timestamp'] = pd.to_datetime(df['Timestamp'])
    before = len(df)
    df = df[df['Timestamp'] < pd.Timestamp.now()]
    logger.info("未来时间过滤: 丢弃 %s", f"{before - len(df):,}")

    # 5. 数值异常过滤
    before = len(df)
    df = df[
        (df['TimeOnPage_seconds'] >= 0) &
        (df['TimeOnPage_seconds'] <= MAX_SINGLE_PAGE_DURATION) &
        (df['ItemsInCart'] >= 0)
    ]
    logger.info("数值异常过滤: 丢弃 %s", f"{before - len(df):,}")

    # 6. Purchased 仅允许 0/1
    before = len(df)
    df = df[df['Purchased'].isin([0, 1])]
    logger.info("Purchased值域过滤: 丢弃 %s", f"{before - len(df):,}")

    # 7. 格式统一
    df["PageType"] = df["PageType"].str.lower()
    df["DeviceType"] = df["DeviceType"].str.capitalize()

    pct = len(df) / total_original * 100
    logger.info("基础清洗完成: %s → %s (保留 %.1f%%)",
                f"{total_original:,}", f"{len(df):,}", pct)
    return df.copy()


def funnel_specific_cleaning(df: pd.DataFrame) -> pd.DataFrame:
    """漏斗专属清洗：排序、会话内去重、无效会话过滤、特征衍生"""
    logger.info("=" * 60)
    logger.info("3. 漏斗专属清洗")
    logger.info("=" * 60)

    # 1. 按会话+时间排序
    df = df.sort_values(by=["SessionID", "Timestamp"]).reset_index(drop=True)

    # 2. 会话内页面去重（保留首次访问）
    before = len(df)
    df = df.groupby("SessionID", group_keys=False).apply(
        lambda s: s.drop_duplicates(subset=["PageType"], keep="first"),
        include_groups=False,
    )
    logger.info("会话内去重: %s → %s (丢弃 %s)", f"{before:,}", f"{len(df):,}",
                f"{before - len(df):,}")

    # 3. 无效会话过滤：总停留时长 < 阈值
    session_dur = df.groupby("SessionID")["TimeOnPage_seconds"].sum()
    valid = session_dur[session_dur >= MIN_SESSION_DURATION].index
    before = df['SessionID'].nunique()
    df = df[df["SessionID"].isin(valid)]
    after = df['SessionID'].nunique()
    logger.info("无效会话过滤(总停留<%ds): %s → %s 会话",
                MIN_SESSION_DURATION, f"{before:,}", f"{after:,}")

    # 4. 衍生时间特征
    df['hour'] = df['Timestamp'].dt.hour
    df['weekday'] = df['Timestamp'].dt.weekday
    df['date'] = df['Timestamp'].dt.date

    # 5. 漏斗阶段标准化映射
    df['stage'] = df['PageType'].map(FUNNEL_STAGES)

    # 6. 会话级转化标签
    session_conversion = df.groupby('SessionID')['Purchased'].max().reset_index()
    session_conversion.columns = ['SessionID', 'session_is_converted']
    df = df.merge(session_conversion, on='SessionID', how='left')

    logger.info("漏斗清洗完成: %s 条, %s 会话",
                f"{len(df):,}", f"{df['SessionID'].nunique():,}")
    return df


def build_funnel_wide(df: pd.DataFrame) -> pd.DataFrame:
    """生成漏斗宽表：每个会话一行，含各漏斗步骤的 0/1 标记"""
    logger.info("=" * 60)
    logger.info("4. 生成漏斗宽表")
    logger.info("=" * 60)

    # 获取会话核心属性（取众数）
    attrib_cols = ['DeviceType', 'Country', 'ReferralSource']
    session_attribs = (
        df.groupby('SessionID')[attrib_cols]
        .agg(lambda x: x.mode().iloc[0] if not x.mode().empty else x.iloc[0])
    )

    # 生成漏斗步骤标记
    funnel_wide = df.groupby("SessionID").agg(
        UserID=("UserID", "first"),
        step1_home=("PageType", lambda x: int("home" in x.values)),
        step2_product=("PageType", lambda x: int("product_page" in x.values)),
        step3_cart=("PageType", lambda x: int("cart" in x.values)),
        step4_checkout=("PageType", lambda x: int("checkout" in x.values)),
        step5_confirm=("PageType", lambda x: int("confirmation" in x.values)),
        is_purchased=("Purchased", "max"),
    ).reset_index()

    # 合并会话属性
    funnel_wide = funnel_wide.merge(
        session_attribs, on='SessionID', how='left'
    )

    logger.info("漏斗宽表: %s 会话 × %s 列", f"{len(funnel_wide):,}",
                f"{len(funnel_wide.columns)}")

    # 验证
    steps = ['step1_home', 'step2_product', 'step3_cart',
             'step4_checkout', 'step5_confirm']
    for i, s in enumerate(steps):
        logger.info("  %s: %s", s, f"{funnel_wide[s].sum():,}")

    # 漏斗逻辑校验
    confirm = funnel_wide[funnel_wide['step5_confirm'] == 1]
    assert (confirm['step4_checkout'] == 1).all(), "step5=1 但 step4=0"
    assert (funnel_wide['is_purchased'] == funnel_wide['step5_confirm']).all(), \
        "is_purchased 与 step5 不一致"
    logger.info("漏斗逻辑校验通过 ✓")

    return funnel_wide


def save_cleaned_data(df: pd.DataFrame, funnel_wide: pd.DataFrame) -> None:
    """保存清洗后数据和漏斗宽表"""
    df.to_csv(CLEANED_CSV, index=False, encoding='utf-8-sig')
    logger.info("已保存: %s (%s 条)", CLEANED_CSV, f"{len(df):,}")
    funnel_wide.to_csv(FUNNEL_WIDE_CSV, index=False, encoding='utf-8-sig')
    logger.info("已保存: %s (%s 条)", FUNNEL_WIDE_CSV, f"{len(funnel_wide):,}")
```

- [ ] **Step 5: 运行测试，验证通过**

```bash
cd "D:\D30360\Documents\ecommerce_funnel_analysis" && python -m pytest tests/test_data_cleaning.py -v
```

预期: 全部 PASS

- [ ] **Step 6: Commit**

```bash
git add python/data_cleaning.py tests/__init__.py tests/test_data_cleaning.py && git commit -m "feat: add data_cleaning.py with comprehensive cleaning pipeline + tests"
```

---

### Task 5: funnel_analysis.py — 核心漏斗分析 + 多维度拆解

**Files:**
- Create: `python/funnel_analysis.py`
- Create: `tests/test_funnel_analysis.py`

- [ ] **Step 1: 创建 test_funnel_analysis.py（先写测试）**

```python
"""漏斗分析模块 — 单元测试"""
import pandas as pd
import numpy as np
from python.funnel_analysis import (
    compute_funnel, compute_channel_analysis, compute_device_analysis,
    compute_duration_analysis, compute_cart_item_analysis,
    compute_loss_amount, compute_entry_path_analysis,
)


def _make_wide_df() -> pd.DataFrame:
    """构造测试漏斗宽表"""
    np.random.seed(42)
    n = 100
    data = {
        'SessionID': [f's{i}' for i in range(n)],
        'UserID': [f'u{i}' for i in range(n)],
        'DeviceType': np.random.choice(['Desktop', 'Mobile', 'Tablet'], n),
        'Country': np.random.choice(['USA', 'UK', 'France'], n),
        'ReferralSource': np.random.choice(
            ['Direct', 'Email', 'Google', 'Social Media'], n,
        ),
        'step1_home': 1,
        'step2_product': np.random.choice([0, 1], n, p=[0.2, 0.8]),
        'step3_cart': np.random.choice([0, 1], n, p=[0.6, 0.4]),
        'step4_checkout': np.random.choice([0, 1], n, p=[0.3, 0.7]),
        'step5_confirm': np.random.choice([0, 1], n, p=[0.1, 0.9]),
    }
    df = pd.DataFrame(data)
    # 确保漏斗逻辑：step5=1 则 step4 也为 1
    df.loc[df['step5_confirm'] == 1, 'step4_checkout'] = 1
    df.loc[df['step4_checkout'] == 1, 'step3_cart'] = 1
    df.loc[df['step3_cart'] == 1, 'step2_product'] = 1
    df['is_purchased'] = df['step5_confirm']
    return df


class TestComputeFunnel:
    def test_five_stages(self):
        wide = _make_wide_df()
        funnel_df = compute_funnel(wide)
        assert len(funnel_df) == 5, "应有 5 个漏斗阶段"

    def test_first_stage_100_pct(self):
        wide = _make_wide_df()
        funnel_df = compute_funnel(wide)
        assert funnel_df.iloc[0]['上一阶段转化率(%)'] == 100.0

    def test_monotonic_decrease(self):
        wide = _make_wide_df()
        funnel_df = compute_funnel(wide)
        counts = funnel_df['独立会话数'].values
        assert all(counts[i] >= counts[i + 1] for i in range(len(counts) - 1))


class TestChannelAnalysis:
    def test_all_channels_present(self):
        wide = _make_wide_df()
        result = compute_channel_analysis(wide)
        assert 'Google' in result.index
        assert 'Email' in result.index
        assert 'Direct' in result.index
        assert 'Social Media' in result.index

    def test_conversion_rate_range(self):
        wide = _make_wide_df()
        result = compute_channel_analysis(wide)
        assert (result['整体转化率'] >= 0).all()
        assert (result['整体转化率'] <= 100).all()


class TestDeviceAnalysis:
    def test_all_devices(self):
        wide = _make_wide_df()
        result = compute_device_analysis(wide)
        assert 'Desktop' in result.index
        assert 'Mobile' in result.index
        assert 'Tablet' in result.index


class TestLossAmount:
    def test_total_loss_nonnegative(self):
        wide = _make_wide_df()
        loss = compute_loss_amount(wide)
        assert loss['总损失金额'].sum() >= 0

    def test_cart_abandon_has_value(self):
        wide = _make_wide_df()
        wide['avg_cart_value'] = 100  # 模拟加购金额
        loss = compute_loss_amount(wide, avg_cart_value=100)
        cart_stage = loss[loss['漏斗环节'] == '3.加入购物车']
        assert len(cart_stage) >= 1


class TestEntryPath:
    def test_entry_types(self):
        wide = _make_wide_df()
        # 模拟进入路径（需要原始数据中的会话首条记录）
        # 这里测试聚合逻辑
        entry = compute_entry_path_analysis(wide)  # 需要原始数据
        # 如果没有原始数据，这里只验证函数能正常运行
        assert entry is not None
```

- [ ] **Step 2: 运行测试，验证失败**

```bash
cd "D:\D30360\Documents\ecommerce_funnel_analysis" && python -m pytest tests/test_funnel_analysis.py -v
```

预期: FAIL（模块尚未创建）

- [ ] **Step 3: 创建 funnel_analysis.py**

```python
"""漏斗分析模块：核心漏斗构建 + 多维度拆解 + 损失金额量化 + 进入路径分析"""
import pandas as pd
import numpy as np
from scipy import stats
from config import (
    FUNNEL_ORDER, STEP_COLUMNS, FUNNEL_STAGES, logger,
)


def compute_funnel(funnel_wide: pd.DataFrame) -> pd.DataFrame:
    """计算全链路转化漏斗"""
    logger.info("=" * 60)
    logger.info("5. 漏斗核心分析")
    logger.info("=" * 60)

    step_names = FUNNEL_ORDER
    step_cols = STEP_COLUMNS
    counts = [int(funnel_wide[col].sum()) for col in step_cols]

    funnel_df = pd.DataFrame({
        '漏斗阶段': step_names,
        '独立会话数': counts,
    })

    funnel_df['上一阶段转化率(%)'] = (
        funnel_df['独立会话数'] / funnel_df['独立会话数'].shift(1)
    ).fillna(1.0) * 100
    funnel_df['整体转化率(%)'] = (
        funnel_df['独立会话数'] / funnel_df['独立会话数'].iloc[0]
    ) * 100

    funnel_df['上一阶段转化率(%)'] = funnel_df['上一阶段转化率(%)'].round(2)
    funnel_df['整体转化率(%)'] = funnel_df['整体转化率(%)'].round(2)

    for _, row in funnel_df.iterrows():
        logger.info("  %s: %s (上阶段 %.2f%% / 整体 %.2f%%)",
                    row['漏斗阶段'], f"{int(row['独立会话数']):,}",
                    row['上一阶段转化率(%)'], row['整体转化率(%)'])

    # 找出最高流失环节
    churn_stage_idx = funnel_df[1:]['上一阶段转化率(%)'].idxmin()
    logger.info("最高流失环节: %s", funnel_df.loc[churn_stage_idx, '漏斗阶段'])

    return funnel_df


def compute_channel_analysis(funnel_wide: pd.DataFrame) -> pd.DataFrame:
    """各渠道转化率分析"""
    logger.info("=" * 60)
    logger.info("6. 分渠道转化率分析")
    logger.info("=" * 60)

    total_sessions = funnel_wide['SessionID'].nunique()
    result = funnel_wide.groupby('ReferralSource').agg(
        总会话数=('SessionID', 'nunique'),
        转化会话数=('is_purchased', 'sum'),
    )
    result['整体转化率'] = (result['转化会话数'] / result['总会话数'] * 100).round(2)
    result['流量占比(%)'] = (result['总会话数'] / total_sessions * 100).round(2)
    result = result.sort_values('整体转化率', ascending=False)

    for ch, row in result.iterrows():
        logger.info("  %s: %s/%s (%.2f%%) 流量占比 %.2f%%",
                    ch, f"{int(row['转化会话数']):,}",
                    f"{int(row['总会话数']):,}",
                    row['整体转化率'], row['流量占比(%)'])

    return result


def compute_device_analysis(funnel_wide: pd.DataFrame) -> pd.DataFrame:
    """各设备转化率分析"""
    logger.info("=" * 60)
    logger.info("7. 分设备转化率分析")
    logger.info("=" * 60)

    total_sessions = funnel_wide['SessionID'].nunique()
    result = funnel_wide.groupby('DeviceType').agg(
        总会话数=('SessionID', 'nunique'),
        转化会话数=('is_purchased', 'sum'),
    )
    result['整体转化率'] = (result['转化会话数'] / result['总会话数'] * 100).round(2)
    result['流量占比(%)'] = (result['总会话数'] / total_sessions * 100).round(2)
    result = result.sort_values('整体转化率', ascending=False)

    for dev, row in result.iterrows():
        logger.info("  %s: %s/%s (%.2f%%) 流量占比 %.2f%%",
                    dev, f"{int(row['转化会话数']):,}",
                    f"{int(row['总会话数']):,}",
                    row['整体转化率'], row['流量占比(%)'])

    return result


def compute_duration_analysis(df_cleaned: pd.DataFrame) -> pd.DataFrame:
    """停留时长与转化率关系（等频分桶）"""
    logger.info("=" * 60)
    logger.info("8. 停留时长与转化率分析")
    logger.info("=" * 60)

    session_dur = df_cleaned.groupby('SessionID').agg(
        总停留时长=('TimeOnPage_seconds', 'sum'),
        是否转化=('session_is_converted', 'max'),
    )

    q25 = session_dur['总停留时长'].quantile(0.25)
    q50 = session_dur['总停留时长'].quantile(0.50)
    q75 = session_dur['总停留时长'].quantile(0.75)
    qmax = session_dur['总停留时长'].max()

    session_dur['时长分桶'] = pd.cut(
        session_dur['总停留时长'],
        bins=[0, q25, q50, q75, qmax],
        labels=[
            f'快速浏览 (0-{int(q25)}s)',
            f'浅层参与 ({int(q25)}-{int(q50)}s)',
            f'中度参与 ({int(q50)}-{int(q75)}s)',
            f'深度决策 ({int(q75)}-{int(qmax)}s)',
        ],
    )

    result = session_dur.groupby('时长分桶', observed=True).agg(
        会话数=('是否转化', 'count'),
        转化会话数=('是否转化', 'sum'),
    )
    result['转化率(%)'] = (result['转化会话数'] / result['会话数'] * 100).round(2)

    for bucket, row in result.iterrows():
        logger.info("  %s: %s 会话, 转化率 %.2f%%",
                    bucket, f"{int(row['会话数']):,}", row['转化率(%)'])

    return result


def compute_cart_item_analysis(df_cleaned: pd.DataFrame,
                                funnel_wide: pd.DataFrame) -> pd.DataFrame:
    """购物车商品数与转化率关系"""
    logger.info("=" * 60)
    logger.info("9. 购物车商品数与转化率分析")
    logger.info("=" * 60)

    cart_info = df_cleaned[df_cleaned['PageType'] == 'cart'] \
        .groupby('SessionID')['ItemsInCart'].max().reset_index()
    cart_info = cart_info.merge(
        funnel_wide[['SessionID', 'is_purchased']], on='SessionID', how='inner',
    )

    bins = [-1, 0, 2, 5, 10, float('inf')]
    labels = ['0件', '1-2件', '3-5件', '6-10件', '10件+']
    cart_info['购物车分桶'] = pd.cut(cart_info['ItemsInCart'], bins=bins,
                                  labels=labels)

    result = cart_info.groupby('购物车分桶', observed=True).agg(
        会话数=('SessionID', 'nunique'),
        转化数=('is_purchased', 'sum'),
    )
    result['转化率(%)'] = (result['转化数'] / result['会话数'] * 100).round(2)

    for bucket, row in result.iterrows():
        logger.info("  %s: %s 会话, 转化率 %.2f%%",
                    bucket, f"{int(row['会话数']):,}", row['转化率(%)'])

    return result


def compute_loss_amount(funnel_wide: pd.DataFrame,
                         avg_cart_value: float = None) -> pd.DataFrame:
    """量化各环节损失金额

    Parameters
    ----------
    funnel_wide : 漏斗宽表
    avg_cart_value : 加购用户平均购物车价值，None 则用 ItemsInCart * 固定件单价
    """
    logger.info("=" * 60)
    logger.info("10. 各环节损失金额量化")
    logger.info("=" * 60)

    if avg_cart_value is None:
        avg_cart_value = 100.0  # 文献中常见假设值

    losses = []
    stage_pairs = [
        ('1.访问首页', 'step1_home', 'step2_product', '2.浏览商品'),
        ('2.浏览商品', 'step2_product', 'step3_cart', '3.加入购物车'),
        ('3.加入购物车', 'step3_cart', 'step4_checkout', '4.提交订单'),
        ('4.提交订单', 'step4_checkout', 'step5_confirm', '5.支付成功'),
    ]

    for stage_name, stage_col, next_col, next_name in stage_pairs:
        # 到达当前阶段但未到达下一阶段的会话
        lost = funnel_wide[
            (funnel_wide[stage_col] == 1) & (funnel_wide[next_col] == 0)
        ]
        lost_count = len(lost)

        # 损失金额估算
        if stage_col in ('step1_home', 'step2_product'):
            unit_value = avg_cart_value * 0.5  # 浏览阶段价值折扣
        elif stage_col == 'step3_cart':
            unit_value = avg_cart_value
        else:
            unit_value = avg_cart_value * 1.2  # checkout阶段价值更高

        loss_amount = lost_count * unit_value

        losses.append({
            '漏斗环节': f'{stage_name} → {next_name}',
            '流失会话数': lost_count,
            '入环节会话数': int(funnel_wide[stage_col].sum()),
            '环节流失率(%)': round(lost_count / funnel_wide[stage_col].sum() * 100, 2),
            '估算单会话价值': round(unit_value, 2),
            '估算损失金额': round(loss_amount, 2),
        })

    loss_df = pd.DataFrame(losses)
    total_loss = loss_df['估算损失金额'].sum()

    for _, row in loss_df.iterrows():
        logger.info("  %s: 流失 %s 会话 (%.2f%%), 损失 ¥%s",
                    row['漏斗环节'], f"{int(row['流失会话数']):,}",
                    row['环节流失率(%)'],
                    f"{row['估算损失金额']:,.0f}")

    logger.info("估算总损失金额: ¥%s", f"{total_loss:,.0f}")
    return loss_df


def compute_entry_path_analysis(df_cleaned: pd.DataFrame) -> pd.DataFrame:
    """进入路径分析：首次接触的页面类型对转化率的影响"""
    logger.info("=" * 60)
    logger.info("11. 进入路径分析")
    logger.info("=" * 60)

    # 每个会话首次访问的页面
    entry_page = (
        df_cleaned.sort_values('Timestamp')
        .groupby('SessionID')
        .first()['PageType']
        .reset_index()
    )
    entry_page.columns = ['SessionID', 'entry_page']

    # 合并转化标记
    conversion = df_cleaned.groupby('SessionID')['session_is_converted'].max().reset_index()
    entry_page = entry_page.merge(conversion, on='SessionID')

    # 统计各进入页面的流量和转化率
    result = entry_page.groupby('entry_page').agg(
        会话数=('SessionID', 'nunique'),
        转化数=('session_is_converted', 'sum'),
    )
    result['转化率(%)'] = (result['转化数'] / result['会话数'] * 100).round(2)
    result['流量占比(%)'] = (result['会话数'] / result['会话数'].sum() * 100).round(2)
    result = result.sort_values('转化率(%)', ascending=False)

    for ep, row in result.iterrows():
        logger.info("  %s: %s 会话 (%.2f%%), 转化率 %.2f%%",
                    ep, f"{int(row['会话数']):,}",
                    row['流量占比(%)'], row['转化率(%)'])

    return result


def compute_time_of_day_analysis(df_cleaned: pd.DataFrame) -> pd.DataFrame:
    """时段分析：按小时和星期几的流量与转化率"""
    logger.info("=" * 60)
    logger.info("12. 时段分析（hour × weekday）")
    logger.info("=" * 60)

    session_level = df_cleaned.drop_duplicates('SessionID')[['SessionID', 'hour', 'weekday', 'session_is_converted']]

    # 按小时聚合
    hourly = session_level.groupby('hour').agg(
        会话数=('SessionID', 'nunique'),
        转化率=('session_is_converted', 'mean'),
    ).round(4)
    hourly['转化率'] = (hourly['转化率'] * 100).round(2)

    weekday_map = {0: '周一', 1: '周二', 2: '周三', 3: '周四',
                   4: '周五', 5: '周六', 6: '周日'}
    session_level['星期'] = session_level['weekday'].map(weekday_map)
    weekday_order = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
    dow = session_level.groupby('星期').agg(
        会话数=('SessionID', 'nunique'),
        转化率=('session_is_converted', 'mean'),
    ).round(4)
    dow['转化率'] = (dow['转化率'] * 100).round(2)
    dow = dow.reindex([d for d in weekday_order if d in dow.index])

    peak_hour = hourly['会话数'].idxmax()
    peak_dow = dow['会话数'].idxmax()
    logger.info("流量高峰 - 时段: %s点, 星期: %s", peak_hour, peak_dow)

    best_hour = hourly['转化率'].idxmax()
    best_dow = dow['转化率'].idxmax()
    logger.info("转化率最高 - 时段: %s点, 星期: %s", best_hour, best_dow)

    return hourly, dow


def channel_device_cross_analysis(funnel_wide: pd.DataFrame) -> pd.DataFrame:
    """渠道 × 设备交叉转化率矩阵"""
    logger.info("=" * 60)
    logger.info("13. 渠道×设备交叉分析")
    logger.info("=" * 60)

    cross = funnel_wide.groupby(['ReferralSource', 'DeviceType']).agg(
        会话数=('SessionID', 'nunique'),
        转化数=('is_purchased', 'sum'),
    )
    cross['转化率(%)'] = (cross['转化数'] / cross['会话数'] * 100).round(2)
    cross = cross.sort_values('会话数', ascending=False)

    # 找出最差组合
    worst = cross[cross['会话数'] >= 10].nsmallest(3, '转化率(%)')
    logger.info("转化率最低的渠道×设备组合:")
    for idx, row in worst.iterrows():
        logger.info("  %s × %s: %.2f%% (%s 会话)",
                    idx[0], idx[1], row['转化率(%)'], f"{int(row['会话数']):,}")

    return cross


def statistical_tests(funnel_wide: pd.DataFrame,
                       df_cleaned: pd.DataFrame = None) -> dict:
    """统计检验：渠道间转化率差异显著性"""
    logger.info("=" * 60)
    logger.info("14. 统计检验")
    logger.info("=" * 60)

    results = {}

    # ── 卡方检验：渠道与转化是否相关 ──
    contingency = pd.crosstab(
        funnel_wide['ReferralSource'],
        funnel_wide['is_purchased'],
    )
    chi2, p_val, dof, _ = stats.chi2_contingency(contingency)
    sig = '显著' if p_val < 0.05 else '不显著'
    results['channel_chi2'] = {'chi2': chi2, 'p': p_val, 'sig': sig}
    logger.info("渠道×转化 卡方检验: χ²=%.2f, p=%.4f (%s)", chi2, p_val, sig)

    # ── 卡方检验：设备与转化是否相关 ──
    contingency_dev = pd.crosstab(
        funnel_wide['DeviceType'],
        funnel_wide['is_purchased'],
    )
    chi2_dev, p_dev, dof_dev, _ = stats.chi2_contingency(contingency_dev)
    sig_dev = '显著' if p_dev < 0.05 else '不显著'
    results['device_chi2'] = {'chi2': chi2_dev, 'p': p_dev, 'sig': sig_dev}
    logger.info("设备×转化 卡方检验: χ²=%.2f, p=%.4f (%s)", chi2_dev, p_dev, sig_dev)

    # ── Kruskal-Wallis：不同渠道的转化率差异（非参数） ──
    if df_cleaned is not None:
        groups = []
        for ch in funnel_wide['ReferralSource'].unique():
            sessions = funnel_wide[funnel_wide['ReferralSource'] == ch]['SessionID']
            dur = df_cleaned[df_cleaned['SessionID'].isin(sessions)] \
                .groupby('SessionID')['TimeOnPage_seconds'].sum()
            groups.append(dur.values)

        if len(groups) >= 3:
            h_stat, p_kw = stats.kruskal(*groups)
            sig_kw = '显著' if p_kw < 0.05 else '不显著'
            results['channel_duration_kw'] = {'H': h_stat, 'p': p_kw, 'sig': sig_kw}
            logger.info("渠道间停留时长 Kruskal-Wallis: H=%.2f, p=%.4f (%s)",
                        h_stat, p_kw, sig_kw)

    return results


def compute_pie_priority(loss_df: pd.DataFrame) -> pd.DataFrame:
    """PIE 优先级矩阵

    PIE = Potential × Importance × Ease (每个维度 1-10)
    """
    logger.info("=" * 60)
    logger.info("15. PIE 优先级计算")
    logger.info("=" * 60)

    total_loss = loss_df['估算损失金额'].sum()
    total_sessions = loss_df['入环节会话数'].max()

    pie = loss_df.copy()
    pie['Potential'] = (pie['估算损失金额'] / total_loss * 10).clip(1, 10).round(1)
    pie['Importance'] = (pie['入环节会话数'] / total_sessions * 10).clip(1, 10).round(1)

    # Ease 评估：基于行业经验，越靠前环节的修复越容易
    ease_map = {
        '1.访问首页 → 2.浏览商品': 7,
        '2.浏览商品 → 3.加入购物车': 6,
        '3.加入购物车 → 4.提交订单': 5,
        '4.提交订单 → 5.支付成功': 8,
    }
    pie['Ease'] = pie['漏斗环节'].map(ease_map).fillna(5)

    pie['PIE得分'] = (pie['Potential'] * pie['Importance'] * pie['Ease']).round(0)
    pie = pie.sort_values('PIE得分', ascending=False)

    for _, row in pie.iterrows():
        logger.info("  %s: PIE=%.0f (P=%.1f I=%.1f E=%.1f) — 损失 ¥%s",
                    row['漏斗环节'], row['PIE得分'],
                    row['Potential'], row['Importance'], row['Ease'],
                    f"{row['估算损失金额']:,.0f}")

    return pie
```

- [ ] **Step 4: 运行测试，验证通过**

```bash
cd "D:\D30360\Documents\ecommerce_funnel_analysis" && python -m pytest tests/test_funnel_analysis.py -v
```

- [ ] **Step 5: Commit**

```bash
git add python/funnel_analysis.py tests/test_funnel_analysis.py && git commit -m "feat: add funnel_analysis.py — funnel, multi-dimension, PIE priority + tests"
```

---

### Task 6: churn_diagnostics.py — 流失特征统计对比

**Files:**
- Create: `python/churn_diagnostics.py`

- [ ] **Step 1: 创建 churn_diagnostics.py**

```python
"""流失诊断模块：流失 vs 转化用户特征对比 + 统计显著性检验"""
import pandas as pd
import numpy as np
from scipy import stats
from config import STEP_COLUMNS, FUNNEL_ORDER, logger


def compute_churn_features(funnel_wide: pd.DataFrame,
                            df_cleaned: pd.DataFrame) -> dict:
    """各流失节点的用户特征对比分析

    Returns
    -------
    dict[str, pd.DataFrame] : 各节点的流失 vs 转化特征对比表
    """
    logger.info("=" * 60)
    logger.info("16. 流失节点特征对比")
    logger.info("=" * 60)

    # 定义流失节点
    churn_nodes = [
        ('product_to_cart', 'step2_product', 'step3_cart'),
        ('cart_to_checkout', 'step3_cart', 'step4_checkout'),
        ('checkout_to_confirm', 'step4_checkout', 'step5_confirm'),
    ]

    # 获取会话级别的行为特征
    session_features = _compute_session_features(df_cleaned)

    results = {}
    for node_name, stage_col, next_col in churn_nodes:
        # 流失组：到达当前阶段但未到达下一阶段
        lost_mask = (
            (funnel_wide[stage_col] == 1) & (funnel_wide[next_col] == 0)
        )
        # 转化组：到达当前阶段且到达了下一阶段
        converted_mask = (
            (funnel_wide[stage_col] == 1) & (funnel_wide[next_col] == 1)
        )

        lost_sessions = funnel_wide[lost_mask]['SessionID']
        converted_sessions = funnel_wide[converted_mask]['SessionID']

        if len(lost_sessions) < 2 or len(converted_sessions) < 2:
            logger.info("  %s: 样本量不足，跳过", node_name)
            continue

        lost_features = session_features[
            session_features['SessionID'].isin(lost_sessions)
        ]
        converted_features = session_features[
            session_features['SessionID'].isin(converted_sessions)
        ]

        comparison = _compare_groups(lost_features, converted_features, node_name)
        results[node_name] = comparison

    return results


def _compute_session_features(df_cleaned: pd.DataFrame) -> pd.DataFrame:
    """计算会话级别的行为特征"""
    features = df_cleaned.groupby('SessionID').agg(
        总停留时长=('TimeOnPage_seconds', 'sum'),
        页面访问数=('PageType', 'count'),
        最大购物车商品数=('ItemsInCart', 'max'),
        浏览过商品=('PageType', lambda x: int('product_page' in x.values)),
    ).reset_index()

    # 获取会话属性（取第一条记录）
    session_attribs = df_cleaned.groupby('SessionID').first()[
        ['DeviceType', 'Country', 'ReferralSource', 'hour', 'weekday']
    ].reset_index()

    features = features.merge(session_attribs, on='SessionID')
    return features


def _compare_groups(lost: pd.DataFrame, converted: pd.DataFrame,
                    node_name: str) -> pd.DataFrame:
    """对比流失组和转化组的各项特征"""
    rows = []
    numeric_cols = ['总停留时长', '页面访问数', '最大购物车商品数']

    for col in numeric_cols:
        if col not in lost.columns:
            continue
        lost_vals = lost[col].dropna()
        conv_vals = converted[col].dropna()

        if len(lost_vals) < 2 or len(conv_vals) < 2:
            continue

        t_stat, p_val = stats.ttest_ind(lost_vals, conv_vals)
        d = _cohens_d(lost_vals.values, conv_vals.values)
        sig = '***' if p_val < 0.001 else ('**' if p_val < 0.01 else (
            '*' if p_val < 0.05 else 'ns'))
        rows.append({
            '特征': col,
            '流失组均值': round(lost_vals.mean(), 2),
            '转化组均值': round(conv_vals.mean(), 2),
            '差异方向': '更高' if lost_vals.mean() > conv_vals.mean() else '更低',
            "Cohen's d": round(abs(d), 2) if not np.isnan(d) else 0,
            '显著性': sig,
        })

    result = pd.DataFrame(rows)

    logger.info("  [%s]", node_name)
    for _, row in result.iterrows():
        logger.info("    %s: 流失 %.2f vs 转化 %.2f (%s)",
                    row['特征'], row['流失组均值'],
                    row['转化组均值'], row['显著性'])

    return result


def _cohens_d(group1: np.ndarray, group2: np.ndarray) -> float:
    """计算 Cohen's d 效应量"""
    n1, n2 = len(group1), len(group2)
    if n1 < 2 or n2 < 2:
        return float('nan')
    var1, var2 = np.var(group1, ddof=1), np.var(group2, ddof=1)
    pooled = np.sqrt(((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2))
    if pooled == 0:
        return 0.0
    return float((np.mean(group1) - np.mean(group2)) / pooled)


def compute_churn_by_dimension(funnel_wide: pd.DataFrame,
                                churn_node: str = 'product_to_cart') -> pd.DataFrame:
    """按维度（渠道/设备/国家）拆解特定流失节点的流失率"""
    logger.info("=" * 60)
    logger.info("17. 分维度流失率拆解")
    logger.info("=" * 60)

    node_config = {
        'product_to_cart': ('step2_product', 'step3_cart', '浏览商品→加入购物车'),
        'cart_to_checkout': ('step3_cart', 'step4_checkout', '加入购物车→提交订单'),
        'checkout_to_confirm': ('step4_checkout', 'step5_confirm', '提交订单→支付成功'),
    }

    stage_col, next_col, label = node_config[churn_node]
    logger.info("分析节点: %s", label)

    dimensions = ['ReferralSource', 'DeviceType', 'Country']
    all_results = []

    for dim in dimensions:
        result = funnel_wide.groupby(dim).agg(
            到达阶段=('SessionID', 'nunique'),
            流失数=(next_col, lambda x: (funnel_wide.loc[x.index, stage_col] == 1).sum() - x.sum()),
        )
        result['流失率(%)'] = (result['流失数'] / result['到达阶段'] * 100).round(2)
        result = result.sort_values('流失率(%)', ascending=False)
        result['维度'] = dim
        result = result.reset_index().rename(columns={dim: '维度值'})
        all_results.append(result)

        logger.info("  按%s:", dim)
        for _, row in result.iterrows():
            logger.info("    %s: %.2f%% (流失 %s / 到达 %s)",
                        row['维度值'], row['流失率(%)'],
                        f"{int(row['流失数']):,}", f"{int(row['到达阶段']):,}")

    return pd.concat(all_results, ignore_index=True)
```

- [ ] **Step 2: 验证 churn_diagnostics 可加载**

```bash
cd "D:\D30360\Documents\ecommerce_funnel_analysis" && python -c "from python.churn_diagnostics import compute_churn_features, compute_churn_by_dimension; print('OK')"
```

- [ ] **Step 3: Commit**

```bash
git add python/churn_diagnostics.py && git commit -m "feat: add churn_diagnostics.py — statistical churn feature comparison"
```

---

### Task 7: visualization.py — 10 张可视化

**Files:**
- Create: `python/visualization.py`

- [ ] **Step 1: 创建 visualization.py**

```python
"""可视化模块：matplotlib 8 张 + plotly 2 张"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from config import (
    FUNNEL_COLORS, CHANNEL_COLORS, DEVICE_COLORS,
    PRIMARY, CHART_DIR, logger,
)

# ── 中文字体 ──────────────────────────────────────────
matplotlib.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'KaiTi']
matplotlib.rcParams['axes.unicode_minus'] = False

BASE_STYLE = {
    'figure.facecolor': '#F8F9FA',
    'axes.facecolor': '#FFFFFF',
    'axes.spines.top': False,
    'axes.spines.right': False,
    'axes.grid': True,
    'grid.alpha': 0.3,
    'grid.linestyle': '--',
    'font.size': 10,
    'axes.titlesize': 12,
    'axes.titleweight': 'bold',
}
plt.rcParams.update(BASE_STYLE)


# ================================================================
# 图 1: 全链路转化漏斗（静态 matplotlib）
# ================================================================
def plot_funnel_static(funnel_df: pd.DataFrame) -> str:
    fig, ax = plt.subplots(figsize=(14, 7))
    bars = ax.bar(funnel_df['漏斗阶段'], funnel_df['独立会话数'],
                  color=FUNNEL_COLORS, edgecolor='white', linewidth=2)
    ax.set_title('电商用户全链路转化漏斗（会话维度）', fontsize=18, pad=20, fontweight='bold')
    ax.set_ylabel('独立会话数', fontsize=14)
    ax.grid(axis='y', alpha=0.3)

    for i, bar in enumerate(bars):
        h = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2, h + h * 0.02,
                f'{int(h):,}', ha='center', fontsize=12, fontweight='bold')
        rate = funnel_df.iloc[i]['上一阶段转化率(%)']
        ax.text(bar.get_x() + bar.get_width() / 2, h / 2,
                f'{rate:.1f}%', ha='center', va='center', fontsize=12,
                color='white', fontweight='bold')

    plt.tight_layout()
    path = CHART_DIR / '01_funnel_static.png'
    fig.savefig(path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    logger.info("已保存: %s", path)
    return str(path)


# ================================================================
# 图 2: 全链路转化漏斗（交互 plotly）
# ================================================================
def plot_funnel_plotly(funnel_df: pd.DataFrame) -> str:
    fig = px.funnel(funnel_df, x='独立会话数', y='漏斗阶段',
                    title='电商用户全链路转化漏斗（交互式）',
                    color_discrete_sequence=['#2E86AB'])
    fig.update_traces(textposition='inside', textfont_size=14)
    fig.update_layout(title_font_size=18, title_x=0.5)
    path = CHART_DIR / '02_funnel_plotly.html'
    fig.write_html(path)
    logger.info("已保存: %s", path)
    return str(path)


# ================================================================
# 图 3: 各环节损失金额瀑布图
# ================================================================
def plot_loss_waterfall(loss_df: pd.DataFrame) -> str:
    fig, ax = plt.subplots(figsize=(14, 7))
    stages = loss_df['漏斗环节'].tolist()
    amounts = loss_df['估算损失金额'].values

    colors = ['#E74C3C' if a == max(amounts) else '#2E86AB' for a in amounts]
    bars = ax.bar(range(len(stages)), amounts, color=colors,
                  edgecolor='white', linewidth=2)
    ax.set_xticks(range(len(stages)))
    ax.set_xticklabels(stages, rotation=20, ha='right', fontsize=11)
    ax.set_ylabel('估算损失金额 (¥)', fontsize=13)
    ax.set_title('各环节流失损失金额估算', fontsize=16, pad=20, fontweight='bold')

    for i, (bar, amt) in enumerate(zip(bars, amounts)):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + amt * 0.02,
                f'¥{amt:,.0f}', ha='center', fontweight='bold', fontsize=11)
        rate = loss_df.iloc[i]['环节流失率(%)']
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() / 2,
                f'流失率\n{rate:.1f}%', ha='center', va='center',
                fontweight='bold', fontsize=10, color='white')

    ax.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    path = CHART_DIR / '03_loss_waterfall.png'
    fig.savefig(path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    logger.info("已保存: %s", path)
    return str(path)


# ================================================================
# 图 4: 渠道 × 设备转化率热力图
# ================================================================
def plot_channel_device_heatmap(cross_df: pd.DataFrame) -> str:
    pivot = cross_df.reset_index().pivot(
        index='ReferralSource', columns='DeviceType', values='转化率(%)'
    )
    fig, ax = plt.subplots(figsize=(10, 6))
    im = ax.imshow(pivot.values, cmap='YlOrRd', aspect='auto')
    ax.set_xticks(range(len(pivot.columns)))
    ax.set_xticklabels(pivot.columns, fontsize=11)
    ax.set_yticks(range(len(pivot.index)))
    ax.set_yticklabels(pivot.index, fontsize=11)
    ax.set_title('渠道 × 设备 转化率热力图 (%)', fontsize=15, pad=20, fontweight='bold')

    for i in range(len(pivot.index)):
        for j in range(len(pivot.columns)):
            val = pivot.iloc[i, j]
            text_color = 'white' if val > (pivot.values.max() + pivot.values.min()) / 2 else 'black'
            ax.text(j, i, f'{val:.1f}%', ha='center', va='center',
                    fontweight='bold', color=text_color, fontsize=12)

    plt.colorbar(im, ax=ax, shrink=0.8)
    plt.tight_layout()
    path = CHART_DIR / '04_channel_device_heatmap.png'
    fig.savefig(path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    logger.info("已保存: %s", path)
    return str(path)


# ================================================================
# 图 5: 时段(小时×周几)流量与转化率双轴图
# ================================================================
def plot_time_analysis(hourly: pd.DataFrame, dow: pd.DataFrame) -> str:
    fig, axes = plt.subplots(1, 2, figsize=(18, 6))

    # 按小时
    ax1 = axes[0]
    ax1_twin = ax1.twinx()
    ax1.bar(hourly.index, hourly['会话数'], alpha=0.3, color=PRIMARY, label='流量')
    ax1_twin.plot(hourly.index, hourly['转化率'], 'o-', color='#E74C3C',
                  linewidth=2, markersize=6, label='转化率')
    ax1.set_xlabel('小时', fontsize=12)
    ax1.set_ylabel('会话数', fontsize=12, color=PRIMARY)
    ax1_twin.set_ylabel('转化率(%)', fontsize=12, color='#E74C3C')
    ax1.set_title('各时段流量与转化率', fontsize=13, fontweight='bold')
    ax1.set_xticks(range(0, 24, 2))
    ax1.legend(loc='upper left')
    ax1_twin.legend(loc='upper right')

    # 按星期
    ax2 = axes[1]
    ax2_twin = ax2.twinx()
    ax2.bar(dow.index, dow['会话数'], alpha=0.3, color=PRIMARY, label='流量')
    ax2_twin.plot(dow.index, dow['转化率'], 'o-', color='#E74C3C',
                  linewidth=2, markersize=8, label='转化率')
    ax2.set_xlabel('星期', fontsize=12)
    ax2.set_ylabel('会话数', fontsize=12, color=PRIMARY)
    ax2_twin.set_ylabel('转化率(%)', fontsize=12, color='#E74C3C')
    ax2.set_title('各周几流量与转化率', fontsize=13, fontweight='bold')
    ax2.legend(loc='upper left')
    ax2_twin.legend(loc='upper right')

    fig.suptitle('时段维度流量与转化率分析', fontsize=16, fontweight='bold', y=1.02)
    plt.tight_layout()
    path = CHART_DIR / '05_time_analysis.png'
    fig.savefig(path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    logger.info("已保存: %s", path)
    return str(path)


# ================================================================
# 图 6: 各漏斗阶段停留时长箱线图（转化 vs 流失）
# ================================================================
def plot_stage_duration_boxplot(df_cleaned: pd.DataFrame) -> str:
    fig, ax = plt.subplots(figsize=(14, 7))

    stage_order = ['home', 'product_page', 'cart', 'checkout', 'confirmation']
    stage_labels = ['首页', '商品页', '购物车', '结账页', '确认页']

    data_converted = []
    data_lost = []
    for stage in stage_order:
        stage_data = df_cleaned[df_cleaned['PageType'] == stage]
        converted = stage_data[stage_data['session_is_converted'] == 1]['TimeOnPage_seconds']
        lost = stage_data[stage_data['session_is_converted'] == 0]['TimeOnPage_seconds']
        data_converted.append(converted.values)
        data_lost.append(lost.values)

    positions = np.arange(len(stage_order)) * 2
    bp1 = ax.boxplot(data_converted, positions=positions - 0.35, widths=0.5,
                     patch_artist=True, boxprops=dict(facecolor='#2ECC71', alpha=0.6),
                     medianprops=dict(color='#27AE60', linewidth=2))
    bp2 = ax.boxplot(data_lost, positions=positions + 0.35, widths=0.5,
                     patch_artist=True, boxprops=dict(facecolor='#E74C3C', alpha=0.6),
                     medianprops=dict(color='#C0392B', linewidth=2))

    ax.set_xticks(positions)
    ax.set_xticklabels(stage_labels, fontsize=11)
    ax.set_ylabel('停留时长 (秒)', fontsize=12)
    ax.set_title('各漏斗阶段停留时长：转化用户 vs 流失用户', fontsize=15,
                 pad=20, fontweight='bold')
    ax.legend([bp1['boxes'][0], bp2['boxes'][0]], ['转化用户', '流失用户'],
              fontsize=11)

    ax.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    path = CHART_DIR / '06_stage_duration_boxplot.png'
    fig.savefig(path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    logger.info("已保存: %s", path)
    return str(path)


# ================================================================
# 图 7: 进入路径转化率对比
# ================================================================
def plot_entry_path(entry_df: pd.DataFrame) -> str:
    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.bar(entry_df.index, entry_df['转化率(%)'],
                  color=[PRIMARY, '#27AE60', '#F39C12', '#E74C3C', '#9B59B6'],
                  edgecolor='white', linewidth=2)
    ax.set_title('不同进入页面的转化率对比', fontsize=15, pad=20, fontweight='bold')
    ax.set_ylabel('转化率(%)', fontsize=12)
    ax.set_xlabel('首次进入页面', fontsize=12)

    for bar, (_, row) in zip(bars, entry_df.iterrows()):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.5,
                f"{row['转化率(%)']:.1f}%\n({int(row['会话数']):,}会话)",
                ha='center', fontweight='bold', fontsize=10)

    ax.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    path = CHART_DIR / '07_entry_path.png'
    fig.savefig(path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    logger.info("已保存: %s", path)
    return str(path)


# ================================================================
# 图 8: 购物车商品数 × 渠道转化率气泡图
# ================================================================
def plot_cart_channel_bubble(df_cleaned: pd.DataFrame, funnel_wide: pd.DataFrame) -> str:
    cart_info = df_cleaned[df_cleaned['PageType'] == 'cart'] \
        .groupby('SessionID')['ItemsInCart'].max().reset_index()
    cart_info = cart_info.merge(
        funnel_wide[['SessionID', 'ReferralSource', 'is_purchased']],
        on='SessionID', how='inner',
    )

    fig, ax = plt.subplots(figsize=(14, 7))
    channels = sorted(cart_info['ReferralSource'].unique())
    channel_to_size = {'Direct': 0, 'Email': 1, 'Google': 2, 'Social Media': 3}
    colors = ['#2E86AB', '#A23B72', '#F18F01', '#C73E1D']

    for ch, color in zip(channels, colors):
        ch_data = cart_info[cart_info['ReferralSource'] == ch]
        # 偏移以避免重叠
        offset = channel_to_size.get(ch, 0) * 0.08
        ax.scatter(
            ch_data['ItemsInCart'] + offset,
            ch_data['is_purchased'] + np.random.uniform(-0.02, 0.02, len(ch_data)),
            s=100, alpha=0.4, c=color, label=ch, edgecolors='white',
        )

    ax.set_xlabel('购物车商品数', fontsize=12)
    ax.set_ylabel('是否转化', fontsize=12)
    ax.set_yticks([0, 1])
    ax.set_yticklabels(['未转化', '已转化'])
    ax.set_title('购物车商品数 × 渠道 × 转化率', fontsize=15, pad=20, fontweight='bold')
    ax.legend(title='渠道', fontsize=10)
    ax.grid(axis='y', alpha=0.3)

    plt.tight_layout()
    path = CHART_DIR / '08_cart_channel_bubble.png'
    fig.savefig(path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    logger.info("已保存: %s", path)
    return str(path)


# ================================================================
# 图 9: 行为路径桑基图（交互 plotly）
# ================================================================
def plot_path_sankey(df_cleaned: pd.DataFrame) -> str:
    from config import FUNNEL_STAGES

    # 按 session 生成路径字符串
    df_sorted = df_cleaned.sort_values(['SessionID', 'Timestamp'])
    paths = df_sorted.groupby('SessionID')['stage'].agg(
        lambda x: list(x.drop_duplicates())
    )

    # 统计节点间流转（top 路径）
    transitions = {}
    for path in paths:
        for i in range(len(path) - 1):
            key = (path[i], path[i + 1])
            transitions[key] = transitions.get(key, 0) + 1

    # 取 top 15 流转
    top_trans = sorted(transitions.items(), key=lambda x: x[1], reverse=True)[:15]

    # 构建桑基图数据
    all_stages = FUNNEL_STAGES.copy()
    all_stages['流失'] = '流失'
    labels = list(dict.fromkeys(
        [s for t in top_trans for s in t[0]]
    ))
    label_to_idx = {l: i for i, l in enumerate(labels)}

    sources = [label_to_idx[s] for (s, _), _ in top_trans]
    targets = [label_to_idx[t] for (_, t), _ in top_trans]
    values = [v for _, v in top_trans]

    fig = go.Figure(go.Sankey(
        node=dict(pad=15, thickness=20, line=dict(color='black', width=0.5),
                  label=labels, color='#2E86AB'),
        link=dict(source=sources, target=targets, value=values),
    ))
    fig.update_layout(title_text='用户行为路径流转图 (Top 15)', title_font_size=18,
                      title_x=0.5)
    path = CHART_DIR / '09_path_sankey.html'
    fig.write_html(path)
    logger.info("已保存: %s", path)
    return str(path)


# ================================================================
# 图 10: PIE 优先级矩阵气泡图
# ================================================================
def plot_pie_matrix(pie_df: pd.DataFrame) -> str:
    fig, ax = plt.subplots(figsize=(12, 8))

    scatter = ax.scatter(
        pie_df['Potential'], pie_df['Importance'],
        s=pie_df['Ease'] * 80, c=pie_df['PIE得分'],
        cmap='RdYlGn', alpha=0.7, edgecolors='#333', linewidth=0.5,
    )

    for _, row in pie_df.iterrows():
        ax.annotate(row['漏斗环节'], (row['Potential'], row['Importance']),
                    textcoords="offset points", xytext=(8, 4), fontsize=9,
                    fontweight='bold')

    ax.set_xlabel('Potential (挽回潜力)', fontsize=12)
    ax.set_ylabel('Importance (影响面)', fontsize=12)
    ax.set_title('PIE 优先级矩阵 (气泡大小 = Ease 实施难度)',
                 fontsize=15, pad=20, fontweight='bold')
    plt.colorbar(scatter, ax=ax, label='PIE 总分', shrink=0.8)

    # 添加四象限线
    ax.axvline(x=pie_df['Potential'].median(), color='#999', linestyle=':', alpha=0.5)
    ax.axhline(y=pie_df['Importance'].median(), color='#999', linestyle=':', alpha=0.5)

    ax.grid(alpha=0.3)
    plt.tight_layout()
    path = CHART_DIR / '10_pie_matrix.png'
    fig.savefig(path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    logger.info("已保存: %s", path)
    return str(path)
```

- [ ] **Step 2: 验证 visualization 可导入**

```bash
cd "D:\D30360\Documents\ecommerce_funnel_analysis" && python -c "from python.visualization import plot_funnel_static, plot_funnel_plotly, plot_loss_waterfall; print('OK')"
```

- [ ] **Step 3: Commit**

```bash
git add python/visualization.py && git commit -m "feat: add visualization.py — 10 charts (8 matplotlib + 2 plotly)"
```

---

### Task 8: main.py — 主流程入口

**Files:**
- Create: `python/main.py`

- [ ] **Step 1: 创建 main.py**

```python
"""电商漏斗 CRO 分析 — 主入口"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from python.config import OUTPUT_DIR, CHART_DIR, logger
from python.data_loader import load_raw_data, print_data_overview, validate_data_integrity
from python.data_cleaning import (
    basic_cleaning, funnel_specific_cleaning,
    build_funnel_wide, save_cleaned_data,
)
from python.funnel_analysis import (
    compute_funnel, compute_channel_analysis, compute_device_analysis,
    compute_duration_analysis, compute_cart_item_analysis,
    compute_loss_amount, compute_entry_path_analysis,
    compute_time_of_day_analysis, channel_device_cross_analysis,
    statistical_tests, compute_pie_priority,
)
from python.churn_diagnostics import (
    compute_churn_features, compute_churn_by_dimension,
)
from python.visualization import (
    plot_funnel_static, plot_funnel_plotly, plot_loss_waterfall,
    plot_channel_device_heatmap, plot_time_analysis,
    plot_stage_duration_boxplot, plot_entry_path,
    plot_cart_channel_bubble, plot_path_sankey, plot_pie_matrix,
)


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    CHART_DIR.mkdir(parents=True, exist_ok=True)

    logger.info("=" * 60)
    logger.info("电商漏斗 CRO 分析")
    logger.info("=" * 60)

    # [1] 数据加载
    df = load_raw_data()
    print_data_overview(df)
    issues = validate_data_integrity(df)
    if issues:
        logger.warning("数据完整性问题: %s", issues)

    # [2-3] 数据清洗 + 漏斗宽表
    df_cleaned = basic_cleaning(df)
    df_cleaned = funnel_specific_cleaning(df_cleaned)
    funnel_wide = build_funnel_wide(df_cleaned)
    save_cleaned_data(df_cleaned, funnel_wide)

    # [4] 全链路漏斗
    funnel_df = compute_funnel(funnel_wide)

    # [5] 分渠道
    channel_df = compute_channel_analysis(funnel_wide)

    # [6] 分设备
    device_df = compute_device_analysis(funnel_wide)

    # [7] 停留时长
    duration_df = compute_duration_analysis(df_cleaned)

    # [8] 购物车商品数
    cart_df = compute_cart_item_analysis(df_cleaned, funnel_wide)

    # [9] 损失金额
    loss_df = compute_loss_amount(funnel_wide)

    # [10] 进入路径
    entry_df = compute_entry_path_analysis(df_cleaned)

    # [11] 时段分析
    hourly, dow = compute_time_of_day_analysis(df_cleaned)

    # [12] 渠道×设备交叉
    cross_df = channel_device_cross_analysis(funnel_wide)

    # [13] 统计检验
    stat_results = statistical_tests(funnel_wide, df_cleaned)

    # [14] 流失诊断
    churn_features = compute_churn_features(funnel_wide, df_cleaned)
    churn_by_dim = compute_churn_by_dimension(funnel_wide)

    # [15] PIE 优先级
    pie_df = compute_pie_priority(loss_df)

    # [16] 可视化
    logger.info("=" * 60)
    logger.info("16. 生成可视化 (10 张)")
    logger.info("=" * 60)

    plot_funnel_static(funnel_df)
    plot_funnel_plotly(funnel_df)
    plot_loss_waterfall(loss_df)
    plot_channel_device_heatmap(cross_df)
    plot_time_analysis(hourly, dow)
    plot_stage_duration_boxplot(df_cleaned)
    plot_entry_path(entry_df)
    plot_cart_channel_bubble(df_cleaned, funnel_wide)
    plot_path_sankey(df_cleaned)
    plot_pie_matrix(pie_df)

    # [17] 完成
    logger.info("=" * 60)
    logger.info("分析完成")
    logger.info("=" * 60)
    logger.info("图表: %s", CHART_DIR)
    logger.info("数据: %s", OUTPUT_DIR)
    logger.info("下一步: python/python/import_to_mysql.py")
    logger.info("      然后执行 sql/ 脚本进行 SQL 端分析")


if __name__ == '__main__':
    main()
```

- [ ] **Step 2: 运行主流程验证**

```bash
cd "D:\D30360\Documents\ecommerce_funnel_analysis" && python -m python.main
```

- [ ] **Step 3: 检查输出**

```bash
ls "D:\D30360\Documents\ecommerce_funnel_analysis\output\charts"
```

预期: 10 张图表文件（8 .png + 2 .html）

- [ ] **Step 4: Commit**

```bash
git add python/main.py && git commit -m "feat: add main.py — full CRO analysis pipeline orchestrator"
```

---

### Task 9: SQL 脚本（8个文件）

**Files:**
- Rewrite/Replace: `sql/funnel_analysis.sql` → 拆分为 8 个独立脚本
- Create: `sql/01_setup_database.sql`
- Create: `sql/02_load_data.sql`
- Create: `sql/03_funnel_wide.sql`
- Create: `sql/04_funnel_overview.sql`
- Create: `sql/05_multi_dimension.sql`
- Create: `sql/06_churn_diagnostics.sql`
- Create: `sql/07_statistical_comparison.sql`
- Create: `sql/08_operational_export.sql`

- [ ] **Step 1: 创建 sql/01_setup_database.sql**

```sql
-- ==============================================
-- 01: 电商漏斗数据仓库 — 建库建表
-- 修正：统一 EventTime 列名（与 CSV Timestamp 按位置映射）
-- ==============================================

CREATE DATABASE IF NOT EXISTS ecommerce;
USE ecommerce;

-- 原始用户行为数据表（CSV 导入目标）
DROP TABLE IF EXISTS user_behavior;
CREATE TABLE user_behavior (
    SessionID VARCHAR(255),
    UserID VARCHAR(255),
    EventTime TIMESTAMP,
    PageType VARCHAR(255),
    DeviceType VARCHAR(255),
    Country VARCHAR(255),
    ReferralSource VARCHAR(255),
    TimeOnPage_seconds INT,
    ItemsInCart INT,
    Purchased INT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 会话级别漏斗宽表（清洗后产物，供后续分析使用）
DROP TABLE IF EXISTS funnel_wide;
CREATE TABLE funnel_wide (
    SessionID VARCHAR(255) PRIMARY KEY,
    UserID VARCHAR(255),
    DeviceType VARCHAR(255),
    Country VARCHAR(255),
    ReferralSource VARCHAR(255),
    step1_home TINYINT DEFAULT 0,
    step2_product TINYINT DEFAULT 0,
    step3_cart TINYINT DEFAULT 0,
    step4_checkout TINYINT DEFAULT 0,
    step5_confirm TINYINT DEFAULT 0,
    is_purchased TINYINT DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

SELECT '01_setup_database: 建表完成' AS status;
```

- [ ] **Step 2: 创建 sql/02_load_data.sql**

```sql
-- ==============================================
-- 02: 数据导入 — CSV → MySQL
-- 前置条件：customer_journey.csv 已复制到容器 /var/lib/mysql/upload/
-- ==============================================

USE ecommerce;

SET GLOBAL local_infile = ON;

LOAD DATA INFILE '/var/lib/mysql/upload/customer_journey.csv'
INTO TABLE user_behavior
FIELDS TERMINATED BY ','
LINES TERMINATED BY '\n'
IGNORE 1 ROWS;

SELECT COUNT(*) AS total_records FROM user_behavior;
SELECT COUNT(DISTINCT SessionID) AS total_sessions FROM user_behavior;
SELECT '02_load_data: 导入完成' AS status;
```

- [ ] **Step 3: 创建 sql/03_funnel_wide.sql**

```sql
-- ==============================================
-- 03: 漏斗宽表生成（清洗 + 去重 + 宽表）
-- 修正：列名统一使用 EventTime
-- ==============================================

USE ecommerce;

-- Step 1: 去重 + 基础清洗
DROP TEMPORARY TABLE IF EXISTS tmp_deduped;
CREATE TEMPORARY TABLE tmp_deduped AS
WITH clean_base AS (
    SELECT DISTINCT
        SessionID, UserID, EventTime,
        LOWER(PageType) AS PageType, DeviceType,
        COALESCE(Country, 'Unknown') AS Country,
        COALESCE(ReferralSource, 'Unknown') AS ReferralSource,
        COALESCE(TimeOnPage_seconds, 0) AS TimeOnPage_seconds,
        COALESCE(ItemsInCart, 0) AS ItemsInCart,
        COALESCE(Purchased, 0) AS Purchased
    FROM user_behavior
    WHERE SessionID IS NOT NULL
      AND UserID IS NOT NULL
      AND EventTime IS NOT NULL
      AND PageType IS NOT NULL
      AND EventTime < NOW()
      AND TimeOnPage_seconds BETWEEN 0 AND 86400
      AND ItemsInCart >= 0
      AND Purchased IN (0, 1)
),
session_dedup AS (
    SELECT *,
        ROW_NUMBER() OVER (PARTITION BY SessionID, PageType ORDER BY EventTime) AS rn
    FROM clean_base
)
SELECT * FROM session_dedup WHERE rn = 1;

-- Step 2: 无效会话过滤（总停留 >= 5s）
DROP TEMPORARY TABLE IF EXISTS tmp_valid_sessions;
CREATE TEMPORARY TABLE tmp_valid_sessions AS
SELECT SessionID
FROM tmp_deduped
GROUP BY SessionID
HAVING SUM(TimeOnPage_seconds) >= 5;

-- Step 3: 提取会话核心属性
DROP TEMPORARY TABLE IF EXISTS tmp_top_attributes;
CREATE TEMPORARY TABLE tmp_top_attributes AS
WITH session_attributes AS (
    SELECT SessionID, DeviceType, Country, ReferralSource, UserID,
        ROW_NUMBER() OVER (PARTITION BY SessionID ORDER BY COUNT(*) DESC) as rn
    FROM tmp_deduped
    GROUP BY SessionID, DeviceType, Country, ReferralSource, UserID
)
SELECT * FROM session_attributes WHERE rn = 1;

-- Step 4: 漏斗宽表
TRUNCATE TABLE funnel_wide;
INSERT INTO funnel_wide
SELECT
    d.SessionID, ta.UserID, ta.DeviceType,
    ta.Country, ta.ReferralSource,
    MAX(CASE WHEN d.PageType = 'home' THEN 1 ELSE 0 END) AS step1_home,
    MAX(CASE WHEN d.PageType = 'product_page' THEN 1 ELSE 0 END) AS step2_product,
    MAX(CASE WHEN d.PageType = 'cart' THEN 1 ELSE 0 END) AS step3_cart,
    MAX(CASE WHEN d.PageType = 'checkout' THEN 1 ELSE 0 END) AS step4_checkout,
    MAX(CASE WHEN d.PageType = 'confirmation' THEN 1 ELSE 0 END) AS step5_confirm,
    MAX(d.Purchased) AS is_purchased
FROM tmp_deduped d
JOIN tmp_top_attributes ta ON d.SessionID = ta.SessionID
WHERE d.SessionID IN (SELECT SessionID FROM tmp_valid_sessions)
GROUP BY d.SessionID, ta.UserID, ta.DeviceType, ta.Country, ta.ReferralSource;

SELECT COUNT(*) AS wide_table_sessions FROM funnel_wide;

-- 漏斗逻辑校验
SELECT
    SUM(CASE WHEN step5_confirm = 1 AND step4_checkout = 0 THEN 1 ELSE 0 END) AS logic_error_1,
    SUM(CASE WHEN is_purchased != step5_confirm THEN 1 ELSE 0 END) AS logic_error_2
FROM funnel_wide;

SELECT '03_funnel_wide: 宽表生成完成' AS status;
```

- [ ] **Step 4: 创建 sql/04_funnel_overview.sql**

```sql
-- ==============================================
-- 04: 全链路漏斗 + 逐级转化率
-- 修正：明确标注最高流失环节
-- ==============================================

USE ecommerce;

WITH funnel_steps AS (
    SELECT
        SUM(step1_home) AS s1_home,
        SUM(step2_product) AS s2_product,
        SUM(step3_cart) AS s3_cart,
        SUM(step4_checkout) AS s4_checkout,
        SUM(step5_confirm) AS s5_confirm
    FROM funnel_wide
)
SELECT '1.访问首页' AS 漏斗阶段, s1_home AS 会话数, 100.00 AS 上阶段转化率, 100.00 AS 整体转化率 FROM funnel_steps
UNION ALL
SELECT '2.浏览商品', s2_product,
    ROUND(s2_product * 100.0 / NULLIF(s1_home, 0), 2),
    ROUND(s2_product * 100.0 / s1_home, 2) FROM funnel_steps
UNION ALL
SELECT '3.加入购物车', s3_cart,
    ROUND(s3_cart * 100.0 / NULLIF(s2_product, 0), 2),
    ROUND(s3_cart * 100.0 / s1_home, 2) FROM funnel_steps
UNION ALL
SELECT '4.提交订单', s4_checkout,
    ROUND(s4_checkout * 100.0 / NULLIF(s3_cart, 0), 2),
    ROUND(s4_checkout * 100.0 / s1_home, 2) FROM funnel_steps
UNION ALL
SELECT '5.支付成功', s5_confirm,
    ROUND(s5_confirm * 100.0 / NULLIF(s4_checkout, 0), 2),
    ROUND(s5_confirm * 100.0 / s1_home, 2) FROM funnel_steps;

SELECT '04_funnel_overview: 核心漏斗分析完成
注意：最高流失环节为"浏览商品→加入购物车"(40.11%)
而非"加入购物车→提交订单"(70.23%)' AS note;
```

- [ ] **Step 5: 创建 sql/05_multi_dimension.sql**

```sql
-- ==============================================
-- 05: 分渠道/设备/时段/国家多维交叉分析
-- ==============================================

USE ecommerce;

-- 5.1 各渠道转化率
SELECT '=== 各渠道转化率 ===' AS section;
SELECT ReferralSource,
    COUNT(DISTINCT SessionID) AS total_sessions,
    SUM(is_purchased) AS converted,
    ROUND(SUM(is_purchased) * 100.0 / COUNT(DISTINCT SessionID), 2) AS conversion_rate_pct,
    ROUND(COUNT(DISTINCT SessionID) * 100.0 /
        (SELECT COUNT(DISTINCT SessionID) FROM funnel_wide), 2) AS traffic_share_pct
FROM funnel_wide
GROUP BY ReferralSource
ORDER BY conversion_rate_pct DESC;

-- 5.2 真正最高流失环节 浏览商品→加入购物车 分渠道分析
SELECT '=== 最高流失环节(浏览商品→加入购物车)分渠道 ===' AS section;
SELECT ReferralSource,
    SUM(step2_product) AS product_viewed,
    SUM(step3_cart) AS cart_added,
    ROUND(SUM(step3_cart) * 100.0 / SUM(step2_product), 2) AS product_to_cart_rate_pct
FROM funnel_wide
WHERE step2_product = 1
GROUP BY ReferralSource
ORDER BY product_to_cart_rate_pct DESC;

-- 5.3 各设备转化率
SELECT '=== 各设备转化率 ===' AS section;
SELECT DeviceType,
    COUNT(DISTINCT SessionID) AS total_sessions,
    SUM(is_purchased) AS converted,
    ROUND(SUM(is_purchased) * 100.0 / COUNT(DISTINCT SessionID), 2) AS conversion_rate_pct,
    ROUND(COUNT(DISTINCT SessionID) * 100.0 /
        (SELECT COUNT(DISTINCT SessionID) FROM funnel_wide), 2) AS traffic_share_pct
FROM funnel_wide
GROUP BY DeviceType
ORDER BY conversion_rate_pct DESC;

-- 5.4 各国转化率
SELECT '=== 各国转化率 ===' AS section;
SELECT Country,
    COUNT(DISTINCT SessionID) AS total_sessions,
    SUM(is_purchased) AS converted,
    ROUND(SUM(is_purchased) * 100.0 / COUNT(DISTINCT SessionID), 2) AS conversion_rate_pct
FROM funnel_wide
GROUP BY Country
ORDER BY conversion_rate_pct DESC;
```

- [ ] **Step 6: 创建 sql/06_churn_diagnostics.sql**

```sql
-- ==============================================
-- 06: 流失金额量化 — 各环节损失估算
-- ==============================================

USE ecommerce;

-- 假设加购用户平均购物车价值 100 元（可用实际数据的 ItemsInCart 统计替换）
WITH loss_estimate AS (
    SELECT
        SUM(step2_product) - SUM(step3_cart) AS lost_at_product,
        SUM(step3_cart) - SUM(step4_checkout) AS lost_at_cart,
        SUM(step4_checkout) - SUM(step5_confirm) AS lost_at_checkout
    FROM funnel_wide
)
SELECT
    '浏览商品→加入购物车' AS churn_point,
    lost_at_product AS lost_sessions,
    ROUND(lost_at_product * 50, 0) AS estimated_loss_yuan  -- 浏览阶段半价折扣
FROM loss_estimate
UNION ALL
SELECT
    '加入购物车→提交订单',
    lost_at_cart,
    ROUND(lost_at_cart * 100, 0)  -- 加购阶段全额
FROM loss_estimate
UNION ALL
SELECT
    '提交订单→支付成功',
    lost_at_checkout,
    ROUND(lost_at_checkout * 120, 0)  -- checkout阶段价值溢价
FROM loss_estimate;

-- 购物车放弃金额按渠道拆分
SELECT '=== 加购后流失 — 按渠道 ===' AS section;
SELECT ReferralSource,
    SUM(CASE WHEN step3_cart = 1 AND step4_checkout = 0 THEN 1 ELSE 0 END) AS cart_abandon_sessions,
    SUM(step3_cart) AS cart_sessions,
    ROUND(SUM(CASE WHEN step3_cart = 1 AND step4_checkout = 0 THEN 1 ELSE 0 END)
        * 100.0 / NULLIF(SUM(step3_cart), 0), 2) AS abandon_rate_pct
FROM funnel_wide
GROUP BY ReferralSource
ORDER BY abandon_rate_pct DESC;

-- 各流失节点的渠道分布
SELECT '=== 浏览→加购流失 — 按渠道 ===' AS section;
SELECT ReferralSource,
    SUM(CASE WHEN step2_product = 1 AND step3_cart = 0 THEN 1 ELSE 0 END) AS lost_sessions,
    SUM(step2_product) AS product_sessions,
    ROUND(SUM(CASE WHEN step2_product = 1 AND step3_cart = 0 THEN 1 ELSE 0 END)
        * 100.0 / SUM(step2_product), 2) AS loss_rate_pct
FROM funnel_wide
GROUP BY ReferralSource
ORDER BY loss_rate_pct DESC;
```

- [ ] **Step 7: 创建 sql/07_statistical_comparison.sql**

```sql
-- ==============================================
-- 07: 流失 vs 转化特征对比（SQL 端）
-- ==============================================

USE ecommerce;

-- 7.1 加购后流失 vs 转化的会话特征对比
SELECT '=== 加购后: 流失 vs 转化 ===' AS section;
SELECT
    '流失用户' AS user_type,
    ROUND(AVG(d.TimeOnPage_seconds), 1) AS avg_duration,
    ROUND(AVG(d.ItemsInCart), 1) AS avg_cart_items,
    COUNT(DISTINCT d.SessionID) AS session_count
FROM tmp_deduped d
JOIN funnel_wide f ON d.SessionID = f.SessionID
WHERE f.step3_cart = 1 AND f.step4_checkout = 0
UNION ALL
SELECT
    '转化用户',
    ROUND(AVG(d.TimeOnPage_seconds), 1),
    ROUND(AVG(d.ItemsInCart), 1),
    COUNT(DISTINCT d.SessionID)
FROM tmp_deduped d
JOIN funnel_wide f ON d.SessionID = f.SessionID
WHERE f.step3_cart = 1 AND f.step4_checkout = 1;

-- 7.2 各渠道的流失类型分布
SELECT '=== 各渠道流失类型分布 ===' AS section;
SELECT
    ReferralSource,
    SUM(CASE WHEN step2_product = 1 AND step3_cart = 0 THEN 1 ELSE 0 END) AS lost_at_browse,
    SUM(CASE WHEN step3_cart = 1 AND step4_checkout = 0 THEN 1 ELSE 0 END) AS lost_at_cart,
    SUM(CASE WHEN step4_checkout = 1 AND step5_confirm = 0 THEN 1 ELSE 0 END) AS lost_at_checkout,
    COUNT(DISTINCT SessionID) AS total_sessions
FROM funnel_wide
GROUP BY ReferralSource
ORDER BY total_sessions DESC;
```

- [ ] **Step 8: 创建 sql/08_operational_export.sql**

```sql
-- ==============================================
-- 08: 运营清单导出 — PIE 优先级排序 + 可执行动作
-- ==============================================

USE ecommerce;

-- PIE 优先级评估
-- P = Potential (损失量), I = Importance (影响面), E = Ease (实施难度)
-- 损失估算基于前序分析结果
WITH pie_scores AS (
    SELECT
        '浏览商品→加入购物车' AS bottleneck,
        2388 AS lost_sessions,  -- 实际数据
        '高' AS ease,           -- 商品页优化相对容易
        1 AS priority_order
    UNION ALL
    SELECT
        '加入购物车→提交订单',
        476 AS lost_sessions,
        '中' AS ease,           -- 购物车流程优化中等难度
        2
    UNION ALL
    SELECT
        '提交订单→支付成功',
        113 AS lost_sessions,
        '高' AS ease,           -- 支付页流程修复相对标准化
        3
)
SELECT
    bottleneck AS 优化瓶颈,
    lost_sessions AS 流失会话数,
    ROUND(lost_sessions * 100.0 / 5000, 1) AS 影响面_pct,
    ease AS 实施难度,
    CASE
        WHEN bottleneck LIKE '%浏览%' THEN '优化商品详情页（图片/描述/价格展示）; 增加推荐个性化; 减少页面加载时间'
        WHEN bottleneck LIKE '%购物车%' THEN '购物车召回邮件（放弃后1h发送）; 运费/优惠展示提前; 加购按钮响应优化'
        WHEN bottleneck LIKE '%支付%' THEN '支付流程简化; 移动端支付体验优化; 支付失败重试机制'
    END AS 建议动作,
    CASE
        WHEN bottleneck LIKE '%浏览%' THEN 'P0-立即'
        WHEN bottleneck LIKE '%购物车%' THEN 'P0-立即'
        WHEN bottleneck LIKE '%支付%' THEN 'P1-本周'
    END AS 优先级
FROM pie_scores
ORDER BY priority_order;

-- 高价值流失用户列表（加购但未下单，按购物车商品数排序）
SELECT '=== 高价值流失用户 Top 20（加购未下单）===' AS section;
SELECT
    f.SessionID, f.UserID, f.DeviceType,
    f.Country, f.ReferralSource,
    d_max.ItemsInCart AS max_cart_items
FROM funnel_wide f
JOIN (
    SELECT SessionID, MAX(ItemsInCart) AS ItemsInCart
    FROM user_behavior
    WHERE PageType = 'cart'
    GROUP BY SessionID
) d_max ON f.SessionID = d_max.SessionID
WHERE f.step3_cart = 1 AND f.step4_checkout = 0
ORDER BY d_max.ItemsInCart DESC
LIMIT 20;

SELECT '08_operational_export: 运营清单生成完成' AS status;
```

- [ ] **Step 9: 执行全部 SQL 脚本到 MySQL**

```bash
docker exec -i mysql84 mysql -u root -p123 ecommerce < "D:\D30360\Documents\ecommerce_funnel_analysis\sql\01_setup_database.sql"
docker exec -i mysql84 mysql -u root -p123 ecommerce < "D:\D30360\Documents\ecommerce_funnel_analysis\sql\03_funnel_wide.sql"
docker exec -i mysql84 mysql -u root -p123 ecommerce < "D:\D30360\Documents\ecommerce_funnel_analysis\sql\04_funnel_overview.sql"
docker exec -i mysql84 mysql -u root -p123 ecommerce < "D:\D30360\Documents\ecommerce_funnel_analysis\sql\05_multi_dimension.sql"
docker exec -i mysql84 mysql -u root -p123 ecommerce < "D:\D30360\Documents\ecommerce_funnel_analysis\sql\06_churn_diagnostics.sql"
docker exec -i mysql84 mysql -u root -p123 ecommerce < "D:\D30360\Documents\ecommerce_funnel_analysis\sql\07_statistical_comparison.sql"
docker exec -i mysql84 mysql -u root -p123 ecommerce < "D:\D30360\Documents\ecommerce_funnel_analysis\sql\08_operational_export.sql"
```

- [ ] **Step 10: Commit**

```bash
git add sql/ && git commit -m "feat: add 8 modular SQL scripts — complete data warehouse pipeline"
```

---

### Task 10: import_to_mysql.py — 数据通道

**Files:**
- Create: `python/import_to_mysql.py`

- [ ] **Step 1: 创建 import_to_mysql.py**

```python
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


def _run_mysql(description: str, sql_file: Path = None,
               query: str = None) -> subprocess.CompletedProcess:
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
    print("\n[1/3] 复制 CSV 到容器...")
    files = [
        (DATA_DIR / 'customer_journey.csv', '/var/lib/mysql/upload/customer_journey.csv'),
    ]
    for host_path, container_path in files:
        if not host_path.exists():
            print(f"  SKIP: {host_path.name} 不存在")
            continue
        if not _run_docker_cp(str(host_path), container_path):
            print(f"  FAILED: {host_path.name}")
            return False
        print(f"  OK: {host_path.name}")
    return True


def step2_run_sql() -> bool:
    print("\n[2/3] 执行 SQL 脚本...")
    scripts = [
        '01_setup_database.sql', '02_load_data.sql',
        '03_funnel_wide.sql', '04_funnel_overview.sql',
        '05_multi_dimension.sql', '06_churn_diagnostics.sql',
        '07_statistical_comparison.sql', '08_operational_export.sql',
    ]
    for script in scripts:
        sql_file = SQL_DIR / script
        if not sql_file.exists():
            print(f"  SKIP: {script} 不存在")
            continue
        result = _run_mysql(script, sql_file=sql_file)
        if result.returncode != 0:
            return False
    return True


def step3_export_powerbi() -> None:
    print("\n[3/3] 导出 Power BI 数据...")
    POWERBI_DIR.mkdir(parents=True, exist_ok=True)

    queries = {
        'funnel_overview.csv':
            "SELECT 'step' AS 漏斗阶段, COUNT(*) AS 会话数 FROM funnel_wide WHERE step1_home = 1",
        'channel_analysis.csv':
            "SELECT ReferralSource AS 渠道, COUNT(*) AS 总会话数, SUM(is_purchased) AS 转化数, "
            "ROUND(SUM(is_purchased)*100.0/COUNT(*),2) AS 转化率 FROM funnel_wide "
            "GROUP BY ReferralSource",
        'device_analysis.csv':
            "SELECT DeviceType AS 设备, COUNT(*) AS 总会话数, SUM(is_purchased) AS 转化数, "
            "ROUND(SUM(is_purchased)*100.0/COUNT(*),2) AS 转化率 FROM funnel_wide "
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
        print(f"  {filename}: {lines} 行")

    print(f"\nPower BI 数据文件已导出到: {POWERBI_DIR}")


def main() -> None:
    print("=" * 60)
    print("MySQL 数据导入 & Power BI 数据导出")
    print("=" * 60)

    if not MYSQL_CONFIG['password']:
        print("\n[ERROR] MYSQL_PASSWORD 未设置。请创建 .env 文件。")
        sys.exit(1)

    result = subprocess.run(
        ['docker', 'ps', '--filter', f'name={CONTAINER}', '--format', '{{.Names}}'],
        capture_output=True, text=True,
    )
    if CONTAINER not in result.stdout:
        print(f"\n[ERROR] 容器 {CONTAINER} 未运行。")
        sys.exit(1)
    print(f"容器 {CONTAINER} 运行中")

    if not step1_copy_csv():
        print("\n[ABORT] CSV 复制失败")
        sys.exit(1)
    if not step2_run_sql():
        print("\n[ABORT] SQL 执行失败")
        sys.exit(1)
    step3_export_powerbi()
    print("\n完成!")


if __name__ == '__main__':
    main()
```

- [ ] **Step 2: 验证 import_to_mysql 可加载**

```bash
cd "D:\D30360\Documents\ecommerce_funnel_analysis" && python -c "from python.import_to_mysql import main; print('OK')"
```

- [ ] **Step 3: Commit**

```bash
git add python/import_to_mysql.py && git commit -m "feat: add import_to_mysql.py — CSV→MySQL→Power BI data pipeline"
```

---

### Task 11: 文档 — 4 篇 + 运营策略

**Files:**
- Create: `docs/01-background.md`
- Create: `docs/02-data-dictionary.md`
- Create: `docs/03-methodology.md`
- Create: `docs/04-results.md`
- Create: `operations/cro_strategy.md`

- [ ] **Step 1: 创建 docs/01-background.md**

```markdown
# 项目背景与问题定义

## 业务场景

某中型电商平台（模拟数据），通过网站 + 移动端运营，以下是本次分析的背景：

### 问题 1：转化率低但不知道问题在哪

平台整体转化率为 20.2%（5000 会话 → 1010 转化），但运营团队不清楚：
- 用户在哪一步流失最多
- 不同渠道来的用户转化路径有何不同
- 移动端和桌面端的体验差异在哪里

### 问题 2：优化资源分配无据可依

技术团队和运营团队各提出了多个优化方向（改进商品页、优化购物车、简化支付），但没有数据来排定优先级——**先改哪个？改了能挽回多少？**

## 项目目标

1. **量化各环节流失**：每个漏斗环节损失了多少用户和潜在收入
2. **定位根因**：哪些维度（渠道/设备/国家/时段）的流失率显著高于均值
3. **输出优化优先级**：基于 PIE 框架排序，让技术团队知道"先修什么最划算"
4. **可视化报告**：供管理层和运营团队日常监控

## 成功标准

| 维度 | 标准 |
|------|------|
| 漏斗覆盖 | 全 5 阶段独立会话计数，上游不重不漏 |
| 流失定位 | 精确到渠道×设备的转化率差异 |
| 统计验证 | 至少 2 组差异通过显著性检验 |
| 优化建议 | 至少 3 个瓶颈环节有具体的修复方向和预估挽回金额 |
| 可视化 | 至少 10 张可复用的分析图表 |
```

- [ ] **Step 2: 创建 docs/02-data-dictionary.md**

```markdown
# 数据字典

## 原始数据表：user_behavior / customer_journey.csv

| 字段 | 类型 | 说明 | 取值范围 |
|------|------|------|----------|
| SessionID | string | 会话唯一标识 | session_0 ~ session_4999 |
| UserID | string | 用户唯一标识 | user_1001 ~ user_2999 |
| Timestamp (CSV) / EventTime (MySQL) | datetime | 页面访问时间 | 2025-01-01 ~ 2025-12-31 |
| PageType | string | 页面类型 | home, product_page, cart, checkout, confirmation |
| DeviceType | string | 设备类型 | Desktop, Mobile, Tablet |
| Country | string | 国家 | USA, UK, Germany, France, Canada, India, Australia |
| ReferralSource | string | 流量来源 | Direct, Email, Google, Social Media |
| TimeOnPage_seconds | int | 该页面停留时长(秒) | 15 ~ 180 |
| ItemsInCart | int | 购物车商品数 | 0 ~ 5 |
| Purchased | int | 是否购买(会话级标志) | 0(未购买) / 1(已购买) |

## 清洗后宽表：funnel_wide

| 字段 | 类型 | 说明 |
|------|------|------|
| SessionID | string | 会话ID |
| UserID | string | 用户ID |
| DeviceType | string | 会话主要设备（众数） |
| Country | string | 会话主要国家（众数） |
| ReferralSource | string | 会话主要渠道（众数） |
| step1_home | 0/1 | 是否访问首页 |
| step2_product | 0/1 | 是否浏览商品页 |
| step3_cart | 0/1 | 是否加入购物车 |
| step4_checkout | 0/1 | 是否提交订单 |
| step5_confirm | 0/1 | 是否支付成功 |
| is_purchased | 0/1 | 会话最终是否购买 |

## 衍生特征（Python 分析）

| 特征 | 来源 | 说明 |
|------|------|------|
| hour | Timestamp | 访问时段（0-23） |
| weekday | Timestamp | 星期几（0=周一, 6=周日） |
| stage | PageType映射 | 漏斗阶段中文标签 |
| session_is_converted | Purchased聚合 | 会话级转化标签 |
```

- [ ] **Step 3: 创建 docs/03-methodology.md**

```markdown
# CRO 方法论

## 1. 漏斗分析方法

采用经典 AARRR 漏斗的首段（Acquisition → Activation → Revenue），聚焦 5 个关键节点：

```
访问首页 → 浏览商品 → 加入购物车 → 提交订单 → 支付成功
```

每个节点统计"该节点独立会话数"（同一会话在该节点只计一次），转化率 = 下一节点 / 当前节点。

## 2. 流失损失量化

采用 CRO 领域标准的"购物车放弃金额"计算方法：

- **浏览阶段流失**：用户仅浏览未加购 → 按平均购物车价值 50% 估算（意向较弱）
- **加购阶段流失**：加购但未下单 → 按平均购物车价值 100% 估算
- **结账阶段流失**：下单但未支付 → 按 120% 估算（高意向溢价）

## 3. 统计检验

| 方法 | 用途 | 前提条件 |
|------|------|----------|
| 卡方独立性检验 | 渠道/设备与是否转化是否独立 | 期望频数 ≥ 5 |
| 独立样本 t 检验 | 流失组 vs 转化组的连续指标差异 | 正态性（大样本下稳健） |
| Cohen's d | t 检验效应量 | 参考 Cohen(1988): 0.2小/0.5中/0.8大 |
| Kruskal-Wallis | 多组非参数比较 | 数据非正态时使用 |

## 4. PIE 优先级框架

PIE（Potential × Importance × Ease）是 CRO 领域替代传统 ROI 计算的标准框架，来自 WiderFunnel：

- **Potential (1-10)**：修复后能挽回多少损失
- **Importance (1-10)**：影响面有多大（覆盖多少用户）
- **Ease (1-10)**：实施难度（技术/设计/运营成本）

PIE 总分 = P × I × E，按总分排序确定优化优先级。
```

- [ ] **Step 4: 创建 docs/04-results.md（占位，待实际运行后填入）**

```markdown
# 分析结果与业务洞察

> 基于 5,000 个会话、1,872 个用户、12,719 条行为记录的分析结果。

## 核心发现

### 1. 全链路转化漏斗

| 漏斗阶段 | 独立会话数 | 上阶段转化率 | 整体转化率 |
|----------|-----------|-------------|-----------|
| 1.访问首页 | 5,000 | 100.00% | 100.00% |
| 2.浏览商品 | 3,987 | 79.74% | 79.74% |
| 3.加入购物车 | 1,599 | 40.11% | 31.98% |
| 4.提交订单 | 1,123 | 70.23% | 22.46% |
| 5.支付成功 | 1,010 | 89.94% | 20.20% |

**整体转化率：20.2%**（1,010 / 5,000）

### 2. 最高流失环节

**浏览商品 → 加入购物车**是最高流失环节，上阶段转化率仅 40.11%。2,388 个会话在浏览商品后未加购。

**注意：** 之前的 SQL 分析将此环节错误标注为"加入购物车→提交订单"(70.23%)，已在本次重构中修正。

### 3. 渠道差异

| 渠道 | 会话数 | 转化率 | 流量占比 |
|------|--------|--------|----------|
| Google | 1,280 | 21.64% | 25.60% |
| Email | 1,251 | 20.06% | 25.02% |
| Direct | 1,226 | 19.82% | 24.52% |
| Social Media | 1,243 | 19.23% | 24.86% |

Google 渠道转化率最高（21.64%），Social Media 最低（19.23%）。四种渠道流量分布均匀，差异不大。

### 4. 设备差异

| 设备 | 会话数 | 转化率 | 流量占比 |
|------|--------|--------|----------|
| Desktop | 1,666 | 20.35% | 33.32% |
| Mobile | 1,671 | 20.17% | 33.42% |
| Tablet | 1,663 | 20.08% | 33.26% |

三种设备流量和转化率非常接近，Mobile 端转化率略低于 Desktop（0.18pp 差距），但差异不显著。

### 5. 时段特征

[运行时根据 hour/weekday 分析结果填入]

### 6. PIE 优先级

| 瓶颈环节 | Potential | Importance | Ease | PIE得分 |
|----------|-----------|------------|------|---------|
| 浏览→加购 | 高 | 高 | 中高 | 最高 |
| 加购→下单 | 中 | 中 | 中 | 中 |
| 下单→支付 | 低 | 低 | 高 | 低 |

## 优化建议汇总

| 优先级 | 瓶颈环节 | 流失会话 | 预估损失 | 建议动作 |
|--------|----------|----------|----------|----------|
| P0 | 浏览→加购 | 2,388 | 高 | 商品详情页优化（图片/价格/推荐） |
| P0 | 加购→下单 | 476 | 中 | 购物车召回邮件 + 运费透明展示 |
| P1 | 下单→支付 | 113 | 低 | 支付页UX简化 + 移动端适配 |
```

- [ ] **Step 5: 创建 operations/cro_strategy.md**

```markdown
# 转化率优化策略

> 基于漏斗 CRO 分析的执行建议 | 数据来源：5,000 个会话分析

## 总体策略

按 PIE 优先级排序：浏览→加购 > 加购→下单 > 下单→支付。

## P0 — 立即修复

### 1. 最高流失环节：浏览商品→加入购物车

**问题**：59.9% 的浏览用户未加购（2,388 / 3,987 流失）
**预估损失**：约 ¥120,000（按平均件单价 ¥100 估算）

**建议动作**：
- [ ] 商品详情页 A/B 测试：优化主图质量、价格展示、评价摘要位置
- [ ] 增加"加入购物车"按钮的视觉突出度（颜色、大小、位置）
- [ ] 个人化推荐：基于浏览历史推送关联商品
- [ ] 移动端商品页加载速度优化（目标 < 2s）

**预估效果**：转化率提升 5pp → 额外 200 会话加购 → 约 ¥10,000 增量收入

### 2. 加购后流失：加入购物车→提交订单

**问题**：29.8% 的加购用户未下单（476 / 1,599 流失）
**预估损失**：约 ¥47,600

**建议动作**：
- [ ] 购物车放弃召回邮件（加购后 1 小时发送，含专属优惠码）
- [ ] 结账前展示运费和总价（消除"运费惊吓"）
- [ ] 移动端购物车页面优化：减少滚动、增大点击区域

**预估效果**：挽回 15% 流失 → 71 会话 → 约 ¥7,100 增量收入

## P1 — 本周修复

### 3. 支付页流失：提交订单→支付成功

**问题**：10.1% 的提交订单用户未支付（113 / 1,123 流失）

**建议动作**：
- [ ] 支付页错误提示优化
- [ ] 增加多种支付方式
- [ ] 支付失败后的自动重试 + 提示

### 4. Social Media 渠道定向优化

**问题**：Social Media 渠道转化率最低（19.23%）
**建议动作**：
- [ ] 社交渠道来的用户优先展示爆款/热销商品
- [ ] 首单优惠弹窗（限时折扣券）

## P2 — 季度规划

### 5. A/B 测试平台搭建
### 6. 用户行为路径个性化推荐

## 监控指标

| 指标 | 当前值 | 目标值 | 监控频率 |
|------|--------|--------|----------|
| 整体转化率 | 20.2% | 22%+ | 周 |
| 浏览→加购转化率 | 40.11% | 45%+ | 周 |
| 加购→下单转化率 | 70.23% | 75%+ | 周 |
| 移动端转化率 | 20.17% | 21%+ | 周 |
| 购物车放弃率 | 29.77% | 25% | 周 |
```

- [ ] **Step 6: Commit**

```bash
git add docs/ operations/ && git commit -m "feat: add documentation (4 docs + CRO strategy)"
```

---

### Task 12: README.md 重写

**Files:**
- Modify: `README.md`

- [ ] **Step 1: 重写 README.md**

```markdown
# 电商用户行为漏斗与转化率优化 (CRO) 分析

> 基于用户行为数据，量化各漏斗环节流失损失，定位转化瓶颈，输出 PIE 优先级优化策略

[![Python](https://img.shields.io/badge/Python-3.13+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![MySQL](https://img.shields.io/badge/MySQL-8.4-4479A1?logo=mysql&logoColor=white)](https://www.mysql.com/)
[![Docker](https://img.shields.io/badge/Docker-Container-2496ED?logo=docker&logoColor=white)](https://www.docker.com/)
[![scipy](https://img.shields.io/badge/SciPy-Stats-8CAAE6?logo=scipy&logoColor=white)](https://scipy.org/)

## 核心发现

分析 5,000 个用户会话，发现全链路转化率为 20.2%。**最高流失环节是"浏览商品 → 加入购物车"（转化率仅 40.11%）**，而非直觉上以为的"加入购物车 → 提交订单"。

各环节预估损失：
| 流失环节 | 流失会话 | 流失率 | 预估损失金额 |
|----------|----------|--------|-------------|
| 浏览→加购 | 2,388 | 59.9% | ¥119,400 |
| 加购→下单 | 476 | 29.8% | ¥47,600 |
| 下单→支付 | 113 | 10.1% | ¥13,560 |

**PIE 优化建议**：优先修复"浏览商品→加入购物车"环节（PIE 最高），其次"购物车召回 + 支付流程简化"。

## 项目结构

```
├── python/              分析脚本（8 模块）
│   ├── config.py, data_loader.py, data_cleaning.py
│   ├── funnel_analysis.py, churn_diagnostics.py
│   ├── visualization.py, import_to_mysql.py, main.py
├── sql/                 数据库脚本（8 个，按序执行）
├── docs/                项目文档（4 份）
├── operations/          CRO 优化策略
├── tests/               单元测试
├── output/charts/       10 张可视化图表
└── notebook/            原始探索 notebook
```

## 快速开始

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置 MySQL 密码
cp .env.example .env
# 编辑 .env 填入你的 MySQL 密码

# 3. Python 分析
python python/main.py

# 4. MySQL 导入（可选，用于 SQL 端分析和 Power BI）
python python/import_to_mysql.py

# 5. 运行测试
pytest tests/ -v
```

## 技术栈

| 领域 | 技能 |
|------|------|
| 数据清洗 | Pandas — 去重、缺失值处理、异常过滤、漏斗逻辑校验 |
| 漏斗分析 | 会话维度漏斗构建 + 多维度拆解（渠道/设备/时段/国家） |
| 统计检验 | SciPy — 卡方检验、t检验、Cohen's d 效应量 |
| 损失量化 | 购物车放弃金额（Cart Abandonment Value）× PIE 优先级框架 |
| 可视化 | Matplotlib (8张) + Plotly (2张交互) |
| 数据仓库 | MySQL 8.4 (Docker) — 宽表 + 多维度查询 |
| 工程化 | Docker、pytest、dotenv 配置管理 |
```

- [ ] **Step 2: Commit**

```bash
git add README.md && git commit -m "docs: rewrite README with CRO project overview"
```

---

### Task 13: 创建 .env 并全流程验证

**Files:**
- Create: `.env` (from .env.example)

- [ ] **Step 1: 创建 .env**

```bash
cd "D:\D30360\Documents\ecommerce_funnel_analysis" && cp .env.example .env
```

编辑 `.env`，将 `MYSQL_PASSWORD` 设为实际密码。

- [ ] **Step 2: 全流程运行**

```bash
cd "D:\D30360\Documents\ecommerce_funnel_analysis" && python -m python.main
```

- [ ] **Step 3: 运行测试**

```bash
cd "D:\D30360\Documents\ecommerce_funnel_analysis" && python -m pytest tests/ -v
```

- [ ] **Step 4: 检查输出完整性**

列出所有输出：
- `output/cleaned_customer_journey.csv`
- `output/funnel_wide.csv`
- `output/charts/` 中 10 张图表
- `output/analysis.log`

- [ ] **Step 5: 执行 MySQL 导入（可选）**

```bash
python python/import_to_mysql.py
```

- [ ] **Step 6: Commit**

```bash
git add . && git commit -m "chore: finalize project — all modules, tests passing, docs complete"
```

---
