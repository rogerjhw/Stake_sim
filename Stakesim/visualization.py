import streamlit as st
import pandas as pd
import plotly.graph_objects as go

def show_simulation_summary(results):
    col1, _ = st.columns([1, 1])  # 1/3 width chart
    with col1:
        st.markdown("**Transaction Log**")
        st.dataframe(pd.DataFrame(results["tx_log"], columns=["Day", "User", "Action", "Team", "Quantity", "Fee", "Nominal Value"]))
    
        st.markdown("**Failed Transactions**")
        st.dataframe(pd.DataFrame(results["failed_tx_log"], columns=["Day", "User", "Action", "Team", "Quantity", "Reason"]))
    
    
        st.markdown("**LP Contributions**")
        st.dataframe(pd.DataFrame(results["lp_contributions"], columns=["Day", "Amount", "Proportional Pool Share at Entry", "Reserve at Entry"]))
    
        st.markdown("**End of Simulation Market Overview**")
        final_prices = results["price_df"].iloc[-1]
        final_supply = results["supply_df"].iloc[-1]
        final_holdings = results["user_tokens"].sum()
        available_supply = final_supply - final_holdings
        market_df = pd.DataFrame({"Final Price": final_prices, "Available Supply": available_supply})
        st.dataframe(market_df.sort_values("Final Price", ascending=False))

def show_price_chart(results, token):
    col1, _ = st.columns([1, 1])  # 1/3 width chart
   
    with col1:
        st.markdown('**Token price**')
        
        token_to_plot = token
        col1, _ = st.columns([1, 2])  # 1/3 width chart
        
        container = st.container(border = True)
        container.line_chart(results["price_df"][token_to_plot])

def show_mcap(results):
    col1, _ = st.columns([1, 1])  # 1/3 width chart
   
    with col1:
        st.markdown("**Mcap vs Reserve pool**")
        container = st.container(border = True)
        container.line_chart(results['mcap_df'].set_index("Day"))
        

def show_available_supply_chart(results, token):
    col1, _ = st.columns([1, 1])  # 1/3 width chart
   
    with col1:
        st.markdown('**Available token supply**')
        available_over_time = results["supply_df"][token] - results["user_holdings_df"][token]
        container = st.container(border = True)
        container.line_chart(available_over_time)

def visualize_price_with_volume(results, token):
    
    #st.subheader("📊 Token Price vs Trade Volume")

    price_df = results["price_df"]
    tx_df = pd.DataFrame(results["tx_log"], columns=["Day", "User", "Action", "Team", "Quantity", "Fee", "Nominal Value"])


    # Filter transactions for selected team
    team_tx = tx_df[tx_df["Team"] == token]

    # Group volume by day and action
    daily_volume = team_tx.groupby(["Day", "Action"])["Quantity"].sum().unstack(fill_value=0)

    # Align with price data
    daily_price = price_df[token]

    fig = go.Figure()

    # Line chart for price
    fig.add_trace(go.Scatter(
        x=daily_price.index,
        y=daily_price.values,
        mode="lines",
        name="Price",
        yaxis="y1",
        line=dict(width=4)
    ))

    # Stacked bar for buys and sells
    if "buy" in daily_volume:
        fig.add_trace(go.Bar(
            x=daily_volume.index,
            y=daily_volume["buy"],
            name="Buys",
            yaxis="y2",
            marker_color="green",
            opacity=0.6
        ))

    if "sell" in daily_volume:
        fig.add_trace(go.Bar(
            x=daily_volume.index,
            y=daily_volume["sell"],
            name="Sells",
            yaxis="y2",
            marker_color="red",
            opacity=0.6
        ))

    fig.update_layout(
        title=f"{token} price and volume",
        xaxis=dict(title="Day"),
        yaxis=dict(title="Token Price", side="left"),
        yaxis2=dict(title="Trade Volume", overlaying="y", side="right", showgrid=False),
        barmode="stack"
    )
     
    col1, _ = st.columns([1, 1])  # 1/3 width chart
   
    with col1:
        container = st.container(border = True)
        container.plotly_chart(fig, use_container_width=True)

def show_all_prices_chart(results):

    price_df = results["price_df"]

    fig = go.Figure()
    for team in price_df.columns:
        fig.add_trace(go.Scatter(
            x=price_df.index,
            y=price_df[team],
            mode="lines",
            name=team,
            line=dict(width=2),
            opacity=0.6
        ))

    fig.update_layout(
        xaxis_title="Day",
        yaxis_title="Price (USD)",
        showlegend=False,
        height=500,
        title = 'All token prices'
    )
    
    col1, _ = st.columns([1, 1])  # 1/3 width chart
   
    with col1:
        container = st.container(border = True)
        container.plotly_chart(fig, use_container_width=False)
