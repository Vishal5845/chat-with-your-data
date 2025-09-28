import pandas as pd
import re
import matplotlib.pyplot as plt
import os
from datetime import *

# Load all summaries

summary = pd.read_csv("data/processed/summary.csv").to_dict(orient="records")[0]
countries = pd.read_csv("data/processed/countries_revenue.csv")
products = pd.read_csv("data/processed/products_revenue.csv")


class QAPrototype:
    def __init__ (self, summary_folder = "data/processed"):
        self.summary_folder = summary_folder
        os.makedirs("reports/plots", exist_ok=True)
        os.makedirs("logs", exist_ok=True)
        self.log_file = "logs/qa_log.txt"

        # Synonyms for query types
        self.queries = {
            "customers": ["customer", "customers", "users", "buyers"],
            "revenue": ["revenue", "sales", "income"],
            "countries": ["country", "countries", "nation", "region"],
            "products": ["product", "products", "item", "sku"],
            "monthly_revenue": ["monthly revenue", "sales trend", "trend"]
        }

        # Metadata defines CSV, columns, and behavior for each category
        self.metadata = {
            "customers" :{
                "file": "summary.csv",
                "name_col": None,
                "value_col": "Total Customers",
                "top_n": False,
                "plot": False
            },
            "revenue" :{
                "file": "summary.csv",
                "name_col": None,
                "value_col": "Total Revenue",
                "top_n": False,
                "plot": False
            },
            "countries" :{
                "file": "countries_revenue.csv",
                "name_col": "Country",
                "value_col": "Revenue",
                "top_n": True,
                "plot": True
            },
            "products" :{
                "file": "products_revenue.csv",
                "name_col": "Description",
                "value_col": "Revenue",
                "top_n": True,
                "plot": True
            },
            "monthly_revenue" :{
                "file": "monthly_revenue.csv",
                "name_col": "YearMonth",
                "value_col": "Revenue",
                "top_n": False,
                "plot": True
            }
        }
    
    def detect_category(self, query: str):
        """Detect category using synonyms."""
        q = query.lower()
        for cat, words in self.queries.items():
            if any(i in q for i in words):
                return cat
        return None
    
    def extract_top_n(self, query:str, default=5):
        """Extract Top N from query, default=5."""
        match = re.search(r"\btop\s*(\d+)", query.lower())
        return int(match.group(1)) if match else default
    
    def load_csv(self, category):
        """ Load CSV file into DataFrame """
        meta = self.metadata[category]
        file_path = os.path.join(self.summary_folder, meta["file"])
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"CSV file not found: {file_path}")
        return pd.read_csv(file_path)
    
    def plot_chart(self, df, x_col, y_col, category, chart_type=None):
        if chart_type is None:
            print(f"⚠️ No chart type specified for {category}, skipping plot.")
            return
        
        if chart_type == "line":
            df[x_col] = pd.to_datetime(df[x_col], format="%Y-%m")
            df.plot(x_col, y_col, kind= "line", marker="o")
        elif chart_type == "bar":
            df.plot(x_col, y_col, kind="bar")
        else:
            print(f"⚠️ Unknown chart type: {chart_type}")
            return
        
        plt.title(f"{category.replace('_',' ').title()} Trend")
        plt.ylabel(y_col)
        plt.xlabel(x_col)
        plt.tight_layout()
        save_path = f"reports/plots/{category}.png"
        plt.savefig(save_path)
        plt.show()
        print(f"✅ Plot saved to {save_path}")
    
    def display(self, category, query=None):
        print(f"\n🔎 Query: {query}")
        meta = self.metadata[category]
        df = self.load_csv(category)
        
        # Determine top N 
        n = self.extract_top_n(query) if meta["top_n"] and query else None
        if meta['top_n'] and n:
            df = df.sort_values(meta["value_col"], ascending=False).head(n)

        # Combined Query
        if "products" in query.lower() and ("country" in query.lower() or "from" in query.lower() or "in" in query.lower()):
            # print("iside if")
            country_match = re.search(r"(?:in|from) ([\w\s]+)", query, re.IGNORECASE)
            # print(country_match)
            if country_match:
                country = country_match.group(1).strip().title()
                print(country)
                tx_file = os.path.join(self.summary_folder, "transactions.csv")
                if os.path.exists(tx_file):
                    tx = pd.read_csv(tx_file)
                    top_n = self.extract_top_n(query)
                    df_country = (
                        tx[tx["Country"] == country]
                        .groupby("Description")["Revenue"].sum().nlargest(n).reset_index()
                    )
                    self.plot_chart(df_country, "Description", "Revenue", f"products_in_{country}", "bar")
                    print(f"\nTop {top_n} Products in {country}")
                    print("-"*40)
                    print(df_country.to_string(index=False))
                    return
        
        # Decide chart type
        chart_type = None
        if meta["plot"] :
            if category == "monthly_revenue":
                chart_type = "line"
            else:
                chart_type = "bar"
            
            self.plot_chart(df, meta["name_col"], meta["value_col"], category, chart_type)
            return
        
        # Top N display
        if meta["top_n"] and n:
            print(f"\nTop {n} {category.replace('_', ' ').title()}")
            print("-"*40)
            for _, r in df.iterrows():
                print(f"{r[meta['name_col']]:<25} ${r[meta['value_col']]:,}")
        else:
            # Single value display
            print(f"{meta['value_col']}: {df.iloc[0][meta['value_col']]:,}")
    
    def fallback_response(self):
        print("Sorry, I don’t know how to answer that yet.")
        print("Try asking about customers, revenue, countries, products, or monthly trends.")
    
    def log_query(self, query:str, category: str = None, status:str = "success"):
        """Log user queries with detected category and status."""
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        with open(self.log_file, 'a') as f:
            f.write(f"[{ts}] Query: {query} | Category: {category} | Status: {status}\n")

    def run_interactive(self):
        print("Welcome to QA Prototype! Type 'exit' to quit.")
        while True:
            query = input("\nEnter your query: ").strip().lower()
            if query == 'exit':
                print("Exiting. Goodbye!")
                break

            try:
                cat = self.detect_category(query)
                if not cat:
                    self.fallback_response()
                    self.log_query(query, None, "fallback")
                    continue
                self.display(cat, query)
                self.log_query(query, cat, status="success")

            except Exception as e:
                print(f"⚠️ Error: {e}")
                self.log_query(query, category="Error", status=str(e))


if __name__ == "__main__":
    qa = QAPrototype(summary_folder="data/processed")
    qa.run_interactive()

