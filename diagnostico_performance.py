"""
Script de Diagnóstico de Performance
Adicione este código temporariamente no app.py para medir gargalos
"""

import time
import sys

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
    
    # SEU CÓDIGO DO DATAFRAME AQUI
    event = st.dataframe(
        df_filtered,
        # ... suas configurações ...
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