# Northwind dataset profile

## Tables

| Sheet | Rows | Columns | Primary key | Missing values |
|---|---|---|---|---|
| Categories | 8 | 4 | CategoryID | Picture (8) |
| Customers | 91 | 11 | CustomerID | Region (60), PostalCode (1), Fax (22) |
| Employees | 9 | 17 | EmployeeID | Region (4), ReportsTo (1) |
| Orders Details | 2,155 | 5 | OrderID + ProductID | none |
| Orders | 830 | 14 | OrderID | ShippedDate (21), ShipRegion (507), ShipPostalCode (19) |
| Shippers | 3 | 3 | ShipperID | none |
| Product | 77 | 16 | ProductID | Unnamed: 14 (77), NewPrice.1 (51) |
| Suppliers | 29 | 12 | SupplierID | Region (20), Fax (16), HomePage (26) |

## Sales

- Order dates: 1996-07-04 to 1998-05-06 (1996 and 1998 are partial years)
- Gross revenue: $1,354,458.59; net revenue: $1,265,793.04; discounts: $88,665.55
- Order value: mean $1,525, median $943, max $16,388
- Lines per order: mean 2.60, max 25

### Revenue by year

| Year | Orders | Revenue |
|---|---|---|
| 1996 | 152 | 208,083.97 |
| 1997 | 408 | 617,085.20 |
| 1998 | 270 | 440,623.87 |

### Revenue by month

| Month | Orders | Revenue |
|---|---|---|
| 1996-07 | 22 | 27,861.90 |
| 1996-08 | 25 | 25,485.28 |
| 1996-09 | 23 | 26,381.40 |
| 1996-10 | 26 | 37,515.73 |
| 1996-11 | 25 | 45,600.04 |
| 1996-12 | 31 | 45,239.63 |
| 1997-01 | 33 | 61,258.07 |
| 1997-02 | 29 | 38,483.63 |
| 1997-03 | 30 | 38,547.22 |
| 1997-04 | 31 | 53,032.95 |
| 1997-05 | 32 | 53,781.29 |
| 1997-06 | 30 | 36,362.80 |
| 1997-07 | 33 | 51,020.86 |
| 1997-08 | 33 | 47,287.67 |
| 1997-09 | 37 | 55,629.24 |
| 1997-10 | 38 | 66,749.23 |
| 1997-11 | 34 | 43,533.81 |
| 1997-12 | 48 | 71,398.43 |
| 1998-01 | 55 | 94,222.11 |
| 1998-02 | 54 | 99,415.29 |
| 1998-03 | 73 | 104,854.16 |
| 1998-04 | 74 | 123,798.68 |
| 1998-05 | 14 | 18,333.63 |

### Discount levels

| Discount | Lines |
|---|---|
| 0.00 | 1,317 |
| 0.01 | 1 |
| 0.02 | 2 |
| 0.03 | 3 |
| 0.04 | 1 |
| 0.05 | 185 |
| 0.06 | 1 |
| 0.10 | 173 |
| 0.15 | 157 |
| 0.20 | 161 |
| 0.25 | 154 |

## Products

- 77 products in 8 categories from 29 suppliers in 16 countries; 8 discontinued
- List price: min $2.50, median $19.50, max $263.50
- 18 active products at or below their reorder level

### Revenue by category

| CategoryName | Revenue | Units |
|---|---|---|
| Beverages | 267,868.18 | 9,532 |
| Dairy Products | 234,507.29 | 9,149 |
| Confections | 167,357.23 | 7,906 |
| Meat/Poultry | 163,022.36 | 4,199 |
| Seafood | 131,261.74 | 7,681 |
| Condiments | 106,047.09 | 5,298 |
| Produce | 99,984.58 | 2,990 |
| Grains/Cereals | 95,744.59 | 4,562 |

### Top 10 products by revenue

| ProductName | Revenue |
|---|---|
| Côte de Blaye | 141,396.73 |
| Thüringer Rostbratwurst | 80,368.67 |
| Raclette Courdavault | 71,155.70 |
| Tarte au sucre | 47,234.97 |
| Camembert Pierrot | 46,825.48 |
| Gnocchi di nonna Alice | 42,593.06 |
| Manjimup Dried Apples | 41,819.65 |
| Alice Mutton | 32,698.38 |
| Carnarvon Tigers | 29,171.88 |
| Rössle Sauerkraut | 25,696.64 |

### Top 5 products by units sold

| ProductName | Units |
|---|---|
| Camembert Pierrot | 1,577 |
| Raclette Courdavault | 1,496 |
| Gorgonzola Telino | 1,397 |
| Gnocchi di nonna Alice | 1,263 |
| Pavlova | 1,158 |

## Customers

- 91 customers in 21 countries; without orders: FISSA, PARIS
- Orders per customer: mean 9.3, min 1, max 31
- Top 3 customers bring in 25% of net revenue

### Top 10 ship-to countries by revenue

| ShipCountry | Revenue |
|---|---|
| USA | 245,584.61 |
| Germany | 230,284.63 |
| Austria | 128,003.84 |
| Brazil | 106,925.78 |
| France | 81,358.32 |
| UK | 58,971.31 |
| Venezuela | 56,810.63 |
| Sweden | 54,495.14 |
| Canada | 50,196.29 |
| Ireland | 49,979.90 |

### Top 10 customers by revenue

| CompanyName | Revenue |
|---|---|
| QUICK-Stop | 110,277.31 |
| Ernst Handel | 104,874.98 |
| Save-a-lot Markets | 104,361.95 |
| Rattlesnake Canyon Grocery | 51,097.80 |
| Hungry Owl All-Night Grocers | 49,979.90 |
| Hanari Carnes | 32,841.37 |
| Königlich Essen | 30,908.38 |
| Folk och fä HB | 29,567.56 |
| Mère Paillarde | 28,872.19 |
| White Clover Markets | 27,363.60 |

## Employees

| Employee | Title | Country | Orders | Revenue |
|---|---|---|---|---|
| Margaret Peacock | Sales Representative | USA | 156 | 232,890.85 |
| Janet Leverling | Sales Representative | USA | 127 | 202,812.84 |
| Nancy Davolio | Sales Representative | USA | 123 | 192,107.60 |
| Andrew Fuller | Vice President, Sales | USA | 96 | 166,537.76 |
| Laura Callahan | Inside Sales Coordinator | USA | 104 | 126,862.28 |
| Robert King | Sales Representative | UK | 72 | 124,568.24 |
| Anne Dodsworth | Sales Representative | UK | 43 | 77,308.07 |
| Michael Suyama | Sales Representative | UK | 67 | 73,913.13 |
| Steven Buchanan | Sales Manager | UK | 42 | 68,792.28 |

## Shipping

| CompanyName | Orders | AvgFreight | TotalFreight |
|---|---|---|---|
| Federal Shipping | 255 | 80.44 | 20,512.51 |
| Speedy Express | 249 | 65.00 | 16,185.33 |
| United Package | 326 | 86.64 | 28,244.85 |

- Freight per order: mean $78.24, max $1,007.64
- Days to ship: mean 8.5, median 7, max 37
- Shipped after the required date: 37; never shipped: 21

## Country and regional growth

Orders run from July 1996 to 6 May 1998, so calendar years are not comparable. Growth compares like-for-like windows: H2 1997 vs H2 1996, and Jan-Apr 1998 vs Jan-Apr 1997 (the latest).

- Company-wide growth, Jan-Apr 1998 vs 1997: +121%

### By region

| Region | Share | H2 1996 | H2 1997 | H2 growth | Jan-Apr 1997 | Jan-Apr 1998 | Jan-Apr growth |
|---|---|---|---|---|---|---|---|
| Western Europe | 40% | 88,852.67 | 134,269.48 | +51% | 76,011.79 | 158,285.27 | +108% |
| North America | 25% | 50,166.25 | 91,094.28 | +82% | 53,692.97 | 101,529.25 | +89% |
| Northern Europe | 17% | 32,456.84 | 54,618.88 | +68% | 33,204.64 | 73,941.63 | +123% |
| South America | 14% | 29,886.92 | 42,235.59 | +41% | 22,210.60 | 69,104.88 | +211% |
| Southern & Eastern Europe | 4% | 6,721.28 | 13,401.01 | +99% | 6,201.88 | 19,429.20 | +213% |

### By country

| Country | Region | Share | Jan-Apr 1997 | Jan-Apr 1998 | Jan-Apr growth | H2 growth | Segment |
|---|---|---|---|---|---|---|---|
| USA | North America | 19.4% | 31,517.75 | 86,118.80 | +173% | +98% | Invest |
| Germany | Western Europe | 18.2% | 28,433.64 | 75,840.50 | +167% | +79% | Invest |
| Austria | Western Europe | 10.1% | 19,973.37 | 39,782.65 | +99% | +28% | Defend |
| Brazil | South America | 8.4% | 11,097.12 | 42,808.69 | +286% | +37% | Invest |
| France | Western Europe | 6.4% | 17,083.50 | 17,929.43 | +5% | +25% | Defend |
| UK | Northern Europe | 4.7% | 7,591.70 | 22,623.53 | +198% | +22% | Develop |
| Venezuela | South America | 4.5% | 10,125.38 | 19,993.69 | +97% | +43% | Monitor |
| Sweden | Northern Europe | 4.3% | 1,703.82 | 20,398.23 | +1097% | +126% | Develop |
| Canada | North America | 4.0% | 15,210.71 | 11,525.55 | -24% | +76% | Fix or deprioritize |
| Ireland | Northern Europe | 3.9% | 5,870.93 | 20,402.12 | +248% | +32% | Develop |
| Belgium | Western Europe | 2.7% | 6,109.48 | 16,083.67 | +163% | -31% | Develop |
| Denmark | Northern Europe | 2.6% | 13,706.40 | 4,284.00 | -69% | +261% | Fix or deprioritize |
| Switzerland | Western Europe | 2.5% | 4,411.80 | 8,649.01 | +96% | +192% | Monitor |
| Mexico | North America | 1.9% | 6,964.51 | 3,884.90 | -44% | -46% | Fix or deprioritize |
| Finland | Northern Europe | 1.5% | 4,131.80 | 2,257.00 | -45% | +40% | Fix or deprioritize |
| Spain | Southern & Eastern Europe | 1.4% | 338.20 | 8,028.60 | +2274% | +95% | Develop |
| Italy | Southern & Eastern Europe | 1.2% | 2,585.69 | 6,843.80 | +165% | +397% | Develop |
| Portugal | Southern & Eastern Europe | 0.9% | 3,277.99 | 2,691.70 | -18% | -34% | Fix or deprioritize |
| Argentina | South America | 0.6% | 988.10 | 6,302.50 | +538% | new | Develop |
| Norway | Northern Europe | 0.5% | 200.00 | 3,976.75 | +1888% | -53% | Develop |
| Poland | Southern & Eastern Europe | 0.3% | 0.00 | 1,865.10 | new | +163% | Develop |

### Where to focus

- **Invest** (large (>= 5% of revenue) and growing faster than the company): USA, Germany, Brazil
- **Defend** (large but growing slower than the company): Austria, France
- **Develop** (small but growing faster than the company): UK, Sweden, Ireland, Belgium, Spain, Italy, Argentina, Norway, Poland
- **Monitor** (small and growing slower than the company): Venezuela, Switzerland
- **Fix or deprioritize** (revenue fell year over year): Canada, Denmark, Mexico, Finland, Portugal

- Declining in both windows: Mexico, Portugal
- Small base (Jan-Apr 1997 revenue < $5,000), so growth rates are volatile: Sweden, Switzerland, Finland, Spain, Italy, Portugal, Argentina, Norway, Poland

Charts: `region_trend.png` (quarterly revenue by region) and `country_trends.png` (top 12 countries).

## Revenue concentration and loss scenarios

### How concentrated is revenue?

| Measure | Customers | Products |
|---|---|---|
| Entities with sales | 89 | 77 |
| Share of the #1 | 8.7% | 11.2% |
| Share of the top 5 | 33.2% | 30.6% |
| Share of the top 10 | 45.0% | 44.2% |
| Needed for 50% of revenue | 13 | 14 |
| Needed for 80% of revenue | 34 | 36 |
| HHI (0-10,000) | 337 | 327 |

- Both HHIs sit far below 1,500, so the base is not concentrated overall, but the top is steep: 33% of revenue comes from 5 of 89 customers and 31% from 5 of 77 products.
- Discontinued products already account for 14.6% of past revenue, including top-10 sellers Thüringer Rostbratwurst, Alice Mutton, Rössle Sauerkraut.

### Top 5 customers

| Customer | Share | Orders | Days since last order | Biggest product |
|---|---|---|---|---|
| QUICK-Stop | 8.7% | 28 | 22 | Côte de Blaye |
| Ernst Handel | 8.3% | 30 | 1 | Raclette Courdavault |
| Save-a-lot Markets | 8.2% | 31 | 5 | Thüringer Rostbratwurst |
| Rattlesnake Canyon Grocery | 4.0% | 18 | 0 | Côte de Blaye |
| Hungry Owl All-Night Grocers | 3.9% | 19 | 6 | Thüringer Rostbratwurst |

### If a top customer leaves

| If lost | Revenue lost | Revenue drop | Revenue left |
|---|---|---|---|
| QUICK-Stop | 110,277.31 | -8.7% | 1,155,515.73 |
| Ernst Handel | 104,874.98 | -8.3% | 1,160,918.06 |
| Save-a-lot Markets | 104,361.95 | -8.2% | 1,161,431.09 |
| Rattlesnake Canyon Grocery | 51,097.80 | -4.0% | 1,214,695.24 |
| Hungry Owl All-Night Grocers | 49,979.90 | -3.9% | 1,215,813.13 |
| All top 5 together | 420,591.94 | -33.2% | 845,201.10 |

### Top 5 products

| Product | Share | Buyers | Biggest buyer | Biggest buyer's share | Discontinued |
|---|---|---|---|---|---|
| Côte de Blaye | 11.2% | 19 | QUICK-Stop | 16% | False |
| Thüringer Rostbratwurst | 6.3% | 27 | Hungry Owl All-Night Grocers | 21% | True |
| Raclette Courdavault | 5.6% | 43 | Ernst Handel | 12% | False |
| Tarte au sucre | 3.7% | 34 | Rattlesnake Canyon Grocery | 17% | False |
| Camembert Pierrot | 3.7% | 36 | QUICK-Stop | 15% | False |

### If a top product is lost

| If lost | Revenue lost | Revenue drop | Revenue left |
|---|---|---|---|
| Côte de Blaye | 141,396.73 | -11.2% | 1,124,396.30 |
| Thüringer Rostbratwurst | 80,368.67 | -6.3% | 1,185,424.37 |
| Raclette Courdavault | 71,155.70 | -5.6% | 1,194,637.34 |
| Tarte au sucre | 47,234.97 | -3.7% | 1,218,558.07 |
| Camembert Pierrot | 46,825.48 | -3.7% | 1,218,967.56 |
| All top 5 together | 386,981.56 | -30.6% | 878,811.48 |

Losses are first-order: they assume no buyer switches to another product and no lost customer is replaced.

Chart: `concentration.png` (revenue vs orders per customer and revenue vs units per product).

## Fulfillment by shipper and product

Days = order date to shipped date. Late = shipped after the required date. 95% CI of the mean from 2,000 bootstrap resamples.

### Shipper scorecard

| Shipper | Orders | Mean days | 95% CI | Median | 90th pct | Within 7 days | Late | Unshipped | Avg freight | Freight / revenue |
|---|---|---|---|---|---|---|---|---|---|---|
| Federal Shipping | 255 | 7.5 | 6.8-8.2 | 6 | 12 | 63% | 3.6% | 6 | $80.44 | 5.4% |
| Speedy Express | 249 | 8.6 | 7.7-9.5 | 7 | 18 | 58% | 4.9% | 4 | $65.00 | 4.6% |
| United Package | 326 | 9.2 | 8.5-10.1 | 7 | 22 | 55% | 5.1% | 11 | $86.64 | 5.3% |

- Fastest: Federal Shipping (mean 7.5 days); slowest: United Package (mean 9.2 days, 90th percentile 22 days).
- The confidence intervals of Federal Shipping and United Package do not overlap, so the gap is unlikely to be chance.
- Late shipments are rare for every shipper (3.6%-5.1%); most orders allow 28 days.

### Do some products take longer to ship?

Overall mean: 8.3 days per order line. A product is flagged only if |z| >= 3.41 (5% Bonferroni-corrected across 77 products).

#### Slowest 10 products

| Product | Orders | Mean days | Median | z | Verdict |
|---|---|---|---|---|---|
| Sir Rodney's Marmalade | 15 | 16.1 | 9 | +4.5 | Slower |
| Mishi Kobe Niku | 5 | 15.2 | 6 | +2.3 | Typical |
| Gravad lax | 6 | 14.2 | 13 | +2.1 | Typical |
| Schoggi Schokolade | 9 | 12.3 | 8 | +1.8 | Typical |
| Lakkalikööri | 38 | 10.7 | 8 | +2.2 | Typical |
| Chocolade | 6 | 10.3 | 8 | +0.7 | Typical |
| Thüringer Rostbratwurst | 32 | 9.8 | 9 | +1.2 | Typical |
| Côte de Blaye | 24 | 9.7 | 9 | +1.0 | Typical |
| Chef Anton's Cajun Seasoning | 19 | 9.6 | 7 | +0.8 | Typical |
| Maxilaku | 19 | 9.5 | 7 | +0.7 | Typical |

#### Fastest 5 products

| Product | Orders | Mean days | Median | z | Verdict |
|---|---|---|---|---|---|
| Spegesild | 24 | 5.8 | 6 | -1.9 | Typical |
| Röd Kaviar | 13 | 6.2 | 6 | -1.2 | Typical |
| Escargots de Bourgogne | 18 | 6.3 | 6 | -1.3 | Typical |
| Uncle Bob's Organic Dried Pears | 27 | 6.6 | 6 | -1.4 | Typical |
| Mozzarella di Giovanni | 38 | 6.6 | 6 | -1.6 | Typical |

- Beyond chance: Sir Rodney's Marmalade (mean 16.1 vs median 9 days, so a few very slow orders drive it). Without the correction, 4 products would look unusual at |z| >= 1.96, about the 4 expected by chance alone.
- Shipping time is measured per order, so a slow order slows every product on it; products are not shipped separately.

Charts: `shipper_performance.png`, `shipment_share.png` (pie of orders by shipper) and `product_ship_times.png`.

## Data quality

- Duplicate primary keys: 0
- Orphaned foreign keys: 0 across 8 relationships
- Product helper columns: Cheap, NewPrice, Cheap.1, IsCheap, Unnamed: 14, NewPrice.1
- Product.Cheap values other than t/f: ['Côte de Blaye']
- Product.IsCheap marks 14 products (price <= 10) vs 11 for Cheap (price < 10)
- Order lines priced differently from today's list price: 658 of 2155
- Discounts stored with floating-point noise: 684
