"""
Model training module for football score prediction.

Handles training XGBoost models for home and away goals prediction
with proper cross-validation and hyperparameter tuning.
"""

import logging
import pickle
import sys
from pathlib import Path
from typing import Tuple, Dict, Any, Optional

import numpy as np
import pandas as pd
from sklearn.model_selection import TimeSeriesSplit, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.ensemble import RandomForestRegressor
from xgboost import XGBRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import optuna
from optuna.samplers import TPESampler
from tqdm import tqdm

from models.v2.data_loader import DataLoader
from models.v2.feature_engineering import FeatureEngineer
from models.v2.config import TRAINING_CONFIG, MODEL_FILES

logger = logging.getLogger(__name__)


class ModelTrainer:
    """Train and evaluate XGBoost models for goal prediction."""
    
    def __init__(self, data_loader: DataLoader):
        """
        Initialize ModelTrainer.
        
        Args:
            data_loader: DataLoader instance.
        """
        self.loader = data_loader
        self.engineer = FeatureEngineer(data_loader)
        
        self.model_home: Optional[XGBRegressor] = None
        self.model_away: Optional[XGBRegressor] = None
        self.scaler = StandardScaler()
        self.imputer = SimpleImputer(strategy="mean")
        self.feature_columns: Optional[list] = None
        self.label_encoders: Dict[str, Any] = {}
        
        logger.info("ModelTrainer initialized")
    
    def prepare_data(self) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Prepare training data with feature engineering.
        
        Returns:
            Tuple of (X_train, y_train)
        """
        logger.info("Preparing training data...")
        X, y = self.engineer.build_training_data()
        
        # Remove rows with NaN targets
        mask = (y["home_goals"].notna()) & (y["away_goals"].notna())
        X = X[mask]
        y = y[mask]
        
        # Store feature columns
        self.feature_columns = X.columns.tolist()
        
        logger.info(f"Training data shape: {X.shape}")
        logger.info(f"Feature columns: {len(self.feature_columns)}")
        
        return X, y
    
    def preprocess_features(
        self,
        X: pd.DataFrame,
        fit: bool = True
    ) -> pd.DataFrame:
        """
        Preprocess features (handle missing values, scale).
        
        Args:
            X: Feature dataframe.
            fit: If True, fit imputer and scaler. If False, just transform.
            
        Returns:
            Preprocessed feature array (as DataFrame).
        """
        logger.info("Preprocessing features...")
        
        # Separate numeric and categorical columns
        numeric_cols = X.select_dtypes(include=[np.number]).columns.tolist()
        
        X_numeric = X[numeric_cols].copy()
        if fit:
            self.feature_columns = numeric_cols
        
        # Handle missing values
        if fit:
            X_numeric = pd.DataFrame(
                self.imputer.fit_transform(X_numeric),
                columns=numeric_cols,
                index=X_numeric.index
            )
        else:
            X_numeric = pd.DataFrame(
                self.imputer.transform(X_numeric),
                columns=numeric_cols,
                index=X_numeric.index
            )
        
        # Scale features
        if fit:
            X_numeric = pd.DataFrame(
                self.scaler.fit_transform(X_numeric),
                columns=numeric_cols,
                index=X_numeric.index
            )
        else:
            X_numeric = pd.DataFrame(
                self.scaler.transform(X_numeric),
                columns=numeric_cols,
                index=X_numeric.index
            )
        
        logger.info(f"Features preprocessed: {X_numeric.shape}")
        
        return X_numeric
    
    def _compute_cv_folds(self, n_samples: int) -> int:
        """Compute a valid number of TimeSeriesSplit folds based on sample count."""
        desired_splits = int(TRAINING_CONFIG.get("cv_folds", 5))
        if n_samples < 4:
            return 0
        return min(desired_splits, n_samples - 1)
    
    def hyperparameter_optimization(
        self,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        n_trials: int = 50,
        target: str = "home_goals"
    ) -> Dict[str, Any]:
        """
        Optimize hyperparameters using Optuna.
        
        Args:
            X_train: Training features.
            y_train: Training targets.
            n_trials: Number of optimization trials.
            target: "home_goals" or "away_goals"
            
        Returns:
            Best hyperparameters.
        """
        logger.info(f"Starting hyperparameter optimization for {target}...")
        
        n_samples = len(X_train)
        n_splits = self._compute_cv_folds(n_samples)
        if n_splits == 0:
            logger.warning(
                "Not enough training samples to run TimeSeriesSplit. "
                "Skipping hyperparameter optimization and using default parameters."
            )
            fallback_params = TRAINING_CONFIG["xgboost_base_params"].copy()
            fallback_params.update({
                "n_estimators": 100,
                "max_depth": 5,
                "learning_rate": 0.1,
                "subsample": 0.8,
                "colsample_bytree": 0.8,
                "min_child_weight": 1,
            })
            return fallback_params
        
        def objective(trial):
            # Suggest hyperparameters
            params = {
                "n_estimators": trial.suggest_int("n_estimators", 50, 300),
                "max_depth": trial.suggest_int("max_depth", 3, 12),
                "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.3),
                "subsample": trial.suggest_float("subsample", 0.6, 1.0),
                "colsample_bytree": trial.suggest_float("colsample_bytree", 0.6, 1.0),
                "min_child_weight": trial.suggest_int("min_child_weight", 1, 10),
                **TRAINING_CONFIG["xgboost_base_params"]
            }
            
            # Create model
            model = XGBRegressor(**params)
            
            # Cross-validation
            cv_scores = cross_val_score(
                model, X_train, y_train,
                cv=TimeSeriesSplit(n_splits=n_splits),
                scoring="neg_mean_squared_error",
                n_jobs=-1
            )
            
            # Return mean score (negative MSE, so higher is better)
            return -cv_scores.mean()
        
        # Create study and optimize
        sampler = TPESampler(seed=42)
        study = optuna.create_study(sampler=sampler, direction="minimize")
        study.optimize(objective, n_trials=n_trials, show_progress_bar=True)
        
        best_params = study.best_params
        logger.info(f"Best parameters for {target}: {best_params}")
        logger.info(f"Best score: {study.best_value:.4f}")
        
        return best_params
    
    def train(
        self,
        X_train: Optional[pd.DataFrame] = None,
        y_train: Optional[pd.DataFrame] = None,
        optimize_hyperparams: bool = True
    ) -> Dict[str, Any]:
        """
        Train models for home and away goals.
        
        Args:
            X_train: Training features. If None, will prepare from data.
            y_train: Training targets. If None, will prepare from data.
            optimize_hyperparams: Whether to optimize hyperparameters.
            
        Returns:
            Dictionary with training metrics.
        """
        # Prepare data if not provided
        if X_train is None or y_train is None:
            X_train, y_train = self.prepare_data()
        
        # Preprocess features
        X_processed = self.preprocess_features(X_train, fit=True)
        
        if len(X_processed) == 0:
            raise ValueError("No training samples available after preprocessing.")
        
        # Split data for validation (time series aware)
        n_train = int(len(X_processed) * 0.8)
        if n_train < 1:
            n_train = 1
        if len(X_processed) - n_train < 1:
            n_train = len(X_processed) - 1
        
        if n_train < 1:
            raise ValueError(
                "Insufficient data to create a train/test split. "
                "Need at least 2 samples."
            )
        
        X_train_split = X_processed[:n_train]
        X_test_split = X_processed[n_train:]
        y_train_split = y_train[:n_train]
        y_test_split = y_train[n_train:]
        
        logger.info(f"Train/Test split: {len(X_train_split)}/{len(X_test_split)}")
        
        # Train models
        metrics = {}
        
        for target in ["home_goals", "away_goals"]:
            logger.info(f"\n{'='*60}")
            logger.info(f"Training model for {target}")
            logger.info(f"{'='*60}")
            
            y_target = y_train_split[target]
            y_target_test = y_test_split[target]
            
            # Optimize hyperparameters if requested
            if optimize_hyperparams:
                best_params = self.hyperparameter_optimization(
                    X_train_split, y_target, n_trials=50, target=target
                )
            else:
                best_params = TRAINING_CONFIG["xgboost_base_params"].copy()
                best_params.update({
                    "n_estimators": 100,
                    "max_depth": 5,
                    "learning_rate": 0.1,
                    "subsample": 0.8,
                    "colsample_bytree": 0.8,
                    "min_child_weight": 1,
                })
            
            # Create and train model
            model = XGBRegressor(**best_params)
            model.fit(
                X_train_split, y_target,
                eval_set=[(X_test_split, y_target_test)],
                verbose=False
            )
            
            # Evaluate on test set
            y_pred_train = model.predict(X_train_split)
            y_pred_test = model.predict(X_test_split)
            
            train_mae = mean_absolute_error(y_target, y_pred_train)
            test_mae = mean_absolute_error(y_target_test, y_pred_test)
            
            train_rmse = np.sqrt(mean_squared_error(y_target, y_pred_train))
            test_rmse = np.sqrt(mean_squared_error(y_target_test, y_pred_test))
            
            train_r2 = r2_score(y_target, y_pred_train)
            test_r2 = r2_score(y_target_test, y_pred_test)
            
            logger.info(f"\nMetrics for {target}:")
            logger.info(f"  Train MAE:  {train_mae:.4f}")
            logger.info(f"  Test MAE:   {test_mae:.4f}")
            logger.info(f"  Train RMSE: {train_rmse:.4f}")
            logger.info(f"  Test RMSE:  {test_rmse:.4f}")
            logger.info(f"  Train R2:   {train_r2:.4f}")
            logger.info(f"  Test R2:    {test_r2:.4f}")
            
            # Store model
            if target == "home_goals":
                self.model_home = model
                metrics["home_goals"] = {
                    "train_mae": train_mae,
                    "test_mae": test_mae,
                    "train_rmse": train_rmse,
                    "test_rmse": test_rmse,
                    "train_r2": train_r2,
                    "test_r2": test_r2,
                }
            else:
                self.model_away = model
                metrics["away_goals"] = {
                    "train_mae": train_mae,
                    "test_mae": test_mae,
                    "train_rmse": train_rmse,
                    "test_rmse": test_rmse,
                    "train_r2": train_r2,
                    "test_r2": test_r2,
                }
            
            # Feature importance
            importance = pd.DataFrame({
                "feature": self.feature_columns,
                "importance": model.feature_importances_,
                "target": target
            }).sort_values("importance", ascending=False)
            
            logger.info(f"\nTop 10 features for {target}:")
            logger.info(importance.head(10).to_string(index=False))
            
            metrics[f"{target}_importance"] = importance
        
        return metrics
    
    def save_models(self) -> None:
        """Save trained models and preprocessing objects."""
        logger.info("Saving models...")
        
        if self.model_home is None or self.model_away is None:
            raise ValueError("Models not trained yet")
        
        # Create save directory
        MODEL_FILES["home_goals_model"].parent.mkdir(parents=True, exist_ok=True)
        
        # Save models
        with open(MODEL_FILES["home_goals_model"], "wb") as f:
            pickle.dump(self.model_home, f)
        logger.info(f"Saved home goals model to {MODEL_FILES['home_goals_model']}")
        
        with open(MODEL_FILES["away_goals_model"], "wb") as f:
            pickle.dump(self.model_away, f)
        logger.info(f"Saved away goals model to {MODEL_FILES['away_goals_model']}")
        
        # Save preprocessing
        with open(MODEL_FILES["scaler"], "wb") as f:
            pickle.dump(self.scaler, f)
        logger.info(f"Saved scaler to {MODEL_FILES['scaler']}")
        
        with open(MODEL_FILES["imputer"], "wb") as f:
            pickle.dump(self.imputer, f)
        logger.info(f"Saved imputer to {MODEL_FILES['imputer']}")
        
        # Save feature columns
        with open(MODEL_FILES["feature_columns"], "wb") as f:
            pickle.dump(self.feature_columns, f)
        logger.info(f"Saved feature columns to {MODEL_FILES['feature_columns']}")
        
        logger.info("All models saved successfully")


def setup_logging() -> None:
    """Setup logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(
                Path(__file__).parent / "logs" / "training.log",
                mode="a"
            )
        ]
    )
    logging.getLogger("optuna").setLevel(logging.WARNING)


def main():
    """Main training function."""
    setup_logging()
    logger.info("="*70)
    logger.info("Starting model training")
    logger.info("="*70)
    
    try:
        # Load data
        loader = DataLoader()
        
        # Create trainer
        trainer = ModelTrainer(loader)
        
        # Train models
        metrics = trainer.train(optimize_hyperparams=True)
        
        # Save models
        trainer.save_models()
        
        # Print summary
        logger.info("\n" + "="*70)
        logger.info("TRAINING SUMMARY")
        logger.info("="*70)
        
        for target in ["home_goals", "away_goals"]:
            if target in metrics:
                logger.info(f"\n{target.upper()}:")
                for key, value in metrics[target].items():
                    logger.info(f"  {key}: {value:.4f}")
        
        logger.info("\nTraining completed successfully!")
        
    except Exception as e:
        logger.error(f"Training failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
