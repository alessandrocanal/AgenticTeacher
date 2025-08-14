# Project Agentic Teacher
## Structure

```
├─ app/ \
│  ├─ __init__.py \
│  ├─ main.py                   # FastAPI app (simple health check for now) \
│  ├─ config.py                 # env/config loading \
│  ├─ logging.py                # logger setup \
│  ├─ models/                   # pydantic models for rubric, feedback, submissions \
│  │  ├─ __init__.py \
│  │  ├─ rubric.py \
│  │  ├─ submission.py \
│  │  └─ feedback.py \
│  ├─ clients/                  # thin wrappers around Google APIs \
│  │  ├─ __init__.py \
│  │  ├─ google_auth.py \
│  │  ├─ classroom.py \
│  │  ├─ drive.py \
│  │  ├─ docs.py \
│  │  └─ sheets.py \
│  ├─ services/                 # app logic (rubric loader, evaluator, feedback writer) \
│  │  ├─ __init__.py \
│  │  ├─ rubric_loader.py \
│  │  ├─ evaluation.py \
│  │  ├─ feedback_writer.py \
│  │  └─ pipeline.py \
│  ├─ repositories/             # persistence (swap memory → Postgres later) \
│  │  ├─ __init__.py \
│  │  ├─ results_repo.py        # interface \
│  │  ├─ memory_repo.py \
│  │  └─ postgres_repo.py       # (later) \
│  ├─ llm/                      # pluggable LLM provider(s) \
│  │  ├─ __init__.py \
│  │  ├─ provider.py \
│  │  └─ openai_provider.py     # or vertex_provider.py later \
│  └─ scripts/                  # small CLIs for development \
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

## Setup
First of all you need to check `requirements.txt` file and check the last version of the libraries.
Then you can go to your console and
`pip install -r requirements.txt`


