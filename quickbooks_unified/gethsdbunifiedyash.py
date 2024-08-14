import os
import json
import pandas as pd
from utils import get_data_unified
from modules.data_processing_scripts.get_dashboard_qb_api import get_dashboard_data_quickbooks_api

# Set environment variables
os.environ['ENVIRONMENT'] = 'local'
os.chdir("/Users/yashvardhansinghranawat/Desktop/HeronHealthScore/backend-mainbu")
print(os.getcwd())

# Variables (some are hard-coded for local testing)
authorization_token ="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySWQiOiI2Njc0NjA4MGQ5N2QzZjg5ZjdkMjIwZTIiLCJ3b3Jrc3BhY2VfaWQiOiI2NjAzMDhiZjM2ODcyOWJjMzczNzRhM2EiLCJpYXQiOjE3MTg5MDI5MTJ9.9IyJnTX4OWLxWCUyfN1M-umXszYwj8JCGlhdEQxnPZc"
app_name = 'Quickbooks'
connection_id = '66842173f171e7968e77d58e'
#connection_id = ''
environment = 'local'
bucket_name = 'heron-db'
organizationname = 'Test'

# Fetch data from Unified
data_json = get_data_unified(
    app_name,
    authorization_token,
    connection_id,
    passthrough=True
)

print(data_json.keys())
file_name = f"{organizationname}/{app_name}/{str(connection_id)}.json"

# Write data to local file if in local environment
if environment == 'local':
    local_path = "public/json/"
    df_path = local_path + file_name
    with open(df_path, "w") as f:
        json.dump(data_json, f, indent=4)

# Process dashboard data
get_dashboard_data_quickbooks_api(413, file_name)