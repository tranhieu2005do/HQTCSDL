"""
Feature engineering module for football score prediction.

Handles creation of all features for training and prediction,
with strong emphasis on avoiding data leakage.
"""

import logging
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime, timedelta
import pickle
from pathlib import Path

import pandas as pd
import numpy as np
from tqdm import tqdm

from models.v2.data_loader import DataLoader
from models.v2.config import FEATURE_CONFIG, MODEL_FILES

logger = logging.getLogger(__name__)


class FeatureEngineer:
    
    def __init__(self, data_loader: DataLoader):
        self.loader = data_loader
        self.fixtures = data_loader.load_fixtures()
        self.head_to_head = data_loader.load_head_to_head()
        self.feature_cache: Dict[str, Any] = {}
        logger.info("FeatureEngineer initialized")
    
    def build_features_for_match(
        self,
        home_team_id: int,
        away_team_id: int,
        match_date: datetime,
        include_target: bool = False
    ) -> pd.Series:
       
        if not isinstance(match_date, (datetime, pd.Timestamp)):
            match_date = pd.to_datetime(match_date)
        
        features = {
            "match_date": match_date,
            "home_team_id": home_team_id,
            "away_team_id": away_team_id,
        }
        
        # Filter fixtures strictly before match_date (NO data leakage)
        history = self.fixtures[self.fixtures["date"] < match_date].copy()
        
        if len(history) == 0:
            logger.warning(f"No history before {match_date}")
            return pd.Series(self._get_default_features())
        
        # Get matches for each team
        home_matches = self._get_team_matches(
            home_team_id, history, as_home=True
        )
        away_matches = self._get_team_matches(
            away_team_id, history, as_home=False
        )
        
        # Recent form features
        if FEATURE_CONFIG["use_recent_form"]:
            features.update(
                self._build_recent_form_features(home_matches, "home")
            )
            features.update(
                self._build_recent_form_features(away_matches, "away")
            )
        
        # Home/Away specialization
        if FEATURE_CONFIG["use_home_away_specialization"]:
            features.update(
                self._build_specialization_features(
                    home_team_id, away_team_id, history
                )
            )
        
        # Head-to-head features
        if FEATURE_CONFIG["use_head_to_head"]:
            features.update(
                self._build_h2h_features(
                    home_team_id, away_team_id, match_date
                )
            )
        
        # Attack/Defense strength
        if FEATURE_CONFIG["use_attack_defense_strength"]:
            features.update(
                self._build_strength_features(
                    home_team_id, away_team_id, history
                )
            )
        
        # Momentum features
        if FEATURE_CONFIG["use_momentum"]:
            features.update(
                self._build_momentum_features(home_matches, away_matches)
            )
        
        # Rest features
        if FEATURE_CONFIG["use_rest_days"]:
            features.update(
                self._build_rest_features(
                    home_team_id, away_team_id, match_date, history
                )
            )
        
        # Venue features (if available)
        if FEATURE_CONFIG["use_venue"] and "venue_id" in self.fixtures.columns:
            venue_id = self.fixtures[
                (self.fixtures["home_id"] == home_team_id) |
                (self.fixtures["away_id"] == home_team_id)
            ]["venue_id"].mode()
            if len(venue_id) > 0:
                features["venue_id"] = venue_id.iloc[0]
        
        # Event features (if statistics available)
        if FEATURE_CONFIG["use_event_features"]:
            features.update(
                self._build_event_features(
                    home_team_id, away_team_id, history
                )
            )
        
        # Convert to Series
        feature_series = pd.Series(features)
        
        # Add target if requested (for training only)
        if include_target:
            # Find the actual match if it exists in history
            match = self.fixtures[
                (self.fixtures["home_id"] == home_team_id) &
                (self.fixtures["away_id"] == away_team_id) &
                (self.fixtures["date"] == match_date)
            ]
            if len(match) > 0:
                feature_series["home_goals"] = match.iloc[0]["home_goals"]
                feature_series["away_goals"] = match.iloc[0]["away_goals"]
        
        return feature_series
    
    def build_training_data(self) -> Tuple[pd.DataFrame, pd.DataFrame]:
      
        logger.info("Building training data...")
        
        features_list = []
        targets_list = []
        
        for idx, row in tqdm(self.fixtures.iterrows(), total=len(self.fixtures)):
            match_date = row["date"]
            home_id = row["home_id"]
            away_id = row["away_id"]
            
            try:
                # Build features WITHOUT target first
                features = self.build_features_for_match(
                    home_id, away_id, match_date, include_target=False
                )
                
                # Add target separately to ensure no leakage
                features["home_goals"] = row["home_goals"]
                features["away_goals"] = row["away_goals"]
                
                features_list.append(features)
                
            except Exception as e:
                logger.warning(f"Error processing match {idx}: {e}")
                continue
        
        if not features_list:
            raise ValueError("No valid training data generated")
        
        df = pd.DataFrame(features_list)
        
        # Separate features and targets
        target_cols = ["home_goals", "away_goals"]
        feature_cols = [col for col in df.columns if col not in target_cols]
        
        X = df[feature_cols]
        y = df[target_cols]
        
        logger.info(f"Built training data: {len(X)} samples, {len(X.columns)} features")
        
        return X, y
    
    def _get_team_matches(
        self,
        team_id: int,
        history: pd.DataFrame,
        as_home: bool = True
    ) -> pd.DataFrame:
        if as_home:
            return history[history["home_id"] == team_id].copy()
        else:
            return history[history["away_id"] == team_id].copy()
    
    def _build_recent_form_features(
        self,
        team_matches: pd.DataFrame,
        prefix: str
    ) -> Dict[str, float]:

        features = {}
        
        for window in FEATURE_CONFIG["lookback_windows"]:
            recent = team_matches.tail(window)
            
            if len(recent) == 0:
                # Default values if no data
                features[f"{prefix}_last{window}_matches_played"] = 0
                features[f"{prefix}_last{window}_avg_goals_scored"] = 0
                features[f"{prefix}_last{window}_avg_goals_conceded"] = 0
                features[f"{prefix}_last{window}_win_rate"] = 0
                features[f"{prefix}_last{window}_draw_rate"] = 0
                features[f"{prefix}_last{window}_loss_rate"] = 0
                features[f"{prefix}_last{window}_clean_sheet_rate"] = 0
                features[f"{prefix}_last{window}_failed_to_score_rate"] = 0
                features[f"{prefix}_last{window}_total_points"] = 0
                features[f"{prefix}_last{window}_goal_difference"] = 0
                continue
            
            # Determine if team is home or away
            if prefix == "home":
                goals_for = recent["home_goals"].values
                goals_against = recent["away_goals"].values
            else:
                goals_for = recent["away_goals"].values
                goals_against = recent["home_goals"].values
            
            # Calculate stats
            matches_played = len(recent)
            avg_scored = goals_for.mean()
            avg_conceded = goals_against.mean()
            
            # Win/Draw/Loss rates
            wins = (goals_for > goals_against).sum()
            draws = (goals_for == goals_against).sum()
            losses = (goals_for < goals_against).sum()
            
            win_rate = wins / matches_played if matches_played > 0 else 0
            draw_rate = draws / matches_played if matches_played > 0 else 0
            loss_rate = losses / matches_played if matches_played > 0 else 0
            
            # Points (3 for win, 1 for draw)
            total_points = wins * 3 + draws
            
            # Clean sheets (goals_against == 0)
            clean_sheets = (goals_against == 0).sum()
            clean_sheet_rate = clean_sheets / matches_played if matches_played > 0 else 0
            
            # Failed to score (goals_for == 0)
            failed_to_score = (goals_for == 0).sum()
            failed_to_score_rate = failed_to_score / matches_played if matches_played > 0 else 0
            
            # Goal difference
            goal_diff = (goals_for - goals_against).sum()
            
            # Store features
            features[f"{prefix}_last{window}_matches_played"] = matches_played
            features[f"{prefix}_last{window}_avg_goals_scored"] = avg_scored
            features[f"{prefix}_last{window}_avg_goals_conceded"] = avg_conceded
            features[f"{prefix}_last{window}_win_rate"] = win_rate
            features[f"{prefix}_last{window}_draw_rate"] = draw_rate
            features[f"{prefix}_last{window}_loss_rate"] = loss_rate
            features[f"{prefix}_last{window}_clean_sheet_rate"] = clean_sheet_rate
            features[f"{prefix}_last{window}_failed_to_score_rate"] = failed_to_score_rate
            features[f"{prefix}_last{window}_total_points"] = total_points
            features[f"{prefix}_last{window}_goal_difference"] = goal_diff
        
        return features
    
    def _build_specialization_features(
        self,
        home_id: int,
        away_id: int,
        history: pd.DataFrame
    ) -> Dict[str, float]:

        features = {}
        
        # Home team's home performance
        home_team_home = history[history["home_id"] == home_id]
        if len(home_team_home) >= FEATURE_CONFIG["min_matches_for_stats"]:
            recent_home = home_team_home.tail(5)
            features["home_last5_home_avg_goals"] = recent_home["home_goals"].mean()
            features["home_last5_home_conceded"] = recent_home["away_goals"].mean()
            home_wins = (recent_home["home_goals"] > recent_home["away_goals"]).sum()
            features["home_last5_home_win_rate"] = home_wins / len(recent_home)
        else:
            features["home_last5_home_avg_goals"] = 0
            features["home_last5_home_conceded"] = 0
            features["home_last5_home_win_rate"] = 0
        
        # Away team's away performance
        away_team_away = history[history["away_id"] == away_id]
        if len(away_team_away) >= FEATURE_CONFIG["min_matches_for_stats"]:
            recent_away = away_team_away.tail(5)
            features["away_last5_away_avg_goals"] = recent_away["away_goals"].mean()
            features["away_last5_away_conceded"] = recent_away["home_goals"].mean()
            away_wins = (recent_away["away_goals"] > recent_away["home_goals"]).sum()
            features["away_last5_away_win_rate"] = away_wins / len(recent_away)
        else:
            features["away_last5_away_avg_goals"] = 0
            features["away_last5_away_conceded"] = 0
            features["away_last5_away_win_rate"] = 0
        
        return features
    
    def _build_h2h_features(
        self,
        home_id: int,
        away_id: int,
        match_date: pd.Timestamp
    ) -> Dict[str, float]:

        features = {}
        
        # Filter h2h strictly before match_date
        h2h = self.head_to_head[self.head_to_head["date"] < match_date].copy()
        
        # Find matches between these two teams
        h2h_matches = h2h[
            ((h2h["home_team_id"] == home_id) & (h2h["away_team_id"] == away_id)) |
            ((h2h["home_team_id"] == away_id) & (h2h["away_team_id"] == home_id))
        ]
        
        if len(h2h_matches) == 0:
            features["h2h_total_matches"] = 0
            features["h2h_home_team_win_rate"] = 0
            features["h2h_away_team_win_rate"] = 0
            features["h2h_draw_rate"] = 0
            features["h2h_home_avg_goals"] = 0
            features["h2h_away_avg_goals"] = 0
            features["h2h_over_2_5_rate"] = 0
            features["h2h_btts_rate"] = 0
            return features
        
        features["h2h_total_matches"] = len(h2h_matches)
        
        # Calculate win rates for home team in h2h context
        home_team_wins = 0
        away_team_wins = 0
        draws = 0
        home_goals_list = []
        away_goals_list = []
        
        for _, match in h2h_matches.iterrows():
            if match["home_team_id"] == home_id:
                # This match has our home_team as home
                if match["home_goals"] > match["away_goals"]:
                    home_team_wins += 1
                elif match["home_goals"] < match["away_goals"]:
                    away_team_wins += 1
                else:
                    draws += 1
                home_goals_list.append(match["home_goals"])
                away_goals_list.append(match["away_goals"])
            else:
                # This match has our home_team as away
                if match["away_goals"] > match["home_goals"]:
                    home_team_wins += 1
                elif match["away_goals"] < match["home_goals"]:
                    away_team_wins += 1
                else:
                    draws += 1
                home_goals_list.append(match["away_goals"])
                away_goals_list.append(match["home_goals"])
        
        total = len(h2h_matches)
        features["h2h_home_team_win_rate"] = home_team_wins / total if total > 0 else 0
        features["h2h_away_team_win_rate"] = away_team_wins / total if total > 0 else 0
        features["h2h_draw_rate"] = draws / total if total > 0 else 0
        features["h2h_home_avg_goals"] = np.mean(home_goals_list) if home_goals_list else 0
        features["h2h_away_avg_goals"] = np.mean(away_goals_list) if away_goals_list else 0
        
        # Over 2.5 goals
        total_goals = np.array(home_goals_list) + np.array(away_goals_list)
        features["h2h_over_2_5_rate"] = (total_goals > 2.5).mean() if len(total_goals) > 0 else 0
        
        # BTTS (Both Teams To Score)
        btts = (np.array(home_goals_list) > 0) & (np.array(away_goals_list) > 0)
        features["h2h_btts_rate"] = btts.mean() if len(btts) > 0 else 0
        
        return features
    
    def _build_strength_features(
        self,
        home_id: int,
        away_id: int,
        history: pd.DataFrame
    ) -> Dict[str, float]:

        features = {}
        
        # League average stats
        league_avg_goals = history["home_goals"].mean() + history["away_goals"].mean() / 2
        league_avg_conceded = league_avg_goals
        
        if league_avg_goals == 0:
            league_avg_goals = 1  # Avoid division by zero
        
        # Home team stats
        home_team_all = history[
            (history["home_id"] == home_id) | (history["away_id"] == home_id)
        ]
        
        if len(home_team_all) > 0:
            # Goals scored (as home and away)
            home_scored = history[history["home_id"] == home_id]["home_goals"].sum()
            away_scored = history[history["away_id"] == home_id]["away_goals"].sum()
            home_total_scored = home_scored + away_scored
            
            # Goals conceded
            home_conceded = history[history["home_id"] == home_id]["away_goals"].sum()
            away_conceded = history[history["away_id"] == home_id]["home_goals"].sum()
            home_total_conceded = home_conceded + away_conceded
            
            home_matches = len(home_team_all)
            home_avg_scored = home_total_scored / home_matches if home_matches > 0 else 0
            home_avg_conceded = home_total_conceded / home_matches if home_matches > 0 else 0
            
            features["home_attack_strength"] = home_avg_scored / league_avg_goals
            features["home_defense_strength"] = home_avg_conceded / league_avg_conceded
        else:
            features["home_attack_strength"] = 1.0
            features["home_defense_strength"] = 1.0
        
        # Away team stats
        away_team_all = history[
            (history["home_id"] == away_id) | (history["away_id"] == away_id)
        ]
        
        if len(away_team_all) > 0:
            away_scored = history[history["home_id"] == away_id]["home_goals"].sum()
            home_scored_away = history[history["away_id"] == away_id]["away_goals"].sum()
            away_total_scored = away_scored + home_scored_away
            
            away_conceded = history[history["home_id"] == away_id]["away_goals"].sum()
            home_conceded_away = history[history["away_id"] == away_id]["home_goals"].sum()
            away_total_conceded = away_conceded + home_conceded_away
            
            away_matches = len(away_team_all)
            away_avg_scored = away_total_scored / away_matches if away_matches > 0 else 0
            away_avg_conceded = away_total_conceded / away_matches if away_matches > 0 else 0
            
            features["away_attack_strength"] = away_avg_scored / league_avg_goals
            features["away_defense_strength"] = away_avg_conceded / league_avg_conceded
        else:
            features["away_attack_strength"] = 1.0
            features["away_defense_strength"] = 1.0
        
        return features
    
    def _build_momentum_features(
        self,
        home_matches: pd.DataFrame,
        away_matches: pd.DataFrame
    ) -> Dict[str, float]:

        features = {}
        
        # Home team momentum
        if len(home_matches) >= 6:
            last3 = home_matches.tail(3)
            prev3 = home_matches.tail(6).head(3)
            
            home_scored_last3 = last3["home_goals"].sum()
            home_scored_prev3 = prev3["home_goals"].sum()
            features["home_momentum_attack"] = home_scored_last3 - home_scored_prev3
            
            home_conceded_last3 = last3["away_goals"].sum()
            home_conceded_prev3 = prev3["away_goals"].sum()
            features["home_momentum_defense"] = home_conceded_prev3 - home_conceded_last3
        else:
            features["home_momentum_attack"] = 0
            features["home_momentum_defense"] = 0
        
        # Away team momentum
        if len(away_matches) >= 6:
            last3 = away_matches.tail(3)
            prev3 = away_matches.tail(6).head(3)
            
            away_scored_last3 = last3["away_goals"].sum()
            away_scored_prev3 = prev3["away_goals"].sum()
            features["away_momentum_attack"] = away_scored_last3 - away_scored_prev3
            
            away_conceded_last3 = last3["home_goals"].sum()
            away_conceded_prev3 = prev3["home_goals"].sum()
            features["away_momentum_defense"] = away_conceded_prev3 - away_conceded_last3
        else:
            features["away_momentum_attack"] = 0
            features["away_momentum_defense"] = 0
        
        return features
    
    def _build_rest_features(
        self,
        home_id: int,
        away_id: int,
        match_date: pd.Timestamp,
        history: pd.DataFrame
    ) -> Dict[str, float]:

        features = {}
        
        # Home team's last match
        home_last = history[history["home_id"] == home_id].sort_values("date").tail(1)
        if len(home_last) == 0:
            home_last = history[history["away_id"] == home_id].sort_values("date").tail(1)
        
        if len(home_last) > 0:
            days_rest = (match_date - home_last.iloc[0]["date"]).days
            features["home_days_since_last_match"] = max(days_rest, 0)
        else:
            features["home_days_since_last_match"] = 0
        
        # Away team's last match
        away_last = history[history["away_id"] == away_id].sort_values("date").tail(1)
        if len(away_last) == 0:
            away_last = history[history["home_id"] == away_id].sort_values("date").tail(1)
        
        if len(away_last) > 0:
            days_rest = (match_date - away_last.iloc[0]["date"]).days
            features["away_days_since_last_match"] = max(days_rest, 0)
        else:
            features["away_days_since_last_match"] = 0
        
        return features
    
    def _build_event_features(
        self,
        home_id: int,
        away_id: int,
        history: pd.DataFrame
    ) -> Dict[str, float]:

        features = {}
        
        # Try to load fixture statistics
        try:
            fixture_stats = self.loader.load_fixture_statistics()
            if len(fixture_stats) == 0:
                return features
            
            # Get fixture IDs for these teams' recent matches
            relevant_fixtures = history[
                (history["home_id"] == home_id) | (history["away_id"] == home_id) |
                (history["home_id"] == away_id) | (history["away_id"] == away_id)
            ]
            
            if "fixture_id" in relevant_fixtures.columns:
                fixture_ids = set(relevant_fixtures["fixture_id"].unique())
                stats = fixture_stats[fixture_stats["fixture_id"].isin(fixture_ids)]
                
                # Average statistics
                for col in ["shots", "shots_on_target", "ball_possession", "corners", "fouls"]:
                    if col in stats.columns:
                        features[f"avg_{col}_last5"] = stats[col].mean()
                    else:
                        features[f"avg_{col}_last5"] = 0
        
        except Exception as e:
            logger.debug(f"Could not load event features: {e}")
        
        return features
    
    def _get_default_features(self) -> Dict[str, float]:

        # This is a fallback - features are built based on config
        default_dict = {}
        
        # Add all possible features with 0/default values
        for window in FEATURE_CONFIG["lookback_windows"]:
            for prefix in ["home", "away"]:
                default_dict[f"{prefix}_last{window}_matches_played"] = 0
                default_dict[f"{prefix}_last{window}_avg_goals_scored"] = 0
                default_dict[f"{prefix}_last{window}_avg_goals_conceded"] = 0
                default_dict[f"{prefix}_last{window}_win_rate"] = 0
                default_dict[f"{prefix}_last{window}_draw_rate"] = 0
                default_dict[f"{prefix}_last{window}_loss_rate"] = 0
                default_dict[f"{prefix}_last{window}_clean_sheet_rate"] = 0
                default_dict[f"{prefix}_last{window}_failed_to_score_rate"] = 0
                default_dict[f"{prefix}_last{window}_total_points"] = 0
                default_dict[f"{prefix}_last{window}_goal_difference"] = 0
        
        return default_dict
    
    def get_feature_names(self) -> List[str]:

        # Build dummy features to determine all columns
        sample = self.build_features_for_match(1, 2, self.fixtures["date"].max())
        return [col for col in sample.index if col not in ["match_date", "home_goals", "away_goals"]]
