"""Profile the Northwind workbook, draw its ERD and chart growth.

Writes a Markdown profile, a Mermaid ERD and PNG charts to ``output/``.
"""

import argparse
import sys
from pathlib import Path
from statistics import NormalDist

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.patches import Rectangle  # noqa: E402

HERE = Path(__file__).resolve().parent
DEFAULT_WORKBOOK = HERE / "Northwind Database.xlsx"
DEFAULT_OUT_DIR = HERE / "output"

PRIMARY_KEYS = {
    "Categories": ["CategoryID"],
    "Customers": ["CustomerID"],
    "Employees": ["EmployeeID"],
    "Orders": ["OrderID"],
    "Orders Details": ["OrderID", "ProductID"],
    "Product": ["ProductID"],
    "Shippers": ["ShipperID"],
    "Suppliers": ["SupplierID"],
}

# (child sheet, child column, parent sheet, parent column, verb,
#  Mermaid cardinality read from parent to child)
RELATIONSHIPS = [
    ("Orders", "CustomerID", "Customers", "CustomerID", "places", "||--o{"),
    ("Orders", "EmployeeID", "Employees", "EmployeeID", "handles",
     "||--o{"),
    ("Orders", "ShipVia", "Shippers", "ShipperID", "ships", "||--o{"),
    ("Orders Details", "OrderID", "Orders", "OrderID", "contains",
     "||--|{"),
    ("Orders Details", "ProductID", "Product", "ProductID", "appears in",
     "||--o{"),
    ("Product", "CategoryID", "Categories", "CategoryID", "groups",
     "||--o{"),
    ("Product", "SupplierID", "Suppliers", "SupplierID", "supplies",
     "||--o{"),
    ("Employees", "ReportsTo", "Employees", "EmployeeID", "reports to",
     "|o--o{"),
]

# Columns drawn in the ERD; contact details and the Product sheet's
# spreadsheet helper columns (Cheap, NewPrice, IsCheap) are left out.
ERD_COLUMNS = {
    "Customers": ["CustomerID", "CompanyName", "ContactName", "City",
                  "Region", "Country"],
    "Employees": ["EmployeeID", "LastName", "FirstName", "Title",
                  "HireDate", "Country", "ReportsTo"],
    "Shippers": ["ShipperID", "CompanyName", "Phone"],
    "Orders": ["OrderID", "CustomerID", "EmployeeID", "ShipVia",
               "OrderDate", "RequiredDate", "ShippedDate", "Freight",
               "ShipCountry"],
    "Orders Details": ["OrderID", "ProductID", "UnitPrice", "Quantity",
                       "Discount"],
    "Product": ["ProductID", "ProductName", "SupplierID", "CategoryID",
                "QuantityPerUnit", "Price", "UnitsInStock",
                "UnitsOnOrder", "ReorderLevel", "Discontinued"],
    "Categories": ["CategoryID", "CategoryName", "Description"],
    "Suppliers": ["SupplierID", "CompanyName", "ContactName", "City",
                  "Country"],
}

# Top-left corner of each table in the PNG ERD, in plot units.
ERD_LAYOUT = {
    "Customers": (0.5, 21.5),
    "Employees": (0.5, 16.5),
    "Shippers": (0.5, 10.5),
    "Orders": (8.5, 17.5),
    "Orders Details": (16.5, 16.5),
    "Product": (24.5, 17.5),
    "Categories": (32.5, 20.0),
    "Suppliers": (32.5, 14.0),
}
BOX_WIDTH = 5.6
HEADER_HEIGHT = 0.6
ROW_HEIGHT = 0.5

# Ship-to countries grouped into sales regions for the growth analysis.
REGIONS = {
    "North America": ["USA", "Canada", "Mexico"],
    "South America": ["Brazil", "Venezuela", "Argentina"],
    "Western Europe": ["Germany", "Austria", "Switzerland", "France",
                       "Belgium"],
    "Northern Europe": ["UK", "Ireland", "Sweden", "Denmark", "Finland",
                        "Norway"],
    "Southern & Eastern Europe": ["Spain", "Italy", "Portugal", "Poland"],
}
COUNTRY_REGION = {c: r for r, countries in REGIONS.items()
                  for c in countries}

# Chart colors from the dataviz reference palette (light mode).
# Categorical slots 1-5 go to regions in fixed order; the blue/red
# diverging poles mark growing vs declining countries.
SERIES_COLORS = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4"]
UP_COLOR, DOWN_COLOR = "#2a78d6", "#e34948"
INK, INK_2, MUTED = "#0b0b0b", "#52514e", "#898781"
GRID, AXIS, SURFACE = "#e1e0d9", "#c3c2b7", "#fcfcfb"

# Like-for-like windows; orders run from 4 Jul 1996 to 6 May 1998, so
# whole calendar years cannot be compared.
WINDOWS = {
    "H2 1996": ("1996-07-01", "1997-01-01"),
    "H2 1997": ("1997-07-01", "1998-01-01"),
    "Jan-Apr 1997": ("1997-01-01", "1997-05-01"),
    "Jan-Apr 1998": ("1998-01-01", "1998-05-01"),
}
LAST_FULL_QUARTER = pd.Period("1998Q1")
LARGE_SHARE = 0.05   # share of revenue that makes a market "large"
SMALL_BASE = 5000    # Jan-Apr 1997 revenue below this is a small base

# Concentration analysis: how many top customers/products to single out,
# and the HHI level above which a base counts as concentrated (US DOJ
# merger guideline, on a 0-10,000 scale).
TOP_N = 5
HHI_CONCENTRATED = 1500
OTHER_COLOR = "#b4b2a9"

# Fulfillment analysis: an order counts as "fast" if it ships within
# FAST_DAYS; product differences must clear a Bonferroni-corrected
# 5% test across all products to count as more than chance.
FAST_DAYS = 7
ALPHA = 0.05
BOOTSTRAP_REPS = 2000


def load_workbook(path):
    """Read every sheet of the workbook.

    Args:
        path (pathlib.Path): Northwind ``.xlsx`` file.

    Returns:
        dict[str, pandas.DataFrame]: Each sheet keyed by its name.

    Raises:
        SystemExit: If the file is locked, e.g. open in Excel.
    """
    try:
        return pd.read_excel(path, sheet_name=None)
    except PermissionError:
        sys.exit(f"Cannot open {path.name}: close it in Excel and rerun.")


def md_table(df):
    """Render a DataFrame as a Markdown table.

    Args:
        df (pandas.DataFrame): Rows to render; the index is ignored.

    Returns:
        str: Markdown table with floats to 2 decimals and thousands
        separators on numbers.
    """
    def fmt(value):
        """Format one table cell.

        Args:
            value (object): Cell value.

        Returns:
            str: Bools as-is, floats to 2 decimals with separators,
            ints with separators, anything else via ``str``.
        """
        if isinstance(value, bool):
            return str(value)
        if pd.api.types.is_float(value):
            return f"{value:,.2f}"
        if pd.api.types.is_integer(value):
            return f"{value:,}"
        return str(value)

    header = "| " + " | ".join(map(str, df.columns)) + " |"
    rule = "|" + "---|" * len(df.columns)
    rows = ["| " + " | ".join(fmt(v) for v in row) + " |"
            for row in df.itertuples(index=False)]
    return "\n".join([header, rule, *rows])


def build_sales(sheets):
    """Join order lines with orders, products, customers and staff.

    Args:
        sheets (dict[str, pandas.DataFrame]): Workbook sheets by name.

    Returns:
        pandas.DataFrame: One row per order line, with ``Revenue``
        (net of discount), ``GrossRevenue`` and descriptive columns.
    """
    lines = sheets["Orders Details"].copy()
    lines["Discount"] = lines["Discount"].round(2)
    lines["GrossRevenue"] = lines["UnitPrice"] * lines["Quantity"]
    lines["Revenue"] = lines["GrossRevenue"] * (1 - lines["Discount"])
    emp = sheets["Employees"].assign(
        Employee=lambda d: d["FirstName"] + " " + d["LastName"])
    products = sheets["Product"][["ProductID", "ProductName",
                                  "CategoryID", "Price"]]
    return (
        lines.merge(sheets["Orders"], on="OrderID")
        .merge(products, on="ProductID")
        .merge(sheets["Categories"][["CategoryID", "CategoryName"]],
               on="CategoryID")
        .merge(sheets["Customers"][["CustomerID", "CompanyName"]],
               on="CustomerID")
        .merge(emp[["EmployeeID", "Employee"]], on="EmployeeID")
    )


def check_integrity(sheets):
    """Count duplicate primary keys and orphaned foreign keys.

    Args:
        sheets (dict[str, pandas.DataFrame]): Workbook sheets by name.

    Returns:
        tuple[dict[str, int], dict[str, int]]: Duplicate key rows per
        sheet, and orphaned non-null values per relationship label.
    """
    duplicates = {name: int(sheets[name].duplicated(keys).sum())
                  for name, keys in PRIMARY_KEYS.items()}
    orphans = {}
    for child, fk, parent, pk, *_ in RELATIONSHIPS:
        values = sheets[child][fk].dropna()
        missing = ~values.isin(sheets[parent][pk])
        orphans[f"{child}.{fk} -> {parent}.{pk}"] = int(missing.sum())
    return duplicates, orphans


def overview_section(sheets):
    """Describe each sheet's size, key and missing values.

    Args:
        sheets (dict[str, pandas.DataFrame]): Workbook sheets by name.

    Returns:
        list[str]: Markdown lines for the overview section.
    """
    rows = []
    for name, df in sheets.items():
        nulls = df.isna().sum()
        nulls = ", ".join(f"{c} ({n})" for c, n in nulls[nulls > 0].items())
        rows.append({"Sheet": name, "Rows": len(df), "Columns": df.shape[1],
                     "Primary key": " + ".join(PRIMARY_KEYS.get(name, [])),
                     "Missing values": nulls or "none"})
    return ["## Tables", "", md_table(pd.DataFrame(rows)), ""]


def sales_section(sales):
    """Summarize revenue over time, order size and discounts.

    Args:
        sales (pandas.DataFrame): Order lines from ``build_sales``.

    Returns:
        list[str]: Markdown lines for the sales section.
    """
    dates = sales["OrderDate"]
    gross, net = sales["GrossRevenue"].sum(), sales["Revenue"].sum()
    by_year = (sales.groupby(dates.dt.year.astype(str))
               .agg(Orders=("OrderID", "nunique"), Revenue=("Revenue", "sum"))
               .rename_axis("Year").reset_index())
    by_month = (sales.groupby(dates.dt.to_period("M").astype(str))
                .agg(Orders=("OrderID", "nunique"),
                     Revenue=("Revenue", "sum"))
                .rename_axis("Month").reset_index())
    order_value = sales.groupby("OrderID")["Revenue"].sum()
    lines_per_order = sales.groupby("OrderID").size()
    discounts = (sales["Discount"].value_counts().sort_index()
                 .rename_axis("Discount").reset_index(name="Lines"))
    return [
        "## Sales", "",
        f"- Order dates: {dates.min():%Y-%m-%d} to {dates.max():%Y-%m-%d}"
        " (1996 and 1998 are partial years)",
        f"- Gross revenue: ${gross:,.2f}; net revenue: ${net:,.2f}; "
        f"discounts: ${gross - net:,.2f}",
        f"- Order value: mean ${order_value.mean():,.0f}, median "
        f"${order_value.median():,.0f}, max ${order_value.max():,.0f}",
        f"- Lines per order: mean {lines_per_order.mean():.2f}, "
        f"max {lines_per_order.max()}", "",
        "### Revenue by year", "", md_table(by_year), "",
        "### Revenue by month", "", md_table(by_month), "",
        "### Discount levels", "", md_table(discounts), "",
    ]


def product_section(sales, sheets):
    """Summarize categories, best sellers, prices and stock.

    Args:
        sales (pandas.DataFrame): Order lines from ``build_sales``.
        sheets (dict[str, pandas.DataFrame]): Workbook sheets by name.

    Returns:
        list[str]: Markdown lines for the product section.
    """
    products = sheets["Product"]
    by_cat = (sales.groupby("CategoryName")
              .agg(Revenue=("Revenue", "sum"), Units=("Quantity", "sum"))
              .sort_values("Revenue", ascending=False).reset_index())
    top_rev = (sales.groupby("ProductName")["Revenue"].sum().nlargest(10)
               .reset_index())
    top_units = (sales.groupby("ProductName")["Quantity"].sum().nlargest(5)
                 .reset_index(name="Units"))
    low = products[(products["UnitsInStock"] <= products["ReorderLevel"])
                   & ~products["Discontinued"]]
    price = products["Price"]
    return [
        "## Products", "",
        f"- {len(products)} products in {len(sheets['Categories'])} "
        f"categories from {len(sheets['Suppliers'])} suppliers in "
        f"{sheets['Suppliers']['Country'].nunique()} countries; "
        f"{int(products['Discontinued'].sum())} discontinued",
        f"- List price: min ${price.min():,.2f}, median "
        f"${price.median():,.2f}, max ${price.max():,.2f}",
        f"- {len(low)} active products at or below their reorder level",
        "",
        "### Revenue by category", "", md_table(by_cat), "",
        "### Top 10 products by revenue", "", md_table(top_rev), "",
        "### Top 5 products by units sold", "", md_table(top_units), "",
    ]


def customer_section(sales, sheets):
    """Summarize customers, geography and revenue concentration.

    Args:
        sales (pandas.DataFrame): Order lines from ``build_sales``.
        sheets (dict[str, pandas.DataFrame]): Workbook sheets by name.

    Returns:
        list[str]: Markdown lines for the customer section.
    """
    customers, orders = sheets["Customers"], sheets["Orders"]
    idle = sorted(set(customers["CustomerID"]) - set(orders["CustomerID"]))
    per_customer = orders["CustomerID"].value_counts()
    by_country = (sales.groupby("ShipCountry")["Revenue"].sum()
                  .nlargest(10).reset_index())
    top = sales.groupby("CompanyName")["Revenue"].sum().nlargest(10)
    share = top.head(3).sum() / sales["Revenue"].sum()
    return [
        "## Customers", "",
        f"- {len(customers)} customers in "
        f"{customers['Country'].nunique()} countries; "
        f"without orders: {', '.join(idle) or 'none'}",
        f"- Orders per customer: mean {per_customer.mean():.1f}, "
        f"min {per_customer.min()}, max {per_customer.max()}",
        f"- Top 3 customers bring in {share:.0%} of net revenue", "",
        "### Top 10 ship-to countries by revenue", "",
        md_table(by_country), "",
        "### Top 10 customers by revenue", "",
        md_table(top.reset_index()), "",
    ]


def employee_section(sales, sheets):
    """Summarize sales performance per employee.

    Args:
        sales (pandas.DataFrame): Order lines from ``build_sales``.
        sheets (dict[str, pandas.DataFrame]): Workbook sheets by name.

    Returns:
        list[str]: Markdown lines for the employee section.
    """
    emp = sheets["Employees"][["EmployeeID", "Title", "Country"]]
    perf = (sales.groupby(["EmployeeID", "Employee"])
            .agg(Orders=("OrderID", "nunique"), Revenue=("Revenue", "sum"))
            .reset_index().merge(emp, on="EmployeeID")
            .sort_values("Revenue", ascending=False)
            [["Employee", "Title", "Country", "Orders", "Revenue"]])
    return ["## Employees", "", md_table(perf), ""]


def shipping_section(sheets):
    """Summarize shippers, freight cost and delivery timing.

    Args:
        sheets (dict[str, pandas.DataFrame]): Workbook sheets by name.

    Returns:
        list[str]: Markdown lines for the shipping section.
    """
    orders = sheets["Orders"]
    shippers = (orders.merge(sheets["Shippers"], left_on="ShipVia",
                             right_on="ShipperID")
                .groupby("CompanyName")
                .agg(Orders=("OrderID", "count"),
                     AvgFreight=("Freight", "mean"),
                     TotalFreight=("Freight", "sum"))
                .reset_index())
    days = (orders["ShippedDate"] - orders["OrderDate"]).dt.days
    late = int((orders["ShippedDate"] > orders["RequiredDate"]).sum())
    unshipped = int(orders["ShippedDate"].isna().sum())
    return [
        "## Shipping", "", md_table(shippers), "",
        f"- Freight per order: mean ${orders['Freight'].mean():,.2f}, "
        f"max ${orders['Freight'].max():,.2f}",
        f"- Days to ship: mean {days.mean():.1f}, median {days.median():.0f}"
        f", max {days.max():.0f}",
        f"- Shipped after the required date: {late}; never shipped: "
        f"{unshipped}", "",
    ]


def quality_section(sheets):
    """List integrity checks and data-quality issues.

    Args:
        sheets (dict[str, pandas.DataFrame]): Workbook sheets by name.

    Returns:
        list[str]: Markdown lines for the data-quality section.
    """
    duplicates, orphans = check_integrity(sheets)
    products, lines = sheets["Product"], sheets["Orders Details"]
    helpers = [c for c in products.columns
               if c.startswith(("Cheap", "NewPrice", "IsCheap", "Unnamed"))]
    odd_cheap = products.loc[~products["Cheap"].isin(["t", "f"]),
                             "ProductName"].tolist()
    noisy = lines["Discount"].round(2).ne(lines["Discount"]).sum()
    repriced = lines.merge(products, on="ProductID")
    repriced = int((repriced["UnitPrice"] != repriced["Price"]).sum())
    return [
        "## Data quality", "",
        f"- Duplicate primary keys: {sum(duplicates.values())}",
        f"- Orphaned foreign keys: {sum(orphans.values())} across "
        f"{len(orphans)} relationships",
        f"- Product helper columns: {', '.join(helpers)}",
        f"- Product.Cheap values other than t/f: {odd_cheap}",
        f"- Product.IsCheap marks {int(products['IsCheap'].sum())} products"
        f" (price <= 10) vs {int((products['Cheap'] == 't').sum())} for "
        "Cheap (price < 10)",
        f"- Order lines priced differently from today's list price: "
        f"{repriced} of {len(lines)}",
        f"- Discounts stored with floating-point noise: {int(noisy)}", "",
    ]


def pct_change(before, after):
    """Compute growth from one period to the next.

    Args:
        before (pandas.Series): Revenue in the earlier window.
        after (pandas.Series): Revenue in the later window.

    Returns:
        pandas.Series: ``after / before - 1``; NaN if ``before`` is 0.
    """
    return (after / before.where(before > 0)) - 1


def fmt_pct(value):
    """Format a ratio as a signed whole percentage.

    Args:
        value (float): Ratio such as 0.25; NaN allowed.

    Returns:
        str: E.g. ``"+25%"``, or ``"new"`` for NaN (no earlier sales).
    """
    return "new" if pd.isna(value) else f"{value:+.0%}"


def window_revenue(sales, by):
    """Sum revenue per group in each comparison window.

    Args:
        sales (pandas.DataFrame): Order lines from ``build_sales``.
        by (str | pandas.Series): Column name or series to group by.

    Returns:
        pandas.DataFrame: One column per ``WINDOWS`` entry, plus
        ``H2 growth`` and ``Jan-Apr growth`` ratios.
    """
    cols = {}
    for name, (start, end) in WINDOWS.items():
        mask = (sales["OrderDate"] >= start) & (sales["OrderDate"] < end)
        cols[name] = sales[mask].groupby(by)["Revenue"].sum()
    out = pd.DataFrame(cols).fillna(0.0)
    out["H2 growth"] = pct_change(out["H2 1996"], out["H2 1997"])
    out["Jan-Apr growth"] = pct_change(out["Jan-Apr 1997"],
                                       out["Jan-Apr 1998"])
    return out


def classify_market(share, growth, overall):
    """Assign a country to a focus segment.

    Args:
        share (float): Country's share of total net revenue (0-1).
        growth (float): Jan-Apr 1998 vs 1997 growth ratio; NaN if the
            country had no sales in Jan-Apr 1997.
        overall (float): Company-wide growth ratio for the same window.

    Returns:
        str: ``Invest``, ``Defend``, ``Develop``, ``Monitor`` or
        ``Fix or deprioritize``.
    """
    if pd.isna(growth):
        return "Develop"
    if growth < 0:
        return "Fix or deprioritize"
    if share >= LARGE_SHARE:
        return "Invest" if growth >= overall else "Defend"
    return "Develop" if growth >= overall else "Monitor"


def country_growth(sales):
    """Measure each country's revenue share, growth and focus segment.

    Args:
        sales (pandas.DataFrame): Order lines from ``build_sales``.

    Returns:
        pandas.DataFrame: One row per ship-to country, sorted by share,
        with window revenue, growth ratios, ``Region``, ``Share`` and
        ``Segment``.
    """
    totals = window_revenue(sales, "ShipCountry")
    overall = (totals["Jan-Apr 1998"].sum()
               / totals["Jan-Apr 1997"].sum() - 1)
    share = sales.groupby("ShipCountry")["Revenue"].sum()
    totals["Share"] = share / share.sum()
    totals["Region"] = totals.index.map(COUNTRY_REGION)
    totals["Segment"] = [classify_market(s, g, overall) for s, g in
                         zip(totals["Share"], totals["Jan-Apr growth"])]
    return totals.sort_values("Share", ascending=False)


def growth_section(sales):
    """Rank country and region growth and recommend where to focus.

    Args:
        sales (pandas.DataFrame): Order lines from ``build_sales``.

    Returns:
        list[str]: Markdown lines with region and country growth
        tables, focus segments and caveats.
    """
    by_country = country_growth(sales)
    regions = window_revenue(sales, sales["ShipCountry"].map(COUNTRY_REGION))
    regions["Share"] = (sales.groupby(sales["ShipCountry"]
                                      .map(COUNTRY_REGION))["Revenue"].sum()
                        / sales["Revenue"].sum())
    regions = regions.sort_values("Share", ascending=False)
    jan_apr = by_country[["Jan-Apr 1997", "Jan-Apr 1998"]].sum()
    overall = jan_apr["Jan-Apr 1998"] / jan_apr["Jan-Apr 1997"] - 1

    region_rows = pd.DataFrame({
        "Region": regions.index,
        "Share": regions["Share"].map("{:.0%}".format),
        "H2 1996": regions["H2 1996"],
        "H2 1997": regions["H2 1997"],
        "H2 growth": regions["H2 growth"].map(fmt_pct),
        "Jan-Apr 1997": regions["Jan-Apr 1997"],
        "Jan-Apr 1998": regions["Jan-Apr 1998"],
        "Jan-Apr growth": regions["Jan-Apr growth"].map(fmt_pct),
    })
    country_rows = pd.DataFrame({
        "Country": by_country.index,
        "Region": by_country["Region"],
        "Share": by_country["Share"].map("{:.1%}".format),
        "Jan-Apr 1997": by_country["Jan-Apr 1997"],
        "Jan-Apr 1998": by_country["Jan-Apr 1998"],
        "Jan-Apr growth": by_country["Jan-Apr growth"].map(fmt_pct),
        "H2 growth": by_country["H2 growth"].map(fmt_pct),
        "Segment": by_country["Segment"],
    })

    segments = []
    for name, rule in [
        ("Invest", f"large (>= {LARGE_SHARE:.0%} of revenue) and growing "
                   "faster than the company"),
        ("Defend", "large but growing slower than the company"),
        ("Develop", "small but growing faster than the company"),
        ("Monitor", "small and growing slower than the company"),
        ("Fix or deprioritize", "revenue fell year over year"),
    ]:
        members = by_country.index[by_country["Segment"] == name]
        segments.append(f"- **{name}** ({rule}): "
                        f"{', '.join(members) or 'none'}")
    both_down = by_country.index[(by_country["H2 growth"] < 0)
                                 & (by_country["Jan-Apr growth"] < 0)]
    small = by_country.index[by_country["Jan-Apr 1997"] < SMALL_BASE]
    return [
        "## Country and regional growth", "",
        "Orders run from July 1996 to 6 May 1998, so calendar years are "
        "not comparable. Growth compares like-for-like windows: H2 1997 "
        "vs H2 1996, and Jan-Apr 1998 vs Jan-Apr 1997 (the latest).", "",
        f"- Company-wide growth, Jan-Apr 1998 vs 1997: {fmt_pct(overall)}",
        "",
        "### By region", "", md_table(region_rows), "",
        "### By country", "", md_table(country_rows), "",
        "### Where to focus", "", *segments, "",
        f"- Declining in both windows: {', '.join(both_down) or 'none'}",
        f"- Small base (Jan-Apr 1997 revenue < ${SMALL_BASE:,}), so "
        f"growth rates are volatile: {', '.join(small)}", "",
        "Charts: `region_trend.png` (quarterly revenue by region) and "
        "`country_trends.png` (top 12 countries).", "",
    ]


def quarterly_revenue(sales, by):
    """Pivot revenue into full quarters by group.

    Args:
        sales (pandas.DataFrame): Order lines from ``build_sales``.
        by (pandas.Series): Group label for each order line.

    Returns:
        pandas.DataFrame: Quarters (up to ``LAST_FULL_QUARTER``) as
        rows, groups as columns, net revenue as values.
    """
    quarter = sales["OrderDate"].dt.to_period("Q")
    table = (sales.groupby([quarter, by])["Revenue"].sum()
             .unstack(fill_value=0.0))
    return table[table.index <= LAST_FULL_QUARTER]


def style_axes(ax):
    """Apply recessive gridlines, axes and a $k y-axis format.

    Call ``ax.set_ylim(bottom=0)`` after plotting; setting it here
    would freeze the y-range before the data is drawn.

    Args:
        ax (matplotlib.axes.Axes): Axes to style in place.

    Returns:
        None.
    """
    ax.set_facecolor(SURFACE)
    ax.grid(axis="y", color=GRID, lw=1)
    ax.set_axisbelow(True)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color(AXIS)
    ax.tick_params(colors=MUTED, length=0, labelsize=9)
    ax.yaxis.set_major_formatter(
        matplotlib.ticker.FuncFormatter(lambda v, _: f"${v / 1000:,.0f}k"))


def draw_region_trend(sales, out_path):
    """Draw a line chart of quarterly revenue by region.

    Args:
        sales (pandas.DataFrame): Order lines from ``build_sales``.
        out_path (pathlib.Path): PNG destination; overwritten.

    Returns:
        None. Saves the chart to ``out_path``.
    """
    table = quarterly_revenue(sales, sales["ShipCountry"].map(COUNTRY_REGION))
    table = table[list(REGIONS)]
    labels = [f"Q{q.quarter} {q.year}" for q in table.index]
    x = range(len(labels))
    fig, ax = plt.subplots(figsize=(11, 6), facecolor=SURFACE)
    style_axes(ax)
    for region, color in zip(REGIONS, SERIES_COLORS):
        ax.plot(x, table[region], color=color, lw=2, label=region,
                solid_capstyle="round", solid_joinstyle="round")
        ax.plot(x[-1], table[region].iloc[-1], "o", color=color, ms=8,
                mec=SURFACE, mew=2)
    ax.set_ylim(bottom=0)

    # Direct end labels, nudged apart so they do not collide.
    ends = sorted(((table[r].iloc[-1], r) for r in REGIONS))
    gap = table.values.max() * 0.06
    placed = []
    for value, region in ends:
        y = max(value, placed[-1] + gap) if placed else value
        placed.append(y)
        ax.text(x[-1] + 0.15, y, f"{region}  ${value / 1000:,.0f}k",
                va="center", fontsize=9, color=INK_2)

    ax.set_xticks(list(x), labels)
    ax.set_xlim(-0.2, len(labels) + 1.2)
    ax.legend(loc="upper left", frameon=False, fontsize=9,
              labelcolor=INK_2)
    fig.suptitle("Net revenue by region, per quarter", x=0.06, ha="left",
                 fontsize=14, color=INK)
    ax.set_title("Q2 1998 left out: orders stop on 6 May 1998",
                 loc="left", fontsize=9, color=MUTED)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150, facecolor=SURFACE)
    plt.close(fig)


def draw_country_trends(sales, growth, out_path, top=12):
    """Draw small-multiple line charts for the largest countries.

    Args:
        sales (pandas.DataFrame): Order lines from ``build_sales``.
        growth (pandas.DataFrame): Output of ``country_growth``.
        out_path (pathlib.Path): PNG destination; overwritten.
        top (int): Number of countries, by revenue share, to plot.

    Returns:
        None. Saves the chart to ``out_path``.
    """
    countries = list(growth.index[:top])
    table = quarterly_revenue(sales, sales["ShipCountry"])
    labels = [f"Q{q.quarter}\n{str(q.year)[2:]}" for q in table.index]
    cols = 4
    rows = -(-len(countries) // cols)
    fig, axes = plt.subplots(rows, cols, figsize=(14, 3 * rows),
                             facecolor=SURFACE, squeeze=False)
    for ax, country in zip(axes.flat, countries):
        change = growth.loc[country, "Jan-Apr growth"]
        color = DOWN_COLOR if change < 0 else UP_COLOR
        style_axes(ax)
        ax.plot(range(len(labels)), table[country], color=color, lw=2)
        ax.plot(len(labels) - 1, table[country].iloc[-1], "o", color=color,
                ms=8, mec=SURFACE, mew=2)
        ax.set_ylim(bottom=0)
        ax.set_title(f"{country}   {fmt_pct(change)} YoY  ·  "
                     f"{growth.loc[country, 'Segment']}",
                     loc="left", fontsize=10, color=INK)
        ax.set_xticks(range(len(labels)), labels)
        ax.yaxis.set_major_locator(matplotlib.ticker.MaxNLocator(3))
    for ax in axes.flat[len(countries):]:
        ax.axis("off")
    fig.suptitle(f"Quarterly net revenue, top {len(countries)} countries "
                 "(each panel has its own y-axis)", x=0.02, ha="left",
                 fontsize=14, color=INK)
    fig.text(0.02, 0.005, "YoY = Jan-Apr 1998 vs Jan-Apr 1997. Blue line: "
             "growing; red line: declining.", fontsize=9, color=MUTED)
    fig.tight_layout(rect=(0, 0.02, 1, 1))
    fig.savefig(out_path, dpi=150, facecolor=SURFACE)
    plt.close(fig)


def concentration_stats(revenue):
    """Measure how concentrated revenue is across entities.

    Args:
        revenue (pandas.Series): Net revenue per customer or product.

    Returns:
        dict[str, float]: ``count``; ``top1``, ``top5`` and ``top10``
        revenue shares; ``n50`` and ``n80``, the fewest entities that
        make up 50% and 80% of revenue; ``hhi`` on a 0-10,000 scale.
    """
    share = revenue.sort_values(ascending=False) / revenue.sum()
    cumulative = share.cumsum()
    return {
        "count": len(share),
        "top1": share.iloc[0],
        "top5": share.head(5).sum(),
        "top10": share.head(10).sum(),
        "n50": int((cumulative < 0.5).sum() + 1),
        "n80": int((cumulative < 0.8).sum() + 1),
        "hhi": float((share ** 2).sum() * 10_000),
    }


def entity_summary(sales, key, partner):
    """Summarize revenue and reach for each customer or product.

    Args:
        sales (pandas.DataFrame): Order lines from ``build_sales``.
        key (str): Column naming the entity, ``CompanyName`` or
            ``ProductName``.
        partner (str): Column naming the other side of each sale, used
            to find each entity's biggest partner.

    Returns:
        pandas.DataFrame: One row per entity, sorted by revenue, with
        ``Revenue``, ``Share``, ``Orders``, ``Units``, ``Partners``
        (distinct partners), ``Days since last order``,
        ``Top partner`` and ``Top partner share`` (of the entity's
        revenue).
    """
    end = sales["OrderDate"].max()
    out = sales.groupby(key).agg(
        Revenue=("Revenue", "sum"), Orders=("OrderID", "nunique"),
        Units=("Quantity", "sum"), Partners=(partner, "nunique"),
        Last=("OrderDate", "max"))
    out["Share"] = out["Revenue"] / out["Revenue"].sum()
    out["Days since last order"] = (end - out.pop("Last")).dt.days
    pair = sales.groupby([key, partner])["Revenue"].sum()
    top = pair.loc[pair.groupby(level=0).idxmax()].reset_index(level=1)
    out["Top partner"] = top[partner]
    out["Top partner share"] = top["Revenue"] / out["Revenue"]
    return out.sort_values("Revenue", ascending=False)


def loss_scenarios(summary, n=TOP_N):
    """Model losing each of the top entities, then all of them at once.

    Args:
        summary (pandas.DataFrame): Output of ``entity_summary``.
        n (int): Number of top entities to model.

    Returns:
        pandas.DataFrame: One row per scenario with ``If lost``,
        ``Revenue lost``, ``Revenue drop`` (formatted percentage) and
        ``Revenue left``.
    """
    total = summary["Revenue"].sum()
    top = summary.head(n)
    rows = [(name, rev) for name, rev in top["Revenue"].items()]
    rows.append((f"All top {n} together", top["Revenue"].sum()))
    return pd.DataFrame({
        "If lost": [name for name, _ in rows],
        "Revenue lost": [rev for _, rev in rows],
        "Revenue drop": [f"-{rev / total:.1%}" for _, rev in rows],
        "Revenue left": [total - rev for _, rev in rows],
    })


def concentration_section(sales, sheets):
    """Quantify revenue dependence on top customers and products.

    Args:
        sales (pandas.DataFrame): Order lines from ``build_sales``.
        sheets (dict[str, pandas.DataFrame]): Workbook sheets by name.

    Returns:
        list[str]: Markdown lines with concentration measures, loss
        scenarios and findings.
    """
    customers = entity_summary(sales, "CompanyName", "ProductName")
    products = entity_summary(sales, "ProductName", "CompanyName")
    products["Discontinued"] = products.index.map(
        sheets["Product"].set_index("ProductName")["Discontinued"])
    stats = {"Customers": concentration_stats(customers["Revenue"]),
             "Products": concentration_stats(products["Revenue"])}

    measures = [
        ("Entities with sales", "count", "{:.0f}"),
        ("Share of the #1", "top1", "{:.1%}"),
        ("Share of the top 5", "top5", "{:.1%}"),
        ("Share of the top 10", "top10", "{:.1%}"),
        ("Needed for 50% of revenue", "n50", "{:.0f}"),
        ("Needed for 80% of revenue", "n80", "{:.0f}"),
        ("HHI (0-10,000)", "hhi", "{:,.0f}"),
    ]
    stats_rows = pd.DataFrame(
        [{"Measure": label,
          **{k: fmt.format(v[key]) for k, v in stats.items()}}
         for label, key, fmt in measures])

    top_c = customers.head(TOP_N)
    cust_rows = pd.DataFrame({
        "Customer": top_c.index,
        "Share": top_c["Share"].map("{:.1%}".format),
        "Orders": top_c["Orders"],
        "Days since last order": top_c["Days since last order"],
        "Biggest product": top_c["Top partner"],
    })
    top_p = products.head(TOP_N)
    prod_rows = pd.DataFrame({
        "Product": top_p.index,
        "Share": top_p["Share"].map("{:.1%}".format),
        "Buyers": top_p["Partners"],
        "Biggest buyer": top_p["Top partner"],
        "Biggest buyer's share": top_p["Top partner share"]
        .map("{:.0%}".format),
        "Discontinued": top_p["Discontinued"],
    })

    gone = products[products["Discontinued"]]
    top10_gone = gone.index.intersection(products.index[:10])
    level = ("concentrated" if max(s["hhi"] for s in stats.values())
             >= HHI_CONCENTRATED else "not concentrated")
    c, p = stats["Customers"], stats["Products"]
    return [
        "## Revenue concentration and loss scenarios", "",
        "### How concentrated is revenue?", "", md_table(stats_rows), "",
        f"- Both HHIs sit far below {HHI_CONCENTRATED:,}, so the base is "
        f"{level} overall, but the top is steep: {c['top5']:.0%} of "
        f"revenue comes from {TOP_N} of {c['count']} customers and "
        f"{p['top5']:.0%} from {TOP_N} of {p['count']} products.",
        f"- Discontinued products already account for "
        f"{gone['Share'].sum():.1%} of past revenue, including top-10 "
        f"sellers {', '.join(top10_gone)}.", "",
        f"### Top {TOP_N} customers", "", md_table(cust_rows), "",
        f"### If a top customer leaves", "",
        md_table(loss_scenarios(customers)), "",
        f"### Top {TOP_N} products", "", md_table(prod_rows), "",
        f"### If a top product is lost", "",
        md_table(loss_scenarios(products)), "",
        "Losses are first-order: they assume no buyer switches to "
        "another product and no lost customer is replaced.", "",
        "Chart: `concentration.png` (revenue vs orders per customer and "
        "revenue vs units per product).", "",
    ]


def mark_top(ax, table, x_col, hollow, key_xy):
    """Number the top entities' dots and write a matching key.

    Numbers sit inside enlarged dots, so clustered points stay legible
    without leader lines crossing other dots.

    Args:
        ax (matplotlib.axes.Axes): Axes to draw on.
        table (pandas.DataFrame): Output of ``entity_summary``.
        x_col (str): Column plotted on the x-axis.
        hollow (pandas.Series): True for entities drawn as hollow
            (discontinued), indexed like ``table``.
        key_xy (tuple[float, float]): Top-left of the key, in axes
            fraction coordinates.

    Returns:
        None. Draws numbered dots and the key text.
    """
    lines = []
    for rank, (name, row) in enumerate(table.head(TOP_N).iterrows(), 1):
        empty = bool(hollow[name])
        ax.scatter(row[x_col], row["Revenue"], s=300, zorder=4,
                   facecolors=SURFACE if empty else UP_COLOR,
                   edgecolors=UP_COLOR if empty else SURFACE,
                   linewidths=2)
        ax.text(row[x_col], row["Revenue"], str(rank), zorder=5,
                ha="center", va="center", fontsize=8, fontweight="bold",
                color=UP_COLOR if empty else "white")
        note = " (discontinued)" if empty else ""
        lines.append(f"{rank}  {name}  {row['Share']:.1%}{note}")
    ax.text(*key_xy, "\n".join(lines), transform=ax.transAxes,
            va="top", fontsize=9, color=INK_2, linespacing=1.7,
            bbox=dict(facecolor=SURFACE, edgecolor="none", pad=4))


def draw_concentration_scatter(sales, sheets, out_path):
    """Draw scatter plots of revenue concentration.

    The left panel plots customers (orders vs revenue); the right plots
    products (units vs revenue), with discontinued products hollow.

    Args:
        sales (pandas.DataFrame): Order lines from ``build_sales``.
        sheets (dict[str, pandas.DataFrame]): Workbook sheets by name.
        out_path (pathlib.Path): PNG destination; overwritten.

    Returns:
        None. Saves the chart to ``out_path``.
    """
    customers = entity_summary(sales, "CompanyName", "ProductName")
    products = entity_summary(sales, "ProductName", "CompanyName")
    discontinued = products.index.map(
        sheets["Product"].set_index("ProductName")["Discontinued"])
    fig, axes = plt.subplots(1, 2, figsize=(15, 6.5), facecolor=SURFACE)
    panels = [
        (axes[0], customers, "Orders", "Number of orders",
         "Customers", pd.Series(False, index=customers.index),
         (0.30, 0.82), "upper left"),
        (axes[1], products, "Units", "Units sold", "Products",
         pd.Series(discontinued, index=products.index), (0.42, 0.78),
         "upper right"),
    ]
    for ax, table, x_col, x_label, name, hollow, key_xy, corner in panels:
        style_axes(ax)
        rest = table.iloc[TOP_N:]
        for empty in (False, True):
            rows = rest[hollow[rest.index] == empty]
            if rows.empty:
                continue
            ax.scatter(rows[x_col], rows["Revenue"], s=64, zorder=3,
                       facecolors=SURFACE if empty else OTHER_COLOR,
                       edgecolors=OTHER_COLOR if empty else SURFACE,
                       linewidths=2 if empty else 1.5,
                       label="Other, discontinued" if empty else "Other")
        ax.scatter([], [], s=64, color=UP_COLOR,
                   label=f"Top {TOP_N} by revenue (numbered)")
        mark_top(ax, table, x_col, hollow, key_xy)
        ax.set_ylim(bottom=0, top=table["Revenue"].max() * 1.12)
        ax.set_xlim(0, table[x_col].max() * 1.08)
        ax.set_xlabel(x_label, color=MUTED, fontsize=9)
        stats = concentration_stats(table["Revenue"])
        ax.set_title(f"{name}: top {TOP_N} = {stats['top5']:.0%} of "
                     f"revenue; {stats['n80']} of {stats['count']} make "
                     "80%", loc="left", fontsize=11, color=INK)
        ax.legend(loc=corner, frameon=False, fontsize=9,
                  labelcolor=INK_2)
    fig.suptitle("How dependent is revenue on a few customers and "
                 "products?", x=0.02, ha="left", fontsize=14, color=INK)
    fig.text(0.02, 0.01, "Each dot is one customer or product. The key "
             "gives each numbered dot's share of total net revenue "
             "(Jul 1996 - May 1998).",
             fontsize=9, color=MUTED)
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    fig.savefig(out_path, dpi=150, facecolor=SURFACE)
    plt.close(fig)


def order_fulfillment(sheets):
    """Compute fulfillment timing for every order.

    Args:
        sheets (dict[str, pandas.DataFrame]): Workbook sheets by name.

    Returns:
        pandas.DataFrame: One row per order with ``Shipper``,
        ``Days`` (order to shipment; NaN if unshipped), ``Shipped``,
        ``Late`` (shipped after the required date), ``Fast`` (shipped
        within ``FAST_DAYS``), ``Freight`` and ``Revenue``.
    """
    lines = sheets["Orders Details"]
    revenue = (lines["UnitPrice"] * lines["Quantity"]
               * (1 - lines["Discount"].round(2))).groupby(
                   lines["OrderID"]).sum()
    names = sheets["Shippers"].set_index("ShipperID")["CompanyName"]
    orders = sheets["Orders"]
    days = (orders["ShippedDate"] - orders["OrderDate"]).dt.days
    return pd.DataFrame({
        "OrderID": orders["OrderID"],
        "Shipper": orders["ShipVia"].map(names),
        "Days": days,
        "Shipped": orders["ShippedDate"].notna(),
        "Late": orders["ShippedDate"] > orders["RequiredDate"],
        "Fast": days <= FAST_DAYS,
        "Freight": orders["Freight"],
        "Revenue": orders["OrderID"].map(revenue),
    })


def bootstrap_mean_ci(values, reps=BOOTSTRAP_REPS, seed=0):
    """Estimate a 95% confidence interval for a mean by bootstrapping.

    Args:
        values (pandas.Series): Observations; NaNs are dropped.
        reps (int): Number of bootstrap resamples.
        seed (int): Random seed, for reproducible intervals.

    Returns:
        tuple[float, float]: Lower and upper bounds (2.5th and 97.5th
        percentiles of the resampled means).
    """
    data = values.dropna().to_numpy()
    rng = np.random.default_rng(seed)
    means = rng.choice(data, (reps, len(data))).mean(axis=1)
    return float(np.percentile(means, 2.5)), float(np.percentile(means,
                                                                 97.5))


def shipper_scorecard(orders):
    """Compare shippers on speed, reliability and cost.

    Args:
        orders (pandas.DataFrame): Output of ``order_fulfillment``.

    Returns:
        pandas.DataFrame: One row per shipper, fastest mean first, with
        order counts, mean/median/90th-percentile days, bootstrap
        ``CI low``/``CI high`` for the mean, ``Fast rate``,
        ``Late rate`` (of shipped orders), ``Unshipped``,
        ``Avg freight`` and ``Freight / revenue``.
    """
    shipped = orders[orders["Shipped"]]
    card = shipped.groupby("Shipper").agg(
        Orders=("OrderID", "count"), Mean=("Days", "mean"),
        Median=("Days", "median"),
        P90=("Days", lambda d: d.quantile(0.9)),
        Fast_rate=("Fast", "mean"), Late_rate=("Late", "mean"))
    card = card.rename(columns={"Fast_rate": "Fast rate",
                                "Late_rate": "Late rate"})
    cis = {s: bootstrap_mean_ci(g["Days"])
           for s, g in shipped.groupby("Shipper")}
    card["CI low"] = [cis[s][0] for s in card.index]
    card["CI high"] = [cis[s][1] for s in card.index]
    by_all = orders.groupby("Shipper")
    card["Orders"] = by_all.size()
    card["Unshipped"] = by_all["Shipped"].apply(lambda s: int((~s).sum()))
    card["Avg freight"] = by_all["Freight"].mean()
    card["Freight / revenue"] = (by_all["Freight"].sum()
                                 / by_all["Revenue"].sum())
    return card.sort_values("Mean")


def product_ship_times(sheets, orders):
    """Test whether any product ships slower or faster than average.

    Each product inherits the shipping time of every shipped order it
    appears on, and its mean is compared with the overall line-level
    mean using a z-test with a Bonferroni correction across products.

    Args:
        sheets (dict[str, pandas.DataFrame]): Workbook sheets by name.
        orders (pandas.DataFrame): Output of ``order_fulfillment``.

    Returns:
        tuple[pandas.DataFrame, float, float]: Per-product table sorted
        by mean days (``Mean``, ``Median``, ``Orders``, ``CI low``,
        ``CI high``, ``Z``, ``Verdict``), the overall mean days, and
        the z threshold used.
    """
    lines = (sheets["Orders Details"][["OrderID", "ProductID"]]
             .merge(orders[["OrderID", "Days"]], on="OrderID")
             .dropna(subset=["Days"]))
    lines["Product"] = lines["ProductID"].map(
        sheets["Product"].set_index("ProductID")["ProductName"])
    overall, spread = lines["Days"].mean(), lines["Days"].std()
    table = lines.groupby("Product")["Days"].agg(
        Mean="mean", Median="median", Orders="count", SD="std")
    half = 1.96 * table["SD"].fillna(0) / np.sqrt(table["Orders"])
    table["CI low"], table["CI high"] = (table["Mean"] - half,
                                         table["Mean"] + half)
    table["Z"] = (table["Mean"] - overall) / (spread
                                              / np.sqrt(table["Orders"]))
    threshold = NormalDist().inv_cdf(1 - ALPHA / 2 / len(table))
    table["Verdict"] = np.select(
        [table["Z"] >= threshold, table["Z"] <= -threshold],
        ["Slower", "Faster"], "Typical")
    return table.drop(columns="SD").sort_values("Mean"), overall, threshold


def fulfillment_section(sheets):
    """Compare shipper fulfillment and flag slow-shipping products.

    Args:
        sheets (dict[str, pandas.DataFrame]): Workbook sheets by name.

    Returns:
        list[str]: Markdown lines with the shipper scorecard, the
        slowest and fastest products, and conclusions.
    """
    orders = order_fulfillment(sheets)
    card = shipper_scorecard(orders)
    products, overall, z_cut = product_ship_times(sheets, orders)

    card_rows = pd.DataFrame({
        "Shipper": card.index,
        "Orders": card["Orders"],
        "Mean days": card["Mean"].map("{:.1f}".format),
        "95% CI": [f"{lo:.1f}-{hi:.1f}" for lo, hi in
                   zip(card["CI low"], card["CI high"])],
        "Median": card["Median"].map("{:.0f}".format),
        "90th pct": card["P90"].map("{:.0f}".format),
        f"Within {FAST_DAYS} days": card["Fast rate"].map("{:.0%}".format),
        "Late": card["Late rate"].map("{:.1%}".format),
        "Unshipped": card["Unshipped"],
        "Avg freight": card["Avg freight"].map("${:,.2f}".format),
        "Freight / revenue": card["Freight / revenue"]
        .map("{:.1%}".format),
    })

    def product_rows(table):
        """Format product ship-time rows for a Markdown table.

        Args:
            table (pandas.DataFrame): Rows from ``product_ship_times``.

        Returns:
            pandas.DataFrame: Display columns with formatted numbers.
        """
        return pd.DataFrame({
            "Product": table.index,
            "Orders": table["Orders"],
            "Mean days": table["Mean"].map("{:.1f}".format),
            "Median": table["Median"].map("{:.0f}".format),
            "z": table["Z"].map("{:+.1f}".format),
            "Verdict": table["Verdict"],
        })

    fast, slow = card.index[0], card.index[-1]
    overlap = card.loc[fast, "CI high"] >= card.loc[slow, "CI low"]
    flagged = products[products["Verdict"] != "Typical"]
    naive = int((products["Z"].abs() >= 1.96).sum())
    return [
        "## Fulfillment by shipper and product", "",
        "Days = order date to shipped date. Late = shipped after the "
        "required date. 95% CI of the mean from "
        f"{BOOTSTRAP_REPS:,} bootstrap resamples.", "",
        "### Shipper scorecard", "", md_table(card_rows), "",
        f"- Fastest: {fast} (mean {card.loc[fast, 'Mean']:.1f} days); "
        f"slowest: {slow} (mean {card.loc[slow, 'Mean']:.1f} days, 90th "
        f"percentile {card.loc[slow, 'P90']:.0f} days).",
        f"- The confidence intervals of {fast} and {slow} "
        + ("overlap, so the gap may be noise." if overlap else
           "do not overlap, so the gap is unlikely to be chance."),
        f"- Late shipments are rare for every shipper "
        f"({card['Late rate'].min():.1%}-{card['Late rate'].max():.1%}); "
        "most orders allow 28 days.", "",
        "### Do some products take longer to ship?", "",
        f"Overall mean: {overall:.1f} days per order line. A product is "
        f"flagged only if |z| >= {z_cut:.2f} (5% Bonferroni-corrected "
        f"across {len(products)} products).", "",
        "#### Slowest 10 products", "",
        md_table(product_rows(products.tail(10).iloc[::-1])), "",
        "#### Fastest 5 products", "",
        md_table(product_rows(products.head(5))), "",
        "- Beyond chance: "
        + (", ".join(f"{p} (mean {r['Mean']:.1f} vs median "
                     f"{r['Median']:.0f} days, so a few very slow orders "
                     "drive it)" for p, r in flagged.iterrows())
           or "none") + ". "
        f"Without the correction, {naive} products would look unusual "
        f"at |z| >= 1.96, about the {len(products) * ALPHA:.0f} expected "
        "by chance alone.",
        "- Shipping time is measured per order, so a slow order slows "
        "every product on it; products are not shipped separately.", "",
        "Charts: `shipper_performance.png`, `shipment_share.png` (pie "
        "of orders by shipper) and `product_ship_times.png`.",
        "",
    ]


def draw_shipper_performance(sheets, out_path):
    """Draw a three-panel shipper comparison.

    Panels: distribution of days to ship (box plot with mean and 95%
    CI), share of orders shipped late, and average freight per order.

    Args:
        sheets (dict[str, pandas.DataFrame]): Workbook sheets by name.
        out_path (pathlib.Path): PNG destination; overwritten.

    Returns:
        None. Saves the chart to ``out_path``.
    """
    orders = order_fulfillment(sheets)
    card = shipper_scorecard(orders).iloc[::-1]
    names = list(card.index)
    colors = dict(zip(sorted(names), SERIES_COLORS))
    y = np.arange(len(names))
    fig, axes = plt.subplots(1, 3, figsize=(16, 4.8), facecolor=SURFACE,
                             gridspec_kw={"width_ratios": [2.2, 1, 1]})

    ax = axes[0]
    style_axes(ax)
    ax.grid(axis="y", visible=False)
    ax.grid(axis="x", color=GRID, lw=1)
    data = [orders.loc[orders["Shipper"] == n, "Days"].dropna()
            for n in names]
    box = ax.boxplot(data, positions=y, orientation="horizontal",
                     widths=0.45,
                     patch_artist=True, showfliers=True,
                     medianprops=dict(color=INK, lw=1.5),
                     flierprops=dict(marker="o", ms=4, mfc=OTHER_COLOR,
                                     mec="none"),
                     whiskerprops=dict(color=MUTED),
                     capprops=dict(color=MUTED))
    for patch, n in zip(box["boxes"], names):
        patch.set(facecolor=colors[n], alpha=0.25, edgecolor=colors[n])
    for i, n in enumerate(names):
        ax.errorbar(card.loc[n, "Mean"], i,
                    xerr=[[card.loc[n, "Mean"] - card.loc[n, "CI low"]],
                          [card.loc[n, "CI high"] - card.loc[n, "Mean"]]],
                    fmt="D", color=colors[n], ms=7, capsize=4, lw=2,
                    zorder=4)
        ax.text(card.loc[n, "CI high"] + 0.6, i + 0.3,
                f"mean {card.loc[n, 'Mean']:.1f}", fontsize=9, color=INK_2)
    ax.xaxis.set_major_formatter(matplotlib.ticker.ScalarFormatter())
    ax.set_yticks(y, names)
    ax.set_xlim(left=0)
    ax.set_xlabel("Days from order to shipment", color=INK_2, fontsize=10)
    ax.set_ylabel("Shipper", color=INK_2, fontsize=10)
    ax.set_title("Time to ship (box = middle 50%, line = median,\n"
                 "diamond = mean with 95% CI)", loc="left", fontsize=11,
                 color=INK)

    bars = [
        (axes[1], card["Late rate"] * 100, "{:.1f}%",
         "Orders shipped after required date (%)", "Late shipments"),
        (axes[2], card["Avg freight"], "${:,.0f}",
         "Average freight per order ($)", "Freight cost"),
    ]
    for ax, values, fmt, xlabel, title in bars:
        style_axes(ax)
        ax.grid(axis="y", visible=False)
        ax.grid(axis="x", color=GRID, lw=1)
        ax.xaxis.set_major_formatter(matplotlib.ticker.ScalarFormatter())
        ax.barh(y, values, height=0.16, color=[colors[n] for n in names])
        for i, v in enumerate(values):
            ax.text(v, i, "  " + fmt.format(v), va="center", fontsize=9,
                    color=INK_2)
        ax.set_yticks(y, names)
        ax.set_xlim(0, values.max() * 1.3)
        ax.set_xlabel(xlabel, color=INK_2, fontsize=10)
        ax.set_title(title, loc="left", fontsize=11, color=INK)
    fig.suptitle("Shipper fulfillment performance, Jul 1996 - May 1998",
                 x=0.01, ha="left", fontsize=14, color=INK)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150, facecolor=SURFACE)
    plt.close(fig)


def draw_shipment_share_pie(sheets, out_path):
    """Draw a pie chart of orders handled by each shipper.

    Counts every order by its assigned shipper (``ShipVia``),
    including orders not yet shipped.

    Args:
        sheets (dict[str, pandas.DataFrame]): Workbook sheets by name.
        out_path (pathlib.Path): PNG destination; overwritten.

    Returns:
        None. Saves the chart to ``out_path``.
    """
    orders = order_fulfillment(sheets)
    counts = orders["Shipper"].value_counts()
    colors = dict(zip(sorted(counts.index), SERIES_COLORS))
    total = counts.sum()
    fig, ax = plt.subplots(figsize=(8, 6.5), facecolor=SURFACE)
    ax.pie(counts, colors=[colors[n] for n in counts.index],
           startangle=90, counterclock=False,
           labels=[f"{n}\n{c:,} orders ({c / total:.0%})"
                   for n, c in counts.items()],
           labeldistance=1.12,
           textprops=dict(color=INK_2, fontsize=10),
           wedgeprops=dict(edgecolor=SURFACE, linewidth=2))
    ax.set_aspect("equal")
    fig.suptitle("Share of orders by shipper", x=0.03, y=0.98,
                 ha="left", fontsize=14, color=INK)
    fig.text(0.03, 0.925, f"All {total:,} orders, Jul 1996 - May 1998 "
             f"(includes {int((~orders['Shipped']).sum())} not yet "
             "shipped)", fontsize=9, color=MUTED)
    fig.tight_layout(rect=(0, 0, 1, 0.92))
    fig.savefig(out_path, dpi=150, facecolor=SURFACE)
    plt.close(fig)


def draw_product_ship_times(sheets, out_path):
    """Draw a ranked dot plot of mean days to ship for every product.

    Args:
        sheets (dict[str, pandas.DataFrame]): Workbook sheets by name.
        out_path (pathlib.Path): PNG destination; overwritten.

    Returns:
        None. Saves the chart to ``out_path``.
    """
    orders = order_fulfillment(sheets)
    table, overall, _ = product_ship_times(sheets, orders)
    colors = table["Verdict"].map({"Slower": DOWN_COLOR,
                                   "Faster": UP_COLOR,
                                   "Typical": OTHER_COLOR})
    y = np.arange(len(table))
    fig, ax = plt.subplots(figsize=(10, 0.19 * len(table) + 2),
                           facecolor=SURFACE)
    style_axes(ax)
    ax.grid(axis="y", visible=False)
    ax.grid(axis="x", color=GRID, lw=1)
    ax.xaxis.set_major_formatter(matplotlib.ticker.ScalarFormatter())
    ax.hlines(y, table["CI low"].clip(lower=0), table["CI high"],
              color=colors, lw=1.5)
    ax.scatter(table["Mean"], y, s=40, color=colors, zorder=3,
               edgecolors=SURFACE, linewidths=1)
    ax.axvline(overall, color=INK_2, lw=1, ls="-", zorder=1)
    ax.text(overall, len(table) + 0.3, f" overall mean {overall:.1f} days",
            fontsize=9, color=INK_2, va="bottom")
    ax.set_yticks(y, [f"{p}  (n={n})" for p, n in
                      zip(table.index, table["Orders"])], fontsize=7.5)
    ax.set_ylim(-1, len(table) + 1.5)
    ax.set_xlim(left=0)
    ax.set_xlabel("Mean days from order to shipment (line = 95% CI)",
                  color=INK_2, fontsize=10)
    ax.set_ylabel("Product (n = order lines)", color=INK_2, fontsize=10)
    ax.scatter([], [], color=DOWN_COLOR, label="Slower beyond chance "
               "(Bonferroni)")
    ax.scatter([], [], color=OTHER_COLOR, label="Within normal variation")
    ax.legend(loc="lower right", frameon=False, fontsize=9,
              labelcolor=INK_2)
    fig.suptitle("Do some products take longer to ship?", x=0.02,
                 y=0.995, ha="left", fontsize=14, color=INK)
    fig.text(0.02, 0.975, "Products ranked by mean shipping time of the "
             "orders they appear on", fontsize=10, color=MUTED)
    fig.tight_layout(rect=(0, 0, 1, 0.97))
    fig.savefig(out_path, dpi=150, facecolor=SURFACE)
    plt.close(fig)


def build_profile(sheets):
    """Assemble the full Markdown profile of the workbook.

    Args:
        sheets (dict[str, pandas.DataFrame]): Workbook sheets by name.

    Returns:
        str: Markdown report covering every section.
    """
    sales = build_sales(sheets)
    parts = [
        ["# Northwind dataset profile", ""],
        overview_section(sheets),
        sales_section(sales),
        product_section(sales, sheets),
        customer_section(sales, sheets),
        employee_section(sales, sheets),
        shipping_section(sheets),
        growth_section(sales),
        concentration_section(sales, sheets),
        fulfillment_section(sheets),
        quality_section(sheets),
    ]
    return "\n".join(line for part in parts for line in part)


def column_type(series):
    """Map a pandas column to a short ERD type name.

    Args:
        series (pandas.Series): Column to classify.

    Returns:
        str: One of ``int``, ``decimal``, ``date``, ``bool`` or
        ``string``; floats holding only whole numbers count as ``int``.
    """
    if pd.api.types.is_bool_dtype(series):
        return "bool"
    if pd.api.types.is_datetime64_any_dtype(series):
        return "date"
    if pd.api.types.is_integer_dtype(series):
        return "int"
    if pd.api.types.is_float_dtype(series):
        values = series.dropna()
        return "int" if (values == values.round()).all() else "decimal"
    return "string"


def key_tags(sheet, column):
    """Return the key markers for one column.

    Args:
        sheet (str): Sheet name.
        column (str): Column name in that sheet.

    Returns:
        list[str]: ``"PK"`` and/or ``"FK"``, or empty if neither.
    """
    tags = []
    if column in PRIMARY_KEYS[sheet]:
        tags.append("PK")
    if any(child == sheet and fk == column
           for child, fk, *_ in RELATIONSHIPS):
        tags.append("FK")
    return tags


def entity_name(sheet):
    """Convert a sheet name to a Mermaid entity name.

    Args:
        sheet (str): Sheet name, possibly with spaces.

    Returns:
        str: Upper-case name with spaces replaced by underscores.
    """
    return sheet.upper().replace(" ", "_")


def build_mermaid(sheets):
    """Write the ERD as Mermaid ``erDiagram`` source.

    Args:
        sheets (dict[str, pandas.DataFrame]): Workbook sheets by name.

    Returns:
        str: Mermaid source with relationships and entity columns.
    """
    out = ["erDiagram"]
    for child, _, parent, _, verb, card in RELATIONSHIPS:
        out.append(f'  {entity_name(parent)} {card} {entity_name(child)}'
                   f' : "{verb}"')
    for sheet, columns in ERD_COLUMNS.items():
        out.append(f"  {entity_name(sheet)} {{")
        for col in columns:
            tags = ", ".join(key_tags(sheet, col))
            line = f"    {column_type(sheets[sheet][col])} {col}"
            out.append(f"{line} {tags}".rstrip())
        out.append("  }")
    return "\n".join(out) + "\n"


def row_y(sheet, column):
    """Return the vertical centre of a column's row in the PNG ERD.

    Args:
        sheet (str): Sheet name.
        column (str): Column name listed in ``ERD_COLUMNS[sheet]``.

    Returns:
        float: Y coordinate in plot units.
    """
    top = ERD_LAYOUT[sheet][1]
    index = ERD_COLUMNS[sheet].index(column)
    return top - HEADER_HEIGHT - ROW_HEIGHT * (index + 0.5)


def draw_table(ax, sheet, df):
    """Draw one table box with its header and column rows.

    Args:
        ax (matplotlib.axes.Axes): Axes to draw on.
        sheet (str): Sheet name; sets position and listed columns.
        df (pandas.DataFrame): Sheet data, used for row count and types.

    Returns:
        float: Y coordinate of the box's bottom edge.
    """
    x, top = ERD_LAYOUT[sheet]
    columns = ERD_COLUMNS[sheet]
    bottom = top - HEADER_HEIGHT - ROW_HEIGHT * len(columns)
    ax.add_patch(Rectangle((x, bottom), BOX_WIDTH, top - bottom,
                           facecolor="white", edgecolor="#5f5e5a", lw=1))
    ax.add_patch(Rectangle((x, top - HEADER_HEIGHT), BOX_WIDTH,
                           HEADER_HEIGHT, facecolor="#534ab7",
                           edgecolor="#5f5e5a", lw=1))
    ax.text(x + 0.15, top - HEADER_HEIGHT / 2, sheet, color="white",
            fontsize=10, fontweight="bold", va="center")
    ax.text(x + BOX_WIDTH - 0.15, top - HEADER_HEIGHT / 2,
            f"{len(df):,} rows", color="#cecbf6", fontsize=8,
            va="center", ha="right")
    for i, col in enumerate(columns):
        y = row_y(sheet, col)
        if i % 2:
            ax.add_patch(Rectangle((x, y - ROW_HEIGHT / 2), BOX_WIDTH,
                                   ROW_HEIGHT, facecolor="#f1efe8", lw=0))
        tags = key_tags(sheet, col)
        ax.text(x + 0.15, y, col, fontsize=8.5, va="center",
                fontweight="bold" if "PK" in tags else "normal")
        ax.text(x + 3.4, y, column_type(df[col]), fontsize=7.5,
                va="center", color="#5f5e5a")
        ax.text(x + BOX_WIDTH - 0.15, y, ",".join(tags), fontsize=7.5,
                va="center", ha="right", color="#993c1d")
    return bottom


def draw_link(ax, child, fk, parent, pk, lane):
    """Draw an elbow connector from a parent key to a child key.

    Args:
        ax (matplotlib.axes.Axes): Axes to draw on.
        child (str): Sheet holding the foreign key.
        fk (str): Foreign-key column in ``child``.
        parent (str): Sheet holding the referenced key.
        pk (str): Referenced column in ``parent``.
        lane (float): Fraction (0-1) across the gap between the two
            boxes where the vertical segment runs.

    Returns:
        None. Draws the line and its ``1``/``N`` cardinality labels.
    """
    y1, y2 = row_y(parent, pk), row_y(child, fk)
    px, cx = ERD_LAYOUT[parent][0], ERD_LAYOUT[child][0]
    style = dict(color="#73726c", lw=1)
    if parent == child:
        x0 = px - 0.4
        ax.plot([px, x0, x0, px], [y1, y1, y2, y2], **style)
        ax.text(px - 0.05, y1 + 0.12, "0..1", fontsize=7, ha="right")
        ax.text(px - 0.05, y2 + 0.12, "N", fontsize=7, ha="right")
        return
    if px < cx:
        x1, x2, sign = px + BOX_WIDTH, cx, 1
    else:
        x1, x2, sign = px, cx + BOX_WIDTH, -1
    xm = x1 + (x2 - x1) * lane
    ax.plot([x1, xm, xm, x2], [y1, y1, y2, y2], **style)
    ax.text(x1 + sign * 0.15, y1 + 0.12, "1", fontsize=7,
            ha="left" if sign > 0 else "right")
    ax.text(x2 - sign * 0.15, y2 + 0.12, "N", fontsize=7,
            ha="right" if sign > 0 else "left")


def draw_erd(sheets, out_path):
    """Render the ERD to a PNG file.

    Args:
        sheets (dict[str, pandas.DataFrame]): Workbook sheets by name.
        out_path (pathlib.Path): PNG destination; overwritten.

    Returns:
        None. Saves the figure to ``out_path``.
    """
    fig, ax = plt.subplots(figsize=(20, 8.5))
    bottoms = [draw_table(ax, s, sheets[s]) for s in ERD_LAYOUT]
    gaps = {}
    for child, fk, parent, pk, *_ in RELATIONSHIPS:
        gap = tuple(sorted((ERD_LAYOUT[parent][0], ERD_LAYOUT[child][0])))
        gaps.setdefault(gap, []).append((child, fk, parent, pk))
    for links in gaps.values():
        for i, (child, fk, parent, pk) in enumerate(links):
            draw_link(ax, child, fk, parent, pk, (i + 1) / (len(links) + 1))
    ax.set_xlim(-0.5, ERD_LAYOUT["Suppliers"][0] + BOX_WIDTH + 0.5)
    ax.set_ylim(min(bottoms) - 0.5, 22)
    ax.axis("off")
    ax.set_title("Northwind entity-relationship diagram", fontsize=14,
                 loc="left")
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def main(argv=None):
    """Profile the workbook and write the report and ERD files.

    Args:
        argv (list[str] | None): Command-line arguments; None reads
            ``sys.argv``.

    Returns:
        None. Prints the profile and writes ``northwind_profile.md``,
        ``northwind_erd.mmd``, ``northwind_erd.png``,
        ``region_trend.png``, ``country_trends.png``,
        ``concentration.png``, ``shipper_performance.png``,
        ``product_ship_times.png`` and ``shipment_share.png``.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workbook", type=Path, default=DEFAULT_WORKBOOK)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    args = parser.parse_args(argv)

    sys.stdout.reconfigure(encoding="utf-8")
    sheets = load_workbook(args.workbook)
    args.out_dir.mkdir(parents=True, exist_ok=True)

    profile = build_profile(sheets)
    (args.out_dir / "northwind_profile.md").write_text(profile,
                                                       encoding="utf-8")
    (args.out_dir / "northwind_erd.mmd").write_text(build_mermaid(sheets),
                                                    encoding="utf-8")
    draw_erd(sheets, args.out_dir / "northwind_erd.png")
    sales = build_sales(sheets)
    draw_region_trend(sales, args.out_dir / "region_trend.png")
    draw_country_trends(sales, country_growth(sales),
                        args.out_dir / "country_trends.png")
    draw_concentration_scatter(sales, sheets,
                               args.out_dir / "concentration.png")
    draw_shipper_performance(sheets,
                             args.out_dir / "shipper_performance.png")
    draw_product_ship_times(sheets, args.out_dir / "product_ship_times.png")
    draw_shipment_share_pie(sheets, args.out_dir / "shipment_share.png")

    print(profile)
    print(f"Files written to {args.out_dir}")


if __name__ == "__main__":
    main()
