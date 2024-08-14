import os
import pandas as pd
from utils import get_chart_options, get_dataframe,get_data_unified,create_dataframe
from models.models import Graph, Statistics
from datetime import date, datetime, timedelta
import json


### Hard  coding certain variables but when script is integrated we can remove this part
authorization_token ="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySWQiOiI2Njc0NjA4MGQ5N2QzZjg5ZjdkMjIwZTIiLCJ3b3Jrc3BhY2VfaWQiOiI2NjAzMDhiZjM2ODcyOWJjMzczNzRhM2EiLCJpYXQiOjE3MTg5MDI5MTJ9.9IyJnTX4OWLxWCUyfN1M-umXszYwj8JCGlhdEQxnPZc"
app_name = 'Quickbooks'
connection_api_id = '66939d0b247ea2a8fd17a108'
connection_id = '66939d0b247ea2a8fd17a108'
environment = 'local'
bucket_name = 'heron-db'
organizationname= 'Test' #organization.name

#Fetching Data from Unified
data_json = get_data_unified(
    app_name,
    authorization_token,
    connection_api_id,
    passthrough=True
)

print("data json keys: ", data_json.keys())

### Some variables are hard coded
if environment == 'local':
    file_path = "/Users/yashvardhansinghranawat/Documents/HeronAI/backend-mainbu/modules/data_processing_scripts/quickbooks_unified/csv_files_healthscore_unified/healthscore_unified.json"
    # Write the data_json to the file
    with open(file_path, "w") as f:
        json.dump(data_json, f, indent=4)


#else:
#    write_json_on_s3(bucket_name, f"{organization.name}/{app_name}/{connection_id}.json", data_json)

# Assuming data_json, environment, organization, app_name, connection_id, and bucket_name are defined

file_name = f"{organizationname}/{app_name}/{str(connection_id)}.xlsx"

# Preparing the DataFrames
dfs = {}
for category in data_json.keys():
    df = pd.DataFrame(data_json[category])
    sheet_name = category.replace("/", "")
    dfs[sheet_name] = df

    # Save each DataFrame to a CSV file
    csv_file_path = f"/Users/yashvardhansinghranawat/Documents/HeronAI/backend-mainbu/modules/data_processing_scripts/quickbooks_unified/csv_files_healthscore_unified/{sheet_name}.csv"
    df.to_csv(csv_file_path, index=False)
    print(f"Saved {sheet_name} to {csv_file_path}")

# Create the Excel file with multiple sheets
#create_dataframe(bucket_name, dfs, file_name, sheet_name=None, environment=environment, type='excel')