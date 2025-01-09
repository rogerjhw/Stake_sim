from sklearn.ensemble import IsolationForest
import pandas as pd

agg_file_path = ''

df =  pd.read_csv(agg_file_path)

#Feature engineering

df['Total_Daily_Cost_By_Service'] = df.groupby(['Year','Month','Day', 'Service'])['Cost'].transform('sum')
df['Total_Daily_Cost_By_Account'] = df.groupby(['Year','Month','Day', 'Account'])['Cost'].transform('sum')
df['Daily_Cost'] = df.groupby(['Year','Month','Day'])['Cost'].transform('sum')
df['Service_Cost'] = df.groupby(['Year','Month','Day', 'Service'])['Cost'].transform('sum')

df_filled = df.fillna({
    'Cost': 0,
    'Total_Daily_Cost_By_Service': 0,
    'Total_Daily_Cost_By_Account': 0,
    'Daily_Cost': 0,
    'Service_Cost': 0
})

features = df_filled[['Cost', 'Total_Daily_Cost_By_Service', 'Total_Daily_Cost_By_Account', 'Daily_Cost', 'Service_Cost']].values

iso_forest = IsolationForest(contamination=0.002)
iso_forest.fit(features)

anomaly_scores = iso_forest.decision_function(features)
anomalies = iso_forest.predict(features)

df['Anomaly'] = anomalies

local_download_path = ''

df.to_csv(local_download_path + 'agg_anom.csv')