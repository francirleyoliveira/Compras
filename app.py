import streamlit as st
import pandas as pd
import oracledb
import os
import time
import sys
import re
import requests
import logging
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from io import BytesIO
from datetime import datetime
from PIL import Image

# --- CONFIGURAÇÃO DE LOGS ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="Gestão de Compras & Imagens",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 1. SETUP E ESTADO DA SESSÃO ---
load_dotenv()

# Inicializa estados da sessão
if 'search_results' not in st.session_state:
    st.session_state.search_results = {}

if 'api_quota' not in st.session_state:
    st.session_state.api_quota = {
        'count': 0, 
        'reset_time': time.time() + 3600,
        'history': []
    }

if 'last_saved_image' not in st.session_state:
    st.session_state.last_saved_image = None

# Inicialização do Oracle Client
try:
    lib_dir = os.getenv("ORACLE_CLIENT_PATH")
    if lib_dir and not os.path.exists(lib_dir):
        st.warning(f"⚠️ Diretório do Oracle Client não encontrado em {lib_dir}")
    else:
        oracledb.init_oracle_client(lib_dir=lib_dir)
        logger.info("Oracle Client inicializado com sucesso")
except Exception as e:
    if "already initialized" not in str(e):
        st.error(f"❌ Erro Client Oracle: {e}")
        logger.error(f"Erro Oracle Client: {e}")

# --- 2. CONEXÃO E DADOS ---
def get_db_engine():
    """Cria engine de conexão com Oracle"""
    user = os.getenv("DB_USER")
    password = os.getenv("DB_PASSWORD")
    host = os.getenv("DB_HOST")
    port = os.getenv("DB_PORT")
    service = os.getenv("DB_SERVICE")
    connection_string = f"oracle+oracledb://{user}:{password}@{host}:{port}/?service_name={service}"
    return create_engine(connection_string)
# ============================================
# FUNÇÕES AUXILIARES PARA MÚLTIPLOS EANs
# ============================================

def parse_eans(todos_eans_str):
    """
    Converte string de EANs concatenados em lista.
    
    Args:
        todos_eans_str: String tipo "123456|789012|345678"
    
    Returns:
        Lista de EANs válidos: ['123456', '789012', '345678']
    """
    if pd.isna(todos_eans_str) or not todos_eans_str:
        return []
    
    # Remove espaços e divide pelo separador
    eans = [ean.strip() for ean in str(todos_eans_str).split('|')]
    
    # Filtra EANs válidos (mínimo 8 dígitos)
    eans_validos = [ean for ean in eans if len(ean) >= 8]
    
    return eans_validos


def has_ean(todos_eans_str, busca):
    """
    Verifica se um EAN está presente na lista de EANs do produto.
    
    Args:
        todos_eans_str: String tipo "123456|789012|345678"
        busca: EAN a buscar (string)
    
    Returns:
        True se encontrou, False caso contrário
    """
    if not busca or pd.isna(todos_eans_str):
        return False
    
    busca = str(busca).strip()
    eans = parse_eans(todos_eans_str)
    
    # Busca exata ou parcial
    return any(busca in ean for ean in eans)


def get_primary_ean(row):
    """
    Retorna o EAN principal do produto.
    Prioriza a coluna EAN, senão pega o primeiro de TODOS_EANS.
    """
    # Tenta usar EAN principal
    if pd.notna(row.get('EAN')):
        ean_str = str(row['EAN']).replace('.0', '').strip()
        if len(ean_str) >= 8:
            return ean_str
    
    # Fallback: primeiro EAN da lista
    eans = parse_eans(row.get('TODOS_EANS'))
    return eans[0] if eans else None


# ============================================
# ATUALIZAÇÃO DO FETCH_PRODUCT_DATA
# ============================================

@st.cache_data(ttl=300)
def fetch_product_data():
    """Busca dados do Oracle COM suporte a múltiplos EANs e cache de 5 minutos"""
    query = """
    WITH EmbalagemPrincipal AS (
        SELECT 
            CODPROD, 
            EMBALAGEM, 
            CODAUXILIAR AS EAN_PRINCIPAL, 
            ROW_NUMBER() OVER (
                PARTITION BY CODPROD 
                ORDER BY QTUNIT ASC, EMBALAGEM ASC
            ) as rn
        FROM PCEMBALAGEM
        WHERE DTINATIVO IS NULL
    ),
    TodosEans AS (
        SELECT DISTINCT 
            CODPROD,
            CODAUXILIAR
        FROM PCEMBALAGEM
        WHERE DTINATIVO IS NULL
          AND CODAUXILIAR IS NOT NULL
          AND LENGTH(TRIM(CODAUXILIAR)) >= 8
    ),
    EansAgregados AS (
        SELECT 
            CODPROD,
            LISTAGG(CODAUXILIAR, '|') 
                WITHIN GROUP (ORDER BY CODAUXILIAR) AS TODOS_EANS,
            COUNT(*) AS QTD_EANS
        FROM TodosEans
        GROUP BY CODPROD
    ),
    ProdutosAtivos AS (
        SELECT DISTINCT CODPROD 
        FROM PCEST
        WHERE CODFILIAL IN (1, 2, 3) 
    )
    SELECT
        P.CODPROD, 
        P.DESCRICAO, 
        EP.EAN_PRINCIPAL AS EAN, 
        EP.EMBALAGEM,
        EA.TODOS_EANS,
        EA.QTD_EANS,
        E.CODFILIAL, 
        E.QTEST, 
        E.DTULTSAIDA, 
        P.DIRFOTOPROD, 
        P.DTEXCLUSAO,
        F.FORNECEDOR, 
        D.DESCRICAO AS DEPARTAMENTO, 
        S.DESCRICAO AS SECAO,
        CASE 
            WHEN P.OBS2 = 'FL' THEN 'Fora de Linha' 
            ELSE 'Ativo' 
        END AS STATUS,
        TRUNC(SYSDATE - E.DTULTSAIDA) AS DIAS_SEM_VENDA
    FROM PCPRODUT P
    INNER JOIN ProdutosAtivos PA ON P.CODPROD = PA.CODPROD
    INNER JOIN PCEST E ON P.CODPROD = E.CODPROD
    LEFT JOIN EmbalagemPrincipal EP ON P.CODPROD = EP.CODPROD AND EP.rn = 1
    LEFT JOIN EansAgregados EA ON P.CODPROD = EA.CODPROD
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
            
            # Log de estatísticas
            produtos_com_multiplos_eans = len(df[df['QTD_EANS'] > 1])
            logger.info(f"Dados carregados: {len(df)} produtos")
            logger.info(f"Produtos com múltiplos EANs: {produtos_com_multiplos_eans}")
            
            return df
    except Exception as e:
        st.error(f"❌ Erro ao buscar dados: {e}")
        logger.error(f"Erro SQL: {e}")
        return pd.DataFrame()
# --- 3. CONTROLE DE COTAS DA API ---
def check_quota():
    """Limita a 100 buscas por hora (limite gratuito do Google)"""
    now = time.time()
    
    # Reset do contador após 1 hora
    if now > st.session_state.api_quota['reset_time']:
        st.session_state.api_quota = {
            'count': 0, 
            'reset_time': now + 3600,
            'history': []
        }
        logger.info("Quota de API resetada")
    
    # Verifica limite
    if st.session_state.api_quota['count'] >= 100:
        tempo_restante = int((st.session_state.api_quota['reset_time'] - now) / 60)
        st.warning(f"⚠️ Limite de 100 buscas/hora atingido. Aguarde {tempo_restante} minutos.")
        return False
    
    st.session_state.api_quota['count'] += 1
    return True

# --- 4. LIMPEZA DE TEXTO OTIMIZADA ---
def clean_text(text):
    """Limpa descrição para busca (versão otimizada)"""
    if not text: 
        return ""
    
    # Remove unidades de medida comuns
    unidades = r'\b(UN|UND|UNID|CX|CAIXA|KG|KILO|QUILO|LT|LITRO|ML|PCT|PACOTE|FD|FARDO|LATA|VD|VIDRO|GR|GRAMA|MG)\b'
    text = re.sub(unidades, '', text, flags=re.IGNORECASE)
    
    # Remove padrões tipo "12X500ML" ou "C/24"
    text = re.sub(r'\b\d+[X|x|C|c|/]\d*\w*\b', '', text)
    
    # Remove números com unidades no final (ex: "500ML", "2L")
    text = re.sub(r'\b\d+\s*(ML|L|G|KG|MG)\b', '', text, flags=re.IGNORECASE)
    
    # Remove caracteres especiais mas mantém acentos
    text = re.sub(r'[^\w\sÀ-ÿ]', ' ', text)
    
    # Remove espaços duplicados
    return " ".join(text.split()).strip()

# --- 5. BUSCA GOOGLE IMAGENS (COM TRATAMENTO DE ERROS) ---
def google_image_search_api(query, num_results=4):
    """
    Consulta a API Custom Search do Google com tratamento completo de erros.
    Retorna uma lista de dicionários com 'link' e 'thumbnail'.
    """
    api_key = os.getenv("GOOGLE_API_KEY")
    cse_id = os.getenv("GOOGLE_CSE_ID")
    
    if not api_key or not cse_id:
        st.error("⚠️ Configuração da API do Google ausente no .env")
        logger.error("API Key ou CSE ID não encontrados")
        return []

    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        'q': query,
        'cx': cse_id,
        'key': api_key,
        'searchType': 'image',
        'num': num_results,
        'fileType': 'jpg,png,jpeg',
        'gl': 'br',
        'hl': 'pt',
        'safe': 'active'
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()  # ✅ Verifica status HTTP
        
        data = response.json()
        
        if 'items' in data:
            logger.info(f"Busca bem-sucedida: {len(data['items'])} imagens para '{query}'")
            return data['items']
        elif 'error' in data:
            error_msg = data['error'].get('message', 'Erro desconhecido')
            st.error(f"❌ Erro da API: {error_msg}")
            logger.error(f"Erro API Google: {error_msg}")
            return []
        else:
            logger.warning(f"Nenhuma imagem encontrada para: {query}")
            return []
            
    except requests.exceptions.Timeout:
        st.warning("⏱️ Tempo limite esgotado. Tente novamente.")
        logger.warning(f"Timeout na busca: {query}")
        return []
    except requests.exceptions.HTTPError as e:
        st.error(f"❌ Erro HTTP {e.response.status_code}: {e.response.text}")
        logger.error(f"HTTP Error: {e}")
        return []
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Erro de conexão: {str(e)}")
        logger.error(f"Request Error: {e}")
        return []
    except Exception as e:
        st.error(f"❌ Erro inesperado: {e}")
        logger.error(f"Unexpected error: {e}")
        return []

# ============================================
# ATUALIZAÇÃO DA FUNÇÃO perform_search
# ============================================

def perform_search(ean, description, cache_key=None):
    """
    Gerencia busca com cache usando chave personalizada.
    
    Args:
        ean: EAN selecionado pelo usuário
        description: Descrição do produto
        cache_key: Chave única para cache (produto + EAN)
    """
    # Se não forneceu cache_key, usa lógica antiga
    if not cache_key:
        cache_key = str(ean) if pd.notna(ean) else description
    
    # Verifica cache
    if cache_key in st.session_state.search_results:
        logger.info(f"Usando cache para: {cache_key}")
        return st.session_state.search_results[cache_key]

    # Verifica quota
    if not check_quota():
        return []

    ean_clean = str(ean).replace('.0', '').strip() if pd.notna(ean) else ""
    desc_clean = clean_text(description)
    
    # Prioriza EAN
    if ean_clean and len(ean_clean) >= 8:
        query = f'"{ean_clean}" produto'
    else:
        query = f'{desc_clean} embalagem produto'
    
    logger.info(f"Buscando com cache_key={cache_key}, query={query}")
    
    # Busca no Google
    results = google_image_search_api(query, num_results=4)
    
    # Salva no cache com a chave correta
    st.session_state.search_results[cache_key] = results
    st.session_state.api_quota['history'].append({
        'timestamp': datetime.now(),
        'query': query,
        'results': len(results),
        'cache_key': cache_key
    })
    
    return results

# --- 6. CONVERSÃO DE TIPOS NUMPY ---
def convert_to_python_type(value):
    """
    Converte tipos numpy para tipos Python nativos.
    Necessário para compatibilidade com Oracle/SQLAlchemy.
    """
    import numpy as np
    
    if isinstance(value, (np.integer, np.int64, np.int32)):
        return int(value)
    elif isinstance(value, (np.floating, np.float64, np.float32)):
        return float(value)
    elif isinstance(value, np.bool_):
        return bool(value)
    elif isinstance(value, np.ndarray):
        return value.tolist()
    elif pd.isna(value):
        return None
    else:
        return value

# --- 7. SALVAR IMAGEM NO SISTEMA ---
def save_image_to_winthor(codprod, image_url):
    """
    Baixa imagem da URL e salva no diretório do WinThor.
    Atualiza o campo DIRFOTOPROD no Oracle.
    """
    try:
        # Converter para tipo Python nativo (resolve problema com numpy.int64)
        codprod = convert_to_python_type(codprod)
        
        logger.info(f"Iniciando salvamento de imagem para produto {codprod}")
        
        # Baixar imagem
        response = requests.get(image_url, timeout=15, stream=True)
        response.raise_for_status()
        
        # Validar se é uma imagem válida
        try:
            img = Image.open(BytesIO(response.content))
            img.verify()
            logger.info(f"Imagem validada: {img.format} {img.size}")
        except Exception as e:
            st.error("❌ Arquivo baixado não é uma imagem válida")
            logger.error(f"Validação de imagem falhou: {e}")
            return False
        
        # Definir caminho (AJUSTAR CONFORME SEU AMBIENTE)
        img_dir = os.getenv("WINTHOR_IMAGE_DIR", "fotos_produtos")
        
        # Criar diretório se não existir
        os.makedirs(img_dir, exist_ok=True)
        
        filename = f"{codprod}.png"
        filepath = os.path.join(img_dir, filename)
        
        # Salvar arquivo localmente convertendo para PNG
        image_data = BytesIO(response.content)
        with Image.open(image_data) as img_save:
            img_save.save(filepath, format="PNG")
        
        logger.info(f"Imagem salva em: {filepath}")
        
        # Atualizar banco Oracle
        engine = get_db_engine()
        with engine.connect() as conn:
            query = text("""
                UPDATE PCPRODUT 
                SET DIRFOTOPROD = :filepath 
                WHERE CODPROD = :codprod
            """)
            # Garante tipos Python nativos
            params = {
                'filepath': str(filepath), 
                'codprod': int(codprod)
            }
            logger.info(f"Executando UPDATE com params: {params}")
            
            result = conn.execute(query, params)
            conn.commit()
            
            logger.info(f"Linhas afetadas: {result.rowcount}")
        
        logger.info(f"Banco atualizado para produto {codprod}")
        
        # Limpar cache para forçar reload
        fetch_product_data.clear()
        
        return True
        
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Erro ao baixar imagem: {e}")
        logger.error(f"Download error: {e}")
        return False
    except Exception as e:
        st.error(f"❌ Erro ao salvar: {e}")
        logger.error(f"Save error: {e}", exc_info=True)
        return False

# --- 7. MODAL DE DETALHES (COM SALVAMENTO) ---
# ============================================
# ATUALIZAÇÃO DO MODAL - SELETOR DE EANs
# ============================================

@st.dialog("Detalhes do Produto", width="large")
def show_product_modal(row):
    # Converter valores para tipos Python nativos
    codprod = convert_to_python_type(row['CODPROD'])
    
    # NOVO: Obter lista de todos os EANs
    todos_eans = parse_eans(row.get('TODOS_EANS'))
    ean_principal = get_primary_ean(row)
    qtd_eans = convert_to_python_type(row.get('QTD_EANS', 1))
    
    # Cabeçalho
    st.header(f"📦 {row['DESCRICAO']}")
    
    # Dados Cadastrais Compactos
    col_info1, col_info2, col_info3, col_info4 = st.columns(4)
    col_info1.metric("Código", codprod)
    col_info2.metric("EAN Principal", ean_principal or '-')
    col_info3.metric("Filial", convert_to_python_type(row['CODFILIAL']))
    col_info4.metric("Estoque", f"{convert_to_python_type(row.get('QTEST', 0)):,.0f}")
    
    # NOVO: Exibir múltiplos EANs se existirem
    if qtd_eans > 1:
        st.info(f"ℹ️ Este produto possui **{qtd_eans} códigos de barras** cadastrados")
        with st.expander("📊 Ver todos os EANs", expanded=False):
            for i, ean in enumerate(todos_eans, 1):
                badge = "🏆 Principal" if ean == ean_principal else ""
                st.code(f"{i}. {ean}  {badge}")
    
    col_info5, col_info6, col_info7 = st.columns(3)
    col_info5.write(f"**Fornecedor:** {row.get('FORNECEDOR', '-')}")
    col_info6.write(f"**Departamento:** {row.get('DEPARTAMENTO', '-')}")
    col_info7.write(f"**Status:** {row.get('STATUS', '-')}")

    st.divider()

    c1, c2 = st.columns([1, 1])
    
    # --- COLUNA 1: IMAGEM LOCAL ---
    with c1:
        st.subheader("📂 Imagem Cadastrada (WinThor)")
        dir_foto = row.get('DIRFOTOPROD')
        
        if dir_foto and os.path.exists(dir_foto):
            try:
                st.image(dir_foto, caption="Imagem Atual no Sistema", use_container_width=True)
                st.success(f"✅ Caminho: `{dir_foto}`")
            except Exception as e:
                st.error(f"❌ Arquivo corrompido ou inacessível: {e}")
        else:
            st.info("ℹ️ Nenhuma imagem cadastrada localmente.")
            if dir_foto:
                st.caption(f"Caminho registrado: `{dir_foto}` (não encontrado)")

    # --- COLUNA 2: BUSCA GOOGLE COM SELETOR DE EAN ---
    with c2:
        st.subheader("🌐 Busca Google (Sugestões)")
        
        # NOVO: Seletor de EAN para busca
        if todos_eans and len(todos_eans) > 1:
            st.write("**Selecione o código de barras para buscar:**")
            
            # Tenta usar st.pills (Streamlit 1.31+)
            if hasattr(st, 'pills'):
                ean_selecionado = st.pills(
                    "EAN para busca:",
                    options=todos_eans,
                    default=ean_principal,
                    label_visibility="collapsed"
                )
            else:
                # Fallback para selectbox
                ean_selecionado = st.selectbox(
                    "EAN para busca:",
                    options=todos_eans,
                    index=todos_eans.index(ean_principal) if ean_principal in todos_eans else 0,
                    label_visibility="collapsed"
                )
        else:
            # Apenas um EAN, usa o principal
            ean_selecionado = ean_principal
            if ean_selecionado:
                st.caption(f"📊 Usando EAN: `{ean_selecionado}`")
        
        desc = row.get('DESCRICAO')
        
        # CHAVE DO CACHE ATUALIZADA: Inclui produto + EAN selecionado
        cache_key = f"{codprod}_{ean_selecionado}" if ean_selecionado else str(codprod)
        
        # Botão para iniciar busca
        if cache_key not in st.session_state.search_results:
            if st.button("🔍 Buscar Imagens na Web", key=f"btn_{codprod}", type="primary"):
                with st.spinner("🔄 Consultando Google Imagens..."):
                    # Passa o EAN selecionado para a busca
                    perform_search(ean_selecionado, desc, cache_key)
                    time.sleep(0.5)
                    st.rerun()
        
        # Exibição dos Resultados
        results = st.session_state.search_results.get(cache_key, [])
        
        if results:
            st.success(f"✅ {len(results)} imagens encontradas")
            
            if ean_selecionado:
                st.caption(f"🔍 Busca realizada com EAN: `{ean_selecionado}`")
            
            # Grid de imagens (igual ao código anterior)
            selected_img = None
            
            for i in range(0, len(results), 2):
                cols = st.columns(2)
                for j, col in enumerate(cols):
                    idx = i + j
                    if idx < len(results):
                        with col:
                            item = results[idx]
                            try:
                                st.image(item['link'], use_container_width=True)
                                
                                if st.button(
                                    f"✔️ Selecionar",
                                    key=f"select_{codprod}_{idx}",
                                    use_container_width=True
                                ):
                                    selected_img = item['link']
                                    st.session_state.last_saved_image = selected_img
                                    
                            except Exception as e:
                                st.error(f"Erro ao carregar imagem {idx+1}")
                                logger.error(f"Image load error: {e}")
            
            # Botão de salvamento
            if st.session_state.get('last_saved_image'):
                st.divider()
                st.info(f"📌 Imagem selecionada")
                
                col_save1, col_save2 = st.columns([3, 1])
                with col_save1:
                    if st.button("💾 SALVAR NO SISTEMA", type="primary", use_container_width=True):
                        with st.spinner("💾 Salvando imagem..."):
                            if save_image_to_winthor(codprod, st.session_state.last_saved_image):
                                st.success("✅ Imagem salva com sucesso!")
                                st.session_state.last_saved_image = None
                                time.sleep(1.5)
                                st.rerun()
                            else:
                                st.error("❌ Falha ao salvar imagem")
                
                with col_save2:
                    if st.button("🔄 Cancelar", use_container_width=True):
                        st.session_state.last_saved_image = None
                        st.rerun()
                        
        elif cache_key in st.session_state.search_results:
            st.warning("⚠️ Nenhuma imagem encontrada no Google para este produto.")
            if ean_selecionado:
                st.caption(f"Tentou buscar com EAN: `{ean_selecionado}`")
            st.caption("Tente selecionar outro código de barras ou ajustar o cadastro.")

# --- 8. INTERFACE PRINCIPAL ---
st.title("🛒 Painel de Compras")
st.caption("Sistema de Gestão de Produtos com Busca Automática de Imagens")

# Barra superior de controles
col_top1, col_top2, col_top3 = st.columns([2, 1, 1])
with col_top1:
    if st.button("🔄 Atualizar Base de Dados", use_container_width=True):
        fetch_product_data.clear()
        st.session_state.search_results = {}
        logger.info("Cache limpo pelo usuário")
        st.rerun()

with col_top2:
    if st.button("🗑️ Limpar Cache de Imagens", use_container_width=True):
        st.session_state.search_results = {}
        st.success("✅ Cache limpo!")
        time.sleep(0.5)
        st.rerun()

# Carregar dados
df = fetch_product_data()

if not df.empty:
    # SIDEBAR - Filtros e Estatísticas
# ============================================
# ATUALIZAÇÃO DOS FILTROS (NO MAIN)
# ============================================

    # Dentro do bloco "if not df.empty:"
    with st.sidebar:
        st.header("🔍 Filtros Avançados")
        
        f_cod = st.text_input("🔢 Código do Produto")
        
        # FILTRO EAN ATUALIZADO
        f_ean = st.text_input(
            "📊 EAN / Código de Barras",
            help="Busca em TODOS os EANs cadastrados do produto"
        )
        
        f_desc = st.text_input("📝 Descrição (contém)")
        
        # Filtros categóricos
        col_f1, col_f2 = st.columns(2)
        f_filial = col_f1.multiselect("🏢 Filial", options=sorted(df['CODFILIAL'].unique()))
        f_status = col_f2.multiselect("⚡ Status", options=df['STATUS'].unique())
        
        f_depto = st.multiselect("🏷️ Departamento", options=sorted(df['DEPARTAMENTO'].dropna().unique()))
        
        # Filtro de dias sem venda
        max_dias = int(df['DIAS_SEM_VENDA'].max()) if not df['DIAS_SEM_VENDA'].isnull().all() else 0
        f_dias = st.slider("📅 Dias sem Venda (Mínimo)", 0, max_dias, 0)
        
        st.markdown("---")
        
        # Filtros de foto e exclusão
        opcao_foto = st.radio(
            "📷 Status da Foto:", 
            ["Todos", "✅ Com Foto", "❌ Sem Foto"], 
            index=0
        )
        
        opcao_exclusao = st.radio(
            "👁️ Visualizar:", 
            ["Todos", "Apenas Ativos", "Apenas Excluídos"], 
            index=0
        )
        
        st.markdown("---")
        
        # Estatísticas da API
        st.header("📊 Estatísticas da Sessão")
        
        quota_info = st.session_state.api_quota
        tempo_reset = int((quota_info['reset_time'] - time.time()) / 60)
        
        col_stat1, col_stat2 = st.columns(2)
        col_stat1.metric("🔍 Buscas API", f"{quota_info['count']}/100")
        col_stat2.metric("⏱️ Reset em", f"{max(0, tempo_reset)} min")
        
        st.metric("💾 Imagens em Cache", len(st.session_state.search_results))
        
        # Progresso da quota
        progress = min(quota_info['count'] / 100, 1.0)
        st.progress(progress)
        
        if quota_info['count'] >= 80:
            st.warning("⚠️ Quota próxima do limite!")

    # Aplicação dos Filtros
    df_filtered = df.copy()
    
    if f_cod: 
        df_filtered = df_filtered[df_filtered['CODPROD'].astype(str) == f_cod]
    
    # FILTRO EAN ATUALIZADO - Busca em todos os EANs
    if f_ean:
        logger.info(f"Filtrando por EAN: {f_ean}")
        df_filtered = df_filtered[
            df_filtered.apply(lambda row: has_ean(row['TODOS_EANS'], f_ean), axis=1)
        ]
        logger.info(f"Produtos encontrados: {len(df_filtered)}")
    
    if f_desc: 
        df_filtered = df_filtered[
            df_filtered['DESCRICAO'].str.contains(f_desc, case=False, na=False)
        ]

    if f_filial: 
        df_filtered = df_filtered[df_filtered['CODFILIAL'].isin(f_filial)]
    
    if f_status: 
        df_filtered = df_filtered[df_filtered['STATUS'].isin(f_status)]
    
    if f_depto: 
        df_filtered = df_filtered[df_filtered['DEPARTAMENTO'].isin(f_depto)]
    
    df_filtered = df_filtered[df_filtered['DIAS_SEM_VENDA'] >= f_dias]

    # Filtro de foto
    if opcao_foto == "✅ Com Foto":
        df_filtered = df_filtered[df_filtered['DIRFOTOPROD'].notna() & (df_filtered['DIRFOTOPROD'] != '')]
    elif opcao_foto == "❌ Sem Foto":
        df_filtered = df_filtered[df_filtered['DIRFOTOPROD'].isna() | (df_filtered['DIRFOTOPROD'] == '')]

    # Filtro de exclusão
    if opcao_exclusao == "Apenas Ativos":
        df_filtered = df_filtered[df_filtered['DTEXCLUSAO'].isna()]
    elif opcao_exclusao == "Apenas Excluídos":
        df_filtered = df_filtered[df_filtered['DTEXCLUSAO'].notna()]

    # Adicionar coluna visual de status da foto
    df_filtered['STATUS_FOTO'] = df_filtered['DIRFOTOPROD'].apply(
        lambda x: '✅' if pd.notna(x) and x != '' else '❌'
    )

    # Métricas Principais
    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    col_m1.metric("📦 Produtos", f"{len(df_filtered):,}")
    col_m2.metric("📊 Estoque Total", f"{df_filtered['QTEST'].sum():,.0f}")
    
    com_foto = len(df_filtered[df_filtered['STATUS_FOTO'] == '✅'])
    sem_foto = len(df_filtered[df_filtered['STATUS_FOTO'] == '❌'])
    col_m3.metric("✅ Com Foto", com_foto)
    col_m4.metric("❌ Sem Foto", sem_foto)

    # Tabela Interativa
    st.subheader("📋 Tabela de Produtos")
    
    # Adicione ANTES do st.dataframe() no código principal:

if not df_filtered.empty:
    # MÉTRICAS DE DIAGNÓSTICO
    st.sidebar.markdown("---")
    st.sidebar.subheader("🔍 Diagnóstico de Performance")
    
    # 1. Tamanho dos dados
    linhas = len(df_filtered)
    colunas = len(df_filtered.columns)
    tamanho_mb = df_filtered.memory_usage(deep=True).sum() / 1024**2
    
    col_d1, col_d2 = st.sidebar.columns(2)
    col_d1.metric("Linhas", f"{linhas:,}")
    col_d2.metric("Tamanho", f"{tamanho_mb:.2f} MB")
    
    # 2. Tempo de renderização
    start_render = time.time()

    event = st.dataframe(
        df_filtered,
        use_container_width=True,
        hide_index=True,
        column_order=[
            "STATUS_FOTO", "CODFILIAL", "CODPROD", "DESCRICAO", 
            "EAN", "QTEST", "DIAS_SEM_VENDA", "STATUS", "DTEXCLUSAO"
        ],
        column_config={
            "STATUS_FOTO": st.column_config.TextColumn("📷", width="small", help="Status da foto no sistema"),
            "CODFILIAL": st.column_config.NumberColumn("Filial", width="small"),
            "CODPROD": st.column_config.NumberColumn("Código", width="small"),
            "DESCRICAO": st.column_config.TextColumn("Descrição", width="large"),
            "EAN": st.column_config.TextColumn("EAN", width="medium"),
            "QTEST": st.column_config.NumberColumn("Estoque", format="%.0f", width="small"),
            "DIAS_SEM_VENDA": st.column_config.NumberColumn("Dias s/ Venda", format="%d", width="small"),
            "STATUS": st.column_config.TextColumn("Status", width="small"),
            "DTEXCLUSAO": st.column_config.DateColumn("Dt. Exclusão", format="DD/MM/YYYY", width="small"),
        },
        on_select="rerun",
        selection_mode="single-row"
    )

    render_time = time.time() - start_render
    
    if render_time > 2:
        st.sidebar.warning(f"⚠️ Renderização lenta: {render_time:.2f}s")
    else:
        st.sidebar.success(f"✅ Renderização: {render_time:.2f}s")
    
    # 3. Recomendações
    if linhas > 1000:
        st.sidebar.error("❌ Muitas linhas! Use paginação.")
    elif linhas > 500:
        st.sidebar.warning("⚠️ Considere adicionar paginação.")
    
    if tamanho_mb > 10:
        st.sidebar.error("❌ DataFrame muito grande!")
    elif tamanho_mb > 5:
        st.sidebar.warning("⚠️ DataFrame pesado.")

    # Abre modal ao selecionar linha
    if len(event.selection['rows']) > 0:
        idx = event.selection['rows'][0]
        show_product_modal(df_filtered.iloc[idx])

    # Exportação Excel
    st.markdown("---")
    col_exp1, col_exp2 = st.columns([3, 1])
    
    with col_exp2:
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_filtered.to_excel(writer, index=False, sheet_name='Analise_Produtos')
        
        st.download_button(
            label="📥 Exportar para Excel",
            data=output.getvalue(),
            file_name=f"relatorio_produtos_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

else:
    st.info("ℹ️ Nenhum dado carregado. Verifique a conexão com o banco de dados.")
    
    # Botão de diagnóstico
    if st.button("🔧 Testar Conexão"):
        try:
            engine = get_db_engine()
            with engine.connect() as conn:
                result = conn.execute(text("SELECT 1 FROM DUAL"))
                st.success("✅ Conexão com Oracle estabelecida com sucesso!")
        except Exception as e:
            st.error(f"❌ Erro de conexão: {e}")

# Rodapé
st.markdown("---")
st.caption(f"🕐 Última atualização: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')} | Sistema desenvolvido por Francirley Oliveira")