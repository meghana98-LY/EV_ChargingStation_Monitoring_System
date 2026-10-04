import joblib, pandas as pd
from sklearn.ensemble import IsolationForest
from ..config import TRAINING_DATA,ML_MODEL_PATH,ML_CONTAMINATION
def train():
    if not TRAINING_DATA.exists(): raise FileNotFoundError(TRAINING_DATA)
    df=pd.read_csv(TRAINING_DATA)
    cols=["voltage","current","power"]
    missing=[c for c in cols if c not in df]
    if missing: raise ValueError(f"Missing columns: {missing}")
    X=df[cols].dropna()
    if len(X)<20: raise ValueError("At least 20 training rows are required")
    model=IsolationForest(n_estimators=100,contamination=ML_CONTAMINATION,random_state=42)
    model.fit(X)
    ML_MODEL_PATH.parent.mkdir(parents=True,exist_ok=True)
    joblib.dump(model,ML_MODEL_PATH)
    print(f"Saved model to {ML_MODEL_PATH}")
if __name__=="__main__": train()
