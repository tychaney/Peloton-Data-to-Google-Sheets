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

```bash

pip install pandas
pip install seaborn
pip install matplotlib
pip install gspread
pip install plotly
pip install plotly.express
pip install oauth2client
pip install gspread_dataframe
pip install numpy

```


# The CSV file used for importing data can be found here:

[LoginData.csv](https://github.com/tychaney/Peloton-Data-to-Google-Sheets/files/7835659/LoginData.csv)

# For formatting of your Google Sheet:

https://docs.google.com/spreadsheets/d/1ZfYI-NGeTK08VAQsnpXk_e_z_mnyT_7vX98O82nLxPY/edit#gid=1196700570

# To Run the Script (Ensure the Login.CSV is stored in the same directory)[Note: if you already have python set as the alias, no need for 'python3']

```bash

python3 PelotonToSheets.py

```
#In-Depth Look at the Script

The first part of the script takes the data provided in the Login.csv file and applies each value to user-specific variables. Please note, for more than 1 user, the paths for graphs and the Google Sheets API JSON will be the same for all users

```python
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
```

Following the aquisition of data, the script logs into Peloton and downloads the user's CSV file, and creates an intitial dataframe

```python
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
```

Following this, the data is simplified to cycling only, with other DFs created for data usage later on. Additionally, a 'Summary DF' is also created

```python
# Remove all non cycling
def change_df_cycling_only (workout_df):
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
```
Then Plots are created using Seaborn and Plotly (These are saved to a specified path [noted earlier] and are sent via text at the end of the day [if running on a Pi type device based on time])

```python
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

#Chart with Plotly
def make_charts(requested_workout_data,username):        
    figOutput_Distance = px.scatter(requested_workout_data, x = 'Total Output', y = 'Distance (mi)', color = 'Length (minutes)')
    figOutput_Distance.update_layout(autosize = True, width = 1200, height = 900, font_size = 22)
    figOutput_Distance.update_traces(marker=dict(size=12,line=dict(width=3, color='DarkSlateGrey')),
                  selector=dict(mode='markers'))
    figOutput_Distance.write_image(graph_path + username + '/' + username +  '_Output_to_Distance2D.jpg')           

```
Then, the data is prepared to be placed in the Google Sheets. Prior to being set_with_dataframe, the sheets themselves are opened. (User 1 shown as example)

```python
# Sort DFs in Descending Order (User Preference)
def descending(moaDF_by_month, current_year_df, current_year_requested,moaDF):

    moaDF_by_month.sort_values(by=['Month/Year'], inplace=True, ascending=False)
    current_year_requested.sort_values(by=['Workout Date'], inplace=True, ascending=False)
    current_year_df.sort_values(by=['Workout Date'], inplace=True, ascending=False)
    moaDF.sort_values(by=['Workout Date'], inplace=True, ascending=False)

# GSpread
# Name each sheet as a variable
# user_1
ws_user_11 = gc.open_by_url(google_sheets_link_user_1).get_worksheet(0)
ws_user_12 = gc.open_by_url(google_sheets_link_user_1).get_worksheet(1)
ws_user_13 = gc.open_by_url(google_sheets_link_user_1).get_worksheet(2)
ws_user_14 = gc.open_by_url(google_sheets_link_user_1).get_worksheet(3)
ws_user_15 = gc.open_by_url(google_sheets_link_user_1).get_worksheet(4)
ws_user_16 = gc.open_by_url(google_sheets_link_user_1).get_worksheet(5)

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

# Sort DFs in Descending Order (User Preference)
def descending(moaDF_by_month, current_year_df, current_year_requested,moaDF, moaDF_by_week):

    moaDF_by_month.sort_values(by=['Month/Year'], inplace=True, ascending=False)
    current_year_requested.sort_values(by=['Workout Date'], inplace=True, ascending=False)
    current_year_df.sort_values(by=['Workout Date'], inplace=True, ascending=False)
    moaDF.sort_values(by=['Workout Date'], inplace=True, ascending=False)
    moaDF_by_week.sort_values(by=['Workout Date'], inplace=True, ascending=False)

# DataFrame Formatting for setting to DF with GSpread
def format_for_gspread (df):
    df.index = pd.to_datetime(df.index)
    df.index = df.index.strftime('%Y-%m-%d')


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
```
Finally, the daily wrap text message is sent. Note the domains by carrier in the comments. Also, the email function is included in the code should that be preferred. Both rely on SMTP

```python
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
        msg['Subject'] = "Daily Wrap\n"
        # Make sure you also add new lines to your body
        body = '\Your workout tracker has been updated on your peloton output file via automatic scripting. So far this year, you have ridden ' + str(total_distance) + \
                ' miles. Your most recent ride was on ' + str(most_recent_workout) + '. You are currently on pace for ' + str(current_pace) + ' miles this year. You can access the file here: ' + str(sheets_link)
        # and then attach that body furthermore you can also send html content.
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
```
