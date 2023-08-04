from pulp import LpMaximize, LpProblem, LpVariable, lpSum, value


# Define the composite score function with weights for each position and column
def calculate_player_rating(row):
    if row["singular_name"] == "Forward":
        return (
            (row["total_points"])
            + (3.0 * row["expected_goal_involvements_per_90"])
            + (2.5 * row["penalties_order"])
            + (2.0 * row["starts"])
            + (1.5 * row["bonus"])
            + (1.2 * row["bps"])
            + (1.1 * row["direct_freekicks_order"])
            + (0.9 * row["influence"])
            + (0.7 * row["threat"])
            - (7.5 * row["avg_fixture_difficulty_first_5_gwks"])
        )
    elif row["singular_name"] == "Midfielder":
        return (
            (row["total_points"])
            + (3.0 * row["expected_goal_involvements_per_90"])
            + (2.5 * row["penalties_order"])
            + (2.0 * row["starts"])
            + (1.5 * row["bonus"])
            + (1.2 * row["bps"])
            + (1.1 * row["direct_freekicks_order"])
            + (0.9 * row["influence"])
            + -(7.5 * row["avg_fixture_difficulty_first_5_gwks"])
        )
    elif row["singular_name"] == "Defender":
        return (
            (row["total_points"])
            + (3.0 * row["expected_goal_involvements_per_90"])
            + (2.5 * row["penalties_order"])
            + (2.0 * row["starts"])
            + (1.5 * row["bonus"])
            + (1.2 * row["bps"])
            + (3 * row["clean_sheets"])
            + (1.1 * row["direct_freekicks_order"])
            - (7.5 * row["avg_fixture_difficulty_first_5_gwks"])
        )
    elif row["singular_name"] == "Goalkeeper":
        return (
            (row["total_points"])
            + (2.0 * row["starts"])
            + (1.3 * row["saves_per_90"])
            + (1.5 * row["bonus"])
            + (1.2 * row["bps"])
            + (5 * row["clean_sheets"])
            - (7.5 * row["avg_fixture_difficulty_first_5_gwks"])
        )
    else:
        return 0


def squad_selection_forwards(df, total_cost, include_players=None, exclude_players=None):
    df = df[df["singular_name"] == "Forward"]
    if total_cost < (df["start_cost"].min() * 3):
        total_cost = df["start_cost"].min() * 3
        include_players = None

    # Create the linear programming problem
    prob = LpProblem("PlayerSelection", LpMaximize)

    # Decision variables
    selected = LpVariable.dicts("selected", df["web_name"], cat="Binary")

    # Additional decision variable for average_fixture_difficulty
    # avg_fixture_difficulty = LpVariable("avg_fixture_difficulty")

    # Objective function
    prob += lpSum(selected[player] * df.loc[df.index[i], "rating"] for i, player in enumerate(df["web_name"]))

    # # Additional objective term for minimizing avg_fixture_difficulty
    # prob += -1 * avg_fixture_difficulty

    # Constraints
    prob += lpSum(selected[player] for player in df["web_name"]) == 3
    prob += (
        lpSum(selected[player] * df.loc[df.index[i], "start_cost"] for i, player in enumerate(df["web_name"]))
        <= total_cost
    )

    # Include specified players (if any)
    if include_players:
        prob += lpSum(selected[player] for player in include_players) == len(include_players)

    # Exclude specified players (if any)
    if exclude_players:
        prob += lpSum(selected[player] for player in exclude_players) == 0

    # Solve the problem

    prob.solve()

    # Retrieve the solution
    status = prob.status
    if status == -1:
        print(f"Failed!!.. exactly 3 forwards must be selected... set budget accordingly")
        return []
    total_points = value(prob.objective)
    selected_players = [player for player in df["web_name"] if selected[player].value() == 1]
    selected_players_df = df[df["web_name"].isin(selected_players)][
        ["full_name", "pos", "team_name", "start_cost", "avg_fixture_difficulty_first_5_gwks", "selected_by_percent"]
    ]
    # selected_players_df.rename(columns={"name":"team"},inplace= True)
    return selected_players_df


def squad_selection_midfield(df, total_cost, include_players=None, exclude_players=None):
    df = df[df["singular_name"] == "Midfielder"]
    if total_cost < (df["start_cost"].min() * 5):
        total_cost = df["start_cost"].min() * 5
        include_players = None
    # Create the linear programming problem
    prob = LpProblem("PlayerSelection", LpMaximize)

    # Decision variables
    selected = LpVariable.dicts("selected", df["web_name"], cat="Binary")

    # Additional decision variables for team count
    team_count = LpVariable.dicts("team_count", set(df["team"]), lowBound=0, upBound=1, cat="Integer")

    # Objective function
    prob += lpSum(selected[player] * df.loc[df.index[i], "rating"] for i, player in enumerate(df["web_name"]))

    # Constraints
    prob += lpSum(selected[player] for player in df["web_name"]) == 5
    prob += (
        lpSum(selected[player] * df.loc[df.index[i], "start_cost"] for i, player in enumerate(df["web_name"]))
        <= total_cost
    )

    # Constraint: No more than 2 players from the same team
    for team in set(df["team"]):
        prob += lpSum(selected[player] for player in df[df["team"] == team]["web_name"]) <= team_count[team]

    # Include specified players (if any)
    if include_players:
        prob += lpSum(selected[player] for player in include_players) == len(include_players)

    # Exclude specified players (if any)
    if exclude_players:
        prob += lpSum(selected[player] for player in exclude_players) == 0
    # Solve the problem
    prob.solve()

    # Retrieve the solution
    status = prob.status
    if status == -1:
        print(f"Failed!!.. exactly 5 midfielders must be selected... set budget accordingly")
        return []
    total_points = value(prob.objective)
    selected_players = [player for player in df["web_name"] if selected[player].value() == 1]
    selected_players_df = df[df["web_name"].isin(selected_players)][
        ["full_name", "pos", "team_name", "start_cost", "avg_fixture_difficulty_first_5_gwks", "selected_by_percent"]
    ]
    # selected_players_df.rename(columns={"name": "team"}, inplace=True)
    return selected_players_df


def squad_selection_defence(df, total_cost, include_players=None, exclude_players=None):
    df = df[df["singular_name"] == "Defender"]
    if total_cost < (df["start_cost"].min() * 5):
        total_cost = df["start_cost"].min() * 5
        include_players = None
    # Create the linear programming problem
    prob = LpProblem("PlayerSelection", LpMaximize)

    # Decision variables
    selected = LpVariable.dicts("selected", df["web_name"], cat="Binary")

    # Additional decision variables for team count
    team_count = LpVariable.dicts("team_count", set(df["team"]), lowBound=0, upBound=1, cat="Integer")

    # Objective function
    prob += lpSum(selected[player] * df.loc[df.index[i], "rating"] for i, player in enumerate(df["web_name"]))

    # Constraints
    prob += lpSum(selected[player] for player in df["web_name"]) == 5
    prob += (
        lpSum(selected[player] * df.loc[df.index[i], "start_cost"] for i, player in enumerate(df["web_name"]))
        <= total_cost
    )

    # Constraint: No more than 2 players from the same team
    for team in set(df["team"]):
        prob += lpSum(selected[player] for player in df[df["team"] == team]["web_name"]) <= team_count[team]

    # Include specified players (if any)
    if include_players:
        prob += lpSum(selected[player] for player in include_players) == len(include_players)

    # Exclude specified players (if any)
    if exclude_players:
        prob += lpSum(selected[player] for player in exclude_players) == 0

    # Solve the problem
    prob.solve()

    # Retrieve the solution
    status = prob.status
    if status == -1:
        print(f"Failed!!.. exactly 5 defenders must be selected... set budget accordingly")
        return []
    total_points = value(prob.objective)
    selected_players = [player for player in df["web_name"] if selected[player].value() == 1]
    selected_players_df = df[df["web_name"].isin(selected_players)][
        ["full_name", "pos", "team_name", "start_cost", "avg_fixture_difficulty_first_5_gwks", "selected_by_percent"]
    ]
    # selected_players_df.rename(columns={"name": "team"}, inplace=True)
    return selected_players_df


def squad_selection_gk(df, total_cost, include_players=None, exclude_players=None):
    df = df[df["singular_name"] == "Goalkeeper"]
    if total_cost < (df["start_cost"].min() * 2):
        total_cost = df["start_cost"].min() * 2
        include_players = None
    # df.rename(columns={"name": "team"}, inplace=True)
    # Create the linear programming problem
    prob = LpProblem("PlayerSelection", LpMaximize)

    # Decision variables
    selected = LpVariable.dicts("selected", df["web_name"], cat="Binary")

    # Additional decision variables for team count
    team_count = LpVariable.dicts("team_count", set(df["team"]), lowBound=0, upBound=1, cat="Integer")

    # Objective function
    prob += lpSum(selected[player] * df.loc[df.index[i], "rating"] for i, player in enumerate(df["web_name"]))

    # Constraints
    prob += lpSum(selected[player] for player in df["web_name"]) == 2
    prob += (
        lpSum(selected[player] * df.loc[df.index[i], "start_cost"] for i, player in enumerate(df["web_name"]))
        <= total_cost
    )

    # Constraint: No more than 2 players from the same team
    for team in set(df["team"]):
        prob += lpSum(selected[player] for player in df[df["team"] == team]["web_name"]) <= team_count[team]

    # Include specified players (if any)
    if include_players:
        prob += lpSum(selected[player] for player in include_players) == len(include_players)

    # Exclude specified players (if any)
    if exclude_players:
        prob += lpSum(selected[player] for player in exclude_players) == 0

    # Solve the problem
    prob.solve()

    # Retrieve the solution
    status = prob.status
    if status == -1:
        print(f"Failed!!.. exactly 2 goalkeeper must be selected... set budget accordingly")
        return []
    total_points = value(prob.objective)
    selected_players = [player for player in df["web_name"] if selected[player].value() == 1]
    selected_players_df = df[df["web_name"].isin(selected_players)][
        ["full_name", "pos", "team_name", "start_cost", "avg_fixture_difficulty_first_5_gwks", "selected_by_percent"]
    ]
    return selected_players_df


def select_squad(df, include_players=None, exclude_players=None):
    # Filter players by position
    goalkeepers = df[df["singular_name"] == "Goalkeeper"]
    defenders = df[df["singular_name"] == "Defender"]
    midfielders = df[df["singular_name"] == "Midfielder"]
    forwards = df[df["singular_name"] == "Forward"]

    # Create the linear programming problem
    prob = LpProblem("SquadSelection", LpMaximize)

    # Decision variables
    selected = LpVariable.dicts("selected", df["web_name"], cat="Binary")

    # Additional decision variables for position count and team count
    position_count = {
        "Goalkeeper": LpVariable("goalkeeper_count", lowBound=0, upBound=2, cat="Integer"),
        "Defender": LpVariable("defender_count", lowBound=0, upBound=5, cat="Integer"),
        "Midfielder": LpVariable("midfielder_count", lowBound=0, upBound=5, cat="Integer"),
        "Forward": LpVariable("forward_count", lowBound=0, upBound=3, cat="Integer"),
    }

    team_count = LpVariable.dicts("team_count", set(df["team"]), lowBound=0, upBound=3, cat="Integer")

    # Objective function
    prob += lpSum(selected[player] * df.loc[df.index[i], "rating"] for i, player in enumerate(df["web_name"]))

    # Constraints
    prob += lpSum(selected[player] for player in df["web_name"]) == 15
    prob += (
        lpSum(selected[player] * df.loc[df.index[i], "start_cost"] for i, player in enumerate(df["web_name"])) <= 100
    )

    # Position count constraints
    for position, count_var in position_count.items():
        players = df[df["singular_name"] == position]["web_name"]
        prob += lpSum(selected[player] for player in players) == count_var

    # Team count constraints
    for team in set(df["team"]):
        prob += lpSum(selected[player] for player in df[df["team"] == team]["web_name"]) <= team_count[team]

    # Additional constraint for total cost of forward players
    # prob += (
    #     lpSum(selected[player] * df.loc[df.index[i], "start_cost"] for i, player in enumerate(forwards["web_name"]))
    #     <= 26 * position_count["Forward"]
    # )

    # Include specified players (if any)
    if include_players:
        prob += lpSum(selected[player] for player in include_players) == len(include_players)

    # Exclude specified players (if any)
    if exclude_players:
        prob += lpSum(selected[player] for player in exclude_players) == 0

    prob.solve()

    # Retrieve the solution
    status = prob.status
    total_points = value(prob.objective)
    selected_players = [player for player in df["web_name"] if selected[player].value() == 1]
    selected_players_df = df[df["web_name"].isin(selected_players)][
        ["full_name", "pos", "team_name", "start_cost", "avg_fixture_difficulty_first_5_gwks", "selected_by_percent"]
    ]
    return status, total_points, selected_players_df
