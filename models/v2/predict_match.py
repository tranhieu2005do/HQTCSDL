
import logging
import pickle
import sys
from pathlib import Path
from typing import Dict, Optional, Tuple, Any, List
from datetime import datetime

import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer

from models.v2.data_loader import DataLoader
from models.v2.feature_engineering import FeatureEngineer
from models.v2.config import MODEL_FILES, PREDICTION_CONFIG

logger = logging.getLogger(__name__)


class PredictionEngine:
    
    def __init__(self, model_dir: Optional[Path] = None):
        self.model_dir = model_dir or MODEL_FILES["home_goals_model"].parent
        
        self.model_home = None
        self.model_away = None
        self.scaler = None
        self.imputer = None
        self.feature_columns = None
        
        self.data_loader = DataLoader()
        self.feature_engineer = FeatureEngineer(self.data_loader)
        
        self._load_models()
        logger.info("PredictionEngine initialized")
    
    def _load_models(self) -> None:
        logger.info("Loading models...")
        
        # Load models
        try:
            with open(MODEL_FILES["home_goals_model"], "rb") as f:
                self.model_home = pickle.load(f)
            logger.info("Loaded home goals model")
        except FileNotFoundError:
            raise FileNotFoundError(f"Home goals model not found at {MODEL_FILES['home_goals_model']}")
        
        try:
            with open(MODEL_FILES["away_goals_model"], "rb") as f:
                self.model_away = pickle.load(f)
            logger.info("Loaded away goals model")
        except FileNotFoundError:
            raise FileNotFoundError(f"Away goals model not found at {MODEL_FILES['away_goals_model']}")
        
        # Load preprocessing objects
        try:
            with open(MODEL_FILES["scaler"], "rb") as f:
                self.scaler = pickle.load(f)
            logger.info("Loaded scaler")
        except FileNotFoundError:
            logger.warning("Scaler not found, will use identity transform")
            self.scaler = StandardScaler()
        
        try:
            with open(MODEL_FILES["imputer"], "rb") as f:
                self.imputer = pickle.load(f)
            logger.info("Loaded imputer")
        except FileNotFoundError:
            logger.warning("Imputer not found, will use mean strategy")
            self.imputer = SimpleImputer(strategy="mean")
        
        # Load feature columns
        try:
            with open(MODEL_FILES["feature_columns"], "rb") as f:
                self.feature_columns = pickle.load(f)
            logger.info(f"Loaded {len(self.feature_columns)} feature columns")
        except FileNotFoundError:
            raise FileNotFoundError(f"Feature columns not found at {MODEL_FILES['feature_columns']}")
    
    def predict_match(
        self,
        home_team_name: str,
        away_team_name: str,
        match_date: str
    ) -> Dict[str, Any]:
        logger.info(f"Predicting {home_team_name} vs {away_team_name} on {match_date}")
        
        # Convert match date
        try:
            match_date_dt = pd.to_datetime(match_date)
        except Exception as e:
            raise ValueError(f"Invalid date format: {match_date}. Use YYYY-MM-DD. Error: {e}")
        
        # Get team IDs
        team_id_mapping = self.data_loader.get_team_id_mapping()
        
        home_id = team_id_mapping.get(home_team_name)
        away_id = team_id_mapping.get(away_team_name)
        
        if home_id is None:
            raise ValueError(f"Home team '{home_team_name}' not found. Available teams: {list(team_id_mapping.keys())[:5]}...")
        if away_id is None:
            raise ValueError(f"Away team '{away_team_name}' not found. Available teams: {list(team_id_mapping.keys())[:5]}...")
        
        # Build features
        logger.info("Building match features...")
        try:
            features = self.feature_engineer.build_features_for_match(
                home_id, away_id, match_date_dt, include_target=False
            )
        except Exception as e:
            logger.error(f"Error building features: {e}")
            raise
        
        # Ensure all required columns exist (in correct order)
        feature_df = pd.DataFrame([features])
        
        # Add missing columns with 0
        for col in self.feature_columns:
            if col not in feature_df.columns:
                feature_df[col] = 0
        
        # Select and reorder columns to match training
        X = feature_df[self.feature_columns].copy()
        
        # Preprocess features (using fitted scaler/imputer)
        X_imputed = pd.DataFrame(
            self.imputer.transform(X),
            columns=self.feature_columns
        )
        
        X_scaled = pd.DataFrame(
            self.scaler.transform(X_imputed),
            columns=self.feature_columns
        )
        
        # Get last 5 head-to-head stats
        h2h_summary, h2h_last5 = self._get_last5_h2h_stats(home_id, away_id, match_date_dt)

        # Get predictions
        pred_home_goals = self.model_home.predict(X_scaled)[0]
        pred_away_goals = self.model_away.predict(X_scaled)[0]
        
        # Post-process predictions
        if PREDICTION_CONFIG["round_predictions"]:
            pred_home_goals = max(0, round(pred_home_goals))
            pred_away_goals = max(0, round(pred_away_goals))
        else:
            pred_home_goals = max(0, pred_home_goals)
            pred_away_goals = max(0, pred_away_goals)
        
        # Cap at maximum
        pred_home_goals = min(pred_home_goals, PREDICTION_CONFIG["max_goals"])
        pred_away_goals = min(pred_away_goals, PREDICTION_CONFIG["max_goals"])
        
        # Determine winner
        if pred_home_goals > pred_away_goals:
            winner = "HOME_WIN"
        elif pred_away_goals > pred_home_goals:
            winner = "AWAY_WIN"
        else:
            winner = "DRAW"
        
        # Calculate confidence
        goal_diff = abs(pred_home_goals - pred_away_goals)
        confidence = min(0.95, 0.5 + goal_diff * 0.15)
        
        prediction_result = {
            "home_team": home_team_name,
            "away_team": away_team_name,
            "match_date": match_date,
            "predicted_home_goals": int(pred_home_goals),
            "predicted_away_goals": int(pred_away_goals),
            "winner_prediction": winner,
            "confidence": round(confidence, 3),
            "h2h_summary": h2h_summary,
            "h2h_last5_matches": h2h_last5,
            "status": "success"
        }
        
        logger.info(f"Prediction: {home_team_name} {int(pred_home_goals)}-{int(pred_away_goals)} {away_team_name}")
        
        return prediction_result

    def _get_last5_h2h_stats(
        self,
        home_id: int,
        away_id: int,
        match_date: pd.Timestamp
    ) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """Fetch last 5 head-to-head matches and summary stats."""
        h2h = self.feature_engineer.head_to_head
        team_name_mapping = self.data_loader.get_team_name_mapping()

        mask = (
            ((h2h["home_team_id"] == home_id) & (h2h["away_team_id"] == away_id)) |
            ((h2h["home_team_id"] == away_id) & (h2h["away_team_id"] == home_id))
        ) & (h2h["date"] < match_date)

        recent_h2h = h2h.loc[mask].sort_values("date", ascending=False).head(5)

        matches: List[Dict[str, Any]] = []
        summary = {
            "total_matches": int(len(recent_h2h)),
            "home_team_wins": 0,
            "away_team_wins": 0,
            "draws": 0,
            "home_team_avg_goals": 0.0,
            "away_team_avg_goals": 0.0,
            "btts_rate": 0.0,
            "over_2_5_rate": 0.0,
        }

        if len(recent_h2h) == 0:
            return summary, matches

        home_goals = []
        away_goals = []
        btts_count = 0
        over_2_5_count = 0

        for _, row in recent_h2h.iterrows():
            match_home_name = team_name_mapping.get(row["home_team_id"], str(row["home_team_id"]))
            match_away_name = team_name_mapping.get(row["away_team_id"], str(row["away_team_id"]))
            home_score = int(row.get("home_goals", 0))
            away_score = int(row.get("away_goals", 0))

            if row["home_team_id"] == home_id:
                if home_score > away_score:
                    summary["home_team_wins"] += 1
                elif home_score < away_score:
                    summary["away_team_wins"] += 1
                else:
                    summary["draws"] += 1
            else:
                if away_score > home_score:
                    summary["home_team_wins"] += 1
                elif away_score < home_score:
                    summary["away_team_wins"] += 1
                else:
                    summary["draws"] += 1

            home_goals.append(home_score)
            away_goals.append(away_score)
            btts_count += int(home_score > 0 and away_score > 0)
            over_2_5_count += int(home_score + away_score > 2.5)

            matches.append({
                "date": row["date"].strftime("%Y-%m-%d"),
                "home_team": match_home_name,
                "away_team": match_away_name,
                "home_goals": home_score,
                "away_goals": away_score,
                "result": (
                    "HOME_WIN" if home_score > away_score else
                    "AWAY_WIN" if away_score > home_score else
                    "DRAW"
                )
            })

        summary["home_team_avg_goals"] = round(float(np.mean(home_goals)), 2)
        summary["away_team_avg_goals"] = round(float(np.mean(away_goals)), 2)
        summary["btts_rate"] = round(btts_count / len(recent_h2h), 3)
        summary["over_2_5_rate"] = round(over_2_5_count / len(recent_h2h), 3)

        return summary, matches
    
    def predict_multiple(
        self,
        matches: list
    ) -> list:
        logger.info(f"Predicting {len(matches)} matches...")
        results = []
        
        for match in matches:
            try:
                result = self.predict_match(
                    match["home_team"],
                    match["away_team"],
                    match["match_date"]
                )
                results.append(result)
            except Exception as e:
                logger.error(f"Error predicting {match}: {e}")
                results.append({
                    "home_team": match["home_team"],
                    "away_team": match["away_team"],
                    "match_date": match["match_date"],
                    "status": "error",
                    "error": str(e)
                })
        
        logger.info(f"Predicted {len([r for r in results if r.get('status') == 'success'])}/{len(matches)} matches successfully")
        
        return results
    
    def get_confidence_interpretation(self, confidence: float) -> str:
        if confidence >= 0.8:
            return "HIGH"
        elif confidence >= 0.6:
            return "MEDIUM"
        else:
            return "LOW"


def setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(
                Path(__file__).parent / "logs" / "prediction.log",
                mode="a"
            )
        ]
    )


def main():
    setup_logging()
    logger.info("Starting predictions")
    
    try:
        # Initialize engine
        engine = PredictionEngine()
        
        # Example predictions
        test_matches = [
            {
                "home_team": "Liverpool",
                "away_team": "Everton",
                "match_date": "2022-12-15"
            },
            {
                "home_team": "Chelsea",
                "away_team": "Arsenal",
                "match_date": "2024-01-20"
            }
        ]
        
        # Make predictions
        results = engine.predict_multiple(test_matches)
        
        # Print results
        logger.info("\n" + "="*70)
        logger.info("PREDICTION RESULTS")
        logger.info("="*70)
        
        for result in results:
            if result.get("status") == "success":
                logger.info(f"\n{result['home_team']} vs {result['away_team']} ({result['match_date']})")
                logger.info(f"  Predicted Score: {result['predicted_home_goals']}-{result['predicted_away_goals']}")
                logger.info(f"  Winner: {result['winner_prediction']}")
                logger.info(f"  Confidence: {result['confidence']} ({engine.get_confidence_interpretation(result['confidence'])})")

                h2h_summary = result.get("h2h_summary", {})
                if h2h_summary and h2h_summary.get("total_matches", 0) > 0:
                    logger.info("  Last 5 head-to-head summary:")
                    logger.info(f"    Total matches: {h2h_summary['total_matches']}")
                    logger.info(f"    Home wins: {h2h_summary['home_team_wins']}")
                    logger.info(f"    Away wins: {h2h_summary['away_team_wins']}")
                    logger.info(f"    Draws: {h2h_summary['draws']}")
                    logger.info(f"    Avg home goals: {h2h_summary['home_team_avg_goals']}")
                    logger.info(f"    Avg away goals: {h2h_summary['away_team_avg_goals']}")
                    logger.info(f"    BTTS rate: {h2h_summary['btts_rate'] * 100:.1f}%")
                    logger.info(f"    Over 2.5 goals rate: {h2h_summary['over_2_5_rate'] * 100:.1f}%")
                    logger.info("  Last 5 head-to-head matches:")
                    for match in result.get("h2h_last5_matches", []):
                        logger.info(
                            f"    {match['date']}: {match['home_team']} {match['home_goals']}-{match['away_goals']} {match['away_team']} ({match['result']})"
                        )
                else:
                    logger.info("  No head-to-head history available before this match date.")
            else:
                logger.error(f"Error predicting {result.get('home_team')} vs {result.get('away_team')}: {result.get('error')}")
        
        logger.info("\nPrediction completed successfully!")
        
    except Exception as e:
        logger.error(f"Prediction failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
