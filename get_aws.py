import boto3 #For accessing aws data
import os #For acccessing downloaded data
import pandas as pd #For cleaning data
from datetime import datetime #For ordering dates
import sqlite3 #For cleaning data
from collections import defaultdict #For cleaning data

#@title Configuring AWS credentials using boto3

temporary_credentials = {
    'aws_access_key_id': '',
    'aws_secret_access_key': '',
    'aws_session_token': ''
}

session = boto3.Session(
    aws_access_key_id=temporary_credentials['aws_access_key_id'],
    aws_secret_access_key=temporary_credentials['aws_secret_access_key'],
    aws_session_token=temporary_credentials['aws_session_token']
)

s3 = session.client('s3')

#Where the files will be downloaded to
local_download_path = ''

#Name of bucket with relevant data
bucket_name = 'datasociety-ops'

most_recent_day = []
months = []
most_recent_files_by_month = {}

response = s3.list_objects_v2(Bucket=bucket_name)

latest_dates = defaultdict(lambda: None)
date_times = []


for obj in response.get('Contents', [])[::-1]:
    
  key = obj['Key']
  date_str = key.split('/')[5][:13] 

  try:
    datetime = datetime.strptime(date_str, '%Y-%m-%dT%H')
  except Exception as e:
    print(e)
    continue
  date_times.append(datetime)

#Identifying relevant files

for dt in date_times:
    month_key = (dt.year, dt.month)
    if latest_dates[month_key] is None or dt > latest_dates[month_key]:
        latest_dates[month_key] = dt

# Convert datetime objects back to strings
latest_date_strings = [dt.strftime('%Y-%m-%dT%H') for dt in latest_dates.values()]

dataframes = {}

for obj in response.get('Contents', []):
  key = obj['Key']
  date_str = key.split('/')[5][:13] 
  
  if date_str in latest_date_strings:
    local_file_path = os.path.join(local_download_path, date_str + '.snappy.parquet')
    latest_date_strings.remove(date_str)
    
    s3.download_file(bucket_name, key, local_file_path)
    df = pd.read_parquet(local_file_path)
    dataframes[date_str] = df

pd.set_option('display.float_format', '{:.2f}'.format)
merged_df = pd.DataFrame()

for frame, key in zip(dataframes.values(), dataframes.keys()):
  merged_df = pd.concat([merged_df, frame], ignore_index=True)

merged_df.to_csv(local_download_path + 'Agg_aws.csv')