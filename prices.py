import pandas as pd

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



