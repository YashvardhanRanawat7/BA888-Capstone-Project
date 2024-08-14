import requests
import json
import pandas as pd

class UnifiedAPI_Data_Fetch:
    def __init__(self, api_key, base_url, account_id):
        self.api_key = api_key
        self.base_url = base_url
        self.account_id = account_id
        self.valid_combinations = {
            "accounting": {
                "invoice": "Fetches invoice data",
                "transaction": "Fetches transaction data",
                "contact": "Fetches contact data",
            },
            "hris": {
                "employee": "Fetches employee data",
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
        print(f"Fetching data from URL: {url}")
        response = requests.get(url, headers=self.get_headers())
        if response.status_code == 200:
            data = response.json()
            print(f"{api.capitalize()} {endpoint.capitalize()} Response JSON:")
            print(json.dumps(data, indent=4))  # Print the response for debugging
            return data
        else:
            print(f"Error fetching {api}/{endpoint}: {response.status_code} - {response.text}")
            return None

    def save_to_dataframe(self, data, df_name):
        if data is None:
            print(f"No data to save for {df_name}")
            return

        if isinstance(data, list):
            # Normalize the JSON data
            df = pd.json_normalize(data)
            # Save to DataFrame
            self.dataframes[df_name] = df
            print(f"Data has been successfully saved to DataFrame with name {df_name}")
        else:
            print(f"Unexpected data format for {df_name}: {json.dumps(data, indent=4)}")

def main():
    API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySWQiOiI2Njc0NjA4MGQ5N2QzZjg5ZjdkMjIwZTIiLCJ3b3Jrc3BhY2VfaWQiOiI2NjAzMDhiZjM2ODcyOWJjMzczNzRhM2EiLCJpYXQiOjE3MTg5MDI5MTJ9.9IyJnTX4OWLxWCUyfN1M-umXszYwj8JCGlhdEQxnPZc"
    ACCOUNT_ID = "6682df74a47781b0590f56fe"
    BASE_URL = 'https://api.unified.to'

    unified_api = UnifiedAPI_Data_Fetch(API_KEY, BASE_URL, ACCOUNT_ID)

    for api, endpoints in unified_api.valid_combinations.items():
        for endpoint, description in endpoints.items():
            print(f"Fetching {api}/{endpoint}: {description}")
            data = unified_api.get_data(api, endpoint)
            df_name = f'{api}_{endpoint}_data'
            unified_api.save_to_dataframe(data, df_name)

    print("All data has been successfully saved to DataFrames.")

    # Access the DataFrame
    hris_employee_data = unified_api.dataframes['hris_employee_data']
    print(hris_employee_data.head())

if __name__ == "__main__":
    main()



