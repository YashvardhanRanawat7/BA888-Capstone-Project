import dash
from dash import dcc, html
import plotly.graph_objs as go
import plotly.express as px

# Initialize the Dash app
app = dash.Dash(__name__, external_stylesheets=[
    'https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;700&display=swap'
])
server = app.server

# Define Colors
COLORS = {
    'background': '#F0F4FA',
    'card_bg': '#FFFFFF',
    'text_primary': '#343A40',
    'text_secondary': '#6C757D',
    'accent': '#5867DD',
    'positive': '#28A745',
    'negative': '#DC3545',
    'icon': '#5867DD',
    'gauge_bg': '#E9ECEF',
    'chart_colors': ['#7044FF', '#36A2EB', '#FFCE56', '#FF6384', '#4BC0C0']
}

# Custom CSS for Card Styles
CARD_STYLE = {
    'backgroundColor': COLORS['card_bg'],
    'borderRadius': '15px',
    'boxShadow': '0 8px 20px rgba(0, 0, 0, 0.05)',
    'padding': '15px',
    'margin': '10px',
    'flex': '1',
    'minWidth': '200px',
    'textAlign': 'center',
    'fontFamily': 'Montserrat, sans-serif',
    'color': COLORS['text_secondary'],
}

CARD_TITLE_STYLE = {
    'marginBottom': '5px',
    'fontSize': '1.2em',
    'fontWeight': '500',
    'color': COLORS['text_secondary'],
}

CARD_VALUE_STYLE = {
    'color': COLORS['text_primary'],
    'fontSize': '2.5em',
    'fontWeight': '700',
}

ICON_STYLE = {
    'color': COLORS['icon'],
    'fontSize': '1.5em',
    'marginBottom': '10px',
}

SECTION_TITLE_STYLE = {
    'color': COLORS['text_primary'],
    'fontSize': '1.5em',
    'marginBottom': '20px',
    'fontWeight': '600',
    'textAlign': 'left',
    'fontFamily': 'Montserrat, sans-serif'
}

# Mock data for an AI SaaS startup
MOCK_STATISTICS_SAAS = [
    {"title": "ARR", "stat_type": "number", "data": {"value": 750000, "evol": 12.0}},
    {"title": "MRR", "stat_type": "number", "data": {"value": 62500}},
    {"title": "Runway (months)", "stat_type": "number", "data": {"value": 18}},
    {"title": "Cash Balance", "stat_type": "number", "data": {"value": 2000000}},
    {"title": "Total Sales", "stat_type": "number", "data": {"value": 1000000}},
    {"title": "AR Aging", "stat_type": "value", "data": {"Current": 100000, "1-30 days": 25000, "31-60 days": 15000, "61-90 days": 5000, "90+ days": 2000}},
    {"title": "AP Aging", "stat_type": "value", "data": {"Current": 80000, "1-30 days": 30000, "31-60 days": 10000, "61-90 days": 5000, "90+ days": 2000}},
    {"title": "Top Customers by Revenue", "stat_type": "value", "data": [(1, 250000), (2, 150000), (3, 120000), (4, 100000), (5, 80000)]},
    {"title": "Outstanding Invoices", "stat_type": "number", "data": {"value": 10}},
    {"title": "Customer Acquisition (last 30 days)", "stat_type": "number", "data": {"value": 25}},
    {"title": "Expense Breakdown", "stat_type": "value", "data": {"Payroll": 60000, "Marketing": 20000, "Cloud Services": 15000,"Travel": 10000}},
    {"title": "Payroll Summary", "stat_type": "number", "data": {"value": 60000}},
    {"title": "Employee Headcount", "stat_type": "number", "data": {"value": 30}},
    {"title": "ARR/Emp Score", "stat_type": "number", "data": {"value": 10}},
    {"title": "ARR/YiO Score", "stat_type": "number", "data": {"value": 12}},
    {"title": "Tech Count Score", "stat_type": "number", "data": {"value": 8}},
    {"title": "Fundraise/ARR Score", "stat_type": "number", "data": {"value": 7}},
    {"title": "Total Health Score", "stat_type": "number", "data": {"value": 37}},
]

# Replace processing function with a mock function for AI SaaS startup
def process_all_data(data):
    return MOCK_STATISTICS_SAAS

# Create metric card
def create_metric_card(title, value, change=None, is_currency=False):
    value_display = f"${value:,.2f}" if is_currency else f"{value:,.2f}" if isinstance(value, (int, float)) else str(value)
    change_color = COLORS['positive'] if isinstance(change, (int, float)) and change > 0 else COLORS['negative']
    change_display = f"{change:+.2f}%" if change is not None else ""

    return html.Div([
        html.Div([
            html.I(className="fas fa-dollar-sign", style=ICON_STYLE)
        ]),
        html.H3(title, style=CARD_TITLE_STYLE),
        html.H2(value_display, style=CARD_VALUE_STYLE),
        html.P(change_display, style={'color': change_color, 'fontSize': '0.9em'}),
    ], style=CARD_STYLE)

def create_pie_chart(data, title):
    if not data or not isinstance(data, dict):
        return html.Div([
            html.H3(title, style=CARD_TITLE_STYLE),
            html.P("No data available", style={'color': COLORS['text_secondary'], 'textAlign': 'center', 'fontSize': '1em'})
        ], style=CARD_STYLE)

    return html.Div([
        html.H3(title, style=CARD_TITLE_STYLE),
        dcc.Graph(
            responsive=True,
            figure=px.pie(
                values=list(data.values()),
                names=list(data.keys()),
                hole=0.4,
                color_discrete_sequence=COLORS['chart_colors']
            ).update_layout(
                showlegend=True,
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
                margin=dict(l=10, r=10, t=20, b=20),
                height=320,
            )
        )
    ], style={**CARD_STYLE, **{'minWidth': '300px', 'padding': '15px'}})

def create_bar_chart(data, title):
    if not data or not isinstance(data, list):
        return html.Div([
            html.H3(title, style=CARD_TITLE_STYLE),
            html.P("No data available", style={'color': COLORS['text_secondary'], 'textAlign': 'center', 'fontSize': '1em'})
        ], style=CARD_STYLE)
    
    customers, revenue = zip(*data)
    
    return html.Div([
        html.H3(title, style=CARD_TITLE_STYLE),
        dcc.Graph(
            responsive=True,
            figure=px.bar(
                x=customers,
                y=revenue,
                labels={'x': 'Customer', 'y': 'Revenue'},
                color=revenue,
                color_continuous_scale=COLORS['chart_colors']
            ).update_layout(
                showlegend=False,
                margin=dict(l=10, r=10, t=20, b=30),
                height=320,
                xaxis=dict(title='Customer'),
                yaxis=dict(title='Revenue'),
            )
        )
    ], style={**CARD_STYLE, **{'minWidth': '300px', 'padding': '15px'}})

# Create gauge chart with consistent color theme
def create_gauge_chart(value, title, max_value):
    return html.Div([
        html.H3(title, style=CARD_TITLE_STYLE),
        dcc.Graph(
            responsive=True,
            figure=go.Figure(go.Indicator(
                mode="gauge+number",
                value=value,
                domain={'x': [0, 1], 'y': [0, 1]},
                title={'text': "", 'font': {'size': 18}},
                gauge={
                    'axis': {'range': [None, max_value], 'visible': False},
                    'bar': {'color': COLORS['accent']},
                    'bgcolor': COLORS['gauge_bg'],
                    'borderwidth': 2,
                    'bordercolor': COLORS['text_secondary'],
                    'steps': [
                        {'range': [0, max_value], 'color': COLORS['gauge_bg']},
                    ],
                }
            )).update_layout(
                height=250,
                margin=dict(l=10, r=10, t=20, b=10),
                font={'family': 'Montserrat, sans-serif', 'color': COLORS['text_primary']},
                paper_bgcolor=COLORS['background'],
                plot_bgcolor=COLORS['background'],
            )
        )
    ], style={**CARD_STYLE, **{'minWidth': '300px', 'padding': '15px'}})

def health_score_layout(statistics):
    arr_emp_score_stat = next((stat for stat in statistics if stat['title'] == "ARR/Emp Score"), {})
    arr_yio_score_stat = next((stat for stat in statistics if stat['title'] == "ARR/YiO Score"), {})
    tech_count_score_stat = next((stat for stat in statistics if stat['title'] == "Tech Count Score"), {})
    fundraise_arr_score_stat = next((stat for stat in statistics if stat['title'] == "Fundraise/ARR Score"), {})
    total_health_score_stat = next((stat for stat in statistics if stat['title'] == "Total Health Score"), {})

    return html.Div([
        html.H2("Health Score", style=SECTION_TITLE_STYLE),
        html.Div([
            create_gauge_chart(arr_emp_score_stat.get('data', {}).get("value", 0), "ARR/Emp Score", 15),
            create_gauge_chart(arr_yio_score_stat.get('data', {}).get("value", 0), "ARR/YiO Score", 15),
            create_gauge_chart(tech_count_score_stat.get('data', {}).get("value", 0), "Tech Count Score", 10),
            create_gauge_chart(fundraise_arr_score_stat.get('data', {}).get("value", 0), "Fundraise/ARR Score", 10),
        ], style={'display': 'flex', 'justifyContent': 'space-between', 'flexWrap': 'wrap', 'padding': '10px'}),
        html.Div([
            create_gauge_chart(total_health_score_stat.get('data', {}).get("value", 0), "Total Health Score", 50),
        ], style={'display': 'flex', 'justifyContent': 'center', 'flexWrap': 'wrap', 'marginTop': '20px'}),
    ])

def financial_overview_layout(statistics):
    arr_stat = next((stat for stat in statistics if stat['title'] == "ARR"), {})
    mrr_stat = next((stat for stat in statistics if stat['title'] == "MRR"), {})
    runway_stat = next((stat for stat in statistics if stat['title'] == "Runway (months)"), {})
    cash_balance_stat = next((stat for stat in statistics if stat['title'] == "Cash Balance"), {})
    total_sales_stat = next((stat for stat in statistics if stat['title'] == "Total Sales"), {})

    return html.Div([
        html.H2("Financial Overview", style=SECTION_TITLE_STYLE),
        html.Div([
            create_metric_card("Annual Recurring Revenue", arr_stat.get('data', {}).get("value"), arr_stat.get('data', {}).get("evol"), is_currency=True),
            create_metric_card("Monthly Recurring Revenue", mrr_stat.get('data', {}).get("value"), is_currency=True),
            create_metric_card("Runway (Months)", runway_stat.get('data', {}).get("value")),
            create_metric_card("Cash Balance", cash_balance_stat.get('data', {}).get("value"), is_currency=True),
            create_metric_card("Total Sales", total_sales_stat.get('data', {}).get("value"), is_currency=True),
        ], style={'display': 'flex', 'justifyContent': 'space-between', 'flexWrap': 'wrap'}),
    ])

def cash_flow_layout(statistics):
    ar_aging_stat = next((stat for stat in statistics if stat['title'] == "AR Aging"), {})
    ap_aging_stat = next((stat for stat in statistics if stat['title'] == "AP Aging"), {})
    
    return html.Div([
        html.H2("Cash Flow & Sales", style=SECTION_TITLE_STYLE),
        html.Div([
            create_pie_chart(ar_aging_stat.get('data'), "Accounts Receivable Aging"),
            create_pie_chart(ap_aging_stat.get('data'), "Accounts Payable Aging"),
        ], style={'display': 'flex', 'justifyContent': 'space-between', 'flexWrap': 'wrap'}),
    ])

def customer_insights_layout(statistics):
    top_customers_stat = next((stat for stat in statistics if stat['title'] == "Top Customers by Revenue"), {})
    outstanding_invoices_stat = next((stat for stat in statistics if stat['title'] == "Outstanding Invoices"), {})
    new_customers_stat = next((stat for stat in statistics if stat['title'] == "Customer Acquisition (last 30 days)"), {})
    
    return html.Div([
        html.H2("Customer Insights", style=SECTION_TITLE_STYLE),
        html.Div([
            create_bar_chart(top_customers_stat.get('data', []), "Top Customers by Revenue"),
            create_metric_card("Outstanding Invoices", outstanding_invoices_stat.get('data', {}).get("value")),
            create_metric_card("New Customers (Last 30 Days)", new_customers_stat.get('data', {}).get("value")),
        ], style={'display': 'flex', 'justifyContent': 'space-between', 'flexWrap': 'wrap'}),
    ])

def expense_breakdown_layout(statistics):
    expenses_stat = next((stat for stat in statistics if stat['title'] == "Expense Breakdown"), {})
    
    return html.Div([
        html.H2("Expense Breakdown", style=SECTION_TITLE_STYLE),
        html.Div([
            create_pie_chart(expenses_stat.get('data'), "Major Expense Categories"),
        ], style={'display': 'flex', 'justifyContent': 'center', 'flexWrap': 'wrap'}),
    ])

def operational_metrics_layout(statistics):
    payroll_stat = next((stat for stat in statistics if stat['title'] == "Payroll Summary"), {})
    headcount_stat = next((stat for stat in statistics if stat['title'] == "Employee Headcount"), {})
    
    return html.Div([
        html.H2("Operational Metrics", style=SECTION_TITLE_STYLE),
        html.Div([
            create_metric_card("Payroll Expenses", payroll_stat.get('data', {}).get("value"), is_currency=True),
            create_metric_card("Employee Headcount", headcount_stat.get('data', {}).get("value")),
        ], style={'display': 'flex', 'justifyContent': 'space-between', 'flexWrap': 'wrap'}),
    ])

# Define the layout function
def serve_layout():
    statistics = process_all_data(None)
    
    return html.Div([
        html.Div([
            html.Img(src='/Users/yashvardhansinghranawat/Documents/dash_healthscore_app/assets/HeronAI_Colorful_Black_Background (1).png', style={'height': '50px', 'float': 'left'}),
            html.H1("BUSINESS SNAPSHOT DASHBOARD", style={'textAlign': 'center', 'margin': '0', 'lineHeight': '50px', 'color': 'white', 'fontSize': '24px', 'fontFamily': 'Montserrat, sans-serif'}),
            html.Div(style={'clear': 'both'})
        ], style={'backgroundColor': COLORS['accent'], 'padding': '10px', 'marginBottom': '20px', 'boxShadow': '0 4px 6px rgba(0, 0, 0, 0.1)'}),
        
        # Move Health Score to the top
        health_score_layout(statistics),
        
        # Adjust Financial Overview to include Sales
        financial_overview_layout(statistics),
        
        cash_flow_layout(statistics),
        customer_insights_layout(statistics),
        expense_breakdown_layout(statistics),
        operational_metrics_layout(statistics),
    ], style={'padding': '20px', 'backgroundColor': COLORS['background'], 'borderRadius': '15px', 'fontFamily': 'Montserrat, sans-serif'})

# Set the layout
app.layout = serve_layout

if __name__ == '__main__':
    app.run_server(debug=True)
