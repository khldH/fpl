import pandas as pd
from pulp import LpMaximize, LpProblem, LpVariable, lpSum
import streamlit as st


def get_transfers_between_gwks(gw_picks_df, player_perf_df):
    changes = []
    events = []
    unique_events = gw_picks_df["event"].unique()
    unique_events.sort()

    for i in range(len(unique_events) - 1):
        event1 = unique_events[i]
        event2 = unique_events[i + 1]

        event1_elements = set(gw_picks_df[gw_picks_df["event"] == event1]["element"])
        event2_elements = set(gw_picks_df[gw_picks_df["event"] == event2]["element"])

        elements_added = event2_elements - event1_elements
        elements_removed = event1_elements - event2_elements

        added_elements = []
        for element in elements_added:
            total_points = player_perf_df[(player_perf_df["round"] == event2) & (player_perf_df["element"] == element)]["total_points"].sum()
            second_name = player_perf_df[(player_perf_df["round"] == event2) & (player_perf_df["element"] == element)]["web_name"].values[0]
            added_elements.append({"element": element, "total_points": total_points, "web_name": second_name})

        removed_elements = []
        for element in elements_removed:
            total_points = player_perf_df[(player_perf_df["round"] == event2) & (player_perf_df["element"] == element)]["total_points"].sum()
            second_name = player_perf_df[(player_perf_df["element"] == element)]["web_name"].values[0]
            removed_elements.append({"element": element, "total_points": total_points, "web_name": second_name})

        change = {
            "gw_from": event1,
            "gw_to": event2,
            "elements_added": added_elements,
            "elements_removed": removed_elements,
        }
        # for chip in chips:
        #     if chip['event'] == event2:
        #         print(chip)
        #         change['name'] = chip['name']
        #         print(change)
        #         break
        # else:
        #     change['name'] = None

        changes.append(change)

    return changes


def calculate_transfer_points_difference(data):
    result = {}

    for transfer in data:
        gw_to = int(transfer["gw_to"])
        total_points_in = sum(int(player["total_points"]) for player in transfer["elements_added"])
        total_points_out = sum(int(player["total_points"]) for player in transfer["elements_removed"])

        overall_diff_points = total_points_in - total_points_out
        result[gw_to] = overall_diff_points

    return result


def get_similar_players(df, reference_player):
    df['now_cost'] =  df['now_cost']/10
    if reference_player not in df['web_name'].values.tolist():
        st.write("make sure you provide the name of the player as it appears in your fantasy team")
        return
    _player = df[df['web_name'] == reference_player]#.iloc[0]
    st.write(_player[['web_name', 'now_cost', 'total_points']])

    # Filter out the reference player and players from different positions

    reference_player = df[df['web_name'] == reference_player].iloc[0]
    df_filtered = df[
        (df['web_name'] != reference_player['web_name']) & (df['singular_name'] == reference_player['singular_name'])]

    # Create a condition to compare players based on their stats and cost
    rating_threshold = reference_player['rating'] * 0.9
    condition = (df_filtered['rating'] >= rating_threshold) & \
                (df_filtered['start_cost'] < reference_player['start_cost'])

    # Sort the DataFrame based on the condition and select the top 5 players
    similar_players = df_filtered[condition].nlargest(5, 'rating')

    return similar_players[['web_name', 'now_cost', 'total_points','avg_fixture_difficulty_next_5_gwks']]


def find_best_player(df, web_name, money_in_the_bank=0.0):
    if web_name not in df['web_name'].values.tolist():
        st.write("make sure you provide the name of the player as it appears in your fantasy team")
        return
    player_df = df[df['web_name'] == web_name]
    position = player_df['singular_name'].values[0]
    cost = player_df['now_cost'].values[0]
    max_cost = cost + money_in_the_bank
    position_df = df[df['singular_name'] == position]
    # Create the linear programming problem
    prob = LpProblem(f"Best_{position}_Player_Selection", LpMaximize)

    # Decision variables for player selection and selected_by_percent minimization
    selected = LpVariable.dicts(f"{position}_selected", position_df['web_name'], cat='Binary')
    selected_by_percent = LpVariable(f"{position}_selected_by_percent", 0, 100,
                                     cat='Continuous')  # Minimize selected_by_percent

    # Objective function: maximize the rating of selected players
    prob += lpSum(selected[player] * position_df.loc[position_df.index[i], 'rating']
                  for i, player in enumerate(position_df['web_name']))

    # Constraint: select only one player from the given position
    prob += lpSum(selected[player] for player in position_df['web_name']) == 1

    # Constraint: limit total cost to be within the specified max_cost
    prob += lpSum(selected[player] * position_df.loc[position_df.index[i], 'start_cost']
                  for i, player in enumerate(position_df['web_name'])) <= max_cost

    # Constraint: minimize selected_by_percent for the selected player
    # prob += selected_by_percent == lpSum(selected[player] * position_df.loc[position_df.index[i], 'selected_by_percent']
    #                                      for i, player in enumerate(position_df['web_name']))

    # Solve the problem
    prob.solve()

    # Retrieve the best player for the given position and cost
    best_player = None
    for player in position_df['web_name']:
        if selected[player].value() == 1:
            best_player = position_df[position_df['web_name'] == player]  # .iloc[0]
            break

    return best_player[['web_name','team_name', 'now_cost','total_points','selected_by_percent','avg_fixture_difficulty_next_5_gwks']]
