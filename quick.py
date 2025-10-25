from google_auth_oauthlib.flow import InstalledAppFlow
import json

SCOPES = ["https://www.googleapis.com/auth/gmail.send"]

flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
creds = flow.run_local_server(port=0)

# Save token.json for later use by your backend
with open("token.json", "w") as token:
    token.write(creds.to_json())

print("Token saved successfully!")
