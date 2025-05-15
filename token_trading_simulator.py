
import streamlit as st
import pandas as pd

# Constants
INITIAL_GLOBAL_RESERVE = 13400
TOKENS_PER_DOLLAR = 1 / 134
RESERVE_INCREMENT = 134
MAX_OWNERSHIP_RATIO = 0.3

# Initialize session state
if "users" not in st.session_state:
    NUM_TEAMS = 134
    NUM_USERS = 5
    INITIAL_CASH = 10000

    st.session_state.teams = [f"Team_{i}" for i in range(NUM_TEAMS)]
    st.session_state.users = [f"User_{i}" for i in range(NUM_USERS)]
    st.session_state.token_supply = pd.Series(100.0, index=st.session_state.teams)
    st.session_state.global_reserve = INITIAL_GLOBAL_RESERVE
    st.session_state.reserve_buffer = 0.0
    st.session_state.user_cash = pd.Series(INITIAL_CASH, index=st.session_state.users)
    st.session_state.user_tokens = pd.DataFrame(0, index=st.session_state.users, columns=st.session_state.teams)
    st.session_state.transactions = []
    st.session_state.last_filled_price = {team: 1.0 for team in st.session_state.teams}
    st.session_state.pending_burns = {team: 0 for team in st.session_state.teams}

# AMM price function based on demand ratio
def update_prices():
    prices = {}
    for team in st.session_state.teams:
        supply = st.session_state.token_supply[team]
        demand = st.session_state.user_tokens[team].sum()
        demand_ratio = demand / (supply + 1e-6)
        price = 1.0 * (1 + 0.5 * (demand_ratio - 0.5))
        prices[team] = price
    raw_prices = pd.Series(prices)
    market_cap = (raw_prices * st.session_state.token_supply).sum()
    if market_cap > 0:
        raw_prices *= st.session_state.global_reserve / market_cap
    return raw_prices

st.title("Stakeholder Token Trading Simulator")
st.session_state.token_prices = update_prices()

# UI Controls
st.sidebar.header("Trade")
selected_user = st.sidebar.selectbox("User", st.session_state.users)
action = st.sidebar.radio("Action", ["Buy", "Sell"])
selected_team = st.sidebar.selectbox("Team", st.session_state.teams)
price = st.session_state.token_prices[selected_team]
st.sidebar.write(f"Price: ${price:.2f}")
quantity = st.sidebar.number_input("Quantity", min_value=1, step=1, value=1)

# Execute trade
if st.sidebar.button("Execute Trade"):
    total_price = price * quantity

    if action == "Buy":
        available_supply = st.session_state.token_supply[selected_team] - st.session_state.user_tokens[selected_team].sum()
        current_holdings = st.session_state.user_tokens.loc[selected_user, selected_team]
        max_allowed = MAX_OWNERSHIP_RATIO * st.session_state.token_supply[selected_team]

        if st.session_state.user_cash[selected_user] < total_price:
            st.error("Insufficient funds.")
        elif available_supply < quantity:
            st.error("Not enough supply.")
        elif current_holdings + quantity > max_allowed:
            st.error("Cannot exceed 30% ownership.")
        else:
            st.session_state.user_cash[selected_user] -= total_price
            st.session_state.user_tokens.loc[selected_user, selected_team] += quantity
            st.session_state.reserve_buffer += total_price
            st.session_state.last_filled_price[selected_team] = price
            for _ in range(quantity):
                st.session_state.transactions.append((selected_user, "buy", selected_team, price))
            st.success(f"{selected_user} bought {quantity} {selected_team} tokens at ${price:.2f}")

    elif action == "Sell":
        if st.session_state.user_tokens.loc[selected_user, selected_team] < quantity:
            st.error("Insufficient tokens.")
        else:
            sell_price = st.session_state.last_filled_price[selected_team]
            payout = sell_price * quantity
            st.session_state.user_cash[selected_user] += payout
            st.session_state.user_tokens.loc[selected_user, selected_team] -= quantity
            st.session_state.reserve_buffer -= payout
            for _ in range(quantity):
                st.session_state.transactions.append((selected_user, "sell", selected_team, sell_price))
            st.success(f"{selected_user} sold {quantity} {selected_team} tokens at ${sell_price:.2f}")

    # Reserve-based mint/burn
    if abs(st.session_state.reserve_buffer) >= RESERVE_INCREMENT:
        steps = int(abs(st.session_state.reserve_buffer) // RESERVE_INCREMENT)
        direction = 1 if st.session_state.reserve_buffer > 0 else -1
        st.session_state.reserve_buffer -= direction * steps * RESERVE_INCREMENT
        st.session_state.global_reserve += direction * steps * RESERVE_INCREMENT
        for team in st.session_state.teams:
            if direction > 0:
                burn_offset = min(st.session_state.pending_burns[team], steps)
                st.session_state.pending_burns[team] -= burn_offset
                st.session_state.token_supply[team] += (steps - burn_offset)
            else:
                available = st.session_state.token_supply[team] - st.session_state.user_tokens[team].sum()
                if available > 0:
                    burnable = min(steps, available)
                    st.session_state.token_supply[team] -= burnable
                    st.session_state.pending_burns[team] += (steps - burnable)
                else:
                    st.session_state.pending_burns[team] += steps

    st.session_state.token_prices = update_prices()

# UI Display
st.subheader("User Cash")
st.dataframe(st.session_state.user_cash)

st.subheader("User Holdings")
st.dataframe(st.session_state.user_tokens)

st.subheader("Token Supply")
st.dataframe(st.session_state.token_supply)

st.subheader("Pending Burns")
st.dataframe(pd.Series(st.session_state.pending_burns))

st.subheader("Prices")
st.dataframe(st.session_state.token_prices)

st.subheader("Transactions")
log_df = pd.DataFrame(st.session_state.transactions, columns=["User", "Action", "Team", "Price"])
st.dataframe(log_df)

st.sidebar.markdown(f"**Reserve:** ${st.session_state.global_reserve:.2f}")
st.sidebar.markdown(f"**Buffer:** ${st.session_state.reserve_buffer:.2f}")
st.sidebar.markdown(f"**Market Cap:** ${(st.session_state.token_prices * st.session_state.token_supply).sum():.2f}")

if st.button("Reset"):
    st.session_state.clear()
    st.experimental_rerun()
