import pandas as pd
from unified_data_fetch_healthscore import main as fetch_data

def perform_calculations(dataframes, arr_average):
    
    if 'accounting_invoice' in dataframes and 'hris_employee' in dataframes:
        df_invoice = dataframes['accounting_invoice']
        df_employee = dataframes['hris_employee']
        print(df_invoice.describe())  
        
        
        if 'total_amount' in df_invoice.columns:
            
            df_invoice_active = df_invoice[df_invoice['status'].isin(['paid', 'active'])]

            
            arr = df_invoice['total_amount'].sum()
            employee_count = len(df_employee)

            
            if employee_count == 0 or arr_average == 0:
                print("Employee count or ARR average is zero, cannot perform calculations.")
                return None

            
            arr_per_employee = arr / employee_count

            
            intermediary_calc = arr_per_employee / arr_average
            score = intermediary_calc * 15

            result = {
                "ARR": arr,
                "Employee Count": employee_count,
                "ARR per Employee": arr_per_employee,
                "Score": score
            }
            return result
        else:
            print("No 'total_amount' column in the 'accounting_invoice' dataframe.")
            return None
    else:
        print("'accounting_invoice' or 'hris_employee' dataframe not found.")
        return None

def main_processor(arr_average):
    dataframes = fetch_data()  
    result = perform_calculations(dataframes, arr_average)

    if result:
        print("\nCalculation Results:")
        for key, value in result.items():
            print(f"{key}: {value}")

if __name__ == "__main__":
    ARR_AVERAGE = 187500  
    main_processor(ARR_AVERAGE)
