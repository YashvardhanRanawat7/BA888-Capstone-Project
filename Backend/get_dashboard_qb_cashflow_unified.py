import os
import pandas as pd
from utils import get_chart_options, get_dataframe
from models.models import Graph, Statistics
from datetime import date

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

class CashFlowProcessor(PLProcessor):
    def process_data(self):
        try:

            df_outflow = self.df["Outflow"]
            df_inflow = self.df["Inflow"]

            end_date = pd.to_datetime(date.today())
            #as a start date take the first of the month 6 months ago
            start_date = pd.to_datetime(date.today().replace(day=1) - pd.DateOffset(months=5))

            df_outflow['created_at_no_tz'] = pd.to_datetime(df_outflow['created_at']).dt.tz_localize(None)

            # Re-define the end date and start date for filtering, ensuring no timezone information
            start_date_no_tz = start_date.tz_localize(None)
            end_date_no_tz = end_date.tz_localize(None)

            # Re-filter the data to include only the last 6 months, now without timezone issues
            filtered_payment_data_no_tz = df_outflow[(df_outflow['created_at_no_tz'] >= start_date_no_tz) & 
                                                    (df_outflow['created_at_no_tz'] <= end_date_no_tz)]
 
            period_index = pd.period_range(start=start_date_no_tz, end=end_date_no_tz, freq='M')

            # Group by month and sum balances, then reindex to ensure all last 6 months are covered
            monthly_payment_corrected = filtered_payment_data_no_tz.groupby(filtered_payment_data_no_tz['created_at_no_tz'].dt.to_period('M'))['total_amount'].sum()
            monthly_payment_corrected = monthly_payment_corrected.reindex(period_index, fill_value=0).reset_index()

            # Preparing the data for the expected output structure, considering all months in the period
            total_payment_corrected = monthly_payment_corrected['total_amount'].tolist()
            dates_str = monthly_payment_corrected['index'].astype(str).tolist()

            total_payment_corrected = [0 if pd.isna(item) else item for item in total_payment_corrected]
            
            line_chart_total_income = [
                        {
                            "name": "Total Payments Made",
                            "data": total_payment_corrected
                        }
                    ]

            lineChartOptions = get_chart_options(chart_type="line")
            lineChartOptions["xaxis"]["categories"] = dates_str
            lineChartOptions["yaxis"]["title"] = {"text": "Payments (USD)"}

            self.add_graph("Payments over Time", "line chart", line_chart_total_income, options=lineChartOptions)

            

            # Initialize a dictionary to store sums for each cash flow category
            cashflow = []
            net_income = []
            operating_adjustments = []
            ending_cash = []
            finance_activities = []
            # Iterate through columns to get the cash flow category titles
            for j in range(6):
                rows = df_inflow[j]["Rows"]["Row"]
                # Iterate through rows to accumulate sums for each cash flow category
                for row in rows:
                    # Skip rows that are not vendor type (e.g., GrandTotal)
                    if "group" in row:
                        if row["group"] == "CashIncrease":
                            col_data = row["Summary"]["ColData"]
                            for i, col in enumerate(col_data):
                                # Check if the column corresponds to a cash flow category
                                if i > 0:  # Exclude first column
                                    value = col["value"]
                                    if value and value != "":
                                        # Convert value to float and add it to the corresponding sum
                                        cashflow.append(value)

                    if "group" in row:
                        if row["group"] == "NetIncome":
                            col_data = row["Summary"]["ColData"]
                            for i, col in enumerate(col_data):
                                # Check if the column corresponds to a cash flow category
                                if i > 0:  # Exclude first column
                                    value = col["value"]
                                    if value and value != "":
                                        # Convert value to float and add it to the corresponding sum
                                        net_income.append(value)
                    if "group" in row:
                        if row["group"] == "OperatingAdjustments":
                            col_data = row["Summary"]["ColData"]
                            for i, col in enumerate(col_data):
                                # Check if the column corresponds to a cash flow category
                                if i > 0:  # Exclude first column
                                    value = col["value"]
                                    if value and value != "":
                                        # Convert value to float and add it to the corresponding sum
                                        operating_adjustments.append(value)
                                    
                    if "group" in row:
                        if row["group"] == "EndingCash":
                            col_data = row["Summary"]["ColData"]
                            for i, col in enumerate(col_data):
                                # Check if the column corresponds to a cash flow category
                                if i > 0:  # Exclude first column
                                    value = col["value"]
                                    if value and value != "":
                                        # Convert value to float and add it to the corresponding sum
                                        ending_cash.append(value)
                    if "group" in row:
                        if row["group"] == "FinancingActivities":
                            col_data = row["Summary"]["ColData"]
                            for i, col in enumerate(col_data):
                                # Check if the column corresponds to a cash flow category
                                if i > 0:  # Exclude first column
                                    value = col["value"]
                                    if value and value != "":
                                        # Convert value to float and add it to the corresponding sum
                                        finance_activities.append(value)
                if len(cashflow) < j+1:
                    cashflow.append(0)
                if len(net_income) < j+1:
                    net_income.append(0)
                if len(operating_adjustments) < j+1:
                    operating_adjustments.append(0)
                if len(ending_cash) < j+1:
                    ending_cash.append(0)
                if len(finance_activities) < j+1:
                    finance_activities.append(0)
            total_cashflow_values = [0 if pd.isna(item) else item for item in cashflow]
            barChartCashFlow = [
                {
                    "name": "Total Cashflow",
                    "data": total_cashflow_values
                }
            ]

            net_op_cashflow_values = [net_cashflow - operating_cashflow for net_cashflow, operating_cashflow in zip(net_income, operating_adjustments)]
            net_op_cashflow_values = [0 if pd.isna(item) else item for item in net_op_cashflow_values]
            barChartNetOpCashFlow = [
                {
                    "name": "Net Operating Cashflow",
                    "data": net_op_cashflow_values
                }
            ]

            ending_cash_values = [0 if pd.isna(item) else item for item in ending_cash]
            barChartEndingCash = [
                {
                    "name": "Ending Cash",
                    "data": ending_cash_values
                }
            ]

            finance_activities_values = [0 if pd.isna(item) else item for item in finance_activities]
            barChartFinanceActivities = [
                {
                    "name": "Finance Activities",
                    "data": finance_activities_values
                }
            ]

            barChartOptions = get_chart_options(chart_type="bar")
            barChartOptions["xaxis"]["categories"] = dates_str
            barChartOptions["yaxis"]["title"] = {"text": "Amount (USD)"}

            self.add_graph("Cash Flow", "bar chart", barChartCashFlow, options=barChartOptions)
            self.add_graph("Net Operating Cash Flow", "bar chart", barChartNetOpCashFlow, options=barChartOptions)
            self.add_graph("Ending Cash", "bar chart", barChartEndingCash, options=barChartOptions)
            self.add_graph("Finance Activities", "bar chart", barChartFinanceActivities, options=barChartOptions)



        except Exception as e:
            print("Error in CashflowProcessor:", e)

def get_dashboard_qb_cashflow_unified(dashboard_id, df_path):
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



        df_outflow =  pd.DataFrame(df["payment"])       
        df_inflow = df["CashFlow"]
   
        df_cashflow = {"Inflow": df_inflow, "Outflow": df_outflow}
        processors = [
                CashFlowProcessor(dashboard_id, df_cashflow),
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
        print("Error in get_dashboard_qb_pl_unified : ", e)
        return []
