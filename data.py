import json

import pandas as pd
import requests
import streamlit as st


def get_data(url):
    response = requests.get(url)
    if response.status_code == 200:
        # Parse the response content as JSON
        json_data = json.loads(response.content)
        return json_data
    else:
        print("Failed to retrieve the JSON data.")
        return {}


# @st.cache_data
# def get_all_players_gw_data():
#     # Get data from the main URL
#     main_url = "https://fantasy.premierleague.com/api/bootstrap-static/"
#     response = requests.get(main_url)
#
#     if response.status_code == 200:
#         data = response.json()
#         players = data["elements"]
#
#         all_data_dfs = []  # List to store DataFrames for each player
#
#         # Get player data using individual API links
#         for player in players:
#             player_id = player["id"]
#             url = f"https://fantasy.premierleague.com/api/element-summary/{player_id}/"
#             response = requests.get(url)
#
#             if response.status_code == 200:
#                 player_data = response.json()
#                 history_data = player_data["history"]
#                 df = pd.DataFrame(history_data)
#                 all_data_dfs.append(df)
#
#         # Concatenate all player DataFrames into a single DataFrame
#         final_df = pd.concat(all_data_dfs, ignore_index=True)
#
#         return final_df
#
#     return None


@st.cache_data
def get_all_players_per_gw_data():
    # Get data from the main URL
    main_url = "https://fantasy.premierleague.com/api/bootstrap-static/"
    response = requests.get(main_url)

    if response.status_code == 200:
        data = response.json()
        elements = data["elements"]
        element_df = pd.DataFrame(elements)

        element_types = data["element_types"]
        element_types_df = pd.DataFrame(element_types)

        teams = data["teams"]
        teams_df = pd.DataFrame(teams)

        all_data_dfs = []  # List to store DataFrames for each player

        # Get player data using individual API links
        for player in elements:
            player_id = player["id"]
            url = f"https://fantasy.premierleague.com/api/element-summary/{player_id}/"
            response = requests.get(url)

            if response.status_code == 200:
                player_data = response.json()
                history_data = player_data["history"]

                # Create a DataFrame from the history data
                df = pd.DataFrame(history_data)

                # Merge the history DataFrame with the elements DataFrame based on 'element' ID
                df = df.merge(
                    element_df[["id", "first_name", "second_name", "element_type", "team_code"]],
                    left_on="element",
                    right_on="id",
                )

                # Merge the history DataFrame with the element_types DataFrame based on 'element_type' ID
                df = df.merge(element_types_df[["id", "singular_name"]], left_on="element_type", right_on="id")

                # Merge the history DataFrame with the teams DataFrame based on 'team' ID
                df = df.merge(teams_df[["code", "name"]], left_on="team_code", right_on="code")

                all_data_dfs.append(df)

        # Concatenate all player DataFrames into a single DataFrame
        players_df = pd.concat(all_data_dfs, ignore_index=True)

        players_df.to_csv("FPLDATA/all_payer_per_gw_data.csv")

        return players_df

    return None


@st.cache_data
def get_all_gw_picks_data_of_a_manager(manager_id):
    base_url = f"https://fantasy.premierleague.com/api/entry/{manager_id}/event/{{}}/picks/"
    game_weeks = range(1, 39)  # GW 1 to 38
    all_data_dfs = []  # List to store DataFrames for each GW

    for gw in game_weeks:
        url = base_url.format(gw)
        response = requests.get(url)

        if response.status_code == 200:
            gw_data = response.json()
            event = gw_data["entry_history"]["event"]
            gw_picks = gw_data["picks"]
            gw_df = pd.DataFrame(gw_picks)
            gw_df["event"] = event
            all_data_dfs.append(gw_df)

    # Concatenate all GW DataFrames into a single DataFrame
    picks_df = pd.concat(all_data_dfs, ignore_index=True)

    return picks_df


@st.cache_data
def get_all_players_info():
    url = "https://fantasy.premierleague.com/api/bootstrap-static/"
    response = requests.get(url)
    if response.status_code == 200:
        # Parse the response content as JSON
        json_data = json.loads(response.content)

        # Extract the 'element_types' information
        element_types = json_data["element_types"]
        element_types_df = pd.json_normalize(element_types)

        # Extract the 'elements' information
        elements = json_data["elements"]
        elements_df = pd.json_normalize(elements)

        # Extract the 'teams' information
        teams = json_data["teams"]
        teams_df = pd.json_normalize(teams)

        # Merge the 'elements' and 'element_types' DataFrames based on the common 'element_type' field
        merged_df = elements_df.merge(element_types_df, left_on="element_type", right_on="id")

        # Merge the merged DataFrame with the 'teams' DataFrame based on the common 'team_code' field
        final_df = merged_df.merge(teams_df, left_on="team_code", right_on="code")

        return final_df
    else:
        print("Failed to retrieve the JSON data.")
        return {}


import pandas as pd


def aggregate_total_points_for_dwg(df):
    # Sort the DataFrame by 'id' and 'event'
    df_sorted = df.sort_values(["element", "event"])

    # Calculate the sum of 'total_points' per 'id' and 'event'
    df["sum_total_points"] = df.groupby(["element", "event"])["total_points"].transform("sum")

    # Create a mask to filter out duplicate rows
    mask = df.duplicated(subset=["element", "event"])

    # Select the unique rows based on the mask
    unique_rows = df[~mask]

    # Drop the 'total_points' column from the unique rows
    unique_rows = unique_rows.drop("total_points", axis=1)

    # Rename the 'sum_total_points' column to 'total_points'
    unique_rows = unique_rows.rename(columns={"sum_total_points": "total_points"})

    # Reset the index of the unique rows
    unique_rows = unique_rows.reset_index(drop=True)

    return unique_rows


@st.cache_data
def read_in_all_players_gw_data():
    try:
        df = pd.read_csv("FPLData/all_payer_per_gw_data.csv")
        return df
    except Exception as e:
        print(e)
        return pd.DataFrame()


def merge_data(players_fpl_stats, player_picks_data):
    final_df = players_fpl_stats.merge(
        player_picks_data, left_on=["element", "round"], right_on=["element", "event"], how="right"
    )
    return final_df


# @st.cache_data
def prepare_player_data():
    main_url = "https://fantasy.premierleague.com/api/bootstrap-static/"
    response = requests.get(main_url)
    # Extract the dataframes from the data_dict
    if response.status_code == 200:
        data_dict = response.json()
        elements_df = pd.DataFrame(data_dict["elements"])
        element_types_df = pd.DataFrame(data_dict["element_types"])
        teams_df = pd.DataFrame(data_dict["teams"])

        # Merge elements_df with element_types_df
        merged_df = pd.merge(elements_df, element_types_df, how="inner", left_on="element_type", right_on="id")
        merged_df["pos"] = merged_df["singular_name"]

        # Merge the result with teams_df
        merged_df = pd.merge(merged_df, teams_df, how="inner", left_on="team_code", right_on="code")
        merged_df["team_name"] = merged_df["name"]

        # Calculate start_cost and full_name
        merged_df["start_cost"] = merged_df["now_cost"] / 10
        merged_df["full_name"] = merged_df["first_name"] + " " + merged_df["second_name"]

        # Initialize a list to store the average fixture difficulties for each player
        avg_fixture_difficulties = []

        # Iterate over each player to fetch fixture data and calculate average fixture difficulties
        for player in data_dict["elements"]:
            player_id = player["id"]
            url = f"https://fantasy.premierleague.com/api/element-summary/{player_id}/"
            response = requests.get(url)
            player_data = response.json()
            fixtures = player_data["fixtures"]

            # Initialize a list to store fixture difficulties for each window
            fixture_difficulties_window = []
            gameweeks_not_finished = 0

            # Iterate over the fixtures to calculate average fixture difficulty for the first 5 gameweeks that are not
            # finished
            for fixture in fixtures:
                if not fixture["finished"]:
                    fixture_difficulty = fixture["difficulty"]
                    fixture_difficulties_window.append(fixture_difficulty)
                    gameweeks_not_finished += 1

                if gameweeks_not_finished >= 5:
                    break

            # Calculate the overall average fixture difficulty for the player
            avg_fixture_difficulty = sum(fixture_difficulties_window) / len(fixture_difficulties_window)
            avg_fixture_difficulties.append(avg_fixture_difficulty)

        # Add the average fixture difficulties to the merged_df dataframe
        merged_df["avg_fixture_difficulty_first_5_gwks"] = avg_fixture_difficulties

        # Convert necessary columns to numeric data types and fill NaN values with zeros
        numeric_columns = [
            "total_points",
            "starts",
            "bonus",
            "bps",
            "influence",
            "threat",
            "ict_index",
            "creativity",
            "clean_sheets",
            "avg_fixture_difficulty_first_5_gwks",
            "selected_by_percent",
        ]
        merged_df[numeric_columns] = merged_df[numeric_columns].apply(pd.to_numeric, errors="coerce").fillna(0)

        return merged_df
    return []
