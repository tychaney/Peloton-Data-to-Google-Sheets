# Peloton Stats to Google Sheets with Data Visualization through Seaborn and Plotly


## Current Version 2.1.2 (as of February 1, 2022)

Version 2.1.2 includes the initial commit of the sheet_builder.py file. This file can be used to generate your spreadsheet. It will not, however (as of initial release), include the charts or conditional formatting present in the example file below, but it will assist in expediting any copy and pasting you choose to do for formatting purposes. As such, recommend running this file first to create your sheet. You can add the sheet to your Google Drive after it has been shared with you.

Also included is the addition of the 'pause' arg which defaults to false. This is to combat the "Quota Exceeded" Error which occurs to service accounts which exceed their allotted edits per period (occurs with multiple users)

Version 2.1.2 also includes the blank JSON which is not intended for use. This is merely an example of what is produced when the service account is created.

As of Version 2.1.0, the script has been split into multiple files. All functions are on their own and are imported into the peloton_to_sheets.py script. Functionality remains the same, especially if being run passively via a raspberry pi or similar device.

## Example Google Sheet (use this for formatting) with Selected Example Data Displays
The sheet itself can be found here
https://docs.google.com/spreadsheets/d/1ZfYI-NGeTK08VAQsnpXk_e_z_mnyT_7vX98O82nLxPY/edit?usp=sharing


### Aggregate Data Display
<img width="1315" alt="Screen Shot 2022-01-31 at 12 52 53 PM" src="https://user-images.githubusercontent.com/94143619/151871327-335d5da7-2fbe-49c7-8f59-a092a5c88503.png">

### Requested Data Display (Highly Correlated Numerical Data)[Current Year]
<img width="747" alt="Screen Shot 2022-01-31 at 12 53 55 PM" src="https://user-images.githubusercontent.com/94143619/151871524-772aaeb9-66d8-4c99-909c-aa289338e9f3.png">

### All Numerical Data Current Year
<img width="1197" alt="Screen Shot 2022-01-31 at 12 57 48 PM" src="https://user-images.githubusercontent.com/94143619/151872083-aaf54272-9f00-4fd5-9687-39d678818d3f.png">

### Description of Data (Descriptive Stats) by Year
<img width="1049" alt="Screen Shot 2022-01-31 at 12 55 45 PM" src="https://user-images.githubusercontent.com/94143619/151871694-0bcc47b4-bc8a-49c3-8326-18cbbc9a3b56.png">


## Background

Initial Problem: 2 peloton users were looking for a way to track their metrics in a way that was readable and available

Solution: this script. I personally run this at set intervals on a raspberry pi, so access to their data
is usable at virtually all hours.

Here's how it works. The code relies on first having built a csv file which contains the headings of 'name',
'username', 'email', and 'password' (for Peloton). It also includes other unique path and link variables to
simplify execution for inexperienced users. The script pulls data from this file and then logs into
peloton. From there, it downloads the users CSV data with all of their workout data. For my specific needs,
we only cared about cycling data (which you will notice in the code). Several calculations are performed and
some clean up is completed on the dataframes. That data is then passed into the user's assigned Google Sheet
(which also includes their interactive 'goal' cell used for pace calculations [this resets on the first of each year]. Since I am running on a raspberry pi, I use SMTP to send an email or text to each user at the end of the day with
a daily wrap email.

The script utilizes several dependencies (noted in the code itself). One of the dependencies is based on the
google sheets API. Information can be found here: https://developers.google.com/sheets/api

Feel free to reach out with any questions you have or buy me a coffee :) Venmo: @TylerChaney

## Future Releases

Future releases include the following:

1. PR calculation functionality
2. Setup files to automatically set up user machine (Releases aid in this process)

## General Setup

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

## The CSV file used for importing data can be found here:

[LoginData.csv](https://github.com/tychaney/Peloton-Data-to-Google-Sheets/files/7835659/LoginData.csv)

NOTE, it is important to include the '/' at the end of each path input

## For formatting of your Google Sheet:

Below is a link to a sheet that updates daily from 11AM to 12AM UTC based on the code.
https://docs.google.com/spreadsheets/d/1ZfYI-NGeTK08VAQsnpXk_e_z_mnyT_7vX98O82nLxPY/edit#gid=1196700570

## Google Service Account

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

## To Run the Script (Ensure the Login.CSV is stored in the same directory)[Note: if you already have python set as the alias, no need for 'python3']

Prior to running, switch to the directory of your script to avoid errors. Should you still have issues, the code has added a '--folder' input to assist

```bash

python3 peloton_to_sheets.py

```
