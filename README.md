# Project Agentic Teacher
## Structure

```
├─ app/
│  ├─ __init__.py
│  ├─ main.py                   # FastAPI app (simple health check for now)
│  ├─ config.py                 # env/config loading
│  ├─ logging.py                # logger setup
│  ├─ models/                   # pydantic models for rubric, feedback, submissions
│  │  ├─ __init__.py
│  │  ├─ rubric.py
│  │  ├─ submission.py
│  │  └─ feedback.py
│  ├─ clients/                  # thin wrappers around Google APIs
│  │  ├─ __init__.py
│  │  ├─ google_auth.py
│  │  ├─ classroom.py
│  │  ├─ drive.py
│  │  ├─ docs.py
│  │  └─ sheets.py
│  ├─ services/                 # app logic (rubric loader, evaluator, feedback writer)
│  │  ├─ __init__.py
│  │  ├─ rubric_loader.py
│  │  ├─ extraction.py
│  │  ├─ evaluation.py
│  │  ├─ feedback_writer.py
│  │  └─ pipeline.py
│  ├─ repositories/             # persistence (swap memory → Postgres later)
│  │  ├─ __init__.py
│  │  ├─ results_repo.py        # interface
│  │  ├─ memory_repo.py
│  │  └─ postgres_repo.py       # (later)
│  ├─ llm/                      # pluggable LLM provider(s)
│  │  ├─ __init__.py
│  │  ├─ provider.py
│  │  └─ openai_provider.py     # or vertex_provider.py later
│  └─ scripts/                  # small CLIs for development
│     ├─ __init__.py
│     ├─ auth_smoke.py
│     └─ list_assignments.py
├─ tests/
│  └─ test_rubric_parser.py     # first unit test target
├─ .env.example
├─ .gitignore
├─ requirements.txt
└─ README.md
```

## Starting setup
First of all you need to check `requirements.txt` file and check the last version of the libraries.
Then you can go to your console and
`pip install -r requirements.txt`

## Google Classroom API
This is a fundamental step to download `credentials.json` that is the file that consent to connect to your Google Classroom Account.

### Enable the Google Classroom API
Before you can create credentials, you must enable the specific API you want to use.

1. Navigate to the [Google Cloud Console](https://console.cloud.google.com/).
2. From the navigation menu (the three horizontal lines in the top-left corner), select **APIs and Services -> Library**.
3. In the search bar, type "Google Classroom API" and press Enter.
4. Click on the Google Classroom API result.
5. On the API page, click the ENABLE button. This may take a few moments.

You can do the same thing for "Google Drive", "Google Doc" and "Google sheet" as well

### Create the OAuth Consent Screen
The *OAuth consent screen* is what users will see when they are asked to grant your application permission to access their data. \
From the navigation menu, go to **APIs and Services -> OAuth consent screen**. \
Fill in the required information on the OAuth consent screen page:
1. App name: Enter a name for your application (e.g., "My Classroom App").
2. User type: External
3. User support email: Select your email address from the dropdown.
4. Developer contact information: Enter your email address again.
5. Click SAVE AND CONTINUE.

### Create the Credentials (OAuth Client ID)
Now you'll create the actual client ID and secret. \
From the navigation menu, go to **APIs and Services -> Credentials**.
1. Click the + CREATE CREDENTIALS button at the top and select OAuth client ID.
2. For the Application type, choose **Desktop app**.
3. Give it a descriptive name (e.g., "Classroom Desktop Client").
4. Click CREATE.

A pop-up will appear with your Client ID and Client Secret. These are the credentials for your desktop application. \
**It's better that you download the json file right now**, rename it into `credentials.json` and upload it into the root folder of your app.



