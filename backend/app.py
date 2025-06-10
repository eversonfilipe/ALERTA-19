from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import os
import pandas as pd
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Caminho absoluto para o banco de dados
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'dados_covid.db')
# Caminho para o dataset CSV original (usado para atualização)
CSV_PATH = os.path.join(BASE_DIR, 'data', 'dados_covid.csv') # Assumindo que o CSV está em 'data' dentro da pasta do backend

def query_db(query, args=(), one=False):
    """Função auxiliar para executar consultas SQL no banco de dados."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.execute(query, args)
    rv = cur.fetchall()
    conn.close()
    return (rv[0] if rv else None) if one else rv

def process_dataframe_for_db(df):
    """
    Processa o DataFrame do pandas para garantir a compatibilidade com o SQLite.
    Aplica as mesmas lógicas de tratamento de nulos e tipos do criar_db.py.
    """
    for col in ['state', 'city']:
        if col in df.columns:
            df[col] = df[col].fillna('Desconhecido')

    for col in ['last_available_confirmed', 'last_available_deaths', 'new_confirmed', 'new_deaths']:
        if col in df.columns:
            df[col] = df[col].fillna(0).astype(int)

    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'], errors='coerce').dt.strftime('%Y-%m-%d')
        df['date'] = df['date'].fillna('1970-01-01')
    return df

@app.route('/api/login', methods=['POST'])
def login():
    """
    Endpoint para autenticação de usuários.
    Verifica as credenciais fornecidas e retorna o cargo do usuário em caso de sucesso.
    """
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    # Credenciais pré-definidas para fins de teste
    if username == "admin" and password == "admin123":
        return jsonify({"status": "success", "role": "Administrador"})
    elif username == "user" and password == "user123":
        return jsonify({"status": "success", "role": "Civil"})
    else:
        return jsonify({"status": "error", "message": "Credenciais inválidas"}), 401 # 401 Unauthorized

@app.route('/api/estados', methods=['GET'])
def get_estados():
    # Retorna uma lista de estados distintos da base de dados.
    rows = query_db('SELECT DISTINCT state FROM dados_covid ORDER BY state')
    estados = [row['state'] for row in rows]
    return jsonify({"states": estados})

@app.route('/api/municipios', methods=['GET'])
def get_municipios():
    """
    Retorna uma lista de municípios distintos para um dado estado.
    Requer o parâmetro 'estado' na query string.
    """
    estado = request.args.get('estado')
    if not estado:
        return jsonify({"cities": []})

    rows = query_db(
        'SELECT DISTINCT city FROM dados_covid WHERE state = ? ORDER BY city', (estado,)
    )
    municipios = [row['city'] for row in rows]
    return jsonify({"cities": municipios})

@app.route('/api/consulta_dados', methods=['GET'])
def consulta_dados():
    """
    Endpoint para consulta paginada de dados da COVID-19.
    Aceita filtros por data, estado e município.
    """
    data_inicial = request.args.get('data_inicial')
    data_final = request.args.get('data_final')
    estado = request.args.get('estado')
    municipio = request.args.get('municipio')
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 20))

    query = '''
        SELECT
            date,
            state,
            city,
            last_available_confirmed AS confirmed_cases,
            last_available_deaths AS deaths,
            new_confirmed AS new_cases,
            new_deaths AS new_deaths
        FROM dados_covid
        WHERE 1=1
    '''
    params = []

    if data_inicial:
        query += ' AND date >= ?'
        params.append(data_inicial)
    if data_final:
        query += ' AND date <= ?'
        params.append(data_final)
    if estado and estado != "Nenhum estado encontrado":
        query += ' AND state = ?'
        params.append(estado)
    if municipio and municipio != "Nenhum município encontrado":
        query += ' AND city = ?'
        params.append(municipio)

    query += ' ORDER BY date DESC LIMIT ? OFFSET ?'
    params.extend([per_page, (page - 1) * per_page])

    rows = query_db(query, params)

    count_query = '''
        SELECT COUNT(*) as total
        FROM dados_covid
        WHERE 1=1
    '''
    count_params = []
    # Reconstruir count_params com base nos mesmos filtros
    if data_inicial:
        count_query += ' AND date >= ?'
        count_params.append(data_inicial)
    if data_final:
        count_query += ' AND date <= ?'
        count_params.append(data_final)
    if estado and estado != "Nenhum estado encontrado":
        count_query += ' AND state = ?'
        count_params.append(estado)
    if municipio and municipio != "Nenhum município encontrado":
        count_query += ' AND city = ?'
        count_params.append(municipio)


    total = query_db(count_query, count_params, one=True)['total']

    dados = [dict(row) for row in rows]

    return jsonify({
        "data": dados,
        "total_records": total
    })

@app.route('/api/covid_data_for_plot', methods=['GET'])
def covid_data_for_plot():
    """
    Endpoint para obter dados para gráficos dinâmicos.
    Aceita filtros, tipo de gráfico e agregação.
    """
    data_inicial = request.args.get('data_inicial')
    data_final = request.args.get('data_final')
    estado = request.args.get('estado')
    municipio = request.args.get('municipio')
    chart_type = request.args.get('chart_type', 'Casos Diários vs. Óbitos Diários')
    aggregation = request.args.get('aggregation', 'Nenhum') # 'Estado', 'Cidade', 'Nenhum'

    base_query = ""
    params = []

    # Construir a parte WHERE da query
    where_clauses = ["1=1"]
    if data_inicial:
        where_clauses.append('date >= ?')
        params.append(data_inicial)
    if data_final:
        where_clauses.append('date <= ?')
        params.append(data_final)

    # Lógica de agregação e filtros específicos para estado/município
    group_by_clause = "GROUP BY date" # Padrão para gráficos de tempo

    if aggregation == 'Estado':
        group_by_clause += ', state'
        if estado and estado != "Nenhum estado encontrado":
            where_clauses.append('state = ?')
            params.append(estado)
        # Se não houver estado específico, agregará por todos os estados
    elif aggregation == 'Cidade':
        group_by_clause += ', state, city'
        if estado and estado != "Nenhum estado encontrado": # Cidade só faz sentido se um estado for selecionado
            where_clauses.append('state = ?')
            params.append(estado)
        if municipio and municipio != "Nenhum município encontrado":
            where_clauses.append('city = ?')
            params.append(municipio)
        # Se não houver município específico, agregará por todas as cidades no estado (ou nacionalmente)
    else: # aggregation == 'Nenhum' (nacional ou filtro por um único local)
        if estado and estado != "Nenhum estado encontrado":
            where_clauses.append('state = ?')
            params.append(estado)
        if municipio and municipio != "Nenhum município encontrado":
            where_clauses.append('city = ?')
            params.append(municipio)

    where_sql = " AND ".join(where_clauses)

    # Seleção de colunas baseada no tipo de gráfico
    if chart_type == 'Casos Diários vs. Óbitos Diários':
        select_cols = 'date, SUM(new_confirmed) as cases, SUM(new_deaths) as deaths'
    elif chart_type == 'Casos Acumulados vs. Óbitos Acumulados':
        select_cols = 'date, SUM(last_available_confirmed) as cases, SUM(last_available_deaths) as deaths'
    else:
        # Default para Casos Diários
        select_cols = 'date, SUM(new_confirmed) as cases, SUM(new_deaths) as deaths'

    # Adiciona colunas de agregação se aplicável
    if aggregation == 'Estado':
        select_cols += ', state'
    elif aggregation == 'Cidade':
        select_cols += ', state, city'


    query = f"SELECT {select_cols} FROM dados_covid WHERE {where_sql} {group_by_clause} ORDER BY date ASC"

    rows = query_db(query, params)

    # Formatar a resposta para o frontend
    response_data = {
        "dates": [],
        "cases": [],
        "deaths": [],
        "labels": [] # Para agregação, para identificar as séries
    }

    if aggregation == 'Nenhum' or (aggregation == 'Estado' and estado) or (aggregation == 'Cidade' and municipio):
        # Um único conjunto de séries de dados
        response_data["dates"] = [row['date'] for row in rows]
        response_data["cases"] = [row['cases'] for row in rows]
        response_data["deaths"] = [row['deaths'] for row in rows]
    else:
        # Múltiplas séries de dados (por estado ou cidade)
        # Reestruturar dados para facilitar o plot de múltiplas linhas
        # Ex: {"2020-03-01": {"SP": {"cases": 10, "deaths": 0}, "RJ": {"cases": 5, "deaths": 0}}}
        grouped_data = {}
        for row in rows:
            date = row['date']
            label = ""
            if aggregation == 'Estado':
                label = row['state']
            elif aggregation == 'Cidade':
                label = f"{row['city']} ({row['state']})" # Include state for city label
            
            if date not in grouped_data:
                grouped_data[date] = {}
            if label not in grouped_data[date]:
                grouped_data[date][label] = {"cases": 0, "deaths": 0}
            
            grouped_data[date][label]["cases"] = row['cases']
            grouped_data[date][label]["deaths"] = row['deaths']

        # Preencher os dados para o gráfico
        all_dates = sorted(list(grouped_data.keys()))
        all_labels = sorted(list(set(label for date_data in grouped_data.values() for label in date_data.keys())))

        response_data["dates"] = all_dates
        response_data["labels"] = all_labels
        
        # Inicializar listas para cada label
        for label in all_labels:
            response_data[f"cases_{label}"] = []
            response_data[f"deaths_{label}"] = []

        for date in all_dates:
            for label in all_labels:
                data_point = grouped_data.get(date, {}).get(label, {"cases": None, "deaths": None})
                response_data[f"cases_{label}"].append(data_point["cases"])
                response_data[f"deaths_{label}"].append(data_point["deaths"])
        
    return jsonify(response_data)


@app.route('/api/importar_dataset', methods=['POST'])
def importar_dataset():
    """
    Importa um novo dataset a partir de um caminho de arquivo CSV/CSV.GZ.
    Substitui os dados existentes na tabela 'dados_covid'.
    """
    data = request.get_json()
    file_path = data.get('file_path')

    if not file_path:
        return jsonify({'status': 'error', 'message': 'Caminho do arquivo não fornecido.'}), 400

    if not os.path.exists(file_path):
        return jsonify({'status': 'error', 'message': f'Arquivo não encontrado: {file_path}'}), 404

    try:
        if file_path.endswith('.csv.gz'):
            df = pd.read_csv(file_path, compression='gzip')
        elif file_path.endswith('.csv'):
            df = pd.read_csv(file_path)
        else:
            return jsonify({'status': 'error', 'message': 'Formato de arquivo não suportado. Use .csv ou .csv.gz.'}), 400

        df = process_dataframe_for_db(df)

        conn = sqlite3.connect(DB_PATH)
        df.to_sql('dados_covid', conn, if_exists='replace', index=False)

        # Recriar índices para performance
        cursor = conn.cursor()
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_state ON dados_covid(state);')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_city ON dados_covid(city);')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_date ON dados_covid(date);')
        conn.commit()
        conn.close()

        return jsonify({'status': 'success', 'message': f'Dataset importado com sucesso de {file_path}.'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Erro ao processar e importar dataset: {str(e)}'}), 500

@app.route('/api/atualizar_dados', methods=['PUT'])
def atualizar_dados():
    """
    Atualiza os dados existentes na base de dados.
    Para este MVP, simula a re-importação do dataset original ou de uma fonte definida.
    """
    # Para simplicidade e seguindo a sugestão do prompt, vamos re-processar o CSV_PATH
    # em um cenário real, isso poderia envolver baixar um CSV mais recente de brasil.io
    # ou de outra fonte.
    try:
        # Supondo que CSV_PATH aponta para a fonte "original" que deve ser re-importada
        if not os.path.exists(CSV_PATH):
            return jsonify({'status': 'error', 'message': f'Dataset original para atualização não encontrado em {CSV_PATH}.'}), 404

        if CSV_PATH.endswith('.csv.gz'):
            df = pd.read_csv(CSV_PATH, compression='gzip')
        elif CSV_PATH.endswith('.csv'):
            df = pd.read_csv(CSV_PATH)
        else:
            return jsonify({'status': 'error', 'message': 'Formato de arquivo original para atualização não suportado. Use .csv ou .csv.gz.'}), 400

        df = process_dataframe_for_db(df)

        conn = sqlite3.connect(DB_PATH)
        # Estratégia: Substituir se existir, ou adicionar (via replace)
        df.to_sql('dados_covid', conn, if_exists='replace', index=False)

        # Recriar índices para performance
        cursor = conn.cursor()
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_state ON dados_covid(state);')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_city ON dados_covid(city);')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_date ON dados_covid(date);')
        conn.commit()
        conn.close()

        return jsonify({'status': 'success', 'message': 'Dados atualizados com sucesso.'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Erro ao atualizar dados: {str(e)}'}), 500

@app.route('/api/limpar_base', methods=['DELETE'])
def limpar_base():
    """Limpa todos os registros da tabela 'dados_covid'."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM dados_covid')
        conn.commit()
        conn.close()
        return jsonify({'status': 'success', 'message': 'Base de dados limpa com sucesso.'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)