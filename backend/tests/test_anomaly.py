import pandas as pd
from sklearn.ensemble import IsolationForest
def test_features(): 
    x=pd.DataFrame({'voltage':[5,6,7,8,9],'current':[.5,.6,.7,.8,.9],'power':[2.5,3.6,4.9,6.4,8.1]})
    assert len(IsolationForest(random_state=42).fit(x).predict([[7,.7,4.9]]))==1
