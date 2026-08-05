import pandas as pd

data = {
    "sube_kodu": ["S001", "S002", "S003"],
    "teslim_sayisi": [120, 95, 150]
}

df = pd.DataFrame(data)
print(df)