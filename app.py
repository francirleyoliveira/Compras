import streamlit as st
import pandas as pd
import oracledb
import os
import time
import re
import requests  # NOVA IMPORTAÇÃO PARA API DO GOOGLE
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from io import BytesIO

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="Gestão de Compras & Imagens",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 1. SETUP E ESTADO DA SESSÃO ---
load_dotenv()

# Cache para armazenar resultados da busca (lista de imagens)
if 'search_results' not in st.session_state:
    st.session_state.search_results = {}

try:
    lib_dir = os.getenv("ORACLE_CLIENT_PATH")
    if lib_dir and not os.path.exists(lib_dir):
        st.warning(f"Aviso: Diretório do Oracle Client não encontrado em {lib_dir}")
    else:
        oracledb.init_oracle_client(lib_dir=lib_dir)
except Exception as e:
    if "already initialized" not in str(e):
        st.error(f"Erro Client Oracle: {e}")

# --- 2. CONEXÃO E DADOS ---
def get_db_engine():
    user = os.getenv("DB_USER")
    password = os.getenv("DB_PASSWORD")
    host = os.getenv("DB_HOST")
    port = os.getenv("DB_PORT")
    service = os.getenv("DB_SERVICE")
    connection_string = f"oracle+oracledb://{user}:{password}@{host}:{port}/?service_name={service}"
    return create_engine(connection_string)

@st.cache_data(ttl=300)
def fetch_product_data():
    """Busca dados do Oracle."""
    query = """
    WITH EmbalagemPrincipal AS (
        SELECT CODPROD, EMBALAGEM, CODAUXILIAR, 
               ROW_NUMBER() OVER (PARTITION BY CODPROD ORDER BY QTUNIT ASC, EMBALAGEM ASC) as rn
        FROM PCEMBALAGEM
    ),
    ProdutosAtivos AS (
        SELECT DISTINCT CODPROD FROM PCEST
        WHERE CODFILIAL IN (1, 2, 3) AND DTULTSAIDA >= TRUNC(SYSDATE) - 300
    )
    SELECT
        P.CODPROD, P.DESCRICAO, EP.CODAUXILIAR AS EAN, EP.EMBALAGEM,
        E.CODFILIAL, E.QTEST, E.DTULTSAIDA, P.DIRFOTOPROD, P.DTEXCLUSAO,
        F.FORNECEDOR, D.DESCRICAO AS DEPARTAMENTO, S.DESCRICAO AS SECAO,
        CASE WHEN P.OBS2 = 'FL' THEN 'Fora de Linha' ELSE 'Ativo' END AS STATUS,
        TRUNC(SYSDATE - E.DTULTSAIDA) AS DIAS_SEM_VENDA
    FROM PCPRODUT P
    INNER JOIN ProdutosAtivos PA ON P.CODPROD = PA.CODPROD
    INNER JOIN PCEST E ON P.CODPROD = E.CODPROD
    LEFT JOIN EmbalagemPrincipal EP ON P.CODPROD = EP.CODPROD AND EP.rn = 1
    LEFT JOIN PCFORNEC F ON P.CODFORNEC = F.CODFORNEC
    LEFT JOIN PCDEPTO D ON P.CODEPTO = D.CODEPTO
    LEFT JOIN PCSECAO S ON P.CODSEC = S.CODSEC
    WHERE E.CODFILIAL IN (1, 2, 3)
    ORDER BY P.CODPROD
    """
    engine = get_db_engine()
    try:
        with engine.connect() as connection:
            df = pd.read_sql(text(query), connection)
            df.columns = df.columns.str.upper()
            return df
    except Exception as e:
        st.error(f"Erro SQL: {e}")
        return pd.DataFrame()

# --- 3. BUSCA GOOGLE IMAGENS (API OFICIAL) ---

def clean_text(text):
    """Limpa descrição para busca."""
    if not text: return ""
    text = re.sub(r'\b(UN|CX|KG|LT|ML|PCT|FD|FARDO|LATA|VD|VIDRO)\b', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\b[C|X]/\d+\b', '', text) 
    text = re.sub(r'\b\d+[X|C]\d*\b', '', text)
    text = re.sub(r'[^\w\s]', '', text)
    return " ".join(text.split())

def google_image_search_api(query, num_results=4):
    """
    Consulta a API Custom Search do Google.
    Retorna uma lista de dicionários com 'link' e 'thumbnail'.
    """
    api_key = os.getenv("GOOGLE_API_KEY")
    cse_id = os.getenv("GOOGLE_CSE_ID")
    
    if not api_key or not cse_id:
        st.error("⚠️ Configuração da API do Google ausente no .env")
        return []

    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        'q': query,
        'cx': cse_id,
        'key': api_key,
        'searchType': 'image',
        'num': num_results,
        'fileType': 'jpg,png,jpeg',
        'gl': 'br', # Região Brasil
        'hl': 'pt'  # Idioma Português
    }
    
    try:
        response = requests.get(url, params=params)
        data = response.json()
        
        if 'items' in data:
            return data['items'] # Retorna lista de resultados
        else:
            return []
    except Exception as e:
        print(f"Erro na API Google: {e}")
        return []

def perform_search(ean, description):
    """Gerencia a estratégia de busca e cache."""
    key = str(ean) if pd.notna(ean) else description
    
    # Se já temos resultados em memória, retorna-os
    if key in st.session_state.search_results:
        return st.session_state.search_results[key]

    ean_clean = str(ean).replace('.0', '').strip() if pd.notna(ean) else ""
    desc_clean = clean_text(description)
    
    # Prioriza EAN
    query = f'"{ean_clean}"' if ean_clean and len(ean_clean) > 6 else f'{desc_clean} embalagem'
    
    # Busca no Google (Pega top 4 imagens)
    results = google_image_search_api(query, num_results=4)
    
    # Salva no cache da sessão
    st.session_state.search_results[key] = results
    return results

# --- 4. MODAL DE DETALHES ---
@st.dialog("Detalhes do Produto", width="large")
def show_product_modal(row):
    # Layout Principal
    st.header(f"{row['DESCRICAO']}")
    
    # Dados Cadastrais no Topo (Compacto)
    c_info1, c_info2, c_info3 = st.columns(3)
    c_info1.write(f"**Cód:** {row['CODPROD']}")
    ean_show = str(row.get('EAN')).replace('.0', '') if pd.notna(row.get('EAN')) else '-'
    c_info2.write(f"**EAN:** {ean_show}")
    c_info3.write(f"**Fornecedor:** {row.get('FORNECEDOR', '-')}")

    st.divider()

    c1, c2 = st.columns([1, 1])
    
    # --- COLUNA 1: IMAGEM LOCAL ---
    with c1:
        st.subheader("📂 Imagem do WinThor")
        dir_foto = row.get('DIRFOTOPROD')
        
        if dir_foto and os.path.exists(dir_foto):
            try:
                st.image(dir_foto, caption="Imagem Atual no Sistema", width=300)
                st.success(f"Caminho: {dir_foto}")
            except:
                st.error("Arquivo corrompido.")
        else:
            st.info("Nenhuma imagem cadastrada localmente.")

    # --- COLUNA 2: BUSCA GOOGLE (GALERIA) ---
    with c2:
        st.subheader("🌐 Busca Google (Sugestões)")
        
        ean_val = row.get('EAN')
        desc = row.get('DESCRICAO')
        key = str(ean_val) if pd.notna(ean_val) else desc

        # Botão para iniciar busca (para economizar cotas da API)
        if key not in st.session_state.search_results:
            if st.button("🔍 Buscar Imagens na Web", key=f"btn_{row['CODPROD']}"):
                with st.spinner("Consultando Google Imagens..."):
                    perform_search(ean_val, desc)
                    st.rerun()
        
        # Exibição dos Resultados
        results = st.session_state.search_results.get(key, [])
        
        if results:
            st.write("Resultados encontrados (Selecione visualmente):")
            
            # Grid de imagens (2 por linha)
            cols = st.columns(2)
            for i, item in enumerate(results):
                with cols[i % 2]:
                    try:
                        st.image(item['link'], caption=f"Opção {i+1}", use_container_width=True)
                        # Aqui futuramente podes adicionar um botão "Salvar Esta"
                    except:
                        pass
        elif key in st.session_state.search_results:
            st.warning("Nenhuma imagem encontrada no Google.")

# --- 5. INTERFACE PRINCIPAL ---
st.title("🛒 Painel de Compras Inteligente")

if st.button("🔄 Atualizar Base de Dados"):
    fetch_product_data.clear()
    st.session_state.search_results = {} # Limpa cache de imagens
    st.rerun()

df = fetch_product_data()

if not df.empty:
    with st.sidebar:
        st.header("🔍 Filtros Avançados")
        f_cod = st.text_input("Código")
        f_ean = st.text_input("EAN")
        f_desc = st.text_input("Descrição (Contém)")
        col_f1, col_f2 = st.columns(2)
        f_filial = col_f1.multiselect("Filial", options=df['CODFILIAL'].unique())
        f_status = col_f2.multiselect("Status", options=df['STATUS'].unique())
        f_depto = st.multiselect("Departamento", options=df['DEPARTAMENTO'].dropna().unique())
        max_dias = int(df['DIAS_SEM_VENDA'].max()) if not df['DIAS_SEM_VENDA'].isnull().all() else 300
        f_dias = st.slider("Dias sem Venda (Mínimo)", 0, max_dias, 0)
        
        st.markdown("---")
        opcao_foto = st.radio("Status da Foto:", ["Todos", "Com Foto", "Sem Foto"], index=0)
        opcao_exclusao = st.radio("Visualizar:", ["Todos", "Apenas Ativos", "Apenas Excluídos"], index=0)

    # Aplicação dos Filtros
    df_filtered = df.copy()
    if f_cod: df_filtered = df_filtered[df_filtered['CODPROD'].astype(str) == f_cod]
    if f_ean: df_filtered = df_filtered[df_filtered['EAN'].astype(str).str.contains(f_ean, na=False)]
    if f_desc: df_filtered = df_filtered[df_filtered['DESCRICAO'].str.contains(f_desc, case=False, na=False)]
    if f_filial: df_filtered = df_filtered[df_filtered['CODFILIAL'].isin(f_filial)]
    if f_status: df_filtered = df_filtered[df_filtered['STATUS'].isin(f_status)]
    if f_depto: df_filtered = df_filtered[df_filtered['DEPARTAMENTO'].isin(f_depto)]
    df_filtered = df_filtered[df_filtered['DIAS_SEM_VENDA'] >= f_dias]

    if opcao_foto == "Com Foto":
        df_filtered = df_filtered[df_filtered['DIRFOTOPROD'].notna() & (df_filtered['DIRFOTOPROD'] != '')]
    elif opcao_foto == "Sem Foto":
        df_filtered = df_filtered[df_filtered['DIRFOTOPROD'].isna() | (df_filtered['DIRFOTOPROD'] == '')]

    if opcao_exclusao == "Apenas Ativos":
        df_filtered = df_filtered[df_filtered['DTEXCLUSAO'].isna()]
    elif opcao_exclusao == "Apenas Excluídos":
        df_filtered = df_filtered[df_filtered['DTEXCLUSAO'].notna()]

    # Métricas
    m1, m2 = st.columns(2)
    m1.metric("Produtos", len(df_filtered))
    m2.metric("Estoque", f"{df_filtered['QTEST'].sum():,.0f}")

    # Tabela
    st.subheader("📋 Tabela de Produtos")
    event = st.dataframe(
        df_filtered,
        use_container_width=True,
        hide_index=True,
        column_order=["CODFILIAL", "CODPROD", "DESCRICAO", "EAN", "ESTOQUE", "DIAS_SEM_VENDA", "DTEXCLUSAO", "DIRFOTOPROD"],
        column_config={
            "CODFILIAL": st.column_config.TextColumn("Filial", width="small"),
            "CODPROD": "Cód.",
            "DIAS_SEM_VENDA": st.column_config.NumberColumn("Dias s/ Venda", format="%d"),
            "ESTOQUE": st.column_config.NumberColumn("Estoque", format="%.0f"),
            "DTEXCLUSAO": st.column_config.DateColumn("Exclusão", format="DD/MM/YYYY"),
            "DIRFOTOPROD": st.column_config.TextColumn("Dir. Foto", width="small"),
        },
        on_select="rerun",
        selection_mode="single-row"
    )

    if len(event.selection['rows']) > 0:
        idx = event.selection['rows'][0]
        show_product_modal(df_filtered.iloc[idx])

    # Exportação
    st.markdown("---")
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_filtered.to_excel(writer, index=False, sheet_name='Analise')
    st.download_button("📥 Excel", output.getvalue(), "relatorio.xlsx")

else:
    st.info("Nenhum dado carregado.")