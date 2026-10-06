# ============================================================
# BLOCO 5 — LEITURA E CONSOLIDAÇÃO DO IMERG V07 (2021–2025)
# ============================================================

print("=" * 60)
print("CONSOLIDAÇÃO MULTITEMPORAL DO GPM IMERG V07")
print("=" * 60)


# ------------------------------------------------------------
# 1. ABERTURA EFICIENTE MULTI-ARQUIVO (LAZY LOADING)
# ------------------------------------------------------------
# Identificar o nome da variável mapeada no bloco anterior
var_alvo = globals().get("CONFIG_IMERG", {}).get("var_precip", "precipitation")

print(f"Indexando {len(arquivos_imerg)} arquivos NetCDF...")

# xr.open_mfdataset abre e concatena eficientemente pela dimensão temporal
imerg = xr.open_mfdataset(
    arquivos_imerg,
    combine="by_coords",
    parallel=False
)

# ------------------------------------------------------------
# 2. NORMALIZAÇÃO TEMPORAL E REMOÇÃO DE DUPLICATAS
# ------------------------------------------------------------
# Normalizar coordenada temporal para escala diária precisa
datas_normalizadas = pd.to_datetime(imerg["time"].values).normalize()
imerg = imerg.assign_coords(time=datas_normalizadas)

# Ordenação estrita por data
imerg = imerg.sortby("time")

# Remoção de datas duplicadas mantendo a primeira ocorrência
_, idx_unicos = np.unique(imerg["time"].values, return_index=True)
imerg = imerg.isel(time=np.sort(idx_unicos))


# ------------------------------------------------------------
# 3. RECORTE TEMPORAL PARA O PERÍODO DO ESTUDO
# ------------------------------------------------------------
imerg = imerg.sel(time=slice(DATA_INICIAL, DATA_FINAL))


# ------------------------------------------------------------
# 4. VALIDAÇÃO DOS METADADOS E EIXOS COORDENADOS
# ------------------------------------------------------------
coord_lat = next((c for c in ["lat", "latitude"] if c in imerg.coords), "lat")
coord_lon = next((c for c in ["lon", "longitude"] if c in imerg.coords), "lon")

dt_inicio = pd.Timestamp(imerg["time"].values[0]).strftime("%Y-%m-%d")
dt_fim = pd.Timestamp(imerg["time"].values[-1]).strftime("%Y-%m-%d")
n_dias = imerg.sizes["time"]

lat_min, lat_max = float(imerg[coord_lat].min()), float(imerg[coord_lat].max())
lon_min, lon_max = float(imerg[coord_lon].min()), float(imerg[coord_lon].max())

print("\n" + "=" * 60)
print("ESTRUTURA DO DATASET CONSOLIDADO")
print("=" * 60)
print(f"Período contínuo: {dt_inicio} a {dt_fim} ({n_dias} dias)")
print(f"Grade Espacial:   {imerg.sizes[coord_lon]} longitudes × {imerg.sizes[coord_lat]} latitudes")
print(f"Extensão Lon:     [{lon_min:.4f} a {lon_max:.4f}]")
print(f"Extensão Lat:     [{lat_min:.4f} a {lat_max:.4f}]")


# ------------------------------------------------------------
# 5. DIAGNÓSTICO E ESTATÍSTICAS BÁSICAS DE PRECIPITAÇÃO
# ------------------------------------------------------------
if var_alvo not in imerg.data_vars:
    # Fallback caso tenha sido lido direto sem o bloco 4
    var_alvo = "precipitation" if "precipitation" in imerg.data_vars else "precipitationCal"

precipitacao_imerg = imerg[var_alvo]
unidade = precipitacao_imerg.attrs.get("units", "mm/dia")

# Amostragem estatística rápida
val_min = float(precipitacao_imerg.min(skipna=True))
val_max = float(precipitacao_imerg.max(skipna=True))
val_med = float(precipitacao_imerg.mean(skipna=True))

print("\nVariável de Precipitação:")
print(f"  • Variável ativa: {var_alvo}")
print(f"  • Unidade:        {unidade}")
print(f"  • Dimensões:      {precipitacao_imerg.dims}")
print(f"  • Mínimo diário:  {val_min:.2f} {unidade}")
print(f"  • Máximo diário:  {val_max:.2f} {unidade}")
print(f"  • Média global:   {val_med:.2f} {unidade}")

# Verificação final de duplicatas no índice temporal
duplicatas_tempo = pd.Series(imerg["time"].values).duplicated().sum()
print(f"\nConsistência temporal: {duplicatas_tempo} duplicatas após tratamento.")
print("=" * 60)
print("IMERG V07 consolidado e pronto para pareamento espacial.")
print("=" * 60)
