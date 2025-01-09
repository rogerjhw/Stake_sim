import streamlit as st 
import os
import pandas as pd
from datetime import datetime
import plotly.express as px

st.set_page_config(
    page_title="Operational Cost Dashboard",
    page_icon="👨‍💻",
    layout="wide",
    initial_sidebar_state="expanded")

now = datetime.now()
first_of_january = datetime(now.year, 1, 1)
days_difference = (now - first_of_january).days

st.title('Operational Cost Dashboard')

col = st.columns((2.0, 4.5, 2), gap='medium')

date_range = 7

with col[0]:
   range_option = st.selectbox('Date Range',('Last 7 Days','Last 30 Days','YTD'))

if range_option == 'Last 30 Days':
   date_range = 30

if range_option == 'YTD':
   date_range = days_difference

df = pd.read_csv('/Users/rogerwhite/Desktop/Operational_Cost_Analysis/all_cost_data.csv')
df.drop(['Unnamed: 0'], axis = 1,inplace = True)

df['Date'] = pd.to_datetime(df[['Year', 'Month', 'Day']])
df = df.sort_values('Date')

sub_df = df[df['Date'] < '07-01-2024']

latest_date = sub_df['Date'].max()
last_14_days = sub_df[sub_df['Date'] >= (latest_date - pd.Timedelta(days=(date_range*2)))]

last_7_days = last_14_days[last_14_days['Date'] > (latest_date - pd.Timedelta(days=date_range))]
previous_7_days = last_14_days[last_14_days['Date'] <= (latest_date - pd.Timedelta(days=date_range))]

# Calculate the total expenses for each period
all_last_7_days_expense = last_7_days['Cost'].sum()
all_previous_7_days_expense = previous_7_days['Cost'].sum()
all_difference = ((all_last_7_days_expense - all_previous_7_days_expense) / all_previous_7_days_expense) * 100 if all_previous_7_days_expense != 0 else float('inf')

comparison = {
    'Last 7 Days Expense': all_last_7_days_expense,
    'Previous 7 Days Expense': all_previous_7_days_expense,
    'Difference': all_last_7_days_expense - all_previous_7_days_expense,
    'Percentage Change': ((all_last_7_days_expense - all_previous_7_days_expense) / all_previous_7_days_expense) * 100 if all_previous_7_days_expense != 0 else float('inf')
}

platform_comparison = {}

# Iterate through each platform
for platform in sub_df['Platform'].unique():
    platform_data = last_14_days[last_14_days['Platform'] == platform]

    # Calculate expenses for the last seven days and the previous seven days for the current platform
    last_7_days = platform_data[platform_data['Date'] > (latest_date - pd.Timedelta(days=date_range))]
    previous_7_days = platform_data[platform_data['Date'] <= (latest_date - pd.Timedelta(days=date_range))]

    last_7_days_expense = last_7_days['Cost'].sum()
    previous_7_days_expense = previous_7_days['Cost'].sum()

    # Calculate the difference and percentage change
    difference = last_7_days_expense - previous_7_days_expense
    percentage_change = ((difference / previous_7_days_expense) * 100) if previous_7_days_expense != 0 else float('inf')

    # Store the results in the dictionary
    platform_comparison[platform] = {
        'Last 7 Days Expense': last_7_days_expense,
        'Previous 7 Days Expense': previous_7_days_expense,
        'Difference': difference,
        'Percentage Change': percentage_change
    }

# Account comparisons

account_comparison = {}
acc_df = pd.DataFrame()

# Iterate through each platform
for account in sub_df['Account'].unique():
    account_data = last_14_days[last_14_days['Account'] == account]
    
    if account_data.empty:
        continue
    else:
      platform = account_data['Platform'].iloc[0]
      # Calculate expenses for the last seven days and the previous seven days for the current platform
      last_7_days = account_data[account_data['Date'] > (latest_date - pd.Timedelta(days=date_range))]
      previous_7_days = account_data[account_data['Date'] <= (latest_date - pd.Timedelta(days=date_range))]

      acc_last_7_days_expense = last_7_days['Cost'].sum()
      acc_previous_7_days_expense = previous_7_days['Cost'].sum()

      # Calculate the difference and percentage change
      acc_difference = acc_last_7_days_expense - acc_previous_7_days_expense
      acc_percentage_change = ((acc_difference / acc_previous_7_days_expense) * 100) if acc_previous_7_days_expense != 0 else float('inf')

      # Store the results in the dictionary
      account_comparison[account] = {
          'Platform': platform,
          'Last 7 Days Expense': acc_last_7_days_expense,
          'Previous 7 Days Expense': acc_previous_7_days_expense,
          'Difference': acc_difference,
          'Percentage Change': acc_percentage_change
      }

accounts = []
platforms = []
last_7_days_expenses = []
previous_7_days_expenses = []
differences = []
percentage_changes = []


for account in account_comparison:
  accounts.append(account)
  platforms.append(account_comparison[account]['Platform'])
  last_7_days_expenses.append(round(account_comparison[account]['Last 7 Days Expense'],2))
  previous_7_days_expenses.append(round(account_comparison[account]['Previous 7 Days Expense'],2))
  differences.append(round(account_comparison[account]['Percentage Change'],2))

acc_df['Account'] = accounts
acc_df['Platform'] = platforms
acc_df[f'Last {date_range} Days Expense'] = last_7_days_expenses
acc_df[f'Previous {date_range} Days Expense'] = previous_7_days_expenses
acc_df['Difference (%)'] = differences

acc_df_sorted = acc_df.sort_values(f'Last {date_range} Days Expense', ascending = False).reset_index(drop = True)
acc_df_sorted.index.name = '#'

sub_df['Week'] = sub_df['Date'].dt.to_period('W').apply(lambda r: r.start_time)
weekly_spending = sub_df.groupby(['Platform', 'Week']).agg({'Cost': 'sum'}).reset_index()

fig = px.line(weekly_spending, x='Week', y='Cost', color='Platform', title='Weekly Spending by Platform', line_shape= 'spline')
fig.update_layout(
    xaxis_title='Week',
    yaxis_title='Cost',
    title='Weekly Spending by Platform'
)

platforms = list(sub_df['Platform'].unique())[::-1]

with col[0]:
    if range_option == 'YTD':
       container = st.container(border=True)
       container.metric(label = f'YTD Spending', value = '$' + f'{all_last_7_days_expense:,.2f}')
       container = st.container(border=True)
       aws_cost = round(platform_comparison['AWS']['Last 7 Days Expense'],2)
       container.metric(label = 'AWS',  value = f'$ {aws_cost:,.2f}')
       gcp_cost = round(platform_comparison['GCP']['Last 7 Days Expense'],2)
       container.metric(label = 'GCP',  value = f'$ {gcp_cost:,.2f}')
       snow_cost = round(platform_comparison['Snowflake']['Last 7 Days Expense'],2)
       container.metric(label = 'Snowflake',  value = f'$ {snow_cost:,.2f}')
    else:
       aws_cost = round(platform_comparison['AWS']['Last 7 Days Expense'],2)
       gcp_cost = round(platform_comparison['GCP']['Last 7 Days Expense'],2)
       snow_cost = round(platform_comparison['Snowflake']['Last 7 Days Expense'],2)

       container = st.container(border=True)
       container.metric(label = f'Last {date_range} Days of Spending', value = '$' + f'{all_last_7_days_expense:,.2f}', delta = str(round(all_difference,1)) + '%', delta_color = 'inverse')
       container = st.container(border=True)
       container.metric(label = 'AWS',  value = f'$ {aws_cost:,.2f}', delta = str(round(platform_comparison['AWS']['Percentage Change'],1)) + '%', delta_color = 'inverse' )
       container.metric(label = 'GCP',  value = f'$ {gcp_cost:,.2f}', delta = str(round(platform_comparison['GCP']['Percentage Change'],1)) + '%', delta_color = 'inverse' )
       container.metric(label = 'Snowflake',  value = f'$ {snow_cost:,.2f}', delta = str(round(platform_comparison['Snowflake']['Percentage Change'],1)) + '%', delta_color = 'inverse' )
    st.dataframe(acc_df_sorted)

with col[1]:
    container = st.container(border=True)
    container.plotly_chart(fig)
    option = st.selectbox('Platform', (platforms))
    container = st.container(border = True)

    platform_df = pd.DataFrame(sub_df[sub_df['Platform'] == option].groupby('Service')['Cost'].sum()).sort_values('Cost', ascending = False)
    fig_2 = px.bar(platform_df, x = platform_df.index, y = 'Cost', title = 'Spending by Service')
    container.plotly_chart(fig_2)

anomaly_counts = sub_df['Anomaly'].value_counts()

accounts = list(sub_df['Account'].unique())


with col[2]:
   option = st.selectbox('Account',(accounts))

   acc_df = sub_df[sub_df['Account'] == option].reset_index(drop = True)
   platform = acc_df['Platform'][0]
   if len(list(acc_df['Anomaly'].value_counts())) == 1:
      anomaly_count = 0
   else:
      anomaly_count = list(acc_df['Anomaly'].value_counts())[1]
    
   acc_df['Anomaly'].replace(-1, 'Anomalous', inplace = True)
   acc_df['Anomaly'].replace(1, 'Normal', inplace = True)

   container = st.container(border = True)
   container.metric(label = 'Anomaly Count', value = anomaly_count)
   
   fig = px.scatter(acc_df, x = 'Cost', y = 'Service', color = 'Anomaly')
   fig.update_layout(
        legend_title_text='Type of Expense',
        title=dict(
            text=f'{platform} {option} Account Anomalous Expenses',
            x=0.0,
            y=0.95,
            font=dict(
                family="Arial",
                size=10,
                color='#000000'
            )))
   container = st.container(border = True)
   container.plotly_chart(fig)

   anom_df = acc_df[acc_df['Anomaly'] == 'Anomalous'].reset_index(drop=True)
   anom_df['Date'] = [str(date).split(' ')[0] for date in anom_df['Date']]



   if len(anom_df) > 0:
      st.write(f'###### Anomalies for {option}')
      st.dataframe(anom_df[['Cost','Date','Service']])
   else:
      st.write('###### No anomalies were identified')   





