import os
import pandas as pd
from utils import get_chart_options, get_dataframe
from models.models import Graph, Statistics
from datetime import date, datetime, timedelta

class PLProcessor:
    def __init__(self, dashboard_id, df):
        self.dashboard_id = dashboard_id
        self.df = df
        self.graphs = []
        self.statistics = []

    def add_graph(self, title, graph_type, data, options):
        graph = Graph(
            dashboard_id=self.dashboard_id,
            title=title,
            graph_type=graph_type,
            data=data,
            options=options,
            parameters=None
        )
        self.graphs.append(graph)

    def add_statistics(self, title, stat_type, data):
        statistic = Statistics(
            dashboard_id=self.dashboard_id,
            title=title,
            stat_type=stat_type,
            data=data,
            parameters=None
        )
        self.statistics.append(statistic)

    def save_to_db(self):
        db.session.bulk_save_objects(self.graphs + self.statistics)
        db.session.commit()


    
class BalanceSheetStatisticsAR(PLProcessor):
    def process_data(self):
        try:
            AR = self.df['QueryResponse']['Account'][0]["CurrentBalance"]
            if pd.isna(AR):
                AR = 0
            else:
                AR = round(AR, 0)
            data={
                            "value": AR,
                            "evol": None,
                        }
            
            self.add_statistics("Current Accounts Receivable", "money", data)
        except Exception as e:
            print("Error in BalanceSheetStatisticsAR:", e)


class TotalARProcessor(PLProcessor):
    def process_data(self):
        try:
            end_date = pd.to_datetime(date.today())
            start_date = pd.to_datetime(date.today().replace(day=1) - pd.DateOffset(months=5))

            self.df['created_at_no_tz'] = pd.to_datetime(self.df['created_at']).dt.tz_localize(None)

            # Re-define the end date and start date for filtering, ensuring no timezone information
            start_date_no_tz = start_date.tz_localize(None)
            end_date_no_tz = end_date.tz_localize(None)

            # Re-filter the data to include only the last 6 months, now without timezone issues
            filtered_ar_data_no_tz = self.df[(self.df['created_at_no_tz'] >= start_date_no_tz) & 
                                                    (self.df['created_at_no_tz'] <= end_date_no_tz)]
            filtered_ar = filtered_ar_data_no_tz[filtered_ar_data_no_tz['type'] == 'ACCOUNTS_RECEIVABLE']
            # Ensure the monthly period index covers the last 6 months, even for months without income data
            period_index = pd.period_range(start=start_date_no_tz, end=end_date_no_tz, freq='M')

            # Group by month and sum balances, then reindex to ensure all last 6 months are covered
            monthly_ar_corrected = filtered_ar.groupby(filtered_ar['created_at_no_tz'].dt.to_period('M'))['balance'].sum()
            monthly_ar_corrected = monthly_ar_corrected.reindex(period_index, fill_value=0).reset_index()

            # Preparing the data for the expected output structure, considering all months in the period
            total_ar_corrected = monthly_ar_corrected['balance'].tolist()
            dates_str = monthly_ar_corrected['index'].astype(str).tolist()

            total_ar_corrected = [0 if pd.isna(item) else item for item in total_ar_corrected]
            # Structuring the output for the last 6 months
            line_chart_total_ar = [
                {
                    "name": "Accounts Receivable",
                    "data": total_ar_corrected
                }
            ]

            lineChartOptions = get_chart_options(chart_type="line")
            lineChartOptions["xaxis"]["categories"] = dates_str
            lineChartOptions["yaxis"]["title"] = {"text": "Accounts Receivable (USD)"}

            self.add_graph("Accounts  Receivable Over Time", "line chart", line_chart_total_ar, options=lineChartOptions)
        except Exception as e:
            print("Error in TotalARProcessor:", e)


class AgedReceivableProcessor(PLProcessor):
    def process_data(self):
        try:

            aging_sums_AR = {}
            ar_periods = ['Current', '1 - 30', '31 - 60', '61 - 90', '91 and over']
            columns_AR = self.df[-1]["Columns"]["Column"]
            # Iterate through columns to get the aging period titles
            for column in columns_AR:
                if column["ColTitle"] in ar_periods:
                    aging_period = column["ColTitle"]
                    if aging_period:
                        aging_sums_AR[aging_period] = [0 for i in range(len(self.df))]
            for j in range(len(self.df)):          
                rows_AR = self.df[j]["Rows"]["Row"]

                # Iterate through rows to accumulate sums for each aging period
                for row in rows_AR:
                    # Skip rows that are not vendor type (e.g., GrandTotal)
                    if "ColData" in row:
                        col_data = row["ColData"]
                        for i, col in enumerate(col_data):
                            # Check if the column corresponds to an aging period
                            if columns_AR[i]["ColTitle"] in ar_periods:
                                value = col["value"]
                                if value and value != "":
                                    # Convert value to float and add it to the corresponding sum
                                    aging_period = columns_AR[i]["ColTitle"]
                                    aging_sums_AR[aging_period][j] += float(value)




            aging_periods = list(aging_sums_AR.keys())
            barChartAccountsPayable = [
                {
                    "name": category,
                    "data": [0 if pd.isna(aging_sum) else aging_sum for aging_sum in aging_sums_AR[category]]
                } for category in aging_periods
            ]
            #date range corresponds to the last 6 months
            
            # Current date
            current_date = datetime.now()
            months = [(current_date - timedelta(days=30*i)).strftime('%Y-%m') for i in range(6)]
            date_range = sorted(months)
            print("barChartAccountsPayable", barChartAccountsPayable)
            print("date_range", date_range)
            barChartOptions = get_chart_options(chart_type="bar")
            barChartOptions["xaxis"]["categories"] = date_range
            barChartOptions["yaxis"]["title"] = {"text": "Amount (USD)"}

            self.add_graph("Aged Receivable Per Category Over Time", "bar chart", barChartAccountsPayable, options=barChartOptions)
        except Exception as e:
            print("Error in AgedReceivableProcessor:", e)

class AgedReceivablePerCompanyProcessor(PLProcessor):
    def process_data(self):
        try:
            AR_per_category = {}

      
            columns_AR = self.df[-1]["Columns"]["Column"]
            rows_AR = self.df[-1]["Rows"]["Row"]


            # Iterate through rows to accumulate sums for each aging period
            for row in rows_AR:
                # Skip rows that are not vendor type (e.g., GrandTotal)
                if "ColData" in row:
                    col_data = row["ColData"]
                    company_name = col_data[0]["value"]
                    AR_per_category[company_name] = 0
                    for i, col in enumerate(col_data):
                        # Check if the column corresponds to an aging period
                        if columns_AR[i]["ColTitle"] == "Total":
                            value = col["value"]
                            if value and value != "":
                                # Convert value to float and add it to the corresponding sum
                                AR_per_category[company_name] = float(value)


            pieChartDataAR = [
                {
                    "labels": list(AR_per_category.keys()),
                    "series": list(AR_per_category.values())
                }
            ]

            pieChartOptionsAR = get_chart_options(chart_type="pie")
            
            # count the amount of comapany with ar above a certain treshold
            treshold = 1000
            count = 0
            for value in AR_per_category.values():
                if value > treshold:
                    count += 1

            data={
                    "value": count,
                    "evol": None,
                }
            
            self.add_statistics("Number of Companies with AR above $1000", "number", data)
            
            ar_over_time = [0 for i in range(len(self.df))]
            for j in range(len(self.df)):
                columns_AR = self.df[j]["Columns"]["Column"]
                rows_AR = self.df[j]["Rows"]["Row"]
                if "ColData" in row:
                    col_data = row["ColData"]
                    for i, col in enumerate(col_data):
                        # Check if the column corresponds to an aging period
                        if columns_AR[i]["ColTitle"] == "Total":
                            value = col["value"]
                            if value and value != "":
                                # Convert value to float and add it to the corresponding sum
                                ar_over_time[j] += float(value)
            #date range corresponds to the last 6 months
            
            # Current date
            current_date = datetime.now()
            # Generate a list of the last 6 months including the current month
            months = [(current_date - timedelta(days=30*i)).strftime('%Y-%m') for i in range(6)]
            # Sort the months in ascending order
            date_range = sorted(months)

            barChartAROverTime = [  
                {
                    "name": "Total Aged Receivable",
                    "data": ar_over_time
                }
            ]
            print("barChartAROverTime", barChartAROverTime)
            print("date_range", date_range)
            barChartOptionsAR = get_chart_options(chart_type="bar")
            barChartOptionsAR["xaxis"]["categories"] = date_range
            barChartOptionsAR["yaxis"]["title"] = {"text": "Amount (USD)"}

        
            self.add_graph("Total Aged Receivable Over Time", "bar chart", barChartAROverTime, options=barChartOptionsAR)
            self.add_graph("Total Aged Receivable Per Company over Last Month", "pie chart", pieChartDataAR, options=pieChartOptionsAR)
        except Exception as e:
            print("Error in AgedReceivablePerCompanyProcessor:", e)



class TotalRevenueInvoiceProcessor(PLProcessor):
    def process_data(self):
        try:
            invoice_df = self.df
            # compute time to pay from created_at and due_at
            invoice_df['time_to_pay'] = pd.to_datetime(invoice_df['created_at']) - pd.to_datetime(invoice_df['due_at'])
            invoice_df['time_to_pay'] = invoice_df['time_to_pay'].dt.days
            # group by contact name and compute the average time to pay
            invoice_df = invoice_df.groupby('company_name').agg({'time_to_pay': 'mean'}).reset_index()
            invoice_df = invoice_df.sort_values(by='time_to_pay', ascending=False)
            barChartDataTimeToPay = [
                {
                    "name": "Time to Pay",
                    "data": invoice_df['time_to_pay'].tolist()
                }
            ]
            barChartOptionsTimeToPay = get_chart_options(chart_type="bar")
            barChartOptionsTimeToPay["xaxis"]["categories"] = invoice_df['company_name'].tolist()
            barChartOptionsTimeToPay["yaxis"]["title"] = {"text": "Days"}
            self.add_graph("Average Time to Pay Per Company", "bar chart", barChartDataTimeToPay, options=barChartOptionsTimeToPay)
        except Exception as e:
            print("Error in TotalRevenueInvoiceProcessor:", e)

def get_dashboard_qb_ar_unified(dashboard_id, df_path):
    try:
        bucket_name = os.environ.get('BUCKET_NAME')
        environment = os.environ.get('ENVIRONMENT')
        # bucket_name = "heron-db"
        # environment = "dev"
        sheet_name = None
        graphs=[]
        statistics=[]
        print("df_path", df_path)
        organization_name, app_name, connection_id = df_path.split("/")

        # df_path = df_path + ".json"
    
        df = get_dataframe(bucket_name, df_path, sheet_name=sheet_name, environment=environment, type_data="json") 
        print("df keys", df.keys())

        df_account = pd.DataFrame(df["account"])
        
        processors = [
            TotalARProcessor(dashboard_id, df_account),
        ]
      
        
        df_contact = pd.DataFrame(df["contact"])
        print("df_contact", df_contact.head())

        df_invoice =  pd.DataFrame(df["invoice"])

        # add the contact name from contact table to the invoice table using contact id
        try:
            df_invoice = pd.merge(df_invoice, df_contact, left_on='contact_id', right_on='id', how='left')
            print("df_invoice", df_invoice.columns)

        except Exception as e:
            print("Error in merge contact and invoice", e)
        df_payment = pd.DataFrame(df["payment"])

        try:
            df_payment = pd.merge(df_payment, df_invoice, left_on='invoice_id', right_on='id_x', how='left')
        except Exception as e:
            print("Error in merge payment and invoice", e)

        print("df_payment", df_payment.columns) 
        processors += [
                TotalRevenueInvoiceProcessor(dashboard_id, df_payment),
            ]
        
        
        
        df_ar = df["Accounts Receivable"]
        processors += [
                BalanceSheetStatisticsAR(dashboard_id, df_ar),
            ]
        
        df_ar = df["AgedReceivables"]

        processors += [
                AgedReceivableProcessor(dashboard_id, df_ar),
                AgedReceivablePerCompanyProcessor(dashboard_id, df_ar),
            ]


        for processor in processors:
            processor.process_data()
            graphs_processed = processor.graphs
            statistics_processed = processor.statistics
            for graph in graphs_processed:
                graphs.append(graph)
            for statistic in statistics_processed:
                statistics.append(statistic)

        print("Graphs : ", graphs)
        print("Statistics : ", statistics)
        return graphs, statistics
    except Exception as e:
        print("Error in get_dashboard_qb_ar_unified : ", e)
        return []
