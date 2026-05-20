"""可视化模块 — 13 张优化图表（matplotlib + plotly）— 中文版"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import matplotlib.ticker as mticker
import numpy as np
import plotly.graph_objects as go
from python.config import (
    FUNNEL_COLORS, PRIMARY, ACCENT, CHART_DIR, logger,
)

# ── 中文字体 ────────────────────────────────────────
_font_candidates = ['Microsoft YaHei', 'SimHei', 'KaiTi', 'Noto Sans CJK SC']
_available = {f.name for f in fm.fontManager.ttflist}
_font_to_use = next((f for f in _font_candidates if f in _available), None)
if _font_to_use:
    matplotlib.rcParams['font.sans-serif'] = [_font_to_use, 'DejaVu Sans']
else:
    matplotlib.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
matplotlib.rcParams['axes.unicode_minus'] = False

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

# ── 统一调色板 ──────────────────────────────────────
C_RED    = '#D64545'
C_BLUE   = '#3A7CA5'
C_GREEN  = '#4CAF82'
C_ORANGE = '#E8934B'
C_PURPLE = '#8E6BAE'
C_GREY   = '#A0AAB5'
C_DARK   = '#2C3E50'
C_LIGHT  = '#E8ECF1'

# 专用配色
CL_RED    = '#E8C4C4'   # 淡红
CL_BLUE   = '#C4D9E8'   # 淡蓝
CL_GREEN  = '#C4E8D4'   # 淡绿
CL_ORANGE = '#F0D8C0'   # 淡橙
CL_GREY   = '#DDE1E6'   # 淡灰

DURATION_COLORS = ['#D64545', '#E8934B', '#3A7CA5', '#4CAF82']
STAGE_COLORS    = ['#5B9BD5', '#E8934B', '#D64545', '#8E6BAE']
CHANNEL_COLORS_5 = ['#3A7CA5', '#B8456E', '#E8934B', '#D64545', '#4CAF82']


def _save(fig, name: str, is_plotly: bool = False) -> None:
    if is_plotly:
        fig.write_html(str(CHART_DIR / f'{name}.html'),
                       include_plotlyjs='cdn', full_html=True)
    else:
        fig.savefig(str(CHART_DIR / f'{name}.png'), dpi=180, bbox_inches='tight',
                    facecolor=fig.get_facecolor(), edgecolor='none')
    plt.close('all')
    logger.info("  Saved: %s", (CHART_DIR / f'{name}.{"html" if is_plotly else "png"}').name)


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
# 01 — 页面级漏斗 (Plotly)
# ═══════════════════════════════════════════════════════════
def plot_page_funnel(funnel_df: 'pd.DataFrame') -> None:
    labels = funnel_df['漏斗阶段'].tolist()
    counts = funnel_df['到达会话数'].tolist()
    rates = funnel_df['上一阶段转化率(%)'].tolist()

    custom_text = []
    for i, (label, count, rate) in enumerate(zip(labels, counts, rates)):
        if i == 0:
            custom_text.append(f'<b>{label}</b><br>{count:,} 会话')
        else:
            custom_text.append(
                f'<b>{label}</b><br>{count:,} 会话<br>'
                f'<i>交叉转化率 {rate}%</i>'
            )

    fig = go.Figure(go.Funnel(
        y=labels, x=counts, text=custom_text,
        textposition='inside', textinfo='text',
        textfont=dict(size=13, color='white'),
        marker=dict(
            color=['#D64545', '#E8934B', '#F2D398', '#5B9BD5', '#3A7CA5'],
            line=dict(width=0),
        ),
        connector=dict(fillcolor='#ECEFF1', line=dict(width=0)),
    ))
    fig.update_layout(
        title=dict(
            text='页面级转化漏斗<br>'
                 '<sup>交叉转化率 = 同时到达前后两页的会话 / 到达前页的会话</sup>',
            font=dict(size=17),
        ),
        template='plotly_white',
        height=550,
        margin=dict(t=100, b=40, l=60, r=40),
        font=dict(size=13, color='#2C3E50'),
    )
    _save(fig, '01_page_funnel', is_plotly=True)


# ═══════════════════════════════════════════════════════════
# 02 — 行为级漏斗 (Plotly)
# ═══════════════════════════════════════════════════════════
def plot_event_funnel(funnel_df: 'pd.DataFrame') -> None:
    fig = go.Figure(go.Funnel(
        y=funnel_df['漏斗阶段'].tolist(),
        x=funnel_df['会话数'].tolist(),
        textposition='inside',
        textinfo='value+percent previous',
        textfont=dict(size=14, color='white'),
        marker=dict(
            color=['#5B9BD5', '#4CAF82', '#E8934B', '#D64545'],
            line=dict(width=0),
        ),
        connector=dict(fillcolor='#ECEFF1', line=dict(width=0)),
    ))
    fig.update_layout(
        title=dict(
            text='行为级转化漏斗<br>'
                 '<sup>浏览 → 点击 → 加购 → 购买</sup>',
            font=dict(size=17),
        ),
        template='plotly_white',
        height=520,
        margin=dict(t=100, b=40, l=60, r=40),
        font=dict(size=13, color='#2C3E50'),
    )
    _save(fig, '02_event_funnel', is_plotly=True)


# ═══════════════════════════════════════════════════════════
# 03 — 渠道专属漏斗 (5 面板)
# ═══════════════════════════════════════════════════════════
def plot_channel_funnels(channel_funnels: dict[str, 'pd.DataFrame']) -> None:
    fig = plt.figure(figsize=(22, 13))
    colors_map = {'Organic': '#3A7CA5', 'Paid Search': '#B8456E', 'Social': '#E8934B',
                  'Email': '#D64545', 'Direct': '#4CAF82'}
    short_labels = ['首页', '列表页', '详情页', '购物车', '结算页']

    sorted_channels = sorted(channel_funnels.keys(),
                             key=lambda ch: channel_funnels[ch].iloc[-1]['上一阶段转化率(%)'],
                             reverse=True)

    for i, ch in enumerate(sorted_channels):
        ax = fig.add_subplot(2, 3, i + 1)
        df = channel_funnels[ch]
        full_color = colors_map.get(ch, C_BLUE)
        vals = df['到达会话数'].values
        rates_arr = df['上一阶段转化率(%)'].values

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
            b = ax.barh(short_labels[j], v, height=0.6, color=bc,
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
    fig, ax = plt.subplots(figsize=(11, 9))
    labels = [l.replace(' → ', '\n→ ') for l in loss_df['漏斗环节']]
    values = loss_df['估算损失金额'].values / 10000
    n = len(loss_df)

    color_grad = ['#E8A0A0', '#D64545', '#C0392B', '#922B21']
    bars = ax.bar(range(n), values, width=0.50, color=color_grad,
                  edgecolor='white', linewidth=1.5, alpha=0.9, zorder=3)

    max_val = max(values)
    lost_sessions = loss_df['流失会话数'].values
    churn_rates = loss_df['环节流失率(%)'].values

    for i, (bar, val, lost, rate) in enumerate(
            zip(bars, values, lost_sessions, churn_rates)):
        cx = bar.get_x() + bar.get_width() / 2
        bh = bar.get_height()
        ax.text(cx, bh + max_val * 0.015,
                f'¥{val:,.0f}万', ha='center', va='bottom',
                fontsize=14, fontweight='bold', color='#922B21')
        ax.text(cx, bh * 0.75,
                f'{lost:,} 人流失\n流失率 {rate:.1f}%',
                ha='center', va='center',
                fontsize=11, color='white', fontweight='bold', alpha=0.95)

    total_loss = values.sum()
    ax.axhline(y=total_loss, color=C_BLUE, linestyle='--', linewidth=1.5, alpha=0.5, zorder=2)
    ax.text(n - 0.5, total_loss + max_val * 0.025,
            f'合计 ¥{total_loss:,.0f}万', fontsize=12, color=C_BLUE, fontweight='bold')

    ax.set_xticks(range(n))
    ax.set_xticklabels(labels, fontsize=11)
    ax.set_title('各环节年度损失金额估算', fontsize=17, pad=22)
    ax.set_ylabel('损失金额 (万元)', fontsize=12, labelpad=10)
    ax.set_ylim(0, max_val * 1.55)
    ax.tick_params(left=False, bottom=False)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'{x:,.0f}'))
    fig.subplots_adjust(left=0.10, right=0.95, top=0.92, bottom=0.10)
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

    # 自定义分段色：低→中→高 均匀过渡
    from matplotlib.colors import LinearSegmentedColormap
    custom_cmap = LinearSegmentedColormap.from_list(
        'custom_rdylgn',
        ['#D64545', '#E8934B', '#F2D398', '#E8ECCA', '#4CAF82'],
        N=256,
    )

    im = ax.imshow(data, cmap=custom_cmap, aspect='auto', vmin=vmin, vmax=vmax)

    mid_val = (vmin + vmax) / 2
    for i in range(len(pivot.index)):
        for j in range(len(pivot.columns)):
            val = data[i, j]
            text_color = 'white' if val < mid_val else C_DARK
            ax.text(j, i, f'{val:.1f}%', ha='center', va='center',
                    fontsize=14, fontweight='bold', color=text_color)

    ax.set_xticks(range(len(pivot.columns)))
    ax.set_xticklabels(['手机', '桌面', '平板'], fontsize=12)
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
    ax.set_xlim(0, pivot.values.sum(axis=1).max() * 1.12)
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f'{v:.0f}%'))
    fig.tight_layout()
    _save(fig, '09_churn_by_channel')


# ═══════════════════════════════════════════════════════════
# 10 — PIE 优先级矩阵
# ═══════════════════════════════════════════════════════════
def plot_pie_matrix(pie_df: 'pd.DataFrame') -> None:
    fig, ax = plt.subplots(figsize=(11, 8))
    x = pie_df['Potential'].values
    y = pie_df['Importance'].values
    sizes = pie_df['PIE得分'].values * 4
    ease = pie_df['Ease'].values
    pie_labels = [l.replace(' → ', ' →\n') for l in pie_df['漏斗环节']]
    pie_scores = pie_df['PIE得分'].values.astype(int)

    scatter = ax.scatter(x, y, s=sizes, c=ease, cmap='RdYlGn',
                         vmin=5, vmax=9, alpha=0.85,
                         edgecolors=C_DARK, linewidth=1.2, zorder=4)

    for i, label in enumerate(pie_labels):
        ax.annotate(f'{label}\nPIE={pie_scores[i]}',
                    (x[i], y[i]),
                    textcoords='offset points', xytext=(0, 22),
                    ha='center', fontsize=9.5, fontweight='bold', color=C_DARK,
                    bbox=dict(boxstyle='round,pad=0.3', facecolor='white',
                              edgecolor=CL_GREY, alpha=0.85))

    ax.axhline(y=5, color=C_GREY, linestyle=':', alpha=0.25, zorder=1)
    ax.axvline(x=5, color=C_GREY, linestyle=':', alpha=0.25, zorder=1)

    cbar = plt.colorbar(scatter, ax=ax, shrink=0.8, pad=0.02)
    cbar.set_label('优化容易度 (Ease)', fontsize=11, labelpad=8)

    ax.set_xlabel('损失潜力 (Potential)', fontsize=12, labelpad=10)
    ax.set_ylabel('流量重要性 (Importance)', fontsize=12, labelpad=10)
    ax.set_title('PIE 优先级矩阵 (气泡大小 = PIE 得分)', fontsize=16, pad=18)
    ax.set_xlim(0, 11)
    ax.set_ylim(0, 11)
    ax.grid(True, alpha=0.25, linestyle='-', color='#DDE1E6')
    ax.tick_params(left=False, bottom=False)
    fig.tight_layout()
    _save(fig, '10_pie_matrix')


# ═══════════════════════════════════════════════════════════
# 11 — A/B 实验对比
# ═══════════════════════════════════════════════════════════
def plot_ab_test(groups_df: 'pd.DataFrame') -> None:
    fig, ax = plt.subplots(figsize=(9, 6))
    g = groups_df.reset_index()
    palette = ['#A0AAB5', '#5B9BD5', '#4CAF82']
    colors = [palette[i % len(palette)] for i in range(len(g))]
    bars = ax.bar(g['experiment_group'], g['转化率(%)'], width=0.45,
                  color=colors, edgecolor='white', linewidth=1.5, zorder=3)

    control_rate = groups_df.loc['Control', '转化率(%)']
    max_rate = max(g['转化率(%)'])
    for bar, (_, row) in zip(bars, g.iterrows()):
        rate = row['转化率(%)']
        sessions = row['会话数']
        label_top = f'{rate:.2f}%'
        if row['experiment_group'] != 'Control':
            lift = (rate - control_rate) / control_rate * 100
            label_top += f'  (lift {lift:+.1f}%)'

        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.25,
                label_top, ha='center', fontsize=13, fontweight='bold', color=C_DARK)

        sig_note = '不显著' if row['experiment_group'] != 'Control' else ''
        sample_note = f'n = {sessions:,}'
        if sig_note:
            sample_note += f'  [{sig_note}]'
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 1.2,
                sample_note, ha='center', fontsize=10, color=C_GREY)

    ax.set_title('A/B 实验 — 各组转化率对比\n'
                 '(Control 占 97.8% 样本，Variant 组差异不显著)',
                 fontsize=14, pad=18)
    ax.set_ylabel('转化率 (%)', fontsize=12, labelpad=10)
    ax.set_ylim(0, max_rate * 1.28)
    ax.tick_params(left=False, bottom=False)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f'{v:.1f}%'))
    fig.tight_layout()
    _save(fig, '11_ab_test')


# ═══════════════════════════════════════════════════════════
# 12 — 品类双阶段转化率
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
    _save(fig, '12_category_funnel')


# ═══════════════════════════════════════════════════════════
# 13 — 严格漏斗 vs 覆盖分析 对比
# ═══════════════════════════════════════════════════════════
def plot_strict_vs_coverage(strict_df: 'pd.DataFrame') -> None:
    """严格路径漏斗 vs 页面覆盖分析 双柱对比"""
    from python.config import FUNNEL_COLORS

    fig, ax = plt.subplots(figsize=(13, 7))
    labels = ['首页', '列表页', '详情页', '购物车', '结算页']
    x_pos = np.arange(len(labels))
    width = 0.32

    strict_vals = strict_df['严格路径到达会话数'].values
    coverage_vals = strict_df['覆盖到达会话数'].values

    bars1 = ax.bar(
        x_pos - width / 2, coverage_vals, width,
        label='页面覆盖（宽松）', color='#A0AAB5', edgecolor='white',
        linewidth=1.2, alpha=0.85, zorder=3,
    )
    bars2 = ax.bar(
        x_pos + width / 2, strict_vals, width,
        label='严格路径（顺序）', color='#3A7CA5', edgecolor='white',
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

    # 标注差异
    diffs = strict_df['覆盖-严格差异'].values
    for i, diff in enumerate(diffs):
        ax.text(
            i, max(coverage_vals) * 0.55,
            f'Δ {diff:,}', ha='center', fontsize=9.5,
            color=C_RED, fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.2', facecolor='white',
                      edgecolor=CL_RED, alpha=0.8),
        )

    ax.set_xticks(x_pos)
    ax.set_xticklabels(labels, fontsize=11)
    ax.set_title(
        '严格路径漏斗 vs 页面覆盖分析',
        fontsize=16, pad=18,
    )
    ax.set_ylabel('会话数', fontsize=12, labelpad=10)
    ax.legend(fontsize=11, framealpha=0.9, edgecolor=CL_GREY)
    ax.tick_params(left=False, bottom=False)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f'{v/1000:.0f}K'))
    fig.tight_layout()
    _save(fig, '13_strict_vs_coverage')


# ═══════════════════════════════════════════════════════════
# 14 — 深链 vs 首页路径 转化率对比
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
    _save(fig, '14_deep_link_analysis')


# ═══════════════════════════════════════════════════════════
# 15 — 新用户 vs 老用户 漏斗对比
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

    short_labels = ['首页', '列表页', '详情页', '购物车', '结算页']
    event_labels_short = ['浏览', '点击', '加购', '购买']

    for row_idx, (page_key, event_key, group_title, color) in enumerate(titles):
        # 左：页面漏斗
        ax_page = axes[row_idx, 0]
        page_df = nr_results[page_key]
        page_vals = page_df['到达会话数'].values
        bars = ax_page.barh(
            short_labels, page_vals, height=0.55, color=color,
            edgecolor='white', linewidth=1.2, alpha=0.88, zorder=3,
        )
        ax_page.invert_yaxis()
        ax_page.set_title(f'{group_title} — 页面漏斗', fontsize=13, fontweight='bold', pad=10)
        ax_page.tick_params(left=False)
        max_v = max(page_vals)
        for bar, (_, row) in zip(bars, page_df.iterrows()):
            ax_page.text(
                bar.get_width() + max_v * 0.02,
                bar.get_y() + bar.get_height() / 2,
                f'{int(row["到达会话数"]):,}  [{row["上一阶段转化率(%)"]:.1f}%]',
                va='center', fontsize=9, color=C_DARK,
            )
        ax_page.set_xlim(0, max_v * 1.4)

        # 右：行为漏斗
        ax_event = axes[row_idx, 1]
        event_df = nr_results[event_key]
        event_vals = event_df['会话数'].values
        bars2 = ax_event.barh(
            event_labels_short, event_vals, height=0.55, color=color,
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
    _save(fig, '15_new_vs_returning')


# ═══════════════════════════════════════════════════════════
# 16 — 周末 vs 工作日 转化率对比
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
        colors = ['#5B9BD5', '#E8934B']  # 工作日蓝, 周末橙

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
    _save(fig, '16_weekend_comparison')


# ═══════════════════════════════════════════════════════════
# 17 — Cohort 留存热力图
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

    from matplotlib.colors import LinearSegmentedColormap
    fig, ax = plt.subplots(figsize=(min(14, cols * 1.1 + 3), min(8, rows * 0.5 + 2)))

    cmap = LinearSegmentedColormap.from_list(
        'retention_green',
        ['#F5F5F5', '#C4E8D4', '#4CAF82', '#2D7A4A'],
        N=256,
    )
    im = ax.imshow(data, cmap=cmap, aspect='auto', vmin=0, vmax=100)

    for i in range(rows):
        for j in range(cols):
            val = data[i, j]
            if not np.isnan(val) and val > 0:
                text_color = 'white' if val > 60 else C_DARK
                ax.text(j, i, f'{val:.0f}%', ha='center', va='center',
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
    _save(fig, '17_cohort_heatmap')
