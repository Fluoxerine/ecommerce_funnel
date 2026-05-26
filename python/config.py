"""项目配置常量 — 所有路径、参数、颜色、日志均从此处获取"""
import os
import logging
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / '.env')

# ── 项目路径 ──────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / 'data'
OUTPUT_DIR = PROJECT_ROOT / 'output'
CHART_DIR = OUTPUT_DIR / 'charts'

# ── 原始数据文件路径 ─────────────────────────────────
EVENTS_CSV = DATA_DIR / 'events.csv'
TRANSACTIONS_CSV = DATA_DIR / 'transactions.csv'
CUSTOMERS_CSV = DATA_DIR / 'customers.csv'
PRODUCTS_CSV = DATA_DIR / 'products.csv'
CAMPAIGNS_CSV = DATA_DIR / 'campaigns.csv'

# ── 清洗后输出路径 ───────────────────────────────────
CLEANED_EVENTS_CSV = OUTPUT_DIR / 'cleaned_events.csv'
FUNNEL_WIDE_CSV = OUTPUT_DIR / 'funnel_wide.csv'
BASELINE_JSON = OUTPUT_DIR / 'baseline_snapshot.json'

# ── MySQL 连接配置 ────────────────────────────────────
MYSQL_CONFIG = {
    'container': os.getenv('MYSQL_CONTAINER', 'mysql84'),
    'host': os.getenv('MYSQL_HOST', '127.0.0.1'),
    'port': int(os.getenv('MYSQL_PORT', '3306')),
    'user': os.getenv('MYSQL_USER', 'root'),
    'password': os.getenv('MYSQL_PASSWORD', ''),
    'database': os.getenv('MYSQL_DATABASE', 'ecommerce'),
}

# ── 漏斗阶段定义（页面级） ────────────────────────────
PAGE_FUNNEL_STAGES = {
    'Home':     '1.首页',
    'PLP':      '2.商品列表页',
    'PDP':      '3.商品详情页',
    'Cart':     '4.购物车',
    'Checkout': '5.结算页',
}

PAGE_FUNNEL_ORDER = ['1.首页', '2.商品列表页', '3.商品详情页', '4.购物车', '5.结算页']

# 严格路径漏斗阶段（必须按顺序访问才算）
STRICT_PAGE_STAGES = ['Home', 'PLP', 'PDP', 'Cart', 'Checkout']
STRICT_PAGE_ORDER = ['1.首页', '2.商品列表页', '3.商品详情页', '4.购物车', '5.结算页']

PAGE_FUNNEL_COLS = ['step1_home', 'step2_plp', 'step3_pdp', 'step4_cart', 'step5_checkout']

# ── 漏斗阶段定义（行为级） ────────────────────────────
EVENT_FUNNEL_ORDER = ['浏览', '点击', '加购', '购买']
EVENT_FUNNEL_COLS = ['step_view', 'step_click', 'step_add_cart', 'step_purchase']

# ── 流失环节定义（页面级） ────────────────────────────
CHURN_STAGES = [
    ('首页 → 列表页',   'step1_home',  'step2_plp'),
    ('列表页 → 详情页', 'step2_plp',   'step3_pdp'),
    ('详情页 → 购物车', 'step3_pdp',   'step4_cart'),
    ('购物车 → 结算页', 'step4_cart',  'step5_checkout'),
]

# ── 清洗阈值 ──────────────────────────────────────────
MIN_SESSION_DURATION = 1           # 最低会话时长 (秒)
MAX_SESSION_DURATION = 7200        # 最高会话时长 (2小时)
MAX_SINGLE_PAGE_DURATION = 3600    # 最长单页时长

# ── 时长分桶（行为分析常用阈值） ───────────────────────────
DURATION_BINS = [0, 60, 180, 420, float('inf')]
DURATION_LABELS = [
    '快速跳出 (<60s)',
    '浅层浏览 (60-180s)',
    '中度参与 (180-420s)',
    '深度决策 (420s+)',
]

# ── 主要分析期 ──────────────────────────────────────
ANALYSIS_YEAR = 2023
BASELINE_YEARS = [2021, 2022]

# ── CRO 行业基准 (来源: Dynamic Yield, Monetate, Littledata) ──
CRO_BENCHMARKS = {
    'avg_session_cr': 2.5,           # 全球电商会话转化率中位数 (%)
    'top_quartile_session_cr': 5.0,  # 前 25% 电商转化率
    'avg_pdp_to_cart': 10.0,         # 详情页→加购 典型值 (%)
    'avg_cart_to_checkout': 25.0,    # 加购→结算 典型值 (%)
    'avg_bounce_rate': 45.0,         # 平均跳出率 (%)
    'industry_top_cr': 15.0,         # Amazon/Walmart 级转化率
    'avg_refund_rate': 4.0,          # 电商平均退款率
    'mobile_cr_multiplier': 0.7,     # 移动端 vs 桌面端 转化率折扣
    'avg_email_cr': 4.5,             # Email 渠道典型转化率
    'avg_social_cr': 1.5,            # Social 渠道典型转化率
    'avg_search_cr': 3.5,            # Paid Search 渠道典型转化率
}

# ── CRO 策略 ROI 基准 ──────────────────────────────────
STRATEGY_ROI = {
    'pdp_optimization': {
        'expected_conversion_lift_pct': 5.0,     # PDP 优化预期转化提升 (%)
        'implementation_weeks': 4,
        'monthly_impact': 'Y500K-Y1M',
    },
    'cart_optimization': {
        'expected_conversion_lift_pct': 3.0,     # 购物车优化预期转化提升 (%)
        'implementation_weeks': 2,
        'monthly_impact': 'Y300K-Y600K',
    },
    'checkout_optimization': {
        'expected_conversion_lift_pct': 5.0,      # 结算优化预期转化提升 (%)
        'implementation_weeks': 3,
        'monthly_impact': 'Y400K-Y800K',
    },
}

# ── 颜色方案 ──────────────────────────────────────────
FUNNEL_COLORS = ['#DB3124', '#FC8C5A', '#FFDF92', '#90BEE0', '#4B74B2']
CHANNEL_COLORS = {
    'Organic': '#2E86AB', 'Paid Search': '#A23B72',
    'Social': '#F18F01', 'Email': '#C73E1D', 'Direct': '#27AE60',
}
DEVICE_COLORS = {'desktop': '#27AE60', 'mobile': '#3498DB', 'tablet': '#9B59B6'}
PRIMARY = '#2E86AB'
ACCENT = '#E74C3C'

# ── 日志配置 ──────────────────────────────────────────
LOG_FORMAT = '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
LOG_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')  # 支持 DEBUG/INFO/WARNING/ERROR

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
CHART_DIR.mkdir(parents=True, exist_ok=True)

_file_handler = logging.FileHandler(OUTPUT_DIR / 'analysis.log', encoding='utf-8')
_file_handler.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))

logging.basicConfig(
    level=logging.INFO,
    format=LOG_FORMAT,
    datefmt=LOG_DATE_FORMAT,
    handlers=[
        logging.StreamHandler(),
        _file_handler,
    ],
)

logger = logging.getLogger('funnel_cro')

# ── 分析版本信息 ─────────────────────────────────────
ANALYSIS_VERSION = '2.0'
ANALYSIS_PARAMS = {
    'version': ANALYSIS_VERSION,
    'data_years': '2021-2023',
    'funnel_methodology': {
        'page_coverage': '各页面独立统计到达会话数 (允许多入口/深链)',
        'strict_path': '按时间顺序 Home→PLP→PDP→Cart→Checkout (人数必递减)',
        'event_funnel': '行为级顺序漏斗 (view→click→add_cart→purchase)',
        'key_clarification': '页面覆盖 ≠ 严格漏斗。覆盖分析中"交叉到达率"不是"转化率", 下游可因深链超上游。',
    },
}
