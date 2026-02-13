import logging
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from scipy.interpolate import interp1d
import os

logger = logging.getLogger("tnea_ai.predictor")


class Predictor:
    def __init__(self, data_engine):
        self.data_engine = data_engine
        self.mark_to_percentile_model = None
        self.percentile_to_rank_model = None
        self.total_students = 200000

        self.train_models()

    def train_models(self):
        """Trains models using data from DataEngine."""
        if self.data_engine.percentile_ranges is None or self.data_engine.percentile_ranges.empty:
            logger.warning("No data available for training models. Prediction will fail.")
            return

        try:
            df = self.data_engine.percentile_ranges
            X = df[['mark', 'year']]
            y = df['max_percentile']

            self.mark_to_percentile_model = RandomForestRegressor(n_estimators=100, random_state=42)
            self.mark_to_percentile_model.fit(X, y)

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
            
            logger.info(f"Models trained. Latest year: {latest_year}, Total students: {self.total_students}")
        except Exception as e:
            logger.error(f"Error training models: {e}")

    def predict_percentile(self, mark: float, year: int = 2026) -> float:
        """Predicts percentile for a given mark and year."""
        if not self.mark_to_percentile_model:
            return 0.0

        input_data = pd.DataFrame({'mark': [mark], 'year': [year]})
        prediction = self.mark_to_percentile_model.predict(input_data)[0]
        return round(float(prediction), 3)

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
    from data.loader import DataEngine
    data = DataEngine()
    predictor = Predictor(data)

    p = predictor.predict_percentile(195)
    r = predictor.predict_rank(p)
    logger.info(f"Mark: 195 -> Percentile: {p} -> Rank: {r}")
