"""可视化模块：行业标准漏斗分析图表（matplotlib + plotly）"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from python.config import FUNNEL_COLORS, PRIMARY, ACCENT, CHART_DIR, logger

# ── 中文字体配置 ─────────────────────────────────────
_font_candidates = ['Microsoft YaHei', 'SimHei', 'KaiTi', 'STXihei']
_available = {f.name for f in fm.fontManager.ttflist}
_font_to_use = next((f for f in _font_candidates if f in _available), None)
if _font_to_use:
    matplotlib.rcParams['font.sans-serif'] = [_font_to_use, 'DejaVu Sans']
else:
    matplotlib.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
matplotlib.rcParams['axes.unicode_minus'] = False

plt.rcParams.update({
    'figure.facecolor': '#F8F9FA', 'axes.facecolor': '#FFFFFF',
    'axes.spines.top': False, 'axes.spines.right': False,
    'axes.grid': True, 'grid.alpha': 0.3, 'grid.linestyle': '--',
    'font.size': 10, 'axes.titlesize': 13, 'axes.titleweight': 'bold',
})

# 漏斗阶段短标签
STAGE_LABELS_SHORT = ['首页', '商品页', '购物车', '结账页', '确认页']

# ================================================================
# 图 1: 全链路转化漏斗（plotly — 行业标准交互式漏斗图）
# ================================================================
def plot_funnel_plotly(funnel_df: pd.DataFrame) -> str:
    # 构建带阶段名+会话数+转化率的标签
    texts = []
    for _, row in funnel_df.iterrows():
        stage = row['漏斗阶段']
        cnt = int(row['独立会话数'])
        pct = row['整体转化率(%)']
        texts.append(f"{stage}<br>{cnt:,} 会话 ({pct:.1f}%)")
    fig = px.funnel(
        funnel_df, x='独立会话数', y='漏斗阶段',
        title='全链路转化漏斗（会话维度）',
        color_discrete_sequence=[PRIMARY],
    )
    fig.update_traces(
        text=texts,
        textposition='inside', textfont_size=14, textinfo='text',
    )
    fig.update_layout(title_font_size=20, title_x=0.5, height=500)
    path = CHART_DIR / '01_funnel_plotly.html'
    fig.write_html(path)
    logger.info("已保存: %s", path)
    return str(path)


# ================================================================
# 图 2: 逐级转化率与流失量（matplotlib 组合图 — GA 风格）
# ================================================================
def plot_funnel_static(funnel_df: pd.DataFrame) -> str:
    fig, axes = plt.subplots(1, 2, figsize=(16, 7))

    # 左：漏斗柱状图
    ax = axes[0]
    stages = ['首页', '商品页', '购物车', '结账页', '确认页']
    counts = funnel_df['独立会话数'].values
    bars = ax.bar(range(len(stages)), counts, color=FUNNEL_COLORS,
                  edgecolor='white', linewidth=2, width=0.6)
    ax.set_xticks(range(len(stages)))
    ax.set_xticklabels(stages, fontsize=11)
    ax.set_ylabel('会话数', fontsize=12)
    ax.set_title('各阶段到达会话数', fontsize=14, pad=15)
    for i, (bar, c) in enumerate(zip(bars, counts)):
        rate = funnel_df.iloc[i]['整体转化率(%)']
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 50,
                f'{int(c):,}\n({rate:.1f}%)', ha='center', fontsize=10, fontweight='bold')

    # 右：逐级转化率折线（仅 4 个环节）
    ax2 = axes[1]
    step_rates = funnel_df['上一阶段转化率(%)'].values[1:]  # 跳过首页 100%
    step_labels = [f'{a}\n→ {b}' for a, b in zip(stages[:-1], stages[1:])]
    x = range(len(step_labels))
    ax2.plot(x, step_rates, 'o-', color=ACCENT, linewidth=2.5, markersize=12,
             markerfacecolor='white', markeredgewidth=2.5)
    ax2.fill_between(x, step_rates, alpha=0.1, color=ACCENT)
    ax2.set_xticks(x)
    ax2.set_xticklabels(step_labels, fontsize=11)
    ax2.set_ylabel('环节转化率 (%)', fontsize=12)
    ax2.set_title('各环节逐级转化率', fontsize=14, pad=15)
    ax2.set_ylim(0, 105)
    for i, r in enumerate(step_rates):
        ax2.annotate(f'{r:.1f}%', (i, r), textcoords="offset points",
                     xytext=(0, 16), ha='center', fontsize=12, fontweight='bold',
                     color=ACCENT if i == step_rates.argmin() else '#333')
    ax2.axhline(y=50, color='#999', linestyle=':', alpha=0.5)
    ax2.axhline(y=step_rates.mean(), color=PRIMARY, linestyle='--', alpha=0.4,
                label=f'均值 {step_rates.mean():.1f}%')
    ax2.legend(fontsize=9)

    fig.suptitle('电商全链路转化漏斗分析', fontsize=17, fontweight='bold', y=1.02)
    plt.tight_layout()
    path = CHART_DIR / '02_funnel_analysis.png'
    fig.savefig(path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    logger.info("已保存: %s", path)
    return str(path)


# ================================================================
# 图 3: 各环节流失损失（瀑布图风格 — CRO 标准）
# ================================================================
def plot_loss_waterfall(loss_df: pd.DataFrame) -> str:
    fig, ax = plt.subplots(figsize=(14, 7))
    stages_short = ['首页→商品', '商品→加购', '加购→结账', '结账→确认']
    amounts = loss_df['估算损失金额'].values
    lost_counts = loss_df['流失会话数'].values
    colors = [ACCENT if a == max(amounts) else PRIMARY for a in amounts]
    bars = ax.bar(range(len(stages_short)), amounts, color=colors,
                  edgecolor='white', linewidth=2, width=0.55)
    ax.set_xticks(range(len(stages_short)))
    ax.set_xticklabels(stages_short, fontsize=12)
    ax.set_ylabel('估算损失金额（元）', fontsize=13)
    ax.set_title('各漏斗环节流失损失估算', fontsize=16, pad=20)
    for bar, amt, lost, (_, row) in zip(bars, amounts, lost_counts, loss_df.iterrows()):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + amt * 0.02,
                f'¥{amt:,.0f}', ha='center', fontweight='bold', fontsize=12)
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() / 2,
                f'流失 {int(lost):,} 人\n({row["环节流失率(%)"]:.1f}%)',
                ha='center', va='center', fontweight='bold', fontsize=10, color='white')
    ax.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    path = CHART_DIR / '03_loss_waterfall.png'
    fig.savefig(path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    logger.info("已保存: %s", path)
    return str(path)


# ================================================================
# 图 4: 渠道 × 设备转化率热力图（交叉诊断标准图）
# ================================================================
def plot_channel_device_heatmap(cross_df: pd.DataFrame) -> str:
    pivot = cross_df.reset_index().pivot(
        index='ReferralSource', columns='DeviceType', values='转化率(%)'
    )
    if pivot.empty:
        logger.warning("热力图数据为空，跳过")
        return ""
    fig, ax = plt.subplots(figsize=(11, 6))
    arr = pivot.values
    vmin, vmax = arr.min(), arr.max()
    im = ax.imshow(arr, cmap='YlOrRd', aspect='auto', vmin=vmin, vmax=vmax)
    ax.set_xticks(range(len(pivot.columns)))
    ax.set_xticklabels(pivot.columns, fontsize=12)
    ax.set_yticks(range(len(pivot.index)))
    ax.set_yticklabels(pivot.index, fontsize=12)
    ax.set_title('渠道 × 设备 转化率热力图（%）', fontsize=16, pad=20)
    mid = (vmin + vmax) / 2
    for i in range(len(pivot.index)):
        for j in range(len(pivot.columns)):
            val = arr[i, j]
            ax.text(j, i, f'{val:.1f}%', ha='center', va='center',
                    fontweight='bold', fontsize=13,
                    color='white' if abs(val - mid) > 2 else 'black')
    plt.colorbar(im, ax=ax, shrink=0.8, label='转化率 %')
    plt.tight_layout()
    path = CHART_DIR / '04_channel_device_heatmap.png'
    fig.savefig(path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    logger.info("已保存: %s", path)
    return str(path)


# ================================================================
# 图 5: 各渠道 / 设备转化率对比（分组柱状图 — GA 标准样式）
# ================================================================
def plot_dimension_comparison(channel_df: pd.DataFrame, device_df: pd.DataFrame) -> str:
    fig, axes = plt.subplots(1, 2, figsize=(16, 6))

    # 渠道
    ax = axes[0]
    ch_names = channel_df.index.tolist()
    ch_rates = channel_df['整体转化率'].values
    ch_colors = ['#2E86AB', '#A23B72', '#F18F01', '#C73E1D']
    bars = ax.barh(range(len(ch_names)), ch_rates, color=ch_colors,
                   edgecolor='white', linewidth=2, height=0.55)
    ax.set_yticks(range(len(ch_names)))
    ax.set_yticklabels(ch_names, fontsize=12)
    ax.set_xlabel('转化率 (%)', fontsize=12)
    ax.set_title('各渠道整体转化率', fontsize=14, pad=15)
    for bar, rate in zip(bars, ch_rates):
        ax.text(bar.get_width() + 0.3, bar.get_y() + bar.get_height() / 2,
                f'{rate:.2f}%', va='center', fontweight='bold', fontsize=12)

    # 设备
    ax2 = axes[1]
    dev_names = device_df.index.tolist()
    dev_rates = device_df['整体转化率'].values
    dev_colors = ['#27AE60', '#3498DB', '#9B59B6']
    bars2 = ax2.barh(range(len(dev_names)), dev_rates, color=dev_colors,
                     edgecolor='white', linewidth=2, height=0.55)
    ax2.set_yticks(range(len(dev_names)))
    ax2.set_yticklabels(dev_names, fontsize=12)
    ax2.set_xlabel('转化率 (%)', fontsize=12)
    ax2.set_title('各设备整体转化率', fontsize=14, pad=15)
    for bar, rate in zip(bars2, dev_rates):
        ax2.text(bar.get_width() + 0.3, bar.get_y() + bar.get_height() / 2,
                 f'{rate:.2f}%', va='center', fontweight='bold', fontsize=12)

    fig.suptitle('转化率按维度对比', fontsize=16, fontweight='bold', y=1.02)
    plt.tight_layout()
    path = CHART_DIR / '05_dimension_comparison.png'
    fig.savefig(path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    logger.info("已保存: %s", path)
    return str(path)


# ================================================================
# 图 6: 时段(小时×周几)流量与转化率（双轴折线+柱状图）
# ================================================================
def plot_time_analysis(hourly: pd.DataFrame, dow: pd.DataFrame) -> str:
    fig, axes = plt.subplots(1, 2, figsize=(18, 6))

    # 按小时
    ax1 = axes[0]
    ax1_twin = ax1.twinx()
    ax1.bar(hourly.index, hourly['会话数'], alpha=0.25, color=PRIMARY, width=0.8)
    ax1_twin.plot(hourly.index, hourly['转化率'], 'o-', color=ACCENT,
                  linewidth=2.5, markersize=8, markerfacecolor='white', markeredgewidth=2)
    ax1.set_xlabel('小时', fontsize=12)
    ax1.set_ylabel('会话数', fontsize=12, color=PRIMARY)
    ax1_twin.set_ylabel('转化率 (%)', fontsize=12, color=ACCENT)
    ax1.set_title('各时段流量与转化率', fontsize=14, pad=15)
    ax1.set_xticks(range(0, 24, 2))
    ax1.tick_params(axis='y', colors=PRIMARY)
    ax1_twin.tick_params(axis='y', colors=ACCENT)

    # 按周几
    ax2 = axes[1]
    ax2_twin = ax2.twinx()
    ax2.bar(dow.index, dow['会话数'], alpha=0.25, color=PRIMARY, width=0.6)
    ax2_twin.plot(dow.index, dow['转化率'], 'D-', color=ACCENT,
                  linewidth=2.5, markersize=10, markerfacecolor='white', markeredgewidth=2)
    ax2.set_xlabel('星期', fontsize=12)
    ax2.set_ylabel('会话数', fontsize=12, color=PRIMARY)
    ax2_twin.set_ylabel('转化率 (%)', fontsize=12, color=ACCENT)
    ax2.set_title('每日流量与转化率', fontsize=14, pad=15)
    ax2.tick_params(axis='y', colors=PRIMARY)
    ax2_twin.tick_params(axis='y', colors=ACCENT)

    fig.suptitle('时间维度流量与转化率分析', fontsize=16, fontweight='bold', y=1.02)
    plt.tight_layout()
    path = CHART_DIR / '06_time_analysis.png'
    fig.savefig(path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    logger.info("已保存: %s", path)
    return str(path)


# ================================================================
# 图 7: 停留时长 → 转化率（分桶柱状图，转化分析标准图）
# ================================================================
def plot_duration_conversion(duration_df: pd.DataFrame) -> str:
    fig, ax = plt.subplots(figsize=(12, 6))
    buckets = duration_df.index.tolist()
    rates = duration_df['转化率(%)'].values
    counts = duration_df['会话数'].values
    colors = ['#E74C3C', '#F39C12', '#3498DB', '#27AE60']
    bars = ax.bar(range(len(buckets)), rates, color=colors,
                  edgecolor='white', linewidth=2, width=0.55)
    ax.set_xticks(range(len(buckets)))
    ax.set_xticklabels(buckets, fontsize=10)
    ax.set_ylabel('转化率 (%)', fontsize=13)
    ax.set_title('停留时长与转化率关系', fontsize=16, pad=20)
    for bar, rate, cnt in zip(bars, rates, counts):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 1,
                f'{rate:.1f}%\n({int(cnt):,}人)', ha='center', fontweight='bold', fontsize=11)
    ax.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    path = CHART_DIR / '07_duration_conversion.png'
    fig.savefig(path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    logger.info("已保存: %s", path)
    return str(path)


# ================================================================
# 图 8: 最高流失环节分渠道诊断（标准分组柱状图）
# ================================================================
def plot_churn_by_channel(churn_by_dim: pd.DataFrame) -> str:
    """最高流失环节（浏览→加购）按渠道/设备拆分"""
    fig, axes = plt.subplots(1, 2, figsize=(16, 6))

    # 按渠道
    ch_data = churn_by_dim[churn_by_dim['维度'] == 'ReferralSource'].copy()
    ch_data = ch_data.sort_values('流失率(%)')
    ax = axes[0]
    bars = ax.barh(range(len(ch_data)), ch_data['流失率(%)'].values,
                   color=['#2E86AB', '#A23B72', '#F18F01', '#C73E1D'],
                   edgecolor='white', linewidth=2, height=0.55)
    ax.set_yticks(range(len(ch_data)))
    ax.set_yticklabels(ch_data['维度值'].values, fontsize=12)
    ax.set_xlabel('浏览→加购 流失率 (%)', fontsize=12)
    ax.set_title('各渠道浏览→加购流失率', fontsize=14, pad=15)
    for bar, (_, row) in zip(bars, ch_data.iterrows()):
        ax.text(bar.get_width() + 0.3, bar.get_y() + bar.get_height() / 2,
                f'{row["流失率(%)"]:.1f}%', va='center', fontweight='bold', fontsize=11)

    # 按设备
    dev_data = churn_by_dim[churn_by_dim['维度'] == 'DeviceType'].copy()
    dev_data = dev_data.sort_values('流失率(%)')
    ax2 = axes[1]
    bars2 = ax2.barh(range(len(dev_data)), dev_data['流失率(%)'].values,
                     color=['#27AE60', '#3498DB', '#9B59B6'],
                     edgecolor='white', linewidth=2, height=0.55)
    ax2.set_yticks(range(len(dev_data)))
    ax2.set_yticklabels(dev_data['维度值'].values, fontsize=12)
    ax2.set_xlabel('浏览→加购 流失率 (%)', fontsize=12)
    ax2.set_title('各设备浏览→加购流失率', fontsize=14, pad=15)
    for bar, (_, row) in zip(bars2, dev_data.iterrows()):
        ax2.text(bar.get_width() + 0.3, bar.get_y() + bar.get_height() / 2,
                 f'{row["流失率(%)"]:.1f}%', va='center', fontweight='bold', fontsize=11)

    fig.suptitle('最高流失环节（浏览→加购）分维度诊断', fontsize=16, fontweight='bold', y=1.02)
    plt.tight_layout()
    path = CHART_DIR / '08_churn_by_channel.png'
    fig.savefig(path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    logger.info("已保存: %s", path)
    return str(path)


# ================================================================
# 图 9: 用户行为路径桑基图（plotly — 行业标准路径分析）
# ================================================================
def plot_path_sankey(df_cleaned: pd.DataFrame) -> str:
    df_sorted = df_cleaned.sort_values(['SessionID', 'Timestamp'])
    paths = df_sorted.groupby('SessionID')['stage'].agg(
        lambda x: list(x.drop_duplicates()))
    transitions = {}
    for path in paths:
        for i in range(len(path) - 1):
            key = (path[i], path[i + 1])
            transitions[key] = transitions.get(key, 0) + 1
    top_trans = sorted(transitions.items(), key=lambda x: x[1], reverse=True)[:15]
    all_labels = list(dict.fromkeys([s for t in top_trans for s in t[0]]))
    label_to_idx = {l: i for i, l in enumerate(all_labels)}
    sources = [label_to_idx[s] for (s, _), _ in top_trans]
    targets = [label_to_idx[t] for (_, t), _ in top_trans]
    values = [v for _, v in top_trans]
    fig = go.Figure(go.Sankey(
        node=dict(pad=15, thickness=20, line=dict(color='black', width=0.5),
                  label=all_labels, color=PRIMARY),
        link=dict(source=sources, target=targets, value=values),
    ))
    fig.update_layout(title_text='用户行为路径流转图（Top 15）',
                      title_font_size=20, title_x=0.5, height=500)
    path = CHART_DIR / '09_path_sankey.html'
    fig.write_html(path)
    logger.info("已保存: %s", path)
    return str(path)


# ================================================================
# 图 10: PIE 优先级矩阵气泡图（CRO 标准优化决策图）
# ================================================================
def plot_pie_matrix(pie_df: pd.DataFrame) -> str:
    fig, ax = plt.subplots(figsize=(12, 8))
    scatter = ax.scatter(
        pie_df['Potential'], pie_df['Importance'],
        s=pie_df['Ease'] * 80, c=pie_df['PIE得分'],
        cmap='RdYlGn', alpha=0.75, edgecolors='#333', linewidth=0.5,
    )
    for _, row in pie_df.iterrows():
        short_label = row['漏斗环节'].replace(' → ', '→')
        ax.annotate(f"{short_label}\nPIE={row['PIE得分']:.0f}",
                    (row['Potential'], row['Importance']),
                    textcoords="offset points", xytext=(10, 5), fontsize=9, fontweight='bold')
    ax.set_xlabel('挽回潜力 (Potential)', fontsize=13)
    ax.set_ylabel('影响面 (Importance)', fontsize=13)
    ax.set_title('PIE 优先级矩阵（气泡大小 = 实施难度 Ease）', fontsize=16, pad=20)
    cbar = plt.colorbar(scatter, ax=ax, label='PIE 总分', shrink=0.8)
    ax.axvline(x=pie_df['Potential'].median(), color='#999', linestyle=':', alpha=0.5)
    ax.axhline(y=pie_df['Importance'].median(), color='#999', linestyle=':', alpha=0.5)
    ax.grid(alpha=0.3)
    plt.tight_layout()
    path = CHART_DIR / '10_pie_matrix.png'
    fig.savefig(path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    logger.info("已保存: %s", path)
    return str(path)
