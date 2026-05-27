"""可视化模块 — 17 张 matplotlib 图表（中文版）"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import matplotlib.ticker as mticker
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.patches import Polygon
import numpy as np
from python.config import CHART_DIR, logger

# ── 中文字体 ────────────────────────────────────────
_font_candidates = [
    'Microsoft YaHei', 'SimHei', 'KaiTi', 'Noto Sans CJK SC',
    'WenQuanYi Micro Hei', 'Noto Sans SC', 'Source Han Sans SC',
    'SimSun', 'FangSong', 'AR PL UMing CN',
]
_available = {f.name for f in fm.fontManager.ttflist}
_font_to_use = next((f for f in _font_candidates if f in _available), None)
if _font_to_use:
    matplotlib.rcParams['font.sans-serif'] = [_font_to_use, 'DejaVu Sans']
else:
    matplotlib.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
matplotlib.rcParams['axes.unicode_minus'] = False
logger.info("图表中文字体: %s", _font_to_use or 'SimHei (fallback)')

# ── 全局样式 ────────────────────────────────────────
plt.rcParams.update({
    'figure.facecolor': '#FAFBFC',
    'axes.facecolor': '#FFFFFF',
    'axes.spines.top': False,
    'axes.spines.right': False,
    'axes.spines.left': False,
    'axes.spines.bottom': False,
    'axes.grid': True,
    'grid.alpha': 0.25,
    'grid.linestyle': '-',
    'grid.color': '#DDE1E6',
    'font.size': 11,
    'axes.titlesize': 14,
    'axes.titleweight': 'bold',
    'axes.labelsize': 12,
    'xtick.labelsize': 10,
    'ytick.labelsize': 10,
    'legend.fontsize': 10,
})

# ── 共享标签常量 ────────────────────────────────────
PAGE_SHORT_LABELS = ['首页', '列表页', '详情页', '购物车', '结算页']
EVENT_SHORT_LABELS = ['浏览', '点击', '加购', '购买']
DEVICE_CN_LABELS = ['手机', '桌面', '平板']

# ── 统一调色板 (Wong 2011 色盲友好) ──────────────
C_BLUE   = '#0072B2'
C_ORANGE = '#E69F00'
C_GREEN  = '#009E73'   # bluish-green, distinguishable from red
C_RED    = '#D55E00'   # vermilion, distinguishable from green
C_PURPLE = '#CC79A7'
C_CYAN   = '#56B4E9'
C_GREY   = '#A0AAB5'
C_DARK   = '#2C3E50'
C_LIGHT  = '#E8ECF1'

# 淡色背景
CL_BLUE   = '#C4D9E8'
CL_ORANGE = '#F0D8C0'
CL_GREEN  = '#C4E8D4'
CL_RED    = '#E8C4C4'
CL_GREY   = '#DDE1E6'

DURATION_COLORS = ['#0072B2', '#E69F00', '#56B4E9', '#009E73']
STAGE_COLORS    = ['#0072B2', '#56B4E9', '#009E73', '#CC79A7']

# 渠道 → 颜色映射 (与 Wong 2011 主色系协调)
CHANNEL_COLORS_MAP = {
    'Organic': '#3A7CA5', 'Paid Search': '#B8456E', 'Social': '#E8934B',
    'Email': '#D64545', 'Direct': '#4CAF82',
}

# ── 预构建 colormap (模块级复用) ──────────────────
CMAP_RDYLGN = LinearSegmentedColormap.from_list(
    'custom_rdylgn',
    ['#D64545', '#E8934B', '#F2D398', '#E8ECCA', '#4CAF82'],
    N=256,
)
CMAP_RETENTION = LinearSegmentedColormap.from_list(
    'retention_green',
    ['#F5F5F5', '#C4E8D4', '#4CAF82', '#2D7A4A'],
    N=256,
)

# ── 漏斗图专用色板 (深→浅蓝渐变) ─────────────────
FUNNEL_PALETTE = ['#1B4F72', '#2874A6', '#2E86C1', '#5499C7', '#85C1E9', '#AED6F1']

# 全局图表元信息 — 绘图前由 main.py 设置
_CHART_META: dict[str, int] = {}


def set_chart_meta(n_sessions: int) -> None:
    """设置全局样本量 → 所有图表自动添加元信息脚注"""
    _CHART_META['n_sessions'] = n_sessions


def _save(fig, name: str) -> None:
    from datetime import date
    n = _CHART_META.get('n_sessions', 0)
    n_str = f' | n={n:,} sessions' if n else ''
    footnote = f'ecommerce_funnel_analysis{n_str} | {date.today().isoformat()}'
    fig.text(0.5, -0.01, footnote, ha='center', fontsize=7,
             color='#999999', transform=fig.transFigure)
    fig.savefig(str(CHART_DIR / f'{name}.png'), dpi=180, bbox_inches='tight',
                facecolor=fig.get_facecolor(), edgecolor='none')
    plt.close(fig)
    logger.info("  Saved: %s", (CHART_DIR / f'{name}.png').name)


def _draw_funnel_polygons(ax, labels, values, rate_labels, colors, max_val=None, power=1.0):
    """用梯形 Polygon 绘制居中对齐的漏斗图。

    每层宽度按 value/max_val 比例缩放，从上到下逐层变窄。
    如遇下游值大于上游（深链倒挂），梯形会外扩以反映真实数据。

    power < 1.0 时采用幂律压缩宽度，使尾端窄层不至于消失（如 0.3 可将
    0.02% 的末层拉回 ~10% 宽度），标签仍显示原始数值。
    """
    n = len(labels)
    arr = np.array(values, dtype=float)
    if max_val is None:
        max_val = float(np.max(arr))

    # 幂律缩放后的宽度比例 (视觉宽度) — 标签始终显示原始值
    if power != 1.0:
        scaled = np.power(arr, power)
        scaled_max = np.power(max_val, power)
        width_ratios = scaled / scaled_max
    else:
        width_ratios = arr / max_val

    stage_h = 1.0
    gap = 0.28
    max_hw = 5.2  # 最宽层的半宽度

    current_y = 0.0
    for i in range(n):
        y_top = current_y
        y_bottom = current_y - stage_h

        top_hw = width_ratios[i] * max_hw
        if i < n - 1:
            bottom_hw = width_ratios[i + 1] * max_hw
        else:
            bottom_hw = top_hw * 0.12  # 末层收尖

        verts = [
            (-top_hw, y_top),
            (top_hw, y_top),
            (bottom_hw, y_bottom),
            (-bottom_hw, y_bottom),
        ]
        poly = Polygon(verts, facecolor=colors[i], edgecolor='white',
                       linewidth=2.5, zorder=3, alpha=0.92)
        ax.add_patch(poly)

        # 层名 + 原始数值标在梯形内部
        mid_y = (y_top + y_bottom) / 2
        inner_text = f'{labels[i]}\n{int(arr[i]):,}'
        ax.text(0, mid_y + 0.08, inner_text, ha='center', va='center',
                fontsize=11, fontweight='bold', color='white', zorder=5)

        # 转化率标在梯形下方（间隙处）
        ax.text(0, y_bottom - gap * 0.35, rate_labels[i], ha='center', va='top',
                fontsize=10, color=C_DARK, zorder=5)

        current_y = y_bottom - gap

    ax.set_xlim(-max_hw * 1.18, max_hw * 1.18)
    ax.set_ylim(current_y - 0.2, stage_h + 0.3)
    ax.axis('off')


# ═══════════════════════════════════════════════════════════
# 00 — 数据清洗漏斗
# ═══════════════════════════════════════════════════════════
def plot_cleaning_funnel(cleaning_stats: dict) -> None:
    fig, ax = plt.subplots(figsize=(12, 5.5))
    steps = list(cleaning_stats.keys())
    values = list(cleaning_stats.values())
    total = values[0]

    palette = ['#3A7CA5', '#5B9BD5', '#4CAF82', '#E8934B', '#D64545']
    colors = [palette[i % len(palette)] for i in range(len(steps))]
    bars = ax.barh(steps, values, height=0.55, color=colors,
                   edgecolor='white', linewidth=1.5, zorder=3)

    for bar, val in zip(bars, values):
        pct = val / total * 100
        dropped = total - val
        if dropped > 0:
            note = f'{val:,}  ({pct:.2f}%)  丢弃 {dropped:,}'
        else:
            note = f'{val:,}  ({pct:.2f}%)'
        ax.text(bar.get_width() + max(values) * 0.008,
                bar.get_y() + bar.get_height() / 2,
                note, va='center', fontsize=11, color=C_DARK)

    ax.set_title('数据清洗流程 — Events 表', fontsize=16, pad=20)
    ax.set_xlabel('保留记录数', fontsize=12, labelpad=10)
    ax.invert_yaxis()
    ax.set_xlim(0, max(values) * 1.25)
    ax.tick_params(left=False)
    fig.tight_layout()
    _save(fig, '00_cleaning_funnel')


# ═══════════════════════════════════════════════════════════
# 01 — 页面覆盖漏斗 (静态梯形)
# ═══════════════════════════════════════════════════════════
def plot_page_funnel(funnel_df: 'pd.DataFrame') -> None:
    labels = PAGE_SHORT_LABELS
    counts = funnel_df['到达会话数'].tolist()
    overall_rates = funnel_df['整体到达率(%)'].tolist()
    rate_col = '交叉到达率(%)' if '交叉到达率(%)' in funnel_df.columns else '上一阶段转化率(%)'
    rates = funnel_df[rate_col].tolist()

    rate_labels = []
    for i, (rate, ovr) in enumerate(zip(rates, overall_rates)):
        if i == 0:
            rate_labels.append(f'整体到达率 {ovr:.1f}%')
        else:
            rate_labels.append(f'交叉到达率 {rate:.1f}% | 整体 {ovr:.1f}%')

    fig, ax = plt.subplots(figsize=(11, 8))
    colors = FUNNEL_PALETTE[:len(labels)]
    _draw_funnel_polygons(ax, labels, counts, rate_labels, colors)

    ax.set_title('页面覆盖漏斗 (Page Coverage Funnel)\n各页面独立到达统计 · 梯形宽度 ∝ 到达会话数',
                 fontsize=15, pad=24, color=C_DARK)
    fig.tight_layout()
    _save(fig, '01_page_funnel')


# ═══════════════════════════════════════════════════════════
# 01b — 严格路径页面漏斗 (静态梯形)
# ═══════════════════════════════════════════════════════════
def plot_strict_page_funnel(strict_df: 'pd.DataFrame') -> None:
    """严格路径漏斗 — 必须按 Home→PLP→PDP→Cart→Checkout 时间顺序访问"""
    labels = PAGE_SHORT_LABELS
    counts = strict_df['严格路径到达会话数'].tolist()
    seq_rates = strict_df['顺序转化率(%)'].tolist()
    retention_rates = strict_df['整体留存率(%)'].tolist()

    rate_labels = []
    for i, (sr, rr) in enumerate(zip(seq_rates, retention_rates)):
        if i == 0:
            rate_labels.append(f'整体留存率 {rr:.1f}%')
        else:
            rate_labels.append(f'顺序转化率 {sr:.1f}% | 留存率 {rr:.1f}%')

    fig, ax = plt.subplots(figsize=(11, 8))
    colors = ['#5B2C6F', '#7D3C98', '#A569BD', '#C39BD3', '#D7BDE2']
    _draw_funnel_polygons(ax, labels, counts, rate_labels, colors, power=0.3)

    ax.set_title('严格路径漏斗 (Strict Path Funnel)\n按时间顺序 Home→PLP→PDP→Cart→Checkout，人数必递减',
                 fontsize=15, pad=24, color=C_DARK)
    fig.tight_layout()
    _save(fig, '01b_strict_page_funnel')


# ═══════════════════════════════════════════════════════════
# 02 — 行为级漏斗 (静态梯形)
# ═══════════════════════════════════════════════════════════
def plot_event_funnel(funnel_df: 'pd.DataFrame') -> None:
    labels = EVENT_SHORT_LABELS
    counts = funnel_df['会话数'].tolist()
    prev_rates = funnel_df['上一阶段转化率(%)'].tolist()
    total_rates = funnel_df['整体转化率(%)'].tolist()

    rate_labels = []
    for i, (pr, tr) in enumerate(zip(prev_rates, total_rates)):
        if i == 0:
            rate_labels.append(f'整体转化率 {tr:.1f}%')
        else:
            rate_labels.append(f'上阶段转化率 {pr:.1f}% | 整体 {tr:.1f}%')

    fig, ax = plt.subplots(figsize=(10, 7.5))
    colors = ['#1B4F72', '#2E86C1', '#5499C7', '#85C1E9']
    _draw_funnel_polygons(ax, labels, counts, rate_labels, colors)

    ax.set_title('行为级转化漏斗 (Event Funnel)\n浏览 → 点击 → 加购 → 购买',
                 fontsize=15, pad=24, color=C_DARK)
    fig.tight_layout()
    _save(fig, '02_event_funnel')


# ═══════════════════════════════════════════════════════════
# 03 — 渠道专属漏斗 (5 面板)
# ═══════════════════════════════════════════════════════════
def plot_channel_funnels(channel_funnels: dict[str, 'pd.DataFrame']) -> None:
    fig = plt.figure(figsize=(22, 13))

    first_df = next(iter(channel_funnels.values()))
    _rate_col = next(
        (c for c in ['交叉到达率(%)', '上一阶段转化率(%)'] if c in first_df.columns),
        '交叉到达率(%)',
    )
    sorted_channels = sorted(channel_funnels.keys(),
                             key=lambda ch: channel_funnels[ch].iloc[-1][_rate_col],
                             reverse=True)

    for i, ch in enumerate(sorted_channels):
        ax = fig.add_subplot(2, 3, i + 1)
        df = channel_funnels[ch]
        full_color = CHANNEL_COLORS_MAP.get(ch, C_BLUE)
        vals = df['到达会话数'].values
        rates_arr = df[_rate_col].values

        # 找瓶颈
        sub_rates = rates_arr[1:]
        bn_idx = sub_rates.argmin() + 1

        # 瓶颈柱用原色，其余用同色系浅色
        bar_colors = []
        bar_alphas = []
        for j in range(len(vals)):
            if j == bn_idx:
                bar_colors.append(full_color)
                bar_alphas.append(1.0)
            else:
                bar_colors.append(full_color)
                bar_alphas.append(0.28)

        bars = []
        for j, (v, bc, ba) in enumerate(zip(vals, bar_colors, bar_alphas)):
            b = ax.barh(PAGE_SHORT_LABELS[j], v, height=0.6, color=bc,
                        edgecolor='white', linewidth=1.2, alpha=ba, zorder=3)
            bars.append(b)

        # 瓶颈柱描边稍微明显
        bars[bn_idx][0].set_edgecolor(full_color)
        bars[bn_idx][0].set_linewidth(2)
        bars[bn_idx][0].set_zorder(5)

        ax.set_title(ch, fontsize=14, fontweight='bold', color=C_DARK, pad=10)
        ax.invert_yaxis()
        ax.tick_params(left=False, bottom=False, labelsize=10)

        max_v = max(vals)
        for j, (bar_patch, val, rate) in enumerate(zip(bars, vals, rates_arr)):
            b = bar_patch[0]
            if rate == 100:
                txt = f'{val:,}'
            else:
                txt = f'{val:,}  [{rate:.1f}%]'
            clr = C_DARK if j == bn_idx else C_GREY
            fw = 'bold' if j == bn_idx else 'normal'
            fs = 10 if j == bn_idx else 9
            ax.text(b.get_width() + max_v * 0.02, b.get_y() + b.get_height() / 2,
                    txt, va='center', fontsize=fs, color=clr, fontweight=fw)

        ax.set_xlim(0, max_v * 1.38)

    fig.delaxes(fig.add_subplot(2, 3, 6))
    fig.suptitle('各渠道专属漏斗对比', fontsize=18, fontweight='bold',
                 color=C_DARK, y=1.02)
    fig.text(0.5, 0.97, '深色柱 = 该渠道瓶颈环节，浅色柱 = 非瓶颈（同色系）',
             fontsize=12, color=C_GREY, ha='center', va='center')
    fig.tight_layout()
    _save(fig, '03_channel_funnels')


# ═══════════════════════════════════════════════════════════
# 04 — 损失瀑布图
# ═══════════════════════════════════════════════════════════
def plot_loss_waterfall(loss_df: 'pd.DataFrame') -> None:
    """瀑布图 — 各环节损失金额级联累积，清晰展示总损失如何逐步累积"""
    fig, ax = plt.subplots(figsize=(13, 8))
    labels = [l.replace(' → ', '→') for l in loss_df['漏斗环节']]
    values = loss_df['估算损失金额'].values / 10000
    n = len(loss_df)
    total_loss = values.sum()
    max_val = values.max()

    # 阶段严重度颜色：最深的给最大单环节损失
    sorted_vals = sorted(values, reverse=True)

    def _severity_color(val):
        rank = sorted_vals.index(val) / max(len(sorted_vals) - 1, 1)
        r = int(232 - rank * (232 - 120))
        g = int(100 - rank * (100 - 50))
        b = int(100 - rank * (100 - 50))
        return f'#{r:02x}{g:02x}{b:02x}'

    bar_colors = [_severity_color(v) for v in values]

    # 瀑布核心：cumulative 跟踪每步累积值
    cumulative = np.zeros(n + 1)
    bottoms = np.zeros(n)

    for i in range(n):
        bottoms[i] = cumulative[i]
        cumulative[i + 1] = cumulative[i] + values[i]

    bars = ax.bar(range(n), values, width=0.55, color=bar_colors,
                  edgecolor='white', linewidth=1.5, alpha=0.92, zorder=3,
                  bottom=bottoms, label='各环节损失')

    # 累积线连接各柱顶
    ax.plot(range(n), cumulative[:-1], 'D-', color=C_BLUE, linewidth=2.2,
            markersize=9, markerfacecolor='white', markeredgecolor=C_BLUE,
            markeredgewidth=2, zorder=5, label='累积损失')

    lost_sessions = loss_df['流失会话数'].values
    churn_rates = loss_df['环节流失率(%)'].values

    for i, (bar, val, lost, rate) in enumerate(
            zip(bars, values, lost_sessions, churn_rates)):
        cx = bar.get_x() + bar.get_width() / 2
        bh = bar.get_height()
        bot = bar.get_y()
        # 金额标在柱顶上方
        ax.text(cx, bot + bh + max_val * 0.012,
                f'¥{val:,.0f}万', ha='center', va='bottom',
                fontsize=12, fontweight='bold', color='#922B21')
        # 流失信息标在柱中
        mid = bot + bh * 0.4
        ax.text(cx, mid,
                f'{lost:,}\n流失{rate:.1f}%',
                ha='center', va='center',
                fontsize=10, color='#2C3E50', fontweight='bold',
                bbox=dict(boxstyle='round,pad=0.2', facecolor='white', alpha=0.82))

    # 总损失标注在最后一根柱子上方
    ax.annotate(
        f'  合计 ¥{total_loss:,.0f}万',
        xy=(n - 1, total_loss),
        xytext=(n - 1, total_loss + max_val * 0.18),
        fontsize=12, color=C_BLUE, fontweight='bold',
        arrowprops=dict(arrowstyle='->', color=C_BLUE, alpha=0.6, lw=1.5),
        ha='center',
    )

    ax.set_xticks(range(n))
    ax.set_xticklabels(labels, fontsize=11)
    ax.set_title('各环节年度损失金额 — 瀑布累积图', fontsize=17, pad=22)
    ax.set_ylabel('损失金额 (万元)', fontsize=12, labelpad=10)
    ax.set_ylim(0, total_loss + max_val * 0.35)
    ax.set_xlim(-0.6, n - 0.4)
    ax.tick_params(left=False, bottom=False)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'{x:,.0f}'))
    ax.legend(fontsize=11, framealpha=0.9, edgecolor=CL_GREY, loc='upper left')
    fig.subplots_adjust(left=0.10, right=0.92, top=0.92, bottom=0.12)
    _save(fig, '04_loss_waterfall')


# ═══════════════════════════════════════════════════════════
# 05 — 渠道 × 设备热力图
# ═══════════════════════════════════════════════════════════
def plot_channel_device_heatmap(cross_df: 'pd.DataFrame') -> None:
    pivot = cross_df.reset_index().pivot_table(
        values='转化率(%)', index='traffic_source', columns='device_type', aggfunc='mean'
    )
    desired = ['mobile', 'desktop', 'tablet']
    pivot = pivot[[c for c in desired if c in pivot.columns]]

    fig, ax = plt.subplots(figsize=(10, 6.5))
    data = pivot.values
    vmin, vmax = data.min(), data.max()

    im = ax.imshow(data, cmap=CMAP_RDYLGN, aspect='auto', vmin=vmin, vmax=vmax)

    mid_val = (vmin + vmax) / 2
    for i in range(len(pivot.index)):
        for j in range(len(pivot.columns)):
            val = data[i, j]
            text_color = 'white' if val < mid_val else C_DARK
            ax.text(j, i, f'{val:.1f}%', ha='center', va='center',
                    fontsize=14, fontweight='bold', color=text_color)

    ax.set_xticks(range(len(pivot.columns)))
    ax.set_xticklabels(DEVICE_CN_LABELS[:len(pivot.columns)], fontsize=12)
    ax.set_yticks(range(len(pivot.index)))
    ax.set_yticklabels(pivot.index, fontsize=12)
    ax.tick_params(left=False, bottom=False)

    cbar = plt.colorbar(im, ax=ax, shrink=0.85, pad=0.02)
    cbar.set_label('转化率 (%)', fontsize=11, labelpad=8)
    cbar.ax.tick_params(labelsize=9)

    ax.set_title('渠道 × 设备 转化率热力图', fontsize=16, pad=18)
    fig.tight_layout()
    _save(fig, '05_channel_device_heatmap')


# ═══════════════════════════════════════════════════════════
# 06 — 多维度转化率对比
# ═══════════════════════════════════════════════════════════
def plot_dimension_comparison(channel_df: 'pd.DataFrame', device_df: 'pd.DataFrame',
                               loyalty_df: 'pd.DataFrame') -> None:
    fig, axes = plt.subplots(1, 3, figsize=(20, 6.5))
    configs = [
        (axes[0], channel_df, '按渠道'),
        (axes[1], device_df, '按设备'),
        (axes[2], loyalty_df, '按忠诚度'),
    ]

    for ax, df, title in configs:
        vals = df['转化率(%)'].values
        labels = df.index.tolist()
        is_max = vals == vals.max()

        colors_bar = []
        for m in is_max:
            if m:
                colors_bar.append(C_BLUE)
            else:
                colors_bar.append(CL_GREY)

        bars = ax.barh(labels, vals, height=0.55, color=colors_bar,
                       edgecolor='white', linewidth=1.2, zorder=3)
        ax.set_title(title, fontsize=14, fontweight='bold', color=C_DARK, pad=12)
        ax.invert_yaxis()
        ax.tick_params(left=False, bottom=False)

        for bar, val, mx in zip(bars, vals, is_max):
            color = C_BLUE if mx else C_GREY
            ax.text(bar.get_width() + max(vals) * 0.02,
                    bar.get_y() + bar.get_height() / 2,
                    f'{val:.1f}%', va='center',
                    fontsize=13 if mx else 11,
                    fontweight='bold' if mx else 'normal', color=color)

        ax.set_xlim(0, max(vals) * 1.22)

    fig.suptitle('多维度转化率对比', fontsize=18, fontweight='bold',
                 color=C_DARK, y=1.03)
    fig.tight_layout()
    _save(fig, '06_dimension_comparison')


# ═══════════════════════════════════════════════════════════
# 07 — 月度趋势
# ═══════════════════════════════════════════════════════════
def plot_trend(monthly_df: 'pd.DataFrame') -> None:
    fig, ax = plt.subplots(figsize=(16, 6.5))
    x = range(len(monthly_df))
    labels = monthly_df['日期'].tolist()
    values = monthly_df['转化率(%)'].values

    ax.fill_between(x, values, alpha=0.08, color=C_BLUE)
    ax.plot(x, values, color=C_BLUE, linewidth=2.5, marker='o', markersize=3.5,
            markerfacecolor='white', markeredgecolor=C_BLUE, markeredgewidth=1, zorder=4)

    year_config = [(2021, '--', C_RED), (2022, '-.', C_ORANGE), (2023, ':', C_PURPLE)]
    for y, ls, color in year_config:
        y_data = monthly_df[monthly_df['日期'].str.startswith(str(y))]
        if len(y_data) == 0:
            continue
        avg = y_data['转化率(%)'].mean()
        ax.axhline(y=avg, linestyle=ls, color=color, alpha=0.6, linewidth=1.8, zorder=3)
        right_x = monthly_df[monthly_df['日期'].str.startswith(str(y))].index.max()
        ax.annotate(f'{y}年均 {avg:.1f}%', xy=(right_x, avg),
                    xytext=(right_x + 1.5, avg + 0.25),
                    fontsize=10, color=color, fontweight='bold',
                    arrowprops=dict(arrowstyle='-', color=color, alpha=0.4, lw=1))

    tick_indices = [i for i, lbl in enumerate(labels)
                    if lbl.endswith('-01') or lbl.endswith('-04')
                    or lbl.endswith('-07') or lbl.endswith('-10')]
    ax.set_xticks(tick_indices)
    ax.set_xticklabels([labels[i] for i in tick_indices], rotation=45, ha='right', fontsize=9)
    ax.set_ylabel('转化率 (%)', fontsize=12, labelpad=10)
    ax.set_title('月度转化率趋势 (2021–2023)', fontsize=17, pad=18)
    ax.set_ylim(0, max(values) * 1.15)
    ax.tick_params(left=False, bottom=False)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f'{v:.0f}%'))
    fig.tight_layout()
    _save(fig, '07_monthly_trend')


# ═══════════════════════════════════════════════════════════
# 08 — 停留时长 vs 转化率
# ═══════════════════════════════════════════════════════════
def plot_duration_conversion(duration_df: 'pd.DataFrame') -> None:
    fig, ax = plt.subplots(figsize=(12, 6.5))
    labels = duration_df.index.tolist()
    values = duration_df['会话数'].values
    rates = duration_df['转化率(%)'].values

    bars = ax.bar(labels, values, width=0.55, color=DURATION_COLORS,
                  edgecolor='white', linewidth=1.5, alpha=0.88, zorder=3)
    ax2 = ax.twinx()
    ax2.plot(labels, rates, 'D-', color=C_RED, linewidth=2.8, markersize=12,
             markerfacecolor='white', markeredgecolor=C_RED, markeredgewidth=2, zorder=5)

    for bar, val in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width() / 2,
                bar.get_height() + max(values) * 0.015,
                f'{val:,}', ha='center', fontsize=12, fontweight='bold', color=C_DARK)
    for i, rate in enumerate(rates):
        ax2.text(i, rate + max(rates) * 0.03, f'{rate:.1f}%',
                 ha='center', fontsize=12, fontweight='bold', color=C_RED)

    ax.set_title('停留时长 vs 转化率', fontsize=16, pad=18)
    ax.set_ylabel('会话数', fontsize=12, labelpad=10)
    ax2.set_ylabel('转化率 (%)', fontsize=12, color=C_RED, labelpad=10)
    ax2.tick_params(axis='y', colors=C_RED)
    ax2.spines['right'].set_visible(True)
    ax2.spines['right'].set_color(C_RED)
    ax2.spines['right'].set_alpha(0.25)
    ax.tick_params(left=False, bottom=False)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f'{v/1000:.0f}K'))
    fig.tight_layout()
    _save(fig, '08_duration_conversion')


# ═══════════════════════════════════════════════════════════
# 09 — 渠道 × 流失环节
# ═══════════════════════════════════════════════════════════
def plot_churn_by_channel(churn_matrix: 'pd.DataFrame') -> None:
    pivot = churn_matrix.pivot_table(
        values='流失率(%)', index='渠道', columns='流失环节', aggfunc='mean'
    )
    fig, ax = plt.subplots(figsize=(13, 6.5))
    pivot.plot(kind='barh', ax=ax, color=STAGE_COLORS, edgecolor='white',
               linewidth=1, width=0.75, zorder=3)

    ax.set_title('各渠道 × 各环节流失率', fontsize=16, pad=18)
    ax.set_xlabel('流失率 (%)', fontsize=12, labelpad=10)
    ax.legend(loc='lower right', fontsize=10, title='流失环节',
              title_fontsize=11, framealpha=0.9, edgecolor=CL_GREY)
    ax.invert_yaxis()
    ax.tick_params(left=False, bottom=False)
    ax.set_xlim(0, pivot.values.max() * 1.20)
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f'{v:.0f}%'))
    for container in ax.containers:
        ax.bar_label(container, fmt='%.1f%%', label_type='edge',
                     fontsize=9, padding=4, color=C_DARK)
    fig.tight_layout()
    _save(fig, '09_churn_by_channel')


# ═══════════════════════════════════════════════════════════
# 10 — PIE 优先级矩阵
# ═══════════════════════════════════════════════════════════
def plot_pie_matrix(pie_df: 'pd.DataFrame') -> None:
    """PIE 优先级矩阵 — 气泡图 (X=Potential, Y=Importance, 大小=PIE)"""
    fig, ax = plt.subplots(figsize=(10, 7))
    x = pie_df['Potential'].values
    y = pie_df['Importance'].values
    sizes = pie_df['PIE得分'].values * 5
    pie_labels = [l.replace(' → ', '→') for l in pie_df['漏斗环节']]
    pie_scores = pie_df['PIE得分'].values.astype(int)
    ease_vals = pie_df['Ease'].values.astype(int)

    ax.scatter(x, y, s=sizes, c=C_BLUE, alpha=0.65,
               edgecolors=C_DARK, linewidth=1.0, zorder=4)

    for rank, (xi, yi, label, score, e) in enumerate(zip(x, y, pie_labels, pie_scores, ease_vals), 1):
        ax.annotate(f'#{rank} {label}\nPIE={score} (Ease={e})',
                    (xi, yi), textcoords='offset points', xytext=(0, 12),
                    ha='center', fontsize=9, fontweight='bold', color=C_DARK)

    # 象限分割线
    ax.axhline(y=5, color=C_GREY, linestyle=':', alpha=0.4, zorder=1)
    ax.axvline(x=5, color=C_GREY, linestyle=':', alpha=0.4, zorder=1)
    ax.text(10, 10.5, '优先投入', ha='right', fontsize=9, color=C_GREY, alpha=0.6)
    ax.text(0.5, 0.5, '暂缓', ha='left', fontsize=9, color=C_GREY, alpha=0.6)

    ax.set_xlabel('损失潜力 (Potential)', fontsize=12)
    ax.set_ylabel('流量重要性 (Importance)', fontsize=12)
    ax.set_title('PIE 优先级矩阵', fontsize=15, pad=14)
    ax.set_xlim(0, 11)
    ax.set_ylim(0, 11)
    ax.tick_params(left=False, bottom=False)
    fig.tight_layout()
    _save(fig, '10_pie_matrix')


# ═══════════════════════════════════════════════════════════
# 11 — 品类双阶段转化率
# ═══════════════════════════════════════════════════════════
def plot_category_funnel(cat_df: 'pd.DataFrame') -> None:
    fig, ax = plt.subplots(figsize=(13, 6.5))
    x_labels = cat_df['category'].tolist()
    x_pos = np.arange(len(x_labels))
    width = 0.32

    bars1 = ax.bar(x_pos - width / 2, cat_df['浏览→加购(%)'].values,
                   width, label='浏览 → 加购',
                   color='#5B9BD5', edgecolor='white', linewidth=1.2, alpha=0.9, zorder=3)
    bars2 = ax.bar(x_pos + width / 2, cat_df['加购→购买(%)'].values,
                   width, label='加购 → 购买',
                   color='#4CAF82', edgecolor='white', linewidth=1.2, alpha=0.9, zorder=3)

    for bar, val in zip(bars1, cat_df['浏览→加购(%)'].values):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.3,
                f'{val:.1f}%', ha='center', fontsize=9.5, fontweight='bold', color='#2C6296')
    for bar, val in zip(bars2, cat_df['加购→购买(%)'].values):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.3,
                f'{val:.1f}%', ha='center', fontsize=9.5, fontweight='bold', color='#2D7A4A')

    ax.set_xticks(x_pos)
    ax.set_xticklabels(x_labels, fontsize=11)
    ax.set_title('各品类双阶段转化率对比', fontsize=16, pad=18)
    ax.set_ylabel('转化率 (%)', fontsize=12, labelpad=10)
    ax.legend(fontsize=11, framealpha=0.9, edgecolor=CL_GREY)
    ax.set_ylim(0, max(cat_df[['浏览→加购(%)', '加购→购买(%)']].max()) * 1.25)
    ax.tick_params(left=False, bottom=False)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f'{v:.0f}%'))
    fig.tight_layout()
    _save(fig, '11_category_funnel')


# ═══════════════════════════════════════════════════════════
# 12 — 严格漏斗 vs 覆盖分析 对比
# ═══════════════════════════════════════════════════════════
def plot_strict_vs_coverage(strict_df: 'pd.DataFrame') -> None:
    """严格路径漏斗 vs 页面覆盖分析 双柱对比

    两种方法的本质区别:
    - 页面覆盖 (宽松): 只要访问过该页面即计入, 独立统计各页面, 允许多入口/深链
    - 严格路径 (顺序): 必须按 Home→PLP→PDP→Cart→Checkout 时间顺序访问, 人数必递减
    """
    fig, ax = plt.subplots(figsize=(13, 7))
    x_pos = np.arange(len(PAGE_SHORT_LABELS))
    width = 0.32

    strict_vals = strict_df['严格路径到达会话数'].values
    coverage_vals = strict_df['覆盖到达会话数'].values

    bars1 = ax.bar(
        x_pos - width / 2, coverage_vals, width,
        label='页面覆盖 (宽松) — 各页面独立统计', color='#A0AAB5', edgecolor='white',
        linewidth=1.2, alpha=0.85, zorder=3,
    )
    bars2 = ax.bar(
        x_pos + width / 2, strict_vals, width,
        label='严格路径 (顺序) — 按时间顺序访问', color='#3A7CA5', edgecolor='white',
        linewidth=1.2, alpha=0.9, zorder=3,
    )

    for bar, val in zip(bars1, coverage_vals):
        ax.text(
            bar.get_x() + bar.get_width() / 2, bar.get_height() + max(coverage_vals) * 0.01,
            f'{val:,}', ha='center', fontsize=9, color=C_GREY,
        )
    for bar, val in zip(bars2, strict_vals):
        ax.text(
            bar.get_x() + bar.get_width() / 2, bar.get_height() + max(coverage_vals) * 0.01,
            f'{val:,}', ha='center', fontsize=9, fontweight='bold', color=C_BLUE,
        )

    # 标注差异 (深链流量)
    diffs = strict_df['覆盖-严格差异'].values
    for i, diff in enumerate(diffs):
        ax.text(
            i, max(coverage_vals) * 0.55,
            f'深链 Δ{diff:,}', ha='center', fontsize=9.5,
            color=C_RED, fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.2', facecolor='white',
                      edgecolor=CL_RED, alpha=0.8),
        )

    ax.set_xticks(x_pos)
    ax.set_xticklabels(PAGE_SHORT_LABELS, fontsize=11)
    ax.set_title(
        '严格路径漏斗 vs 页面覆盖分析\n'
        '覆盖分析允许深链多入口 (下游可超上游), 严格路径人数必递减',
        fontsize=14, pad=18,
    )
    ax.set_ylabel('会话数', fontsize=12, labelpad=10)
    ax.legend(fontsize=10, framealpha=0.9, edgecolor=CL_GREY)
    ax.tick_params(left=False, bottom=False)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f'{v/1000:.0f}K'))
    fig.tight_layout()
    _save(fig, '12_strict_vs_coverage')


# ═══════════════════════════════════════════════════════════
# 13 — 深链 vs 首页路径 转化率对比
# ═══════════════════════════════════════════════════════════
def plot_deep_link_comparison(path_summary: 'pd.DataFrame',
                              channel_comparison: 'pd.DataFrame') -> None:
    """深链流量 vs 首页路径 转化率对比（双图）"""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(20, 7))

    # 左图：路径类型概览
    plot_types = ['首页→PLP', '深链直达PLP', '仅首页', '其他']
    type_colors = ['#4CAF82', '#E8934B', '#5B9BD5', '#A0AAB5']
    vals = []
    clrs = []
    lbls = []
    for t, c in zip(plot_types, type_colors):
        if t in path_summary.index:
            vals.append(path_summary.loc[t, '会话数'])
            clrs.append(c)
            lbls.append(t)

    bars = ax1.barh(lbls, vals, height=0.5, color=clrs,
                    edgecolor='white', linewidth=1.2, zorder=3)
    ax1.invert_yaxis()
    ax1.set_title('用户路径类型分布', fontsize=14, fontweight='bold', pad=12)
    ax1.tick_params(left=False, bottom=False)
    max_v = max(vals) if vals else 1
    for bar, val, lbl in zip(bars, vals, lbls):
        rate = path_summary.loc[lbl, '转化率(%)']
        ax1.text(bar.get_width() + max_v * 0.02, bar.get_y() + bar.get_height() / 2,
                 f'{val:,} 会话  |  转化率 {rate:.1f}%',
                 va='center', fontsize=11, color=C_DARK)
    ax1.set_xlim(0, max_v * 1.55)
    ax1.xaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f'{v/1000:.0f}K'))

    # 右图：分渠道深链 vs 首页路径 转化率
    channels = channel_comparison.index.tolist()
    x = np.arange(len(channels))
    w = 0.3

    deep_rates = channel_comparison['深链转化率(%)'].values
    home_rates = channel_comparison['首页路径转化率(%)'].values
    diffs = channel_comparison['转化率差异(pp)'].values

    ax2.bar(x - w / 2, deep_rates, w, label='深链直达PLP',
            color='#E8934B', edgecolor='white', linewidth=1, alpha=0.88, zorder=3)
    ax2.bar(x + w / 2, home_rates, w, label='首页→PLP',
            color='#4CAF82', edgecolor='white', linewidth=1, alpha=0.88, zorder=3)

    # 差异标注
    for i, diff in enumerate(diffs):
        y = max(deep_rates[i], home_rates[i])
        symbol = '↑' if diff > 0 else '↓' if diff < 0 else '='
        ax2.text(i, y + max(max(deep_rates), max(home_rates)) * 0.03,
                 f'{symbol}{abs(diff):.1f}pp',
                 ha='center', fontsize=10, fontweight='bold',
                 color=C_RED if diff > 1 else C_DARK)

    ax2.set_xticks(x)
    ax2.set_xticklabels(channels, fontsize=10)
    ax2.set_title('分渠道：深链 vs 首页路径 转化率', fontsize=14, fontweight='bold', pad=12)
    ax2.set_ylabel('转化率 (%)', fontsize=12, labelpad=10)
    ax2.legend(fontsize=10, framealpha=0.9, edgecolor=CL_GREY)
    ax2.tick_params(left=False, bottom=False)
    ax2.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f'{v:.0f}%'))
    ax2.set_ylim(0, max(max(deep_rates), max(home_rates)) * 1.25)

    fig.suptitle('深链流量分析', fontsize=18, fontweight='bold', color=C_DARK, y=1.02)
    fig.tight_layout()
    _save(fig, '13_deep_link_analysis')


# ═══════════════════════════════════════════════════════════
# 14 — 新用户 vs 老用户 漏斗对比
# ═══════════════════════════════════════════════════════════
def plot_new_vs_returning(nr_results: dict) -> None:
    """新用户 vs 老用户 页面+行为漏斗 四象限对比"""
    fig, axes = plt.subplots(2, 2, figsize=(20, 14))

    titles = [
        ('新用户(未购买)_page', '新用户(未购买)_event',
         '新用户（未购买过）', '#E8934B'),
        ('老用户(已购买)_page', '老用户(已购买)_event',
         '老用户（已购买过）', '#4CAF82'),
    ]

    for row_idx, (page_key, event_key, group_title, color) in enumerate(titles):
        # 左：页面漏斗
        ax_page = axes[row_idx, 0]
        page_df = nr_results[page_key]
        page_vals = page_df['到达会话数'].values
        bars = ax_page.barh(
            PAGE_SHORT_LABELS, page_vals, height=0.55, color=color,
            edgecolor='white', linewidth=1.2, alpha=0.88, zorder=3,
        )
        ax_page.invert_yaxis()
        ax_page.set_title(f'{group_title} — 页面漏斗', fontsize=13, fontweight='bold', pad=10)
        ax_page.tick_params(left=False)
        max_v = max(page_vals)
        for bar, (_, row) in zip(bars, page_df.iterrows()):
            rate_val = row.get('交叉到达率(%)', row.get('上一阶段转化率(%)', 0))
            ax_page.text(
                bar.get_width() + max_v * 0.02,
                bar.get_y() + bar.get_height() / 2,
                f'{int(row["到达会话数"]):,}  [{rate_val:.1f}%]',
                va='center', fontsize=9, color=C_DARK,
            )
        ax_page.set_xlim(0, max_v * 1.4)

        # 右：行为漏斗
        ax_event = axes[row_idx, 1]
        event_df = nr_results[event_key]
        event_vals = event_df['会话数'].values
        bars2 = ax_event.barh(
            EVENT_SHORT_LABELS, event_vals, height=0.55, color=color,
            edgecolor='white', linewidth=1.2, alpha=0.88, zorder=3,
        )
        ax_event.invert_yaxis()
        ax_event.set_title(f'{group_title} — 行为漏斗', fontsize=13, fontweight='bold', pad=10)
        ax_event.tick_params(left=False)
        max_v2 = max(event_vals)
        for bar, (_, row) in zip(bars2, event_df.iterrows()):
            ax_event.text(
                bar.get_width() + max_v2 * 0.02,
                bar.get_y() + bar.get_height() / 2,
                f'{int(row["会话数"]):,}  [{row["上一阶段转化率(%)"]:.1f}%]',
                va='center', fontsize=9, color=C_DARK,
            )
        ax_event.set_xlim(0, max_v2 * 1.4)

    fig.suptitle(
        '新用户 vs 老用户 漏斗对比 — 转化模式有何不同？',
        fontsize=17, fontweight='bold', color=C_DARK, y=1.01,
    )
    fig.tight_layout()
    _save(fig, '14_new_vs_returning')


# ═══════════════════════════════════════════════════════════
# 15 — 周末 vs 工作日 转化率对比
# ═══════════════════════════════════════════════════════════
def plot_weekend_comparison(weekend_df: 'pd.DataFrame') -> None:
    """周末 vs 工作日 关键指标对比"""
    fig, axes = plt.subplots(1, 3, figsize=(18, 5.5))

    configs = [
        (0, '会话数', '会话量', 'K'),
        (1, 'CR(%)', '会话转化率', '%'),
        (2, '加购→购买(%)', '加购→购买率', '%'),
    ]

    for idx, col, title, unit in configs:
        ax = axes[idx]
        vals = weekend_df[col].values
        labels = weekend_df.index.tolist()
        colors = ['#5B9BD5', '#E8934B']

        bars = ax.bar(
            labels, vals, width=0.4, color=colors,
            edgecolor='white', linewidth=1.5, zorder=3,
        )
        ax.set_title(title, fontsize=13, fontweight='bold', pad=10)
        ax.tick_params(left=False, bottom=False)

        for bar, val in zip(bars, vals):
            if unit == 'K':
                label = f'{val/1000:.0f}K'
            else:
                label = f'{val:.1f}{unit}'
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + max(vals) * 0.02,
                label, ha='center', fontsize=12, fontweight='bold', color=C_DARK,
            )
        ax.set_ylim(0, max(vals) * 1.2)

    fig.suptitle(
        '周末 vs 工作日 核心指标对比',
        fontsize=16, fontweight='bold', color=C_DARK, y=1.02,
    )
    fig.tight_layout()
    _save(fig, '15_weekend_comparison')


# ═══════════════════════════════════════════════════════════
# 16 — Cohort 留存热力图
# ═══════════════════════════════════════════════════════════
def plot_cohort_heatmap(retention_matrix: 'pd.DataFrame') -> None:
    """Cohort 留存热力图 — 行=首次购买月份, 列=月差, 值=留存率(%)"""
    if retention_matrix.empty:
        logger.info("  Cohort 留存矩阵为空, 跳过图表")
        return

    # 取最近 12 个 cohort，最多 12 个 period
    plot_data = retention_matrix.tail(12)
    max_periods = min(12, plot_data.shape[1])
    plot_data = plot_data.iloc[:, :max_periods]
    data = plot_data.values
    rows, cols = data.shape

    fig, ax = plt.subplots(figsize=(min(14, cols * 1.1 + 3), min(8, rows * 0.5 + 2)))

    im = ax.imshow(data, cmap=CMAP_RETENTION, aspect='auto', vmin=0, vmax=100)

    for i in range(rows):
        for j in range(cols):
            val = data[i, j]
            if not np.isnan(val) and val > 0:
                text_color = 'white' if val > 65 else C_DARK
                ax.text(j, i, f'{val:.1f}%', ha='center', va='center',
                        fontsize=9, fontweight='bold', color=text_color)

    ax.set_xticks(range(cols))
    ax.set_xticklabels([f'M+{j}' if j > 0 else 'M0' for j in range(cols)],
                       fontsize=10)
    ax.set_yticks(range(rows))
    ax.set_yticklabels([str(idx) for idx in plot_data.index], fontsize=10)
    ax.tick_params(left=False, bottom=False)

    cbar = plt.colorbar(im, ax=ax, shrink=0.85, pad=0.02)
    cbar.set_label('留存率 (%)', fontsize=11, labelpad=8)

    ax.set_title('Cohort 留存分析 — 首购后月度回购率', fontsize=16, pad=18)
    ax.set_xlabel('距首次购买的月数', fontsize=12, labelpad=10)
    ax.set_ylabel('首次购买月份 (Cohort)', fontsize=12, labelpad=10)
    fig.tight_layout()
    _save(fig, '16_cohort_heatmap')


def plot_visit_cohort_heatmap(retention_matrix: 'pd.DataFrame') -> None:
    """访问留存 Cohort 热力图 — 行=首次访问月份, 列=月差, 值=回访留存率(%)"""
    if retention_matrix.empty:
        logger.info("  访问留存 Cohort 矩阵为空, 跳过图表")
        return

    plot_data = retention_matrix.tail(12)
    max_periods = min(12, plot_data.shape[1])
    plot_data = plot_data.iloc[:, :max_periods]
    data = plot_data.values
    rows, cols = data.shape

    fig, ax = plt.subplots(figsize=(min(14, cols * 1.1 + 3), min(8, rows * 0.5 + 2)))

    im = ax.imshow(data, cmap=CMAP_RETENTION, aspect='auto', vmin=0, vmax=100)

    for i in range(rows):
        for j in range(cols):
            val = data[i, j]
            if not np.isnan(val) and val > 0:
                text_color = 'white' if val > 65 else C_DARK
                ax.text(j, i, f'{val:.1f}%', ha='center', va='center',
                        fontsize=9, fontweight='bold', color=text_color)

    ax.set_xticks(range(cols))
    ax.set_xticklabels([f'M+{j}' if j > 0 else 'M0' for j in range(cols)],
                       fontsize=10)
    ax.set_yticks(range(rows))
    ax.set_yticklabels([str(idx) for idx in plot_data.index], fontsize=10)
    ax.tick_params(left=False, bottom=False)

    cbar = plt.colorbar(im, ax=ax, shrink=0.85, pad=0.02)
    cbar.set_label('回访率 (%)', fontsize=11, labelpad=8)

    ax.set_title('Cohort 留存分析 — 首次访问后月度回访率', fontsize=16, pad=18)
    ax.set_xlabel('距首次访问的月数', fontsize=12, labelpad=10)
    ax.set_ylabel('首次访问月份 (Cohort)', fontsize=12, labelpad=10)
    fig.tight_layout()
    _save(fig, '16b_visit_cohort_heatmap')


# ═══════════════════════════════════════════════════════════
# 交互式漏斗图 (plotly)
# ═══════════════════════════════════════════════════════════

def plot_page_funnel_interactive(funnel_df: 'pd.DataFrame') -> None:
    """页面覆盖漏斗 — 交互式 plotly 版本，保存为 HTML"""
    import plotly.graph_objects as go
    from datetime import date

    labels = PAGE_SHORT_LABELS
    values = funnel_df['到达会话数'].tolist()
    rate_col = '交叉到达率(%)' if '交叉到达率(%)' in funnel_df.columns else '上一阶段转化率(%)'
    rates = funnel_df[rate_col].tolist()
    overall_rates = funnel_df['整体到达率(%)'].tolist()
    n_sessions = _CHART_META.get('n_sessions', 0)
    first_val = values[0]

    # 瓶颈环节
    if len(rates) > 1:
        bottleneck_idx = rates[1:].index(min(rates[1:])) + 1
    else:
        bottleneck_idx = None

    # 构建每条信息
    inside_text = []
    customdata = []  # [percentInitial, percentPrevious, overallRate]
    for i, (v, rate, ovr) in enumerate(zip(values, rates, overall_rates)):
        pi = v / first_val * 100
        pp = 100.0 if i == 0 else rate
        customdata.append([round(pi, 1), round(pp, 1), ovr])
        if i == 0:
            inside_text.append(f'<b>{v:,}</b> 会话<br>到达率 {ovr:.1f}%')
        else:
            inside_text.append(
                f'<b>{v:,}</b> 会话<br>交叉到达 {rate:.1f}% | 整体 {ovr:.1f}%'
            )

    hovertemplate = (
        '<b>%{y}</b><br>'
        '会话数: <b>%{x:,}</b><br>'
        '占首页比例: %{customdata[0]:.1f}%<br>'
        '占上层比例: %{customdata[1]:.1f}%<br>'
        '整体到达率: %{customdata[2]:.1f}%'
        '<extra></extra>'
    )

    # 渐变蓝绿色板
    colors = ['#0B3D3D', '#146B5A', '#1D9778', '#3EBF9C', '#7ED8C2']

    fig = go.Figure(go.Funnel(
        y=labels,
        x=values,
        text=inside_text,
        textinfo='text',
        textposition='inside',
        textfont={'size': 14, 'color': 'white', 'family': 'Microsoft YaHei'},
        customdata=customdata,
        hovertemplate=hovertemplate,
        marker={
            'color': colors[:len(labels)],
            'line': {'color': 'rgba(255,255,255,0.65)', 'width': 2.5},
        },
        connector={
            'line': {'color': 'rgba(11,61,61,0.12)', 'width': 1.6, 'dash': 'solid'},
        },
        outsidetextfont={'size': 12, 'color': '#555'},
    ))

    annotations = []
    if bottleneck_idx is not None:
        annotations.append(dict(
            x=0.5, y=0.0,
            xref='paper', yref='paper',
            text=(
                f'<b>最大断点</b>:  {labels[bottleneck_idx]}'
                f'  →  交叉到达率仅 <b>{rates[bottleneck_idx]:.1f}%</b>'
            ),
            showarrow=False,
            font={'size': 14, 'color': '#C0392B', 'family': 'Microsoft YaHei'},
            bgcolor='rgba(255,245,245,0.92)',
            borderpad=12,
            bordercolor='#E8C4C4',
            borderwidth=1,
        ))

    footnote = (
        f'ecommerce_funnel_analysis  |  n = {n_sessions:,} sessions  |  '
        f'{date.today().isoformat()}'
    )

    fig.update_layout(
        title={
            'text': '<b>页面覆盖漏斗</b>  ·  Page Coverage Funnel',
            'font': {'size': 24, 'color': '#1a1a2e', 'family': 'Microsoft YaHei'},
            'x': 0.5, 'xanchor': 'center',
        },
        annotations=annotations,
        width=980, height=700,
        margin={'t': 100, 'b': 70, 'l': 80, 'r': 80},
        paper_bgcolor='#F8F9FA',
        plot_bgcolor='rgba(0,0,0,0)',
        font={'family': 'Microsoft YaHei, SimHei, sans-serif'},
    )

    fig.add_annotation(
        text=footnote,
        x=0.5, y=-0.05,
        xref='paper', yref='paper',
        showarrow=False,
        font={'size': 10, 'color': '#AAA'},
    )

    html_path = str(CHART_DIR / '01_page_funnel.html')
    fig.write_html(html_path, include_plotlyjs=True)
    logger.info("  Saved: %s", (CHART_DIR / '01_page_funnel.html').name)


def plot_strict_page_funnel_interactive(strict_df: 'pd.DataFrame') -> None:
    """严格路径漏斗 — 交互式 plotly 版本，保存为 HTML"""
    import plotly.graph_objects as go
    from datetime import date

    labels = PAGE_SHORT_LABELS
    real_values = strict_df['严格路径到达会话数'].tolist()
    seq_rates = strict_df['顺序转化率(%)'].tolist()
    retention_rates = strict_df['整体留存率(%)'].tolist()
    n_sessions = _CHART_META.get('n_sessions', 0)
    first_val = real_values[0]

    # 幂律压缩视觉宽度：末层 73 相对 300K 仅 0.02%，0.3 次方后约 10%
    arr = np.array(real_values, dtype=float)
    display_x = np.power(arr, 0.3).tolist()

    # 最大流失环节
    if len(seq_rates) > 1:
        bottleneck_idx = seq_rates[1:].index(min(seq_rates[1:])) + 1
    else:
        bottleneck_idx = None

    inside_text = []
    customdata = []  # [realValue, percentInitial, percentPrevious, retentionRate]
    for i, (v, sr, rr) in enumerate(zip(real_values, seq_rates, retention_rates)):
        pi = v / first_val * 100
        pp = 100.0 if i == 0 else sr
        customdata.append([v, round(pi, 1), round(pp, 1), rr])
        if i == 0:
            inside_text.append(f'<b>{v:,}</b> 会话<br>留存率 {rr:.1f}%')
        else:
            inside_text.append(
                f'<b>{v:,}</b> 会话<br>顺序转化 {sr:.1f}% | 留存 {rr:.1f}%'
            )

    hovertemplate = (
        '<b>%{y}</b><br>'
        '会话数: <b>%{customdata[0]:,}</b><br>'
        '占首页比例: %{customdata[1]:.1f}%<br>'
        '占上层比例: %{customdata[2]:.1f}%<br>'
        '整体留存率: %{customdata[3]:.1f}%'
        '<extra></extra>'
    )

    colors = ['#5B2C6F', '#7D3C98', '#A569BD', '#C39BD3', '#D7BDE2']

    fig = go.Figure(go.Funnel(
        y=labels,
        x=display_x,
        text=inside_text,
        textinfo='text',
        textposition='inside',
        textfont={'size': 14, 'color': 'white', 'family': 'Microsoft YaHei'},
        customdata=customdata,
        hovertemplate=hovertemplate,
        marker={
            'color': colors,
            'line': {'color': 'rgba(255,255,255,0.65)', 'width': 2.5},
        },
        connector={
            'line': {'color': 'rgba(91,44,111,0.12)', 'width': 1.6, 'dash': 'solid'},
        },
        outsidetextfont={'size': 12, 'color': '#555'},
    ))

    annotations = []
    if bottleneck_idx is not None:
        annotations.append(dict(
            x=0.5, y=0.0,
            xref='paper', yref='paper',
            text=(
                f'<b>最大流失</b>:  {labels[bottleneck_idx - 1]} → {labels[bottleneck_idx]}'
                f'  转化率仅 <b>{seq_rates[bottleneck_idx]:.1f}%</b>'
            ),
            showarrow=False,
            font={'size': 14, 'color': '#C0392B', 'family': 'Microsoft YaHei'},
            bgcolor='rgba(255,245,245,0.92)',
            borderpad=12,
            bordercolor='#E8C4C4',
            borderwidth=1,
        ))

    footnote = (
        f'ecommerce_funnel_analysis  |  n = {n_sessions:,} sessions  |  '
        f'{date.today().isoformat()}'
    )

    fig.update_layout(
        title={
            'text': '<b>严格路径漏斗</b>  ·  Strict Path Funnel',
            'font': {'size': 24, 'color': '#1a1a2e', 'family': 'Microsoft YaHei'},
            'x': 0.5, 'xanchor': 'center',
        },
        annotations=annotations,
        width=980, height=700,
        margin={'t': 100, 'b': 70, 'l': 80, 'r': 80},
        paper_bgcolor='#F8F9FA',
        plot_bgcolor='rgba(0,0,0,0)',
        font={'family': 'Microsoft YaHei, SimHei, sans-serif'},
    )

    fig.add_annotation(
        text=footnote,
        x=0.5, y=-0.05,
        xref='paper', yref='paper',
        showarrow=False,
        font={'size': 10, 'color': '#AAA'},
    )

    html_path = str(CHART_DIR / '01b_strict_page_funnel.html')
    fig.write_html(html_path, include_plotlyjs=True)
    logger.info("  Saved: %s", (CHART_DIR / '01b_strict_page_funnel.html').name)


def plot_event_funnel_interactive(funnel_df: 'pd.DataFrame') -> None:
    """行为级漏斗 — 交互式 plotly 版本，保存为 HTML"""
    import plotly.graph_objects as go
    from datetime import date

    labels = EVENT_SHORT_LABELS
    values = funnel_df['会话数'].tolist()
    prev_rates = funnel_df['上一阶段转化率(%)'].tolist()
    total_rates = funnel_df['整体转化率(%)'].tolist()
    n_sessions = _CHART_META.get('n_sessions', 0)
    first_val = values[0]

    # 最大流失环节
    if len(prev_rates) > 1:
        bottleneck_idx = prev_rates[1:].index(min(prev_rates[1:])) + 1
    else:
        bottleneck_idx = None

    inside_text = []
    customdata = []  # [percentInitial, percentPrevious, totalRate]
    for i, (v, pr, tr) in enumerate(zip(values, prev_rates, total_rates)):
        pi = v / first_val * 100
        pp = 100.0 if i == 0 else pr
        customdata.append([round(pi, 1), round(pp, 1), tr])
        if i == 0:
            inside_text.append(f'<b>{v:,}</b> 会话<br>整体转化 {tr:.1f}%')
        else:
            inside_text.append(
                f'<b>{v:,}</b> 会话<br>阶段转化 {pr:.1f}% | 整体 {tr:.1f}%'
            )

    hovertemplate = (
        '<b>%{y}</b><br>'
        '会话数: <b>%{x:,}</b><br>'
        '占初始: %{customdata[0]:.1f}%<br>'
        '占上层: %{customdata[1]:.1f}%<br>'
        '整体转化率: %{customdata[2]:.1f}%'
        '<extra></extra>'
    )

    colors = ['#1A3A4A', '#2C5F7C', '#4682A8', '#6BA5C7']

    fig = go.Figure(go.Funnel(
        y=labels,
        x=values,
        text=inside_text,
        textinfo='text',
        textposition='inside',
        textfont={'size': 14, 'color': 'white', 'family': 'Microsoft YaHei'},
        customdata=customdata,
        hovertemplate=hovertemplate,
        marker={
            'color': colors,
            'line': {'color': 'rgba(255,255,255,0.65)', 'width': 2.5},
        },
        connector={
            'line': {'color': 'rgba(26,58,74,0.12)', 'width': 1.6, 'dash': 'solid'},
        },
        outsidetextfont={'size': 12, 'color': '#555'},
    ))

    annotations = []
    if bottleneck_idx is not None:
        annotations.append(dict(
            x=0.5, y=0.0,
            xref='paper', yref='paper',
            text=(
                f'<b>最大流失</b>:  {labels[bottleneck_idx - 1]} → {labels[bottleneck_idx]}'
                f'  转化率仅 <b>{prev_rates[bottleneck_idx]:.1f}%</b>'
            ),
            showarrow=False,
            font={'size': 14, 'color': '#C0392B', 'family': 'Microsoft YaHei'},
            bgcolor='rgba(255,245,245,0.92)',
            borderpad=12,
            bordercolor='#E8C4C4',
            borderwidth=1,
        ))

    footnote = (
        f'ecommerce_funnel_analysis  |  n = {n_sessions:,} sessions  |  '
        f'{date.today().isoformat()}'
    )

    fig.update_layout(
        title={
            'text': '<b>行为级转化漏斗</b>  ·  Event Funnel',
            'font': {'size': 24, 'color': '#1a1a2e', 'family': 'Microsoft YaHei'},
            'x': 0.5, 'xanchor': 'center',
        },
        annotations=annotations,
        width=880, height=620,
        margin={'t': 100, 'b': 70, 'l': 80, 'r': 80},
        paper_bgcolor='#F8F9FA',
        plot_bgcolor='rgba(0,0,0,0)',
        font={'family': 'Microsoft YaHei, SimHei, sans-serif'},
    )

    fig.add_annotation(
        text=footnote,
        x=0.5, y=-0.05,
        xref='paper', yref='paper',
        showarrow=False,
        font={'size': 10, 'color': '#AAA'},
    )

    html_path = str(CHART_DIR / '02_event_funnel.html')
    fig.write_html(html_path, include_plotlyjs=True)
    logger.info("  Saved: %s", (CHART_DIR / '02_event_funnel.html').name)
