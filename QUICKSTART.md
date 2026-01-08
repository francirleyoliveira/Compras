# 🚀 Guia de Início Rápido

**Tempo estimado:** 15 minutos

## Pré-requisitos Mínimos
- ✅ Python 3.9+
- ✅ Oracle Instant Client
- ✅ Acesso ao WinThor
- ✅ Conta Google Cloud

---

## Passo 1: Instalação (3 min)

```bash
# Clone o projeto
git clone https://github.com/seu-usuario/gestao-compras.git
cd gestao-compras

# Crie ambiente virtual
python -m venv venv

# Ative o ambiente
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Instale dependências
pip install -r requirements.txt
```

---

## Passo 2: Oracle Client (2 min)

### Windows
1. Baixe: https://www.oracle.com/database/technologies/instant-client/winx64-64-downloads.html
2. Extraia em `C:\oracle\instantclient_21_3`

### Linux (Ubuntu/Debian)
```bash
sudo apt-get install libaio1
wget https://download.oracle.com/otn_software/linux/instantclient/219000/instantclient-basic-linux.x64-21.9.0.0.0dbru.zip
unzip instantclient-basic-linux.x64-21.9.0.0.0dbru.zip -d /opt/oracle
```

---

## Passo 3: Configure o .env (5 min)

```bash
# Copie o template
cp .env.example .env

# Edite o arquivo
nano .env  # ou use seu editor preferido
```

**Variáveis obrigatórias:**
```env
# 1. Banco de Dados WinThor
DB_USER=seu_usuario
DB_PASSWORD=sua_senha
DB_HOST=192.168.1.100
DB_PORT=1521
DB_SERVICE=WINTHOR

# 2. Oracle Client
ORACLE_CLIENT_PATH=C:\oracle\instantclient_21_3

# 3. Google API (veja próximo passo)
GOOGLE_API_KEY=sua_api_key_aqui
GOOGLE_CSE_ID=seu_cse_id_aqui

# 4. Diretório de Imagens
WINTHOR_IMAGE_DIR=C:\WinThor\fotos_produtos
```

---

## Passo 4: Google API (5 min)

### 4.1 Criar Projeto
1. Acesse: https://console.cloud.google.com/
2. **"New Project"** → Nome: `winthor-images`
3. **"Create"**

### 4.2 Ativar API
1. **"APIs & Services"** → **"Library"**
2. Pesquise: **"Custom Search API"**
3. **"Enable"**

### 4.3 Criar API Key
1. **"Credentials"** → **"Create Credentials"** → **"API Key"**
2. Copie a chave (ex: `AIzaSy...`)
3. Cole no `.env` em `GOOGLE_API_KEY`

### 4.4 Criar Search Engine
1. Acesse: https://programmablesearchengine.google.com/
2. **"Add"** → Sites: `www.google.com`
3. Ative **"Image Search"**
4. **"Create"**
5. Copie o **Search Engine ID**
6. Cole no `.env` em `GOOGLE_CSE_ID`

---

## Passo 5: Teste a Configuração (1 min)

```bash
# Execute o diagnóstico
python diagnostico.py
```

**Saída esperada:**
```
✅ TODOS OS TESTES PASSARAM!
   Sistema pronto para uso.

🚀 Execute: streamlit run app.py
```

---

## Passo 6: Inicie o Sistema! 🎉

```bash
streamlit run app.py
```

O navegador abrirá automaticamente em: `http://localhost:8501`

---

## Primeiros Passos no Sistema

### 1️⃣ Filtrar Produtos Sem Foto
- Sidebar → **"Status da Foto"** → **"❌ Sem Foto"**

### 2️⃣ Selecionar um Produto
- Clique em qualquer linha da tabela

### 3️⃣ Buscar Imagem
- Modal → **"🔍 Buscar Imagens na Web"**

### 4️⃣ Salvar Imagem
- Clique em **"✔️ Selecionar"** na imagem desejada
- **"💾 SALVAR NO SISTEMA"**

### 5️⃣ Exportar Relatório
- **"📥 Exportar para Excel"**

---

## Resolução Rápida de Problemas

| Problema | Solução Rápida |
|----------|----------------|
| Erro Oracle Client | Verifique `ORACLE_CLIENT_PATH` no .env |
| Erro 403 Google API | API não ativada no Google Cloud Console |
| Sem permissão para salvar | Verifique permissões em `WINTHOR_IMAGE_DIR` |
| Limite de buscas | Aguarde 1 hora ou configure faturamento |

---

## Checklist Completo

- [ ] Python 3.9+ instalado
- [ ] Oracle Instant Client baixado e extraído
- [ ] Projeto clonado
- [ ] Ambiente virtual criado e ativado
- [ ] Dependências instaladas (`pip install -r requirements.txt`)
- [ ] Arquivo `.env` criado e configurado
- [ ] Google Cloud Project criado
- [ ] Custom Search API ativada
- [ ] API Key criada
- [ ] Search Engine criado
- [ ] Diagnóstico passou (`python diagnostico.py`)
- [ ] Sistema iniciado (`streamlit run app.py`)

---

## Próximos Passos

✅ Sistema funcionando? Leia o [README.md](README.md) completo para recursos avançados.

🐛 Encontrou um bug? Abra uma issue no GitHub.

💡 Quer contribuir? Veja a seção "Contribuições" no README.

---

**Dúvidas?** Consulte os logs em `app.log`