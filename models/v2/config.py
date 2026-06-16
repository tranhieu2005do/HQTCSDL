from pathlib import Path
from typing import Dict, Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATABASE_DIR = PROJECT_ROOT / "database"
MODELS_DIR = PROJECT_ROOT / "models"
SAVE_MODEL_DIR = PROJECT_ROOT / "models" / "v2" / "saved_model"
ETL_DIR = PROJECT_ROOT / "etl"

# Ensure save model directory exists
SAVE_MODEL_DIR.mkdir(parents=True, exist_ok=True)

DATA_FILES = {
    "fixtures": DATABASE_DIR / "fixtures.json",
    "head_to_head": DATABASE_DIR / "head_to_head.json",
    "teams": DATABASE_DIR / "teams.json",
    "fixture_statistics": DATABASE_DIR / "fixture_statistics.json",
    "fixture_player_statistics": DATABASE_DIR / "fixture_player_statistics.json",
    "players_statistic_season": DATABASE_DIR / "players_statistic_season.json",
    "goal_events": DATABASE_DIR / "goal_events.json",
    "card_events": DATABASE_DIR / "card_events.json",
    "subst_events": DATABASE_DIR / "subst_events.json",
    "lineups": DATABASE_DIR / "lineups.json",
    "venues": DATABASE_DIR / "venues.json",
}

MODEL_FILES = {
    "home_goals_model": SAVE_MODEL_DIR / "model_home_goals.pkl",
    "away_goals_model": SAVE_MODEL_DIR / "model_away_goals.pkl",
    "feature_columns": SAVE_MODEL_DIR / "feature_columns.pkl",
    "imputer": SAVE_MODEL_DIR / "imputer.pkl",
    "scaler": SAVE_MODEL_DIR / "scaler.pkl",
    "label_encoders": SAVE_MODEL_DIR / "label_encoders.pkl",
    "feature_importance": SAVE_MODEL_DIR / "feature_importance.csv",
}

TRAINING_CONFIG = {
    # XGBoost parameters
    "xgboost_base_params": {
        "objective": "reg:squarederror",
        "booster": "gbtree",
        "random_state": 42,
        "n_jobs": -1,
        "verbosity": 0,
    },
    
    # Hyperparameter tuning ranges
    "hyperparameter_ranges": {
        "n_estimators": [50, 100, 200, 300],
        "max_depth": [3, 5, 7, 10],
        "learning_rate": [0.01, 0.05, 0.1, 0.2],
        "subsample": [0.6, 0.8, 1.0],
        "colsample_bytree": [0.6, 0.8, 1.0],
        "min_child_weight": [1, 3, 5],
    },
    
    # CV settings
    "cv_folds": 5,
    "test_size": 0.2,
    
    # Data preprocessing
    "handle_missing": True,
    "missing_threshold": 0.5,  # Drop features with >50% missing
}

FEATURE_CONFIG = {
    # Lookback windows for recent form
    "lookback_windows": [3, 5, 10],
    
    # Feature groups
    "use_team_id": True,
    "use_recent_form": True,
    "use_home_away_specialization": True,
    "use_head_to_head": True,
    "use_attack_defense_strength": True,
    "use_momentum": True,
    "use_rest_days": True,
    "use_venue": True,
    "use_event_features": True,
    
    # Advanced settings
    "min_matches_for_stats": 1,  # Minimum matches to calculate stats
    "cache_features": True,  # Cache computed features
}

EVALUATION_METRICS = [
    "mae",
    "rmse", 
    "r2",
    "winner_accuracy",
]

LOGGING_CONFIG = {
    "level": "INFO",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "log_file": MODELS_DIR / "logs" / "prediction_system.log",
}

# Ensure log directory exists
LOGGING_CONFIG["log_file"].parent.mkdir(parents=True, exist_ok=True)

PREDICTION_CONFIG = {
    "round_predictions": True,
    "max_goals": 10,  # Cap maximum predicted goals
    "min_confidence": 0.3,  # Minimum confidence threshold
}

def get_config() -> Dict[str, Any]:

    return {
        "project_root": str(PROJECT_ROOT),
        "database_dir": str(DATABASE_DIR),
        "models_dir": str(MODELS_DIR),
        "save_model_dir": str(SAVE_MODEL_DIR),
        "data_files": {k: str(v) for k, v in DATA_FILES.items()},
        "model_files": {k: str(v) for k, v in MODEL_FILES.items()},
        "training": TRAINING_CONFIG,
        "features": FEATURE_CONFIG,
        "evaluation": EVALUATION_METRICS,
        "prediction": PREDICTION_CONFIG,
    }


def validate_paths() -> bool:
    """
    Validate that all required data files exist.
    
    Returns:
        True if all files exist, False otherwise.
    """
    missing_files = []
    for name, path in DATA_FILES.items():
        if not path.exists():
            missing_files.append(f"{name}: {path}")
    
    if missing_files:
        print(f"Warning: Missing files:\n" + "\n".join(missing_files))
        return False
    return True
