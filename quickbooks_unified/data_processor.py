# data_processor.py
import pandas as pd
#backend-mainbu.modules.data_processing_scripts.quickbooks_unified.
from unified_data_fetch_healthscore import UnifiedAPI_Data_Fetch, main

def perform_calculations(dataframes):
    # Example calculation: Sum of invoice amounts
    if 'hris_employee' in dataframes:
        df_invoice = dataframes['hris_employee']
        print("\nFirst few rows of the 'accounting_invoice' dataframe:")
        print(df_invoice.info())


def main_processor():
    dataframes = main()  # Fetch data using the function from data_fetcher.py
    perform_calculations(dataframes)

if __name__ == "__main__":
    main_processor()