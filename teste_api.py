import os
import requests
from dotenv import load_dotenv

# 1. Carregar variáveis de ambiente
load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY")
cse_id = os.getenv("GOOGLE_CSE_ID")

print("--- INICIANDO TESTE DA API GOOGLE ---")
print(f"API Key lida: {'OK (Encontrada)' if api_key else 'ERRO (Não encontrada)'}")
print(f"CSE ID lido:  {'OK (Encontrado)' if cse_id else 'ERRO (Não encontrado)'}")

if not api_key or not cse_id:
    print("\n❌ ERRO CRÍTICO: As chaves não estão no arquivo .env")
    exit()

# 2. Configurar a busca de teste (ex: Coca Cola 2L)
query = "Coca Cola 2L"
url = "https://www.googleapis.com/customsearch/v1"
params = {
    'q': query,
    'cx': cse_id,
    'key': api_key,
    'searchType': 'image',
    'num': 1,
    'gl': 'br',
    'hl': 'pt'
}

# 3. Fazer a requisição
try:
    print(f"\n🔍 Buscando por: '{query}'...")
    response = requests.get(url, params=params)
    
    # 4. Analisar o resultado
    if response.status_code == 200:
        data = response.json()
        if 'items' in data:
            print("\n✅ SUCESSO! A API funcionou perfeitamente.")
            print(f"Imagem encontrada: {data['items'][0]['link']}")
        else:
            print("\n⚠️ A conexão funcionou, mas nenhuma imagem foi retornada (verifique se 'Image Search' está ativo no painel do Google).")
            print("Resposta bruta:", data)
            
    elif response.status_code == 403:
        print("\n🚫 ERRO 403: Permissão Negada.")
        print("Causas prováveis:")
        print("1. A 'Custom Search API' não foi ativada no Google Cloud Console.")
        print("2. A chave de API copiada está errada.")
        print("3. O Projeto associado à chave não tem conta de faturamento (embora seja grátis até certo ponto, às vezes pedem).")
        print(f"Detalhe do erro: {response.text}")
        
    elif response.status_code == 400:
        print("\n❌ ERRO 400: Requisição Inválida.")
        print("Verifique se o 'Search Engine ID' (CX) está correto.")
        print(f"Detalhe do erro: {response.text}")
        
    else:
        print(f"\n❌ ERRO DESCONHECIDO ({response.status_code})")
        print(response.text)

except Exception as e:
    print(f"\n💥 Erro de conexão/python: {e}")