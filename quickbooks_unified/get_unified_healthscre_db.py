import os
import pandas as pd
from utils import get_chart_options
from models.models import Graph, Statistics
from datetime import date
import json

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

            start_date_no_tz = start_date.tz_localize(None)
            end_date_no_tz = end_date.tz_localize(None)

            filtered_ar_data_no_tz = self.df[(self.df['created_at_no_tz'] >= start_date_no_tz) & 
                                             (self.df['created_at_no_tz'] <= end_date_no_tz)]
            filtered_ar = filtered_ar_data_no_tz[filtered_ar_data_no_tz['type'] == 'ACCOUNTS_RECEIVABLE']
            period_index = pd.period_range(start=start_date_no_tz, end=end_date_no_tz, freq='M')

            monthly_ar_corrected = filtered_ar.groupby(filtered_ar['created_at_no_tz'].dt.to_period('M'))['balance'].sum()
            monthly_ar_corrected = monthly_ar_corrected.reindex(period_index, fill_value=0).reset_index()

            total_ar_corrected = monthly_ar_corrected['balance'].tolist()
            dates_str = monthly_ar_corrected['index'].astype(str).tolist()

            total_ar_corrected = [0 if pd.isna(item) else item for item in total_ar_corrected]
            line_chart_total_ar = [
                {
                    "name": "Accounts Receivable",
                    "data": total_ar_corrected
                }
            ]

            lineChartOptions = get_chart_options(chart_type="line")
            lineChartOptions["xaxis"]["categories"] = dates_str
            lineChartOptions["yaxis"]["title"] = {"text": "Accounts Receivable (USD)"}

            self.add_graph("Accounts Receivable Over Time", "line chart", line_chart_total_ar, options=lineChartOptions)
        except Exception as e:
            print("Error in TotalARProcessor:", e)


class IncomeCategoryProcessor(PLProcessor):
    def process_data(self):
        try:
            end_date = pd.to_datetime(date.today())
            start_date = pd.to_datetime(date.today().replace(day=1) - pd.DateOffset(months=5))

            start_date_no_tz = start_date.tz_localize(None)
            end_date_no_tz = end_date.tz_localize(None)

            revenue_data = self.df[(self.df['type'] == 'REVENUE') & 
                                   (pd.to_datetime(self.df['created_at']).dt.tz_localize(None) >= start_date_no_tz) &
                                   (pd.to_datetime(self.df['created_at']).dt.tz_localize(None) <= end_date_no_tz)]
            
            income_category_breakdown = revenue_data.groupby('name')['balance'].sum().reset_index()

            labels = income_category_breakdown['name'].tolist()
            series = income_category_breakdown['balance'].tolist()
            series = [0 if pd.isna(item) else item for item in series]

            pie_chart_data = [{
                "labels": labels,
                "series": series
            }]

            pieChartOptions = get_chart_options(chart_type="pie")
            self.add_graph("Income by Category", "pie chart", pie_chart_data, options=pieChartOptions)
        except Exception as e:
            print("Error in IncomeCategoryProcessor:", e)


class BalanceSheetRevenuePerCustomer(PLProcessor):
    def process_data(self):
        try:
            customers = []
        
            for column in self.df[0]["Columns"]["Column"]:
                if column.get("ColType") == "Money":
                    customers.append(column["ColTitle"])

            customers = list(set(customers))
            revenue_per_customer =[0 for i in range(len(customers))]
            for i in range(len(self.df)):
                for row in self.df[i]["Rows"]["Row"]:
                    if row.get('group') == 'Income' and 'Summary' in row:
                        for j in range(len(customers)):
                            revenue = row['Summary']['ColData'][j+1].get('value')
                            if revenue and revenue != "":
                                revenue = float(revenue)
                                revenue_per_customer[j] += revenue

            if "TOTAL" in customers or "Total" in customers:
                total_index = customers.index("TOTAL")
                customers.pop(total_index)
                revenue_per_customer.pop(total_index)

            if customers and revenue_per_customer:
                top_customers, top_revenue = zip(*sorted(zip(customers, revenue_per_customer), key=lambda x: x[1], reverse=True)[:10])
            else:
                top_customers = []
                top_revenue = []

            pie_chart_data = [{
                "labels": list(top_customers),
                "series": [0 if pd.isna(item) else item for item in list(top_revenue)]
            }]

            pieChartOptions = get_chart_options(chart_type="pie")
            self.add_graph("Revenue breakdown for top customers", "pie chart", pie_chart_data, options=pieChartOptions)
        except Exception as e:
            print("Error in BalanceSheetRevenuePerCustomer:", e)


class AgedReceivableProcessor(PLProcessor):
    def process_data(self):
        try:
            aging_sums_AR = {}
            ar_periods = ['Current', '1 - 30', '31 - 60', '61 - 90', '91 and over']
            columns_AR = self.df[-1]["Columns"]["Column"]
            for column in columns_AR:
                if column["ColTitle"] in ar_periods:
                    aging_period = column["ColTitle"]
                    if aging_period:
                        aging_sums_AR[aging_period] = 0
                    
            rows_AR = self.df[-1]["Rows"]["Row"]

            for row in rows_AR:
                if "ColData" in row:
                    col_data = row["ColData"]
                    for i, col in enumerate(col_data):
                        if columns_AR[i]["ColTitle"] in ar_periods:
                            value = col["value"]
                            if value and value != "":
                                aging_period = columns_AR[i]["ColTitle"]
                                aging_sums_AR[aging_period] += float(value)

            aging_periods = list(aging_sums_AR.keys())
            barChartAccountsPayable = [
                {
                    "name": "Accounts Receivable",
                    "data": [0 if pd.isna(aging_sums_AR[aging_period]) else aging_sums_AR[aging_period] for aging_period in aging_periods]
                },
            ]

            barChartOptions = get_chart_options(chart_type="bar")
            barChartOptions["xaxis"]["categories"] = aging_periods
            barChartOptions["yaxis"]["title"] = {"text": "Amount (USD)"}

            self.add_graph("Aged Receivables Aging Breakdown", "bar chart", barChartAccountsPayable, options=barChartOptions)
        except Exception as e:
            print("Error in AgedReceivableProcessor:", e)


class TotalRevenueInvoiceProcessor(PLProcessor):
    def process_data(self):
        try:
            invoice_df = self.df

            invoice_df["unpaid_amount"] = invoice_df["total_amount"] - invoice_df["paid_amount"]
            total_unpaid_invoice = sum(invoice_df["unpaid_amount"])    

            data={
                "value": total_unpaid_invoice,
                "evol": None,
            }
            self.add_statistics("Total Unpaid Invoices", "money", data)

            unpaid_invoice_by_customer = invoice_df.groupby("company_name")["unpaid_amount"].sum().reset_index()
            unpaid_invoice_by_customer = unpaid_invoice_by_customer.sort_values(by="unpaid_amount", ascending=False)
            top_10_unpaid_invoice_by_customer = unpaid_invoice_by_customer.head(10)

            barChartDataUnpaidInvoiceByCustomer = [
                {
                    "name": "Unpaid Invoice",
                    "data": top_10_unpaid_invoice_by_customer["unpaid_amount"].tolist(),
                },
            ]

            barChartOptionsUnpaidInvoiceByCustomer = get_chart_options(chart_type="bar")
            barChartOptionsUnpaidInvoiceByCustomer["xaxis"]["categories"] = top_10_unpaid_invoice_by_customer["company_name"].tolist()
            barChartOptionsUnpaidInvoiceByCustomer["yaxis"]["title"] = {"text": "Amount (USD)"}

            self.add_graph("Unpaid Invoice by Customer", "bar chart", barChartDataUnpaidInvoiceByCustomer, options=barChartOptionsUnpaidInvoiceByCustomer)
        except Exception as e:
            print("Error in TotalRevenueInvoiceProcessor:", e)

def get_dashboard_qb_income_tracker_unified(dashboard_id, df_path):
    try:
        # Load local JSON file
        with open(df_path, 'r') as f:
            df = json.load(f)
        
        sheet_name = None
        graphs = []
        statistics = []

        df_account = pd.DataFrame(df["account"])

        processors = [
            IncomeCategoryProcessor(dashboard_id, df_account),
            TotalARProcessor(dashboard_id, df_account),
        ]

        df_pl = df["ProfitAndLoss"]
        processors += [
            BalanceSheetRevenuePerCustomer(dashboard_id, df_pl),
        ]

        df_contact = pd.DataFrame(df["contact"])
        df_invoice = pd.DataFrame(df["invoice"])

        # Merge the contact name from contact table to the invoice table using contact id
        try:
            df_invoice = pd.merge(df_invoice, df_contact, left_on='contact_id', right_on='id', how='left')
        except Exception as e:
            print("Error in merging contact and invoice table", e)

        processors += [
            TotalRevenueInvoiceProcessor(dashboard_id, df_invoice),
        ]

        df_ar = df["Accounts Receivable"]
        processors += [
            BalanceSheetStatisticsAR(dashboard_id, df_ar),
        ]

        df_ar = df["AgedReceivables"]

        processors += [
            AgedReceivableProcessor(dashboard_id, df_ar),
        ]

        for processor in processors:
            processor.process_data()
            graphs_processed = processor.graphs
            statistics_processed = processor.statistics
            for graph in graphs_processed:
                graphs.append(graph)
            for statistic in statistics_processed:
                statistics.append(statistic)

        return graphs, statistics
    except Exception as e:
        print("Error in get_dashboard_qb_income_tracker_unified : ", e)
        return []
