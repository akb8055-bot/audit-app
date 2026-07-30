# Conrad Abu Dhabi EHS Inspection Report

A premium inspection reporting and analytics app built with Streamlit.

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deploy to Streamlit Community Cloud

1. Push this repository to GitHub.
2. Open https://share.streamlit.io/.
3. Connect the repository and select app.py as the entry file.
4. Set the Python version to 3.11 or 3.10.
5. Deploy.

## Share inspection records across devices

The app already supports a remote JSON storage endpoint. The easiest free option is Firebase Realtime Database.

1. Create a Firebase project at https://console.firebase.google.com/.
2. Create a Realtime Database.
3. Set the database rules to allow read/write for now:

```json
{
  "rules": {
    ".read": true,
    ".write": true
  }
}
```

4. Copy the database URL, for example:

```text
https://your-project-id.firebaseio.com/history.json
```

5. In Streamlit Community Cloud, open your app settings and add these environment variables:

```text
REPORT_STORAGE_BACKEND=remote
REPORT_STORAGE_URL=https://your-project-id.firebaseio.com/history.json
```

6. Redeploy the app.

After the redeploy, inspection records will be stored in the shared Firebase endpoint instead of only on your laptop.
