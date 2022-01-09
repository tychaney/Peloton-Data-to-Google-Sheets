# Peloton Stats to Google Sheets with Data Visualization through Seaborn and Plotly

Problem: 2 peloton users were looking for a way to track their metrics in a way that was readable and available

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
year]. Since I am running on a raspberry pi, I use SMTP to send an email to each user at the end of the day with
a daily wrap email.

The script utilizes several dependencies (noted in the code itself). One of the dependencies is based on the 
google sheets API. Information can be found here: https://developers.google.com/sheets/api

Feel free to reach out with any questions you have or buy me a coffee :) Venmo: @TylerChaney

# General Setup
The following dependencies are required to run this script properly

pip install pandas
pip install seaborn
pip install matplotlib
pip install gspread
pip install plotly
pip install plotly.express
pip install oauth2client
pip install gspread_dataframe
pip install numpy

# The CSV file used for importing data can be found here:
[LoginData.csv](https://github.com/tychaney/Peloton-Data-to-Google-Sheets/files/7835659/LoginData.csv)

# For formatting of your Google Sheet:
https://docs.google.com/spreadsheets/d/1ZfYI-NGeTK08VAQsnpXk_e_z_mnyT_7vX98O82nLxPY/edit#gid=1196700570



