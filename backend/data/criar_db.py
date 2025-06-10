import pandas as pd
import sqlite3
import os

# Caminhos
CSV_PATH = './backend/data/dados_covid.csv'
DB_PATH = './backend/data/dados_covid.db'

# Ler o CSV
df = pd.read_csv(CSV_PATH)

# Tratar campos nulos para textos
for col in ['state', 'city']:
    df[col] = df[col].fillna('Desconhecido')

# Tratar campos nulos para numéricos
for col in ['last_available_confirmed', 'last_available_deaths', 'new_confirmed', 'new_deaths']:
    df[col] = df[col].fillna(0).astype(int)

# Tratar datas
df['date'] = pd.to_datetime(df['date'], errors='coerce').dt.strftime('%Y-%m-%d')
df['date'] = df['date'].fillna('1970-01-01')

# Remover banco antigo se existir
if os.path.exists(DB_PATH):
    os.remove(DB_PATH)

# Criar conexão e inserir dados
conn = sqlite3.connect(DB_PATH)
df.to_sql('dados_covid', conn, if_exists='replace', index=False)

# Criar índices para melhorar performance nas consultas
cursor = conn.cursor()
cursor.execute('CREATE INDEX idx_state ON dados_covid(state);')
cursor.execute('CREATE INDEX idx_city ON dados_covid(city);')
cursor.execute('CREATE INDEX idx_date ON dados_covid(date);')

conn.commit()
conn.close()

print('Banco de dados criado com sucesso!')
