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

class TotalRevenueInvoiceProcessor(PLProcessor):
    def process_data(self):
        try:
            invoice_df = self.df["Invoice"]
            # Convert created_at to datetime format in the invoice data
            invoice_df['due_at'] = pd.to_datetime(invoice_df['due_at'])

            # Extract year and month from created_at
            invoice_df['year_month'] = invoice_df['due_at'].dt.to_period('M')

            # Sum total_amount grouped by year and month
            monthly_revenue_invoice = invoice_df.groupby('year_month')['total_amount'].sum().reset_index()
            monthly_revenue_invoice.sort_values(by='year_month', inplace=True)
            dates = monthly_revenue_invoice['year_month'].astype(str)
        
            
            line_chart_total_income = [
                {
                    "name": "Total Income",
                    "data": monthly_revenue_invoice['total_amount'].tolist()
                }
            ]

            lineChartOptions = get_chart_options(chart_type="line")
            lineChartOptions["xaxis"]["categories"] = dates
            lineChartOptions["yaxis"]["title"] = {"text": "Total Revenue (USD)"}

            self.add_graph("Total Revenue from Invoices Over Time", "line chart", line_chart_total_income, options=lineChartOptions)
        except Exception as e:
            print("Error in TotalRevenueInvoiceProcessor:", e)


class TotalRevenuePLProcessor(PLProcessor):
    def process_data(self):
        try:

            revenue = []
            expenditures = []

            for i in range(6):
                # print("Rows:", self.df[i])
                if "Row" not in self.df[i]["Rows"]:
                    revenue.append(0)
                    expenditures.append(0)
                    continue
                for section in self.df[i]["Rows"]["Row"]:
                    if "group" not in section:
                        total_net_revenue = 0

                        continue

                    elif section["group"] == "NetIncome":
                        # print("section:", section["Summary"]["ColData"])
                        # Summarize net revenue
                        if len(section["Summary"]["ColData"]) > 1 and section["Summary"]["ColData"][1]["value"]:
                            total_net_revenue = float(section["Summary"]["ColData"][1]["value"])
                        else:
                            total_net_revenue = 0
                revenue.append(round(total_net_revenue, 0))

                    

            current_date = datetime.now()
            months = [(current_date - timedelta(days=30*i)).strftime('%Y-%m') for i in range(6)]
            date_range = sorted(months)
            # replace any NaN values with 0 in the revenue and expenditures lists
            revenue = [0 if pd.isna(item) else item for item in revenue]
 

            # Structuring the output for the last 6 months
            barChartDataRevenueExpenses = [
                {
                    "name": "Revenue",
                    "data": revenue,
                },
            ]

            barChartOptions = get_chart_options(chart_type="bar")
            barChartOptions["xaxis"]["categories"] = dates_str
            barChartOptions["yaxis"]["title"] = {"text": "Total Income (USD)"}

            self.add_graph("Net Income Over Time", "line chart", barChartDataRevenueExpenses, options=barChartOptions)
        except Exception as e:
            print("Error in TotalRevenuePLProcessor:", e)



class TotalPLProcessor(PLProcessor):
    def process_data(self):
        try:
            last_6_months = []
            revenue = []
            expenditures = []
            net_cash_flow = []
            fundraising_revenue = []
            fundraising_expenditures = []
            for i in range(6):
                # print("Rows:", self.df[i])
                if "Row" not in self.df[i]["Rows"]:
                    revenue.append(0)
                    expenditures.append(0)
                    continue
                for section in self.df[i]["Rows"]["Row"]:
                    if "group" not in section:
                        total_net_revenue = 0
                        total_expenditures = 0
                        continue
                    if section["group"] == "Expenses":
                        # print("section:", section["Summary"]["ColData"])
                        # Summarize total expenditures
                        # Check if section["Summary"]["ColData"][1] exists
                        if len(section["Summary"]["ColData"]) > 1 and section["Summary"]["ColData"][1]["value"]:
                            total_expenditures = float(section["Summary"]["ColData"][1]["value"])
                        else :
                            total_expenditures = 0

                    elif section["group"] == "Income":
                        # print("section:", section["Summary"]["ColData"])
                        # Summarize net revenue
                        if len(section["Summary"]["ColData"]) > 1 and section["Summary"]["ColData"][1]["value"]:
                            total_net_revenue = float(section["Summary"]["ColData"][1]["value"])
                        else:
                            total_net_revenue = 0
                revenue.append(round(total_net_revenue, 0))
                expenditures.append(round(total_expenditures, 0))
                # Calculate net cash flow
                net_cash_flow_item = total_net_revenue - total_expenditures
                net_cash_flow.append(round(net_cash_flow_item, 0))
                    

            current_date = datetime.now()
            months = [(current_date - timedelta(days=30*i)).strftime('%Y-%m') for i in range(6)]
            dates_str = sorted(months)

            # replace any NaN values with 0 in the revenue and expenditures lists
            revenue = [0 if pd.isna(item) else item for item in revenue]
            expenditures = [0 if pd.isna(item) else item for item in expenditures]
            net_cash_flow = [0 if pd.isna(item) else item for item in net_cash_flow]

            total_revenue = sum(revenue)
            total_expenditures = sum(expenditures)
            if total_revenue == 0:
                profit_margin = 0
            else:
                profit_margin = round((total_revenue - total_expenditures) / total_revenue * 100, 2)

            # Structuring the output for the last 6 months
            barChartDataRevenueExpenses = [
                {
                    "name": "Revenue",
                    "data": revenue,
                },
                {
                    "name": "Expenditures",
                    # take the negative of the expenditures to display it as a positive value
                    "data": [-item for item in expenditures],
                }
            ]

            barChartDataExpenses = [
                {
                    "name": "Expenditures",
                    # take the negative of the expenditures to display it as a positive value
                    "data": [-item for item in expenditures],
                }
            ]

            barChartDataRevenue = [
                {
                    "name": "Revenue",
                    "data": revenue,
                },
            ]

            barChartNetCashFlow = [
                {
                    "name": "Net Cash Flow",
                    "data": net_cash_flow,
                }
            ]
            barChartOptionsRevenueExpenses = get_chart_options(chart_type="bar")
            barChartOptionsRevenueExpenses["xaxis"]["categories"] = dates_str
            barChartOptionsRevenueExpenses["yaxis"]["title"] = {"text": "Total Income (USD)"}
            barChartOptionsRevenueExpenses["chart"] = {
                    "stacked": False,
                    "type": 'bar',
                    "toolbar": {
                    "show": False,
                    },
                  }

            barChartOptionsNetCashFlow = get_chart_options(chart_type="bar")
            barChartOptionsNetCashFlow["xaxis"]["categories"] = dates_str
            barChartOptionsNetCashFlow["yaxis"]["title"] = {"text": "Gross Profit (USD)"}
           

            barChartOptionsExpenses = get_chart_options(chart_type="bar")
            barChartOptionsExpenses["xaxis"]["categories"] = dates_str
            barChartOptionsExpenses["yaxis"]["title"] = {"text": "Operating Expenses (USD)"}

            barChartOptions = get_chart_options(chart_type="bar")
            barChartOptions["xaxis"]["categories"] = dates_str
            barChartOptions["yaxis"]["title"] = {"text": "Total Income (USD)"}

            self.add_graph("Income Over Time", "line chart", barChartDataRevenue, options=barChartOptions)
            self.add_graph("Operating Expenses Over Time", "line chart", barChartDataExpenses, options=barChartOptionsExpenses)
            self.add_graph("Income vs Expenditures Over Time", "line chart", barChartDataRevenueExpenses, options=barChartOptionsRevenueExpenses)
            self.add_graph("Gross Profit Over Time", "line chart", barChartNetCashFlow, options=barChartOptionsNetCashFlow)
            self.add_statistics("Profit Margin", "money", {"value": profit_margin, "evol": None})
        except Exception as e:
            print("Error in TotalPLProcessor:", e)



class ExpenseRevenueBySourceProcessor(PLProcessor):
    def process_data(self):
        try:
            income_sources=[]
            expenses_sources=[]
            for i in range(6):
                # print("Rows:", self.df[i])
                if "Row" not in self.df[i]["Rows"]:
                    continue
                for section in self.df[i]["Rows"]["Row"]:
                    # print("section:", section)
                    # print("section keys:", section.keys())
                    if "group" not in section:
                        continue
                    if section["group"] == "Income" or section["group"] == "NetIncome":

                        # Process income sources
                        income_rows = section.get("Rows", {}).get("Row", [])
                        # print("income_rows:", income_rows)
                        for row in income_rows:
                            if "ColData" in row:
                                source_name = row["ColData"][0].get("value", "Unknown")
                                source_amount = float(row["ColData"][1].get("value", 0))
                                income_sources.append((source_name, source_amount))
                    
                    elif section["group"] == "Expenses":

                        # Process income sources
                        expenses_rows = section.get("Rows", {}).get("Row", [])
                        # print("income_rows:", expenses_rows)
                        for row in expenses_rows:
                            if "ColData" in row:
                                source_name = row["ColData"][0].get("value", "Unknown")
                                source_amount = float(row["ColData"][1].get("value", 0))
                                expenses_sources.append((source_name, source_amount))

            # Sort and get top 5 income sources
            top_income_sources = sorted(income_sources, key=lambda x: x[1], reverse=True)[:5]
            print("top_income_sources:", top_income_sources)

            top_expenses_sources = sorted(expenses_sources, key=lambda x: x[1], reverse=True)[:5]
            print("top_expenses_sources:", top_expenses_sources)

            # Structuring the output for the last 6 months
            pieChartDataIncome = [
                {
                    "labels": [item[0] for item in top_income_sources],
                    "series": [0 if pd.isna(item[1]) else round(item[1], 0) for item in top_income_sources],
                }
            ]
        
            pieChartDataExpenses = [
                    {
                        "labels": [item[0] for item in top_expenses_sources],
                        "series": [0 if pd.isna(item[1]) else round(item[1], 0) for item in top_expenses_sources],
                    }
                ]

            pieChartOptions = get_chart_options(chart_type="pie")

            self.add_graph("Main Income Sources", "pie chart", pieChartDataIncome, options=pieChartOptions)
            self.add_graph("Main Expenses Sources", "pie chart", pieChartDataExpenses, options=pieChartOptions)
        except Exception as e:
            print("Error in BalanceSheetTotalLiabilitiesProcessor:", e)



    
class BalanceSheetStatisticsAP(PLProcessor):
    def process_data(self):
        try:
            AP = self.df['QueryResponse']['Account'][0]["CurrentBalance"]
            if pd.isna(AP):
                AP = 0
            else:
                AP = round(AP, 0)
            data={
                            "value": AP,
                            "evol": None,
                        }
            
            self.add_statistics("Current Accounts Receivable", "money", data)
        except Exception as e:
            print("Error in BalanceSheetStatisticsAP:", e)

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
            
            self.add_statistics("Current Accounts Payable", "money", data)
        except Exception as e:
            print("Error in BalanceSheetStatisticsAR:", e)

class BalanceSheetStatisticsExpenses(PLProcessor):
    def process_data(self):
        try:
            expenses = sum([self.df['QueryResponse']['Account'][i]["CurrentBalance"] for i in range(0, len(self.df['QueryResponse']['Account']))])
            if pd.isna(expenses):
                expenses = 0
            else:
                expenses = round(expenses, 0)  
            data={
                            "value": expenses,
                            "evol": None,
                        }
            
            self.add_statistics("Current Expenses", "money", data)
        except Exception as e:
            print("Error in BalanceSheetStatisticsExpenses:", e)

class BalanceSheetStatisticsIncome(PLProcessor):
    def process_data(self):
        try:
            income = sum([self.df['QueryResponse']['Account'][i]["CurrentBalance"] for i in range(0, len(self.df['QueryResponse']['Account']))])
            if pd.isna(income):
                income = 0
            else:
                income = round(income, 0)
            data={
                            "value": income,
                            "evol": None,
                        }
            
            self.add_statistics("Current Income", "money", data)
        except Exception as e:
            print("Error in BalanceSheetStatisticsIncome:", e)

class BalanceSheetStatisticsBankBalance(PLProcessor): 
    def process_data(self):
        try:
            BankBalance = sum([self.df['QueryResponse']['Account'][i]["CurrentBalance"] for i in range(0, len(self.df['QueryResponse']['Account']))])
            if pd.isna(BankBalance):
                BankBalance = 0
            else:
                BankBalance = round(BankBalance, 0)
            data={
                            "value": BankBalance,
                            "evol": None,
                        }
            
            self.add_statistics("Bank Balance", "money", data)
        except Exception as e:
            print("Error in BalanceSheetStatisticsBankBalance:", e)


class BalanceSheetStatisticsTotalAssets(PLProcessor):
    def process_data(self):
        try:
            if not self.df['QueryResponse']:
                TotalAssets = 0
            else:
                TotalAssets = sum([self.df['QueryResponse']['Account'][i]["CurrentBalance"] for i in range(0, len(self.df['QueryResponse']['Account']))])
            if pd.isna(TotalAssets):
                TotalAssets = 0
            else:
                TotalAssets = round(TotalAssets, 0)
            data={
                            "value": TotalAssets,
                            "evol": None,
                        }
            
            self.add_statistics("Total Assets", "money", data)
        except Exception as e:
            print("Error in BalanceSheetStatisticsTotalAssets:", e)

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

class TotalAPProcessor(PLProcessor):
    def process_data(self):
        try:
            end_date = pd.to_datetime(date.today())
            start_date = pd.to_datetime(date.today().replace(day=1) - pd.DateOffset(months=5))

            self.df['created_at_no_tz'] = pd.to_datetime(self.df['created_at']).dt.tz_localize(None)

            # Re-define the end date and start date for filtering, ensuring no timezone information
            start_date_no_tz = start_date.tz_localize(None)
            end_date_no_tz = end_date.tz_localize(None)

            # Re-filter the data to include only the last 6 months, now without timezone issues
            filtered_ap_data_no_tz = self.df[(self.df['created_at_no_tz'] >= start_date_no_tz) & 
                                                    (self.df['created_at_no_tz'] <= end_date_no_tz)]
            filtered_ap = filtered_ap_data_no_tz[filtered_ap_data_no_tz['type'] == 'ACCOUNTS_PAYABLE']
            # Ensure the monthly period index covers the last 6 months, even for months without income data
            period_index = pd.period_range(start=start_date_no_tz, end=end_date_no_tz, freq='M')

            # Group by month and sum balances, then reindex to ensure all last 6 months are covered
            monthly_ap_corrected = filtered_ap.groupby(filtered_ap['created_at_no_tz'].dt.to_period('M'))['balance'].sum()
            monthly_ap_corrected = monthly_ap_corrected.reindex(period_index, fill_value=0).reset_index()

            # Preparing the data for the expected output structure, considering all months in the period
            total_ap_corrected = monthly_ap_corrected['balance'].tolist()
            dates_str = monthly_ap_corrected['index'].astype(str).tolist()
            
            total_ap_corrected = [0 if pd.isna(item) else item for item in total_ap_corrected]
            # Structuring the output for the last 6 months
            line_chart_total_ap = [
                {
                    "name": "Accounts Payable",
                    "data": total_ap_corrected
                }
            ]

            lineChartOptions = get_chart_options(chart_type="line")
            lineChartOptions["xaxis"]["categories"] = dates_str
            lineChartOptions["yaxis"]["title"] = {"text": "Accounts Payable (USD)"}

            self.add_graph("Accounts Payable Over Time", "line chart", line_chart_total_ap, options=lineChartOptions)
        except Exception as e:
            print("Error in TotalAPProcessor:", e)
class TotalFixedAssetsProcessor(PLProcessor):
    def process_data(self):
        try:
            end_date = pd.to_datetime(date.today())
            start_date = pd.to_datetime(date.today().replace(day=1) - pd.DateOffset(months=5))

            self.df['created_at_no_tz'] = pd.to_datetime(self.df['created_at']).dt.tz_localize(None)

            # Re-define the end date and start date for filtering, ensuring no timezone information
            start_date_no_tz = start_date.tz_localize(None)
            end_date_no_tz = end_date.tz_localize(None)

            # Re-filter the data to include only the last 6 months, now without timezone issues
            filtered_ap_data_no_tz = self.df[(self.df['created_at_no_tz'] >= start_date_no_tz) & 
                                                    (self.df['created_at_no_tz'] <= end_date_no_tz)]
            filtered_ap = filtered_ap_data_no_tz[filtered_ap_data_no_tz['type'] == 'FIXED_ASSET']
            # Ensure the monthly period index covers the last 6 months, even for months without income data
            period_index = pd.period_range(start=start_date_no_tz, end=end_date_no_tz, freq='M')

            # Group by month and sum balances, then reindex to ensure all last 6 months are covered
            monthly_ap_corrected = filtered_ap.groupby(filtered_ap['created_at_no_tz'].dt.to_period('M'))['balance'].sum()
            monthly_ap_corrected = monthly_ap_corrected.reindex(period_index, fill_value=0).reset_index()

            # Preparing the data for the expected output structure, considering all months in the period
            total_ap_corrected = monthly_ap_corrected['balance'].tolist()
            dates_str = monthly_ap_corrected['index'].astype(str).tolist()

            total_ap_corrected = [0 if pd.isna(item) else item for item in total_ap_corrected]

            # Structuring the output for the last 6 months
            line_chart_total_ap = [
                {
                    "name": "Fixed Assets",
                    "data": total_ap_corrected
                }
            ]

            lineChartOptions = get_chart_options(chart_type="line")
            lineChartOptions["xaxis"]["categories"] = dates_str
            lineChartOptions["yaxis"]["title"] = {"text": "Fixed Assets (USD)"}

            self.add_graph("Fixed Assets Over Time", "line chart", line_chart_total_ap, options=lineChartOptions)
        except Exception as e:
            print("Error in TotalFixedAssetsProcessor:", e)

class TotalLiabilityProcessor(PLProcessor):
    def process_data(self):
        try:
            end_date = pd.to_datetime(date.today())
            start_date = pd.to_datetime(date.today().replace(day=1) - pd.DateOffset(months=5))

            self.df['created_at_no_tz'] = pd.to_datetime(self.df['created_at']).dt.tz_localize(None)

            # Re-define the end date and start date for filtering, ensuring no timezone information
            start_date_no_tz = start_date.tz_localize(None)
            end_date_no_tz = end_date.tz_localize(None)

            # Re-filter the data to include only the last 6 months, now without timezone issues
            filtered_ap_data_no_tz = self.df[(self.df['created_at_no_tz'] >= start_date_no_tz) & 
                                                    (self.df['created_at_no_tz'] <= end_date_no_tz)]
            filtered_ap = filtered_ap_data_no_tz[filtered_ap_data_no_tz['type'] == 'LIABILITY']
            # Ensure the monthly period index covers the last 6 months, even for months without income data
            period_index = pd.period_range(start=start_date_no_tz, end=end_date_no_tz, freq='M')

            # Group by month and sum balances, then reindex to ensure all last 6 months are covered
            monthly_ap_corrected = filtered_ap.groupby(filtered_ap['created_at_no_tz'].dt.to_period('M'))['balance'].sum()
            monthly_ap_corrected = monthly_ap_corrected.reindex(period_index, fill_value=0).reset_index()

            # Preparing the data for the expected output structure, considering all months in the period
            total_ap_corrected = monthly_ap_corrected['balance'].tolist()
            dates_str = monthly_ap_corrected['index'].astype(str).tolist()

            total_ap_corrected = [0 if pd.isna(item) else item for item in total_ap_corrected]

            # Structuring the output for the last 6 months
            line_chart_total_ap = [
                {
                    "name": "Liability",
                    "data": total_ap_corrected
                }
            ]

            lineChartOptions = get_chart_options(chart_type="line")
            lineChartOptions["xaxis"]["categories"] = dates_str
            lineChartOptions["yaxis"]["title"] = {"text": "Liability (USD)"}

            self.add_graph("Liability Over Time", "line chart", line_chart_total_ap, options=lineChartOptions)
        except Exception as e:
            print("Error in TotalLiabilityProcessor:", e)

class TotalExpenseProcessor(PLProcessor):
    def process_data(self):
        try:
            end_date = pd.to_datetime(date.today())
            start_date = pd.to_datetime(date.today().replace(day=1) - pd.DateOffset(months=5))

            self.df['created_at_no_tz'] = pd.to_datetime(self.df['created_at']).dt.tz_localize(None)

            # Re-define the end date and start date for filtering, ensuring no timezone information
            start_date_no_tz = start_date.tz_localize(None)
            end_date_no_tz = end_date.tz_localize(None)

            # Re-filter the data to include only the last 6 months, now without timezone issues
            filtered_expense_data_no_tz = self.df[(self.df['created_at_no_tz'] >= start_date_no_tz) & 
                                                    (self.df['created_at_no_tz'] <= end_date_no_tz)]
            filtered_expense = filtered_expense_data_no_tz[filtered_expense_data_no_tz['type'] == 'EXPENSE']
            # Ensure the monthly period index covers the last 6 months, even for months without income data
            period_index = pd.period_range(start=start_date_no_tz, end=end_date_no_tz, freq='M')

            # Group by month and sum balances, then reindex to ensure all last 6 months are covered
            monthly_income_corrected = filtered_expense.groupby(filtered_expense['created_at_no_tz'].dt.to_period('M'))['balance'].sum()
            monthly_income_corrected = monthly_income_corrected.reindex(period_index, fill_value=0).reset_index()

            # Preparing the data for the expected output structure, considering all months in the period
            total_expense_corrected = monthly_income_corrected['balance'].tolist()
            dates_str = monthly_income_corrected['index'].astype(str).tolist()
            
            total_expense_corrected = [0 if pd.isna(item) else item for item in total_expense_corrected]
            # Structuring the output for the last 6 months
            line_chart_total_expense = [
                {
                    "name": "Total Expense",
                    "data": total_expense_corrected
                }
            ]
            lineChartOptions = get_chart_options(chart_type="line")
            lineChartOptions["xaxis"]["categories"] = dates_str
            lineChartOptions["yaxis"]["title"] = {"text": "Total Expenses (USD)"}
    

            self.add_graph("Total Expense Over Time", "line chart", line_chart_total_expense, options=lineChartOptions)
        except Exception as e:
            print("Error in TotalExpenseProcessor:", e)
class NetProfitProcessor(PLProcessor):
    def process_data(self):
        try:
            end_date = pd.to_datetime(date.today())
            start_date = pd.to_datetime(date.today().replace(day=1) - pd.DateOffset(months=5))

            self.df['created_at_no_tz'] = pd.to_datetime(self.df['created_at']).dt.tz_localize(None)

            # Re-define the end date and start date for filtering, ensuring no timezone information
            start_date_no_tz = start_date.tz_localize(None)
            end_date_no_tz = end_date.tz_localize(None)

            # Re-filter the data to include only the last 6 months, now without timezone issues
            filtered_expense_data_no_tz = self.df[(self.df['created_at_no_tz'] >= start_date_no_tz) & 
                                                    (self.df['created_at_no_tz'] <= end_date_no_tz)]
            filtered_income = filtered_expense_data_no_tz[filtered_expense_data_no_tz['type'] == 'ACCOUNTS_RECEIVABLE']
            filtered_expense = filtered_expense_data_no_tz[filtered_expense_data_no_tz['type'] == 'EXPENSE']
            # Ensure the monthly period index covers the last 6 months, even for months without income data
            period_index = pd.period_range(start=start_date_no_tz, end=end_date_no_tz, freq='M')

            # Group by month and sum balances, then reindex to ensure all last 6 months are covered
            monthly_income = filtered_income.groupby(filtered_income['created_at_no_tz'].dt.to_period('M'))['balance'].sum()
            monthly_expense = filtered_expense.groupby(filtered_expense['created_at_no_tz'].dt.to_period('M'))['balance'].sum()
            monthly_profit = monthly_income - monthly_expense
            monthly_profit = monthly_profit.reindex(period_index, fill_value=0).reset_index()

            # Preparing the data for the expected output structure, considering all months in the period
            total_profit_corrected = monthly_profit['balance'].tolist()
            dates_str = monthly_profit['index'].astype(str).tolist()

            total_profit_corrected = [0 if pd.isna(item) else item for item in total_profit_corrected]

            # Structuring the output for the last 6 months
            line_chart_net_profit = [
                {
                    "name": "Total Expense",
                    "data": total_profit_corrected
                }
            ]

            lineChartOptions = get_chart_options(chart_type="line")
            lineChartOptions["xaxis"]["categories"] = dates_str
            lineChartOptions["yaxis"]["title"] = {"text": "Net Profit (USD)"}
        

            self.add_graph("Net Profit Over Time", "line chart", line_chart_net_profit, options=lineChartOptions)
        except Exception as e:
            print("Error in NetProfitProcessor:", e)
class IncomeCategoryProcessor(PLProcessor):
    def process_data(self):
        try:
            end_date = pd.to_datetime(date.today())
            start_date = pd.to_datetime(date.today().replace(day=1) - pd.DateOffset(months=5))
            # Re-define the end date and start date for filtering, ensuring no timezone information
            start_date_no_tz = start_date.tz_localize(None)
            end_date_no_tz = end_date.tz_localize(None)

            # Filter the dataset for entries with type 'REVENUE' and consider only the last 6 months of data
            revenue_data = self.df[(self.df['type'] == 'REVENUE') & 
                                (pd.to_datetime(self.df['created_at']).dt.tz_localize(None) >= start_date_no_tz) &
                                (pd.to_datetime(self.df['created_at']).dt.tz_localize(None) <= end_date_no_tz)]
            
            # Aggregate the total amount per income category using the 'name' as the category label
            print("revenue_data", revenue_data[['name', 'balance']])
            income_category_breakdown = revenue_data.groupby('name')['balance'].sum().reset_index()

            # Prepare the labels and series for the pie chart data structure
            labels = income_category_breakdown['name'].tolist()
            series = income_category_breakdown['balance'].tolist()
            print("labels", labels)
            print("series", series)
            series = [0 if pd.isna(item) else item for item in series]
            # Structuring the output for the income category breakdown
            pie_chart_data = [{
                "labels": labels,
                "series": series
            }]


            pieChartOptions = get_chart_options(chart_type="pie")
            self.add_graph("Income by Category", "pie chart", pie_chart_data, options=pieChartOptions)
        except Exception as e:
            print("Error in IncomeCategoryProcessor:", e)
class ExpenseCategoryProcessor(PLProcessor):
    def process_data(self):
        try:
            end_date = pd.to_datetime(date.today())
            start_date = pd.to_datetime(date.today().replace(day=1) - pd.DateOffset(months=5))

            # Re-define the end date and start date for filtering, ensuring no timezone information
            start_date_no_tz = start_date.tz_localize(None)
            end_date_no_tz = end_date.tz_localize(None)

            # Filter the dataset for entries with type 'REVENUE' and consider only the last 6 months of data
            expense_data = self.df[(self.df['type'] == 'EXPENSE') & 
                                (pd.to_datetime(self.df['created_at']).dt.tz_localize(None) >= start_date_no_tz) &
                                (pd.to_datetime(self.df['created_at']).dt.tz_localize(None) <= end_date_no_tz)]
            
            # Aggregate the total amount per income category using the 'name' as the category label
            income_category_breakdown = expense_data.groupby('name')['balance'].sum().reset_index()

            # Prepare the labels and series for the pie chart data structure
            labels = income_category_breakdown['name'].tolist()
            series = income_category_breakdown['balance'].tolist()

            series = [0 if pd.isna(item) else item for item in series]
            # Structuring the output for the income category breakdown
            pie_chart_data = [{
                "labels": labels,
                "series": series
            }]

            pieChartOptions = get_chart_options(chart_type="pie")
            self.add_graph("Expense by Category", "pie chart", pie_chart_data, options=pieChartOptions)
        except Exception as e:
            print("Error in ExpenseCategoryProcessor:", e)

class CombinedDataProcessor(PLProcessor):
    def process_data(self):
        try:
            end_date = pd.to_datetime(date.today())
            start_date = pd.to_datetime(date.today().replace(day=1) - pd.DateOffset(months=5))

            self.df['created_at_no_tz'] = pd.to_datetime(self.df['created_at']).dt.tz_localize(None)

            # Re-define the end date and start date for filtering, ensuring no timezone information
            start_date_no_tz = start_date.tz_localize(None)
            end_date_no_tz = end_date.tz_localize(None)

            # Re-filter the data to include only the last 6 months, now without timezone issues
            filtered_expense_data_no_tz = self.df[(self.df['created_at_no_tz'] >= start_date_no_tz) & 
                                                    (self.df['created_at_no_tz'] <= end_date_no_tz)]
            filtered_income = filtered_expense_data_no_tz[filtered_expense_data_no_tz['type'] == 'REVENUE']
            filtered_expense = filtered_expense_data_no_tz[filtered_expense_data_no_tz['type'] == 'EXPENSE']
            # Ensure the monthly period index covers the last 6 months, even for months without income data
            period_index = pd.period_range(start=start_date_no_tz, end=end_date_no_tz, freq='M')

            # Group by month and sum balances, then reindex to ensure all last 6 months are covered
            monthly_income = filtered_income.groupby(filtered_income['created_at_no_tz'].dt.to_period('M'))['balance'].sum()
            monthly_expense = filtered_expense.groupby(filtered_expense['created_at_no_tz'].dt.to_period('M'))['balance'].sum()
            monthly_profit = monthly_income - monthly_expense
            monthly_profit = monthly_profit.reindex(period_index, fill_value=0).reset_index()
            monthly_income = monthly_income.reindex(period_index, fill_value=0).reset_index()
            monthly_expense = monthly_expense.reindex(period_index, fill_value=0).reset_index()

            # Preparing the data for the expected output structure, considering all months in the period
            total_profit = monthly_profit['balance'].tolist()
            total_income = monthly_income['balance'].tolist()
            total_expense = monthly_expense['balance'].tolist()
            dates_str = monthly_profit['index'].astype(str).tolist()

            # Structuring the output for the last 6 months
            
            total_profit = [0 if pd.isna(item) else item for item in total_profit]
            total_income = [0 if pd.isna(item) else item for item in total_income]
            total_expense = [0 if pd.isna(item) else item for item in total_expense]

            line_chart_combined= [
                {
                    "name": "Total Income",
                    "data": total_income
                },
                {
                    "name": "Total Expense",
                    "data": total_expense
                },
                {
                    "name": "Net Profit",
                    "data": total_profit
                }
            ]

            lineChartOptions = get_chart_options(chart_type="line")
            lineChartOptions["xaxis"]["categories"] = dates_str
            lineChartOptions["yaxis"]["title"] = {"text": "Amount (USD)"}

            self.add_graph("Income Expense and Profit Over Time", "line chart", line_chart_combined, options=lineChartOptions)
        except Exception as e:
            print("Error in CombinedDataProcessor:", e)
class OperationalExpenseVendorExpensesDistributionProcessor(PLProcessor):   
    def process_data(self):
        try:
            end_date = pd.to_datetime(date.today())
            start_date = pd.to_datetime(date.today().replace(day=1) - pd.DateOffset(months=5))

            # Re-define the end date and start date for filtering, ensuring no timezone information
            start_date_no_tz = start_date.tz_localize(None)
            end_date_no_tz = end_date.tz_localize(None)

            # Filter the dataset for entries with type 'REVENUE' and consider only the last 6 months of data
            expense_data = self.df[(self.df['type'] == 'EXPENSE') & 
                                (pd.to_datetime(self.df['created_at']).dt.tz_localize(None) >= start_date_no_tz) &
                                (pd.to_datetime(self.df['created_at']).dt.tz_localize(None) <= end_date_no_tz)]
            
            # Aggregate the total amount per income category using the 'name' as the category label
            expense_category_breakdown = expense_data.groupby('name')['balance'].sum().reset_index()
            # Keep only expense categories  with expense > 0
            expense_category_breakdown = expense_category_breakdown[expense_category_breakdown['balance'] > 0]

            # Prepare the labels and series for the pie chart data structure
            labels = expense_category_breakdown['name'].tolist()
            series = expense_category_breakdown['balance'].tolist()

            series = [0 if pd.isna(item) else item for item in series]

            # Structuring the output for the income category breakdown
            pie_chart_data = [{
                "labels": labels,
                "series": series
            }]

            pieChartOptions = get_chart_options(chart_type="pie")
            self.add_graph("Vendor Expenses Distribution", "pie chart", pie_chart_data, options=pieChartOptions)
        except Exception as e:
            print("Error in OperationalExpenseVendorExpensesDistributionProcessor:", e)

class OperationalExpenseMonthlyExpenseProcessor(PLProcessor):    
    def process_data(self):
        try:
            end_date = pd.to_datetime(date.today())
            start_date = pd.to_datetime(date.today().replace(day=1) - pd.DateOffset(months=5))

            self.df['created_at_no_tz'] = pd.to_datetime(self.df['created_at']).dt.tz_localize(None)

            # Re-define the end date and start date for filtering, ensuring no timezone information
            start_date_no_tz = start_date.tz_localize(None)
            end_date_no_tz = end_date.tz_localize(None)

            # Re-filter the data to include only the last 6 months, now without timezone issues
            filtered_expense_data_no_tz = self.df[(self.df['created_at_no_tz'] >= start_date_no_tz) & 
                                                    (self.df['created_at_no_tz'] <= end_date_no_tz)]
            filtered_expense = filtered_expense_data_no_tz[filtered_expense_data_no_tz['type'] == 'EXPENSE']
            # Ensure the monthly period index covers the last 6 months, even for months without income data
            period_index = pd.period_range(start=start_date_no_tz, end=end_date_no_tz, freq='M')

            # Group by month and sum balances, then reindex to ensure all last 6 months are covered
            monthly_income_corrected = filtered_expense.groupby(filtered_expense['created_at_no_tz'].dt.to_period('M'))['balance'].sum()
            monthly_income_corrected = monthly_income_corrected.reindex(period_index, fill_value=0).reset_index()

            # Preparing the data for the expected output structure, considering all months in the period
            total_expense_corrected = monthly_income_corrected['balance'].tolist()
            dates_str = monthly_income_corrected['index'].astype(str).tolist()

            total_expense_corrected = [0 if pd.isna(item) else item for item in total_expense_corrected]
            # Structuring the output for the last 6 months
            bar_chart_expense = [
                {
                    "name": "Total Expense",
                    "data": total_expense_corrected
                }
            ]

            barChartOptions = get_chart_options(chart_type="bar")
            barChartOptions["xaxis"]["categories"] = dates_str
            barChartOptions["yaxis"]["title"] = {"text": "Amount (USD)"}
        
            self.add_graph("Monthly Expenses Breakdown", "bar chart", bar_chart_expense, options=barChartOptions)
        except Exception as e:
            print("Error in OperationalExpenseMonthlyExpenseProcessor:", e)
class BalanceSheetRevenuePerCustomer(PLProcessor):
    def process_data(self):
        try:  
            customers = []
        
            for column in self.df[0]["Columns"]["Column"]:
                if column.get("ColType") == "Money":
                    customers.append(column["ColTitle"])

            customers = list(set(customers))
            print("customers", customers)
            revenue_per_customer =[0 for i in range(len(customers))]
            for i in range(len(self.df)):
                for row in self.df[i]["Rows"]["Row"]:
                    if row.get('group') == 'Income' and 'Summary' in row:
                        # print("row", row)
                        for j in range(len(customers)):
                            revenue = row['Summary']['ColData'][j+1].get('value')
                            if revenue and revenue != "":
                                revenue = float(revenue)
                                # Aggregate revenue for each customer
                                revenue_per_customer[j] += revenue
            
            # remove any datapoint called "TOTAL" or "total" from the customers list
            if "TOTAL" in customers or "Total" in customers:
                total_index = customers.index("TOTAL")
                customers.pop(total_index)
                revenue_per_customer.pop(total_index)
            print("revenue_per_customer", revenue_per_customer)
            # Sort the dictionary by revenue and get the top 10 customers
            if customers and revenue_per_customer:
                top_customers, top_revenue = zip(*sorted(zip(customers, revenue_per_customer), key=lambda x: x[1], reverse=True)[:10])
            else:
                top_customers = []
                top_revenue = []

            # Structuring the output for the income category breakdown
            pie_chart_data = [{
                "labels": list(top_customers),
                "series": [0 if pd.isna(item) else item for item in list(top_revenue)]
            }]


            pieChartOptions = get_chart_options(chart_type="pie")

            self.add_graph("Revenue breakdown for top customers", "pie chart", pie_chart_data, options=pieChartOptions)
        except Exception as e:
            print("Error in BalanceSheetRevenuePerCustomer:", e)

class AgedPayablesProcessor(PLProcessor):
    def process_data(self):
        try:
            print("accounts payable: ", self.df["AgedPayables"])
            columns_AP = self.df["AgedPayables"]["Columns"]["Column"]
            rows_AP = self.df["AgedPayables"]["Rows"]["Row"]

            print("accounts receivable: ", self.df["AgedReceivables"])
            columns_AR = self.df["AgedReceivables"]["Columns"]["Column"]
            rows_AR = self.df["AgedReceivables"]["Rows"]["Row"]
            

            # Initialize a dictionary to store sums for each aging period
            aging_sums_AP = {}
            aging_sums_AR = {}

            # Iterate through columns to get the aging period titles
            for column in columns_AP:
                if column["ColType"] == "Money":
                    aging_period = column["ColTitle"]
                    if aging_period:
                        aging_sums_AP[aging_period] = 0.0
                        aging_sums_AR[aging_period] = 0.0


            # Iterate through rows to accumulate sums for each aging period
            for row in rows_AR:
                # Skip rows that are not vendor type (e.g., GrandTotal)
                if "ColData" in row:
                    col_data = row["ColData"]
                    for i, col in enumerate(col_data):
                        # Check if the column corresponds to an aging period
                        if i > 0 and i < len(columns_AR) - 1:  # Exclude first and last column
                            value = col["value"]
                            if value and value != "":
                                # Convert value to float and add it to the corresponding sum
                                aging_period = columns_AR[i]["ColTitle"]
                                aging_sums_AR[aging_period] += float(value)


            for row in rows_AP:
                # Skip rows that are not vendor type (e.g., GrandTotal)
                if "ColData" in row:
                    col_data = row["ColData"]
                    for i, col in enumerate(col_data):
                        # Check if the column corresponds to an aging period
                        if i > 0 and i < len(columns_AP) - 1:  # Exclude first and last column
                            value = col["value"]
                            if value and value != "":
                                # Convert value to float and add it to the corresponding sum
                                aging_period = columns_AP[i]["ColTitle"]
                                aging_sums_AP[aging_period] += float(value)

            aging_periods = list(aging_sums_AP.keys())
            barChartAccountsPayable = [
                {
                    "name": "Accounts Payable",
                    "data": [0 if pd.isna(aging_sums_AP[aging_period]) else aging_sums_AP[aging_period] for aging_period in aging_periods]
                },
                {
                    "name": "Accounts Receivable",
                    "data": [0 if pd.isna(aging_sums_AR[aging_period]) else aging_sums_AR[aging_period] for aging_period in aging_periods]
                },
            ]

            barChartOptions = get_chart_options(chart_type="bar")
            barChartOptions["xaxis"]["categories"] = aging_periods
            barChartOptions["yaxis"]["title"] = {"text": "Amount (USD)"}

            self.add_graph("Aged Payables and Receivables", "bar chart", barChartAccountsPayable, options=barChartOptions)
        except Exception as e:
            print("Error in AgedPayablesProcessor:", e)

class CashflowProcessor(PLProcessor):
    def process_data(self):
        try:
            columns = self.df["Columns"]["Column"]
            rows = self.df["Rows"]["Row"]

            # Initialize a dictionary to store sums for each cash flow category
            cashflow_sums = {}

            # Iterate through columns to get the cash flow category titles
            for column in columns:
                if column["ColType"] == "Money":
                    cashflow_category = column["ColTitle"]
                    if cashflow_category:
                        cashflow_sums[cashflow_category] = 0.0
            print("cashflow_sums", cashflow_sums)
            # Iterate through rows to accumulate sums for each cash flow category
            for row in rows:
                # Skip rows that are not vendor type (e.g., GrandTotal)
                if "group" in row:
                    if row["group"] == "EndingCash":
                        col_data = row["Summary"]["ColData"]
                        for i, col in enumerate(col_data):
                            # Check if the column corresponds to a cash flow category
                            if i > 0:  # Exclude first column
                                value = col["value"]
                                if value and value != "":
                                    # Convert value to float and add it to the corresponding sum
                                    cashflow_category = columns[i]["ColTitle"]
                                    cashflow_sums[cashflow_category] += float(value)

            cashflow_categories = list(cashflow_sums.keys())
            barChartCashFlow = [
                {
                    "name": "Cash Flow",
                    "data": [0 if pd.isna(cashflow_sums[cashflow_category]) else cashflow_sums[cashflow_category] for cashflow_category in cashflow_categories]
                }
            ]

            barChartOptions = get_chart_options(chart_type="bar")
            barChartOptions["xaxis"]["categories"] = cashflow_categories
            barChartOptions["yaxis"]["title"] = {"text": "Amount (USD)"}

            self.add_graph("Cash Flow", "bar chart", barChartCashFlow, options=barChartOptions)
        except Exception as e:
            print("Error in CashflowProcessor:", e)

def get_dashboard_qb_pl_unified(dashboard_id, df_path):
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

        # dfs_cat = {}
        # for category in df.keys():
        #     dfs_cat[category] = pd.DataFrame(df[category])
        
        # processors = [

        #         TotalARProcessor(dashboard_id, dfs_cat["account"]),
        #         TotalAPProcessor(dashboard_id, dfs_cat["account"]),
        #         TotalFixedAssetsProcessor(dashboard_id, dfs_cat["account"]),
        #         TotalLiabilityProcessor(dashboard_id, dfs_cat["account"]),
        #         TotalExpenseProcessor(dashboard_id, dfs_cat["account"]),
        #         NetProfitProcessor(dashboard_id, dfs_cat["account"]),
        #         IncomeCategoryProcessor(dashboard_id, dfs_cat["account"]),
        #         ExpenseCategoryProcessor(dashboard_id, dfs_cat["account"]),
        #         CombinedDataProcessor(dashboard_id, dfs_cat["account"])
        #     ]
        # for processor in processors:
        #     processor.process_data()
        #     graph = processor.graphs[0]
        #     graphs.append(graph)
        
        # df_pl_detail = df["ProfitAndLossDetail"]
        # print("df", len(df_pl_detail))
        # processors = [
        #         # BalanceSheetTotalAssetProcessor(dashboard_id, df_pl_detail),
        #         # BalanceSheetTotalLiabilitiesProcessor(dashboard_id, df_pl_detail)
        #     ]
        
        df_pl = df["ProfitAndLoss"]
        print("df", len(df_pl))
        processors = [
                TotalRevenuePLProcessor(dashboard_id, df_pl),
                TotalPLProcessor(dashboard_id, df_pl),
                ExpenseRevenueBySourceProcessor(dashboard_id, df_pl),
            ]
        
        df_invoice =  pd.DataFrame(df["invoice"])
        processors += [
                TotalRevenueInvoiceProcessor(dashboard_id, df_invoice),
            ]
        
        # df_ap = df["Accounts Payable"]
        # processors += [
        #         BalanceSheetStatisticsAP(dashboard_id, df_ap),
        #     ]
    
        # df_ar = df["Accounts Receivable"]
        # processors += [
        #         BalanceSheetStatisticsAR(dashboard_id, df_ar),
        #     ]
        
        # df_expenses = df["Expense"]
        # processors += [
        #         BalanceSheetStatisticsExpenses(dashboard_id, df_expenses),
        #     ]
        
        # df_income = df["Income"]
        # processors += [
        #         BalanceSheetStatisticsIncome(dashboard_id, df_income),
        #     ]
        
        # df_bank = df["Bank"]
        # processors += [
        #         BalanceSheetStatisticsBankBalance(dashboard_id, df_bank),
        #     ]
        
        # df_asset = df["Fixed Asset"]
        # processors += [
        #         BalanceSheetStatisticsTotalAssets(dashboard_id, df_asset),
        #     ]

        # # df_ap_ar = df[["Accounts Payable", "Accounts Receivable"]]
        # df_ap_ar = {k: df.get(k, None) for k in ("AgedPayables", "AgedReceivables")}

        # processors += [
        #         AgedPayablesProcessor(dashboard_id, df_ap_ar),
        #     ]
        
        # df_cashflow = df["CashFlow"]
        # processors += [
        #         CashflowProcessor(dashboard_id, df_cashflow),
        #     ]

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
