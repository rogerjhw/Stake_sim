import numpy as np
import pandas as pd
import random
from plotly.subplots import make_subplots
import plotly.graph_objects as go
from st_aggrid import AgGrid, GridOptionsBuilder
import streamlit as st
import os
import requests
import base64

daily_df = pd.read_csv('/Users/rogerwhite/Desktop/Stakeholder_data/Daily_AP_Votes_Data.csv')
conference_df = pd.read_csv('/Users/rogerwhite/Desktop/Stakeholder_data/Conference_Share_Per_Team_Per_Day.csv')
team_df = pd.read_csv('/Users/rogerwhite/Desktop/Stakeholder_data/teams.csv')

for index, row in team_df.iterrows():
  school = row['School'].lower()
  if school not in daily_df.columns:
    daily_df[school] = 0

def encode_image_to_base64(image_path):
    if os.path.exists(image_path):
        with open(image_path, "rb") as img_file:
            base64_string = base64.b64encode(img_file.read()).decode()
            return f"data:image/png;base64,{base64_string}"  # Add the required prefix
    return None
IMAGE_DIR = "images"

team_df['LogoPath'] = [os.path.join(IMAGE_DIR, f"logo_{i}.png") for i in range(len(team_df))]

reserve_pool = 13400
annual_yield = 0.04
annual_payout = reserve_pool*annual_yield



def get_team_prices(team, conference, vol=0.05, reanchor_interval=7, alpha=0.2, seed = 1234):
    """
    Generate token prices for a team using conference data, rolling averages, and random walk with re-anchoring.

    Parameters:
    team (str): Team name.
    conference (str): Conference name.
    vol (float): Volatility for random walk.
    reanchor_interval (int): Re-anchor interval in days.
    alpha (float): Weight for base price during re-anchoring.
    annual_payout (float): Annual payout value for scaling.

    Returns:
    pd.Series: Simulated random walk prices.
    """
    # Filter conference data
    np.random.seed(seed)

    conf_idx = conference_df['Conference'] == conference
    conf_df = conference_df[conf_idx]
    
    # Compute rolling averages for the conference
    conf_year_avg = conf_df['Conference_Share_Per_Team'].rolling(window=364, min_periods=1).mean()
    conf_share = (conf_year_avg) * annual_payout
    conf_price = (conf_share / 100) / 0.039  # Assuming annual yield of 3.9%

    # Compute rolling averages for the team
    week_avg = daily_df[team].rolling(window=42, center = False).mean()
    year_avg = daily_df[team].rolling(window=1092, center = False).mean()
    total_votes = daily_df['Total_Points'].rolling(window=21, center = False).mean()
    
    # Compute weekly and yearly prices
    weekly_share = (week_avg / total_votes) * annual_payout
    weekly_price = (weekly_share / 100) / 0.039
    yearly_share = (year_avg / total_votes) * annual_payout
    yearly_price = (yearly_share / 100) / 0.039
    
    # Combine prices
    price = (
        (yearly_price * 0.4) +
        (weekly_price * 0.4) +
        (conf_price.reset_index(drop=True) * 0.2) +
        0.1
    ).dropna()  # Drop any NaN values from the combined series
    
    # Ensure price is not empty
    if price.empty:
        raise ValueError("The calculated price series is empty. Check input data.")
    
    # Initialize random walk
    random_changes = np.random.uniform(-vol, vol, len(price))
    random_walk_prices = [price.iloc[0]]

    # Apply random walk with re-anchoring
    for i, change in enumerate(random_changes):
        next_price = random_walk_prices[-1] * (1 + change)
        if (i + 1) % reanchor_interval == 0:
            # Smooth re-anchor to the base price
            base_price = price.iloc[i]
            if not np.isnan(base_price):
                new_price = alpha * base_price + (1 - alpha) * next_price
            else:
                new_price = next_price  # Skip re-anchoring if base price is NaN
        else:
            new_price = next_price
        
        random_walk_prices.append(max(new_price, 0))  # Ensure price stays non-negative
    
    modeled_prices = pd.Series(random_walk_prices[1:], index=price.index)
    
    full_df = pd.DataFrame()
    full_df['Date'] = pd.to_datetime(daily_df['Date'])
    full_df['Price'] = modeled_prices
    full_df['Payout'] = (daily_df[team]/daily_df['Total_Points']*annual_payout)/100
    # Return as a Pandas Series aligned with the price index
    return full_df.dropna(how='any')

team_df['Price'] = 0

for index, row in team_df.iterrows():
  school = row['School'].lower()
  conf = row['Conference']
  price = get_team_prices(school, conf)['Price'].iloc[-1]
  per_yield = get_team_prices(school, conf)['Payout'].iloc[-1]/price
  team_df.at[index, 'Price'] = price
  team_df.at[index, 'Per Yield'] = per_yield

st.set_page_config(
    page_title="Admin Dashboard",
    page_icon="👨‍💻",
    layout="wide",
    initial_sidebar_state="expanded")


main_df = pd.DataFrame()
main_df['Team'] = team_df['School'] 
main_df['Logo'] = team_df['LogoPath']
main_df['Price'] = team_df['Price']
main_df['Per Yield'] = team_df['Per Yield']

main_df['Logo'] = main_df['Logo'].apply(
    lambda path: f'<img src="{encode_image_to_base64(path)}" width="50">' if encode_image_to_base64(path) else "No Image"
)

gb = GridOptionsBuilder.from_dataframe(main_df)

# Add custom cell renderer for the Logo column
# Add custom cell renderer for the Logo column
gb.configure_column(
    'Logo',
    cellRenderer="""
    function(params) {
        if (params.value && params.value.startsWith('<img')) {
            return params.value;  // Render image HTML
        } else {
            return '<div style="color: red; text-align: center;">No Image</div>';
        }
    }
    """
)

# Configure numeric columns with formatting
gb.configure_column('Price', type=["numericColumn"], precision=2)
gb.configure_column('Per Yield', type=["numericColumn"], precision=1)

# Build grid options
grid_options = gb.build()

# Display the AgGrid Table
st.title("Team Table with Local Logos")
AgGrid(main_df, gridOptions=grid_options, height=400, allow_unsafe_jscode=True, theme="material")