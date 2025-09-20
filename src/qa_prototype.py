import pandas as pd
import os

class QAPrototype:
    def __init__ (self, summary_folder = "data/processed"):
        self.summary_folder = summary_folder
    
    def get_file_path(self, query_type):
        """ Map query types to file paths """
        mapping = {
            "countries by revenue" : "countries_revenue.csv",
            "products by revenue" : "products_revenue.csv",
            "total customers" : "summary.csv",
            "total revenue" : "summary.csv"
        }
        file_name = mapping.get(query_type.lower())
        if not file_name:
            raise ValueError(f"No CSV mapping found for query '{query_type}'")
        file_path = os.path.join(self.summary_folder, file_name)
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File '{file_path}' does not exist.")
        return file_path
    
    def load_csv(self, query_type):
        """ Load CSV file into DataFrame """
        file_path = self.get_file_path(query_type)
        return pd.read_csv(file_path)
    
    def top_n(self, query_type, n=None, value_col = None, name_col = None):
        df = self.load_csv(query_type)
        if value_col and value_col in df.columns:
            df_sort = df.sort_values(value_col, ascending=False).head(n)
        else:
            df_sort = df.head(n)
        
        return df_sort[[name_col, value_col]] if name_col and value_col else df_sort
    
    def preety_print(self, query_type, n=None, value_col = None, name_col = None):
        df_top = self.top_n(query_type, n, value_col, name_col)

        if name_col and value_col:
            print(f"Top {n} {query_type.title()}")
            print("-"*30)
            for _,row in df_top.iterrows():
                if value_col and name_col:
                    print(f"{row[name_col]}\t${row[value_col]:,}")
        else:
            if query_type.lower() == "total customers":
                print(f"Total Customers: {int(df_top.iloc[0]['Total Customers']):,}")
            else:
                for _, row in df_top.iterrows():
                    print({i.title(): row[i] for i in df_top.columns})
    
    def run_interactive(self):
        print("Welcome to QA Prototype! Type 'exit' to quit.")
        while True:
            query = input("\nEnter your query: ").strip().lower()
            if query == 'exit':
                print("Exiting. Goodbye!")
                break

            try:
                n = None
                if "top" in query:
                    parts = query.split()
                    try:
                        idx = parts.index("top")
                        n = int(parts[idx+1])
                    except (ValueError, IndexError):
                        n = 5
                
                if "country" in query:
                    query_type = "countries by revenue"
                    value_col = "Revenue"
                    name_col = "Country"
                elif "product" in query:
                    query_type = "products by revenue"
                    value_col = "Revenue"
                    name_col = "Description"
                elif "customer" in query:
                    query_type = "total customers"
                    value_col = None
                    name_col = None
                else:
                    print("Sorry, I can't understand that query.")
                    continue

                self.preety_print(query_type, n, value_col, name_col)
            except Exception as e:
                print(e)


if __name__ == "__main__":
    qa = QAPrototype(summary_folder="data/processed")
    qa.run_interactive()

