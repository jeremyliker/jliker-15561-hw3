# Chat Transcript Outline: Northwind Data Analysis

An outline of the AI-assisted session that produced the Northwind analysis,
webpage and reproducibility guide. Each step lists the request as asked,
what was done, and what came out of it.

- **Assistant:** Claude Code (desktop app)
- **Dates:** 22–23 November 2026
- **Dataset:** `Northwind Database.xlsx`
- **Main deliverables:** `northwind_analysis.py`, `output/`,
  `northwind_brief.html`, `README.md`, `requirements.txt`

---

## 1. Review the dataset

**Request:** "Review the data and give me all the main characteristics of
the data."

**What was done**
- Installed `pandas` and `openpyxl`, then profiled all 8 sheets: shapes,
  columns, missing values, keys and sample rows.
- Computed revenue, date range, top categories, products, countries,
  customers, employees, shippers and shipping times.
- Checked data quality: duplicate keys, orphaned foreign keys, and the
  Product sheet's helper columns.

**Key results**
- 8 related tables; 830 orders and 2,155 order lines from 4 Jul 1996 to
  6 May 1998.
- Net revenue $1,265,793 (gross $1,354,459, so $88.7K of discounts).
- 1996 and 1998 are partial years, so calendar years can't be compared.
- Data-quality notes: conflicting helper columns on the Product sheet
  (`Cheap`, `NewPrice`, `IsCheap`), floating-point noise in discounts, 21
  unshipped orders, and order-line prices that differ from today's list
  price.
- No duplicate keys and no orphaned foreign keys.

## 2. Create an ERD

**Request:** "Please create an ERD for this dataset."

**What was done**
- Drew an inline Mermaid ERD of the 8 tables with primary keys, foreign
  keys, cardinalities, and the `Employees.ReportsTo` self-reference.
- Explained that `Orders Details` is the join table between orders and
  products (composite key OrderID + ProductID), and that `Orders.ShipVia`
  links to `Shippers.ShipperID`.

## 3. Python code for the characteristics and the ERD

**Request:** "Develop python code that creates the output of the dataset
characteristics and the ERD as well. Use the SKILL.md as well."

**What was done**
- Wrote `northwind_analysis.py`. It writes `output/northwind_profile.md`,
  `output/northwind_erd.mmd` and `output/northwind_erd.png`.
- Followed `SKILL.md`: Google-style, PEP 257 docstrings with one line per
  argument and a `Returns:` section, then reported the docstrings and the
  assumptions behind them.
- Fixed problems found during testing:
  - Excel locked the workbook. The script now stops with a clear message;
    testing used a copy of the file.
  - ERD connector lines overlapped. Lanes are now assigned per gap between
    columns.
  - Years printed as "1,996". They are now formatted as text.

**Correction to step 1:** the `�` characters in accented names came from how
the Windows console displayed them, not from the data. The data reads
correctly (for example, Côte de Blaye).

## 4. Business question 1: growth by country and region

**Request:** "Which countries or regions are growing or declining over time,
and where should efforts be focused? Use a visual such as a line chart."

**What was done**
- Compared like-for-like periods: Jan–Apr 1998 vs Jan–Apr 1997, and H2 1997
  vs H2 1996.
- Grouped ship-to countries into 5 regions.
- Sorted countries into segments: Invest, Defend, Develop, Monitor, and Fix
  or deprioritize.
- Charts: `region_trend.png` (line chart by region) and `country_trends.png`
  (small multiples for the top 12 countries).
- Used the dataviz skill's palette and mark specs. Fixed a crash caused by
  setting the y-axis limits before the data was plotted.

**Findings**
- The company grew +121% (Jan–Apr). Every region grew.
- USA (+173%), Germany (+167%) and Brazil (+286%) are large and growing
  fast: segment Invest.
- France (+5%) has stalled.
- Canada, Denmark, Finland, Mexico and Portugal declined. Mexico and
  Portugal declined in both comparisons.

## 5. Business question 2: revenue concentration

**Request:** "How dependent is revenue on a few customers or products, and
what happens if one leaves? Use a visual such as a scatter plot."

**What was done**
- Measured top-N revenue shares, how many customers or products make up 50%
  and 80% of revenue, and the Herfindahl-Hirschman Index (HHI).
- Modeled what-if losses for the top 5 customers and products.
- Chart: `concentration.png`, two scatter panels (customers: orders vs
  revenue; products: units sold vs revenue).
- The first version had colliding labels. It now uses numbered dots with a
  key, and the legend was moved off the data.

**Findings**
- HHI is about 330 for both customers and products, so the base is not
  concentrated overall.
- The top 5 customers bring in 33% of revenue. Losing any one of the top 3
  costs about 8%.
- Côte de Blaye is the largest single exposure at 11.2% of revenue.
- Discontinued products already account for 14.6% of past revenue,
  including the #2 product.

## 6. Business question 3: shipper fulfillment and product ship times

**Request:** "Compare the performance for each shipper in terms of
fulfillment. Are there any products that traditionally take longer than
others to ship? Use a scatter or bar plot. Label axes and chart."

**What was done**
- Built a shipper scorecard: mean, median and 90th-percentile days to ship,
  share shipped within 7 days, late rate, unshipped orders and freight.
  Added bootstrap 95% confidence intervals with a fixed seed.
- Tested each product's ship time against the overall average, with a
  Bonferroni correction across 77 products (|z| ≥ 3.41).
- Charts: `shipper_performance.png` (box plot plus bar charts) and
  `product_ship_times.png` (ranked dot plot with confidence intervals).
- Fixed a deprecated matplotlib argument, made the bars thinner, and fixed
  an overlapping chart subtitle.

**Findings**
- Federal Shipping is fastest: mean 7.5 days, 63% shipped within 7 days.
- United Package is slowest (mean 9.2 days, 90th percentile 22 days) and
  has the highest freight cost.
- Speedy Express is the cheapest.
- Only Sir Rodney's Marmalade ships slower than chance would explain: mean
  16.1 days but median 9, so a few very slow orders drive the result.

## 7. Pie chart of shipments by shipper

**Request:** "Can you add a pie chart that shows the distribution of all
shipments across the shippers?"

**What was done**
- Added `shipment_share.png`: United Package 326 orders (39%), Federal
  Shipping 255 (31%), Speedy Express 249 (30%).
- Counted all 830 orders by assigned shipper, including the 21 not yet
  shipped. Fixed the subtitle alignment.

## 8. Advisory webpage

**Request:** Create a webpage that explains Northwind to a manager, from the
point of view of an advising organization. Show the three business questions
and their answers, and for each include why it matters, the analytical
approach, the visualizations, the main finding and the business
implication. All visuals must come from the code.

**What was done**
- Wrote `northwind_brief.html` and published it as a private artifact:
  "Northwind Advisory Brief".
- Sections:
  - an organization overview with key figures and the ERD
  - the three questions, each with the same five parts
  - five priorities for the next quarter
  - notes on the data
- Used only the 7 charts generated by `northwind_analysis.py`. Two other
  images in `output/` were not created by the script, so they were left
  out.
- Fixed two wording errors and an uneven key-figures grid before
  publishing.

## 9. Reproducibility guide for GitHub

**Request:** Create a README.md that explains how to reproduce the numbers,
figures and tables on the webpage, so another person can reproduce the
results from the Northwind dataset.

**What was done**
- Wrote `README.md` covering:
  - a SHA-256 hash to check the dataset is the same file
  - environment setup and run instructions
  - which output file feeds which webpage section
  - expected hashes for all nine output files
  - a checklist of key figures and where each appears in the profile
  - methods, parameters and known data issues
- Wrote `requirements.txt` with the exact versions used: Python 3.12.10,
  pandas 3.1.1, numpy 2.5.5, matplotlib 3.11.2, openpyxl 3.1.5.
- Ran the script twice from a clean state; all outputs were byte-identical.
- Searched the generated profile for every number on the webpage. Added
  "29 suppliers in 16 countries" to the profile, because the supplier
  country count was the one number missing.

## 10. Cleanup

**Request:** "Yes, delete them."

**What was done**
- Deleted `output/concentration_pareto.png` and
  `output/customer_risk_front.png`. The script doesn't create them, so
  `output/` now holds only reproducible files.

---

## Final file inventory

| File | Purpose |
|---|---|
| `Northwind Database.xlsx` | Input dataset (SHA-256 `0770a298…8ad9`) |
| `northwind_analysis.py` | Full analysis script |
| `requirements.txt` | Pinned package versions |
| `README.md` | Reproduction guide |
| `northwind_brief.html` | Advisory webpage |
| `output/northwind_profile.md` | All numbers and tables |
| `output/northwind_erd.png`, `output/northwind_erd.mmd` | ERD |
| `output/region_trend.png`, `output/country_trends.png` | Question 1 charts |
| `output/concentration.png` | Question 2 chart |
| `output/shipment_share.png`, `output/shipper_performance.png`, `output/product_ship_times.png` | Question 3 charts |
| `SKILL.md` | Docstring style guide the code follows |
| `CHAT_TRANSCRIPT.md` | This outline |
