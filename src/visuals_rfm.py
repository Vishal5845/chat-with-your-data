import pandas as pd
import duckdb as ddb
import matplotlib.pyplot as plt
import seaborn as sns

con = ddb.connect("ai_assistant.duckdb")

rfm_df = con.execute("select * from rfm").fetchdf()
print(rfm_df.head())

# Plot histograms for R, F, M
fig, axes = plt.subplots(1,3, figsize=(15,5))
axes[0].hist(rfm_df["Recency"], bins=30, color='skyblue', edgecolor='black')
axes[0].set_title('Recency Distribution')

axes[1].hist(rfm_df["Frequency"], bins=30, color='lightgreen', edgecolor='black')
axes[1].set_title('Frequency Distribution')

axes[2].hist(rfm_df["Monetary"], bins=30, color='salmon', edgecolor='black')
axes[2].set_title('Monetary Distribution')

plt.tight_layout()
plt.savefig("reports/rfm_histograms.png")
plt.close()

# Segments bar chart
rfm_df["Segment"].value_counts().plot(kind = "bar", color= "purple", figsize=(8,8), rot=45)
plt.title("Customer Segments Distribution")
plt.ylabel("Number of Customers")
plt.savefig("reports/rfm_segments_distribution.png")
plt.close()

# Heatmap
rfm_pivot = rfm_df.pivot_table(index = "R_Quartile", columns= "F_Quartile", values="CustomerID", aggfunc="count")

plt.figure(figsize=(6,4))
sns.heatmap(rfm_pivot, annot=True, fmt="g", cmap="YlGnBu")
plt.title("Recency vs Frequency Heatmap")
plt.savefig("reports/rfm_heatmap.png")
plt.close()