# ANTES (❌ Erro):
codprod = row['CODPROD']  # np.int64(731)
conn.execute(query, {'codprod': codprod})  # ❌ DPY-3002

# DEPOIS (✅ Funciona):
codprod = convert_to_python_type(row['CODPROD'])  # int(731)
conn.execute(query, {'codprod': codprod})  # ✅ OK!