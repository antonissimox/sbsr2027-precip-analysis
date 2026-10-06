# ============================================================
# BLOCO 7 — PAREAMENTO TEMPORAL CEMADEN × GPM IMERG V07
# Construção da Base Diária Pareada (2021–2025)
# ============================================================

print("=" * 60)
print("PAREAMENTO TEMPORAL: CEMADEN (IN SITU) × IMERG (SATÉLITE)")
print("=" * 60)


# ------------------------------------------------------------
# 1. PREPARAÇÃO DA BASE DE REFERÊNCIA CEMADEN
# ------------------------------------------------------------
# Manter apenas observações consistentes e válidas (QC aprovado)
df_cemaden = (
    cemaden_elegivel[cemaden_elegivel["observacao_valida"]]
    [["codestacao", "data", "precipitacao"]]
    .copy()
    .rename(columns={"precipitacao": "precipitacao_cemaden"})
)
df_cemaden["data"] = pd.to_datetime(df_cemaden["data"]).dt.normalize()


# ------------------------------------------------------------
# 2. EXTRAÇÃO VETORIZADA INDEXADA POR ESTAÇÃO NO XARRAY
# ------------------------------------------------------------
var_alvo = globals().get("CONFIG_IMERG", {}).get("var_precip", "precipitation")
if var_alvo not in imerg:
    var_alvo = "precipitationCal" if "precipitationCal" in imerg else "precipitation"

coord_lat_nome = next((c for c in ["lat", "latitude"] if c in imerg.coords), "lat")
coord_lon_nome = next((c for c in ["lon", "longitude"] if c in imerg.coords), "lon")

# Criamos a dimensão 'station' já vinculada ao código real da estação
da_lat = xr.DataArray(
    pareamento["latitude"].values,
    dims="station",
    coords={"station": pareamento["codestacao"].values}
)
da_lon = xr.DataArray(
    pareamento["longitude"].values,
    dims="station",
    coords={"station": pareamento["codestacao"].values}
)

# Amostragem espacial nos centróides vizinhos mais próximos
da_imerg_pontual = imerg[var_alvo].sel(
    {coord_lat_nome: da_lat, coord_lon_nome: da_lon},
    method="nearest"
)


# ------------------------------------------------------------
# 3. CONVERSÃO DIRETA PARA DATAFRAME LIMPO
# ------------------------------------------------------------
df_imerg = (
    da_imerg_pontual
    .to_dataframe(name="precipitacao_imerg")
    .reset_index()
)

# Renomear e normalizar coordenadas temporais
coord_tempo_col = next((c for c in ["time", "datetime", "date"] if c in df_imerg.columns), "time")
df_imerg["data"] = pd.to_datetime(df_imerg[coord_tempo_col]).dt.normalize()
df_imerg["codestacao"] = df_imerg["station"]

# Descartar colunas intermediárias para economia de RAM
df_imerg = df_imerg[["codestacao", "data", "precipitacao_imerg"]].dropna(subset=["precipitacao_imerg"])


# ------------------------------------------------------------
# 4. JUNÇÃO TEMPORAL (INNER JOIN: PARIDADE EXATA DIA-A-DIA)
# ------------------------------------------------------------
base_validacao = pd.merge(
    df_cemaden,
    df_imerg,
    on=["codestacao", "data"],
    how="inner"
)

# Adicionar metadados geográficos da estação para facilitar auditorias
base_validacao = pd.merge(
    base_validacao,
    pareamento[["codestacao", "municipio", "nomeestacao", "latitude", "longitude", "distancia_centroide_km"]],
    on="codestacao",
    how="left"
)

# Ordenação cronológica estrita por estação
base_validacao = base_validacao.sort_values(["codestacao", "data"]).reset_index(drop=True)


# ------------------------------------------------------------
# 5. DIAGNÓSTICO E AUDITORIA DA BASE PAREADA
# ------------------------------------------------------------
n_estacoes_pareadas = base_validacao["codestacao"].nunique()
n_pares = len(base_validacao)
dt_min = base_validacao["data"].min().date()
dt_max = base_validacao["data"].max().date()

print("\n" + "=" * 60)
print("AUDITORIA DA BASE CONSOLIDADA (CEMADEN x IMERG)")
print("=" * 60)
print(f"Estações monitoradas: {n_estacoes_pareadas}")
print(f"Total de pares diários (estação-dia): {n_pares:,}")
print(f"Janela temporal conjunta: {dt_min} a {dt_max}")
print(f"Valores nulos em CEMADEN: {base_validacao['precipitacao_cemaden'].isna().sum()}")
print(f"Valores nulos em IMERG:   {base_validacao['precipitacao_imerg'].isna().sum()}")

# Amostragem estatística rápida
print("\nEstatísticas básicas de precipitação (mm/dia):")
resumo_estat = base_validacao[["precipitacao_cemaden", "precipitacao_imerg"]].describe().T[["mean", "std", "min", "50%", "max"]]
resumo_estat.columns = ["Média", "Desv. Pad.", "Mín.", "Mediana", "Máx."]
print(resumo_estat.to_string())


# ------------------------------------------------------------
# 6. EXIBIÇÃO DA AMOSTRA
# ------------------------------------------------------------
print("\nAmostra dos registros pareados:")
try:
    display(base_validacao.head(10))
except NameError:
    print(base_validacao.head(10).to_string(index=False))


# ------------------------------------------------------------
# 7. EXPORTAÇÃO
# ------------------------------------------------------------
arquivo_saida = SAIDA_DIR / "01_auditoria" / "base_pareada_CEMADEN_IMERG.csv"
base_validacao.to_csv(arquivo_saida, index=False, encoding="utf-8-sig")

print("\n" + "=" * 60)
print(f"Base pareada exportada com sucesso:\n{arquivo_saida}")
print("=" * 60)
