import time

import numpy as np
import pandas as pd

pd.set_option("display.max_rows", None)

import plotly.graph_objects as go
import streamlit as st

from data import (aggregate_total_points_for_dwg,
                  get_all_gw_picks_data_of_a_manager,
                  get_all_players_per_gw_data, get_data, merge_data,
                  prepare_player_data, read_in_all_players_gw_data)
from plotting import (player_form_guide, plot_captain_points,
                      plot_cumulative_points, plot_points_per_event,
                      plot_season_points, plot_tranfer_perf_per_gw)
from squad_management.squad_analysis import (
    calculate_transfer_points_difference, get_transfers_between_gwks, get_similar_players, find_best_player)
from squad_selection.optimiztion import (calculate_player_rating, select_squad,
                                         squad_selection_defence,
                                         squad_selection_forwards,
                                         squad_selection_gk,
                                         squad_selection_midfield)

st.set_option("deprecation.showPyplotGlobalUse", False)

st.set_page_config(
    layout="wide",
    initial_sidebar_state="expanded",
    page_title="FPL",
)


def create_card(value, caption, background_color="", text_color="black"):
    return f"""
        <div class="card" style="background-color: {background_color}; color: {text_color};">
            <div class="card-value">{value}</div>
            <div class="card-caption">{caption}</div>
        </div>
    """


st.markdown(
    """
    <style>
    .card-container {
        display: flex;
    }
    .card {
        padding: 10px;
        background-color: rgb(250, 250, 250);
        color: black;
        margin-right: 10px;
        font-size: 18px;
        font-weight: bold;
        border-radius: 5px;
        width: 120px;
        height: 120px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
    }
    .card-value {
        margin-bottom: 5px;
        text-align: center;
    }
    .card-caption {
        text-align: center;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def long_running_process():
    # Simulate a long-running process
    for i in range(4):
        time.sleep(1)


if __name__ == "__main__":
    # st.sidebar.title("Sidebar")
    # st.sidebar.subheader("FPL")
    # Add sidebar inputs option = st.sidebar.radio("Select an option", ["Overview", "Your team vs current champion",
    # "Your team vs any team "])
    # option = st.sidebar.radio("", ["Squad selection"])
    #
    # if option == "Squad selection":
    stats_df = pd.read_csv("FPLData/all_payer_per_gw_data.csv")
    stats_df["full_name"] = stats_df["first_name"] + " " + stats_df["second_name"]

    fw_df = stats_df[stats_df["singular_name"] == "Forward"]
    mid_df = stats_df[stats_df["singular_name"] == "Midfielder"]
    dif_df = stats_df[stats_df["singular_name"] == "Defender"]
    gk_df = stats_df[stats_df["singular_name"] == "Goalkeeper"]

    # with st.expander("Player performance: position break-down"):
    #
    #     col1, col2 = st.columns(2)
    #     with col1:
    #         st.write("Goalkeepers")
    #         st.dataframe(gk_df.groupby('full_name')['total_points'].sum().sort_values(ascending=False).rename(
    #             'total_points_scored').reset_index())
    #     with col2:
    #         st.write("Defenders")
    #         st.dataframe(dif_df.groupby('full_name')['total_points'].sum().sort_values(ascending=False).rename(
    #             'total_points_scored').reset_index())
    #
    #     col1, col2 = st.columns(2)
    #
    #     with col1:
    #         st.write("Midfielders")
    #         st.dataframe(mid_df.groupby('full_name')['total_points'].sum().sort_values(ascending=False).rename(
    #             'total_points_scored').reset_index())
    #     with col2:
    #         st.write("Forwards")
    #         st.dataframe(fw_df.groupby('full_name')['total_points'].sum().sort_values(ascending=False).rename(
    #             'total_points_scored').reset_index())

    # selected_player = st.selectbox("select player from the list", stats_df['full_name'].unique().tolist())

    st.subheader("Fantasy Premier League squad selection")
    st.write("---")
    st.write(
        "Set budgets for each position and an optimization algorithm will select the best squad that fits your "
        "allocated budgets "
    )
    st.markdown(
        "- Algorithm creates and optimizes a custom metric that combines all underlying player stats from last "
        "season"
    )
    st.markdown(
        "- Metric takes into account the fixture difficulty - uses the average fixture difficulty of the first "
        "5 gwks "
    )
    st.markdown(
        "- Player ownership (selected_by_percent) shown is updated in realtime as data is pulled life using " "FPL API"
    )
    st.markdown(
        "- Down below select two or more players and campare their form - form guide is caculated using "
        "rolling "
        "average of window 5 (gwks)"
    )
    st.write(
        "Limitations: new players that have joined the league are not included in squad selection since there's "
        "no data available for them "
    )
    st.write("---")

    fpl_players_data = prepare_player_data()
    fpl_players_data["rating"] = fpl_players_data.apply(calculate_player_rating, axis=1)
    # fpl_players_data = fpl_players_data[fpl_players_data["chance_of_playing_next_round"].isna()]
    # st.write(fpl_players_data.head(1).T)

    col1, col2, col3, col4 = st.columns(4)

    # Add input fields in each column
    with col1:
        fwds = st.text_input("Forwards budget", value=26)
        if len(fwds) == 0:
            fwds = 13.5
    with col2:
        mids = st.text_input("Midfielders budget", value=39)
        if len(mids) == 0:
            mids = 22.5

    with col3:
        defs = st.text_input("Defenders budget", value=27)
        if len(defs) == 0:
            defs = 20.0

    with col4:
        gks = st.text_input("Goalkeepers budget", value=9)
        if len(gks) == 0:
            gks = 8.0

    col1, col2 = st.columns(2)
    with col1:
        include = st.multiselect(
            "If you need to explicitly include player(s) in squad selection, choose from the list ",
            fpl_players_data["web_name"].unique().tolist(),
            default=["Haaland"],
        )
    with col2:
        exclude = st.multiselect(
            "If you need to explicitly exclude player(s) in squad selection, choose from the list ",
            fpl_players_data["web_name"].unique().tolist(),
            default="Toney",
        )
    st.write("---")

    if float(fwds) + float(mids) + float(defs) + float(gks) > 100:
        st.write(
            f"Your total budget of **{float(fwds) + float(mids) + float(defs) + float(gks)}** is above the allocated **100** for squad selection"
        )

    include_df = fpl_players_data[fpl_players_data["web_name"].isin(include)]
    exclude_df = fpl_players_data[fpl_players_data["web_name"].isin(exclude)]

    gk_list_include, def_list_include, mid_list_include, fwd_list_include = [
        include_df[include_df["pos"] == pos]["web_name"].tolist()
        for pos in ["Goalkeeper", "Defender", "Midfielder", "Forward"]
    ]
    gk_list_exclude, def_list_exclude, mid_list_exclude, fwd_list_exclude = [
        exclude_df[exclude_df["pos"] == pos]["web_name"].tolist()
        for pos in ["Goalkeeper", "Defender", "Midfielder", "Forward"]
    ]

    selected_fwds_df = squad_selection_forwards(
        df=fpl_players_data,
        total_cost=float(fwds),
        include_players=fwd_list_include,
        exclude_players=fwd_list_exclude,
    )
    selected_mids_df = squad_selection_midfield(
        df=fpl_players_data,
        total_cost=float(mids),
        include_players=mid_list_include,
        exclude_players=mid_list_exclude,
    )
    selected_defs_df = squad_selection_defence(
        df=fpl_players_data,
        total_cost=float(defs),
        include_players=def_list_include,
        exclude_players=def_list_exclude,
    )
    selected_gks_df = squad_selection_gk(
        df=fpl_players_data, total_cost=float(gks), include_players=gk_list_include, exclude_players=gk_list_exclude
    )
    try:
        with st.spinner("Squad selection in progess..."):
            long_running_process()

            # After the long process is done, remove the spinner and show the result
            st.success("Squad selection complete!")

            squad_df = pd.concat(
                [selected_gks_df, selected_defs_df, selected_mids_df, selected_fwds_df], ignore_index=True
            )
            st.write("Selected_squad")
            st.dataframe(squad_df.sort_values("pos"))
            st.write("Total cost of selected squad using allocated budgets :", squad_df["start_cost"].sum())
            st.write(f"Cost break down of selected squad per pos:")
            st.dataframe(squad_df.groupby("pos")["start_cost"].sum().rename("total_cost").reset_index())
    except Exception as e:
        print(e)
        st.write("an an expected error occurre...check your allocated budgets are within range")

    st.write("---")
    # st.write("Select squad without setting specific budgets for each pos")
    # if st.button('Click here to select squad!'):
    #     # Code to be executed when the button is clicked
    #     s,pts, p = squad_selected_df = select_squad(df=fpl_players_data)
    #     # st.write(f'Total cost of squad selected {squad_selected_df["start_cost"].sum()}')
    #     st.dataframe(p)

    # st.text("Form guide: compare form guide of two more players ")
    # st.write("Form guide is calculated using moving average of window 5 gwks")
    # selected_players = st.multiselect(
    #     "Select players to compare from the list",
    #     stats_df["full_name"].unique().tolist(),
    #     default=["Erling " "Haaland", "Harry Kane"],
    # )
    # if len(selected_players):
    #     st.plotly_chart(
    #         player_form_guide(stats_df[stats_df["full_name"].isin(selected_players)]), use_container_width=True
    #     )

    st.write("---")

    # st.text("Bonus: players with biggest total bonus points over the season - position break-down")

    #
    # if option == "Overview":

    fpl_manager_id = st.text_input(
        "Enter your team id:",
        max_chars=20,
        key="input",
        help="Get your team id from the URL when you check your gameweek points on the FPL website.",
    )
    if fpl_manager_id:
        url = f"https://fantasy.premierleague.com/api/entry/{fpl_manager_id}/history/"

        fpl_manager_gw_data = get_data(url)
        # Get all players' data
        players_fpl_stats = get_all_players_per_gw_data()
        # Get gameweek picks data for a specific player
        player_picks_data = get_all_gw_picks_data_of_a_manager(fpl_manager_id)

        final_df = merge_data(players_fpl_stats=players_fpl_stats, player_picks_data=player_picks_data)
        final_df = aggregate_total_points_for_dwg(final_df)

        if len(fpl_manager_gw_data):
            col1, col2 = st.columns(2)
            # with col1:
            st.subheader("Overview")
            total_points = fpl_manager_gw_data["current"][-1]["total_points"]
            overall_rank = np.round((fpl_manager_gw_data["current"][-1]["overall_rank"] / 9822586) * 100, 2)
            total_transfers = pd.DataFrame(fpl_manager_gw_data["current"])["event_transfers"].sum()
            total_points_on_bench = pd.DataFrame(fpl_manager_gw_data["current"])["points_on_bench"].sum()
            total_transfer_cost = pd.DataFrame(fpl_manager_gw_data["current"])["event_transfers_cost"].sum()
            avg_points_per_gw = np.round(total_points / len(fpl_manager_gw_data["current"]), 2)

            card_container = ""
            card_container += create_card(total_points, "Total points")
            card_container += create_card(avg_points_per_gw, "Average points per gw")
            card_container += create_card(overall_rank, "Overall rank %")
            card_container += create_card(
                total_points_on_bench, "Total points on bench", background_color="yellow", text_color="black"
            )
            card_container += create_card(total_transfers, "Total transfers")
            card_container += create_card(total_transfer_cost, "Total transfers cost", background_color="red")

            st.markdown(
                f"""
                <div class="card-container">
                    {card_container}

                """,
                unsafe_allow_html=True,
            )
            # with col2:
            st.write("---")
            st.write("Are your transfers working?")
            st.text("This doesn't take into account the hits you take if you make extra transfers")
            changes = get_transfers_between_gwks(final_df)
            diff_points_by_gw = calculate_transfer_points_difference(changes)
            st.plotly_chart(plot_tranfer_perf_per_gw(diff_points_by_gw))

            st.write(changes)
            # st.write(diff_points_by_gw)
            # st.empty()
                # st.plotly_chart(plot_season_points(fpl_history=fpl_manager_gw_data))
            st.write("---")
            st.subheader("Make better transfers")
            col1, col2 = st.columns(2)
            with col1:
                st.write("Get up to 5 players with similar performance but cheaper than a reference player")
                reference_player = st.text_input("Player name as it appears in your fantasy app/web", value='Salah')
                similar = get_similar_players(df=fpl_players_data, reference_player=reference_player)
                st.write("---")
                st.write(f"Players with similar performance as ***{reference_player}*** but cheaper")
                st.dataframe(similar)
            with col2:
                st.write("Get suggestions for a transfer")
                name = st.text_input("Player name as it appears in your fantasy app/web", value='Botman')
                money_in_bank = st.text_input("Money in your bank", value=0.0)
                transfer_in_suggested = find_best_player(df=fpl_players_data, web_name=name,
                                                         money_in_the_bank=float(money_in_bank))
                st.write("---")
                st.write(f"Best transfer to replace ***{name}***")
                st.dataframe(transfer_in_suggested)

            # with col1:
            # st.plotly_chart(plot_points_per_event(fpl_history=fpl_manager_gw_data))
            # # with col2:
            # st.plotly_chart(plot_cumulative_points(fpl_history=fpl_manager_gw_data))
            # st.write("---")
            # st.subheader("Player selection")
            # st.write(f"You have used a total of {final_df['element'].nunique()} players through the season")
            # col1, col2 = st.columns(2)
            # with col1:
            #     # with st.expander("points breakdown per player"):
            #     final_df["full_name"] = final_df["first_name"] + " " + final_df["second_name"]
            #     player_break_down_df = (
            #         final_df.groupby("full_name")["total_points"]
            #             .sum()
            #             .rename("Total Points")
            #             .rename_axis("Name")
            #             .astype(int)
            #             .reset_index()
            #             .sort_values(by="Total Points", ascending=True)
            #     )
            #     fig = go.Figure(go.Bar(
            #         x=player_break_down_df['Total Points'],
            #         y=player_break_down_df['Name'],
            #         orientation='h'
            #     ))
            #
            #     # Set the title and axis labels
            #     fig.update_layout(
            #         title='Points breakdown per player',
            #         xaxis_title='Total Points',
            #         yaxis_title='Name',
            #         height=1250,  # Set the height of the chart
            #         width=650  # Set the width of the chart
            #     )
            #     st.plotly_chart(fig)
            # with col2:
            #     # with st.expander("points breakdown per postion"):
            #     pos_df = (
            #         final_df.groupby("singular_name")["total_points"]
            #             .sum()
            #             .rename("Total Points")
            #             .astype(int)
            #             .rename_axis("Position")
            #             .reset_index()
            #             .sort_values(by="Total Points", ascending=True)
            #     )
            #     # pos_df = pos_df.rename_axis('Position')
            #     fig = go.Figure(go.Bar(
            #         x=pos_df['Total Points'],
            #         y=pos_df['Position'],
            #         orientation='h'
            #     ))
            #
            #     # Set the title and axis labels
            #     fig.update_layout(
            #         title='Points breakdown per position',
            #         xaxis_title='Total Points',
            #         yaxis_title='Position'
            #     )
            #     st.plotly_chart(fig)
            #     # st.table(pos_df)
            #
            # st.subheader("Performance of captain picks")
            # st.plotly_chart(plot_captain_points(final_df))

    else:
        st.write("enter the id of the team you want to anlayze")
