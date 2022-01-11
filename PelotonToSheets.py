# Version 2.0.0 Current As Of 11JAN22
# SIGNIFICANT CODE EDITING COURTESY OF JHJCo
# Now command line inputs are available if you see errors, additionally, the code automatically iterates through users based on the CSV
# Additional Changes include the changing of years from hard coded (2021, 2022, 2023) to current year, last year, and 2 years prior so no need to adjust code each year
# The next edit coming soon will be the rounding of all numbers to 2 decimal places for ease of reading
# For what started as a simple favor to my dad, the support I've gotten has been incredible, HAPPY RIDING!

import os #For sending the text message
import pandas as pd
pd.options.mode.chained_assignment = None  # default='warn'
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
import argparse
import sys
import calendar

## Let's accept some command line input to streamline some things
## --folder is an input arg that says what folder the LoginData.csv is in
## --sendtext and --sendemail are boolean arguments. Set them to True to enable either of these functionalities
## note that you will need to populate the gmail credentials and/or the mobile provider if you enable them
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--folder', type=str, help="Location of LoginData.csv with the trailing slash", required=True)
    parser.add_argument('--sendtext', type=bool, help="Set to True to send a text message", default=False)
    parser.add_argument('--sendemail', type=bool, help="Set to True to send an email message", default=False)
    args = parser.parse_args()
    folder = args.folder
    sendtext = args.sendtext
    sendemail = args.sendemail

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

# Month
first_day_of_month = date(today.year, today.month, 1)
last_day_of_month =  date(today.year, today.month, calendar.monthrange(today.year, today.month)[1])
days_left_in_month = last_day_of_month - today
days_left_in_month_float = float(days_left_in_month.days)
total_days_in_month = last_day_of_month - first_day_of_month
total_days_in_month_float = float(total_days_in_month.days)
days_so_far_month = today - first_day_of_month
days_so_far_month_float = float(days_so_far_month.days + 1)

# This is the email we send from if you want to use the email or text update function
gmail_user = 'gmailaccount@gmail.com'
gmail_password = 'password'

# This was added to ease use for those with limited Coding Experience
# Pull the Admin Variables from the CSV
login_data = pd.read_csv(folder + 'LoginData.csv')
login_df = pd.DataFrame(login_data)

## Below is all the internal functions. Moved to top for clarity

# Get Workout CSVs
def get_peloton_data(email_user, password_user, username_user, peloton_csv_link):
    s = requests.Session()
    payload = {'username_or_email': email_user, 'password': password_user}
    s.post('https://api.onepeloton.com/auth/login', json=payload)
    download_data = s.get(peloton_csv_link, allow_redirects=True)
    csv_file = str(username_user) + '.csv'
    with open(csv_file, 'wb') as f:
        f.write(download_data.content)

# Remove non cycling workouts
def change_df_cycling_only(workout_df):
    cycling_only = workout_df[workout_df['Fitness Discipline'] == 'Cycling']
    return cycling_only

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
    workout_data_we_want.index = pd.to_datetime(workout_data_we_want.index)    
    data_by_month = workout_data_we_want.groupby(pd.Grouper(freq='M')).sum()
    data_by_month.index = data_by_month.index.strftime('%Y/%m')
    # Current Year by Week (for pace calculation Purposes) (requested data)
    data_by_week = workout_data_we_want.groupby(pd.Grouper(freq='W-SUN')).sum()
    data_by_week.index = data_by_week.index.strftime('%Y/%m/%d')
    average_df = average_df
    average_df.index = pd.to_datetime(average_df.index)    
    # Current year by month (Average)
    data_by_month_avg = average_df.groupby(pd.Grouper(freq='M')).mean()
    data_by_month_avg.index = data_by_month_avg.index.strftime('%Y/%m')
    # Current Year by Week (for pace calculation Purposes) (non-requested data)
    data_by_week_avg = average_df.groupby(pd.Grouper(freq='W-SUN')).mean()
    data_by_week_avg.index = data_by_week_avg.index.strftime('%Y/%m/%d')  
    # Make the moaDF by Month
    moaDF_by_month = data_by_month.join(data_by_month_avg)
    moaDF_by_month = moaDF_by_month.fillna(0)
    moaDF_by_month.index.rename('Month/Year', inplace=True)
    # Make the moaDF by Week
    moaDF_by_week =data_by_week.join(data_by_week_avg)
    moaDF_by_week = moaDF_by_week.fillna(0)
    # Add Calories per Mile
    workout_data_we_want['Calories/Mile'] = round(workout_data_we_want['Calories Burned']/workout_data_we_want['Distance (mi)'],2)
    return moaDF, moaDF_by_month, workout_data_we_want, moaDF_by_week

# Conduct Calculations
def calculations(goal_distance, current_year_df ,moaDF_all_time, moaDF_by_month, moaDF_by_week):
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
    pace_month = (miles_current_month / days_so_far_month_float) * (total_days_in_month_float)
    # Summary Data Frame for Sheets
    calculations = [
            'Today', 'Most Recent Workout','Goal Distance (mi)', 'Current Total Distance (mi)',
            'Total Distance from Goal', 'Percent of Goal Achieved (%)',
            'Total Days Elapsed This Year', 'Total Days Left This Year',
            'Current Pace by End of Year (mi)', 'Goal Distance - Pace', 'Average Ride Length (minutes)', 
            'Average Ride Output', 'Average Distance Per Ride (mi)', 
            'Average Calories Burned Per Ride (kCal)', 'Miles Ridden This Month', 'Pace This Month', 'Miles Ridden This Week (Starting Mon)'
            ]
    values = [
            str(today), str(most_recent_workout) ,int(goal_distance), round(total_distance, 2), 
            round (distance_from_goal, 2), round(percent_of_goal, 4), str(days_so_far_float), 
            str(days_left_in_year_float), round(pace, 2), round(pace_versus_goal, 2),round(avg_length, 2), 
            round(avg_output, 2), round(avg_distance, 2), round(avg_calories, 2), round(miles_current_month,2), 
            round(pace_month, 2),round(miles_this_week, 2)
            ]
    summary = {'Metric': calculations, 'Value': values}
    summary_df = pd.DataFrame(summary)
    return summary_df

# Create Descriptive Stats DF
def describe_by_year(moaDF_all_time, year):
    moaDF_all_time.index = pd.to_datetime(moaDF_all_time.index)
    moaDF_year = moaDF_all_time[moaDF_all_time.index.year == year]
    description_df = moaDF_year.replace(0, np.NaN).describe()
    return description_df

def make_sns_plots(username, moaDF_all_time):    
    moaDF_all_time.index = pd.to_datetime(moaDF_all_time.index)
    avg_hr_all_time = moaDF_all_time['Avg. Heartrate']
    avg_hr_all_time = [i for i in avg_hr_all_time if i != 0]
    plt.figure(figsize = (15,8))
    sns.set_style("darkgrid")
    sns.kdeplot(avg_hr_all_time, shade=True)

    # Check if graph path exists. If it doesn't, create it
    if not os.path.isdir(graph_path + username):
        print ("Creating Graphs directory")
        os.mkdir(graph_path + username)

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

def make_charts(requested_workout_data,username):        
    figOutput_Distance = px.scatter(requested_workout_data, x = 'Total Output', y = 'Distance (mi)', color = 'Length (minutes)')
    figOutput_Distance.update_layout(autosize = True, width = 1200, height = 900, font_size = 22)
    figOutput_Distance.update_traces(marker=dict(size=12,line=dict(width=3, color='DarkSlateGrey')),
                  selector=dict(mode='markers'))
    figOutput_Distance.write_image(graph_path + username + '/' + username +  '_Output_to_Distance2D.jpg')  

def descending(moaDF_by_month, current_year_df, current_year_requested,moaDF):

    moaDF_by_month.sort_values(by=['Month/Year'], inplace=True, ascending=False)
    current_year_requested.sort_values(by=['Workout Date'], inplace=True, ascending=False)
    current_year_df.sort_values(by=['Workout Date'], inplace=True, ascending=False)
    moaDF.sort_values(by=['Workout Date'], inplace=True, ascending=False)

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

def descending_user(moaDF_by_month, current_year_df, current_year_requested,moaDF, moaDF_by_week):

    moaDF_by_month.sort_values(by=['Month/Year'], inplace=True, ascending=False)
    current_year_requested.sort_values(by=['Workout Date'], inplace=True, ascending=False)
    current_year_df.sort_values(by=['Workout Date'], inplace=True, ascending=False)
    moaDF.sort_values(by=['Workout Date'], inplace=True, ascending=False)
    moaDF_by_week.sort_values(by=['Workout Date'], inplace=True, ascending=False)


def format_for_gspread(df):
    df.index = pd.to_datetime(df.index)
    df.index = df.index.strftime('%Y-%m-%d')

def find_by_postfix(postfix, graph_path):
    for root, _, files in os.walk(graph_path):
        for file in files:
            if file.endswith(postfix):
                yield os.path.join(root, file)

def send_text_update(phone_number, summary_df, sheets_link, username):
    time_now = datetime.now()    

    user_graphs = find_by_postfix('.jpg', graph_path + username + '/')
    
    if time_now.hour < 16:
        pass
    
    else:
        current_pace = summary_df.iloc[8]['Value']
        total_distance = summary_df.iloc[3]['Value']
        most_recent_workout = summary_df.iloc[1]['Value']
        sms_gateway = f'{phone_number}@tmomail.net' #in order to send SMS, need to know carrier 
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

def send_email_update(email, username, summary_df,sheets_link):
    time_now = datetime.now()    
    time_now = datetime.now()    

    user_graphs = find_by_postfix('.jpg', graph_path + username + '/')
    
    if time_now.hour < 16:
        pass
    
    else:
        current_pace = summary_df.iloc[8]['Value']
        total_distance = summary_df.iloc[3]['Value']
        most_recent_workout = summary_df.iloc[1]['Value']
        sms_gateway = email
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

## End of functions
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
    service_account_path = login_df.iloc[indexcount]['Path for Service Account JSON'] #Same for all users
    graph_path = login_df.iloc[indexcount]['Path to Save Graphs']
    indexcount += 1

    print("Starting work on " + email_user)

    # Google API
    scopes = ['https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive']
    credentials = ServiceAccountCredentials.from_json_keyfile_name('PelotonToGoogle.json', scopes) #see the API documentation for explanation. 'PelotonToGoogle' is what I named the file
    gc = gspread.service_account(service_account_path + 'PelotonToGoogle.json')

    # Global Goal Variables
    goal_distance = gc.open_by_url(google_sheets_link).get_worksheet(0).acell('B19').value

    # Get the Raw Data
    get_peloton_data(email_user, password_user, username_user, peloton_csv_link)
    peloton_data_user = pd.read_csv(username_user + '.csv')
    peloton_df_user = pd.DataFrame(peloton_data_user)

    # Remove all non cycling data
    cycling_only_user = change_df_cycling_only(peloton_df_user)

    # Create the Giant moaDF's (all time data)
    moaDF_user, moaDF_by_month_user, requested_user, moaDF_by_week_user = simplify_df_all_data(cycling_only_user)

    # Create Data Frames which only include data from current year
    current_year_df_user = moaDF_user[~(moaDF_user.index <= first_day_of_year)]
    current_year_requested_user = requested_user[requested_user.index.year == today.year]

    # Create the Summary DFs which will be displayed on Sheet1
    summary_df_user = calculations(goal_distance, current_year_df_user, moaDF_user,moaDF_by_month_user, moaDF_by_week_user)

    # Create Describe DFs for Years Requested
    # Current Year
    descript_current_year_user = describe_by_year(moaDF_user, today.year)
    descript_user_last_year = describe_by_year(moaDF_user, today.year - 1)
    descript_user_two_years_ago = describe_by_year(moaDF_user, today.year - 2)
    descript_user_three_years_ago = describe_by_year(moaDF_user, today.year - 3)

    # Graph Making
    # Seaborn First
    # Make KDE Plot
    make_sns_plots(username_user, moaDF_user)

    #Chart with Plotly
    make_charts(current_year_requested_user, username_user)

    # Sort DFs in Descending Order (User Preference)
    descending(moaDF_by_month_user,current_year_df_user,current_year_requested_user, moaDF_user)

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

    #Check if its the first of the year, and clear the middle 2 sheets if it is
    clear_if_first(ws_user_11, ws_user_12, ws_user_13, goal_distance)

    # Sort DFs in Descending Order (User Preference)
    descending_user(moaDF_by_month_user,current_year_df_user,current_year_requested_user, moaDF_user, moaDF_by_week_user)

    # DataFrame Formatting for setting to DF with GSpread
    format_for_gspread(moaDF_user)
    format_for_gspread(current_year_requested_user)
    format_for_gspread(current_year_df_user)

    # Add DFs to each sheet
    # SummaryDF
    set_with_dataframe(ws_user_11, summary_df_user, row, col)
    # Monthly
    set_with_dataframe(ws_user_11, moaDF_by_month_user, row=24, col=1,include_index=True )
    # Requested Data Current Year
    set_with_dataframe(ws_user_12, current_year_requested_user, row, col, include_index= True)
    # Current Year moaDF
    set_with_dataframe(ws_user_13,current_year_df_user, row, col, include_index=True)
    # Description Dataframes
    # Current Year
    set_with_dataframe(ws_user_14, descript_current_year_user, row, col,include_index=True)
    ws_user_14.update('K2', str(today.year))
    # Last Year
    set_with_dataframe(ws_user_14, descript_user_last_year, 12, col,include_index=True)
    ws_user_14.update('K12', str(today.year - 1))
    # 2 Years Ago
    set_with_dataframe(ws_user_14, descript_user_two_years_ago, 21, col,include_index=True)
    ws_user_14.update('K21', str(today.year - 2))
    # 3 Years Ago
    set_with_dataframe(ws_user_14, descript_user_three_years_ago, 30, col,include_index=True)
    ws_user_14.update('K30', str(today.year - 3))
    # All Time All Data (moaDF)
    set_with_dataframe(ws_user_15, moaDF_user, row, col,include_index=True)

    if sendtext:
        send_text_update(phone_user,summary_df_user,google_sheets_link,username_user)

    if sendemail:
        send_email_update(email_user, username_user, summary_df_user, google_sheets_link)