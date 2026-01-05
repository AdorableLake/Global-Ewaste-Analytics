import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D # <<< 新增：用于 3D 绘图
import contextily as ctx
import os
import imageio
import numpy as np
import glob
import warnings # <<< 新增：用于管理警告

# --- 配置区域 ---
CSV_FILE_PATH = 'Data/ewaste_data_full_20250402_003307.csv'
OUTPUT_DIR = 'geospatial_plots'
GIF_OUTPUT_DIR = os.path.join(OUTPUT_DIR, 'gifs')
FRAMES_TEMP_DIR = os.path.join(OUTPUT_DIR, 'temp_frames')
CHART_OUTPUT_DIR = os.path.join(OUTPUT_DIR, 'charts') # <<< 新增：存放条形图和3D图

# 确保输出目录存在
for dir_path in [OUTPUT_DIR, GIF_OUTPUT_DIR, FRAMES_TEMP_DIR, CHART_OUTPUT_DIR]:
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)

metrics_to_plot = {
    'E-waste Generated (kg/capita)': 'E-waste Gen. (kg/capita)',
    'EEE Put on Market (kg/capita)': 'EEE Market (kg/capita)'
}
YEARS = ['2018', '2019', '2020', '2021', '2022']
YEARS_COMPARE = ['2018', '2022'] # 用于对比的年份

# --- 数据加载与准备 ---
print("Loading data...")
# ... (保持不变，直到合并数据之前) ...
try:
    ewaste_df = pd.read_csv(CSV_FILE_PATH)
except FileNotFoundError:
    print(f"错误: CSV 文件未找到于 {CSV_FILE_PATH}")
    exit()

for col in metrics_to_plot.keys():
    if col in ewaste_df.columns:
        ewaste_df[col] = pd.to_numeric(ewaste_df[col], errors='coerce')
ewaste_df['Year'] = ewaste_df['Year'].astype(str)
ewaste_df['Population'] = pd.to_numeric(ewaste_df['Population'], errors='coerce') # <<< 确保人口也是数字

WORLD_SHP_PATH = 'Data/ne_110m_admin_0_countries/ne_110m_admin_0_countries.shp'
try:
    world = gpd.read_file(WORLD_SHP_PATH)
    print(f"成功加载 Shapefile: {WORLD_SHP_PATH}")
    # print("Shapefile 的列名是:") # 可以取消注释来查看
    # print(world.columns)
except Exception as e:
    print(f"错误: 无法加载 Shapefile '{WORLD_SHP_PATH}'. 错误: {e}")
    exit()

CORRECT_NAME_COLUMN = 'ADMIN' # <<< 确认这是正确的列名
if CORRECT_NAME_COLUMN not in world.columns:
    print(f"错误: 列 '{CORRECT_NAME_COLUMN}' 不在 Shapefile 中。")
    exit()
else:
     print(f"使用 Shapefile 中的 '{CORRECT_NAME_COLUMN}' 列进行国家匹配。")

try:
    world = world[(world[CORRECT_NAME_COLUMN] != "Antarctica")]
except KeyError:
     print(f"警告: 无法基于列 '{CORRECT_NAME_COLUMN}' 筛选南极洲。")

name_mapping = {
    "United States of America": "United States", "Russian Federation": "Russia",
    "Republic of Korea": "South Korea", "Iran (Islamic Republic of)": "Iran",
    "Bolivia (Plurinational State of)": "Bolivia", "Venezuela (Bolivarian Republic of)": "Venezuela",
    "Viet Nam": "Vietnam", "Syrian Arab Republic": "Syria",
    "United Republic of Tanzania": "Tanzania", "The former Yugoslav Republic of Macedonia": "North Macedonia",
    "Swaziland": "Eswatini", "Czech Republic": "Czechia",
    "Lao People's Democratic Republic": "Laos"
    # ... 添加更多 ...
}
ewaste_df['Name_mapped'] = ewaste_df['Name'].replace(name_mapping)

# --- 分离不同层级的数据 ---
ewaste_countries = ewaste_df[ewaste_df['Category'] == 'Country'].copy()
ewaste_regions = ewaste_df[ewaste_df['Category'] == 'Region'].copy() # <<< 新增
ewaste_continents = ewaste_df[ewaste_df['Category'] == 'Continent'].copy() # <<< 新增

# --- 合并国家级地理数据 ---
print("Merging country-level geospatial and e-waste data...")
try:
    merged_gdf = world.merge(ewaste_countries, left_on=CORRECT_NAME_COLUMN, right_on='Name_mapped', how='left')
    print("国家级数据合并成功。")
    print(f"合并后非空匹配国家行数: {merged_gdf['Name'].notna().sum()}")
    print(f"合并后总地理实体数: {len(merged_gdf)}")
except Exception as e:
     print(f"错误: 合并国家级数据时出错。错误: {e}")
     exit()

# --- 绘图函数定义 ---
# plot_choropleth 函数保持不变 (省略以节省空间)
def plot_choropleth(gdf, column, year, title, filename, cmap='viridis', add_basemap=True, scheme='Quantiles', k=7):
    """绘制分级统计地图 (修正 legend_kwds - 移除 loc)"""
    fig, ax = plt.subplots(1, 1, figsize=(16, 10))
    data_to_plot = gdf[gdf['Year'] == year].copy()

    if data_to_plot.empty or data_to_plot[column].isnull().all():
        print(f"警告: {year} 年的 {column} 没有有效数据可绘制地图。")
        world.plot(ax=ax, color='lightgrey', edgecolor='k', linewidth=0.5)
    else:
        with warnings.catch_warnings(): 
            warnings.simplefilter("ignore", UserWarning)
            # <<< 修改：移除 legend_kwds 中的 'loc' >>>
            plot_result = data_to_plot.plot(column=column,
                              ax=ax,
                              legend=True,
                              cmap=cmap,
                              missing_kwds={
                                  "color": "lightgrey", "edgecolor": "grey",
                                  "hatch": "///", "label": "No data"},
                              scheme=scheme, k=k, 
                              legend_kwds={} # <<< 修改：现在为空字典或只包含其他有效参数 (如 shrink)
                              ) 
        # ... (可选的图例标题设置逻辑，如之前所述) ...
        pass 

    ax.set_axis_off()
    if add_basemap:
        try:
            ctx.add_basemap(ax, crs=world.crs.to_string(), source=ctx.providers.CartoDB.PositronNoLabels)
        except Exception as e:
            print(f"警告: 添加底图失败 - {e}.")
    ax.set_title(f'{title} ({year})', fontsize=16)
    filepath = os.path.join(OUTPUT_DIR, filename)
    plt.savefig(filepath, dpi=300, bbox_inches='tight')
    print(f"地图已保存到: {filepath}")
    plt.close(fig)


# plot_single_year_map 函数保持不变 (省略以节省空间)
def plot_single_year_map(gdf, column, year, vmin, vmax, cmap, title_prefix, frame_filename, add_basemap=True):
    """绘制用于GIF的单帧地图。(修正 legend_kwds - 移除 loc)"""
    fig, ax = plt.subplots(1, 1, figsize=(16, 10))
    data_to_plot = gdf[gdf['Year'] == year].copy()

    if data_to_plot.empty or data_to_plot[column].isnull().all():
        print(f"警告: {year} 年的 {column} 没有有效数据。绘制空白帧。")
        world.plot(ax=ax, color='lightgrey', edgecolor='k', linewidth=0.5)
    else:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
             # <<< 修改：移除 legend_kwds 中的 'loc' >>>
            plot_result = data_to_plot.plot(column=column,
                              ax=ax,
                              legend=True,
                              cmap=cmap,
                              vmin=vmin, vmax=vmax,
                              missing_kwds={
                                  "color": "lightgrey", "edgecolor": "grey",
                                  "hatch": "///", "label": "No data"},
                              legend_kwds={'shrink': 0.6} # <<< 修改：移除了 loc，只保留 shrink
                              )
        # ... (可选的图例标题设置逻辑) ...
        pass 

    ax.set_axis_off()
    if add_basemap:
        try:
            ctx.add_basemap(ax, crs=world.crs.to_string(), source=ctx.providers.CartoDB.PositronNoLabels)
        except Exception as e:
            print(f"警告: 添加底图失败 - {e}.")

    ax.set_title(f'{title_prefix} ({year})', fontsize=16)
    plt.savefig(frame_filename, dpi=150, bbox_inches='tight')
    print(f"  帧已保存: {frame_filename}")
    plt.close(fig)

# <<< 新增：绘制大洲/地区对比条形图的函数 >>>
def plot_comparison_bar_chart(df, category_level, entities, years, metric_col, title, filename):
    """绘制对比条形图"""
    print(f"绘制对比条形图: {title}...")
    df_filtered = df[(df['Category'] == category_level) &
                     (df['Name'].isin(entities)) &
                     (df['Year'].isin(years))].copy()

    if df_filtered.empty:
        print(f"警告: 没有找到用于绘制 '{title}' 的数据。")
        return

    # 数据透视，方便绘图
    pivot_df = df_filtered.pivot(index='Name', columns='Year', values=metric_col)
    pivot_df = pivot_df[years] # 确保年份顺序正确
    
    if pivot_df.isnull().all().all():
         print(f"警告: '{title}' 的透视数据全为空。")
         return

    ax = pivot_df.plot(kind='bar', figsize=(12, 7), rot=45, width=0.8) # rot旋转x轴标签

    plt.title(title, fontsize=16)
    plt.ylabel(metrics_to_plot.get(metric_col, metric_col))
    plt.xlabel(category_level)
    plt.xticks(ha='right') # 让旋转后的标签右对齐
    plt.legend(title='Year')
    plt.tight_layout() # 调整布局防止标签重叠

    # 在柱子上添加数值标签
    for container in ax.containers:
        ax.bar_label(container, fmt='%.1f', label_type='edge', padding=3, fontsize=8)

    filepath = os.path.join(CHART_OUTPUT_DIR, filename)
    plt.savefig(filepath, dpi=300, bbox_inches='tight')
    print(f"条形图已保存到: {filepath}")
    plt.close()

# <<< 新增：绘制3D柱状图的函数 >>>
def plot_3d_bar_chart(labels, values, z_label, title, filename):
    """绘制简单的 3D 柱状图"""
    print(f"绘制 3D 柱状图: {title}...")
    if not labels or not values or len(labels) != len(values):
        print(f"警告: 无法绘制 3D 图 '{title}'，标签或数值数据无效。")
        return
        
    fig = plt.figure(figsize=(10, 7))
    ax = fig.add_subplot(111, projection='3d')

    xpos = np.arange(len(labels)) # x 轴位置
    ypos = np.zeros(len(labels))  # y 轴位置 (设为0，让柱子在一条线上)
    zpos = np.zeros(len(labels))  # z 轴起点 (地面)
    dx = np.ones(len(labels)) * 0.6 # x 方向宽度
    dy = np.ones(len(labels)) * 0.6 # y 方向宽度
    dz = values                 # z 方向高度 (数据值)

    # 使用 try-except 捕捉可能的 NaN 或非数值错误
    try:
        valid_dz = [v if pd.notna(v) else 0 for v in dz] # 将 NaN 替换为 0
        colors = plt.cm.viridis(np.array(valid_dz) / max(valid_dz) if max(valid_dz) > 0 else 0) # 根据高度上色
        ax.bar3d(xpos, ypos, zpos, dx, dy, valid_dz, color=colors, zsort='average')
    except Exception as e:
        print(f"警告: 绘制 3D 柱体时出错 '{title}': {e}")
        # 可以选择绘制空图或跳过
        plt.close(fig)
        return

    ax.set_xticks(xpos)
    ax.set_xticklabels(labels, rotation=30, ha='right') # 旋转标签避免重叠
    ax.set_yticks([]) # 隐藏 y 轴刻度
    ax.set_zlabel(z_label)
    plt.title(title, fontsize=16)
    plt.tight_layout()

    filepath = os.path.join(CHART_OUTPUT_DIR, filename)
    plt.savefig(filepath, dpi=300, bbox_inches='tight')
    print(f"3D 图已保存到: {filepath}")
    plt.close(fig)

# --- 绘图执行 ---

# 1. 按大洲/地区/国家对比 2018 vs 2022 人均数据 (绘制全球国家地图)
print("\n绘制全球人均数据地图 (2018 & 2022)...")
for year in ['2018', '2022']:
    for metric_col, metric_name in metrics_to_plot.items():
        plot_choropleth(merged_gdf, metric_col, year,
                        f'Global {metric_name}',
                        f'global_{metric_col.replace(" ", "_").replace("/", "per").replace("(","").replace(")","").replace("%","pct")}_{year}.png',
                        cmap='OrRd' if 'Generated' in metric_col else 'YlGnBu') # 产生用红色系，EEE用蓝色系

# 2. 中国统计区域 (大陆、港、澳、台) 2018 vs 2022 人均数据
print("\n绘制大中华区人均数据地图 (2018 & 2022)...")
greater_china_names = ["China", "China, Hong Kong Special Administrative Region", "China, Macao Special Administrative Region", "Taiwan"]
# 在合并后的 GeoDataFrame 中筛选这些区域
greater_china_gdf = merged_gdf[merged_gdf['Name'].isin(greater_china_names)]

# 由于区域太少，地图效果可能不好，但还是按要求绘制
# 为了突出显示，我们将只绘制这几个区域，背景为灰色
for year in ['2018', '2022']:
    for metric_col, metric_name in metrics_to_plot.items():
        fig, ax = plt.subplots(1, 1, figsize=(10, 8))
        # 绘制底图 (所有国家，浅灰色)
        world.plot(ax=ax, color='lightgrey', edgecolor='white', linewidth=0.5)
        
        data_to_plot = greater_china_gdf[greater_china_gdf['Year'] == year]
        
        if not data_to_plot.empty and not data_to_plot[metric_col].isnull().all():
             data_to_plot.plot(column=metric_col,
                               ax=ax,
                               legend=True,
                               cmap='plasma', # 换个颜色突出显示
                               scheme='Quantiles', # 可能只有几个值，Quantiles可能效果不好，可尝试'UserDefined'或'EqualInterval'
                               k=min(len(data_to_plot[metric_col].unique()), 4), # 级别数不超过不同值的数量
                               legend_kwds={'title': metric_name, 'loc': 'lower left'})
             # 添加标签
             for idx, row in data_to_plot.iterrows():
                 # 检查坐标是否存在
                 if not pd.isna(row.geometry.centroid.x) and not pd.isna(row.geometry.centroid.y):
                     plt.text(row.geometry.centroid.x, row.geometry.centroid.y,
                              f"{row['Name_mapped']}\n{row[metric_col]:.1f}", # 显示名称和数值
                              fontsize=8, ha='center', color='black')
                 else:
                     print(f"警告: {row['Name_mapped']} 的几何中心无效，无法添加标签。")

        ax.set_axis_off()
        ax.set_title(f'Greater China {metric_name} ({year})', fontsize=14)
        # 调整显示范围以聚焦
        minx, miny, maxx, maxy = data_to_plot.total_bounds
        if all(v is not None for v in [minx, miny, maxx, maxy]): # 确保边界有效
             ax.set_xlim(minx - 10, maxx + 10) # 加一点边距
             ax.set_ylim(miny - 10, maxy + 10)
        else:
             print(f"警告: 无法为大中华区 {year} {metric_name} 设置聚焦范围，边界无效。")

        filename = f'greater_china_{metric_col.replace(" ", "_").replace("/", "per").replace("(","").replace(")","").replace("%","pct")}_{year}.png'
        filepath = os.path.join(OUTPUT_DIR, filename)
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        print(f"地图已保存到: {filepath}")
        plt.close(fig)

# ... (前面的代码保持不变) ...

# 3. 中国、美国、欧盟国家对比 2018 vs 2022 人均数据
print("\n绘制 中国 vs 美国 vs 欧盟 人均数据地图 (2018 & 2022)...")
# 欧盟成员国列表 (需要确认是否准确反映该时期, 使用 geopandas 能识别的名称)
eu_countries_in_world_data = [
    'Austria', 'Belgium', 'Bulgaria', 'Croatia', 'Cyprus', 'Czechia', 
    'Denmark', 'Estonia', 'Finland', 'France', 'Germany', 'Greece', 'Hungary',
    'Ireland', 'Italy', 'Latvia', 'Lithuania', 'Luxembourg', 'Malta',
    'Netherlands', 'Poland', 'Portugal', 'Romania', 'Slovakia', 'Slovenia',
    'Spain', 'Sweden'
]
entities_to_compare_eu = ['China', 'United States'] + eu_countries_in_world_data 

# <<< 修改：使用 CORRECT_NAME_COLUMN 进行筛选 >>>
compare_eu_gdf = merged_gdf[merged_gdf[CORRECT_NAME_COLUMN].isin(entities_to_compare_eu) | merged_gdf['Name_mapped'].isin(entities_to_compare_eu)]

# 检查筛选结果
if compare_eu_gdf.empty:
    print(f"警告: 筛选中、美、欧数据后为空，请检查 '{CORRECT_NAME_COLUMN}' 列中的名称和 'entities_to_compare_eu' 列表是否匹配。")
else:
    print(f"筛选到 {len(compare_eu_gdf['geometry'].unique())} 个中、美、欧的地理实体。") # 打印唯一地理实体数量

# 绘图循环 (保持不变)
for year in ['2018', '2022']:
    for metric_col, metric_name in metrics_to_plot.items():
        # ... (调用 plot_choropleth 的代码不变) ...
        plot_choropleth(compare_eu_gdf, metric_col, year,
                        f'China vs USA vs EU {metric_name}',
                        f'compare_chn_us_eu_{metric_col.replace(" ", "_").replace("/", "per").replace("(","").replace(")","").replace("%","pct")}_{year}.png',
                        cmap='coolwarm', 
                        add_basemap=False) 

# 4. 中日韩三国对比 2018 vs 2022 人均数据
print("\n绘制 中日韩 人均数据地图 (2018 & 2022)...")
# 确保 cjk_names_mapped 使用的是与 CORRECT_NAME_COLUMN 或 Name_mapped 中匹配的名称
cjk_names_mapped = ["China", "Japan", "South Korea"] # 假设这些名称在 CORRECT_NAME_COLUMN 或 Name_mapped 中存在

# <<< 修改：使用 CORRECT_NAME_COLUMN 进行筛选 >>>
cjk_gdf = merged_gdf[merged_gdf[CORRECT_NAME_COLUMN].isin(cjk_names_mapped) | merged_gdf['Name_mapped'].isin(cjk_names_mapped)]

# 检查筛选结果
if cjk_gdf.empty:
    print(f"警告: 筛选中、日、韩数据后为空，请检查 '{CORRECT_NAME_COLUMN}' 列中的名称和 'cjk_names_mapped' 列表是否匹配。")
else:
     print(f"筛选到 {len(cjk_gdf['geometry'].unique())} 个中、日、韩的地理实体。")

# <<< 新增：绘制大洲和地区对比条形图 >>>
print("\n--- 开始绘制大洲和地区对比图 ---")
continents_to_show = ['Africa', 'Americas', 'Asia', 'Europe', 'Oceania']
key_regions = ['South-Eastern Asia', 'Eastern Asia', 'Northern Europe', 'Southern Europe', 'Northern America', 'Southern Africa'] # 选一些有代表性的

for metric_col, metric_name in metrics_to_plot.items():
    # 大洲对比
    plot_comparison_bar_chart(ewaste_continents, 'Continent', continents_to_show, YEARS_COMPARE,
                              metric_col, f'Continent Comparison: {metric_name}',
                              f'bar_continent_compare_{metric_col.replace(" ", "_").replace("/", "per").replace("(","").replace(")","").replace("%","pct")}.png')
    # 关键地区对比
    plot_comparison_bar_chart(ewaste_regions, 'Region', key_regions, YEARS_COMPARE,
                              metric_col, f'Key Region Comparison: {metric_name}',
                              f'bar_region_compare_{metric_col.replace(" ", "_").replace("/", "per").replace("(","").replace(")","").replace("%","pct")}.png')

# <<< 新增：绘制 3D 柱状图对比 >>>
print("\n--- 开始绘制 3D 对比图 (2022) ---")
# 准备3D图数据 (中国, 美国, 日本, 德国, 欧盟平均 - 2022)
entities_3d = ['China', 'United States', 'Japan', 'Germany']
labels_3d = ['China', 'USA', 'Japan', 'Germany', 'EU Avg']

# 计算欧盟2022年平均值
eu_countries_names_for_avg = [ # 需要使用 ewaste_df 中的原始 Name 或 Name_mapped
    'Austria', 'Belgium', 'Bulgaria', 'Croatia', 'Cyprus', 'Czechia', 'Denmark', 'Estonia', 'Finland',
    'France', 'Germany', 'Greece', 'Hungary', 'Ireland', 'Italy', 'Latvia', 'Lithuania', 'Luxembourg',
    'Malta', 'Netherlands', 'Poland', 'Portugal', 'Romania', 'Slovakia', 'Slovenia', 'Spain', 'Sweden'
]
# 获取欧盟国家的数据
eu_data_2022 = ewaste_countries[ewaste_countries['Name_mapped'].isin(eu_countries_names_for_avg) & (ewaste_countries['Year'] == '2022')]

for metric_col, metric_name in metrics_to_plot.items():
    values_3d = []
    # 获取中、美、日、德的数据
    for entity in entities_3d:
        val = ewaste_countries[(ewaste_countries['Name_mapped'] == entity) & (ewaste_countries['Year'] == '2022')][metric_col].iloc[0]
        values_3d.append(val)
    
    # 计算欧盟加权平均值 (按人口加权)
    if not eu_data_2022.empty and eu_data_2022[metric_col].notna().any() and eu_data_2022['Population'].notna().any():
        eu_avg = np.nansum(eu_data_2022[metric_col] * eu_data_2022['Population']) / np.nansum(eu_data_2022[eu_data_2022[metric_col].notna()]['Population'])
    else:
        eu_avg = np.nan # 如果没有数据则为 NaN
    values_3d.append(eu_avg)

    # 过滤掉 NaN 值以便绘图（虽然 bar3d 现在处理了，但标签可能需要）
    valid_labels = [lbl for lbl, val in zip(labels_3d, values_3d) if pd.notna(val)]
    valid_values = [val for val in values_3d if pd.notna(val)]
    
    plot_3d_bar_chart(valid_labels, valid_values, metric_name,
                      f'3D Comparison: {metric_name} (2022)',
                      f'bar3d_compare_{metric_col.replace(" ", "_").replace("/", "per").replace("(","").replace(")","").replace("%","pct")}_2022.png')


# --- GIF 生成模块 --- 
# (请确保此模块包含在你的最终脚本中)
print("\n--- 开始生成 GIF 动画 ---")
import imageio # 确保 imageio 已导入
import glob    # 确保 glob 已导入
import numpy as np # 确保 numpy 已导入

# 对每个指标生成一个 GIF
for metric_col, metric_name in metrics_to_plot.items():
    print(f"\n正在为指标 '{metric_name}' 生成 GIF...")
    frame_filenames = []

    # 1. 计算该指标在所有年份的全局最小值和最大值 (忽略 NaN)
    # 注意：确保 merged_gdf 包含所有年份的数据
    valid_years_data = merged_gdf[merged_gdf['Year'].isin(YEARS)][metric_col].dropna()
    if valid_years_data.empty:
         print(f"  警告: 指标 '{metric_name}' 在年份 {YEARS} 中没有有效数值，跳过 GIF。")
         continue
    global_min = valid_years_data.min()
    global_max = valid_years_data.max()
    print(f"  GIF 颜色标度范围 [{global_min:.1f}, {global_max:.1f}]")

    # 2. 为每一年生成地图帧
    temp_frame_dir_metric = os.path.join(FRAMES_TEMP_DIR, metric_col.replace(" ", "_").replace("/", "per").replace("(","").replace(")","").replace("%","pct"))
    if not os.path.exists(temp_frame_dir_metric):
        os.makedirs(temp_frame_dir_metric) # 为每个指标创建子目录
        
    for year in YEARS:
        # 使用更安全的、特定于指标和年份的文件名
        frame_path = os.path.join(temp_frame_dir_metric, f'frame_{year}.png') 
        plot_single_year_map(merged_gdf, metric_col, year,
                             global_min, global_max, # 使用全局范围
                             'OrRd' if 'Generated' in metric_col else 'YlGnBu', # 选择颜色图
                             f'Global {metric_name}',
                             frame_path,
                             add_basemap=False) # 建议关闭底图以加快速度和减小文件大小
        if os.path.exists(frame_path): # 确保文件已生成
             frame_filenames.append(frame_path)
        else:
             print(f"警告: 帧文件未能生成 {frame_path}")

    # 3. 使用 imageio 将帧合成为 GIF (确保有帧生成)
    if frame_filenames:
        gif_path = os.path.join(GIF_OUTPUT_DIR, f'global_{metric_col.replace(" ", "_").replace("/", "per").replace("(","").replace(")","").replace("%","pct")}_2018-2022.gif')
        try:
            print(f"  正在合并 {len(frame_filenames)} 帧到 GIF: {gif_path}...")
            images = [imageio.imread(filename) for filename in sorted(frame_filenames)] # 按年份排序
            # duration 控制每帧显示时间 (秒)，loop=0 表示无限循环
            imageio.mimsave(gif_path, images, duration=1.5, loop=0) 
            print(f"  GIF 已成功保存: {gif_path}")
        except Exception as e:
            print(f"  错误: 生成 GIF 失败 - {e}")

        # 4. (可选) 清理单帧图片
        print("  清理临时帧文件...")
        for filename in frame_filenames:
            try:
                os.remove(filename)
            except OSError as e:
                print(f"    无法删除文件 {filename}: {e}")
        # (可选) 删除临时子目录
        try:
            os.rmdir(temp_frame_dir_metric)
        except OSError as e:
            print(f"    无法删除临时目录 {temp_frame_dir_metric}: {e}") # 可能因为出错而未删除所有文件
    else:
        print(f"  没有成功生成的帧文件，无法创建 GIF。")

# --- GIF 生成模块结束 ---
# --- 关于 3D 效果的说明 (保持不变) ---
print("\n--- 关于 3D 地理空间展示的说明 ---")
print("...") 
print("------")

print("\n所有任务完成！图像保存在 '{}', '{}', 和 '{}' 文件夹中。".format(OUTPUT_DIR, CHART_OUTPUT_DIR, GIF_OUTPUT_DIR))