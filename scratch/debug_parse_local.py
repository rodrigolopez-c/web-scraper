import pandas as pd
df = pd.read_csv("datasets/diario_debates_senado_trafilatura.csv")
print(df[['id', 'speaker', 'role', 'date', 'context']])
