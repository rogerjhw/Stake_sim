import streamlit as st
import pandas as pd

def trade_interface(results):
    st.subheader("📊 Post-Simulation Token Trading")

    if "user_cash" not in st.session_state:
        st.session_state["user_cash"] = 1000.0
    if "user_holdings" not in st.session_state:
        st.session_state["user_holdings"] = pd.Series(0, index=results["final_prices"].index)
    if "global_holdings" not in st.session_state:
        st.session_state["global_holdings"] = results["user_tokens"].sum().copy()
    if "dynamic_prices" not in st.session_state:
        st.session_state["dynamic_prices"] = results["final_prices"].copy()
    if "supply" not in st.session_state:
        st.session_state["supply"] = results["final_supply"].copy()

    user_cash = st.session_state["user_cash"]
    user_holdings = st.session_state["user_holdings"]
    global_holdings = st.session_state["global_holdings"]
    prices = st.session_state["dynamic_prices"]
    supply = st.session_state["supply"]

    st.markdown(f"**Available Cash:** ${user_cash:,.2f}")
    st.dataframe(user_holdings.rename("Your Holdings"))

    team = st.selectbox("Select Team", prices.index.tolist())
    action = st.radio("Action", ["Buy", "Sell"])
    quantity = st.number_input("Quantity", min_value=1, value=1, step=1)

    price = prices[team]
    total_cost = quantity * price

    st.markdown(f"**Price per Token:** ${price:.2f}")
    st.markdown(f"**Total {'Cost' if action == 'Buy' else 'Payout'}:** ${total_cost:.2f}")

    def recalculate_prices():
        new_prices = {}
        scarcity_multiplier = 3
        epsilon = 1e-6
        for t in prices.index:
            held = global_holdings[t]
            available = supply[t] - held
            base = results["price_df"].iloc[0][t] if not results["price_df"].empty else 1.0
            scarcity_ratio = available / (held + epsilon)
            scarcity_penalty = max(0, scarcity_multiplier * (1 - scarcity_ratio))
            price = base * (1 + scarcity_penalty)
            new_prices[t] = price

        # Scale prices to match reserve backing
        global_reserve = results["global_reserve"]
        total_supply = supply
        raw = pd.Series(new_prices)
        cap = (raw * total_supply).sum()
        if cap > 0:
            raw *= global_reserve / cap
        return raw

    if st.button("Execute Trade"):
        if action == "Buy":
            if user_cash >= total_cost:
                user_cash -= total_cost
                user_holdings[team] += quantity
                global_holdings[team] += quantity
                st.success(f"Purchased {quantity} {team} tokens for ${total_cost:.2f}")
            else:
                st.error("Insufficient funds.")
        elif action == "Sell":
            if user_holdings[team] >= quantity:
                user_cash += total_cost
                user_holdings[team] -= quantity
                global_holdings[team] -= quantity
                st.success(f"Sold {quantity} {team} tokens for ${total_cost:.2f}")
            else:
                st.error("You don't own that many tokens.")

        st.session_state["user_cash"] = user_cash
        st.session_state["user_holdings"] = user_holdings
        st.session_state["global_holdings"] = global_holdings
        st.session_state["dynamic_prices"] = recalculate_prices()
        st.rerun()

