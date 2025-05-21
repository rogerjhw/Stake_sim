import pandas as pd
import random
import streamlit as st

# Constants
INITIAL_GLOBAL_RESERVE = 13400
RESERVE_INCREMENT = 134
MAX_OWNERSHIP_RATIO = 0.3
NUM_TEAMS = 134
INITIAL_SUPPLY_PER_TEAM = 100
INITIAL_CASH = 10000
CHURN_PROBABILITY = 0.10
MIN_PRICE = 0.01

def run_simulation(sim_days, users_per_day, transaction_prob):
    teams = [f"Team_{i}" for i in range(NUM_TEAMS)]

    # Assign tiered pricing
    hot_ids = random.sample(range(NUM_TEAMS), 10)
    warm_pool = [i for i in range(NUM_TEAMS) if i not in hot_ids]
    warm_ids = random.sample(warm_pool, 15)

    base_prices = {}
    for i in range(NUM_TEAMS):
        team = f"Team_{i}"
        if i in hot_ids:
            base_prices[team] = 6.0
        elif i in warm_ids:
            base_prices[team] = 2.0
        else:
            base_prices[team] = 0.40
    prices = pd.Series(base_prices)

    user_tokens = pd.DataFrame(0, index=[], columns=teams)
    token_supply = pd.Series(INITIAL_SUPPLY_PER_TEAM, index=teams)
    user_cash = {}
    users = []

    global_reserve = INITIAL_GLOBAL_RESERVE
    reserve_buffer = 0
    total_fees_collected = 0

    price_history, supply_history, reserve_history, user_holdings_history = [], [], [], []
    tx_log, failed_tx_log, lp_contributions = [], [], []
    buy_volume = {team: 0.0 for team in teams}
    mcap_history = []

    def rotate_hot_warm():
        nonlocal hot_ids, warm_ids
        cold_ids = [i for i in range(NUM_TEAMS) if i not in hot_ids and i not in warm_ids]

        if cold_ids:
            promoted_to_warm = random.choice(cold_ids)
            warm_ids.append(promoted_to_warm)

        if warm_ids:
            promoted_to_hot = random.choice(warm_ids)
            hot_ids.append(promoted_to_hot)
            warm_ids.remove(promoted_to_hot)

        if hot_ids:
            demoted_to_warm = random.choice(hot_ids)
            warm_ids.append(demoted_to_warm)
            hot_ids.remove(demoted_to_warm)

        if warm_ids:
            demoted_to_cold = random.choice(warm_ids)
            warm_ids.remove(demoted_to_cold)

    def apply_zero_sum_price_change(prices, target_team, direction, quantity):
        circulating = user_tokens[target_team].sum()
        available = max(token_supply[target_team] - circulating, 1e-6)
        scarcity_multiplier = 1 + (circulating / available)
        base_delta = 0.01 * quantity
        delta_price = base_delta * scarcity_multiplier if direction == "up" else -base_delta * scarcity_multiplier

        old_price = prices[target_team]
        new_price = max(old_price + delta_price, MIN_PRICE)
        delta_mc = (new_price - old_price) * token_supply[target_team]
        prices[target_team] = new_price

        if abs(delta_mc) < 1e-6:
            return prices

        others = [t for t in teams if t != target_team]
        total_supply_others = token_supply[others].sum()
        for t in others:
            share = token_supply[t] / total_supply_others if total_supply_others > 0 else 1 / len(others)
            adjustment = -delta_mc * share / token_supply[t]
            prices[t] = max(prices[t] + adjustment, MIN_PRICE)

        return prices

    progress = st.progress(0)

    for day in range(sim_days):
        progress.progress((day + 1) / sim_days)

        if day % 7 == 0:
            rotate_hot_warm()

        if (day + 1) % 30 == 0:
            lp_amount = 13400
            proportion = lp_amount / (global_reserve + 1e-6)
            lp_contributions.append((day + 1, lp_amount, proportion, global_reserve))
            reserve_buffer += lp_amount

        for _ in range(users_per_day):
            user = f"user_{len(users)}"
            users.append(user)
            user_cash[user] = INITIAL_CASH
            user_tokens.loc[user] = 0

        for user in users:
            churn = random.random() < (CHURN_PROBABILITY / sim_days)
            if churn:
                for team in teams:
                    qty = user_tokens.loc[user, team]
                    if qty > 0:
                        payout = prices[team] * qty
                        user_cash[user] += payout
                        reserve_buffer -= payout
                        user_tokens.loc[user, team] = 0
                        tx_log.append((day + 1, user, "churn_sell", team, qty, 0.0))
                continue

            if random.random() < transaction_prob:
                owned = [t for t in teams if user_tokens.loc[user, t] > 0]
                if owned and random.random() < 0.5:
                    team = random.choice(owned)
                    price = prices[team]
                    quantity = min(user_tokens.loc[user, team], random.choice([1, 2, 5]))
                    payout = price * quantity
                    user_cash[user] += payout
                    reserve_buffer -= payout
                    user_tokens.loc[user, team] -= quantity
                    tx_log.append((day + 1, user, "sell", team, quantity, 0.0))
                    prices = apply_zero_sum_price_change(prices, team, "down", quantity)
                else:
                    weights = [3 if f"Team_{i}" in [f"Team_{j}" for j in warm_ids]
                               else 6 if f"Team_{i}" in [f"Team_{j}" for j in hot_ids] else 1 for i in range(NUM_TEAMS)]
                    team_id = random.choices(range(NUM_TEAMS), weights=weights)[0]
                    team = f"Team_{team_id}"
                    price = max(prices[team], MIN_PRICE)
                    quantity = max(1, int(round(10 / price)))
                    total = price * quantity

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
                        buy_volume[team] += price * quantity
                        tx_log.append((day + 1, user, "buy", team, quantity, fee))
                        prices = apply_zero_sum_price_change(prices, team, "up", quantity)
                    else:
                        reason = (
                            "insufficient funds" if user_cash[user] < total else
                            "supply constraint" if available < quantity else
                            "whale constraint"
                        )
                        failed_tx_log.append((day + 1, user, "buy", team, quantity, reason))

        while abs(reserve_buffer) >= RESERVE_INCREMENT:
            if reserve_buffer > 0:
                for team in teams:
                    token_supply[team] += 1
                global_reserve += RESERVE_INCREMENT
                reserve_buffer -= RESERVE_INCREMENT
            else:
                for team in teams:
                    if token_supply[team] > user_tokens[team].sum():
                        token_supply[team] -= 1
                global_reserve -= RESERVE_INCREMENT
                reserve_buffer += RESERVE_INCREMENT

        price_history.append(prices.copy())
        supply_history.append(token_supply.copy())
        reserve_history.append(global_reserve)
        user_holdings_history.append(user_tokens.sum().copy())
        total_market_cap = (prices * token_supply).sum()
        mcap_history.append((day + 1, total_market_cap, global_reserve))

    st.subheader("Market Cap vs Reserve Over Time")
    mcap_df = pd.DataFrame(mcap_history, columns=["Day", "Market Cap", "Global Reserve"])
    st.line_chart(mcap_df.set_index("Day"))

    return {
        "price_df": pd.DataFrame(price_history),
        "supply_df": pd.DataFrame(supply_history),
        "reserve_df": pd.DataFrame(reserve_history, columns=["Global Reserve"]),
        "user_holdings_df": pd.DataFrame(user_holdings_history),
        "tx_log": tx_log,
        "failed_tx_log": failed_tx_log,
        "lp_contributions": lp_contributions,
        "user_tokens": user_tokens,
        "total_fees": total_fees_collected,
        "global_reserve": global_reserve,
        "final_prices": prices.copy(),
        "final_supply": token_supply.copy(),
        "buy_volume": buy_volume
    }
