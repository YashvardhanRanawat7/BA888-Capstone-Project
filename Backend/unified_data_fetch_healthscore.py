# Libraries

import requests
import json
import pandas as pd

# Class to fetch objects from Unified API

class UnifiedAPI_Data_Fetch:
    def __init__(self, api_key, base_url, account_id):
        self.api_key = api_key
        self.base_url = base_url
        self.account_id = account_id
        self.valid_combinations = {
            "accounting": {
                "account": "Fetches account data",
                "journal": "Fetches journal data",
                "transaction": "Fetches transaction data",
                "contact": "Fetches contact data",
                "invoice": "Fetches invoice data",
                "taxrate": "Fetches tax rate data",
                "organization": "Fetches organization data"
            },
            "hris": {
                "employee": "Fetches employee data",
                "company": "Fetches company data",
                "group": "Fetches group data",
                "timeoff": "Fetches time off data",
                "payslip": "Fetches payslip data"
            },
            "payment": {
                "payment": "Fetches payment data",
                "link": "Fetches link data",
                "refund": "Fetches refund data",
                "payout": "Fetches payout data"
            }
        }
        self.dataframes = {}

    def get_headers(self):
        return {
            "accept": "application/json",
            "authorization": f"Bearer {self.api_key}"
        }

    def get_data(self, api, endpoint):
        url = f'{self.base_url}/{api}/{self.account_id}/{endpoint}'
        response = requests.get(url, headers=self.get_headers())
        if response.status_code == 200:
            data = response.json()
            return data
        else:
            print(f"Error fetching {api}/{endpoint}: {response.status_code} - {response.text}")
            return None

    def save_to_dataframe(self, data, api, endpoint):
        if data is None:
            print(f"No data to save for {api}_{endpoint}")
            return

        if isinstance(data, list):
            df = pd.json_normalize(data)
            self.dataframes[f"{api}_{endpoint}"] = df
        else:
            print(f"Unexpected data format for {api}_{endpoint}: {json.dumps(data, indent=4)}")

    def save_dataframes_to_csv(self, output_dir):
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        for key, df in self.dataframes.items():
            file_path = os.path.join(output_dir, f"{key}.csv")
            df.to_csv(file_path, index=False)
            print(f"Saved {key} to {file_path}")

    def fetch_all_data(self):
        for api, endpoints in self.valid_combinations.items():
            for endpoint, description in endpoints.items():
                print(f"Fetching data for {api}/{endpoint}: {description}")
                data = self.get_data(api, endpoint)
                self.save_to_dataframe(data, api, endpoint)
        return self.dataframes

def main():
    API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySWQiOiI2Njc0NjA4MGQ5N2QzZjg5ZjdkMjIwZTIiLCJ3b3Jrc3BhY2VfaWQiOiI2NjAzMDhiZjM2ODcyOWJjMzczNzRhM2EiLCJpYXQiOjE3MTg5MDI5MTJ9.9IyJnTX4OWLxWCUyfN1M-umXszYwj8JCGlhdEQxnPZc"
    ACCOUNT_ID = "6682df74a47781b0590f56fe"
    BASE_URL = 'https://api.unified.to'
    OUTPUT_DIR = '/Users/yashvardhansinghranawat/Documents/HeronAI/backend-mainbu/modules/data_processing_scripts/quickbooks_unified/csv_files_healthscore_unified/' 

    unified_api = UnifiedAPI_Data_Fetch(API_KEY, BASE_URL, ACCOUNT_ID)
    dataframes = unified_api.fetch_all_data()

    for key, df in dataframes.items():
        print(f"\nDataFrame for {key}:")
        print(df.head())  # Print the first few rows of each dataframe

    # Save all dataframes to CSV files
    unified_api.save_dataframes_to_csv(OUTPUT_DIR)

    return dataframes

if __name__ == "__main__":
    main()