# Peloton Stats to Google Sheets with Data Visualization through Seaborn and Plotly

## Current Version 2.0.8 (as of January 26, 2022)
### Background

Initial Problem: 2 peloton users were looking for a way to track their metrics in a way that was readable and available

Solution: this script. I personally run this at set intervals on a raspberry pi, so access to their data 
is usable at virtually all hours.

Example Google Sheet (use this for formatting)
https://docs.google.com/spreadsheets/d/1ZfYI-NGeTK08VAQsnpXk_e_z_mnyT_7vX98O82nLxPY/edit?usp=sharing

Here's how it works. The code relies on first having built a csv file which contains the headings of 'name',
'username', 'email', and 'password' (for Peloton). It also includes other unique path and link variables to
simplify execution for inexperienced users. The script pulls data from this file and then logs into
peloton. From there, it downloads the users CSV data with all of their workout data. For my specific needs,
we only cared about cycling data (which you will notice in the code). Several calculations are performed and
some clean up is completed on the dataframes. That data is then passed into the user's assigned Google Sheet
(which also includes their interactive 'goal' cell used for pace calculations [this resets on the first of each
year]. Since I am running on a raspberry pi, I use SMTP to send an email or text to each user at the end of the day with
a daily wrap email.

The script utilizes several dependencies (noted in the code itself). One of the dependencies is based on the 
google sheets API. Information can be found here: https://developers.google.com/sheets/api

Feel free to reach out with any questions you have or buy me a coffee :) Venmo: @TylerChaney
# Future Releases
Future releases include the following:
1. A script to automatically produce the Google Sheet (rather than utilizing the copying and pasting of the example found below)
2. Conditional Formatting Built into the script (Not Just the Google Sheet)

# General Setup
Python3 and the following dependencies are required to run this script properly

```bash

pip install pandas
pip install seaborn
pip install matplotlib
pip install gspread
pip install gspread_dataframe
pip install gspread_formatting
pip install oauth2client
pip install gclient-service-account-auth
pip install plotly
pip install plotly.express
pip install numpy

```


# The CSV file used for importing data can be found here:

[LoginData.csv](https://github.com/tychaney/Peloton-Data-to-Google-Sheets/files/7835659/LoginData.csv)

NOTE, it is important to include the '/' at the end of each path input

# For formatting of your Google Sheet:
Below is a link to a sheet that updates daily from 11AM to 12AM UTC based on the code.
https://docs.google.com/spreadsheets/d/1ZfYI-NGeTK08VAQsnpXk_e_z_mnyT_7vX98O82nLxPY/edit#gid=1196700570

# Google Service Account

In order to run the script, you will have to set up a Google Service Account and an existing Google Sheet. Here is a quickstart guide

1. Create a Google Console Cloud Platform Account (or simply link your Gmail) https://console.cloud.google.com/home/
2. Create a new project
3. Click on APIs & Services --> Credentials --> Manage Service Accounts --> Create Service Account
4. Enter a name
5. Give your Service Account access to your new project (Role=Editor)
6. Click Done
7. Navigate to the APIs & Services tab
8. Verify you see your newly created service account as having access to your project
9. Click on Library (Leftmost column)
10. Search Drive and Enable the Google Drive API
11. Search Sheets and enable the Google Sheets API
12. From the Navigation Menu, click IAM & ADMIN --> Service Accounts
13. Click on your service account
14. Click on 'Keys'
15. Click 'Add Key'
16. Select JSON
17. Create (This is the referenced JSON file in the code itself)
18. Move the JSON from your downloads folder to the folder where your script resides (make note of that path for entry into LoginData.CSV
19. Open your Google Sheets File
20. Share the File with the email of your Service Account

For trouble shooting or should you not want to familiarize yourself with the basic Google API:
https://developers.google.com/sheets/api

# To Run the Script (Ensure the Login.CSV is stored in the same directory)[Note: if you already have python set as the alias, no need for 'python3']

Prior to running, switch to the directory of your script to avoid errors. Should you still have issues, the code has added a '--folder' input to assist

```bash

python3 PelotonToSheets.py

```
# In-Depth Look at the Script

The first part of the script takes the data provided in the Login.csv file and applies each value to user-specific variables. Please note, for more than 1 user, the paths for graphs and the Google Sheets API JSON will be the same for all users for simplicity. Also, for those recieving errors, feel free to utilize the --folder function to ensure accurate use of the folder. If you are not having errors, the folder argument can be set to false, and the default location will be the location of the script itself.

```python
## Let's accept some command line input to streamline some things
## --folder is an input arg that says what folder the LoginData.csv is in
## --sendtext and --sendemail are boolean arguments. Set them to True to enable either of these functionalities
## note that you will need to populate the gmail credentials and/or the mobile provider if you enable them
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    # Set this to True if you are runninf the script in a different directory
    # than your LoginData.csv (Go to Line 103 for more details)
    parser.add_argument(
        '--folder',
        type=str,
        help="Location of LoginData.csv with the trailing slash",
        required=False)
    parser.add_argument(
        '--sendtext',
        type=bool,
        help="Set to True to send a text message",
        default=False)
    parser.add_argument(
        '--sendemail',
        type=bool,
        help="Set to True to send an email message",
        default=False)
    args = parser.parse_args()
    folder = args.folder
    sendtext = args.sendtext
    sendemail = args.sendemail
```

As of Version 2.0.0, the script autoiterates through the rows on the LoginData.csv (credit to JHJCo). Below is how the script takes the data from peloton to google sheets.

```python
## This is the meat of the code
## Iterate through the LoginData.csv and do all the things for each user
indexcount = 0
for row in login_df.iterrows():
    email_user = login_df.iloc[indexcount]['email']
    password_user = login_df.iloc[indexcount]['password']
    username_user = login_df.iloc[indexcount]['username']
    peloton_csv_link = login_df.iloc[indexcount]['Peloton CSV Link']
    google_sheets_link = login_df.iloc[indexcount]['Google Sheets Link']
    phone_user = login_df.iloc[indexcount]['phone']
    # Same for all users
    service_account_path = login_df.iloc[indexcount]['Path for Service Account JSON']
    graph_path = login_df.iloc[indexcount]['Path to Save Graphs']
    indexcount += 1

    print("Starting work on " + email_user)

    # Google API
    scopes = ['https://www.googleapis.com/auth/spreadsheets',
              'https://www.googleapis.com/auth/drive']
    # see the API documentation for explanation. 'PelotonToGoogle' is what I
    # named the file
    credentials = ServiceAccountCredentials.from_json_keyfile_name(
        'PelotonToGoogle.json', scopes)
    gc = gspread.service_account(service_account_path + 'PelotonToGoogle.json')

    # Global Goal Variables
    goal_distance = gc.open_by_url(
        google_sheets_link).get_worksheet(0).acell('B19').value

    # Get the Raw Data
    get_peloton_data(
        email_user,
        password_user,
        username_user,
        peloton_csv_link)
    peloton_data_user = pd.read_csv(username_user + '.csv')
    peloton_df_user = pd.DataFrame(peloton_data_user)

    # Remove all non cycling data
    cycling_only_user = change_df_cycling_only(peloton_df_user)

    # Create the Giant moaDF's (all time data)
    moaDF_user, moaDF_by_month_user, requested_user, moaDF_by_week_user = simplify_df_all_data(
        cycling_only_user)

    # Create Data Frames which only include data from current year
    current_year_df_user = moaDF_user[~(moaDF_user.index <= first_day_of_year)]
    current_year_requested_user = requested_user[requested_user.index.year == today.year]

    # Create the Summary DFs which will be displayed on Sheet1
    summary_df_user = calculations(
        goal_distance,
        current_year_df_user,
        moaDF_user,
        moaDF_by_month_user,
        moaDF_by_week_user)

    # Create Describe DFs for Years Requested
    # Current Year
    descript_current_year_user = describe_by_year(moaDF_user, today.year)
    descript_user_last_year = describe_by_year(moaDF_user, today.year - 1)
    descript_user_two_years_ago = describe_by_year(moaDF_user, today.year - 2)
    descript_user_three_years_ago = describe_by_year(
        moaDF_user, today.year - 3)

    # Graph Making
    # Seaborn First
    # Make KDE Plot
    make_sns_plots(username_user, moaDF_user)

    # Chart with Plotly
    make_charts(current_year_requested_user, username_user)

    # Sort DFs in Descending Order (User Preference)
    descending(
        moaDF_by_month_user,
        current_year_df_user,
        current_year_requested_user,
        moaDF_user)

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
        moaDF_by_week_user)

    # DataFrame Formatting for setting to DF with GSpread
    format_for_gspread(moaDF_user)
    format_for_gspread(current_year_requested_user)
    format_for_gspread(current_year_df_user)

    # This formatter will make all DF's 2 Decimals With Consistent Column
    # Headers (Feel Free to change Colors)
    formatter = BasicFormatter(header_background_color=Color(0, 0, 0),
                               header_text_color=Color(1, 1, 1),
                               decimal_format='#,##0.00',
                               integer_format='#,##0')

    center_fmt = CellFormat(horizontalAlignment='CENTER')
    # Add DFs to each sheet
    # SummaryDF
    set_with_dataframe(ws_user_11, summary_df_user, row, col)
    # Monthly
    set_with_dataframe(
        ws_user_11,
        moaDF_by_month_user,
        row=24,
        col=1,
        include_index=True)
    # Requested Data Current Year
    set_with_dataframe(
        ws_user_12,
        current_year_requested_user,
        row,
        col,
        include_index=True)
    # Current Year moaDF
    set_with_dataframe(
        ws_user_13,
        current_year_df_user,
        row,
        col,
        include_index=True)
    # Description Dataframes
    # Current Year
    set_with_dataframe(
        ws_user_14,
        descript_current_year_user,
        row,
        col,
        include_index=True)
    # Last Year
    set_with_dataframe(
        ws_user_14,
        descript_user_last_year,
        12,
        col,
        include_index=True)
    # 2 Years Ago
    set_with_dataframe(
        ws_user_14,
        descript_user_two_years_ago,
        21,
        col,
        include_index=True)
    # 3 Years Ago
    set_with_dataframe(
        ws_user_14,
        descript_user_three_years_ago,
        30,
        col,
        include_index=True)
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
        include_column_header=True)
    # Monthly
    format_with_dataframe(
        ws_user_11,
        moaDF_by_month_user,
        formatter,
        row=24,
        col=1,
        include_index=True,
        include_column_header=True)
    ws_user_11.update('D1', f'PelotonToSheets_V:{version}')
    ws_user_11.update('D2', git)
    # Requested Data Current Year
    format_with_dataframe(
        ws_user_12,
        current_year_requested_user,
        formatter,
        row,
        col,
        include_index=True,
        include_column_header=True)
    # Current Year moaDF
    format_with_dataframe(
        ws_user_13,
        current_year_df_user,
        formatter,
        row,
        col,
        include_index=True,
        include_column_header=True)
    # Description Dataframes
    # Current Year
    format_with_dataframe(
        ws_user_14,
        descript_current_year_user,
        formatter,
        row,
        col,
        include_index=True,
        include_column_header=True)
    ws_user_14.update('K2', str(today.year))
    # Last Year
    format_with_dataframe(
        ws_user_14,
        descript_user_last_year,
        formatter,
        12,
        col,
        include_index=True,
        include_column_header=True)
    ws_user_14.update('K12', str(today.year - 1))
    # 2 Years Ago
    format_with_dataframe(
        ws_user_14,
        descript_user_two_years_ago,
        formatter,
        21,
        col,
        include_index=True,
        include_column_header=True)
    ws_user_14.update('K21', str(today.year - 2))
    # 3 Years Ago
    format_with_dataframe(
        ws_user_14,
        descript_user_three_years_ago,
        formatter,
        30,
        col,
        include_index=True,
        include_column_header=True)
    ws_user_14.update('K30', str(today.year - 3))
    # All Time All Data (moaDF)
    format_with_dataframe(
        ws_user_15,
        moaDF_user,
        formatter,
        row,
        col,
        include_index=True,
        include_column_header=True)

    # Centers the Data
    format_cell_range(ws_user_11, 'A:Z', center_fmt)
    format_cell_range(ws_user_12, 'A:Z', center_fmt)
    format_cell_range(ws_user_13, 'A:Z', center_fmt)
    format_cell_range(ws_user_14, 'A:Z', center_fmt)
    format_cell_range(ws_user_15, 'A:Z', center_fmt)

    if sendtext:
        send_text_update(
            phone_user,
            summary_df_user,
            google_sheets_link,
            username_user)

    if sendemail:
<<<<<<< HEAD
        send_email_update(
            email_user,
            username_user,
            summary_df_user,
            google_sheets_link)

    # Depending on how many accounts you are runnning, you may have to uncomment this block to prevent errors
    # for remaining in range(60, 0, -1):
    #     sys.stdout.write('\r')
    #     sys.stdout.write('Pausing to Avoid Service Acount Overload. {:2d} seconds remaining.'.format(remaining))
    #     sys.stdout.flush()
    #     time.sleep(1)

```
