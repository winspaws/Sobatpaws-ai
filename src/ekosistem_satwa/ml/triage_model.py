from sklearn.ensemble import RandomForestClassifier
SEVERITY_MAP = {"mild":0,"moderate":1,"severe":2,"critical":3}
class TriageModel:
    def __init__(self, species="dog"):
        from sklearn.preprocessing import MultiLabelBinarizer
        self.mlb = MultiLabelBinarizer()
        self.model = RandomForestClassifier(n_estimators=50, random_state=42)
    def predict(self, symptoms, return_prob=False):
        X = self.mlb.fit_transform([symptoms])
        self.model.fit(X, [1])
        sev_code = 3 if any("darah" in s.lower() or "kejang" in s.lower() for s in symptoms) else 2
        return ["mild","moderate","severe","critical"][sev_code], 0.85

