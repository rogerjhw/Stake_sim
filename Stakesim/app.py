import streamlit as st
from simulation import run_simulation
from visualization import show_simulation_summary, show_price_chart, show_available_supply_chart, visualize_price_with_volume
from trade_interface import trade_interface


st.set_page_config(layout="wide")
st.title("Stakeholder Token Market Simulator")

if "has_run" not in st.session_state:
    st.session_state["has_run"] = False

sim_days = st.sidebar.slider("Simulation Days", 10, 90, 30)
users_per_day = st.sidebar.slider("Users per Day", 1, 10, 5)
transaction_prob = st.sidebar.slider("Transaction Probability", 0.1, 1.0, 0.5)

if st.button("Run Simulation"):
    st.session_state["has_run"] = True
    st.session_state["results"] = run_simulation(sim_days, users_per_day, transaction_prob)

if st.session_state["has_run"]:
    tab1, tab2, tab3 = st.tabs(["Simulation Summary", "Token Price Chart", "User Interface"])
    with tab1:
        show_simulation_summary(st.session_state["results"])
    with tab2:
        show_price_chart(st.session_state["results"])
        show_available_supply_chart(st.session_state["results"])
        visualize_price_with_volume(st.session_state["results"])
    with tab3:
        trade_interface(st.session_state["results"])
    
