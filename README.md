# Football Data Warehouse with ETL Pipeline

A data engineering project that collects football data from API-Football, transforms raw API responses into structured analytical datasets, and loads them into ClickHouse for querying, analytics, and machine learning.

---

# Project Objectives

This project aims to:

- Collect football data from API-Football
- Build an ETL pipeline
- Store analytical data in ClickHouse
- Support:

  - Team analysis
  - Player analysis
  - Match analysis
  - Head-to-head analysis
  - Feature engineering for prediction models

---

# Tech Stack

- Python 3.10+
- :contentReference[oaicite:0]{index=0}
- Jupyter Notebook
- REST API
- JSON

---

# ETL Pipeline

```text
API-Football
    │
    ▼
extract/
    │
    ▼
output/              (raw API response)
    │
    ▼
transform/
    │
    ▼
database/            (cleaned data)
    │
    ▼
load/
    │
    ▼
ClickHouse
```

---

# Project Structure

```text
HQTCSDL/
│
├── extract/                 # Extract data from API-Football
│   ├── api_client.py
│   ├── config.py
│   ├── utils.py
│   ├── extract_events.py
│   ├── extract_fixture_headtohead.py
│   ├── extract_fixture_players.py
│   ├── extract_fixture_statistics.py
│   ├── extract_fixtures.py
│   ├── extract_lineup.py
│   ├── extract_players.py
│   └── extract_teams.py
│
├── output/                  # Raw API responses
│   ├── events.json
│   ├── fixture_headtohead.json
│   ├── fixture_players.json
│   ├── fixture_statistics.json
│   ├── fixtures.json
│   ├── lineups.json
│   ├── players.json
│   └── teams.json
│
├── transform/               # Data transformation notebooks
│   ├── transform_event_data.ipynb
│   ├── transform_fixture_data.ipynb
│   ├── transform_fixture_player.ipynb
│   ├── transform_fixture_statistics.ipynb
│   ├── transform_headtohead.ipynb
│   ├── transform_lineup_data.ipynb
│   ├── transform_player_data.ipynb
│   ├── transform_team_data.ipynb
│   └── etl_script.ipynb
│
├── database/                # Cleaned datasets
│   ├── teams.json
│   ├── players.json
│   ├── venues.json
│   ├── coaches.json
│   ├── fixtures.json
│   ├── lineups.json
│   ├── fixture_statistics.json
│   ├── fixture_player_statistics.json
│   ├── players_statistic_season.json
│   ├── goal_events.json
│   ├── card_events.json
│   ├── subst_events.json
│   ├── var_events.json
│   ├── head_to_head.json
│   └── INIT_DATABASE_CLICKHOUSE.txt
│
├── load/                    # Load cleaned data into ClickHouse
│   ├── clickhouse_client.py
│   ├── clickhouse_connect_config.py
│   ├── load_team_data.py
│   ├── load_player_data.py
│   ├── load_venue_data.py
│   ├── load_coach_data.py
│   ├── load_fixture_data.py
│   ├── load_lineup_data.py
│   ├── load_fixture_statistic_data.py
│   ├── load_fixture_player_statistic_data.py
│   ├── load_player_statistic_season.py
│   ├── load_goal_event_data.py
│   ├── load_card_event_data.py
│   ├── load_subst_event_data.py
│   ├── load_var_event_data.py
│   └── load_head_to_head_data.py
│
└── README.md
```

---

# ETL Stages

# 1. Extract

Collect raw data from API-Football.

Example:

```bash
python extract/extract_teams.py
```

Output:

```text
output/teams.json
```

---

# 2. Transform

Clean and normalize raw data.

Transformation tasks:

- Flatten nested JSON
- Remove duplicated fields
- Handle null values
- Convert data types
- Normalize schema

Example:

```bash
transform/transform_team_data.ipynb
```

Output:

```text
database/teams.json
```

---

# 3. Load

Insert cleaned data into ClickHouse.

Example:

```bash
python load/load_team_data.py
```

---

# Available Datasets

## Dimension Data

- teams
- players
- coaches
- venues

## Match Data

- fixtures
- lineups
- fixture_statistics
- fixture_player_statistics

## Event Data

- goal_events
- card_events
- subst_events
- var_events

## Historical Data

- head_to_head

## Season Statistics

- players_statistic_season

---

# Database

Database engine:

:contentReference[oaicite:1]{index=1}

Initialization script:

```text
database/INIT_DATABASE_CLICKHOUSE.txt
```

---

# How To Run

## Step 1: Extract

```bash
python extract/extract_teams.py
python extract/extract_players.py
python extract/extract_fixtures.py
```

## Step 2: Transform

Run notebooks in:

```text
transform/
```

## Step 3: Load

```bash
python load/load_team_data.py
python load/load_player_data.py
python load/load_fixture_data.py
```

---

# Future Improvements

- Airflow orchestration
- Incremental ETL
- Data quality validation
- Feature store
- ML prediction pipeline
- Dashboard with BI tools

---

# Author

Do Tran Hieu

Backend Developer | Data Engineering | Machine Learning
