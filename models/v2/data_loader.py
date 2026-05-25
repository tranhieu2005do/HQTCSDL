
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

import pandas as pd
import numpy as np

from models.v2.config import DATA_FILES, FEATURE_CONFIG

logger = logging.getLogger(__name__)


class DataLoader:
    
    def __init__(self, data_files: Optional[Dict[str, Path]] = None):
        self.data_files = data_files or DATA_FILES
        self.data_cache: Dict[str, pd.DataFrame] = {}
    
    def load_json(self, file_path: Path) -> List[Dict[str, Any]]:
        if not file_path.exists():
            logger.error(f"File not found: {file_path}")
            raise FileNotFoundError(f"Data file not found: {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                logger.debug(f"Loaded {len(data)} records from {file_path.name}")
                return data if isinstance(data, list) else [data]
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in {file_path}: {e}")
            raise
    
    def load_fixtures(self) -> pd.DataFrame:
        if "fixtures" in self.data_cache:
            return self.data_cache["fixtures"]
        
        data = self.load_json(self.data_files["fixtures"])
        df = pd.DataFrame(data)
        
        # Convert date to datetime
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        
        # Sort by date
        df = df.sort_values("date").reset_index(drop=True)
        
        self.data_cache["fixtures"] = df
        return df
    
    def load_head_to_head(self) -> pd.DataFrame:
        if "head_to_head" in self.data_cache:
            return self.data_cache["head_to_head"]
        
        data = self.load_json(self.data_files["head_to_head"])
        df = pd.DataFrame(data)
        
        # Convert date to datetime
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        
        # Sort by date
        df = df.sort_values("date").reset_index(drop=True)
        
        self.data_cache["head_to_head"] = df
        return df
    
    def load_teams(self) -> pd.DataFrame:
        if "teams" in self.data_cache:
            return self.data_cache["teams"]
        
        data = self.load_json(self.data_files["teams"])
        df = pd.DataFrame(data)
        
        self.data_cache["teams"] = df
        logger.info(f"Loaded {len(df)} teams")
        return df
    
    def load_fixture_statistics(self) -> pd.DataFrame:
        if "fixture_statistics" in self.data_cache:
            return self.data_cache["fixture_statistics"]
        
        try:
            data = self.load_json(self.data_files["fixture_statistics"])
            df = pd.DataFrame(data)
            self.data_cache["fixture_statistics"] = df
            logger.info(f"Loaded {len(df)} fixture statistics")
            return df
        except FileNotFoundError:
            logger.warning("Fixture statistics file not found")
            return pd.DataFrame()
    
    def load_goal_events(self) -> pd.DataFrame:
        if "goal_events" in self.data_cache:
            return self.data_cache["goal_events"]
        
        try:
            data = self.load_json(self.data_files["goal_events"])
            df = pd.DataFrame(data)
            self.data_cache["goal_events"] = df
            logger.info(f"Loaded {len(df)} goal events")
            return df
        except FileNotFoundError:
            logger.warning("Goal events file not found")
            return pd.DataFrame()
    
    def load_card_events(self) -> pd.DataFrame:
        if "card_events" in self.data_cache:
            return self.data_cache["card_events"]
        
        try:
            data = self.load_json(self.data_files["card_events"])
            df = pd.DataFrame(data)
            self.data_cache["card_events"] = df
            logger.info(f"Loaded {len(df)} card events")
            return df
        except FileNotFoundError:
            logger.warning("Card events file not found")
            return pd.DataFrame()
    
    def load_venues(self) -> pd.DataFrame:
        if "venues" in self.data_cache:
            return self.data_cache["venues"]
        
        try:
            data = self.load_json(self.data_files["venues"])
            df = pd.DataFrame(data)
            self.data_cache["venues"] = df
            logger.info(f"Loaded {len(df)} venues")
            return df
        except FileNotFoundError:
            logger.warning("Venues file not found")
            return pd.DataFrame()
    
    def load_all_data(self) -> Dict[str, pd.DataFrame]:
        logger.info("Loading all data...")
        return {
            "fixtures": self.load_fixtures(),
            "head_to_head": self.load_head_to_head(),
            "teams": self.load_teams(),
            "fixture_statistics": self.load_fixture_statistics(),
            "goal_events": self.load_goal_events(),
            "card_events": self.load_card_events(),
            "venues": self.load_venues(),
        }
    
    def get_team_id_mapping(self) -> Dict[str, int]:
        teams = self.load_teams()
        
        # Try different naming column possibilities
        name_cols = ["name", "team_name", "team", "Name"]
        id_cols = ["id", "team_id", "Id"]
        
        name_col = next((col for col in name_cols if col in teams.columns), None)
        id_col = next((col for col in id_cols if col in teams.columns), None)
        
        if name_col is None or id_col is None:
            logger.warning(f"Could not find name/id columns in teams. Available: {teams.columns.tolist()}")
            return {}
        
        mapping = dict(zip(teams[name_col], teams[id_col]))
        return mapping
    
    def get_team_name_mapping(self) -> Dict[int, str]:
        teams = self.load_teams()
        
        # Try different naming column possibilities
        name_cols = ["name", "team_name", "team", "Name"]
        id_cols = ["id", "team_id", "Id"]
        
        name_col = next((col for col in name_cols if col in teams.columns), None)
        id_col = next((col for col in id_cols if col in teams.columns), None)
        
        if name_col is None or id_col is None:
            return {}
        
        mapping = dict(zip(teams[id_col], teams[name_col]))
        return mapping
    
    def data_summary(self) -> Dict[str, Any]:
        fixtures = self.load_fixtures()
        
        summary = {
            "total_fixtures": len(fixtures),
            "date_range": {
                "start": fixtures["date"].min() if len(fixtures) > 0 else None,
                "end": fixtures["date"].max() if len(fixtures) > 0 else None,
            },
            "total_goals": {
                "home": fixtures["home_goals"].sum(),
                "away": fixtures["away_goals"].sum(),
            },
            "avg_goals": {
                "home": fixtures["home_goals"].mean(),
                "away": fixtures["away_goals"].mean(),
            },
            "unique_teams": len(set(list(fixtures["home_id"].unique()) + list(fixtures["away_id"].unique()))),
        }
        
        return summary
    
    def clear_cache(self) -> None:
        """Clear the data cache."""
        self.data_cache.clear()
        logger.info("Data cache cleared")
