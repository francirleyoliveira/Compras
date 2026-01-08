# 🛒 Sistema de Gestão de Compras & Imagens

Sistema web desenvolvido em Streamlit para gestão inteligente de produtos com integração ao WinThor (Oracle Database) e busca automática de imagens via Google Custom Search API.

## 📋 Índice

- [Recursos](#-recursos)
- [Requisitos](#-requisitos)
- [Instalação](#-instalação)
- [Configuração](#-configuração)
- [Uso](#-uso)
- [Estrutura do Projeto](#-estrutura-do-projeto)
- [Troubleshooting](#-troubleshooting)
- [Melhorias Futuras](#-melhorias-futuras)

---

## ✨ Recursos

### Principais Funcionalidades
- ✅ **Consulta ao WinThor**: Busca produtos ativos com histórico de vendas
- ✅ **Busca Inteligente de Imagens**: Integração com Google Custom Search API
- ✅ **Gerenciamento de Fotos**: Visualiza e salva imagens no sistema
- ✅ **Filtros Avançados**: Por código, EAN, descrição, filial, departamento, etc.
- ✅ **Análise de Estoque**: Métricas de produtos sem foto e dias sem venda
- ✅ **Exportação Excel**: Relatórios personalizados
- ✅ **Cache Inteligente**: Otimização de consultas e cotas da API

### Melhorias Implementadas (Versão 2.0)
- 🔒 **Controle de Cotas**: Limita 100 buscas/hora (quota gratuita do Google)
- 🛡️ **Tratamento de Erros**: HTTP timeout, rate limiting, validação de imagens
- 📊 **Estatísticas em Tempo Real**: Uso da API e cache
- 💾 **Salvamento Automático**: Download e registro de imagens no Oracle
- 📝 **Sistema de Logs**: Auditoria completa de operações
- 🎨 **UI Melhorada**: Indicadores visuais de status (✅/❌)

---

## 🔧 Requisitos

### Software
- Python 3.9 ou superior
- Oracle Instant Client (11c ou superior)
- Acesso ao banco WinThor
- Conta Google Cloud (para API de busca)

### Bibliotecas Python
```bash
streamlit>=1.31.1
pandas>=2.2.0
oracledb>=2.0.1
sqlalchemy>=2.0.25
python-dotenv>=1.0.1
requests>=2.31.0
Pillow>=10.2.0
openpyxl>=3.1.2
```

---

## 📦 Instalação

### 1. Clone o Repositório
```bash
git clone https://github.com/seu-usuario/gestao-compras.git
cd gestao-compras
```

### 2. Crie um Ambiente Virtual
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### 3. Instale as Dependências
```bash
pip install -r requirements.txt
```

### 4. Instale o Oracle Instant Client

#### Windows:
1. Baixe de: https://www.oracle.com/database/technologies/instant-client/downloads.html
2. Extraia em `C:\oracle\instantclient_21_3`
3. Adicione ao PATH do sistema (opcional)

#### Linux:
```bash
# Ubuntu/Debian
sudo apt-get install libaio1
wget https://download.oracle.com/otn_software/linux/instantclient/instantclient-basic-linux.x64-21.9.0.0.0dbru.zip
unzip instantclient-basic-linux.x64-21.9.0.0.0dbru.zip -d /opt/oracle
```

---

## ⚙️ Configuração

### 1. Configure o Banco de Dados

Crie um arquivo `.env` na raiz do projeto:

```bash
cp .env.example .env
```

Edite o `.env` com suas credenciais:

```env
# Oracle Database
DB_USER=usuario_winthor
DB_PASSWORD=sua_senha_segura
DB_HOST=192.168.1.100
DB_PORT=1521
DB_SERVICE=WINTHOR
ORACLE_CLIENT_PATH=C:\\oracle\\instantclient_21_3

# Diretório de Imagens
WINTHOR_IMAGE_DIR=C:\\WinThor\\fotos_produtos
```

### 2. Configure a Google Custom Search API

#### Passo 1: Criar Projeto no Google Cloud
1. Acesse: https://console.cloud.google.com/
2. Clique em **"Select a project"** → **"New Project"**
3. Nome do projeto: `winthor-image-search`
4. Clique em **"Create"**

#### Passo 2: Ativar a API
1. No menu lateral: **"APIs & Services"** → **"Library"**
2. Pesquise por **"Custom Search API"**
3. Clique em **"Enable"**

#### Passo 3: Criar API Key
1. **"APIs & Services"** → **"Credentials"**
2. **"Create Credentials"** → **"API Key"**
3. Copie a chave gerada (ex: `AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX`)
4. (Opcional) Clique em **"Restrict Key"** → Configure restrições de IP

#### Passo 4: Criar Search Engine
1. Acesse: https://programmablesearchengine.google.com/
2. Clique em **"Add"** (Adicionar)
3. Configure:
   - **Sites to search**: `www.google.com` (busca em toda a web)
   - **Name**: `WinThor Product Images`
   - **Search Settings**: Ative **"Image Search"** e **"SafeSearch"**
4. Clique em **"Create"**
5. Copie o **Search Engine ID** (ex: `a1b2c3d4e5f6g7h8i`)

#### Passo 5: Adicione ao .env
```env
GOOGLE_API_KEY=AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
GOOGLE_CSE_ID=a1b2c3d4e5f6g7h8i
```

### 3. Teste a Configuração

Execute o script de teste:
```bash
python teste_api.py
```

Saída esperada:
```
--- INICIANDO TESTE DA API GOOGLE ---
API Key lida: OK (Encontrada)
CSE ID lido:  OK (Encontrado)

🔍 Buscando por: 'Coca Cola 2L'...

✅ SUCESSO! A API funcionou perfeitamente.
Imagem encontrada: https://example.com/image.jpg
```

---

## 🚀 Uso

### Iniciar o Sistema
```bash
streamlit run app.py
```

O sistema abrirá automaticamente em `http://localhost:8501`

### Fluxo de Trabalho

#### 1. **Filtrar Produtos**
- Use a **sidebar** para aplicar filtros:
  - Código do produto
  - EAN (código de barras)
  - Descrição
  - Filial, Departamento, Status
  - Produtos sem foto (❌ Sem Foto)

#### 2. **Selecionar Produto**
- Clique em qualquer linha da tabela
- Um modal será aberto com detalhes completos

#### 3. **Buscar Imagens**
- No modal, clique em **"🔍 Buscar Imagens na Web"**
- Aguarde o carregamento (4 resultados)

#### 4. **Salvar Imagem**
- Clique em **"✔️ Selecionar"** na imagem desejada
- Clique em **"💾 SALVAR NO SISTEMA"**
- A imagem será:
  - Baixada automaticamente
  - Salva em `WINTHOR_IMAGE_DIR`
  - Registrada no campo `DIRFOTOPROD` do Oracle

#### 5. **Exportar Relatório**
- Clique em **"📥 Exportar para Excel"**
- Arquivo gerado: `relatorio_produtos_YYYYMMDD_HHMMSS.xlsx`

---

## 📁 Estrutura do Projeto

```
gestao-compras/
│
├── app.py                  # Aplicação principal
├── teste_api.py            # Script de teste da API Google
├── requirements.txt        # Dependências Python
├── .env                    # Configurações (NÃO COMMITAR)
├── .env.example            # Template de configuração
├── .gitignore              # Arquivos ignorados pelo Git
├── app.log                 # Logs de execução (gerado automaticamente)
├── README.md               # Este arquivo
│
└── venv/                   # Ambiente virtual (NÃO COMMITAR)
```

---

## 🐛 Troubleshooting

### Problema: "Oracle Client não inicializado"
**Solução:**
1. Verifique se o caminho em `ORACLE_CLIENT_PATH` está correto
2. No Windows, adicione o diretório ao PATH:
   ```
   setx PATH "%PATH%;C:\oracle\instantclient_21_3"
   ```
3. Reinicie o terminal/IDE

### Problema: "Erro 403 - Permissão Negada" (Google API)
**Causas possíveis:**
- API Key incorreta
- Custom Search API não ativada no projeto
- Restrições de IP configuradas incorretamente

**Solução:**
1. Acesse o Google Cloud Console
2. Verifique se a API está ativa
3. Recrie a API Key sem restrições (para teste)

### Problema: "Nenhuma imagem encontrada"
**Solução:**
1. Verifique se "Image Search" está ativo no Programmable Search Engine
2. Teste a busca manualmente no painel do Google
3. Ajuste a query (função `clean_text()`)

### Problema: "Limite de 100 buscas atingido"
**Solução:**
- Aguarde 1 hora para reset automático
- **OU** configure faturamento no Google Cloud (limite passa para 10.000/dia)

### Problema: Imagem não salva no WinThor
**Solução:**
1. Verifique permissões de escrita em `WINTHOR_IMAGE_DIR`
2. Confirme que o usuário do banco tem permissão de UPDATE em `PCPRODUT`
3. Verifique os logs em `app.log`

---

## 📊 Logs e Monitoramento

Os logs são salvos automaticamente em `app.log`:

```python
# Exemplo de logs
2024-12-20 10:30:15 - INFO - Oracle Client inicializado com sucesso
2024-12-20 10:30:20 - INFO - Dados carregados: 1542 produtos
2024-12-20 10:35:42 - INFO - Buscando: "Coca Cola 2L embalagem produto"
2024-12-20 10:35:43 - INFO - Busca bem-sucedida: 4 imagens para 'Coca Cola 2L'
2024-12-20 10:36:10 - INFO - Imagem salva em: C:\WinThor\fotos_produtos\12345.jpg
2024-12-20 10:36:11 - INFO - Banco atualizado para produto 12345
```

---

## 🔮 Melhorias Futuras

### Planejadas para v3.0
- [ ] Edição em lote (múltiplos produtos)
- [ ] Upload manual de imagens (drag & drop)
- [ ] Histórico de alterações (audit trail)
- [ ] Notificações por email (produtos sem foto)
- [ ] Dashboard analítico (Plotly/Altair)
- [ ] Integração com outras APIs de imagem (Unsplash, Pexels)
- [ ] Sistema de aprovação de imagens (workflow)
- [ ] Comparação lado a lado (imagem atual vs nova)
- [ ] Recorte e edição básica de imagens
- [ ] API REST para integração com outros sistemas

### Contribuições
Pull requests são bem-vindos! Para mudanças maiores:
1. Abra uma issue primeiro
2. Fork o projeto
3. Crie uma branch (`git checkout -b feature/NovaFuncionalidade`)
4. Commit suas mudanças (`git commit -m 'Adiciona nova funcionalidade'`)
5. Push para a branch (`git push origin feature/NovaFuncionalidade`)
6. Abra um Pull Request

---

## 📄 Licença

Este projeto é proprietário e confidencial. Uso exclusivo interno.

---

## 👨‍💻 Autor

**Seu Nome**  
📧 email@empresa.com.br  
🏢 Departamento de TI - Gestão de Compras

---

## 🙏 Agradecimentos

- Equipe de Compras pelo feedback
- Oracle/WinThor pela documentação
- Google Cloud Platform
- Comunidade Streamlit

---

**Última atualização:** Dezembro 2024  
**Versão:** 2.0.0