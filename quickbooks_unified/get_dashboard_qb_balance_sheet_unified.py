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


    
class BalanceSheetEquity(PLProcessor):
    def process_data(self):
        try:
            equity=[]
        
            for i, row in self.df.iterrows():

                if row['type'] == 'EQUITY':
                    equity.append(row['balance'])
             

            total_equity = sum(equity)
           

            self.add_statistics("Equity", "money", {"value": total_equity, "evol": None})
        except Exception as e:
            print("Error in BalanceSheetEquity:", e)

class BalanceSheetLiabilityAsset(PLProcessor):
    def process_data(self):
        try:
            liability = {}
            asset = {}
            
            for i, row in self.df.iterrows():
                if row['type'] == 'LIABILITY':
                    liability[row["name"]]=abs(row['balance'])
                elif row['type'] == 'FIXED_ASSET':
                    asset[row["name"]]=abs(row['balance'])

            total_liability = sum(liability.values())
            total_asset = sum(asset.values())

            # Structuring the output for the last 6 months
            barChartDataLiabilityAsset= [
                {
                    "name": "Liability vs Asset",
                    "data": [total_liability, total_asset],
                },
            ]

            pieChartDataLiability = [
                {
                    "labels": list(liability.keys()),
                    "series": list(liability.values())
                }
            ]



            pieChartDataAsset = [
                {
                    "labels": list(asset.keys()),
                    "series": list(asset.values())
                }
            ]
            
            pieChartOptionsAsset = get_chart_options(chart_type="pie")

            barChartOptionsLiabilityAsset = get_chart_options(chart_type="bar")
            barChartOptionsLiabilityAsset["xaxis"]["categories"] = ["Liability", "Asset"]
            barChartOptionsLiabilityAsset["yaxis"]["title"] = {"text": "Amount (USD)"}
           

            self.add_graph("Liability by Category", "pie chart", pieChartDataLiability, options=pieChartOptionsAsset)
            self.add_graph("Asset by Category", "pie chart", pieChartDataAsset, options=pieChartOptionsAsset)
            self.add_graph("Asset vs Liability", "bar chart", barChartDataLiabilityAsset, options=barChartOptionsLiabilityAsset)
        except Exception as e:
            print("Error in BalanceSheetLiabilityAsset:", e)




def get_dashboard_qb_balance_sheet_unified(dashboard_id, df_path):
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

       
        df_account = pd.DataFrame(df['account'])
        processors = [
                BalanceSheetEquity(dashboard_id, df_account),
                BalanceSheetLiabilityAsset(dashboard_id, df_account)
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
