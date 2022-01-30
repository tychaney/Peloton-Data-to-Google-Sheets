# Version 2.1.0 Current As Of 01FEB22
# Simplified into 2 files (functions and script)

import argparse

from gspread_dataframe import set_with_dataframe
from gspread_formatting import CellFormat, Color, format_cell_range
from gspread_formatting.dataframe import BasicFormatter, format_with_dataframe
from oauth2client.service_account import ServiceAccountCredentials

# trunk-ignore(flake8/F403)
from peloton_functions import *

# Let's accept some command line input to streamline some things
# --folder is an input arg that says what folder the LoginData.csv is in
# --sendtext and --sendemail are boolean arguments. Set them to True to enable either of these functionalities
# note that you will need to populate the gmail credentials and/or the
# mobile provider if you enable them
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    # Set this to True if you are runninf the script in a different directory
    # than your LoginData.csv (Go to Line 103 for more details)
    parser.add_argument(
        "--folder",
        type=str,
        help="Location of LoginData.csv with the trailing slash",
        required=False,
    )
    parser.add_argument(
        "--sendtext",
        type=bool,
        help="Set to True to send a text message",
        default=False,
    )
    parser.add_argument(
        "--sendemail",
        type=bool,
        help="Set to True to send an email message",
        default=False,
    )
    args = parser.parse_args()
    folder = args.folder
    sendtext = args.sendtext
    sendemail = args.sendemail

# Iterate through the LoginData.csv and do all the things for each user
indexcount = 0
for row in login_df.iterrows():
    email_user = login_df.iloc[indexcount]["email"]
    password_user = login_df.iloc[indexcount]["password"]
    username_user = login_df.iloc[indexcount]["username"]
    peloton_csv_link = login_df.iloc[indexcount]["Peloton CSV Link"]
    google_sheets_link = login_df.iloc[indexcount]["Google Sheets Link"]
    phone_user = login_df.iloc[indexcount]["phone"]
    # Same for all users
    service_account_path = login_df.iloc[indexcount]["Path for Service Account JSON"]
    graph_path = login_df.iloc[indexcount]["Path to Save Graphs"]
    indexcount += 1

    print("Starting work on " + email_user)

    # Google API
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    # see the API documentation for explanation. 'PelotonToGoogle' is what I
    # named the file
    credentials = ServiceAccountCredentials.from_json_keyfile_name(
        "PelotonToGoogle.json", scopes
    )

    # Global Goal Variables
    goal_distance = (
        gc.open_by_url(google_sheets_link).get_worksheet(0).acell("B19").value
    )
    gc.open_by_url(google_sheets_link).get_worksheet(0).update(
        "H1", "Update in Progress"
    )

    # Get the Raw Data
    get_peloton_data(email_user, password_user, username_user, peloton_csv_link)
    peloton_data_user = pd.read_csv(username_user + ".csv")
    peloton_df_user = pd.DataFrame(peloton_data_user)
    gc.open_by_url(google_sheets_link).get_worksheet(0).update(
        "H2", "Gathering Peloton Data"
    )

    # Remove all non cycling data
    cycling_only_user = change_df_cycling_only(peloton_df_user)
    gc.open_by_url(google_sheets_link).get_worksheet(0).update(
        "H2", "Preparing Data for Import"
    )

    # Create the Giant moaDF's (all time data)
    (
        moaDF_user,
        moaDF_by_month_user,
        requested_user,
        moaDF_by_week_user,
    ) = simplify_df_all_data(cycling_only_user)

    # Create Data Frames which only include data from current year
    current_year_df_user = moaDF_user[~(moaDF_user.index <= first_day_of_year)]
    current_year_requested_user = requested_user[
        requested_user.index.year == today.year
    ]

    # Create the Summary DFs which will be displayed on Sheet1
    summary_df_user = calculations(
        goal_distance,
        current_year_df_user,
        moaDF_user,
        moaDF_by_month_user,
        moaDF_by_week_user,
    )

    # Create Describe DFs for Years Requested
    # Current Year
    descript_current_year_user = describe_by_year(moaDF_user, today.year)
    descript_user_last_year = describe_by_year(moaDF_user, today.year - 1)
    descript_user_two_years_ago = describe_by_year(moaDF_user, today.year - 2)
    descript_user_three_years_ago = describe_by_year(moaDF_user, today.year - 3)

    # Add CumSum Columns
    moaDF_user["Cumulative Distance (mi)"] = moaDF_user["Distance (mi)"].cumsum()
    current_year_df_user["Cumulative Distance (mi)"] = current_year_df_user[
        "Distance (mi)"
    ].cumsum()
    current_year_requested_user[
        "Cumulative Distance (mi)"
    ] = current_year_requested_user["Distance (mi)"].cumsum()

    # Graph Making
    # Seaborn First
    # Make KDE Plot
    gc.open_by_url(google_sheets_link).get_worksheet(0).update("H2", "Preparing Graphs")
    make_sns_plots(username_user, moaDF_user)

    # Chart with Plotly
    make_charts(current_year_requested_user, username_user)

    # Sort DFs in Descending Order (User Preference)
    descending(
        moaDF_by_month_user,
        current_year_df_user,
        current_year_requested_user,
        moaDF_user,
    )

    # GSpread
    # Name each sheet as a variable
    ws_user_11 = gc.open_by_url(google_sheets_link).get_worksheet(0)
    ws_user_12 = gc.open_by_url(google_sheets_link).get_worksheet(1)
    ws_user_13 = gc.open_by_url(google_sheets_link).get_worksheet(2)
    ws_user_14 = gc.open_by_url(google_sheets_link).get_worksheet(3)
    ws_user_15 = gc.open_by_url(google_sheets_link).get_worksheet(4)
    ws_user_16 = gc.open_by_url(google_sheets_link).get_worksheet(5)

    # Write Each to Google Sheets
    row = 1
    col = 1

    # Check if its the first of the year, and clear the middle 2 sheets if it
    # is
    clear_if_first(ws_user_11, ws_user_12, ws_user_13, goal_distance)

    # Sort DFs in Descending Order (User Preference)
    descending_user(
        moaDF_by_month_user,
        current_year_df_user,
        current_year_requested_user,
        moaDF_user,
        moaDF_by_week_user,
    )

    gc.open_by_url(google_sheets_link).get_worksheet(0).update("H2", "Tidying Up")
    # DataFrame Formatting for setting to DF with GSpread
    format_for_gspread(moaDF_user)
    format_for_gspread(current_year_requested_user)
    format_for_gspread(current_year_df_user)

    # This formatter will make all DF's 2 Decimals With Consistent Column
    # Headers (Feel Free to change Colors)
    formatter = BasicFormatter(
        header_background_color=Color(0, 0, 0),
        header_text_color=Color(1, 1, 1),
        decimal_format="#,##0.00",
        integer_format="#,##0",
    )

    center_fmt = CellFormat(horizontalAlignment="CENTER")
    # Add DFs to each sheet
    # SummaryDF
    set_with_dataframe(ws_user_11, summary_df_user, row, col)
    # Monthly
    set_with_dataframe(
        ws_user_11, moaDF_by_month_user, row=24, col=1, include_index=True
    )
    # Requested Data Current Year
    set_with_dataframe(
        ws_user_12, current_year_requested_user, row, col, include_index=True
    )
    # Current Year moaDF
    set_with_dataframe(ws_user_13, current_year_df_user, row, col, include_index=True)
    # Description Dataframes
    # Current Year
    set_with_dataframe(
        ws_user_14, descript_current_year_user, row, col, include_index=True
    )
    # Last Year
    set_with_dataframe(ws_user_14, descript_user_last_year, 12, col, include_index=True)
    # 2 Years Ago
    set_with_dataframe(
        ws_user_14, descript_user_two_years_ago, 21, col, include_index=True
    )
    # 3 Years Ago
    set_with_dataframe(
        ws_user_14, descript_user_three_years_ago, 30, col, include_index=True
    )
    # All Time All Data (moaDF)
    set_with_dataframe(ws_user_15, moaDF_user, row, col, include_index=True)
    # Add DFs to each sheet
    # SummaryDF
    format_with_dataframe(
        ws_user_11,
        summary_df_user,
        formatter,
        row,
        col,
        include_index=False,
        include_column_header=True,
    )
    # Monthly
    format_with_dataframe(
        ws_user_11,
        moaDF_by_month_user,
        formatter,
        row=24,
        col=1,
        include_index=True,
        include_column_header=True,
    )
    ws_user_11.update("D1", f"PelotonToSheets_V:{version}")
    ws_user_11.update("D2", git)
    # Requested Data Current Year
    format_with_dataframe(
        ws_user_12,
        current_year_requested_user,
        formatter,
        row,
        col,
        include_index=True,
        include_column_header=True,
    )
    # Current Year moaDF
    format_with_dataframe(
        ws_user_13,
        current_year_df_user,
        formatter,
        row,
        col,
        include_index=True,
        include_column_header=True,
    )
    # Description Dataframes
    # Current Year
    format_with_dataframe(
        ws_user_14,
        descript_current_year_user,
        formatter,
        row,
        col,
        include_index=True,
        include_column_header=True,
    )
    ws_user_14.update("K2", str(today.year))
    # Last Year
    format_with_dataframe(
        ws_user_14,
        descript_user_last_year,
        formatter,
        12,
        col,
        include_index=True,
        include_column_header=True,
    )
    ws_user_14.update("K12", str(today.year - 1))
    # 2 Years Ago
    format_with_dataframe(
        ws_user_14,
        descript_user_two_years_ago,
        formatter,
        21,
        col,
        include_index=True,
        include_column_header=True,
    )
    ws_user_14.update("K21", str(today.year - 2))
    # 3 Years Ago
    format_with_dataframe(
        ws_user_14,
        descript_user_three_years_ago,
        formatter,
        30,
        col,
        include_index=True,
        include_column_header=True,
    )
    ws_user_14.update("K30", str(today.year - 3))
    # All Time All Data (moaDF)
    format_with_dataframe(
        ws_user_15,
        moaDF_user,
        formatter,
        row,
        col,
        include_index=True,
        include_column_header=True,
    )

    # Centers the Data
    format_cell_range(ws_user_11, "A:Z", center_fmt)
    format_cell_range(ws_user_12, "A:Z", center_fmt)
    format_cell_range(ws_user_13, "A:Z", center_fmt)
    format_cell_range(ws_user_14, "A:Z", center_fmt)
    format_cell_range(ws_user_15, "A:Z", center_fmt)

    if sendtext:
        send_text_update(phone_user, summary_df_user, google_sheets_link, username_user)

    if sendemail:
        send_email_update(
            email_user, username_user, summary_df_user, google_sheets_link
        )

    ws_user_11.update("H1", "Update Complete:")
    ws_user_11.update("H2", f"{datetime.now()}")

    # Depending on how many accounts you are runnning, you may have to uncomment this block to prevent errors
    # Recommend pausing every 2 users AT A MINIMUM (Code below pauses after each user)
    # for remaining in range(60, -1, -1):
    #     sys.stdout.write('\r')
    #     sys.stdout.write('Pausing to Avoid Service Acount Overload. {:2d} seconds remaining.'.format(remaining))
    #     sys.stdout.flush()
    #     time.sleep(1)
