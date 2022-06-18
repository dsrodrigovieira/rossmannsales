import pandas as pd
import seaborn as sns
from matplotlib import pyplot as plt

px = 1/plt.rcParams['figure.dpi']

class Reports( object ):


    def data_transformation( self, data ):
        
        data['date'] = pd.to_datetime(pd.to_datetime(data['date']).dt.strftime('%Y-%m-%d'))
        data['day_of_month'] = data['date'].apply(lambda x: x.month_name()[:3] + ', ' + (str(x.day)+'st' if x.day == 1 else str(x.day)+'nd' if x.day == 2 else str(x.day)+'rd' if x.day == 3 else str(x.day)+'th'))
        data = data.sort_values('date').reset_index(drop=True)        

        return data
    
    def plots( self, data ):        
        
        plt.figure(figsize=(1800*px,600*px), tight_layout=True)
        sns.set_context("poster")
        sns.set_style("dark")

        g = sns.lineplot(data=data, x='day_of_month', y='prediction')
        g.set_ylabel('Sales (US$)')
        g.set_xlabel('')

        plt.xticks(rotation=60)

        plt.savefig('plots.png');

        return None