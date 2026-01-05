import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import contextily as ctx # 用于添加底图
import os # 用于创建输出文件夹

# --- 配置区域 ---
# !! 修改为你实际的CSV文件路径 !!
CSV_FILE_PATH = 'Data/ewaste_data_full_20250402_003307.csv'
OUTPUT_DIR = 'geospatial_plots'

# 确保输出目录存在
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

# 要绘制的指标列和它们的显示名称
metrics_to_plot = {
    'E-waste Generated (kg/capita)': 'E-waste Gen. (kg/capita)',
    'EEE Put on Market (kg/capita)': 'EEE Market (kg/capita)'
}

# --- 数据加载与准备 ---

print("Loading data...")
try:
    ewaste_df = pd.read_csv(CSV_FILE_PATH)
except FileNotFoundError:
    print(f"错误: CSV 文件未找到于 {CSV_FILE_PATH}")
    exit()

# 清理数据：将 'n/a' 替换为 NaN，并将指标列转换为数字
for col in metrics_to_plot.keys():
    if col in ewaste_df.columns:
        ewaste_df[col] = pd.to_numeric(ewaste_df[col], errors='coerce') # coerce会将无法转换的变成NaN
ewaste_df['Year'] = ewaste_df['Year'].astype(str) # 确保年份是字符串

# 加载世界地图形状文件 (geopandas自带)
# world = gpd.read_file(gpd.datasets.get_path('naturalearth_lowres')) # <<< 这是旧代码，注释掉或删除

# --- 修改后的地图加载与列名处理代码 ---
# !! 将下面的路径替换为你解压后的 ne_110m_admin_0_countries.shp 文件的实际路径 !!
WORLD_SHP_PATH = 'Data/ne_110m_admin_0_countries/ne_110m_admin_0_countries.shp' # <<< 确保这是你正确的路径

try:
    world = gpd.read_file(WORLD_SHP_PATH)
    print(f"成功加载 Shapefile: {WORLD_SHP_PATH}")
    print("Shapefile 的列名是:")
    print(world.columns) # <<< 打印列名，方便你确认正确的国家名称列
except Exception as e:
    print(f"错误: 无法加载 Shapefile '{WORLD_SHP_PATH}'. 请检查路径是否正确以及文件是否完整。错误信息: {e}")
    exit()

# --- !! 在这里暂停一下，查看上面打印出的列名 !! ---
# --- !! 并将下面 CORRECT_NAME_COLUMN 的值修改为实际的国家名称列名 !! ---
# 常见可能性: 'ADMIN', 'NAME', 'NAME_EN', 'NAME_LONG', 'SOVEREIGNT', 'GU_A3' 等
CORRECT_NAME_COLUMN = 'ADMIN' # <<< 在这里修改为你找到的正确列名！

# 检查选择的列名是否存在
if CORRECT_NAME_COLUMN not in world.columns:
    print(f"错误: 您选择的国家名称列 '{CORRECT_NAME_COLUMN}' 不存在于 Shapefile 中。")
    print(f"可用的列名是: {world.columns.tolist()}")
    exit()
else:
     print(f"使用 Shapefile 中的 '{CORRECT_NAME_COLUMN}' 列作为国家名称进行匹配。")


# --- 后续处理，使用正确的列名 ---
# 移除南极洲
try:
    world = world[(world[CORRECT_NAME_COLUMN] != "Antarctica")]
except KeyError:
     print(f"警告: 无法基于列 '{CORRECT_NAME_COLUMN}' 筛选南极洲。请确保该列包含 'Antarctica' 值或调整筛选逻辑。")

# --- 数据准备 (Name mapping for ewaste_df, 保持不变) ---
name_mapping = {
    "United States of America": "United States", "Russian Federation": "Russia",
    "Republic of Korea": "South Korea", "Iran (Islamic Republic of)": "Iran",
    "Bolivia (Plurinational State of)": "Bolivia", "Venezuela (Bolivarian Republic of)": "Venezuela",
    "Viet Nam": "Vietnam", "Syrian Arab Republic": "Syria",
    "United Republic of Tanzania": "Tanzania", "The former Yugoslav Republic of Macedonia": "North Macedonia",
    "Swaziland": "Eswatini", "Czech Republic": "Czechia",
    "Lao People's Democratic Republic": "Laos"
    # ... 您可能需要添加更多 ...
}
# 应用映射到 ewaste_df 的新列 (这一步仍然是需要的)
ewaste_df['Name_mapped'] = ewaste_df['Name'].replace(name_mapping)


# --- 合并数据，使用正确的列名 ---
ewaste_countries = ewaste_df[ewaste_df['Category'] == 'Country'].copy()
print("Merging geospatial and e-waste data...")
try:
    # 使用 world 数据框中的 CORRECT_NAME_COLUMN 和 ewaste_df 数据框中的 Name_mapped 进行合并
    merged_gdf = world.merge(ewaste_countries, left_on=CORRECT_NAME_COLUMN, right_on='Name_mapped', how='left')
    print("数据合并成功。")
    # 可以在这里检查一下合并后的数据有多少行匹配成功
    print(f"合并后非空匹配行数: {merged_gdf['Name'].notna().sum()}")
    print(f"合并后总行数: {len(merged_gdf)}")
except KeyError as e:
     print(f"错误: 合并数据时出错。请检查列名是否正确。错误信息: {e}")
     exit()
except Exception as e:
     print(f"错误: 合并数据时发生未知错误。错误信息: {e}")
     exit()

# --- 绘图函数和后续代码 (保持不变) ---

# ... (绘图函数和后续代码) ...

# --- 定义绘图函数 ---

def plot_choropleth(gdf, column, year, title, filename, cmap='viridis', add_basemap=True, scheme='Quantiles', k=7):
    """绘制分级统计地图"""
    fig, ax = plt.subplots(1, 1, figsize=(16, 10))
    
    # 筛选特定年份的数据
    data_to_plot = gdf[gdf['Year'] == year].copy()
    
    if data_to_plot.empty or data_to_plot[column].isnull().all():
        print(f"警告: {year} 年的 {column} 没有有效数据可绘制地图。将绘制空白世界地图。")
        world.plot(ax=ax, color='lightgrey', edgecolor='k', linewidth=0.5) # 画出世界轮廓
    else:
        data_to_plot.plot(column=column,
                          ax=ax,
                          legend=True,
                          cmap=cmap,
                          missing_kwds={ # 控制无数据的区域显示
                              "color": "lightgrey",
                              "edgecolor": "grey",
                              "hatch": "///",
                              "label": "No data",
                          },
                          scheme=scheme, # 使用分位数分级，适应偏态分布
                          k=k, # 分成 k 个等级
                          legend_kwds={'title': metrics_to_plot[column],
                                       'loc': 'lower left'})
                          
    # 移除坐标轴
    ax.set_axis_off()
    
    # 添加底图 (可选，如果下载失败或不需要可以注释掉)
    if add_basemap:
        try:
            # 使用 Web Mercator 投影 (EPSG:3857) 以匹配 contextily 底图
            current_crs = data_to_plot.crs
            data_to_plot_wm = data_to_plot.to_crs(epsg=3857)
            ctx.add_basemap(ax, crs=data_to_plot_wm.crs.to_string(), source=ctx.providers.CartoDB.PositronNoLabels)
            # 重设坐标系回原来的，如果需要的话（通常绘图后不需要）
            # ax.to_crs(current_crs) # 这行通常不需要，因为我们只用底图
        except Exception as e:
            print(f"警告: 添加底图失败 - {e}. 将不显示底图。")

    # 添加标题
    ax.set_title(f'{title} ({year})', fontsize=16)
    
    # 保存图像
    filepath = os.path.join(OUTPUT_DIR, filename)
    plt.savefig(filepath, dpi=300, bbox_inches='tight')
    print(f"地图已保存到: {filepath}")
    plt.close(fig) # 关闭图形，释放内存

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

# 绘图循环 (修改了 plot_choropleth 调用为原来的专用绘图逻辑)
for year in ['2018', '2022']:
    for metric_col, metric_name in metrics_to_plot.items():
        fig, ax = plt.subplots(1, 1, figsize=(10, 8))
        world.plot(ax=ax, color='lightgrey', edgecolor='white', linewidth=0.5)
        
        data_to_plot = cjk_gdf[cjk_gdf['Year'] == year]
        
        if not data_to_plot.empty and not data_to_plot[metric_col].isnull().all():
            data_to_plot.plot(column=metric_col, ax=ax, legend=True, cmap='viridis',
                              scheme='Quantiles', k=min(len(data_to_plot[metric_col].unique()), 3),
                              legend_kwds={'title': metric_name, 'loc': 'lower left'})
            for idx, row in data_to_plot.iterrows():
                 # 使用 CORRECT_NAME_COLUMN 显示标签
                 country_label = row[CORRECT_NAME_COLUMN] 
                 if not pd.isna(row.geometry.centroid.x) and not pd.isna(row.geometry.centroid.y):
                     plt.text(row.geometry.centroid.x, row.geometry.centroid.y,
                              f"{country_label}\n{row[metric_col]:.1f}",
                              fontsize=9, ha='center', color='black', weight='bold')
                 else:
                      print(f"警告: {country_label} 的几何中心无效，无法添加标签。")

        ax.set_axis_off()
        ax.set_title(f'CJK Comparison {metric_name} ({year})', fontsize=14)
        minx, miny, maxx, maxy = data_to_plot.total_bounds
        if all(v is not None for v in [minx, miny, maxx, maxy]):
             ax.set_xlim(minx - 15, maxx + 15)
             ax.set_ylim(miny - 10, maxy + 15)
        else:
             print(f"警告: 无法为CJK {year} {metric_name} 设置聚焦范围，边界无效。")

        filename = f'compare_cjk_{metric_col.replace(" ", "_").replace("/", "per").replace("(","").replace(")","").replace("%","pct")}_{year}.png'
        filepath = os.path.join(OUTPUT_DIR, filename)
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        print(f"地图已保存到: {filepath}")
        plt.close(fig)

# ... (后续代码不变) ...

for year in ['2018', '2022']:
    for metric_col, metric_name in metrics_to_plot.items():
        fig, ax = plt.subplots(1, 1, figsize=(10, 8))
        # 绘制底图 (所有国家，浅灰色)
        world.plot(ax=ax, color='lightgrey', edgecolor='white', linewidth=0.5)
        
        data_to_plot = cjk_gdf[cjk_gdf['Year'] == year]
        
        if not data_to_plot.empty and not data_to_plot[metric_col].isnull().all():
            data_to_plot.plot(column=metric_col,
                              ax=ax,
                              legend=True,
                              cmap='viridis',
                              scheme='Quantiles',
                              k=min(len(data_to_plot[metric_col].unique()), 3),
                              legend_kwds={'title': metric_name, 'loc': 'lower left'})
            # 添加标签
            for idx, row in data_to_plot.iterrows():
                 # 使用 CORRECT_NAME_COLUMN 显示标签
                 # country_label = row[CORRECT_NAME_COLUMN] # 这行可以保留或者直接用下面的方式
                 if not pd.isna(row.geometry.centroid.x) and not pd.isna(row.geometry.centroid.y):
                     plt.text(row.geometry.centroid.x, row.geometry.centroid.y,
                              # f"{row['name']}\n{row[metric_col]:.1f}", # <<< 旧代码，错误发生在这里
                              f"{row[CORRECT_NAME_COLUMN]}\n{row[metric_col]:.1f}", # <<< 修改：使用 CORRECT_NAME_COLUMN
                              fontsize=9, ha='center', color='black', weight='bold')
                 else:
                      # print(f"警告: {country_label} 的几何中心无效，无法添加标签。") # 旧代码
                      print(f"警告: {row[CORRECT_NAME_COLUMN]} 的几何中心无效，无法添加标签。") # <<< 修改：使用 CORRECT_NAME_COLUMN

        ax.set_axis_off()
        ax.set_title(f'CJK Comparison {metric_name} ({year})', fontsize=14)
        # 聚焦中日韩区域
        minx, miny, maxx, maxy = data_to_plot.total_bounds
        if all(v is not None for v in [minx, miny, maxx, maxy]):
             ax.set_xlim(minx - 15, maxx + 15)
             ax.set_ylim(miny - 10, maxy + 15)
        else:
             print(f"警告: 无法为CJK {year} {metric_name} 设置聚焦范围，边界无效。")

        filename = f'compare_cjk_{metric_col.replace(" ", "_").replace("/", "per").replace("(","").replace(")","").replace("%","pct")}_{year}.png'
        filepath = os.path.join(OUTPUT_DIR, filename)
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        print(f"地图已保存到: {filepath}")
        plt.close(fig)

# --- 关于 3D 效果的说明 ---
print("\n--- 关于 3D 地理空间展示 ---")
print("使用标准 Python 库（如 Matplotlib/Geopandas）直接根据数据值挤压国家轮廓（真3D效果）非常复杂。")
print("这通常需要专门的3D可视化库（如 Pydeck, KeplerGL，通常用于Jupyter环境）或专业的GIS软件。")
print("作为替代方案，刚才生成的2D分级统计地图通过颜色深浅来表示数值高低。")
print("您也可以考虑在报告中补充标准的3D柱状图（非地理形状）来展示关键实体的数值对比。")
print("例如，用 Matplotlib 的 'mplot3d' 绘制简单的3D条形图比较中、美、日、德2022年的人均产生量。")
print("------")

print("\n所有绘图任务完成！图像保存在 '{}' 文件夹中。".format(OUTPUT_DIR))