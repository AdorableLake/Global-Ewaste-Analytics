<div align="center">

# 🌎 Global E-waste Analytics & Visualization (2018-2022)

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)](https://www.python.org/)
[![Pandas](https://img.shields.io/badge/Pandas-Data_Processing-orange)](https://pandas.pydata.org/)
[![D3.js](https://img.shields.io/badge/D3.js-Interactive_Viz-F7DF1E)](https://d3js.org/)
[![License](https://img.shields.io/badge/License-MIT-lightgrey)](LICENSE)

<!-- Language Switcher -->
[![English](https://img.shields.io/badge/Language-English-gray)](README_EN.md)
[![Chinese](https://img.shields.io/badge/Language-中文-blue)](README.md)

---

> This project analyzes global e-waste generation and recycling trends, exploring the role of data visualization in communicating complex environmental issues. Data was sourced from public reports and collected via an automated script. All analysis and visualization were completed as part of the CSE6242 course at Georgia Tech.

</div>

---

## 🚀 Interactive Data Exploration (with D3.js)

To intuitively represent the position of major economies in the global e-waste landscape, I developed an interactive network graph using D3.js. Hover over the nodes to explore the corresponding data.

#### **[➡️ Click here for the Interactive Visualization Demo](https://AdorableLake.github.io/Global-Ewaste-Analytics/Node.html)**

<div align="center">
  <a href="https://AdorableLake.github.io/Global-Ewaste-Analytics/Node.html" target="_blank">
    <img src="assets/interactive_node_graph.png" alt="Interactive Network Graph" width="80%">
  </a>
</div>

---

## 📊 Key Findings & Visualizations

Spatio-temporal analysis of the 2018-2022 dataset reveals the following key trends:

#### 1. Stark Geospatial Disparities in Collection Rates (2022)
Europe maintains a high average collection rate (~43%), whereas formal collection systems in most parts of Asia and Africa are significantly less developed, with rates often below 10%.

<div align="center">
  <img src="assets/map_collection_rate.png" alt="Global E-waste Collection Rate Map 2022" width="80%">
</div>

#### 2. Widening "Uncollected Gap" (2018-2022)
The data indicates that global e-waste generation is growing faster than the capacity of formal collection systems. This widening gap represents both a significant loss of valuable resources and a growing environmental risk.

<div align="center">
  <img src="assets/trend_gap_analysis.png" alt="Global E-waste Generation vs. Collection Trend" width="70%">
</div>

---

## 🛠️ Project Workflow

This project covers an end-to-end data science pipeline:
1.  **Data Collection**: An automated script using Python (`Requests`, `BeautifulSoup`) was developed to scrape data from the Global E-waste Statistics Partnership website.
2.  **Data Processing**: The raw data was cleaned, structured, and merged with geospatial information using `Pandas` and `GeoPandas`.
3.  **Data Visualization**:
    *   **Static Visuals**: Trend charts and choropleth maps were generated with `Matplotlib`.
    *   **Interactive Visuals**: A network graph was built using `D3.js`.
4.  **Reporting**: Findings were summarized in a final report and a poster.

---

## 📂 Repository Contents
- `Node.html`: The interactive D3.js visualization file.
- `src/`: Contains the Python source code for data collection.
- `reports/`: Includes the detailed `Final_Report.pdf` and summary `Poster.pdf`.
- `assets/`: Contains all static visualizations.

---
