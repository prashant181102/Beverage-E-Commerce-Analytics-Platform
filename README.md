# Beverage-E-Commerce-Analytics-Platform
A comprehensive data analytics project analyzing India's beverage e-commerce market across 6 major platforms — Amazon, Flipkart, BigBasket, Blinkit, JioMart, and Meesho. Built on a 1,00,000-row synthetic dataset spanning 36 Indian states and 10 beverage categories.
# Problem Statement

India's beverage e-commerce market is growing rapidly, yet stakeholders lack a comprehensive data-driven view of:

Which states generate the highest sales revenue and why?
How do product health scores correlate with pricing and consumer ratings?
Which beverage categories dominate which marketplaces?
Is there a significant difference in profit margins across platforms and brands?
Which nutrition categories are underserved in Tier-2 and Tier-3 states?
How do seasonal trends affect demand for energy drinks, teas, and health drinks?
What is the impact of discount strategy on revenue and profit margins?

# Tools & Technologies

Tool                      Purpose
PythonCore                programming language
Pandas & NumPyData        manipulation & analysis
Excel (openpyxl)          Dataset creation & reporting
Requests                  HTTP requests for web scraping
BeautifulSoup             HTML parsing & data extraction
Power BI                  Dashboard & data visualization


# Analysis Performed

1.  State-Wise Revenue Analysis
Aggregated revenue across all 36 states using Pareto analysis
Identified Top 5 and Bottom 5 states by beverage sales performance
2.  Platform-Wise Profit Margin Analysis
Compared average profit margins across all 6 platforms
Discovered platform fee structures impacting seller profitability
3.  Category × Marketplace Analysis
Cross-tabulated beverage categories against marketplaces by revenue
Identified category dominance per platform
4.  Health Score vs. Price Correlation
Applied Pearson Correlation between Health Score and Selling Price
Validated nutritional value pricing premium hypothesis
5.  Seasonal Demand Analysis
Plotted monthly revenue trends across all 10 categories
Identified peak demand windows for inventory planning
6.  Discount Optimization
Scatter plot analysis of Revenue vs. Discount Percent
Applied Polynomial Regression to find optimal discount range
7.  Tier-2 & Tier-3 Gap Analysis
Measured premium brand penetration in states outside top 10
Identified underserved nutrition markets
8.  Premium Brand Rating Analysis
Applied T-test comparing Premium vs. Non-Premium brand ratings
Validated consistency of premium brand customer satisfaction
9.  Return Rate Analysis
Analyzed return rate patterns across categories and platforms
Flagged high-risk categories for quality improvement
10.  Quality Grade × State Heatmap
Mapped consumer grade preferences across all 36 states
Identified regional quality expectation
