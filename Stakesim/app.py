import streamlit as st
if "results" not in st.session_state:
    st.session_state["results"] = None

from simulation import run_simulation
from visualization import show_simulation_summary, show_price_chart, show_available_supply_chart, visualize_price_with_volume, show_all_prices_chart, show_mcap
from trade_interface import trade_interface

logo = 'stakesim_logo.png'
st.set_page_config(layout="wide")
st.markdown("**Start sim** ⬇️")


if "has_run" not in st.session_state:
    st.session_state["has_run"] = False


with st.sidebar:
    st.logo(logo)
    st.markdown('**Sim params**')
    st.markdown('Set the rules of the sandbox')
    container = st.container(border = True)
    
    with container:
        expand = st.expander('Sim length', icon = '🕒')
        expand.markdown("""Choose length of simulation""")
        sim_days = container.slider('Days',10, 90, 30)

        expand = st.expander('User growth', icon = '📈')
        expand.markdown("""Choose how many users join per day""")
        users_per_day = container.slider("Users", 1, 10, 5)

        expand = st.expander('Transactions per user', icon = '💸')
        expand.markdown("""Choose the probability of a user buying or selling on any given day""")
        transaction_prob = container.slider("Probability", 0.1, 1.0, 0.5)

if st.button("Run Simulation"):
    st.session_state["has_run"] = True
    st.session_state["results"] = run_simulation(sim_days, users_per_day, transaction_prob)

if st.session_state["results"] is not None:
    tab1, tab2, tab3 = st.tabs(["Simulation Summary", "Token Price Chart", "User Interface"])
    with tab1:
        active_users = st.session_state['results']["active_users_30d"]
        average_30d_volume_per_user = st.session_state['results']['avg_volume_per_user_30d']
        annualized_revenue = ((active_users*average_30d_volume_per_user)*0.0175)*12
        
        col1, col2,_ = st.columns([0.5, 0.5,1])  # 1/3 width chart
        
        with col1:
            container = st.container(border = True)
            container.metric("Active users (at end of period)", active_users)
            container.metric("Avg volume per active user", f"${average_30d_volume_per_user:.2f}")
            container.metric("Fees collected (USD)", f"${st.session_state['results']['total_fees']:,.2f}")
            container.metric("Annualized transaction revenue", f"${annualized_revenue:,.2f}")



        show_mcap(st.session_state['results'])
        show_simulation_summary(st.session_state["results"])
        show_all_prices_chart(st.session_state["results"])
    with tab2:
        col1, _ = st.columns([1, 1])  # 1/3 width chart
        with col1: 
            token_to_plot = st.selectbox("Choose a team to plot", st.session_state['results']["price_df"].columns.tolist())
        show_price_chart(st.session_state["results"], token_to_plot)
        show_available_supply_chart(st.session_state["results"], token_to_plot)
        visualize_price_with_volume(st.session_state["results"], token_to_plot)
    with tab3:
        trade_interface(st.session_state["results"])
    
