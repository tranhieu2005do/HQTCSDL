
import logging
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
import json

import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


def setup_logging(log_name: str = "prediction_system") -> None:

    log_dir = Path(__file__).parent / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    
    log_file = log_dir / f"{log_name}.log"
    
    # Remove existing handlers
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
    
    # Create formatters and handlers
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    
    # File handler
    file_handler = logging.FileHandler(log_file, mode="a")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    
    # Root logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)


def validate_team_name(team_name: str, available_teams: Dict[str, int]) -> bool:
    """
    Validate if team name exists in available teams.
    
    Args:
        team_name: Team name to validate.
        available_teams: Dictionary of available teams.
        
    Returns:
        True if team exists, False otherwise.
    """
    return team_name in available_teams


def get_team_statistics(
    fixtures: pd.DataFrame,
    team_id: int,
    limit: Optional[int] = None
) -> Dict[str, Any]:
    """
    Get comprehensive statistics for a team.
    
    Args:
        fixtures: Fixtures dataframe.
        team_id: Team ID.
        limit: Limit number of recent matches.
        
    Returns:
        Dictionary with team statistics.
    """
    # Get all matches
    home_matches = fixtures[fixtures["home_id"] == team_id].copy()
    away_matches = fixtures[fixtures["away_id"] == team_id].copy()
    
    # Apply limit if specified
    if limit:
        home_matches = home_matches.tail(limit)
        away_matches = away_matches.tail(limit)
    
    total_matches = len(home_matches) + len(away_matches)
    
    if total_matches == 0:
        return {"error": f"No matches found for team {team_id}"}
    
    # Calculate statistics
    home_goals_for = home_matches["home_goals"].sum()
    home_goals_against = home_matches["away_goals"].sum()
    away_goals_for = away_matches["away_goals"].sum()
    away_goals_against = away_matches["home_goals"].sum()
    
    total_goals_for = home_goals_for + away_goals_for
    total_goals_against = home_goals_against + away_goals_against
    
    # Win/Draw/Loss
    home_wins = (home_matches["home_goals"] > home_matches["away_goals"]).sum()
    home_draws = (home_matches["home_goals"] == home_matches["away_goals"]).sum()
    home_losses = (home_matches["home_goals"] < home_matches["away_goals"]).sum()
    
    away_wins = (away_matches["away_goals"] > away_matches["home_goals"]).sum()
    away_draws = (away_matches["away_goals"] == away_matches["home_goals"]).sum()
    away_losses = (away_matches["away_goals"] < away_matches["home_goals"]).sum()
    
    total_wins = home_wins + away_wins
    total_draws = home_draws + away_draws
    total_losses = home_losses + away_losses
    
    stats = {
        "team_id": team_id,
        "total_matches": total_matches,
        "matches": {
            "home": len(home_matches),
            "away": len(away_matches),
        },
        "goals": {
            "for": total_goals_for,
            "against": total_goals_against,
            "difference": total_goals_for - total_goals_against,
            "average_per_match": total_goals_for / total_matches if total_matches > 0 else 0,
        },
        "record": {
            "wins": total_wins,
            "draws": total_draws,
            "losses": total_losses,
            "win_rate": total_wins / total_matches if total_matches > 0 else 0,
            "draw_rate": total_draws / total_matches if total_matches > 0 else 0,
            "loss_rate": total_losses / total_matches if total_matches > 0 else 0,
        },
        "home_record": {
            "wins": home_wins,
            "draws": home_draws,
            "losses": home_losses,
            "win_rate": home_wins / len(home_matches) if len(home_matches) > 0 else 0,
        },
        "away_record": {
            "wins": away_wins,
            "draws": away_draws,
            "losses": away_losses,
            "win_rate": away_wins / len(away_matches) if len(away_matches) > 0 else 0,
        },
        "points": total_wins * 3 + total_draws,
    }
    
    return stats


def format_prediction_output(prediction: Dict[str, Any]) -> str:
    """
    Format prediction output for display.
    
    Args:
        prediction: Prediction dictionary.
        
    Returns:
        Formatted string.
    """
    if prediction.get("status") != "success":
        return f"Error: {prediction.get('error', 'Unknown error')}"
    
    home = prediction["home_team"]
    away = prediction["away_team"]
    home_goals = prediction["predicted_home_goals"]
    away_goals = prediction["predicted_away_goals"]
    winner = prediction["winner_prediction"]
    confidence = prediction["confidence"]
    
    output = f"""
╔══════════════════════════════════════════════════════════════╗
║                    MATCH PREDICTION                          ║
╠══════════════════════════════════════════════════════════════╣
║ {home:30} vs {away:30} ║
║                                                              ║
║ Predicted Score: {home_goals} - {away_goals:<46} ║
║ Winner Prediction: {winner:<48} ║
║ Confidence: {confidence} ({_confidence_level(confidence):<43} ║
║ Match Date: {prediction['match_date']:<51} ║
╚══════════════════════════════════════════════════════════════╝
"""
    
    return output


def _confidence_level(confidence: float) -> str:
    """Get confidence level string."""
    if confidence >= 0.8:
        return "HIGH"
    elif confidence >= 0.6:
        return "MEDIUM"
    else:
        return "LOW"


def export_predictions_to_csv(
    predictions: List[Dict[str, Any]],
    output_file: Path
) -> None:
    """
    Export predictions to CSV file.
    
    Args:
        predictions: List of prediction dictionaries.
        output_file: Output file path.
    """
    df = pd.DataFrame(predictions)
    df.to_csv(output_file, index=False)
    logger.info(f"Predictions exported to {output_file}")


def export_predictions_to_json(
    predictions: List[Dict[str, Any]],
    output_file: Path
) -> None:
    """
    Export predictions to JSON file.
    
    Args:
        predictions: List of prediction dictionaries.
        output_file: Output file path.
    """
    with open(output_file, "w") as f:
        json.dump(predictions, f, indent=2)
    logger.info(f"Predictions exported to {output_file}")


class PredictionMetrics:
    """Calculate evaluation metrics for predictions."""
    
    @staticmethod
    def winner_accuracy(y_true: List[str], y_pred: List[str]) -> float:
        """
        Calculate winner prediction accuracy.
        
        Args:
            y_true: True results (HOME_WIN, DRAW, AWAY_WIN).
            y_pred: Predicted results.
            
        Returns:
            Accuracy as float between 0 and 1.
        """
        correct = sum(1 for t, p in zip(y_true, y_pred) if t == p)
        return correct / len(y_true) if len(y_true) > 0 else 0
    
    @staticmethod
    def goals_mae(y_true: np.ndarray, y_pred: np.ndarray) -> float:
        """
        Calculate Mean Absolute Error for goals.
        
        Args:
            y_true: True goals.
            y_pred: Predicted goals.
            
        Returns:
            MAE value.
        """
        return np.mean(np.abs(y_true - y_pred))
    
    @staticmethod
    def score_prediction_accuracy(
        y_true_home: np.ndarray,
        y_true_away: np.ndarray,
        y_pred_home: np.ndarray,
        y_pred_away: np.ndarray
    ) -> float:
        """
        Calculate exact score prediction accuracy.
        
        Args:
            y_true_home: True home goals.
            y_true_away: True away goals.
            y_pred_home: Predicted home goals.
            y_pred_away: Predicted away goals.
            
        Returns:
            Accuracy as float between 0 and 1.
        """
        correct = sum(
            1 for th, ta, ph, pa in zip(y_true_home, y_true_away, y_pred_home, y_pred_away)
            if th == ph and ta == pa
        )
        return correct / len(y_true_home) if len(y_true_home) > 0 else 0


def create_match_batch_from_csv(csv_file: Path) -> List[Dict[str, str]]:
    """
    Create batch of matches from CSV file.
    
    Expected CSV columns: home_team, away_team, match_date
    
    Args:
        csv_file: Path to CSV file.
        
    Returns:
        List of match dictionaries.
    """
    df = pd.read_csv(csv_file)
    
    required_columns = ["home_team", "away_team", "match_date"]
    missing = [col for col in required_columns if col not in df.columns]
    
    if missing:
        raise ValueError(f"CSV missing required columns: {missing}")
    
    matches = df[required_columns].to_dict("records")
    logger.info(f"Loaded {len(matches)} matches from {csv_file}")
    
    return matches


def print_system_info() -> None:
    """Print system information."""
    from models.v2.config import get_config
    
    config = get_config()
    
    print("\n" + "="*70)
    print("FOOTBALL PREDICTION SYSTEM - INFORMATION")
    print("="*70)
    print(f"\nProject Root: {config['project_root']}")
    print(f"Database Dir: {config['database_dir']}")
    print(f"Models Dir: {config['models_dir']}")
    print(f"\nAvailable Models:")
    print(f"  Home Goals: {config['model_files']['home_goals_model']}")
    print(f"  Away Goals: {config['model_files']['away_goals_model']}")
    print(f"\nConfiguration:")
    print(f"  Max Goals Cap: {config['prediction']['max_goals']}")
    print(f"  Round Predictions: {config['prediction']['round_predictions']}")
    print(f"  Feature Groups Enabled: {sum(1 for v in config['features'].values() if v is True)}/{len([v for v in config['features'].values() if isinstance(v, bool)])}")
    print("="*70 + "\n")
