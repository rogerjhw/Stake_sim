import streamlit as st
import pandas as pd
import random

# Constants
INITIAL_GLOBAL_RESERVE = 13400
RESERVE_INCREMENT = 134
MAX_OWNERSHIP_RATIO = 0.3
NUM_TEAMS = 134
INITIAL_SUPPLY_PER_TEAM = 100
INITIAL_CASH = 10000
CHURN_PROBABILITY = 0.10

st.set_page_config(layout="wide")
st.title("Stakeholder Token Market Simulator")

sim_days = st.sidebar.slider("Simulation Days", 10, 90, 30)
users_per_day = st.sidebar.slider("Users per Day", 1, 10, 5)
transaction_prob = st.sidebar.slider("Transaction Probability", 0.1, 1.0, 0.5)

if st.button("Run Simulation"):
    progress = st.progress(0)

    teams = [f"Team_{i}" for i in range(NUM_TEAMS)]
    influential = random.sample(range(NUM_TEAMS), 25)
    hot = random.sample(influential, 10)
    warm = [i for i in influential if i not in hot]

    weights = [1.0] * NUM_TEAMS
    for i in warm:
        weights[i] = 3.0
    for i in hot:
        weights[i] = 6.0
    weights = [w / sum(weights) for w in weights]

    base_prices = {}
    for i in range(NUM_TEAMS):
        if i in hot:
            base_prices[f"Team_{i}"] = 6.0
        elif i in warm:
            base_prices[f"Team_{i}"] = 2.0

    fixed_price_sum = sum(base_prices.values())
    remaining_teams = NUM_TEAMS - len(base_prices)
    remaining_total_value = NUM_TEAMS * 1.0 - fixed_price_sum
    remaining_price = remaining_total_value / remaining_teams

    for i in range(NUM_TEAMS):
        team = f"Team_{i}"
        if team not in base_prices:
            base_prices[team] = remaining_price

    users = []
    user_cash = {}
    user_tokens = pd.DataFrame(0, index=[], columns=teams)
    token_supply = pd.Series(INITIAL_SUPPLY_PER_TEAM, index=teams)
    global_reserve = INITIAL_GLOBAL_RESERVE
    reserve_buffer = 0.0
    total_fees_collected = 0.0
    last_filled_price = base_prices.copy()
    pending_burns = {team: 0 for team in teams}
    price_history = []
    supply_history = []
    reserve_history = []
    tx_log = []
    failed_tx_log = []
    lp_contributions = []

    def update_prices():
        prices = {}
        for team in teams:
            demand = user_tokens[team].sum()
            supply = token_supply[team]
            base = base_prices[team]
            ratio = demand / (supply + 1e-6)
            price = base * (1 + 0.5 * (ratio - 0.5))
            prices[team] = price
        raw = pd.Series(prices)
        cap = (raw * token_supply).sum()
        if cap > 0:
            raw *= global_reserve / cap
        return raw

    for day in range(sim_days):
        progress.progress((day + 1) / sim_days)

        if day % 7 == 0:
            trending_teams = random.sample(teams, 5)

        if (day + 1) % 30 == 0:
            lp_amount = 13400
            proportion = lp_amount / (global_reserve + 1e-6)
            lp_contributions.append((day+1, lp_amount, proportion, global_reserve))
            reserve_buffer += lp_amount

        for _ in range(users_per_day):
            u = f"user_{len(users)}"
            users.append(u)
            user_cash[u] = INITIAL_CASH
            user_tokens.loc[u] = 0

        prices = update_prices()

        for user in users:
            churn = random.random() < (CHURN_PROBABILITY / sim_days)
            if churn:
                for team in teams:
                    qty = user_tokens.loc[user, team]
                    if qty > 0:
                        payout = last_filled_price[team] * qty
                        user_cash[user] += payout
                        reserve_buffer -= payout
                        user_tokens.loc[user, team] = 0
                        tx_log.append((day+1, user, "churn_sell", team, qty, 0.0))
                continue

            if random.random() < transaction_prob:
                owned_teams = [team for team in teams if user_tokens.loc[user, team] > 0]
                possible_actions = ["buy"]
                if owned_teams:
                    possible_actions.append("sell")
                action = random.choice(possible_actions)

                current_weights = weights[:]
                for idx, team in enumerate(teams):
                    if team in trending_teams:
                        current_weights[idx] *= 8.0
                team_id = random.choices(range(NUM_TEAMS), weights=current_weights)[0]
                team = f"Team_{team_id}"
                price = prices[team]
                quantity = max(1, int(round(10 / price))) if action == "buy" else random.choice([1, 2, 5])
                total = price * quantity

                if action == "buy":
                    available = token_supply[team] - user_tokens[team].sum()
                    holding = user_tokens.loc[user, team]
                    max_allowed = MAX_OWNERSHIP_RATIO * token_supply[team]
                    if user_cash[user] >= total and available >= quantity and holding + quantity <= max_allowed:
                        fee = total * 0.0175
                        net = total - fee
                        user_cash[user] -= total
                        reserve_buffer += net
                        total_fees_collected += fee
                        user_tokens.loc[user, team] += quantity
                        last_filled_price[team] = price
                        tx_log.append((day+1, user, "buy", team, quantity, fee))
                    else:
                        failed_tx_log.append((day+1, user, "buy", team, quantity, "denied: constraints"))
                elif action == "sell":
                    if user_tokens.loc[user, team] >= quantity:
                        payout = last_filled_price[team] * quantity
                        user_cash[user] += payout
                        reserve_buffer -= payout
                        user_tokens.loc[user, team] -= quantity
                        tx_log.append((day+1, user, "sell", team, quantity, 0.0))
                    else:
                        failed_tx_log.append((day+1, user, "sell", team, quantity, "denied: insufficient holdings"))

        if abs(reserve_buffer) >= RESERVE_INCREMENT:
            steps = int(abs(reserve_buffer) // RESERVE_INCREMENT)
            direction = 1 if reserve_buffer > 0 else -1
            reserve_buffer -= direction * steps * RESERVE_INCREMENT
            global_reserve += direction * steps * RESERVE_INCREMENT
            for team in teams:
                if direction > 0:
                    offset = min(pending_burns[team], steps)
                    pending_burns[team] -= offset
                    token_supply[team] += (steps - offset)
                else:
                    unowned = token_supply[team] - user_tokens[team].sum()
                    if unowned > 0:
                        burnable = min(steps, unowned)
                        token_supply[team] -= burnable
                        pending_burns[team] += (steps - burnable)
                    else:
                        pending_burns[team] += steps

        price_history.append(update_prices())
        supply_history.append(token_supply.copy())
        reserve_history.append(global_reserve)

    st.subheader("Transaction Log")
    tx_df = pd.DataFrame(tx_log, columns=["Day", "User", "Action", "Team", "Quantity", "Fee"])
    st.dataframe(tx_df)

    st.subheader("Failed Transactions")
    failed_df = pd.DataFrame(failed_tx_log, columns=["Day", "User", "Action", "Team", "Quantity", "Reason"])
    st.dataframe(failed_df)

    st.subheader("Total Fees Collected")
    st.metric("Fees Collected (USD)", f"${total_fees_collected:,.2f}")

    st.subheader("LP Contributions")
    lp_df = pd.DataFrame(lp_contributions, columns=["Day", "Amount", "Proportional Pool Share at Entry", "Reserve at Entry"])
    st.dataframe(lp_df)

    st.subheader("LP Profit Summary")
    lp_profit = []
    if lp_contributions:
        for day, amount, proportion, entry_reserve in lp_contributions:
            exit_value = global_reserve * proportion
            profit = exit_value - amount
            lp_profit.append((day, amount, exit_value, profit))
        st.dataframe(pd.DataFrame(lp_profit, columns=["Day", "Deposit", "Value Now", "Profit"]))

    st.subheader("User Behavior Summary")
    if not tx_df.empty:
        user_volume = tx_df[tx_df["Action"] == "buy"].groupby("User")["Quantity"].sum()
        total_volume = user_volume.sum()
        st.metric("Total Buy Volume Over Period", f"{total_volume:.0f} tokens")

    price_df = pd.DataFrame(price_history)
    supply_df = pd.DataFrame(supply_history)
    reserve_df = pd.DataFrame(reserve_history, columns=["Global Reserve"])

    st.subheader("Select Teams to Visualize")
    default_selection = [f"Team_{i}" for i in hot + warm[:15]]
    selected_teams = st.multiselect("Choose teams", price_df.columns.tolist(), default=default_selection)

    st.subheader("Token Price Trends")
    st.line_chart(price_df[selected_teams])

    st.subheader("Token Supply Over Time")
    st.line_chart(supply_df[selected_teams])

    st.subheader("Global Reserve Over Time")
    st.line_chart(reserve_df)
