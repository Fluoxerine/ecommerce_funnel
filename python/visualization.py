"""可视化模块：matplotlib 8 张 + plotly 2 张"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from python.config import (
    FUNNEL_COLORS, PRIMARY, ACCENT, CHART_DIR, logger, FUNNEL_STAGES,
)

matplotlib.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'KaiTi']
matplotlib.rcParams['axes.unicode_minus'] = False

BASE_STYLE = {
    'figure.facecolor': '#F8F9FA', 'axes.facecolor': '#FFFFFF',
    'axes.spines.top': False, 'axes.spines.right': False,
    'axes.grid': True, 'grid.alpha': 0.3, 'grid.linestyle': '--',
    'font.size': 10, 'axes.titlesize': 12, 'axes.titleweight': 'bold',
}
plt.rcParams.update(BASE_STYLE)


def plot_funnel_static(funnel_df: pd.DataFrame) -> str:
    fig, ax = plt.subplots(figsize=(14, 7))
    bars = ax.bar(funnel_df['漏斗阶段'], funnel_df['独立会话数'],
                  color=FUNNEL_COLORS, edgecolor='white', linewidth=2)
    ax.set_title('Ecommerce Conversion Funnel (Session-level)', fontsize=18, pad=20, fontweight='bold')
    ax.set_ylabel('Unique Sessions', fontsize=14)
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
    logger.info("Saved: %s", path)
    return str(path)


def plot_funnel_plotly(funnel_df: pd.DataFrame) -> str:
    fig = px.funnel(funnel_df, x='独立会话数', y='漏斗阶段',
                    title='Ecommerce Conversion Funnel (Interactive)',
                    color_discrete_sequence=['#2E86AB'])
    fig.update_traces(textposition='inside', textfont_size=14)
    fig.update_layout(title_font_size=18, title_x=0.5)
    path = CHART_DIR / '02_funnel_plotly.html'
    fig.write_html(path)
    logger.info("Saved: %s", path)
    return str(path)


def plot_loss_waterfall(loss_df: pd.DataFrame) -> str:
    fig, ax = plt.subplots(figsize=(14, 7))
    stages = loss_df['漏斗环节'].tolist()
    amounts = loss_df['估算损失金额'].values
    colors = ['#E74C3C' if a == max(amounts) else PRIMARY for a in amounts]
    bars = ax.bar(range(len(stages)), amounts, color=colors, edgecolor='white', linewidth=2)
    ax.set_xticks(range(len(stages)))
    ax.set_xticklabels(stages, rotation=20, ha='right', fontsize=11)
    ax.set_ylabel('Estimated Loss (Y)', fontsize=13)
    ax.set_title('Estimated Revenue Loss by Funnel Stage', fontsize=16, pad=20, fontweight='bold')
    for bar, (_, row) in zip(bars, loss_df.iterrows()):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + bar.get_height() * 0.02,
                f'Y{row["估算损失金额"]:,.0f}', ha='center', fontweight='bold', fontsize=11)
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() / 2,
                f'Loss\n{row["环节流失率(%)"]:.1f}%', ha='center', va='center',
                fontweight='bold', fontsize=10, color='white')
    ax.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    path = CHART_DIR / '03_loss_waterfall.png'
    fig.savefig(path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    logger.info("Saved: %s", path)
    return str(path)


def plot_channel_device_heatmap(cross_df: pd.DataFrame) -> str:
    pivot = cross_df.reset_index().pivot(
        index='ReferralSource', columns='DeviceType', values='转化率(%)')
    # Ensure pivot exists and is not empty
    if pivot.empty:
        logger.warning("Empty pivot for channel-device heatmap")
        return ""
    fig, ax = plt.subplots(figsize=(10, 6))
    arr = pivot.values
    vmin, vmax = arr.min(), arr.max()
    im = ax.imshow(arr, cmap='YlOrRd', aspect='auto', vmin=vmin, vmax=vmax)
    ax.set_xticks(range(len(pivot.columns)))
    ax.set_xticklabels(pivot.columns, fontsize=11)
    ax.set_yticks(range(len(pivot.index)))
    ax.set_yticklabels(pivot.index, fontsize=11)
    ax.set_title('Channel x Device Conversion Rate Heatmap (%)', fontsize=15, pad=20, fontweight='bold')
    mid = (vmin + vmax) / 2
    for i in range(len(pivot.index)):
        for j in range(len(pivot.columns)):
            val = arr[i, j]
            text_color = 'white' if val > mid else 'black'
            ax.text(j, i, f'{val:.1f}%', ha='center', va='center',
                    fontweight='bold', color=text_color, fontsize=12)
    plt.colorbar(im, ax=ax, shrink=0.8)
    plt.tight_layout()
    path = CHART_DIR / '04_channel_device_heatmap.png'
    fig.savefig(path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    logger.info("Saved: %s", path)
    return str(path)


def plot_time_analysis(hourly: pd.DataFrame, dow: pd.DataFrame) -> str:
    fig, axes = plt.subplots(1, 2, figsize=(18, 6))
    ax1 = axes[0]
    ax1_twin = ax1.twinx()
    ax1.bar(hourly.index, hourly['会话数'], alpha=0.3, color=PRIMARY)
    ax1_twin.plot(hourly.index, hourly['转化率'], 'o-', color='#E74C3C',
                  linewidth=2, markersize=6)
    ax1.set_xlabel('Hour', fontsize=12)
    ax1.set_ylabel('Sessions', fontsize=12, color=PRIMARY)
    ax1_twin.set_ylabel('Conversion Rate (%)', fontsize=12, color='#E74C3C')
    ax1.set_title('Hourly Traffic & Conversion', fontsize=13, fontweight='bold')
    ax1.set_xticks(range(0, 24, 2))
    ax2 = axes[1]
    ax2_twin = ax2.twinx()
    ax2.bar(dow.index, dow['会话数'], alpha=0.3, color=PRIMARY)
    ax2_twin.plot(dow.index, dow['转化率'], 'o-', color='#E74C3C',
                  linewidth=2, markersize=8)
    ax2.set_xlabel('Day of Week', fontsize=12)
    ax2.set_ylabel('Sessions', fontsize=12, color=PRIMARY)
    ax2_twin.set_ylabel('Conversion Rate (%)', fontsize=12, color='#E74C3C')
    ax2.set_title('Daily Traffic & Conversion', fontsize=13, fontweight='bold')
    fig.suptitle('Traffic & Conversion by Time', fontsize=16, fontweight='bold', y=1.02)
    plt.tight_layout()
    path = CHART_DIR / '05_time_analysis.png'
    fig.savefig(path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    logger.info("Saved: %s", path)
    return str(path)


def plot_stage_duration_boxplot(df_cleaned: pd.DataFrame) -> str:
    stage_order = ['home', 'product_page', 'cart', 'checkout', 'confirmation']
    stage_labels = ['Home', 'Product', 'Cart', 'Checkout', 'Confirm']
    fig, ax = plt.subplots(figsize=(14, 7))
    data_converted, data_lost = [], []
    for stage in stage_order:
        stage_data = df_cleaned[df_cleaned['PageType'] == stage]
        data_converted.append(stage_data[stage_data['session_is_converted'] == 1]['TimeOnPage_seconds'].values)
        data_lost.append(stage_data[stage_data['session_is_converted'] == 0]['TimeOnPage_seconds'].values)
    positions = np.arange(len(stage_order)) * 2
    bp1 = ax.boxplot(data_converted, positions=positions - 0.35, widths=0.5,
                     patch_artist=True, boxprops=dict(facecolor='#2ECC71', alpha=0.6),
                     medianprops=dict(color='#27AE60', linewidth=2))
    bp2 = ax.boxplot(data_lost, positions=positions + 0.35, widths=0.5,
                     patch_artist=True, boxprops=dict(facecolor='#E74C3C', alpha=0.6),
                     medianprops=dict(color='#C0392B', linewidth=2))
    ax.set_xticks(positions)
    ax.set_xticklabels(stage_labels, fontsize=11)
    ax.set_ylabel('Time on Page (seconds)', fontsize=12)
    ax.set_title('Page Duration: Converted vs Lost Users', fontsize=15, pad=20, fontweight='bold')
    ax.legend([bp1['boxes'][0], bp2['boxes'][0]], ['Converted', 'Lost'], fontsize=11)
    ax.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    path = CHART_DIR / '06_stage_duration_boxplot.png'
    fig.savefig(path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    logger.info("Saved: %s", path)
    return str(path)


def plot_entry_path(entry_df: pd.DataFrame) -> str:
    fig, ax = plt.subplots(figsize=(10, 6))
    colors = ['#27AE60', '#2E86AB', '#F39C12', '#E74C3C', '#9B59B6'][:len(entry_df)]
    bars = ax.bar(entry_df.index, entry_df['转化率(%)'], color=colors, edgecolor='white', linewidth=2)
    ax.set_title('Conversion Rate by Landing Page', fontsize=15, pad=20, fontweight='bold')
    ax.set_ylabel('Conversion Rate (%)', fontsize=12)
    ax.set_xlabel('First Page in Session', fontsize=12)
    for bar, (_, row) in zip(bars, entry_df.iterrows()):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.5,
                f"{row['转化率(%)']:.1f}%\n({int(row['会话数']):,} sess)",
                ha='center', fontweight='bold', fontsize=10)
    ax.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    path = CHART_DIR / '07_entry_path.png'
    fig.savefig(path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    logger.info("Saved: %s", path)
    return str(path)


def plot_cart_channel_bubble(df_cleaned: pd.DataFrame, funnel_wide: pd.DataFrame) -> str:
    cart_info = df_cleaned[df_cleaned['PageType'] == 'cart'] \
        .groupby('SessionID')['ItemsInCart'].max().reset_index()
    cart_info = cart_info.merge(
        funnel_wide[['SessionID', 'ReferralSource', 'is_purchased']],
        on='SessionID', how='inner')
    fig, ax = plt.subplots(figsize=(14, 7))
    channels = sorted(cart_info['ReferralSource'].unique())
    ch_colors = {'Direct': '#2E86AB', 'Email': '#A23B72',
                 'Google': '#F18F01', 'Social Media': '#C73E1D'}
    offsets = {ch: i * 0.06 for i, ch in enumerate(channels)}
    for ch in channels:
        ch_data = cart_info[cart_info['ReferralSource'] == ch]
        ax.scatter(ch_data['ItemsInCart'] + offsets.get(ch, 0),
                   ch_data['is_purchased'] + np.random.uniform(-0.02, 0.02, len(ch_data)),
                   s=100, alpha=0.4, c=ch_colors.get(ch, PRIMARY),
                   label=ch, edgecolors='white')
    ax.set_xlabel('Cart Items', fontsize=12)
    ax.set_ylabel('Converted', fontsize=12)
    ax.set_yticks([0, 1])
    ax.set_yticklabels(['No', 'Yes'])
    ax.set_title('Cart Items x Channel x Conversion', fontsize=15, pad=20, fontweight='bold')
    ax.legend(title='Channel', fontsize=10)
    ax.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    path = CHART_DIR / '08_cart_channel_bubble.png'
    fig.savefig(path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    logger.info("Saved: %s", path)
    return str(path)


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
                  label=all_labels, color='#2E86AB'),
        link=dict(source=sources, target=targets, value=values),
    ))
    fig.update_layout(title_text='User Path Flow (Top 15)', title_font_size=18, title_x=0.5)
    path = CHART_DIR / '09_path_sankey.html'
    fig.write_html(path)
    logger.info("Saved: %s", path)
    return str(path)


def plot_pie_matrix(pie_df: pd.DataFrame) -> str:
    fig, ax = plt.subplots(figsize=(12, 8))
    scatter = ax.scatter(
        pie_df['Potential'], pie_df['Importance'],
        s=pie_df['Ease'] * 80, c=pie_df['PIE得分'],
        cmap='RdYlGn', alpha=0.7, edgecolors='#333', linewidth=0.5,
    )
    for _, row in pie_df.iterrows():
        ax.annotate(row['漏斗环节'], (row['Potential'], row['Importance']),
                    textcoords="offset points", xytext=(8, 4), fontsize=9, fontweight='bold')
    ax.set_xlabel('Potential (Recovery Value)', fontsize=12)
    ax.set_ylabel('Importance (Affected Users)', fontsize=12)
    ax.set_title('PIE Priority Matrix (Bubble=Ease)', fontsize=15, pad=20, fontweight='bold')
    plt.colorbar(scatter, ax=ax, label='PIE Score', shrink=0.8)
    ax.axvline(x=pie_df['Potential'].median(), color='#999', linestyle=':', alpha=0.5)
    ax.axhline(y=pie_df['Importance'].median(), color='#999', linestyle=':', alpha=0.5)
    ax.grid(alpha=0.3)
    plt.tight_layout()
    path = CHART_DIR / '10_pie_matrix.png'
    fig.savefig(path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    logger.info("Saved: %s", path)
    return str(path)
