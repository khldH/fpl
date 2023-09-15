import ast
import datetime

import altair as alt
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st


# def plot_points_per_event(fpl_history):
#     df = pd.DataFrame(fpl_history["current"])
#     # df['points'] = np.where(df['points'] == 0, df['points'].expanding().mean(), df['points'])
#
#     chips_df = pd.DataFrame(fpl_history["chips"])
#     chip_events = chips_df["event"].tolist()
#     chip_names = chips_df["name"].tolist()
#
#     line_chart = (
#         alt.Chart(df)
#             .mark_line()
#             .encode(x=alt.X("event", axis=alt.Axis(labelAngle=0), title="Gameweek"), y="points")
#             .properties(width=800)
#     )
#
#     chip_points = (
#         alt.Chart(chips_df)
#             .mark_circle(size=100)
#             .encode(
#             x="event:Q",
#             y="points:Q",
#             color=alt.Color("name:N", legend=alt.Legend(title="Chip Name")),
#             tooltip=["name:N"],
#         )
#             .properties(title="Chips")
#     )
#
#     chart = line_chart + chip_points
#
#     chart.configure_legend(
#         strokeColor="gray",
#         fillColor="#EEEEEE",
#         padding=10,
#         cornerRadius=10,
#         titleColor="black",
#         titleFontSize=12,
#         labelFontSize=12,
#         labelLimit=0,
#         labelOffset=10,
#     )
#
#     chart.title = "Points per gameweek"
#
#     return chart


def plot_points_per_event(fpl_history):
    df = pd.DataFrame(fpl_history["current"])
    events_url = "https://fantasy.premierleague.com/api/bootstrap-static/"
    events_data = requests.get(events_url).json()
    events_df = pd.DataFrame(events_data["events"])
    chips_df = pd.DataFrame(fpl_history["chips"])

    # Create a line plot for points per gameweek
    line_trace = go.Scatter(x=df["event"], y=df["points"], mode="lines", name="Manager's points per Gameweek")

    # Create a line plot for average entry score
    avg_score_trace = go.Scatter(
        x=events_df["id"], y=events_df["average_entry_score"], mode="lines", name="Average Entry Score"
    )

    # Create a line plot for highest score
    highest_score_trace = go.Scatter(
        x=events_df["id"], y=events_df["highest_score"], mode="lines", name="Highest Score"
    )

    # Create scatter plots for chip events
    chip_traces = []
    for idx, row in chips_df.iterrows():
        event = row["event"]
        chip_name = row["name"]
        chip_points = df.loc[df["event"] == event, "points"].values[0]
        chip_trace = go.Scatter(
            x=[event],
            y=[chip_points],
            mode="markers+text",
            name=chip_name,
            text=[chip_name],
            textposition="top center",
            marker=dict(size=10, line=dict(width=1), symbol="circle"),
        )
        chip_traces.append(chip_trace)

    data = [line_trace, avg_score_trace, highest_score_trace] + chip_traces
    # data = [line_trace] + chip_traces

    # Set layout properties
    layout = go.Layout(
        title="Game week points vs Average entry score vs Highest score per game week",
        xaxis=dict(title="Gameweek", tickmode="linear", dtick=1),
        yaxis=dict(title="Points"),
        showlegend=True,
        width=1000,  # Increase figure width
        height=600,  # Increase figure height
    )

    # Create the figure and display it
    fig = go.Figure(data=data, layout=layout)
    return fig


def plot_cumulative_points(fpl_history):
    df = pd.DataFrame(fpl_history["current"])

    # Calculate cumulative points per gameweek
    df["cumulative_points"] = df["points"].cumsum()

    df.loc[df.index[-1], "cumulative_points"] -= df["event_transfers_cost"].sum()

    # Create a line plot for cumulative points per gameweek
    cumulative_trace = go.Scatter(x=df["event"], y=df["cumulative_points"], mode="lines", name="Cumulative Points")

    data = [cumulative_trace]

    # Set layout properties
    layout = go.Layout(
        title="Cumulative Points per Gameweek",
        xaxis=dict(title="Gameweek", tickmode="linear", dtick=1),
        yaxis=dict(title="Cumulative Points"),
        showlegend=True,
        width=800,
        height=500,
    )

    # Create the figure and display it
    fig = go.Figure(data=data, layout=layout)
    return fig


# def plot_season_points(fpl_history):
#     # Create a DataFrame from the data
#     df = pd.DataFrame(fpl_history["past"])
#
#     # Create the line chart using Altair
#     chart = (
#         alt.Chart(df)
#             .mark_line()
#             .encode(x="season_name", y="total_points", tooltip=["season_name", "total_points"])
#             .properties(title="Total points per season", width=600, height=400)
#     )
#
#     return chart


def plot_season_points(fpl_history):
    # Create a DataFrame from the data
    df = pd.DataFrame(fpl_history["past"])
    last_season_df = pd.DataFrame(fpl_history["current"])
    last_season_points = last_season_df["points"].sum() - last_season_df["event_transfers_cost"].sum()
    season_name = str(datetime.datetime.today().year - 1) + "/" + str(datetime.datetime.today().year).split("0")[1]
    _df = pd.DataFrame({"season_name": [season_name], "total_points": [last_season_points]})

    df = pd.concat([df, _df])
    # Create the line chart using Plotly
    fig = go.Figure(data=go.Scatter(x=df["season_name"], y=df["total_points"], mode="lines+markers"))
    fig.update_layout(
        title="Total points per season",
        xaxis=dict(title="Season"),
        yaxis=dict(title="Total Points", range=[100, df["total_points"].max()]),
        # height= 600
    )

    # fig.update_traces(marker=dict(size=8), textfont=dict(size=12))

    return fig


def plot_captain_points(df):
    # Filter the DataFrame to get data only for the captain
    captain_df = df[df["is_captain"]]

    # Adjust the marker size based on total points
    captain_df["total_points"] = captain_df["total_points"] * captain_df["multiplier"]
    marker_size = captain_df["total_points"] / 10
    marker_size = marker_size + 0.6  # Increase the marker size for all points

    # Create a scatter plot for captain's points per event
    scatter_trace = go.Scatter(
        x=captain_df["event"],
        y=captain_df["total_points"],
        mode="markers+text",
        text=captain_df["second_name"],
        textposition="top center",
        marker=dict(
            size=marker_size,
            sizemode="area",
            sizeref=0.009,
            line=dict(width=1),
            symbol="circle",
            color=[
                "rgb(44, 160, 44)" if multiplier == 3 else "rgb(31, 119, 180)"
                for multiplier in captain_df["multiplier"]
            ],
        ),
        name="Captain Points",
    )

    # Set layout properties
    layout = go.Layout(
        title="Captain Points per Gameweek",
        xaxis=dict(title="Gameweek", dtick=1),
        yaxis=dict(title="Points"),
        showlegend=False,
        width=1000,  # Increase figure width
        height=600,
    )

    # Find the event with multiplier 3
    event_with_multiplier_3 = captain_df[captain_df["multiplier"] == 3]["event"].values[0]

    # Add an annotation for the event with multiplier 3
    annotation = go.layout.Annotation(
        x=event_with_multiplier_3,
        y=captain_df.loc[captain_df["event"] == event_with_multiplier_3, "total_points"].values[0],
        text="3xC",
        showarrow=False,
        arrowhead=7,
        ax=0,
        ay=-40,
    )

    layout.annotations = [annotation]

    # Create the figure
    fig = go.Figure(data=[scatter_trace], layout=layout)

    return fig


def player_form_guide(df):
    df = df.sort_values("round")

    # Calculate the rolling average of points scored for each player on a 5-gameweek interval
    form_df = pd.DataFrame()
    for n in df["full_name"].unique():
        df_p = df[df["full_name"] == n]
        df_p["form_guide"] = df_p.groupby("second_name")["total_points"].rolling(window=5, min_periods=3).mean().values
        form_df = pd.concat([df_p, form_df])

    # st.write(form_df['form_guide'])

    # Plot the form guide for each player using Plotly
    last_gameweek = form_df["round"].max()

    # Plot the form guide for each player using Plotly
    fig = px.line(
        form_df,
        x="round",
        y="form_guide",
        color="second_name",
        title="Player form guide from last season - moving avg of points scored (5 gw window)",
    )
    fig.update_layout(
        xaxis_title="Gameweek",
        yaxis_title="Form Guide",
        xaxis=dict(range=[1, last_gameweek]),
        # width=1000,
        # height=600
    )

    return fig


def plot_tranfer_perf_per_gw(data):
    # Separate the data into gameweeks and transfers
    gameweeks = list(data.keys())
    transfers = list(data.values())

    # Determine the colors based on the transfer values
    colors = ['green' if t >= 0 else 'red' for t in transfers]

    # Create a DataFrame for plotting
    df = pd.DataFrame({'Gameweek': gameweeks, 'points_diff': transfers, 'Color': colors})

    # Create a bar chart using Plotly
    fig = px.bar(
        df,
        x='Gameweek',
        y='points_diff',
        text='points_diff',
        color='Color',
        color_discrete_map={'green': 'green', 'red': 'red'},
        # showlegend=False,
        title='Transfer performance: points difference between players brought in and players sold in the gw',
    )

    fig.update_xaxes(showline=True, showticklabels=True, dtick=1)
    fig.update_yaxes(showline=True, showticklabels=True, dtick=1)
    fig.update_layout(showlegend=False)

    return fig
