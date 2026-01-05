import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import json
from datetime import datetime
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import os
import argparse # Import argparse for command-line arguments

class EwasteDataCollector:
    # --- (Keep the EwasteDataCollector class exactly as it was in the previous "production" version) ---
    # --- (No changes needed inside this class) ---
    def __init__(self):
        """初始化数据收集器"""
        self.session = self._create_session()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3', # 使用常见的 User-Agent
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5', # 偏好英文内容，减少因语言变化导致解析失败的可能
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }

    def _create_session(self):
        """创建带有重试机制的会话"""
        session = requests.Session()
        retry = Retry(
            total=5,              # 总重试次数
            backoff_factor=1,     # 重试间隔时间指数增长因子 (1s, 2s, 4s, 8s, 16s)
            status_forcelist=[429, 500, 502, 503, 504], # 增加 429 Too Many Requests
            allowed_methods=frozenset(['GET', 'POST']) # 明确允许的方法
        )
        adapter = HTTPAdapter(max_retries=retry)
        session.mount('http://', adapter)
        session.mount('https://', adapter)
        return session

    def _extract_number(self, text):
        """从文本中提取数字，处理 'n/a' 和潜在错误"""
        if not text:
            return None
        text_cleaned = text.strip().lower()
        if text_cleaned == 'n/a':
            return 'n/a' # 保留 n/a 作为一个明确的值
        text_cleaned = text_cleaned.replace(',', '')
        try:
            # 尝试提取浮点数
            num_str = ''.join(filter(lambda x: x.isdigit() or x == '.', text_cleaned))
            if num_str: # 确保过滤后还有内容
                 # 检查是否只有一个小数点
                if num_str.count('.') <= 1:
                    return float(num_str)
                else:
                    # 如果有多个小数点，可能是错误数据，尝试只取第一部分
                    parts = num_str.split('.')
                    valid_num_str = parts[0] + '.' + parts[1] if len(parts) > 1 else parts[0]
                    return float(valid_num_str)

            else: # 如果过滤后为空 (例如只有 '%')
                 return None

        except ValueError:
             # print(f"  警告：无法将文本 '{text}' 解析为数字。") # 在生产模式中可以注释掉详细警告
             return None # 解析失败返回 None
        except Exception as e:
            print(f"  警告：提取数字时发生意外错误 '{text}': {e}")
            return None


    def _get_page_data(self, url):
        """获取并解析页面数据"""
        try:
            response = self.session.get(url, headers=self.headers, timeout=20) # 增加超时时间
            response.raise_for_status() # 检查 HTTP 错误 (如 404, 403)
            # 显式指定编码，如果网站未正确声明
            response.encoding = response.apparent_encoding if response.encoding is None else response.encoding
            return BeautifulSoup(response.text, 'html.parser')
        except requests.exceptions.Timeout:
             print(f"  错误：请求超时 {url}")
             return None
        except requests.exceptions.RequestException as e:
            print(f"  错误：获取页面数据失败 {url}, 错误: {e}")
            return None
        except Exception as e:
             print(f"  错误：解析页面时发生未知错误 {url}: {e}")
             return None

    def collect_data(self, base_url):
        """收集所有类别、所有项目、所有年份的电子废弃物数据 (生产模式)"""
        all_data = []
        print(f"开始从 {base_url} 收集数据 (完整模式)...")
        soup = self._get_page_data(base_url)
        if not soup:
            print("错误：无法获取基础页面，收集终止。")
            return all_data

        # 获取所有分类
        categories = {
            'Continent': soup.find('ul', id='continent-list'),
            'Region': soup.find('ul', id='region-list'),
            'Country': soup.find('ul', id='country-list')
        }

        total_items_to_process = sum(len(lst.find_all('a')) for lst in categories.values() if lst)
        processed_items_count = 0
        print(f"总共需要处理约 {total_items_to_process} 个项目。")


        for category_name, category_list in categories.items():
            if not category_list:
                print(f"未找到类别列表: {category_name}")
                continue

            links = category_list.find_all('a')
            print(f"\n正在处理 {category_name}，共找到 {len(links)} 个项目")

            for i, link in enumerate(links):
                processed_items_count += 1
                name = link.text.strip()
                detail_url = link.get('href')

                if not detail_url:
                     print(f"  警告：跳过项目 '{name}'，因为链接为空。")
                     continue

                if not detail_url.startswith('http'):
                    base_domain = "https://globalewaste.org"
                    if not detail_url.startswith('/'):
                        detail_url = '/' + detail_url
                    detail_url = base_domain + detail_url

                print(f"  ({processed_items_count}/{total_items_to_process}) 正在获取 {category_name}-{name} 的数据...")

                try:
                    # 处理该项目的所有年份数据 - 注意这里调用没有 target_years
                    data = self._process_detail_page(detail_url, category_name, name)
                    if data:
                        all_data.extend(data)
                    # else:
                         # print(f"  注意：未从 {category_name}-{name} 获取到任何年份数据。") # 生产模式可以减少日志
                    time.sleep(1.5) # 保持休眠
                except KeyboardInterrupt:
                     print("\n用户中断操作。")
                     return all_data
                except Exception as e:
                    print(f"  严重错误：处理 {category_name}-{name} ({detail_url}) 数据时发生意外错误: {e}")
                    continue

        print(f"\n所有类别处理完毕，共收集到 {len(all_data)} 条记录。")
        return all_data

    def _process_detail_page(self, url, category, name, target_years=None): # 保持 target_years 参数
        """处理详情页数据，获取指定年份或所有年份数据"""
        data_list = []
        soup = self._get_page_data(url)
        if not soup:
            # print(f"  警告：无法获取 {category}-{name} 的详情页 {url}，跳过此项目。") # 生产模式减少日志
            return data_list

        try:
            year_links_all = soup.find_all('a', class_='yclick')
            if not year_links_all:
                 # print(f"  注意：在 {category}-{name} 页面未找到年份链接 ('a.yclick')。") # 生产模式减少日志
                 return data_list
        except Exception as find_err:
            print(f"  错误：查找 {category}-{name} 的年份链接时出错: {find_err}")
            return data_list

        # --- 年份筛选逻辑 ---
        if target_years:
            year_links_to_process = []
            for link in year_links_all:
                 if hasattr(link, 'text') and link.text.strip() in target_years:
                      year_links_to_process.append(link)
            if not year_links_to_process:
                 print(f"    注意：在 {category}-{name} 未找到目标年份 {target_years} 的链接。")
                 return data_list # 没有找到目标年份，直接返回
            # print(f"    找到 {len(year_links_to_process)}/{len(year_links_all)} 个目标年份链接。") # 测试时可以取消注释
        else:
            year_links_to_process = year_links_all # 处理所有年份
            # print(f"    找到 {len(year_links_to_process)} 个年份链接，开始处理...") # 生产模式减少日志


        for i, year_link in enumerate(year_links_to_process):
            try:
                if not hasattr(year_link, 'text') or not hasattr(year_link, 'get'):
                    # print(f"    警告：跳过无效的年份链接元素 (非 Tag 对象): {year_link}") # 生产模式减少日志
                    continue

                year = year_link.text.strip()
                year_url_path = year_link.get('href')

                if not year or not year_url_path:
                     # print(f"    警告：跳过无效的年份链接 (年份: '{year}', 链接路径: '{year_url_path}')") # 生产模式减少日志
                     continue

                if not year_url_path.startswith('http'):
                    base_domain = "https://globalewaste.org"
                    if not year_url_path.startswith('/'):
                         year_url_path = '/' + year_url_path
                    year_url = base_domain + year_url_path
                else:
                     year_url = year_url_path

                year_data = self._extract_year_data(year_url, category, name, year)
                if year_data:
                    data_list.append(year_data)
                time.sleep(1) # 保持休眠

            except KeyboardInterrupt:
                 raise
            except Exception as loop_e:
                 print(f"    错误：处理 {category}-{name} 年份链接 ({year_link.prettify() if hasattr(year_link, 'prettify') else year_link}) 时出错: {loop_e}")
                 continue

        # print(f"    完成处理 {category}-{name}，获取到 {len(data_list)} 个年份的数据。") # 生产模式减少日志
        return data_list

    def _extract_year_data(self, url, category, name, year):
        """提取给定年份页面的具体数据"""
        soup = self._get_page_data(url)
        if not soup:
             # print(f"      警告：无法获取 {category}-{name} 年份 {year} 的页面 {url}") # 生产模式减少日志
             return None

        data = {
            'Category': category,
            'Name': name,
            'Year': year,
            'Population': None,
            'E-waste Generated (kt)': None,
            'EEE Put on Market (kt)': None,
            'E-waste Formally Collected (kt)': None,
            'E-waste Collection Rate (%)': None,
            'E-waste Generated (kg/capita)': None,
            'EEE Put on Market (kg/capita)': None,
            'E-waste Imported (kt)': None,
            'E-waste Exported (kt)': None,
            'Source URL': url # 添加源 URL 方便追溯
        }

        pop_elem = soup.find('p', class_='pop-number')
        if pop_elem:
            data['Population'] = self._extract_number(pop_elem.text)

        self._extract_metrics(soup, data)

        has_metric_data = any(v is not None and v != 'n/a' for k, v in data.items() if k not in ['Category', 'Name', 'Year', 'Source URL', 'Population'])
        if not has_metric_data and data['Population'] is None:
             # print(f"      注意：{category}-{name} 年份 {year} 页面似乎没有有效数据。") # 生产模式减少日志
             return None

        return data

    def _extract_metrics(self, soup, data):
        """从页面中提取各个指标数据"""
        processed_titles = set()
        
        # print("\n=== 开始提取指标数据 ===")
        # print(f"当前URL: {data.get('Source URL', 'Unknown')}")
        
        # 分别处理upper-part和bottom-part
        upper_part = soup.find('div', class_='upper-part')
        bottom_part = soup.find('div', class_='bottom-part upper-part row')
        
        # print("\n--- 页面结构检查 ---")
        # print(f"找到upper-part: {upper_part is not None}")
        # print(f"找到bottom-part: {bottom_part is not None}")
        
        # if upper_part:
        #     print("\n--- upper-part内容 ---")
        #     print(upper_part.prettify()[:500] + "...")
        
        # if bottom_part:
        #     print("\n--- bottom-part内容 ---")
        #     print(bottom_part.prettify()[:500] + "...")
            
        #     # 检查bottom-part中的类名
        #     print("\n--- bottom-part的类名 ---")
        #     print(f"bottom-part的class属性: {bottom_part.get('class', [])}")
            
        #     # 检查所有single-data元素
        #     all_single_data = bottom_part.find_all('div', class_='single-data')
        #     print(f"\n找到 {len(all_single_data)} 个single-data元素")
            
        #     for i, single_data in enumerate(all_single_data):
        #         print(f"\n--- 第 {i+1} 个single-data元素 ---")
        #         print(f"类名: {single_data.get('class', [])}")
        #         print(f"HTML内容: {single_data.prettify()[:300] + '...'}")
                
        #         # 检查标题
        #         title = single_data.find('h3')
        #         if title:
        #             print(f"标题: {title.text.strip()}")
        #         else:
        #             print("未找到标题")
                
        #         # 检查数值元素
        #         value_elements = single_data.find_all('p', class_=['num bignum', 'num middlenum', 'num bignum pomEEE', 'num middlenum pomEEE'])
        #         print(f"找到 {len(value_elements)} 个数值元素")
        #         for j, value_elem in enumerate(value_elements):
        #             print(f"数值元素 {j+1}: {value_elem.text.strip()}")
                
        #         # 检查单位元素
        #         unit_elements = single_data.find_all('p', class_='num')
        #         print(f"找到 {len(unit_elements)} 个单位元素")
        #         for j, unit_elem in enumerate(unit_elements):
        #             print(f"单位元素 {j+1}: {unit_elem.text.strip()}")
        
        # 处理upper-part数据（总量数据）
        if upper_part:
            data_blocks = upper_part.find_all('div', class_=['single-data', 'single-data small-margin'])
            # print(f"\n在upper-part中找到 {len(data_blocks)} 个数据块")
            
            for i, item in enumerate(data_blocks):
                # print(f"\n--- 处理第 {i+1} 个数据块 ---")
                # print(item.prettify()[:300] + "...")
                
                title_element = item.find('h3')
                if not title_element:
                    # print("警告：未找到标题元素")
                    continue

                title_text_raw = title_element.text.strip()
                title_text_lower = title_text_raw.lower()
                # print(f"标题: {title_text_raw}")

                if 'e-waste collection rate' in title_text_lower and title_text_raw not in processed_titles:
                    percent_element = item.find('text', class_='circle-chart__percent')
                    if percent_element:
                        data['E-waste Collection Rate (%)'] = self._extract_number(percent_element.text)
                        processed_titles.add(title_text_raw)
                        # print(f"提取到收集率: {data['E-waste Collection Rate (%)']}")
                    else:
                        # print("警告：未找到收集率数值元素")
                        pass
                    continue

                value_element = item.find('p', class_=['num bignum', 'num middlenum', 'num bignum pomEEE', 'num middlenum pomEEE'])
                if not value_element:
                    # print("警告：未找到数值元素")
                    continue

                unit_elements = item.find_all('p', class_='num')
                unit_text = ""
                item_text_lower = item.text.lower()

                if len(unit_elements) > 0:
                    next_p = value_element.find_next_sibling('p', class_='num') if value_element else None
                    if next_p:
                        unit_text = next_p.text.strip().lower()
                    elif len(unit_elements) > 1:
                        unit_text = unit_elements[-1].text.strip().lower()

                value_text = value_element.text.strip()
                numeric_value = self._extract_number(value_text)
                # print(f"提取到数值: {numeric_value}, 单位: {unit_text}")

                if title_text_raw in processed_titles:
                    # print("标题已处理过，跳过")
                    continue

                # 处理总量数据
                if 'e-waste generated' in title_text_lower:
                    data['E-waste Generated (kt)'] = numeric_value
                    processed_titles.add(title_text_raw)
                    # print(f"设置E-waste Generated (kt): {numeric_value}")
                elif 'eee put on market' in title_text_lower:
                    data['EEE Put on Market (kt)'] = numeric_value
                    processed_titles.add(title_text_raw)
                    # print(f"设置EEE Put on Market (kt): {numeric_value}")
                elif 'e-waste formally collected' in title_text_lower:
                    data['E-waste Formally Collected (kt)'] = numeric_value
                    processed_titles.add(title_text_raw)
                    # print(f"设置E-waste Formally Collected (kt): {numeric_value}")
                elif 'e-waste imported' in title_text_lower:
                    data['E-waste Imported (kt)'] = numeric_value
                    processed_titles.add(title_text_raw)
                    # print(f"设置E-waste Imported (kt): {numeric_value}")
                elif 'e-waste exported' in title_text_lower:
                    data['E-waste Exported (kt)'] = numeric_value
                    processed_titles.add(title_text_raw)
                    # print(f"设置E-waste Exported (kt): {numeric_value}")

        # 处理bottom-part数据（人均数据）
        if bottom_part:
            data_blocks = bottom_part.find_all('div', class_='single-data')
            # print(f"\n在bottom-part中找到 {len(data_blocks)} 个数据块")
            
            for i, item in enumerate(data_blocks):
                # print(f"\n--- 处理第 {i+1} 个数据块 ---")
                # print(item.prettify()[:300] + "...")
                
                title_element = item.find('h3')
                if not title_element:
                    # print("警告：未找到标题元素")
                    continue

                title_text_raw = title_element.text.strip()
                title_text_lower = title_text_raw.lower()
                # print(f"标题: {title_text_raw}")

                value_element = item.find('p', class_=['num bignum', 'num middlenum', 'num bignum pomEEE', 'num middlenum pomEEE'])
                if not value_element:
                    # print("警告：未找到数值元素")
                    continue

                unit_elements = item.find_all('p', class_='num')
                unit_text = ""
                item_text_lower = item.text.lower()

                if len(unit_elements) > 0:
                    next_p = value_element.find_next_sibling('p', class_='num') if value_element else None
                    if next_p:
                        unit_text = next_p.text.strip().lower()
                    elif len(unit_elements) > 1:
                        unit_text = unit_elements[-1].text.strip().lower()

                value_text = value_element.text.strip()
                numeric_value = self._extract_number(value_text)
                # print(f"提取到数值: {numeric_value}, 单位: {unit_text}")

                # 处理人均数据 - 移除processed_titles检查
                if 'e-waste generated' in title_text_lower:
                    data['E-waste Generated (kg/capita)'] = numeric_value
                    # print(f"设置E-waste Generated (kg/capita): {numeric_value}")
                elif 'eee put on market' in title_text_lower:
                    data['EEE Put on Market (kg/capita)'] = numeric_value
                    # print(f"设置EEE Put on Market (kg/capita): {numeric_value}")

        # print("\n=== 提取完成 ===")
        # print("提取到的数据:")
        # for key, value in data.items():
        #     if key not in ['Category', 'Name', 'Year', 'Source URL']:
        #         print(f"{key}: {value}")

# --- 新增的测试运行函数 ---
def run_test_scrape(collector, base_url):
    """运行一个限定范围的测试抓取"""
    test_data = []
    print(f"开始从 {base_url} 进行测试数据收集...")

    # 定义测试目标
    test_targets = {
        'Continent': ['Europe'],
        'Region': ['Australia and New Zealand', 'South-Eastern Asia'],
        'Country': ['China', 'Germany', 'Japan', 'United States of America']
    }
    test_years = ['2022', '2018']
    print(f"测试目标 - 项目: {test_targets}")
    print(f"测试目标 - 年份: {test_years}")

    soup = collector._get_page_data(base_url)
    if not soup:
        print("错误：无法获取基础页面，测试终止。")
        return test_data

    categories_elements = {
        'Continent': soup.find('ul', id='continent-list'),
        'Region': soup.find('ul', id='region-list'),
        'Country': soup.find('ul', id='country-list')
    }

    processed_items_count = 0
    items_to_process_in_test = sum(len(v) for v in test_targets.values())


    for category_name, target_items in test_targets.items():
        category_list_element = categories_elements.get(category_name)
        if not category_list_element:
            print(f"警告：未找到测试类别列表: {category_name}")
            continue

        all_links_in_category = category_list_element.find_all('a')
        # 筛选出测试目标的链接
        target_links = [link for link in all_links_in_category if link.text.strip() in target_items]

        print(f"\n正在处理测试类别 {category_name}，目标项目: {', '.join(target_items)} (找到 {len(target_links)} 个匹配链接)")

        for link in target_links:
            processed_items_count += 1
            name = link.text.strip()
            detail_url = link.get('href')

            if not detail_url:
                 print(f"  警告：跳过测试项目 '{name}'，因为链接为空。")
                 continue

            if not detail_url.startswith('http'):
                base_domain = "https://globalewaste.org"
                if not detail_url.startswith('/'):
                    detail_url = '/' + detail_url
                detail_url = base_domain + detail_url

            print(f"  ({processed_items_count}/{items_to_process_in_test}) [测试] 正在获取 {category_name}-{name} 的数据 (年份: {', '.join(test_years)})...")

            try:
                # 调用 _process_detail_page 并传入 target_years
                data = collector._process_detail_page(detail_url, category_name, name, target_years=test_years)
                if data:
                    test_data.extend(data)
                else:
                    print(f"  [测试] 注意：未从 {category_name}-{name} (年份 {test_years}) 获取到数据。")
                time.sleep(1) # 测试时也保持一定的休眠

            except KeyboardInterrupt:
                 print("\n用户中断测试操作。")
                 return test_data
            except Exception as e:
                print(f"  [测试] 严重错误：处理测试项目 {category_name}-{name} ({detail_url}) 时发生意外错误: {e}")
                continue

    print(f"\n测试数据收集完毕，共收集到 {len(test_data)} 条记录。")
    return test_data


def save_data(data_list, output_dir, file_prefix):
    """将收集到的数据保存为 CSV 和 JSON 文件"""
    if not data_list:
        print("没有数据可保存。")
        return

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # --- 保存为 CSV ---
    df = pd.DataFrame(data_list)
    column_order = [
        'Category', 'Name', 'Year', 'Population',
        'E-waste Generated (kt)', 'EEE Put on Market (kt)',
        'E-waste Formally Collected (kt)', 'E-waste Collection Rate (%)',
        'E-waste Generated (kg/capita)', 'EEE Put on Market (kg/capita)',
        'E-waste Imported (kt)', 'E-waste Exported (kt)',
        'Source URL'
    ]
    df = df.reindex(columns=[col for col in column_order if col in df.columns])

    csv_filename = f'{file_prefix}_{timestamp}.csv'
    csv_filepath = os.path.join(output_dir, csv_filename)
    try:
        df.to_csv(csv_filepath, index=False, encoding='utf-8-sig')
        print(f"\n数据已保存到 CSV 文件: {csv_filepath}")
    except Exception as e:
         print(f"\n错误：保存 CSV 文件失败: {e}")

    # --- 保存为 JSON ---
    json_filename = f'{file_prefix}_{timestamp}.json'
    json_filepath = os.path.join(output_dir, json_filename)
    try:
        data_for_json = df.to_dict(orient='records')
        with open(json_filepath, 'w', encoding='utf-8') as f:
            json.dump(data_for_json, f, ensure_ascii=False, indent=2)
        print(f"数据同时已保存到 JSON 文件: {json_filepath}")
    except Exception as e:
         print(f"错误：保存 JSON 文件失败: {e}")

    # 打印数据预览
    print("\n数据预览 (前 5 条):")
    # 使用 to_string 避免 markdown 在某些终端显示问题
    print(df.head().to_string(index=False))
    print(f"\n总共处理了 {len(df)} 条数据记录。")


def main():
    """主函数，根据命令行参数选择运行模式"""
    parser = argparse.ArgumentParser(description="从 globalewaste.org 收集电子废弃物数据。")
    parser.add_argument(
        "--test",
        action="store_true", # 如果提供了 --test 参数，则此值为 True
        help="运行限定范围的测试抓取，而不是完整抓取。"
    )
    args = parser.parse_args()

    start_time = time.time()
    collector = EwasteDataCollector()
    base_url = "https://globalewaste.org/country-sheets/"
    output_dir = "output_data" # 定义输出文件夹

    # 创建输出文件夹
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"创建输出文件夹: {output_dir}")

    collected_data = []
    file_prefix = "" # 文件名前缀

    if args.test:
        print("=== 开始测试模式运行 ===")
        collected_data = run_test_scrape(collector, base_url)
        file_prefix = "ewaste_data_test"
    else:
        print("=== 开始正式数据收集 (完整模式) ===")
        print("这将抓取所有类别、项目和年份的数据，可能需要较长时间。")
        collected_data = collector.collect_data(base_url)
        file_prefix = "ewaste_data_full"

    # 保存数据
    save_data(collected_data, output_dir, file_prefix)

    end_time = time.time()
    duration = end_time - start_time
    print(f"\n=== {'测试' if args.test else '完整'}运行完成 ===")
    print(f"总耗时: {duration:.2f} 秒")

if __name__ == "__main__":
    main()