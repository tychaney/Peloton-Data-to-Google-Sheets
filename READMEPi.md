# Below are package installations necessary on a Raspberry Pi 4
## Raspbian comes with Python3 pre-installed, so no need to install it manually

```bash
sudo apt-get update
sudo apt-get install python3-pip
sudo apt-get install libatlas-base-dev
sudo apt-get install libopenjp2-7
sudo apt-get install libnss3
pip3 install pandas
pip3 install seaborn
pip3 install matplotlib
pip3 install gspread
pip3 install plotly
pip3 install plotly.express
pip3 install oauth2client
pip3 install gspread_dataframe
ip install gspread_formatting
pip3 install numpy
pip3 install kaleido
```
# To Schedule on the Pi using crontab -e

Enter the following command: 

```bash
crontab -e
```
## Example of a schedule that operates from 3 AM (0300) to 3 PM (1500) with a final run at 4 PM (1600)

The spacing is important, for best results, copy and paste this schedule, and adjust to your specific needs.

```bash

# m h  dom mon dow   command
0 3-15 * * * python3  /home/pi/PelotonToSheets.py

10 3-15 * * * python3  /home/pi/PelotonToSheets.py

20 3-15 * * * python3  /home/pi/PelotonToSheets.py

30 3-15 * * * python3  /home/pi/PelotonToSheets.py

40 3-15 * * * python3  /home/pi/PelotonToSheets.py

50 3-15 * * * python3  /home/pi/PelotonToSheets.py

0 16 * * * python3  /home/pi/PelotonToSheets.py

```
