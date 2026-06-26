from sklearn.ensemble import GradientBoostingRegressor
import numpy as np, datetime
class ForecastModel:
    def __init__(self):
        self.model = GradientBoostingRegressor(n_estimators=50, random_state=42)
    def predict(self, features): return self.model.predict([features])[0]
    def forecast(self, days=30):
        today = datetime.date.today()
        return [{"date":(today+datetime.timedelta(days=d)).isoformat(),"predicted_demand":round(10+(d%7)*2,2)} for d in range(days)]

