# Version 1.0.1 Current As Of 09JAN22
import os #For sending the text message
import pandas as pd
pd.options.mode.chained_assignment = None  # default='warn' (credit to JHJCo for catching this)
import plotly.express as px
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import date, datetime
import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
import numpy as np
from gspread_dataframe import set_with_dataframe
from matplotlib import pyplot as plt
# plt.rcParams.update({'figure.max_open_warning': 0}) #Ignores the output for having too many figures in use (May apply depending on Machine capabilities)
import seaborn as sns


# This was added to ease use for those with limited Coding Experience
# As a part of this update, the SMTP email send function has been commented out (if you would like to utilize this feature, uncomment it out [last lines of code])
# Also, all USER_2 and USER 3 functions have been commented out, simply uncomment to utilize
# Pull the Admin Variables from the CSV
login_data = pd.read_csv('LoginData.csv')
login_df = pd.DataFrame(login_data)

# Create Admin Variables
# Create Logon Variables
# user_1
email_user_1 = login_df.iloc[0]['email']
password_user_1 = login_df.iloc[0]['password']
username_user_1 = login_df.iloc[0]['username']
peloton_csv_link_user_1 = login_df.iloc[0]['Peloton CSV Link']
google_sheets_link_user_1 = login_df.iloc[0]['Google Sheets Link']
phone_user_1 = login_df.iloc[0]['phone']
# # user_2
# email_user_2 = login_df.iloc[1]['email']
# password_user_2 = login_df.iloc[1]['password']
# username_user_2 = login_df.iloc[1]['username']
# peloton_csv_link_user_2 = login_df.iloc[1]['Peloton CSV Link']
# google_sheets_link_user_2 = login_df.iloc[1]['Google Sheets Link']
#phone_user_2 = login_df.iloc[1]['phone']
# # user_3
# email_user_3 = login_df.iloc[2]['email']
# password_user_3 = login_df.iloc[2]['password']
# username_user_3 = login_df.iloc[2]['username']
# peloton_csv_link_user_3 = login_df.iloc[2]['Peloton CSV Link']
# google_sheets_link_user_3 = login_df.iloc[2]['Google Sheets Link']
#phone_user_3 = login_df.iloc[2]['phone']

# Same for Each
service_account_path = login_df.iloc[0]['Path for Service Account JSON'] #Same for all users
graph_path = login_df.iloc[0]['Path to Save Graphs']


# Google API
scopes = ['https://www.googleapis.com/auth/spreadsheets',
'https://www.googleapis.com/auth/drive']
credentials = ServiceAccountCredentials.from_json_keyfile_name('PelotonToGoogle.json', scopes) #see the API documentation for explanation. 'PelotonToGoogle' is what I named the file
gc = gspread.service_account(service_account_path + 'PelotonToGoogle.json') #Note the path for the Service account is the same for user 1&2

#Global Date Variables
today = date.today()
first_day_of_year = date(today.year, 1, 1)
last_day_of_year = date(today.year, 12, 31)
days_left_in_year = last_day_of_year - today
days_left_in_year_float = float(days_left_in_year.days)
total_days_in_year = last_day_of_year - first_day_of_year
total_days_in_year_float = float(total_days_in_year.days)
days_so_far = today - first_day_of_year
days_so_far_float = float(days_so_far.days + 1)

# Get Workout CSVs
index = 0
def get_API_data (dataframe):
    for index, row in dataframe.iterrows():
        index = 0
        email = row['email']
        password = row['password']
        username = row['username']
        s = requests.Session()
        payload = {'username_or_email': email, 'password': password}
        s.post('https://api.onepeloton.com/auth/login', json=payload)
        if email == email_user_1:
            download_data = s.get(peloton_csv_link_user_1, allow_redirects=True)
        #note to uncomment these lines to use more users
        # elif email == email_user_2:
            # download_data = s.get(peloton_csv_link_user_2, allow_redirects=True)
        # elif email == email_user_3:
            # download_data = s.get(peloton_csv_link_user_3, allow_redirects=True)
        csv_file = str(username) + '.csv'
        with open(csv_file, 'wb') as f:
            f.write(download_data.content)
        index += 1
    return index    


# Global Goal Variables
goal_distance_user_1 = gc.open_by_url(google_sheets_link_user_1).get_worksheet(0).acell('B19').value
# goal_distance_user_2 = gc.open_by_url(google_sheets_link_user_2).get_worksheet(0).acell('B19').value
# goal_distance_user_3 = gc.open_by_url(google_sheets_link_user_3).get_worksheet(0).acell('B19').value

# Get the Raw Data
get_API_data(login_df)
peloton_data_user_1 = pd.read_csv(username_user_1 + '.csv')
peloton_df_user_1 = pd.DataFrame(peloton_data_user_1)
# peloton_data_user_2 = pd.read_csv(username_user_2 + '.csv')
# peloton_df_user_2 = pd.DataFrame(peloton_data_user_2)
# peloton_data_user_3 = pd.read_csv(username_user_3 + '.csv')
# peloton_df_user_3 = pd.DataFrame(peloton_data_user_3)

# Remove all non cycling
def change_df_cycling_only (workout_df):
    cycling_only = workout_df[workout_df['Fitness Discipline'] == 'Cycling']
    return cycling_only
cycling_only_user_1 = change_df_cycling_only(peloton_df_user_1)
# cycling_only_user_2 = change_df_cycling_only(peloton_df_user_2)
# cycling_only_user_3 = change_df_cycling_only(peloton_df_user_3)

# Make the big dataframe with everything in it
def simplify_df_all_data (cycling_only):
    # this is the requested data
    workout_data_we_want = cycling_only[
                                        [
                                        'Workout Timestamp', 
                                        'Length (minutes)', 'Total Output', 
                                        'Distance (mi)', 'Calories Burned'
                                        ]
                                        ]
    # This is the rest of the data (called avg df because they are averages)
    average_df = cycling_only[
                                [
                                'Workout Timestamp', 
                                'Avg. Watts', 'Avg. Resistance', 
                                'Avg. Cadence (RPM)', 'Avg. Speed (mph)',
                                'Avg. Heartrate'
                                ]
                                ]
    # Change date formats

    workout_data_we_want['Workout Date'] = workout_data_we_want.loc[:,'Workout Timestamp'].str[:10]
    average_df['Workout Date'] = average_df.loc[:,'Workout Timestamp'].str[:10]
    # workout_data_we_want['Workout Date'] = workout_data_we_want['Workout Timestamp'].str[:10]
    # average_df['Workout Date'] = average_df['Workout Timestamp'].str[:10]
    # Reorder the data so it's more readable
    workout_data_we_want = workout_data_we_want[
                                                [
                                                'Workout Date', 'Length (minutes)', 
                                                'Total Output', 'Distance (mi)', 'Calories Burned'
                                                ]
                                                ]
    # Remove instances of none and replace with '0'
    workout_data_we_want = workout_data_we_want.replace('None', 0)
    # Convert Data from Strings to Numbers
    workout_data_we_want = workout_data_we_want[['Workout Date', 'Length (minutes)', 'Total Output', 
                                            'Distance (mi)', 'Calories Burned']].apply(pd.to_numeric, errors = 'ignore')
    # Aggregation
    # Convert to Date Time
    workout_data_we_want['Workout Date'] = pd.to_datetime(workout_data_we_want['Workout Date']).dt.date
    # Add the values together
    workout_data_we_want = workout_data_we_want.groupby('Workout Date').sum()
    # Same process but to the average DF
    average_df = average_df[
                            ['Workout Date', 
                            'Avg. Watts', 'Avg. Resistance', 
                            'Avg. Cadence (RPM)', 'Avg. Speed (mph)',
                            'Avg. Heartrate'
                            ]
                            ]
    # Fix Percentages
    average_df['Avg. Resistance'] = average_df['Avg. Resistance'].str.rstrip('%').astype('float') / 100.0
    # Remove instances of none and replace with '0'
    average_df = average_df.replace('None', 0)
    # strings to numeric
    average_df = average_df[
                            ['Workout Date', 
                            'Avg. Watts', 'Avg. Resistance', 
                            'Avg. Cadence (RPM)', 'Avg. Speed (mph)',
                            'Avg. Heartrate'
                            ]
                            ].apply(pd.to_numeric, errors = 'ignore')
    #  convert workout date to date
    average_df['Workout Date'] = pd.to_datetime(average_df['Workout Date']).dt.date
    # Average the values together
    average_df = average_df.groupby('Workout Date').mean()
    # At this point we have 'clean' versions of both DFs
    # Below is the combination of DFs to 1 big dataframe (Mother of All DataFrames)
    moaDF = workout_data_we_want.join(average_df)
    moaDF = moaDF.fillna(0)
    # Current Year by Month (Requested Data)
    workout_data_we_want_copy = workout_data_we_want
    workout_data_we_want_copy.index = pd.to_datetime(workout_data_we_want_copy.index)    
    data_by_month = workout_data_we_want_copy.groupby(pd.Grouper(freq='M')).sum()
    data_by_month.index = data_by_month.index.strftime('%Y/%m')
    # Current Year by Week (for pace calculation Purposes) (requested data)
    data_by_week = workout_data_we_want_copy.groupby(pd.Grouper(freq='W-SUN')).sum()
    data_by_week.index = data_by_week.index.strftime('%Y/%m/%d')
    average_df_copy = average_df
    average_df_copy.index = pd.to_datetime(average_df_copy.index)    
    # Current year by month (Average)
    data_by_month_avg = average_df_copy.groupby(pd.Grouper(freq='M')).mean()
    data_by_month_avg.index = data_by_month_avg.index.strftime('%Y/%m')
    # Current Year by Week (for pace calculation Purposes) (non-requested data)
    data_by_week_avg = average_df_copy.groupby(pd.Grouper(freq='W-SUN')).mean()
    data_by_week_avg.index = data_by_week_avg.index.strftime('%Y/%m/%d')  
    # Make the moaDF by Month
    moaDF_by_month = data_by_month.join(data_by_month_avg)
    moaDF_by_month = moaDF_by_month.fillna(0)
    moaDF_by_month.index.rename('Month/Year', inplace=True)
    # Make the moaDF by Week
    moaDF_by_week =data_by_week.join(data_by_week_avg)
    moaDF_by_week = moaDF_by_week.fillna(0)
    return moaDF, moaDF_by_month, workout_data_we_want_copy, moaDF_by_week

# Create the Giant moaDF's (all time data)
moaDF_user_1, moaDF_by_month_user_1, requested_user_1, moaDF_by_week_user_1 = simplify_df_all_data(cycling_only_user_1)
# moaDF_user_2, moaDF_by_month_user_2, requested_user_2, moaDF_by_week_user_2 = simplify_df_all_data(cycling_only_user_2)
# moaDF_user_3, moaDF_by_month_user_3, requested_user_3, moaDF_by_week_user_3 = simplify_df_all_data(cycling_only_user_3)

# Create Data Frames which only include data from current year
current_year_df_user_1 = moaDF_user_1[~(moaDF_user_1.index <= first_day_of_year)]
# current_year_df_user_2 = moaDF_user_2[~(moaDF_user_2.index <= first_day_of_year)]
# current_year_df_user_3 = moaDF_user_3[~(moaDF_user_3.index <= first_day_of_year)]

current_year_requested_user_1 = requested_user_1[requested_user_1.index.year == today.year]
# current_year_requested_user_2 = requested_user_2[requested_user_2.index.year == today.year]
# current_year_requested_user_3 = requested_user_3[requested_user_3.index.year == today.year]

# Conduct Calculations
def calculations (goal_distance, current_year_df ,moaDF_all_time, moaDF_by_month, moaDF_by_week):
    # Average Length Per Ride Day
    avg_length = current_year_df['Length (minutes)'].mean()
    # Average Output Per Ride Day
    avg_output = current_year_df['Total Output'].mean()
    # Average Calories Per Ride Day
    avg_calories = current_year_df['Calories Burned'].mean()
    # Average Distance Per Ride Day
    avg_distance = current_year_df['Distance (mi)'].mean()
    # Total Distance
    total_distance = current_year_df['Distance (mi)'].sum()
    distance_from_goal = float(goal_distance) - total_distance
    pace = (total_distance / days_so_far_float) * (total_days_in_year_float)
    pace_versus_goal = float(goal_distance)- pace
    percent_of_goal = (total_distance/float(goal_distance))
    # Most recent workout needs to be pulled from previous year to account for new years
    most_recent_workout = moaDF_all_time.index[-1]
    # Miles Ridden This Week
    miles_this_week = moaDF_by_week.iloc[-1]['Distance (mi)']
    # Miles Ridden This Month
    miles_current_month = moaDF_by_month.iloc[-1]['Distance (mi)']

    # Summary Data Frame for Sheets
    calculations = [
            'Today', 'Most Recent Workout','Goal Distance (mi)', 'Current Total Distance (mi)',
            'Total Distance from Goal', 'Percent of Goal Achieved (%)',
            'Total Days Elapsed This Year', 'Total Days Left This Year',
            'Current Pace by End of Year (mi)', 'Goal Distance - Pace', 'Average Ride Length (minutes)', 
            'Average Ride Output', 'Average Distance Per Ride (mi)', 
            'Average Calories Burned Per Ride (kCal)', 'Miles Ridden This Month', 'Miles Ridden This Week (Starting Mon)'
            ]
    values = [
            str(today), str(most_recent_workout) ,int(goal_distance), round(total_distance, 2), 
            round (distance_from_goal, 2), round(percent_of_goal, 4), str(days_so_far_float), 
            str(days_left_in_year_float), round(pace, 2), round(pace_versus_goal, 2),round(avg_length, 2), 
            round(avg_output, 2), round(avg_distance, 2), round(avg_calories, 2), round(miles_current_month,2), 
            round(miles_this_week, 2)
            ]
    summary = {'Metric': calculations, 'Value': values}
    summary_df = pd.DataFrame(summary)
    return summary_df

# Create the Summary DFs which will be displayed on Sheet1
summary_df_user_1 = calculations(goal_distance_user_1, current_year_df_user_1, moaDF_user_1,moaDF_by_month_user_1, moaDF_by_week_user_1)
# summary_df_user_2 = calculations(goal_distance_user_2, current_year_df_user_2, moaDF_user_2, moaDF_by_month_user_2, moaDF_by_week_user_2)
# summary_df_user_3 = calculations(goal_distance_user_3, current_year_df_user_3, moaDF_user_3, moaDF_by_month_user_3, moaDF_by_week_user_3)

# Create Descriptive Stats DF
def describe_by_year (moaDF_all_time, year):
    moaDF_all_time.index = pd.to_datetime(moaDF_all_time.index)
    moaDF_year = moaDF_all_time[moaDF_all_time.index.year == year]
    description_df = moaDF_year.replace(0, np.NaN).describe()
    return description_df

# Create Describe DFs for Years Requested
# Current Year
descript_current_year_user_1 = describe_by_year(moaDF_user_1, today.year)
# descript_current_year_user_2 = describe_by_year(moaDF_user_2, today.year)
# descript_current_year_user_3 = describe_by_year(moaDF_user_3, today.year)
# user_1
descript_user_1_2021 = describe_by_year(moaDF_user_1, 2021)
descript_user_1_2022 = describe_by_year(moaDF_user_1, 2022)
descript_user_1_2023 = describe_by_year(moaDF_user_1, 2023)
# # user_2
# descript_user_2_2021 = describe_by_year(moaDF_user_2, 2021)
# descript_user_2_2022 = describe_by_year(moaDF_user_2, 2022)
# descript_user_2_2023 = describe_by_year(moaDF_user_2, 2023)
# # user_3
# descript_user_3_2021 = describe_by_year(moaDF_user_3, 2021)
# descript_user_3_2022 = describe_by_year(moaDF_user_3, 2022)
# descript_user_3_2023 = describe_by_year(moaDF_user_3, 2023)

# Graph Making
# Seaborn First
# Make KDE Plot
def make_sns_plots (username, moaDF_all_time):    
    moaDF_all_time.index = pd.to_datetime(moaDF_all_time.index)
    avg_hr_all_time = moaDF_all_time['Avg. Heartrate']
    avg_hr_all_time = [i for i in avg_hr_all_time if i != 0]
    plt.figure(figsize = (15,8))
    sns.set_style("darkgrid")
    sns.kdeplot(avg_hr_all_time, shade=True)
    # plt.legend()
    plt.title(f'{username} Average HR per Ride KDE All Time')
    plt.savefig(f'{graph_path}{username}/{username}_Average_HR_KDE.jpg')
    plt.clf()
    # Remove all 0s
    moaDF_all_time[moaDF_all_time <= 0] = np.nan
    # Make a violinplot by Year
    plt.figure(figsize = (15,8))
    sns.set_style("darkgrid")
    ax = sns.violinplot(data = moaDF_all_time, x=moaDF_all_time.index.year, y= 'Avg. Heartrate')
    plt.title(f'{username} Average Heartrate per Ride (by Year)')
    ax.set_xticklabels(ax.get_xticklabels(),rotation = 30)
    plt.savefig(f'{graph_path}{username}/{username}_Average_HR_by_year.jpg')
    plt.clf()

    # Make a boxplot by month
    # Heartrate
    plt.figure(figsize=(15,8))
    sns.set_style("darkgrid")
    ax = sns.boxplot(data = moaDF_all_time, x=moaDF_all_time.index.to_period('M'), y= 'Avg. Heartrate')
    plt.title(f'{username} Average Heartrate per Ride (by Year)')
    ax.set_xticklabels(ax.get_xticklabels(),rotation = 30)
    plt.savefig(f'{graph_path}{username}/{username}_Average_HR_by_month.jpg')    
    plt.clf()

    # Make a Violin Chart off of HR
    plt.figure(figsize=(15,8))
    sns.set_style("darkgrid")
    ax = sns.violinplot(data = moaDF_all_time, x=moaDF_all_time.index.to_period('M'), y= 'Avg. Heartrate')
    ax.set_xticklabels(ax.get_xticklabels(),rotation = 30)
    plt.title(f'{username} Average Heartrate per Ride (by Month)')
    plt.savefig(f'{graph_path}{username}/{username}_Violin_Average_HR_by_month.jpg')    
    plt.clf()

    # Output
    # Make a violin plot by Year for HR
    plt.figure(figsize=(15,8))
    sns.set_style("darkgrid")
    ax = sns.violinplot(data = moaDF_all_time, x=moaDF_all_time.index.year, y= 'Total Output')
    plt.title(f'{username} Total Output per Ride (by Year)')
    ax.set_xticklabels(ax.get_xticklabels(),rotation = 30)
    plt.savefig(f'{graph_path}{username}/{username}_Total_Output_by_year.jpg')    
    plt.clf()

    # Violin By Month
    plt.figure(figsize=(15,8))
    sns.set_style('darkgrid')
    ax = sns.violinplot(data = moaDF_all_time, x=moaDF_all_time.index.to_period('M'), y= 'Total Output')
    plt.title(f'{username} Total Output per Ride (by Month)')
    ax.set_xticklabels(ax.get_xticklabels(),rotation = 30)
    plt.savefig(f'{graph_path}{username}/{username}_Violin_Total Output_by_month.jpg')      
    plt.clf()

    # Boxplot per Month
    plt.figure(figsize=(15,8))
    sns.set_style('darkgrid')
    ax = sns.boxplot(data = moaDF_all_time, x=moaDF_all_time.index.to_period('M'), y= 'Total Output')
    plt.title(f'{username} Total Output per Ride (by Month)')
    ax.set_xticklabels(ax.get_xticklabels(),rotation = 30)
    plt.savefig(f'{graph_path}{username}/{username}_Boxplot_Total Output_by_month.jpg')     
    plt.clf()

make_sns_plots(username_user_1, moaDF_user_1)
# make_sns_plots(username_user_2, moaDF_user_2)
# make_sns_plots(username_user_3, moaDF_user_3)

#Chart with Plotly
def make_charts(requested_workout_data,username):        
    figOutput_Distance = px.scatter(requested_workout_data, x = 'Total Output', y = 'Distance (mi)', color = 'Length (minutes)')
    figOutput_Distance.update_layout(autosize = True, width = 1200, height = 900, font_size = 22)
    figOutput_Distance.update_traces(marker=dict(size=12,line=dict(width=3, color='DarkSlateGrey')),
                  selector=dict(mode='markers'))
    figOutput_Distance.write_image(graph_path + username + '/' + username +  '_Output_to_Distance2D.jpg')           

make_charts(current_year_requested_user_1, username_user_1)
# make_charts(current_year_requested_user_2, username_user_2)
# make_charts(current_year_requested_user_3, username_user_3)

# Sort DFs in Descending Order (User Preference)
def descending(moaDF_by_month, current_year_df, current_year_requested,moaDF):

    moaDF_by_month.sort_values(by=['Month/Year'], inplace=True, ascending=False)
    current_year_requested.sort_values(by=['Workout Date'], inplace=True, ascending=False)
    current_year_df.sort_values(by=['Workout Date'], inplace=True, ascending=False)
    moaDF.sort_values(by=['Workout Date'], inplace=True, ascending=False)

descending(moaDF_by_month_user_1,current_year_df_user_1,current_year_requested_user_1, moaDF_user_1)
# descending(moaDF_by_month_user_2, current_year_df_user_2, current_year_requested_user_2, moaDF_user_2)
# descending(moaDF_by_month_user_3, current_year_df_user_3, current_year_requested_user_3, moaDF_user_3)

# GSpread
# Name each sheet as a variable
# user_1
ws_user_11 = gc.open_by_url(google_sheets_link_user_1).get_worksheet(0)
ws_user_12 = gc.open_by_url(google_sheets_link_user_1).get_worksheet(1)
ws_user_13 = gc.open_by_url(google_sheets_link_user_1).get_worksheet(2)
ws_user_14 = gc.open_by_url(google_sheets_link_user_1).get_worksheet(3)
ws_user_15 = gc.open_by_url(google_sheets_link_user_1).get_worksheet(4)
ws_user_16 = gc.open_by_url(google_sheets_link_user_1).get_worksheet(5)

# # user_2
# ws_user_21 = gc.open_by_url(google_sheets_link_user_2).get_worksheet(0)
# ws_user_22 = gc.open_by_url(google_sheets_link_user_2).get_worksheet(1)
# ws_user_23 = gc.open_by_url(google_sheets_link_user_2).get_worksheet(2)
# ws_user_24 = gc.open_by_url(google_sheets_link_user_2).get_worksheet(3)
# ws_user_25 = gc.open_by_url(google_sheets_link_user_2).get_worksheet(4)
# ws_user_26 = gc.open_by_url(google_sheets_link_user_2).get_worksheet(5)

# # user_3
# ws_user_31 = gc.open_by_url(google_sheets_link_user_3).get_worksheet(0)
# ws_user_32 = gc.open_by_url(google_sheets_link_user_3).get_worksheet(1)
# ws_user_33 = gc.open_by_url(google_sheets_link_user_3).get_worksheet(2)
# ws_user_34 = gc.open_by_url(google_sheets_link_user_3).get_worksheet(3)
# ws_user_35 = gc.open_by_url(google_sheets_link_user_3).get_worksheet(4)
# ws_user_36 = gc.open_by_url(google_sheets_link_user_3).get_worksheet(5)

# Write Each to Google Sheets
row = 1
col = 1

#Check if its the first of the year, and clear the middle 2 sheets if it is
def clear_if_first(sheet1, sheet2, sheet3, goal_distance):
    today_date = datetime.now()
    if today_date.month == first_day_of_year.month and today_date.day == first_day_of_year.day:
        sheet2.clear()
        sheet3.clear()
        sheet1.clear()
        sheet1.update('A19', 'Annual Goal:')
        sheet1.update('A20', 'Average Required Miles per Month:')
        sheet1.update('A21', 'Average Required Miles per Week:')
        sheet1.update('B19', goal_distance)
        sheet1.update('A23', 'Workout Data by Month (All Time [Most Recent First])')
        sheet1.update('B20', '=B19/12') #Calculates Miles Needed per Month to achieve annual goal
        sheet1.update('B21', '=B19/(365/7)') #Calcualted Miles Needed per Month to achieve annual goal
    else:
        pass
    return sheet2, sheet3

clear_if_first(ws_user_11, ws_user_12, ws_user_13, goal_distance_user_1)
# clear_if_first(ws_user_21, ws_user_22, ws_user_23, goal_distance_user_2)
# clear_if_first(ws_user_31, ws_user_32, ws_user_33, goal_distance_user_3)

# Sort DFs in Descending Order (User Preference)
def descending(moaDF_by_month, current_year_df, current_year_requested,moaDF, moaDF_by_week):

    moaDF_by_month.sort_values(by=['Month/Year'], inplace=True, ascending=False)
    current_year_requested.sort_values(by=['Workout Date'], inplace=True, ascending=False)
    current_year_df.sort_values(by=['Workout Date'], inplace=True, ascending=False)
    moaDF.sort_values(by=['Workout Date'], inplace=True, ascending=False)
    moaDF_by_week.sort_values(by=['Workout Date'], inplace=True, ascending=False)

descending(moaDF_by_month_user_1,current_year_df_user_1,current_year_requested_user_1, moaDF_user_1, moaDF_by_week_user_1)
# descending(moaDF_by_month_user_2, current_year_df_user_2, current_year_requested_user_2, moaDF_user_2, moaDF_by_week_user_2)
# descending(moaDF_by_month_user_3, current_year_df_user_3, current_year_requested_user_3, moaDF_user_3, moaDF_by_week_user_3)

# DataFrame Formatting for setting to DF with GSpread
def format_for_gspread (df):
    df.index = pd.to_datetime(df.index)
    df.index = df.index.strftime('%Y-%m-%d')

# user_1
format_for_gspread(moaDF_user_1)
format_for_gspread(current_year_requested_user_1)
format_for_gspread(current_year_df_user_1)

# # user_2
# format_for_gspread(moaDF_user_2)
# format_for_gspread(current_year_requested_user_2)
# format_for_gspread(current_year_df_user_2)

# # user_3
# format_for_gspread(moaDF_user_3)
# format_for_gspread(current_year_requested_user_3)
# format_for_gspread(current_year_df_user_3)

# Add DFs to each sheet
# user_1 First
# SummaryDF
set_with_dataframe(ws_user_11, summary_df_user_1,row, col)
# Monthly
set_with_dataframe(ws_user_11, moaDF_by_month_user_1, row=24, col=1,include_index=True )
# Requested Data Current Year
set_with_dataframe(ws_user_12, current_year_requested_user_1, row, col, include_index= True)
# Current Year moaDF
set_with_dataframe(ws_user_13,current_year_df_user_1, row, col, include_index=True)
# Description Dataframes
set_with_dataframe(ws_user_14, descript_current_year_user_1, row, col,include_index=True)
# Current Year
# 2021
set_with_dataframe(ws_user_14, descript_user_1_2021, 12, col,include_index=True)
# 2022
set_with_dataframe(ws_user_14, descript_user_1_2022, 21, col,include_index=True)
# 2023
set_with_dataframe(ws_user_14, descript_user_1_2023, 30, col,include_index=True)
# All Time All Data (moaDF)
set_with_dataframe(ws_user_15, moaDF_user_1, row, col,include_index=True)

# # user_2 Second
# # SummaryDF
# set_with_dataframe(ws_user_21, summary_df_user_2,row, col)
# # Monthly
# set_with_dataframe(ws_user_21, moaDF_by_month_user_2, row=24, col=1,include_index=True )
# # Requested Data Current Year
# set_with_dataframe(ws_user_22, current_year_requested_user_2, row, col, include_index= True)
# # Current Year moaDF
# set_with_dataframe(ws_user_23,current_year_df_user_2, row, col, include_index=True)
# # Description Dataframes
# set_with_dataframe(ws_user_24, descript_current_year_user_2, row, col,include_index=True)
# # Current Year
# # 2021
# set_with_dataframe(ws_user_24, descript_user_2_2021, 12, col,include_index=True)
# # 2022
# set_with_dataframe(ws_user_24, descript_user_2_2022, 21, col,include_index=True)
# # 2023
# set_with_dataframe(ws_user_24, descript_user_2_2023, 30, col,include_index=True)
# # All Time All Data (moaDF)
# set_with_dataframe(ws_user_25, moaDF_user_2, row, col,include_index=True)

# # user_3 Third
# # SummaryDF
# set_with_dataframe(ws_user_31, summary_df_user_3,row, col)
# # Monthly
# set_with_dataframe(ws_user_31, moaDF_by_month_user_3, row=24, col=1,include_index=True )
# # Requested Data Current Year
# set_with_dataframe(ws_user_32, current_year_requested_user_3, row, col, include_index= True)
# # Current Year moaDF
# set_with_dataframe(ws_user_33,current_year_df_user_3, row, col, include_index=True)
# # Description Dataframes
# set_with_dataframe(ws_user_34, descript_current_year_user_3, row, col,include_index=True)
# # Current Year
# # 2021
# set_with_dataframe(ws_user_34, descript_user_3_2021, 12, col,include_index=True)
# # 2022
# set_with_dataframe(ws_user_34, descript_user_3_2022, 21, col,include_index=True)
# # 2023
# set_with_dataframe(ws_user_34, descript_user_3_2023, 30, col,include_index=True)
# # All Time All Data (moaDF)
# set_with_dataframe(ws_user_35, moaDF_user_3, row, col,include_index=True)

# This is the email we send from if you want to use the email or text update function (currently commented out)
gmail_user = 'gmailaccount@gmail.com'
gmail_password = 'password'

# Send Text Update
def send_text_update(phone_number, summary_df, sheets_link, username):
    time_now = datetime.now()    

    def find_by_postfix(postfix, folder):
        for root, _, files in os.walk(folder):
            for file in files:
                if file.endswith(postfix):
                    yield os.path.join(root, file)

    user_graphs = find_by_postfix('.jpg', graph_path + username + '/')
    
    if time_now.hour < 16:
        pass
    
    else:
        current_pace = summary_df.iloc[8]['Value']
        total_distance = summary_df.iloc[3]['Value']
        most_recent_workout = summary_df.iloc[1]['Value']
        sms_gateway = str(phone_number)+'@tmomail.net' #in order to send SMS, need to know carrier 
                                                        # AT&T: [number]@txt.att.net
                                                        # Sprint: [number]@messaging.sprintpcs.com or [number]@pm .sprint.com
                                                        # T-Mobile: [number]@tmomail.net
                                                        # Verizon: [number]@vtext.com
                                                        # Boost Mobile: [number]@myboostmobile.com
                                                        # Cricket: [number]@sms.mycricket.com
                                                        # Metro PCS: [number]@mymetropcs.com
                                                        # Tracfone: [number]@mmst5.tracfone.com
                                                        # U.S. Cellular: [number]@email.uscc.net
                                                        # Virgin Mobile: [number]@vmobl.com
        # The server we use to send emails in our case it will be gmail but every email provider has a different smtp 
        # and port is also provided by the email provider.
        smtp = "smtp.gmail.com" 
        port = 587
        # This will start our email server
        server = smtplib.SMTP(smtp,port)
        # Starting the server
        server.starttls()
        # Now we need to login
        server.login(gmail_user,gmail_password)

        # Now we use the MIME module to structure our message.
        msg = MIMEMultipart()
        msg['From'] = gmail_user
        msg['To'] = sms_gateway
        # Make sure you add a new line in the subject
        msg['Subject'] = f'Daily Wrap {today}\n'
        # Make sure you also add new lines to your body
        body = f'Your workout tracker has been updated on your peloton output file via automatic scripting. So far this year, you have ridden {total_distance} \
                 miles. Your most recent ride was on  {most_recent_workout}. You are currently on pace for {current_pace} miles this year. You can access the file here: \
                {sheets_link}\nYour Graphs can be found below:'
        # and then attach that body
        msg.attach(MIMEText(body, 'plain'))

        for image in user_graphs:
            with open(image, 'rb') as fp:
                img = MIMEImage(fp.read(),_subtype='jpg')
                img.add_header('Content-Disposition', 'attachment', filename= image.split('/')[-1])
        
        msg.attach(img)

        sms = msg.as_string()

        server.sendmail(gmail_user,sms_gateway,sms)

        # lastly quit the server
        server.quit()

send_text_update(phone_user_1,summary_df_user_1,google_sheets_link_user_1,username_user_1)
# send_text_update(phone_user_2,summary_df_user_2,google_sheets_link_user_2, username_user_2)
# send_text_update(phone_user_3,summary_df_user_3,google_sheets_link_user_3, username_user_3)

# Create the email function
def send_email_update (email, username, summary_df,sheets_link):
    time_now = datetime.now()    
    if time_now.hour < 16:
        pass
    else:
       
        current_pace = summary_df.iloc[8]['Value']
       
        total_distance = summary_df.iloc[3]['Value']
       
        most_recent_workout = summary_df.iloc[1]['Value']
       
        sent_from = gmail_user
       
        to = str(email)
       
        subject = 'Daily Wrap for ' + username
       
        body = f'Your workout tracker has been updated on your peloton output file via automatic scripting. So far this year, you have ridden {total_distance} \
                 miles. Your most recent ride was on  {most_recent_workout}. You are currently on pace for {current_pace} miles this year. You can access the file here: \
                {sheets_link}\nYour Graphs can be found below:'

        email_text = '''\
        
        From: %s
        
        To: %s
        
        Subject: %s
        
        %s
        
        '''% (sent_from,','.join(to),subject,body)
        
        try:
        
            smtp_server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        
            smtp_server.ehlo()
        
            smtp_server.login(gmail_user, gmail_password)
        
            smtp_server.sendmail(sent_from, to, email_text)
        
            smtp_server.close()
        
        except Exception as ex:
        
            print ("Something went wrong….",ex)

# Send the emails via SMTP
# send_email_update(email_user_1, username_user_1, summary_df_user_1, google_sheets_link_user_1)
# send_email_update(email_user_2, username_user_2, summary_df_user_2, google_sheets_link_user_2)
# send_email_update(email_user_3, username_user_3, summary_df_user_3, google_sheets_link_user_3)