import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from oauth2client.service_account import ServiceAccountCredentials

credential_file = "peloton_creds.json"


def get_credentials(SERVICE_ACCOUNT_KEY_FILE,SCOPES):
  """Creates a Credential object with the correct OAuth2 authorization.

  Uses the service account key stored in SERVICE_ACCOUNT_KEY_FILE.

  Returns:
    Credentials, the user's credential.
  """
  credential = ServiceAccountCredentials.from_json_keyfile_name(
    SERVICE_ACCOUNT_KEY_FILE, SCOPES)

  if not credential or credential.invalid:
    print('Unable to authenticate using service account key.')
  return credential
# def get_credentials(scopes,credential_file):
#     creds = None
#     if os.path.exists(credential_file):
#         creds = Credentials.from_service_account_file(credential_file,scopes)
#     if not creds or not creds.valid:
#         if creds and creds.expired and creds.refresh_token:
#             creds.refresh(Request())
#         else:
#             flow = InstalledAppFlow.from_service_account_file(credential_file, scopes)
#             creds = flow.run_local_server(port=0)
#         with open("token.json", "w") as token:
#             token.write(creds.to_json())
#     return creds


