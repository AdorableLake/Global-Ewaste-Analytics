import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import contextily as ctx
import os
import numpy as np
import warnings

# --- 配置 ---
CSV_FILE_PATH = '/Users/lakexia/Library/Mobile Documents/com~apple~CloudDocs/GTSI/25Spring/CSE6242/Project/02_DataProcess/Data/ewaste_data_full_20250402_003307.csv'
WORLD_SHP_PATH = '/Users/lakexia/Library/Mobile Documents/com~apple~CloudDocs/GTSI/25Spring/CSE6242/Project/02_DataProcess/Data/ne_110m_admin_0_countries/ne_110m_admin_0_countries.shp'
OUTPUT_DIR_POSTER = 'poster_visuals_map_line_bar' # <<< 新的输出目录名
CORRECT_NAME_COLUMN = 'ADMIN' # <<< 确认这是你找到的正确列名

if not os.path.exists(OUTPUT_DIR_POSTER):
    os.makedirs(OUTPUT_DIR_POSTER)

# --- 数据加载与准备 (简化版) ---
print("Loading and preparing data...")
try:
    ewaste_df = pd.read_csv(CSV_FILE_PATH)
    world = gpd.read_file(WORLD_SHP_PATH)
except Exception as e:
    print(f"Error loading data: {e}")
    exit()

# 清理和转换 (包括总量列)
numeric_cols = ['Population', 'E-waste Generated (kg/capita)', 'E-waste Collection Rate (%)', 
                'E-waste Generated (kt)', 'EEE Put on Market (kt)', 'E-waste Formally Collected (kt)'] # <<< 包含总量列
for col in numeric_cols:
    if col in ewaste_df.columns:
        ewaste_df[col] = pd.to_numeric(ewaste_df[col], errors='coerce')
ewaste_df['Year'] = ewaste_df['Year'].astype(str)
ewaste_df['Population'] = pd.to_numeric(ewaste_df['Population'], errors='coerce')

# 国家名称映射
name_mapping = {
    "United States of America": "United States", "Russian Federation": "Russia",
    "Republic of Korea": "South Korea", "Iran (Islamic Republic of)": "Iran",
    # ... (其他映射) ...
    "Czech Republic": "Czechia"
}
ewaste_df['Name_mapped'] = ewaste_df['Name'].replace(name_mapping)

# 合并国家数据
world = world[(world[CORRECT_NAME_COLUMN] != "Antarctica")]
ewaste_countries = ewaste_df[ewaste_df['Category'] == 'Country'].copy()
merged_gdf = world.merge(ewaste_countries, left_on=CORRECT_NAME_COLUMN, right_on='Name_mapped', how='left')

# 准备大洲数据
ewaste_continents = ewaste_df[ewaste_df['Category'] == 'Continent'].copy()


# --- 图 1: 全球回收率地图 (2022) ---
print("Generating Global Collection Rate Map (2022)...")
fig_map, ax_map = plt.subplots(1, 1, figsize=(14, 8)) # 单独地图可以大一点
data_plot_rate = merged_gdf[merged_gdf['Year'] == '2022']
metric_col_rate = 'E-waste Collection Rate (%)'
metric_name_rate = 'Collection Rate (%)' # 用于图例

if not data_plot_rate.empty and data_plot_rate[metric_col_rate].notna().any():
     with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        data_plot_rate.plot(column=metric_col_rate, ax=ax_map, legend=True,
                        cmap='YlGnBu', missing_kwds={"color": "lightgrey", "label": "No data"},
                        scheme='Quantiles', k=5, vmin=0, vmax=100, # 固定范围 0-100%
                        legend_kwds={'loc': 'lower left'}) # 移除 shrink 和 title
else:
    world.plot(ax=ax_map, color='lightgrey')
ax_map.set_title('Formal E-waste Collection Rate (2022)', fontsize=16)
ax_map.set_axis_off()
try:
    ctx.add_basemap(ax_map, crs=world.crs.to_string(), source=ctx.providers.CartoDB.PositronNoLabels)
except Exception as e: print(f"Basemap error ax_map: {e}")

plt.tight_layout()
filepath1 = os.path.join(OUTPUT_DIR_POSTER, 'map_global_collection_rate_2022.png')
plt.savefig(filepath1, dpi=200, bbox_inches='tight')
print(f"Map saved to: {filepath1}")
plt.close(fig_map)


# --- 图 2: 全球总量趋势折线图 (2018-2022) ---
print("Generating Global Trend Line Chart (2018-2022)...")
# 按年份计算全球总量 (加总所有国家的数据，如果没有全球总计行)
# 注意：这假设 merged_gdf 包含所有国家，并且 'E-waste Generated (kt)' 等列存在
if 'E-waste Generated (kt)' in merged_gdf.columns and 'E-waste Formally Collected (kt)' in merged_gdf.columns:
    global_totals = merged_gdf.groupby('Year')[['E-waste Generated (kt)', 'E-waste Formally Collected (kt)']].sum()
    # 确保年份顺序
    years_numeric = sorted([int(y) for y in ewaste_df['Year'].unique()])
    global_totals = global_totals.reindex([str(y) for y in years_numeric]) # 按数字排序后的年份索引

    fig_line, ax_line = plt.subplots(figsize=(10, 6))

    global_totals['E-waste Generated (kt)'].plot(ax=ax_line, marker='o', label='Generated (kt)', color='firebrick')
    global_totals['E-waste Formally Collected (kt)'].plot(ax=ax_line, marker='s', label='Collected (kt)', color='dodgerblue')

    # 填充两者之间的区域，表示未回收量
    ax_line.fill_between(global_totals.index, 
                         global_totals['E-waste Generated (kt)'], 
                         global_totals['E-waste Formally Collected (kt)'], 
                         color='lightcoral', alpha=0.3, label='Uncollected Gap')

    plt.title('Global E-waste Generation vs. Formal Collection Trend (2018-2022)', fontsize=14)
    plt.xlabel('Year', fontsize=12)
    plt.ylabel('Amount (kilotons, kt)', fontsize=12)
    plt.xticks(rotation=0) # 保持年份标签水平
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.legend()
    plt.tight_layout()

    filepath2 = os.path.join(OUTPUT_DIR_POSTER, 'line_global_generation_vs_collection.png')
    plt.savefig(filepath2, dpi=200, bbox_inches='tight')
    print(f"Line chart saved to: {filepath2}")
    plt.close(fig_line)
else:
    print("警告: 无法生成全球趋势折线图，缺少 'E-waste Generated (kt)' 或 'E-waste Formally Collected (kt)' 列。")


# --- 图 3: 大洲对比柱状图 (2022) ---
print("Generating Continental Comparison Bar Chart (2022)...")
# (这部分代码与之前的回复基本相同，直接使用)
continents_to_show = ['Africa', 'Americas', 'Asia', 'Europe', 'Oceania']
# 获取2022年大洲数据
continents_2022 = ewaste_continents[ewaste_continents['Year'] == '2022'].set_index('Name')
data_bar = continents_2022.loc[continents_to_show, ['E-waste Generated (kg/capita)', 'E-waste Collection Rate (%)']].copy()

fig_bar, ax1_bar = plt.subplots(figsize=(10, 6.5)) # 调整高度以容纳图例
bar_width = 0.35
index = np.arange(len(data_bar.index))

# 左 Y 轴 - Generation
color_gen = 'steelblue'
rects1 = ax1_bar.bar(index - bar_width/2, data_bar['E-waste Generated (kg/capita)'], bar_width, label='Gen. (kg/capita)', color=color_gen)
ax1_bar.set_xlabel('Continent', fontsize=12)
ax1_bar.set_ylabel('E-waste Generated (kg/capita)', color=color_gen, fontsize=12)
ax1_bar.tick_params(axis='y', labelcolor=color_gen)
ax1_bar.set_xticks(index)
ax1_bar.set_xticklabels(data_bar.index, rotation=30, ha='right')

# 右 Y 轴 - Collection Rate
ax2_bar = ax1_bar.twinx()
color_rate = 'orange'
rects2 = ax2_bar.bar(index + bar_width/2, data_bar['E-waste Collection Rate (%)'], bar_width, label='Coll. Rate (%)', color=color_rate)
ax2_bar.set_ylabel('Collection Rate (%)', color=color_rate, fontsize=12)
ax2_bar.tick_params(axis='y', labelcolor=color_rate)
ax2_bar.set_ylim(0, 100)

# 添加标签
ax1_bar.bar_label(rects1, fmt='%.1f', padding=3, fontsize=8)
ax2_bar.bar_label(rects2, fmt='%.1f%%', padding=3, fontsize=8)

plt.title('Continental E-waste Performance (2022)', fontsize=14)
# 合并图例并放在图下方
lines, labels = ax1_bar.get_legend_handles_labels()
lines2, labels2 = ax2_bar.get_legend_handles_labels()
fig_bar.legend(lines + lines2, labels + labels2, loc='lower center', bbox_to_anchor=(0.5, -0.05), ncol=2, fontsize=10) # 调整位置和字体大小

plt.subplots_adjust(bottom=0.25) # 增加底部边距给图例留空间
filepath3 = os.path.join(OUTPUT_DIR_POSTER, 'bar_continent_comparison_2022.png')
plt.savefig(filepath3, dpi=200, bbox_inches='tight')
print(f"Bar chart saved to: {filepath3}")
plt.close(fig_bar)

print("\n海报可视化图片 (地图、折线图、柱状图) 生成完成！保存在 '{}' 文件夹中。".format(OUTPUT_DIR_POSTER))