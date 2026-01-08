# 🧪 Plano de Testes - Múltiplos EANs

## 📋 Visão Geral

Este documento descreve o plano completo de testes para a funcionalidade de **Múltiplos Códigos de Barras (EANs)** por produto.

---

## ✅ Pré-requisitos

### Dados de Teste Necessários

Identifique produtos com diferentes cenários:

1. **Produto A**: 1 único EAN (caso padrão)
2. **Produto B**: 2-3 EANs ativos
3. **Produto C**: Mais de 5 EANs ativos
4. **Produto D**: EANs inativos (DTINATIVO preenchido)

### Como Identificar:

```sql
-- Execute no Oracle para encontrar produtos de teste
SELECT 
    CODPROD,
    COUNT(*) as QTD_EANS
FROM PCEMBALAGEM
WHERE DTINATIVO IS NULL
  AND CODAUXILIAR IS NOT NULL
  AND LENGTH(TRIM(CODAUXILIAR)) >= 8
GROUP BY CODPROD
ORDER BY QTD_EANS DESC
FETCH FIRST 10 ROWS ONLY;
```

---

## 🧪 Testes Funcionais

### **Teste 1: Carregamento de Dados**

**Objetivo:** Verificar se a query retorna múltiplos EANs corretamente.

#### Passos:
1. Inicie o sistema: `streamlit run app.py`
2. Observe o console/logs
3. Verifique se não há erros SQL

#### Critérios de Sucesso:
- ✅ Aplicação inicia sem erros
- ✅ Log mostra: `"Produtos com múltiplos EANs: X"`
- ✅ Tabela carrega normalmente

#### Debug (se falhar):
```python
# Adicione no código após fetch_product_data():
st.write("DEBUG - Primeiros 5 produtos:")
st.dataframe(df[['CODPROD', 'DESCRICAO', 'EAN', 'TODOS_EANS', 'QTD_EANS']].head())
```

---

### **Teste 2: Filtro por EAN Secundário**

**Objetivo:** Confirmar que busca encontra produto por qualquer EAN.

#### Passos:
1. Escolha um **Produto B** (com 2+ EANs)
2. Anote um EAN secundário (não o principal)
3. Digite este EAN no filtro "📊 EAN / Código de Barras"
4. Pressione Enter

#### Critérios de Sucesso:
- ✅ Produto aparece nos resultados
- ✅ Filtro funciona com busca parcial (ex: digitar "7891" encontra "7891234567890")

#### Casos de Teste:

| Cenário | EAN Principal | EAN Secundário | Entrada | Esperado |
|---------|---------------|----------------|---------|----------|
| Busca Exata | 7891234567890 | 7899876543210 | 7899876543210 | ✅ Encontra |
| Busca Parcial | 7891234567890 | 7899876543210 | 789987 | ✅ Encontra |
| EAN Inativo | 7891234567890 | 111111111 (inativo) | 111111111 | ❌ Não encontra |
| EAN Inexistente | 7891234567890 | - | 9999999999 | ❌ Não encontra |

---

### **Teste 3: Visualização no Modal**

**Objetivo:** Verificar exibição de múltiplos EANs.

#### Passos:
1. Selecione um **Produto B** (com 2+ EANs)
2. Observe o modal de detalhes

#### Critérios de Sucesso:
- ✅ Mostra badge "ℹ️ Este produto possui **X códigos de barras**"
- ✅ Expander "📊 Ver todos os EANs" está presente
- ✅ EAN principal marcado com "🏆 Principal"
- ✅ Todos os EANs listados corretamente

#### Screenshot Esperado:
```
ℹ️ Este produto possui 3 códigos de barras cadastrados

📊 Ver todos os EANs (clique para expandir)
  1. 7891234567890  🏆 Principal
  2. 7899876543210
  3. 7895555555555
```

---

### **Teste 4: Seleção de EAN para Busca**

**Objetivo:** Confirmar que o seletor de EAN funciona.

#### Passos:
1. Abra modal de um **Produto B** (com 2+ EANs)
2. Observe a seção "🌐 Busca Google"

#### Critérios de Sucesso:

**Se sistema tem Streamlit 1.31+:**
- ✅ Mostra `st.pills` com todos os EANs
- ✅ EAN principal vem pré-selecionado

**Se sistema tem Streamlit < 1.31:**
- ✅ Mostra `st.selectbox` com todos os EANs
- ✅ EAN principal vem como default

**Para Produto A (1 EAN apenas):**
- ✅ Não mostra seletor
- ✅ Mostra apenas: "📊 Usando EAN: `XXXXXXXX`"

---

### **Teste 5: Busca de Imagens com EAN Secundário**

**Objetivo:** Confirmar que a busca usa o EAN selecionado.

#### Passos:
1. Abra modal de um **Produto B**
2. **Selecione um EAN secundário** (não o principal)
3. Clique em "🔍 Buscar Imagens na Web"
4. Observe os logs (console ou app.log)

#### Critérios de Sucesso:
- ✅ Busca é executada
- ✅ Log mostra: `"Buscando com cache_key=CODPROD_EANSECUNDARIO"`
- ✅ Query enviada ao Google contém o EAN secundário
- ✅ Imagens retornadas

#### Verificação no Log:
```
INFO - Buscando com cache_key=731_7899876543210, query="7899876543210" produto
INFO - Busca bem-sucedida: 4 imagens para '"7899876543210" produto'
```

---

### **Teste 6: Cache Independente por EAN**

**Objetivo:** Verificar que cada EAN tem cache separado.

#### Passos:
1. Abra modal do **Produto B**
2. Selecione **EAN 1**, clique em "Buscar"
3. Feche e reabra o modal
4. Selecione **EAN 2**, clique em "Buscar"
5. Verifique contador de buscas na sidebar

#### Critérios de Sucesso:
- ✅ Primeira busca incrementa contador (+1)
- ✅ Segunda busca incrementa contador novamente (+1)
- ✅ Total de buscas = 2 (não reutilizou cache)
- ✅ Fechar e reabrir modal **não faz nova busca** (usa cache)

---

### **Teste 7: Filtro + Seleção + Busca (Fluxo Completo)**

**Objetivo:** Testar o fluxo end-to-end.

#### Passos:
1. **Filtrar:** Digite EAN secundário no filtro da sidebar
2. **Selecionar:** Clique no produto encontrado
3. **Visualizar:** Confirme que modal mostra múltiplos EANs
4. **Trocar EAN:** Selecione um EAN diferente do principal
5. **Buscar:** Clique em "🔍 Buscar Imagens"
6. **Salvar:** Selecione e salve uma imagem

#### Critérios de Sucesso:
- ✅ Todas etapas funcionam sem erros
- ✅ Imagem salva corretamente
- ✅ Banco atualizado (campo DIRFOTOPROD preenchido)

---

## 🔍 Testes de Edge Cases

### **Edge Case 1: Produto Sem EANs**

**Cenário:** Produto existe mas não tem EANs cadastrados.

#### Comportamento Esperado:
- Coluna `TODOS_EANS` = NULL
- Coluna `QTD_EANS` = NULL ou 0
- Modal não mostra seletor de EAN
- Busca usa apenas descrição do produto

---

### **Edge Case 2: EAN com Caracteres Inválidos**

**Cenário:** PCEMBALAGEM contém EANs tipo "N/A", "000000", etc.

#### Comportamento Esperado:
- Query filtra com `LENGTH(TRIM(CODAUXILIAR)) >= 8`
- EANs inválidos não aparecem

#### Teste:
```sql
-- Verificar EANs problemáticos
SELECT CODPROD, CODAUXILIAR, LENGTH(TRIM(CODAUXILIAR))
FROM PCEMBALAGEM
WHERE CODAUXILIAR IS NOT NULL
  AND LENGTH(TRIM(CODAUXILIAR)) < 8
  AND ROWNUM <= 10;
```

---

### **Edge Case 3: Mais de 4000 Caracteres (Overflow LISTAGG)**

**Cenário:** Produto com dezenas de EANs ultrapassa limite do LISTAGG.

#### Comportamento Esperado:
- Query usa `ON OVERFLOW TRUNCATE '...' WITH COUNT`
- String truncada termina com "..."
- Sistema continua funcionando

#### Teste Manual:
```sql
-- Criar produto de teste (se possível)
SELECT 
    CODPROD,
    LENGTH(TODOS_EANS) as TAMANHO,
    TODOS_EANS
FROM (
    SELECT 
        CODPROD,
        LISTAGG(CODAUXILIAR, '|') WITHIN GROUP (ORDER BY CODAUXILIAR)
            ON OVERFLOW TRUNCATE '...' WITH COUNT AS TODOS_EANS
    FROM PCEMBALAGEM
    WHERE DTINATIVO IS NULL
    GROUP BY CODPROD
)
WHERE LENGTH(TODOS_EANS) > 3900
FETCH FIRST 1 ROWS ONLY;
```

---

## 📊 Testes de Performance

### **Teste P1: Tempo de Carregamento**

**Objetivo:** Medir impacto da query complexa.

#### Métrica:
- Tempo de execução de `fetch_product_data()`

#### Passos:
1. Adicione logging:
```python
import time
start = time.time()
df = fetch_product_data()
elapsed = time.time() - start
logger.info(f"Query executada em {elapsed:.2f}s")
```

2. Execute e anote o tempo

#### Critérios de Sucesso:
- ✅ Tempo < 10 segundos (aceitável)
- ⚠️ Tempo entre 10-30s (revisar índices)
- ❌ Tempo > 30s (otimizar query)

---

### **Teste P2: Uso de Memória**

**Objetivo:** Verificar impacto do cache de EANs.

#### Observação:
- Monitorar uso de RAM do processo Python
- DataFrame agora tem 2 colunas extras: `TODOS_EANS` e `QTD_EANS`

#### Critérios de Sucesso:
- ✅ Aumento de memória < 20% comparado à versão anterior

---

## 🐛 Testes de Regressão

### **R1: Funcionalidades Anteriores**

Confirmar que nada quebrou:

- [ ] Filtro por Código funciona
- [ ] Filtro por Descrição funciona
- [ ] Filtro por Filial funciona
- [ ] Exportação Excel funciona
- [ ] Salvamento de imagem funciona
- [ ] Cache de busca funciona

---

## 📝 Checklist Final

### Antes do Deploy:

- [ ] Todos os testes funcionais passaram
- [ ] Edge cases testados
- [ ] Performance aceitável (< 10s)
- [ ] Logs não mostram erros
- [ ] Documentação atualizada
- [ ] Commit com mensagem descritiva

### Pós-Deploy (Produção):

- [ ] Monitorar logs por 24h
- [ ] Verificar feedback de usuários
- [ ] Confirmar quota da API não estourou
- [ ] Validar com produtos reais do negócio

---

## 🚨 Rollback Plan

### Se algo der errado:

1. **Reverter código:**
```bash
git revert HEAD
git push origin main
```

2. **Restaurar query antiga:**
- Remover CTEs `TodosEans` e `EansAgregados`
- Remover colunas `TODOS_EANS` e `QTD_EANS`

3. **Limpar cache:**
```python
# No terminal Python
import streamlit as st
st.cache_data.clear()
```

---

## 📞 Contatos em Caso de Problemas

**Suporte Técnico:**  
- Email: ti@empresa.com.br
- Slack: #suporte-winthor

**DBA Oracle:**  
- Email: dba@empresa.com.br
- Ramal: 1234

---

**Data de Criação:** Dezembro 2024  
**Versão:** 1.0  
**Responsável:** Equipe de TI