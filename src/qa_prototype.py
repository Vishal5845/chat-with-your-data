import pandas as pd
import re
import matplotlib.pyplot as plt
import os

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
    
    def display(self, category, query=None):
        print(f"\n🔎 Query: {query}")
        meta = self.metadata[category]
        df = self.load_csv(category)
        
        # Determine top N 
        n = self.extract_top_n(query) if meta["top_n"] and query else None
        if meta['top_n'] and n:
            df = df.sort_values(meta["value_col"], ascending=False).head(n)

        # Plot if true
        if meta["plot"]:
            if meta["name_col"] not in df.columns or meta["value_col"] not in df.columns:
                print("CSV must have the required columns for plotting.")
                return
            
            name_col = meta["name_col"]
            value_col = meta["value_col"]
            # try converting to datetime safely
            try:
                df[name_col] = pd.to_datetime(df[name_col], format="%Y-%m")
                is_time_series = True
            except Exception:
                is_time_series = True

            # Print the table first
            print(f"\n{category.replace('_',' ').title()}")
            print("-" * 40)
            print(df.to_string(index=False))

            if is_time_series:
                df.plot(x = name_col, y=value_col, kind="line", marker="o")
            else:
                df.plot(x=name_col, y=value_col, kind="bar")

            plt.title(f"{category.replace('_',' ').title()} Trend")
            plt.ylabel(value_col)
            plt.xlabel(name_col)
            plt.tight_layout()

            # Save Chart
            save_path = f"reports/plots/{category}.png"
            plt.savefig(save_path)
            plt.show()
            print(f"✅ Plot saved to {save_path}")
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
        with open(self.log_file, 'a') as f:
            f.write(f"Query: {query} | Category: {category} | Status: {status}\n")

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

