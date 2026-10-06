# ============================================================
# BLOCO 6 — ASSOCIAÇÃO ESPACIAL CEMADEN × GPM IMERG V07
# Amostragem por Vizinho Mais Próximo (Nearest Neighbor)
# ============================================================

print("=" * 60)
print("PAREAMENTO ESPACIAL: ESTAÇÕES CEMADEN -> GRADE IMERG")
print("=" * 60)


# ------------------------------------------------------------
# 1. FUNÇÃO GEODÉSICA DE HAVERSINE (DISTÂNCIA EM KM)
# ------------------------------------------------------------
def calcular_haversine_np(lat1, lon1, lat2, lon2):
    """Calcula a distância ortodrômica entre pares de coordenadas (em km)."""
    R = 6371.0  # Raio médio da Terra em km
    phi1, phi2 = np.radians(lat1), np.radians(lat2)
    dphi = np.radians(lat2 - lat1)
    dlambda = np.radians(lon2 - lon1)

    a = (
        np.sin(dphi / 2.0) ** 2
        + np.cos(phi1) * np.cos(phi2) * np.sin(dlambda / 2.0) ** 2
    )
    return 2.0 * R * np.arcsin(np.sqrt(a))


# ------------------------------------------------------------
# 2. SELEÇÃO DAS COORDENADAS DAS ESTAÇÕES
# ------------------------------------------------------------
estacoes = estacoes_elegiveis[
    [
        "codestacao",
        "municipio",
        "nomeestacao",
        "latitude",
        "longitude",
        "completude"
    ]
].copy()

# Criação de DataArrays indexados pela dimensão 'station'
da_lat = xr.DataArray(estacoes["latitude"].values, dims="station")
da_lon = xr.DataArray(estacoes["longitude"].values, dims="station")

var_alvo = globals().get("CONFIG_IMERG", {}).get("var_precip", "precipitation")
if var_alvo not in imerg:
    var_alvo = "precipitationCal" if "precipitationCal" in imerg else "precipitation"


# ------------------------------------------------------------
# 3. EXTRAÇÃO VETORIZADA DO PIXEL MAIS PRÓXIMO
# ------------------------------------------------------------
coord_lat_nome = next((c for c in ["lat", "latitude"] if c in imerg.coords), "lat")
coord_lon_nome = next((c for c in ["lon", "longitude"] if c in imerg.coords), "lon")

# Amostra espacial no centróide do pixel mais próximo
selecao_pixels = imerg[var_alvo].sel(
    {coord_lat_nome: da_lat, coord_lon_nome: da_lon},
    method="nearest"
)

# Extração das coordenadas do centro do pixel selecionado
lat_centro_pixel = selecao_pixels[coord_lat_nome].values
lon_centro_pixel = selecao_pixels[coord_lon_nome].values


# ------------------------------------------------------------
# 4. AUDITORIA GEOGRÁFICA DO PAREAMENTO
# ------------------------------------------------------------
dist_km = calcular_haversine_np(
    estacoes["latitude"].values,
    estacoes["longitude"].values,
    lat_centro_pixel,
    lon_centro_pixel
)

pareamento = estacoes.copy()
pareamento["lat_imerg"] = lat_centro_pixel
pareamento["lon_imerg"] = lon_centro_pixel
pareamento["distancia_centroide_km"] = dist_km


# ------------------------------------------------------------
# 5. DIAGNÓSTICO E ESTATÍSTICAS DO PAREAMENTO
# ------------------------------------------------------------
n_estacoes = len(pareamento)
n_pixels_unicos = pareamento[["lat_imerg", "lon_imerg"]].drop_duplicates().shape[0]

print(f"Total de estações associadas: {n_estacoes}")
print(f"Pixels IMERG discretos ocupados: {n_pixels_unicos}")
print(f"Razão estação/pixel: {n_estacoes / n_pixels_unicos:.2f} estações/pixel (efeito de adensamento urbano)")

print("\n" + "=" * 60)
print("DISTÂNCIA ESTAÇÃO IN SITU -> CENTRÓIDE DO PIXEL (KM)")
print("=" * 60)
print(f"  • Mínima:  {pareamento['distancia_centroide_km'].min():.2f} km")
print(f"  • Máxima:  {pareamento['distancia_centroide_km'].max():.2f} km")
print(f"  • Média:   {pareamento['distancia_centroide_km'].mean():.2f} km")
print(f"  • Mediana: {pareamento['distancia_centroide_km'].median():.2f} km")
print(f"  • Desvio Padrão: {pareamento['distancia_centroide_km'].std():.2f} km")


# ------------------------------------------------------------
# 6. TABELA DE VISUALIZAÇÃO
# ------------------------------------------------------------
tabela_ord = pareamento.sort_values("distancia_centroide_km")

try:
    display(tabela_ord.head(10))
except NameError:
    print("\nPrimeiras 10 estações ordenadas por distância:")
    print(tabela_ord.head(10).to_string(index=False))


# ------------------------------------------------------------
# 7. EXPORTAÇÃO
# ------------------------------------------------------------
arquivo_pareamento = SAIDA_DIR / "01_auditoria" / "pareamento_CEMADEN_IMERG.csv"
pareamento.to_csv(arquivo_pareamento, index=False, encoding="utf-8-sig")

print("\n" + "=" * 60)
print(f"Tabela de pareamento salva em:\n{arquivo_pareamento}")
print("=" * 60)
