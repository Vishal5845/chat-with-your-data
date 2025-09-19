import pandas as pd
import duckdb as ddb
import matplotlib.pyplot as plt
import seaborn as sns

con = ddb.connect("ai_assistant.duckdb")

cohort = con.execute("""
    with first_order as(
                    select customerid, min(strptime(Invoicedate, '%m/%d/%Y %H:%M')) as first_order_date
                    from ecommerce
                     group by customerid
                     ),
    cohort as(
                     select e.customerid,
                     strftime(fp.first_order_date, '%Y-%m') as cohort_month,
                     strftime(strptime(e.invoicedate, '%m/%d/%Y %H:%M'), '%Y-%m') as order_month
                     from ecommerce e
                     join first_order fp
                     on e.customerid = fp.customerid
                    )
    select cohort_month,order_month,
    count(distinct customerid) as active_customers
    from cohort
    group by cohort_month, order_month
    order by cohort_month, order_month
                     """).fetch_df()

print(cohort.head())
print(cohort["cohort_month"].unique())
print(cohort["order_month"].unique())

# Cohort Pivot
# Pivot table
cohort_pivot = cohort.pivot_table(
    index='cohort_month',
    columns='order_month',
    values='active_customers',
    aggfunc='sum'
)

# Normalize per cohort (each row by its first non-null value)
cohort_norm = cohort_pivot.divide(cohort_pivot.iloc[:, 0], axis=0)

# More robust: normalize row by first available value
cohort_norm = cohort_pivot.div(cohort_pivot.apply(lambda row: row[row.first_valid_index()], axis=1), axis=0)

# CSV Export
cohort_norm.to_csv("data/processed/cohot_analysis.csv")


plt.figure(figsize=(12, 6))
sns.heatmap(cohort_norm, annot=True, fmt=".0%", cmap="Blues")
plt.title('Cohort Analysis - Customer Retention')
plt.savefig("reports/cohort_analysis.png")

# first_orders = con.execute("""
#     select strftime(min(strptime(Invoicedate, '%m/%d/%Y %H:%M')), '%Y-%m') as first_month,
#            count(distinct customerid) as customers
#     from ecommerce
#     group by customerid
# """).fetch_df()

# print(first_orders["first_month"].value_counts())

