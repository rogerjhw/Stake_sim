import subprocess
from datetime import datetime as dt

now = dt.now()

current_year = str(now.year)
current_month = now.strftime("%m")

bucket_uri = f'datasociety-ops/aws-billing-exports//all_billing_data/data/BILLING_PERIOD={current_year}-{current_month}/'

result = subprocess.run(
    ['aws', 's3', 'ls', bucket_uri, '--recursive'],
    capture_output=True,
    text=True,
    check=True
)

output_lines = result.stdout.strip().split('\n')

files = []
for line in output_lines:
    parts = line.split()
    if len(parts) >= 4:
        file_path = ' '.join(parts[3:])
        files.append(file_path)

rel_file_path = files[-1]

local_download_path = '/Users/rogerwhite/Desktop/Operational_Cost_Analysis/rel_file.parquet'
subprocess.run(['aws','s3','cp', f's3://datasociety-ops/{rel_file_path}', local_download_path])