import logging
import pandas as pd
import numpy as np
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
from scipy.interpolate import interp1d
import os
import joblib
import datetime

logger = logging.getLogger("tnea_ai.predictor")

class Predictor:
    def __init__(self, data_engine):
        self.data_engine = data_engine
        self.mark_to_percentile_model = None
        self.mark_to_percentile_lower = None
        self.mark_to_percentile_upper = None
        self.percentile_to_rank_model = None
        self.total_students = 200000
        
        # Define models directory structure
        self.base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.models_root = os.path.join(self.base_dir, "models")
        self.versions_root = os.path.join(self.models_root, "versions")
        self.latest_pointer_file = os.path.join(self.models_root, "latest.txt")
        
        os.makedirs(self.versions_root, exist_ok=True)
        self.current_version_dir = None
        self.model_paths = {}

        self.initialize_models()

    def _set_model_paths(self, version_dir):
        """Sets internal model paths to a specific version directory."""
        self.current_version_dir = version_dir
        self.model_paths = {
            "percentile": os.path.join(version_dir, "percentile_model.joblib"),
            "percentile_lower": os.path.join(version_dir, "percentile_lower.joblib"),
            "percentile_upper": os.path.join(version_dir, "percentile_upper.joblib"),
            "rank": os.path.join(version_dir, "rank_model.joblib"),
            "meta": os.path.join(version_dir, "model_meta.joblib")
        }

    def initialize_models(self):
        """Initializes models by loading the latest version or training new ones."""
        # Try to resolve latest version
        if os.path.exists(self.latest_pointer_file):
            try:
                with open(self.latest_pointer_file, 'r') as f:
                    rel_path = f.read().strip()
                
                full_path = os.path.join(self.models_root, rel_path)
                if os.path.exists(full_path):
                    self._set_model_paths(full_path)
                    
                    # Check for staleness
                    if not self._should_retrain():
                        logger.info(f"Loading models from version: {rel_path}...")
                        if self.load_models():
                            return
                        else:
                            logger.warning("Failed to load models from latest version.")
                    else:
                        logger.info("Latest model version is stale. Retraining...")
            except Exception as e:
                logger.error(f"Error reading latest model pointer: {e}")

        # Fallback to training
        logger.info("Initializing new model training...")
        self.train_models()

    def _should_retrain(self) -> bool:
        """Checks if current version is stale compared to data."""
        if not self.model_paths: 
            return True
            
        # Check if model files exist
        if not all(os.path.exists(p) for p in self.model_paths.values()):
            return True
            
        # Check data file modification time
        try:
            data_file = os.path.join(self.data_engine.data_dir, "csv/percentile_ranges.csv")
            if not os.path.exists(data_file):
                return True
                
            data_mtime = os.path.getmtime(data_file)
            model_mtime = os.path.getmtime(self.model_paths["meta"])
            
            return data_mtime > model_mtime
        except Exception as e:
            logger.warning(f"Error checking model freshness: {e}")
            return True

    def train_models(self):
        """Trains models creating a new version."""
        if self.data_engine.percentile_ranges is None or self.data_engine.percentile_ranges.empty:
            logger.warning("No data available for training models. Prediction will fail.")
            return

        try:
            logger.info("Starting model training...")
            
            # create new version directory
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            version_id = f"v_{timestamp}"
            new_version_dir = os.path.join(self.versions_root, version_id)
            os.makedirs(new_version_dir, exist_ok=True)
            
            # Point to new directory
            self._set_model_paths(new_version_dir)

            df = self.data_engine.percentile_ranges
            X = df[['mark', 'year']]
            y = df['max_percentile']

            # 1. Main Model
            self.mark_to_percentile_model = HistGradientBoostingRegressor(loss="squared_error", random_state=42)
            self.mark_to_percentile_model.fit(X, y)

            # 2. Lower Bound
            self.mark_to_percentile_lower = HistGradientBoostingRegressor(loss="quantile", quantile=0.05, random_state=42)
            self.mark_to_percentile_lower.fit(X, y)

            # 3. Upper Bound
            self.mark_to_percentile_upper = HistGradientBoostingRegressor(loss="quantile", quantile=0.95, random_state=42)
            self.mark_to_percentile_upper.fit(X, y)

            df_sorted = df.sort_values('max_percentile', ascending=False)
            latest_year = df['year'].max()
            df_latest = df_sorted[df_sorted['year'] == latest_year]

            if not df_latest.empty:
                self.percentile_to_rank_model = interp1d(
                    df_latest['max_percentile'],
                    df_latest['min_rank'],
                    kind='linear',
                    fill_value="extrapolate"
                )
                self.total_students = df_latest['total_students'].iloc[0] if 'total_students' in df_latest.columns else 200000
            
            # Save models to new version dir
            self.save_models()
            
            # Update latest pointer
            try:
                rel_path = os.path.join("versions", version_id)
                with open(self.latest_pointer_file, 'w') as f:
                    f.write(rel_path)
            except Exception as e:
                logger.error(f"Failed to update latest.txt: {e}")
            
            logger.info(f"Models trained and saved to version {version_id}.")
        except Exception as e:
            logger.error(f"Error training models: {e}")

    def save_models(self):
        """Saves trained models to the current version directory."""
        try:
            if self.mark_to_percentile_model:
                joblib.dump(self.mark_to_percentile_model, self.model_paths["percentile"])
            if self.mark_to_percentile_lower:
                joblib.dump(self.mark_to_percentile_lower, self.model_paths["percentile_lower"])
            if self.mark_to_percentile_upper:
                joblib.dump(self.mark_to_percentile_upper, self.model_paths["percentile_upper"])
            
            if self.percentile_to_rank_model:
                joblib.dump(self.percentile_to_rank_model, self.model_paths["rank"])
                
            meta = {
                "total_students": self.total_students,
                "timestamp": pd.Timestamp.now().isoformat()
            }
            joblib.dump(meta, self.model_paths["meta"])
            
        except Exception as e:
            logger.error(f"Error saving models: {e}")

    def load_models(self) -> bool:
        """Loads models from disk."""
        try:
            self.mark_to_percentile_model = joblib.load(self.model_paths["percentile"])
            self.mark_to_percentile_lower = joblib.load(self.model_paths["percentile_lower"])
            self.mark_to_percentile_upper = joblib.load(self.model_paths["percentile_upper"])
            self.percentile_to_rank_model = joblib.load(self.model_paths["rank"])
            
            meta = joblib.load(self.model_paths["meta"])
            self.total_students = meta.get("total_students", 200000)
            
            return True
        except Exception as e:
            logger.error(f"Error loading models: {e}")
            return False

    def predict_percentile(self, mark: float, year: int = 2026) -> dict:
        """Predicts percentile range for a given mark and year."""
        if not self.mark_to_percentile_model:
            return {"prediction": 0.0, "lower": 0.0, "upper": 0.0}

        input_data = pd.DataFrame({'mark': [mark], 'year': [year]})
        
        pred = self.mark_to_percentile_model.predict(input_data)[0]
        lower = self.mark_to_percentile_lower.predict(input_data)[0]
        upper = self.mark_to_percentile_upper.predict(input_data)[0]
        
        # Ensure logical consistency (lower <= pred <= upper) and bounds (0-100)
        pred = max(0.0, min(100.0, pred))
        lower = max(0.0, min(pred, lower)) # lower can't be higher than pred
        upper = min(100.0, max(pred, upper)) # upper can't be lower than pred

        return {
            "prediction": round(float(pred), 3),
            "lower": round(float(lower), 3),
            "upper": round(float(upper), 3)
        }

    def predict_rank(self, percentile: float) -> int:
        """Predicts rank from percentile using latest data interpolation."""
        if not self.percentile_to_rank_model:
            return 0

        percentile = max(0.0, min(100.0, percentile))
        rank = self.percentile_to_rank_model(percentile)
        return int(max(1, rank))

    def predict_total_students(self, target_year: int = 2026) -> int:
        """Predicts total students for a given year using linear trend extrapolation."""
        if self.data_engine.percentile_ranges is None or self.data_engine.percentile_ranges.empty:
            return int(self.total_students)

        try:
            df = self.data_engine.percentile_ranges
            year_totals = df.groupby('year')['total_students'].first().reset_index()

            if len(year_totals) < 2:
                return int(self.total_students)

            from sklearn.linear_model import LinearRegression
            X_years = year_totals['year'].values.reshape(-1, 1)
            y_totals = year_totals['total_students'].values

            model = LinearRegression()
            model.fit(X_years, y_totals)
            predicted = model.predict([[target_year]])[0]

            return int(max(predicted, y_totals.max()))
        except Exception:
            return int(self.total_students)

if __name__ == "__main__":
    # Mock DataEngine for testing
    class MockDataEngine:
        def __init__(self):
            # Try to load real data if possible, or mock it
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            csv_path = os.path.join(base_dir, "data/csv/percentile_ranges.csv")
            self.data_dir = os.path.join(base_dir, "data")
            if os.path.exists(csv_path):
                self.percentile_ranges = pd.read_csv(csv_path)
            else:
                self.percentile_ranges = pd.DataFrame({
                    'mark': [190, 180, 170], 
                    'year': [2025, 2025, 2025],
                    'max_percentile': [99.5, 95.0, 90.0],
                    'min_rank': [100, 1000, 2000],
                    'total_students': [200000, 200000, 200000]
                })

    data = MockDataEngine()
    predictor = Predictor(data)

    p = predictor.predict_percentile(195)
    r = predictor.predict_rank(p)
    logger.info(f"Mark: 195 -> Percentile: {p} -> Rank: {r}")
