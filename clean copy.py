import pandas as pd
import sqlite3

local_aws_file_path = ''
local_gcp_file_path = ''
local_snow_file_path = ''

aws = pd.read_csv(local_aws_file_path)
gcp = pd.read_csv(local_gcp_file_path)
snow =  pd.read_csv(local_snow_file_path)

#Cleaning/reformatting snowflake data

snow['DateTime'] = pd.to_datetime(snow['START_TIME'], utc=True)
snow['Year'] = snow['DateTime'].dt.year
snow['Month'] = snow['DateTime'].dt.month
snow['Day'] = snow['DateTime'].dt.day

snow.rename(columns = {'WAREHOUSE_NAME':'Account','CREDITS_USED':'Cost'}, inplace = True)
snow_clean = snow.drop(columns = ['START_TIME','DateTime','WAREHOUSE_ID','CREDITS_USED_COMPUTE','CREDITS_USED_CLOUD_SERVICES','END_TIME'])
snow_clean['Service'] = 'Snowflake General'
snow_clean['Cost'] *= 3

conn = sqlite3.connect('snow.db')
cursor = conn.cursor()

snow_clean.to_sql('snow', conn, if_exists='replace', index=False)

query = '''
SELECT *
FROM snow
GROUP BY Year, Month, Day, Account ;
'''

cursor.execute(query)
results = cursor.fetchall()

snow_clean = pd.DataFrame(results, columns = ['Account','Cost','Year','Month','Day','Service'])

#Cleaning/reformatting GCP data (the GCP dataset is already formatted in a standard fashion, just need to rename columns)

gcp_clean = gcp.rename(columns = {'year':'Year','month':'Month','day':'Day','description':'Service','id':'Account', 'total_cost':'Cost'})

#Cleaning/reformatting AWS data

conn = sqlite3.connect('aws.db')
cursor = conn.cursor()

aws.to_sql('aws', conn, if_exists='replace', index=False)

query = '''
SELECT strftime('%Y',line_item_usage_start_date) AS Year,
       strftime('%m',line_item_usage_start_date) AS Month,
       strftime('%d',line_item_usage_start_date) AS Day,
       line_item_usage_account_name AS Account,
       SUM(line_item_blended_cost) AS Cost,
       line_item_product_code AS Service
FROM aws
GROUP BY Day, Month, Year, Account, Service;
'''

cursor.execute(query)
results = cursor.fetchall()

aws_clean = pd.DataFrame(results, columns = ['Year','Month','Day','Account','Cost','Service'])

#Merging into one dataset

snow_clean['Platform'] = 'Snowflake'
gcp_clean['Platform'] = 'GCP'
aws_clean['Platform'] = 'AWS'

merged_df = pd.concat([snow_clean, gcp_clean, aws_clean]).reset_index(drop=True)

local_download_path = ''

merged_df.to_csv(local_download_path + 'agg.csv')

