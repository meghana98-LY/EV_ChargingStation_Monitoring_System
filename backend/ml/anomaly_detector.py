import joblib, numpy as np
class AnomalyDetector:
    def __init__(self,path):
        self.model=joblib.load(path) if path.exists() else None
    @property
    def available(self): return self.model is not None
    def predict(self,voltage,current,power):
        if self.model is None: raise RuntimeError("Isolation Forest model is missing")
        x=np.array([[voltage,current,power]],dtype=float)
        pred=int(self.model.predict(x)[0])
        score=float(self.model.decision_function(x)[0])
        return {"status":"ANOMALY" if pred==-1 else "NORMAL","is_anomaly":pred==-1,
                "anomaly_score":score}
