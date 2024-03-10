# This script is designed to build your sheet
# MUST HAVE A SERVICE ACCOUNT SET UP IN ORDER FOR THIS TO WORK
# The service account '.json' must also be present
# This script assumes the LoginData.csv and Service account JSON are colated with the script
# Please note, as of v2.1.2 this will NOT generate the charts present in the example file

import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd


login_data = pd.read_csv('LoginData.csv')
login_df = pd.DataFrame(login_data)


indexcount = 0
for row in login_df.iterrows():
    email_user = login_df.iloc[indexcount]['email']
    username_user = login_df.iloc[indexcount]['username']
    service_account_path = login_df.iloc[indexcount]['Path for Service Account JSON']     # Same for all users

    # Google API
    scopes = ['https://www.googleapis.com/auth/spreadsheets',
              'https://www.googleapis.com/auth/drive']
    gc = gspread.service_account(f'{service_account_path}PelotonToGoogle.json')
    credentials = ServiceAccountCredentials.from_json_keyfile_name(
        "PelotonToGoogle.json", scopes
    )

    print(f"Starting work on {email_user}'s Google Sheet")

    # Create The Spreadsheet
    sh = gc.create(f'{username_user} Peloton Output')
    # Share the spreadsheet
    sh.share(email_user, perm_type='user', role='owner', notify=True)
    # Add Each Sheet
    sh.sheet1.update_title(
        "Aggregate Data")
    sheet2 = sh.add_worksheet(
        title="Workout Data Requested", rows="100", cols="20")
    sheet3 = sh.add_worksheet(
        title="All Numerical Workout Data", rows="100", cols="20")
    sheet4 = sh.add_worksheet(
        title="Description of All Data", rows="100", cols="20")
    sheet5 = sh.add_worksheet(
        title="Lifetime/Historical Data", rows="100", cols="20")
    sheet6 = sh.add_worksheet(
        title="Annual Summary", rows="100", cols="20")

    print(f"{email_user}'s Google Sheet is complete, and a notification email has been sent.")
    
    indexcount += 1