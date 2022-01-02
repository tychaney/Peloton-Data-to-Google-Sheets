import pandas as pd
import plotly.express as px
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import date, datetime
import requests
import smtplib
import numpy as np
from gspread_dataframe import set_with_dataframe
from matplotlib import pyplot as plt
import seaborn as sns

# Google API. Reference the API Documentation linked in the README
# Note that you don't have to use Google Sheets, it just makes it easier to run for a user using a raspberry pi or similar device
# You WILL need to set up an individual service account to use this on your own device with Google sheets
scopes = ['https://www.googleapis.com/auth/spreadsheets',
'https://www.googleapis.com/auth/drive']

credentials = ServiceAccountCredentials.from_json_keyfile_name('PelotonToGoogle.json', scopes) #see the API documentation for explanation. 'PelotonToGoogle' is what I named the file

gc = gspread.service_account('/path/PelotonToGoogle.json')

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


# Login to Peloton and Download workouts
login_data = pd.read_csv('LoginData.csv')

login_df = pd.DataFrame(login_data)

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

        if email == 'email_user1@msn.com':
      
            download_data = s.get('Peloton CSV Link', allow_redirects=True)
      
        else:
      
            download_data = s.get('Peloton CSV Link', allow_redirects=True)

        csv_file = username + '.csv'

        with open(csv_file, 'wb') as f:

            f.write(download_data.content)
        
        index += 1
    return index    
    
# Create Logon Variables

email_user_1 = login_df.iloc[0]['email']

password_user_1 = login_df.iloc[0]['password']

username_user_1 = login_df.iloc[0]['username']

email_user_2 = login_df.iloc[1]['email']

password_user_2 = login_df.iloc[1]['password']

username_user_2 = login_df.iloc[1]['username']

# Global Goal Variables
goal_distance_user_1 = gc.open_by_url('user_1_Google_Sheets_Link').get_worksheet(0).acell('B19').value

goal_distance_user_2 = gc.open_by_url('user_2_Google_Sheets_Link').get_worksheet(0).acell('B19').value

# Get the Raw Data
get_API_data(login_df)

peloton_data_user_1 = pd.read_csv('user_1_username.csv')

peloton_df_user_1 = pd.DataFrame(peloton_data_user_1)

peloton_data_user_2 = pd.read_csv('user_2_username.csv')

peloton_df_user_2 = pd.DataFrame(peloton_data_user_2)

# Remove all non cycling (This step is only for those who are only interested in cycling)
def change_df_cycling_only (workout_df):

    cycling_only = workout_df[workout_df['Fitness Discipline'] == 'Cycling']

    return cycling_only

cycling_only_user_1 = change_df_cycling_only(peloton_df_user_1)

cycling_only_user_2 = change_df_cycling_only(peloton_df_user_2)

# Make the big dataframe with everything in it
def simplify_df_all_data (cycling_only):
    
    # this is the requested data
    workout_data_we_want = cycling_only[['Workout Timestamp', 
                                    'Length (minutes)', 'Total Output', 
                                    'Distance (mi)', 'Calories Burned']]
    
    # This is the rest of the data (called avg df because they are averages)
    average_df = cycling_only[['Workout Timestamp', 
                                'Avg. Watts', 'Avg. Resistance', 
                                'Avg. Cadence (RPM)', 'Avg. Speed (mph)',
                                'Avg. Heartrate']]

    # Change date formats
    workout_data_we_want['Workout Date'] = workout_data_we_want['Workout Timestamp'].str[:10]
    
    average_df['Workout Date'] = average_df['Workout Timestamp'].str[:10]
    
    # Reorder the data so it's more readable
    workout_data_we_want = workout_data_we_want[['Workout Date', 'Length (minutes)', 
                                                    'Total Output', 'Distance (mi)', 'Calories Burned']]

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
    average_df = average_df[['Workout Date', 
                            'Avg. Watts', 'Avg. Resistance', 
                            'Avg. Cadence (RPM)', 'Avg. Speed (mph)',
                            'Avg. Heartrate']]

    # Fix Percentages
    average_df['Avg. Resistance'] = average_df['Avg. Resistance'].str.rstrip('%').astype('float') / 100.0
        
    # Remove instances of none and replace with '0'
    average_df = average_df.replace('None', 0)

    # strings to numeric
    average_df = average_df[['Workout Date', 
                            'Avg. Watts', 'Avg. Resistance', 
                            'Avg. Cadence (RPM)', 'Avg. Speed (mph)',
                            'Avg. Heartrate']].apply(pd.to_numeric, errors = 'ignore')

    #  convert workout date to date
    average_df['Workout Date'] = pd.to_datetime(average_df['Workout Date']).dt.date

    # Average the values together
    average_df = average_df.groupby('Workout Date').mean()

    # At this point we have 'clean' versions of both DFs
    # Below is the combination of DFs to 1 big dataframe (Mother of All DataFrames)
    moaDF = workout_data_we_want.join(average_df)

    moaDF = moaDF.fillna(0)

    # Current Year by Month
    workout_data_we_want_copy = workout_data_we_want

    workout_data_we_want_copy.index = pd.to_datetime(workout_data_we_want_copy.index)    
    
    data_by_month = workout_data_we_want_copy.groupby(pd.Grouper(freq='M')).sum()

    data_by_month.index = data_by_month.index.strftime('%m/%y')

    average_df_copy = average_df
    
    average_df_copy.index = pd.to_datetime(average_df_copy.index)    

    data_by_month_avg = average_df_copy.groupby(pd.Grouper(freq='M')).mean()

    data_by_month_avg.index = data_by_month_avg.index.strftime('%m/%y')

    moaDF_by_month = data_by_month.join(data_by_month_avg)

    moaDF_by_month = moaDF_by_month.fillna(0)

    moaDF_by_month.index.rename('Month/Year', inplace=True)

    return moaDF, moaDF_by_month, workout_data_we_want_copy

# Create the Giant moaDF's (all time data)
moaDF_user_1, moaDF_by_month_user_1, requested_user_1 = simplify_df_all_data(cycling_only_user_1)

moaDF_user_2, moaDF_by_month_user_2, requested_user_2 = simplify_df_all_data(cycling_only_user_2)

# Create Data Frames which only include data from current year
current_year_df_user_1 = moaDF_user_1[~(moaDF_user_1.index <= first_day_of_year)]

current_year_df_user_2 = moaDF_user_2[~(moaDF_user_2.index <= first_day_of_year)]

current_year_requested_user_1 = requested_user_1[requested_user_1.index.year == today.year]

current_year_requested_user_2 = requested_user_2[requested_user_2.index.year == today.year]

# Sort by month DFs in Descending Order
moaDF_by_month_user_1.sort_values(by=['Month/Year'], inplace=True, ascending=False)

moaDF_by_month_user_2.sort_values(by=['Month/Year'], inplace=True, ascending=False)

# Conduct Calculations
def calculations (goal_distance, current_year_df ,moaDF_all_time):

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

    most_recent_workout = moaDF_all_time.index[-1]

    # Summary Data Frame for Excel
    calculations = ['Today', 'Most Recent Workout','Goal Distance (mi)', 'Current Total Distance (mi)',
            'Total Distance from Goal', 'Percent of Goal Achieved (%)',
            'Total Days Elapsed This Year', 'Total Days Left This Year',
            'Current Pace by End of Year (mi)', 'Goal Distance - Pace', 'Average Ride Length (minutes)', 
            'Average Ride Output', 'Average Distance Per Ride (mi)', 
            'Average Calories Burned Per Ride (kCal)']

    values = [str(today), str(most_recent_workout) ,int(goal_distance), round(total_distance, 2), 
            round (distance_from_goal, 2), round(percent_of_goal, 4), 
            str(days_so_far_float), str(days_left_in_year_float), round(pace, 2), round(pace_versus_goal, 2),round(avg_length, 2), 
            round(avg_output, 2), round(avg_distance, 2), round(avg_calories, 2)]

    summary = {'Metric': calculations, 'Value': values}

    summary_df = pd.DataFrame(summary)

    return summary_df

# Create the Summary DFs which will be displayed on Sheet1
summary_df_user_1 = calculations(goal_distance_user_1, current_year_df_user_1, moaDF_user_1)

summary_df_user_2 = calculations(goal_distance_user_2, current_year_df_user_2, moaDF_user_2)

# Create Descriptive Stats DF
def describe_by_year (moaDF_all_time, year):
    
    moaDF_all_time.index = pd.to_datetime(moaDF_all_time.index)

    moaDF_year = moaDF_all_time[moaDF_all_time.index.year == year]

    description_df = moaDF_year.replace(0, np.NaN).describe()

    return description_df

# Create Describe DFs for Years Requested
descript_current_year_user_1 = describe_by_year(moaDF_user_1, today.year)

descript_current_year_user_2 = describe_by_year(moaDF_user_2, today.year)

descript_user_1_2021 = describe_by_year(moaDF_user_1, 2021)

descript_user_1_2022 = describe_by_year(moaDF_user_1, 2022)

descript_user_1_2023 = describe_by_year(moaDF_user_1, 2023)

descript_user_2_2021 = describe_by_year(moaDF_user_2, 2021)

descript_user_2_2022 = describe_by_year(moaDF_user_2, 2022)

descript_user_2_2023 = describe_by_year(moaDF_user_2, 2023)

# Graph Making
# Seaborn First
# Make KDE Plot
def make_sns_plots (username, moaDF_all_time):
    
    moaDF_all_time.index = pd.to_datetime(moaDF_all_time.index)

    avg_hr_all_time = moaDF_all_time['Avg. Heartrate']

    avg_hr_all_time = [i for i in avg_hr_all_time if i != 0]

    sns.set_style("darkgrid")
    
    sns.kdeplot(avg_hr_all_time, shade=True)

    # plt.legend()

    plt.title(username + ' Average HR per Ride KDE All Time')

    plt.savefig('/path/' + username + '_Average_HR_KDE.jpeg')

    plt.clf()

    # Remove all 0s
    moaDF_all_time[moaDF_all_time <= 0] = np.nan
    
    # Make a boxplot by Year
    sns.set_style("darkgrid")
    
    sns.violinplot(data = moaDF_all_time, x=moaDF_all_time.index.year, y= 'Avg. Heartrate')

    plt.title(username + ' Average Heartrate per Ride (by Year)')

    plt.savefig('/path/' + username + '_Average_HR_by_year.jpeg')

    plt.clf()

    # Make a boxplot by month
    # Heartrate
    sns.set_style("darkgrid")

    sns.boxplot(data = moaDF_all_time, x=moaDF_all_time.index.to_period('M'), y= 'Avg. Heartrate')
    
    plt.title(username + ' Average Heartrate per Ride (by Year)')

    plt.savefig('/path/' + username + '_Average_HR_by_month.jpeg')

    plt.clf()

    # Make a Violin Chart off of HR
    sns.set_style("darkgrid")
    
    sns.violinplot(data = moaDF_all_time, x=moaDF_all_time.index.to_period('M'), y= 'Avg. Heartrate')
    
    plt.title(username + ' Average Heartrate per Ride (by Month)')

    plt.savefig('/path/' + username + '_Violin_Average_HR_by_month.jpg')

    plt.clf()

    # Output
    # Make a violin plot by Year for HR
    sns.set_style("darkgrid")

    sns.violinplot(data = moaDF_all_time, x=moaDF_all_time.index.year, y= 'Total Output')

    plt.title(username + ' Total Output per Ride (by Year)')

    plt.savefig('/path/' + username + '_Total_Output_by_year.jpg')

    plt.clf()

    # Violin By Month
    sns.set_style('darkgrid')

    sns.violinplot(data = moaDF_all_time, x=moaDF_all_time.index.to_period('M'), y= 'Total Output')
    
    plt.title(username + ' Total Output per Ride (by Month)')

    plt.savefig('/path/' + username + '_Violin_Total Output_by_month.jpg')

    plt.clf()

    # Boxplot per Month
    sns.set_style('darkgrid')

    sns.boxplot(data = moaDF_all_time, x=moaDF_all_time.index.to_period('M'), y= 'Total Output')
    
    plt.title(username + ' Total Output per Ride (by Month)')

    plt.savefig('/path/' + username + '_Boxplot_Total Output_by_month.jpg')

    plt.clf()

make_sns_plots(username_user_1, moaDF_user_1)

make_sns_plots(username_user_2, moaDF_user_2)

#Chart with Plotly
def make_charts(requested_workout_data,username):    
    
    figOutput_Distance = px.scatter(requested_workout_data, x = 'Total Output', y = 'Distance (mi)', color = 'Length (minutes)')

    figOutput_Distance.update_layout(autosize = True, width = 1200, height = 900, font_size = 22)

    figOutput_Distance.update_traces(marker=dict(size=12,line=dict(width=3, color='DarkSlateGrey')),
                  selector=dict(mode='markers'))

    figOutput_Distance.write_image('/path/' + username + '_Output_to_Distance2D.jpeg')           

make_charts(current_year_requested_user_1, username_user_1)

make_charts(current_year_requested_user_2, username_user_2)

# GSpread
# Name each sheet as a variable
ws_user_11 = gc.open_by_url('user_1_Google_Sheets_Link').get_worksheet(0)

ws_user_12 = gc.open_by_url('user_1_Google_Sheets_Link').get_worksheet(1)

ws_user_13 = gc.open_by_url('user_1_Google_Sheets_Link').get_worksheet(2)

ws_user_14 = gc.open_by_url('user_1_Google_Sheets_Link').get_worksheet(3)

ws_user_15 = gc.open_by_url('user_1_Google_Sheets_Link').get_worksheet(4)

ws_user_16 = gc.open_by_url('user_1_Google_Sheets_Link').get_worksheet(5)

ws_user_21 = gc.open_by_url('user_2_Google_Sheets_Link').get_worksheet(0)

ws_user_22 = gc.open_by_url('user_2_Google_Sheets_Link').get_worksheet(1)

ws_user_23 = gc.open_by_url('user_2_Google_Sheets_Link').get_worksheet(2)

ws_user_24 = gc.open_by_url('user_2_Google_Sheets_Link').get_worksheet(3)

ws_user_25 = gc.open_by_url('user_2_Google_Sheets_Link').get_worksheet(4)

ws_user_26 = gc.open_by_url('user_2_Google_Sheets_Link').get_worksheet(5)

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

        sheet1.update('B19', goal_distance)

        sheet1.update('A23', 'Workout Data by Month (All Time [Most Recent First])')

    else:

        pass

    return sheet2, sheet3

clear_if_first(ws_user_11, ws_user_12, ws_user_13, goal_distance_user_1)

clear_if_first(ws_user_21, ws_user_22, ws_user_23, goal_distance_user_2)

# DataFrame Formatting for setting to DF with GSpread. This is just for neatness prior to setting with GSpread
def format_for_gspread (df):

    df.index = pd.to_datetime(df.index)

    df.index = df.index.strftime('%Y-%m-%d')

# user_1
format_for_gspread(moaDF_user_1)

format_for_gspread(current_year_requested_user_1)

format_for_gspread(current_year_df_user_1)

# user_2
format_for_gspread(moaDF_user_2)

format_for_gspread(current_year_requested_user_2)

format_for_gspread(current_year_df_user_2)

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

# user_2 Second
# SummaryDF
set_with_dataframe(ws_user_21, summary_df_user_2,row, col)
# Monthly
set_with_dataframe(ws_user_21, moaDF_by_month_user_2, row=24, col=1,include_index=True )
# Requested Data Current Year
set_with_dataframe(ws_user_22, current_year_requested_user_2, row, col, include_index= True)
# Current Year moaDF
set_with_dataframe(ws_user_23,current_year_df_user_2, row, col, include_index=True)
# Description Dataframes
set_with_dataframe(ws_user_24, descript_current_year_user_2, row, col,include_index=True)
# Current Year
# 2021
set_with_dataframe(ws_user_24, descript_user_2_2021, 12, col,include_index=True)
# 2022
set_with_dataframe(ws_user_24, descript_user_2_2022, 21, col,include_index=True)
# 2023
set_with_dataframe(ws_user_24, descript_user_2_2023, 30, col,include_index=True)
# All Time All Data (moaDF)
set_with_dataframe(ws_user_25, moaDF_user_2, row, col,include_index=True)

gmail_user = 'email@gmail.com'

gmail_password = 'password'

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

        body = 'Your workout tracker has been updated on your peloton output file via automatic scripting. So far this year, you have ridden ' + str(total_distance) + \
        ' miles. Your most recent ride was on ' + str(most_recent_workout) + '. You are currently on pace for ' + str(current_pace) + ' miles this year. You can access the file here: ' + str(sheets_link)
        
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

send_email_update(email_user_1, username_user_1, summary_df_user_1, 'user_1_Google_Sheets_Link')

send_email_update(email_user_2, username_user_2, summary_df_user_2, 'user_2_Google_Sheets_Link')