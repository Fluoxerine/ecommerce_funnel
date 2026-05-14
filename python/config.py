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
MIN_SESSION_DURATION = 5
MAX_SINGLE_PAGE_DURATION = 86400

# ── 颜色方案 ──────────────────────────────────────────
FUNNEL_COLORS = ['#DB3124', '#FC8C5A', '#FFDF92', '#90BEE0', '#4B74B2']
CHANNEL_COLORS = {'Direct': '#2E86AB', 'Email': '#A23B72',
                  'Google': '#F18F01', 'Social Media': '#C73E1D'}
DEVICE_COLORS = {'Desktop': '#27AE60', 'Mobile': '#3498DB', 'Tablet': '#9B59B6'}

PRIMARY = '#2E86AB'
ACCENT = '#E74C3C'

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
