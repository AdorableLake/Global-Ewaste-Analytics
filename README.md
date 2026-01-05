<div align="center">

# 🌎 全球电子垃圾 (E-waste) 数据分析与可视化 (2018-2022)

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)](https://www.python.org/)
[![Pandas](https://img.shields.io/badge/Pandas-Data_Processing-orange)](https://pandas.pydata.org/)
[![D3.js](https://img.shields.io/badge/D3.js-Interactive_Viz-F7DF1E)](https://d3js.org/)
[![License](https://img.shields.io/badge/License-MIT-lightgrey)](LICENSE)

<!-- 语言切换按钮 -->
[![English](https://img.shields.io/badge/Language-English-blue)](README_EN.md)
[![Chinese](https://img.shields.io/badge/Language-中文-gray)](README.md)

---

> 本项目旨在分析全球电子垃圾的产生与回收趋势，并探索数据可视化在传达复杂环境问题中的应用。项目数据来源于公开报告，并通过自动化脚本进行采集。所有分析与可视化工作均在佐治亚理工学院 CSE6242 课程框架下完成。

</div>

---

## 🚀 交互式数据探索 (D3.js 实现)

为了直观展示各经济体在全球电子垃圾版图中的位置，我使用 D3.js 构建了一个交互式的网络关系图。将鼠标悬停在节点上可查看具体数据。

#### **[➡️ 点击此处，体验交互式可视化 Demo](https://AdorableLake.github.io/Global-Ewaste-Analytics/Node.html)**

<div align="center">
  <a href="https://AdorableLake.github.io/Global-Ewaste-Analytics/Node.html" target="_blank">
    <img src="assets/interactive_node_graph.png" alt="交互式网络图" width="80%">
  </a>
</div>

---

## 📊 核心发现与图表

通过对 2018-2022 年的数据进行时空分析，揭示了以下关键趋势：

#### 1. 回收率的巨大地理差异 (2022)
欧洲地区保持着较高的回收率（约43%），而亚洲和非洲的大部分地区回收体系尚不完善，回收率显著偏低（<10%）。

<div align="center">
  <img src="assets/map_collection_rate.png" alt="2022年全球电子垃圾回收率地图" width="80%">
</div>

#### 2. “未回收缺口”持续扩大 (2018-2022)
数据显示，全球电子垃圾的产生速度远超正规回收体系的处理能力，导致未被回收处理的电子垃圾总量逐年增加，构成了资源浪费与环境风险。

<div align="center">
  <img src="assets/trend_gap_analysis.png" alt="全球电子垃圾产生量 vs. 回收量趋势" width="70%">
</div>

---

## 🛠️ 项目工作流

本项目覆盖了从数据采集到分析报告的完整流程：
1.  **数据采集**: 使用 Python (`Requests`, `BeautifulSoup`) 编写脚本，自动从 Global E-waste Statistics Partnership 网站爬取数据。
2.  **数据处理**: 使用 `Pandas` 和 `GeoPandas` 对原始数据进行清洗、整合与地理空间关联。
3.  **数据可视化**:
    *   **静态图表**: 使用 `Matplotlib` 生成趋势图与地理热力图。
    *   **交互图表**: 使用 `D3.js` 构建网络关系图。
4.  **报告撰写**: 总结发现，完成项目报告与海报。

---

## 📂 仓库文件说明
- `Node.html`: 可交互的 D3.js 可视化文件。
- `src/`: 存放数据采集的 Python 源代码。
- `reports/`: 包含详细的最终报告 (`Final_Report.pdf`) 和项目海报 (`Poster.pdf`)。
- `assets/`: 存放所有静态图表文件。

---
