#!/usr/bin/env python3
"""
Script de Diagnóstico Completo
Verifica todas as configurações e dependências do sistema
"""

import os
import sys
from dotenv import load_dotenv

print("="*60)
print(" 🔧 DIAGNÓSTICO DO SISTEMA - GESTÃO DE COMPRAS & IMAGENS")
print("="*60)
print()

# ==========================================
# 1. VERIFICAÇÃO DO AMBIENTE PYTHON
# ==========================================
print("📦 1. VERIFICANDO AMBIENTE PYTHON")
print("-" * 60)
print(f"✓ Versão Python: {sys.version.split()[0]}")
print(f"✓ Executável: {sys.executable}")
print()

# ==========================================
# 2. VERIFICAÇÃO DE DEPENDÊNCIAS
# ==========================================
print("📚 2. VERIFICANDO DEPENDÊNCIAS")
print("-" * 60)

dependencias = {
    'streamlit': '1.31.1',
    'pandas': '2.2.0',
    'oracledb': '2.0.1',
    'sqlalchemy': '2.0.25',
    'python-dotenv': '1.0.1',
    'requests': '2.31.0',
    'PIL': '10.2.0',
    'openpyxl': '3.1.2'
}

erros_deps = []

for lib, versao_min in dependencias.items():
    try:
        if lib == 'PIL':
            import PIL
            modulo = PIL
        else:
            modulo = __import__(lib)
        
        versao = getattr(modulo, '__version__', 'desconhecida')
        print(f"✅ {lib:20s} v{versao}")
    except ImportError:
        print(f"❌ {lib:20s} NÃO INSTALADO")
        erros_deps.append(lib)

if erros_deps:
    print(f"\n⚠️  Instale as dependências faltantes:")
    print(f"   pip install {' '.join(erros_deps)}")
print()

# ==========================================
# 3. VERIFICAÇÃO DO ARQUIVO .ENV
# ==========================================
print("🔑 3. VERIFICANDO ARQUIVO .ENV")
print("-" * 60)

if not os.path.exists('.env'):
    print("❌ Arquivo .env NÃO ENCONTRADO")
    print("   Copie o template: cp .env.example .env")
    print()
else:
    print("✅ Arquivo .env encontrado")
    load_dotenv()
    
    # Variáveis obrigatórias
    vars_obrigatorias = {
        'DB_USER': 'Usuário do banco',
        'DB_PASSWORD': 'Senha do banco',
        'DB_HOST': 'Host do Oracle',
        'DB_PORT': 'Porta do Oracle',
        'DB_SERVICE': 'Service Name',
        'ORACLE_CLIENT_PATH': 'Caminho do Instant Client',
        'GOOGLE_API_KEY': 'API Key do Google',
        'GOOGLE_CSE_ID': 'Search Engine ID',
        'WINTHOR_IMAGE_DIR': 'Diretório de imagens'
    }
    
    vars_faltando = []
    
    for var, descricao in vars_obrigatorias.items():
        valor = os.getenv(var)
        if valor:
            # Mascara senhas e API keys
            if 'PASSWORD' in var or 'KEY' in var:
                exibir = f"{valor[:8]}...{valor[-4:]}" if len(valor) > 12 else "***"
            else:
                exibir = valor
            print(f"  ✓ {var:25s} = {exibir}")
        else:
            print(f"  ❌ {var:25s} = NÃO CONFIGURADO")
            vars_faltando.append(var)
    
    if vars_faltando:
        print(f"\n⚠️  Configure as variáveis faltantes no .env:")
        for v in vars_faltando:
            print(f"   - {v}")
print()

# ==========================================
# 4. VERIFICAÇÃO DO ORACLE CLIENT
# ==========================================
print("🗄️  4. VERIFICANDO ORACLE INSTANT CLIENT")
print("-" * 60)

oracle_path = os.getenv("ORACLE_CLIENT_PATH")
if oracle_path:
    if os.path.exists(oracle_path):
        print(f"✅ Diretório encontrado: {oracle_path}")
        
        # Verifica arquivos essenciais
        arquivos_essenciais = ['oci.dll', 'oraociei21.dll'] if sys.platform == 'win32' else ['libclntsh.so']
        
        for arq in arquivos_essenciais:
            caminho_completo = os.path.join(oracle_path, arq)
            if os.path.exists(caminho_completo):
                print(f"  ✓ {arq} encontrado")
            else:
                print(f"  ⚠️  {arq} NÃO encontrado")
    else:
        print(f"❌ Diretório NÃO encontrado: {oracle_path}")
else:
    print("❌ ORACLE_CLIENT_PATH não configurado no .env")

# Tenta inicializar o Oracle Client
try:
    import oracledb
    oracledb.init_oracle_client(lib_dir=oracle_path)
    print("✅ Oracle Client inicializado com sucesso")
except Exception as e:
    if "already initialized" in str(e):
        print("✅ Oracle Client já estava inicializado")
    else:
        print(f"❌ Erro ao inicializar: {e}")
print()

# ==========================================
# 5. TESTE DE CONEXÃO COM ORACLE
# ==========================================
print("🔌 5. TESTANDO CONEXÃO COM BANCO DE DADOS")
print("-" * 60)

try:
    from sqlalchemy import create_engine, text
    
    user = os.getenv("DB_USER")
    password = os.getenv("DB_PASSWORD")
    host = os.getenv("DB_HOST")
    port = os.getenv("DB_PORT")
    service = os.getenv("DB_SERVICE")
    
    if all([user, password, host, port, service]):
        connection_string = f"oracle+oracledb://{user}:{password}@{host}:{port}/?service_name={service}"
        engine = create_engine(connection_string)
        
        print("⏳ Conectando ao Oracle...")
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 'OK' as status, SYSDATE as data FROM DUAL"))
            row = result.fetchone()
            print(f"✅ Conexão estabelecida com sucesso!")
            print(f"  Status: {row[0]}")
            print(f"  Data do servidor: {row[1]}")
            
            # Testa acesso às tabelas
            print("\n  Testando acesso às tabelas:")
            tabelas = ['PCPRODUT', 'PCEST', 'PCEMBALAGEM']
            for tabela in tabelas:
                try:
                    result = conn.execute(text(f"SELECT COUNT(*) FROM {tabela} WHERE ROWNUM = 1"))
                    print(f"    ✓ {tabela} acessível")
                except Exception as e:
                    print(f"    ❌ {tabela} não acessível: {e}")
    else:
        print("❌ Credenciais do banco não configuradas completamente")
        
except Exception as e:
    print(f"❌ Erro na conexão: {e}")
print()

# ==========================================
# 6. TESTE DA GOOGLE CUSTOM SEARCH API
# ==========================================
print("🔍 6. TESTANDO GOOGLE CUSTOM SEARCH API")
print("-" * 60)

try:
    import requests
    
    api_key = os.getenv("GOOGLE_API_KEY")
    cse_id = os.getenv("GOOGLE_CSE_ID")
    
    if api_key and cse_id:
        print("⏳ Fazendo busca de teste...")
        
        url = "https://www.googleapis.com/customsearch/v1"
        params = {
            'q': 'teste',
            'cx': cse_id,
            'key': api_key,
            'searchType': 'image',
            'num': 1
        }
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if 'items' in data:
                print("✅ API funcionando perfeitamente!")
                print(f"  Quota usada hoje: Não disponível via API")
                print(f"  Limite diário: 100 buscas (gratuito)")
            else:
                print("⚠️  API respondeu, mas sem resultados")
                print("  Verifique se 'Image Search' está ativo no painel")
        elif response.status_code == 403:
            print("❌ Erro 403: Permissão negada")
            print("  Verifique:")
            print("  1. Custom Search API está ativada?")
            print("  2. API Key está correta?")
            print("  3. Há faturamento configurado? (opcional)")
        elif response.status_code == 400:
            print("❌ Erro 400: Requisição inválida")
            print("  Verifique o Search Engine ID (CSE_ID)")
        else:
            print(f"❌ Erro {response.status_code}: {response.text}")
    else:
        print("❌ API Key ou CSE ID não configurados")
        
except Exception as e:
    print(f"❌ Erro ao testar API: {e}")
print()

# ==========================================
# 7. VERIFICAÇÃO DO DIRETÓRIO DE IMAGENS
# ==========================================
print("📁 7. VERIFICANDO DIRETÓRIO DE IMAGENS")
print("-" * 60)

img_dir = os.getenv("WINTHOR_IMAGE_DIR")
if img_dir:
    print(f"Caminho configurado: {img_dir}")
    
    if os.path.exists(img_dir):
        print("✅ Diretório encontrado")
        
        # Verifica permissões de escrita
        test_file = os.path.join(img_dir, '.test_write')
        try:
            with open(test_file, 'w') as f:
                f.write('test')
            os.remove(test_file)
            print("✅ Permissão de escrita: OK")
        except Exception as e:
            print(f"❌ Sem permissão de escrita: {e}")
        
        # Conta imagens existentes
        try:
            imagens = [f for f in os.listdir(img_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
            print(f"📊 Total de imagens: {len(imagens)}")
        except Exception as e:
            print(f"⚠️  Erro ao listar imagens: {e}")
    else:
        print("⚠️  Diretório NÃO encontrado")
        print("  Criando diretório...")
        try:
            os.makedirs(img_dir, exist_ok=True)
            print("✅ Diretório criado com sucesso")
        except Exception as e:
            print(f"❌ Erro ao criar diretório: {e}")
else:
    print("❌ WINTHOR_IMAGE_DIR não configurado")
print()

# ==========================================
# RESUMO FINAL
# ==========================================
print("="*60)
print(" 📊 RESUMO DO DIAGNÓSTICO")
print("="*60)

problemas = []

if erros_deps:
    problemas.append("Dependências Python faltando")

if not os.path.exists('.env'):
    problemas.append("Arquivo .env não encontrado")
elif vars_faltando:
    problemas.append("Variáveis de ambiente não configuradas")

if not oracle_path or not os.path.exists(oracle_path):
    problemas.append("Oracle Client não configurado corretamente")

if not api_key or not cse_id:
    problemas.append("Google API não configurada")

if not img_dir or not os.path.exists(img_dir):
    problemas.append("Diretório de imagens não existe")

if problemas:
    print("\n⚠️  PROBLEMAS ENCONTRADOS:")
    for i, p in enumerate(problemas, 1):
        print(f"   {i}. {p}")
    print("\n👉 Consulte o README.md para instruções detalhadas")
    sys.exit(1)
else:
    print("\n✅ TODOS OS TESTES PASSARAM!")
    print("   Sistema pronto para uso.")
    print("\n🚀 Execute: streamlit run app.py")
    sys.exit(0)