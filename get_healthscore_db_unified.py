import os
import pandas as pd
from utils import get_chart_options, get_dataframe,get_data_unified
from models.models import Graph, Statistics
from datetime import datetime, timedelta
import json
import pytz


#### Fetching Data ( This part can be removed )

# Environment setup
os.environ['ENVIRONMENT'] = 'local'

#SHOULD BE REMOVED DURING INTEGRATION
os.chdir("/Users/yashvardhansinghranawat/Desktop/HeronHealthScore/backend-mainbu")

# Hard-coded variables (to be removed when integrated)
authorization_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySWQiOiI2Njc0NjA4MGQ5N2QzZjg5ZjdkMjIwZTIiLCJ3b3Jrc3BhY2VfaWQiOiI2NjAzMDhiZjM2ODcyOWJjMzczNzRhM2EiLCJpYXQiOjE3MTg5MDI5MTJ9.9IyJnTX4OWLxWCUyfN1M-umXszYwj8JCGlhdEQxnPZc"
app_name = 'Quickbooks'
connection_api_id = '6691378f636f536021f4ac35' #sandbox
connection_id = '6691378f636f536021f4ac35'
environment = 'local'
organizationname = 'Test'

# Fetch data from Unified
data_json = get_data_unified(
    app_name,
    authorization_token,
    connection_api_id,
    passthrough=True
)

file_name = f"{organizationname}/{app_name}/{str(connection_id)}.json"

# Save data locally if in local environment
if environment == 'local':
    local_path = "public/json/"
    df_path = local_path + file_name
    with open(df_path, "w") as f:
        json.dump(data_json, f, indent=4)

# Constants
ARR_EMP_AVG = 187500
ARR_YIO_AVG = 750000
TECH_COUNT_AVG = 30
FUNDRAISE_ARR_AVG = 1000000  # This value should be updated based on actual data

# Load JSON data
def load_json_data(file_path):
    with open(file_path, 'r') as file:
        return json.load(file)

# Base class for processors
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

    def add_statistics(self, title, stat_type, data, evol=0):
        if isinstance(data, (int, float)):  # Check if data is a simple value
            data = {"value": data, "evol": evol}
        statistic = Statistics(
            dashboard_id=self.dashboard_id,
            title=title,
            stat_type=stat_type,
            data=data,
            parameters=None
        )
        self.statistics.append(statistic)

    def save_to_db(self):
        # Placeholder for saving to database, assuming db should be defined
        # db.session.bulk_save_objects(self.graphs + self.statistics)
        # db.session.commit()
        pass

# Recurring Revenue Processor
class RecurringRevenueProcessor(PLProcessor):
    def process_data(self):
        try:
            invoices = self.df.get('invoice', [])
            df_invoices = pd.DataFrame(invoices)

            if 'created_at' not in df_invoices.columns or 'total_amount' not in df_invoices.columns:
                print("Warning: Required columns not found in invoices. Using total invoice amount as ARR.")
                arr = df_invoices['total_amount'].sum() if 'total_amount' in df_invoices.columns else 0
                mrr = arr / 12
                percent_change = 0
            else:
                df_invoices['created_at'] = pd.to_datetime(df_invoices['created_at'], utc=True)
                df_invoices['total_amount'] = pd.to_numeric(df_invoices['total_amount'], errors='coerce')

                now = pd.Timestamp.now(pytz.utc)
                period_start = now - pd.DateOffset(months=12)
                previous_period_start = period_start - pd.DateOffset(months=12)

                current_revenue = df_invoices[(df_invoices['created_at'] > period_start) & (df_invoices['created_at'] <= now)]['total_amount'].sum()
                previous_revenue = df_invoices[(df_invoices['created_at'] > previous_period_start) & (df_invoices['created_at'] <= period_start)]['total_amount'].sum()

                arr = current_revenue * (12 / 12)
                mrr = arr / 12
                percent_change = ((current_revenue - previous_revenue) / previous_revenue * 100) if previous_revenue else 0

            self.add_statistics("ARR", "number", arr, percent_change)
            self.add_statistics("MRR", "number", mrr)
            self.add_statistics("Percent Change in Revenue", "percentage", percent_change)
        except Exception as e:
            print("Error in RecurringRevenueProcessor:", e)

# Runway Processor
class RunwayProcessor(PLProcessor):
    def process_data(self):
        try:
            transactions = self.df.get('transaction', [])
            accounts = self.df.get('account', [])

            total_capital = sum(account.get('balance', 0) for account in accounts if account.get('type') == 'BANK')

            expenses = [t for t in transactions if t.get('type') in ['Expense', 'Bill']]
            df_expenses = pd.DataFrame(expenses)

            if df_expenses.empty:
                print("Warning: No expense transactions found. Cannot calculate runway.")
                runway = None
            else:
                amount_column = next((col for col in df_expenses.columns if 'amount' in col.lower()), None)
                if not amount_column:
                    print("Error: No amount column found in expense transactions.")
                    runway = None
                else:
                    df_expenses['created_at'] = pd.to_datetime(df_expenses['created_at'], utc=True)
                    df_expenses[amount_column] = pd.to_numeric(df_expenses[amount_column], errors='coerce')

                    cutoff_date = pd.Timestamp.now(pytz.utc) - pd.DateOffset(months=3)
                    recent_expenses = df_expenses[df_expenses['created_at'] > cutoff_date]

                    monthly_expenses = recent_expenses.groupby(recent_expenses['created_at'].dt.to_period('M'))[amount_column].sum()
                    avg_monthly_burn = monthly_expenses.mean()

                    if pd.isna(avg_monthly_burn) or avg_monthly_burn == 0:
                        runway = float('inf')
                    else:
                        runway = total_capital / avg_monthly_burn

            self.add_statistics("Runway (months)", "number", runway)
        except Exception as e:
            print("Error in RunwayProcessor:", e)

# Cash Balance Processor
class CashBalanceProcessor(PLProcessor):
    def process_data(self):
        try:
            accounts = self.df.get('account', [])
            cash_balance = sum(account.get('balance', 0) for account in accounts if account.get('type') in ['BANK', 'CASH'])
            self.add_statistics("Cash Balance", "number", cash_balance)
        except Exception as e:
            print("Error in CashBalanceProcessor:", e)

# AR Aging Processor
class AgingProcessor(PLProcessor):
    def __init__(self, dashboard_id, df, aging_type):
        super().__init__(dashboard_id, df)
        self.aging_type = aging_type

    def process_data(self):
        try:
            if self.aging_type == 'AR':
                items = self.df.get('invoice', [])
            else:  # AP
                items = [t for t in self.df.get('transaction', []) if t.get('type') == 'Bill']

            now = datetime.now(pytz.utc)
            aging_buckets = {'Current': 0, '1-30 days': 0, '31-60 days': 0, '61-90 days': 0, '90+ days': 0}

            for item in items:
                due_date = pd.to_datetime(item.get('due_at'), utc=True)
                days_overdue = (now - due_date).days
                amount = item.get('total_amount', 0)

                if days_overdue <= 0:
                    aging_buckets['Current'] += amount
                elif days_overdue <= 30:
                    aging_buckets['1-30 days'] += amount
                elif days_overdue <= 60:
                    aging_buckets['31-60 days'] += amount
                elif days_overdue <= 90:
                    aging_buckets['61-90 days'] += amount
                else:
                    aging_buckets['90+ days'] += amount

            self.add_statistics(f"{self.aging_type} Aging", "value", aging_buckets)
        except Exception as e:
            print(f"Error in AgingProcessor ({self.aging_type}):", e)

# Total Sales Processor
class TotalSalesProcessor(PLProcessor):
    def process_data(self):
        try:
            invoices = self.df.get('invoice', [])
            total_sales = sum(invoice.get('total_amount', 0) for invoice in invoices if invoice.get('status') == 'PAID')
            self.add_statistics("Total Sales", "number", total_sales)
        except Exception as e:
            print("Error in TotalSalesProcessor:", e)

# Top Customers Processor
class TopCustomersProcessor(PLProcessor):
    def __init__(self, dashboard_id, df, limit=5):
        super().__init__(dashboard_id, df)
        self.limit = limit

    def process_data(self):
        try:
            invoices = self.df.get('invoice', [])
            customer_revenue = {}
            for invoice in invoices:
                customer_id = invoice.get('contact_id')
                customer_revenue[customer_id] = customer_revenue.get(customer_id, 0) + invoice.get('total_amount', 0)
            top_customers = sorted(customer_revenue.items(), key=lambda x: x[1], reverse=True)[:self.limit]
            self.add_statistics("Top Customers by Revenue", "value", top_customers)
        except Exception as e:
            print("Error in TopCustomersProcessor:", e)

# Outstanding Invoices Processor
class OutstandingInvoicesProcessor(PLProcessor):
    def process_data(self):
        try:
            invoices = self.df.get('invoice', [])
            # Count invoices that are not "PAID" or "VOIDED"
            outstanding_invoices = sum(1 for invoice in invoices if invoice.get('status') not in ['PAID', 'VOIDED'])
            self.add_statistics("Outstanding Invoices", "number", outstanding_invoices)
        except Exception as e:
            print("Error in OutstandingInvoicesProcessor:", e)

# Customer Acquisition Processor
class CustomerAcquisitionProcessor(PLProcessor):
    def process_data(self):
        try:
            contacts = self.df.get('contact', [])
            now = datetime.now(pytz.utc)
            one_month_ago = now - timedelta(days=30)
            new_customers = sum(1 for contact in contacts if pd.to_datetime(contact.get('created_at'), utc=True) > one_month_ago)
            self.add_statistics("Customer Acquisition (last 30 days)", "number", new_customers)
        except Exception as e:
            print("Error in CustomerAcquisitionProcessor:", e)

# Expense Breakdown Processor
class ExpenseBreakdownProcessor(PLProcessor):
    def process_data(self):
        try:
            transactions = self.df.get('transaction', [])
            expenses = [t for t in transactions if t.get('type') == 'Expense']
            expense_categories = {}
            for expense in expenses:
                category = expense.get('account_id', 'Other')
                expense_categories[category] = expense_categories.get(category, 0) + expense.get('total_amount', 0)
            self.add_statistics("Expense Breakdown", "value", expense_categories)
        except Exception as e:
            print("Error in ExpenseBreakdownProcessor:", e)

# Payroll Summary Processor
class PayrollSummaryProcessor(PLProcessor):
    def process_data(self):
        try:
            transactions = self.df.get('transaction', [])
            payroll_expenses = sum(t.get('total_amount', 0) for t in transactions if t.get('type') == 'Expense' and t.get('account_id') == 'Payroll')
            self.add_statistics("Payroll Summary", "number", payroll_expenses)
        except Exception as e:
            print("Error in PayrollSummaryProcessor:", e)

# Employee Headcount Processor
class EmployeeHeadcountProcessor(PLProcessor):
    def process_data(self):
        try:
            employees = self.df.get('employee', [])
            employee_headcount = sum(1 for employee in employees if employee.get('employment_status') == 'ACTIVE')
            self.add_statistics("Employee Headcount", "number", employee_headcount)
        except Exception as e:
            print("Error in EmployeeHeadcountProcessor:", e)

# ARR/Emp Score Processor
class ARREmpScoreProcessor(PLProcessor):
    def process_data(self):
        try:
            arr_stat = next(stat for stat in self.statistics if stat.title == "ARR")
            arr = arr_stat.data["value"]
            employees = self.df.get('employee', [])
            num_employees = sum(1 for employee in employees if employee.get('employment_status') == 'ACTIVE')

            if num_employees == 0:
                arr_emp = 0
                arr_emp_score = 0
            else:
                arr_emp = arr / num_employees
                arr_emp_score = min((arr_emp / ARR_EMP_AVG) * 15, 15)
            
            self.add_statistics("ARR/Emp Score", "number", arr_emp_score)
        except Exception as e:
            print("Error in ARREmpScoreProcessor:", e)

# ARR/YiO Score Processor
class ARRYiOScoreProcessor(PLProcessor):
    def process_data(self):
        try:
            arr_stat = next(stat for stat in self.statistics if stat.title == "ARR")
            arr = arr_stat.data["value"]
            years_in_operation = self.df.get('years_in_operation', 1)

            if years_in_operation == 0:
                arr_yio = 0
                arr_yio_score = 0
            else:
                arr_yio = arr / years_in_operation
                arr_yio_score = min((arr_yio / ARR_YIO_AVG) * 15, 15)
            
            self.add_statistics("ARR/YiO Score", "number", arr_yio_score)
        except Exception as e:
            print("Error in ARRYiOScoreProcessor:", e)

# Tech Count Score Processor
class TechCountScoreProcessor(PLProcessor):
    def process_data(self):
        try:
            tech_count = self.df.get('tech_count', 0)
            tech_count_score = min((tech_count / TECH_COUNT_AVG) * 10, 10)
            
            self.add_statistics("Tech Count Score", "number", tech_count_score)
        except Exception as e:
            print("Error in TechCountScoreProcessor:", e)

# Fundraise/ARR Score Processor
class FundraiseARRScoreProcessor(PLProcessor):
    def process_data(self):
        try:
            arr_stat = next(stat for stat in self.statistics if stat.title == "ARR")
            arr = arr_stat.data["value"]
            total_funding = self.df.get('total_funding', 0)

            if arr == 0:
                fundraise_arr = 0
                fundraise_arr_score = 0
            else:
                fundraise_arr = total_funding / arr
                fundraise_arr_score = min((fundraise_arr / FUNDRAISE_ARR_AVG) * 10, 10)
            
            self.add_statistics("Fundraise/ARR Score", "number", fundraise_arr_score)
        except Exception as e:
            print("Error in FundraiseARRScoreProcessor:", e)

# Total Health Score Processor
class TotalHealthScoreProcessor(PLProcessor):
    def process_data(self):
        try:
            arr_emp_score_stat = next(stat for stat in self.statistics if stat.title == "ARR/Emp Score")
            arr_yio_score_stat = next(stat for stat in self.statistics if stat.title == "ARR/YiO Score")
            tech_count_score_stat = next(stat for stat in self.statistics if stat.title == "Tech Count Score")
            fundraise_arr_score_stat = next(stat for stat in self.statistics if stat.title == "Fundraise/ARR Score")

            total_health_score = (
                arr_emp_score_stat.data["value"] +
                arr_yio_score_stat.data["value"] +
                tech_count_score_stat.data["value"] +
                fundraise_arr_score_stat.data["value"]
            )
            
            self.add_statistics("Total Health Score", "number", total_health_score)
        except Exception as e:
            print("Error in TotalHealthScoreProcessor:", e)

# Main processing function
def get_dashboard_data(dashboard_id,file_path):
    try:
        data = data_json
        
        processors = [
            RecurringRevenueProcessor(dashboard_id, data),
            RunwayProcessor(dashboard_id, data),
            CashBalanceProcessor(dashboard_id, data),
            AgingProcessor(dashboard_id, data, 'AR'),
            AgingProcessor(dashboard_id, data, 'AP'),
            TotalSalesProcessor(dashboard_id, data),
            TopCustomersProcessor(dashboard_id, data),
            OutstandingInvoicesProcessor(dashboard_id, data),
            CustomerAcquisitionProcessor(dashboard_id, data),
            ExpenseBreakdownProcessor(dashboard_id, data),
            PayrollSummaryProcessor(dashboard_id, data),
            EmployeeHeadcountProcessor(dashboard_id, data),
            ARREmpScoreProcessor(dashboard_id, data),
            ARRYiOScoreProcessor(dashboard_id, data),
            TechCountScoreProcessor(dashboard_id, data),
            FundraiseARRScoreProcessor(dashboard_id, data),
            TotalHealthScoreProcessor(dashboard_id, data)
        ]

        graphs = []
        statistics = []
        for processor in processors:
            processor.process_data()
            graphs.extend(processor.graphs)
            statistics.extend(processor.statistics)

        # Debugging output, can be removed
        print("Graphs:", graphs)
        print("Statistics:", statistics)
        print("Contents of statistics list:")
        for i, stat in enumerate(statistics):
            print(f"Statistic {i+1}:")
            print(f"  Title: {stat.title}")
            print(f"  Stat Type: {stat.stat_type}")
            print(f"  Data: {stat.data}")
            print(f"  Parameters: {stat.parameters}")
            print("---")

        return graphs, statistics
    except Exception as e:
        print("Error in get_dashboard_data:", e)
        return [], []

# Example usage:
graphs, statistics = get_dashboard_data('dashboard_id',df_path)
#'/Users/yashvardhansinghranawat/Desktop/HeronHealthScore/backend-mainbu/public/json/Test/Quickbooks/669e9eb0f1d1824e28339205.json'