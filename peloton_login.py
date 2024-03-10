import requests

def get_peloton_data(email_user, password_user, username_user, peloton_csv_link):
    s = requests.Session()
    payload = {"username_or_email": email_user, "password": password_user}
    s.post("https://api.onepeloton.com/auth/login", json=payload)
    download_data = s.get(peloton_csv_link, allow_redirects=True)
    csv_file = str(username_user) + ".csv"
    with open(csv_file, "wb") as f:
        f.write(download_data.content)