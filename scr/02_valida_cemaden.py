# ============================================================
# BLOCO 2 — LEITURA E VALIDAÇÃO DOS DADOS CEMADEN
# ============================================================

print("=" * 60)
print("LEITURA E TRATAMENTO DOS DADOS CEMADEN")
print("=" * 60)


# ------------------------------------------------------------
# 1. CARREGAR DADOS DIÁRIOS
# ------------------------------------------------------------
if not CEMADEN_DIARIO.exists():
    raise FileNotFoundError(f"Arquivo diário não encontrado em: {CEMADEN_DIARIO}")

cemaden = pd.read_csv(CEMADEN_DIARIO, low_memory=False)
print(f"Registros brutos carregados: {len(cemaden):,}")


# ------------------------------------------------------------
# 2. PADRONIZAR NOMES DAS COLUNAS
# ------------------------------------------------------------
cemaden.columns = cemaden.columns.str.strip().str.lower()

# Dicionário de possíveis sinônimos de colunas do CEMADEN
alternativas = {
    "datahora": "data",
    "datamedida": "data",
    "valormedida": "precipitacao",
    "chuva": "precipitacao",
    "precipitacao_mm": "precipitacao",
    "cod_estacao": "codestacao",
    "estacao": "codestacao",
}
cemaden = cemaden.rename(columns={k: v for k, v in alternativas.items() if k in cemaden.columns})

colunas_necessarias = [
    "codestacao",
    "municipio",
    "nomeestacao",
    "uf",
    "latitude",
    "longitude",
    "data",
    "precipitacao"
]

faltantes = [c for c in colunas_necessarias if c not in cemaden.columns]
if faltantes:
    raise ValueError(f"Colunas obrigatórias ausentes no arquivo: {', '.join(faltantes)}")


# ------------------------------------------------------------
# 3. CONVERSÃO DE TIPOS E NORMALIZAÇÃO TEMPORAL
# ------------------------------------------------------------
# Normaliza a data para escala diária (remove horas/minutos caso existam)
cemaden["data"] = pd.to_datetime(cemaden["data"], errors="coerce").dt.normalize()
cemaden["precipitacao"] = pd.to_numeric(cemaden["precipitacao"], errors="coerce")

# Coordenadas numéricas
cemaden["latitude"] = pd.to_numeric(cemaden["latitude"], errors="coerce")
cemaden["longitude"] = pd.to_numeric(cemaden["longitude"], errors="coerce")


# ------------------------------------------------------------
# 4. FILTRAGEM TEMPORAL
# ------------------------------------------------------------
cemaden = cemaden[
    (cemaden["data"] >= DATA_INICIAL) & 
    (cemaden["data"] <= DATA_FINAL)
].copy()


# ------------------------------------------------------------
# 5. CONTROLE DE QUALIDADE (QC)
# ------------------------------------------------------------
# Válido: valores não nulos e >= 0 mm/dia
cemaden["observacao_valida"] = (
    cemaden["precipitacao"].notna() & 
    (cemaden["precipitacao"] >= 0)
)


# ------------------------------------------------------------
# 6. AUDITORIA E RELATÓRIO DE CONSISTÊNCIA
# ------------------------------------------------------------
duplicatas = cemaden.duplicated(subset=["codestacao", "data"]).sum()

print("\n" + "=" * 60)
print("RESUMO DA AUDITORIA (CEMADEN)")
print("=" * 60)
print(f"Período analisado:    {cemaden['data'].min().date()} → {cemaden['data'].max().date()}")
print(f"Estações monitoradas: {cemaden['codestacao'].nunique()}")
print(f"Registros no período: {len(cemaden):,}")
print(f"Observações válidas:  {cemaden['observacao_valida'].sum():,} ({cemaden['observacao_valida'].mean():.1%})")
print(f"Observações com falha: {(~cemaden['observacao_valida']).sum():,}")
print(f"Duplicatas (estação/dia): {duplicatas:,}")


# ------------------------------------------------------------
# 7. METADADOS E COMPLETUDE POR ESTAÇÃO
# ------------------------------------------------------------
dias_esperados = (DATA_FINAL - DATA_INICIAL).days + 1

resumo_estacoes = (
    cemaden.groupby("codestacao")
    .agg(
        municipio=("municipio", "first"),
        nomeestacao=("nomeestacao", "first"),
        latitude=("latitude", "first"),
        longitude=("longitude", "first"),
        registros=("data", "size"),
        validos=("observacao_valida", "sum")
    )
    .reset_index()
)

# Completude frente aos dias esperados no período completo
resumo_estacoes["completude"] = resumo_estacoes["validos"] / dias_esperados

print("\nEstações com maior completude no período:")
tabela_top = resumo_estacoes.sort_values("completude", ascending=False).head(10)

try:
    # Se estiver no Jupyter/Colab
    display(tabela_top)
except NameError:
    # Se estiver rodando como script puro no terminal
    print(tabela_top.to_string(index=False))
