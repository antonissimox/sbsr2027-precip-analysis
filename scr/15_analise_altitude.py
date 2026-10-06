# ============================================================
# BLOCO 15 — ANÁLISE DE INFLUÊNCIA TOPOGRÁFICA (MDE)
# Extração Altimétrica e Correlações Orográficas com Métricas
# ============================================================

import warnings
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import rasterio
from pyproj import Transformer
from scipy import stats
import seaborn as sns

warnings.filterwarnings("ignore")

print("=" * 60)
print("AVALIAÇÃO TOPOGRÁFICA: ALTITUDE (MDE) × DESEMPENHO IMERG")
print("=" * 60)

DIR_GRAF = SAIDA_DIR / "06_graficos"
DIR_GRAF.mkdir(parents=True, exist_ok=True)
DIR_ALT = SAIDA_DIR / "05_altitude"
DIR_ALT.mkdir(parents=True, exist_ok=True)


# ------------------------------------------------------------
# 1. LOCALIZAÇÃO ROBUSTA DO ARQUIVO MDE (GeoTIFF)
# ------------------------------------------------------------
candidatos_mde = [
    BASE_DIR / "data" / "MDE" / "MDE_Goias.tif",
    BASE_DIR / "MDE" / "MDE_Goias.tif",
    BASE_DIR / "MDE_GO.tif",
    Path("/content/drive/MyDrive/UFG/Doutorado/Artigos/SBSR/MDE_GO.tif")
]

MDE_PATH = next((p for p in candidatos_mde if p.exists()), None)

if MDE_PATH is None:
    raise FileNotFoundError(
        "Arquivo MDE (GeoTIFF) não localizado. "
        "Certifique-se de disponibilizar o arquivo em 'data/MDE/MDE_Goias.tif'."
    )

print(f"MDE localizado: {MDE_PATH.name}")


# ------------------------------------------------------------
# 2. INSPEÇÃO DE METADADOS DO RASTER
# ------------------------------------------------------------
with rasterio.open(MDE_PATH) as src:
    crs_mde = src.crs
    res_mde = src.res
    nodata_mde = src.nodata
    bounds_mde = src.bounds
    shape_mde = (src.height, src.width)

print("\nMetadados do Modelo Digital de Elevação:")
print(f"  • CRS:        {crs_mde}")
print(f"  • Resolução:  {res_mde[0]:.6f}, {res_mde[1]:.6f}")
print(f"  • Dimensões:  {shape_mde[0]} lin × {shape_mde[1]} col")
print(f"  • NoData:     {nodata_mde}")


# ------------------------------------------------------------
# 3. REPROJEÇÃO DE COORDENADAS (SE NECESSÁRIO)
# ------------------------------------------------------------
lons_orig = metricas_est_cont["longitude"].values
lats_orig = metricas_est_cont["latitude"].values

if crs_mde is None or str(crs_mde).upper().endswith("4326"):
    print("Coordenadas em conformidade nativa (EPSG:4326).")
    lons_amostra, lats_amostra = lons_orig, lats_orig
else:
    print(f"Reprojetando coordenadas de EPSG:4326 para {crs_mde}...")
    transformer = Transformer.from_crs("EPSG:4326", crs_mde, always_xy=True)
    lons_amostra, lats_amostra = transformer.transform(lons_orig, lats_orig)


# ------------------------------------------------------------
# 4. EXTRAÇÃO VETORIZADA EM LOTE (BATCH SAMPLING)
# ------------------------------------------------------------
coords_pts = list(zip(lons_amostra, lats_amostra))

with rasterio.open(MDE_PATH) as src:
    amostras = list(src.sample(coords_pts, indexes=1, masked=True))
    altitudes_vals = [
        float(val[0]) if (val is not None and not np.ma.is_masked(val[0]) and val[0] != nodata_mde) else np.nan
        for val in amostras
    ]

altitudes = pd.DataFrame({
    "codestacao": metricas_est_cont["codestacao"].values,
    "altitude_m": altitudes_vals
})

n_nulos = altitudes["altitude_m"].isna().sum()
if n_nulos > 0:
    print(f"[ALERTA] {n_nulos} estações situadas fora dos limites válidos do MDE.")
else:
    print("Altitude extraída com sucesso para 100% das estações.")

print("\nEstatísticas de Elevação das Estações (m):")
print(altitudes["altitude_m"].describe().round(1).to_string())


# ------------------------------------------------------------
# 5. ASSOCIAÇÃO COM MÉTRICAS E CORRELAÇÃO DE SPEARMAN
# ------------------------------------------------------------
metricas_est_cont_alt = pd.merge(metricas_est_cont, altitudes, on="codestacao", how="left")

metricas_alvo = ["pearson_r", "pbias", "rmse", "kge", "nse", "completude"]
resultados_correlacao = []

for m in metricas_alvo:
    sub = metricas_est_cont_alt[["altitude_m", m]].dropna()
    if len(sub) >= 5:
        rho, p = stats.spearmanr(sub["altitude_m"], sub[m])
        resultados_correlacao.append({
            "metrica": m,
            "spearman_rho": rho,
            "p_valor": p,
            "significativo_5%": p < 0.05
        })
    else:
        resultados_correlacao.append({
            "metrica": m, "spearman_rho": np.nan, "p_valor": np.nan, "significativo_5%": False
        })

df_correlacoes = pd.DataFrame(resultados_correlacao)

print("\n" + "=" * 60)
print("CORRELAÇÃO NÃO-PARAMÉTRICA DE SPEARMAN COM A ALTITUDE")
print("=" * 60)
tabela_corr_show = df_correlacoes.copy()
tabela_corr_show["spearman_rho"] = tabela_corr_show["spearman_rho"].map(lambda x: f"{x:.3f}")
tabela_corr_show["p_valor"] = tabela_corr_show["p_valor"].map(lambda x: f"{x:.4f}")

try:
    display(tabela_corr_show)
except NameError:
    print(tabela_corr_show.to_string(index=False))


# ------------------------------------------------------------
# 6. GRÁFICO 1: DISPERSÃO ALTITUDE × MÉTRICAS
# ------------------------------------------------------------
fig, axes = plt.subplots(1, 3, figsize=(15, 4.5))

pares_plot = [
    ("pearson_r", "Correlação de Pearson (r)", "#1f77b4"),
    ("pbias", "Viés Volumétrico PBIAS (%)", "#d9534f"),
    ("rmse", "RMSE (mm/dia)", "#2ca02c")
]

for ax, (ycol, rotulo_y, cor) in zip(axes, pares_plot):
    sub = metricas_est_cont_alt[["altitude_m", ycol]].dropna()
    
    ax.scatter(sub["altitude_m"], sub[ycol], s=55, color=cor, alpha=0.8, edgecolor="#212529", lw=0.6)
    
    if len(sub) >= 5:
        reg = stats.linregress(sub["altitude_m"], sub[ycol])
        x_lin = np.linspace(sub["altitude_m"].min(), sub["altitude_m"].max(), 100)
        ax.plot(x_lin, reg.slope * x_lin + reg.intercept, color="black", linestyle="--", lw=1.2)
        
        rho_val, p_val = stats.spearmanr(sub["altitude_m"], sub[ycol])
        sig = "*" if p_val < 0.05 else ""
        ax.set_title(f"{rotulo_y}\n(ρ = {rho_val:.2f}{sig})", fontweight="bold", pad=8)

    ax.set_xlabel("Altitude da Estação (m)", fontweight="bold")
    ax.set_ylabel(rotulo_y, fontweight="bold")
    sns.despine(ax=ax)

fig.suptitle("Sensibilidade Orográfica das Métricas de Validação", y=1.03, fontweight="bold")
fig.savefig(DIR_GRAF / "06_altitude_vs_metricas.png", dpi=300)
plt.show()
plt.close(fig)


# ------------------------------------------------------------
# 7. GRÁFICO 2: BOXPLOT POR FAIXA HIPSOMÉTRICA
# ------------------------------------------------------------
# Intervalos hipsométricos seguros cobrindo toda a topografia de Goiás
metricas_est_cont_alt["faixa_altitude"] = pd.cut(
    metricas_est_cont_alt["altitude_m"],
    bins=[-np.inf, 400, 600, 800, np.inf],
    labels=["< 400 m", "400–600 m", "600–800 m", "> 800 m"]
)

fig, axes = plt.subplots(1, 3, figsize=(15, 4.5))

for ax, (ycol, rotulo_y, cor) in zip(axes, pares_plot):
    sns.boxplot(
        x="faixa_altitude", y=ycol, data=metricas_est_cont_alt,
        ax=ax, color=cor, width=0.45
    )
    if ycol == "pbias":
        ax.axhline(0, color="black", linestyle="--", lw=1.0)

    ax.set_title(rotulo_y, fontweight="bold", pad=8)
    ax.set_xlabel("Faixa Hipsométrica", fontweight="bold")
    ax.set_ylabel("")
    sns.despine(ax=ax)

fig.suptitle("Distribuição do Desempenho por Faixas Altimétricas", y=1.03, fontweight="bold")
fig.savefig(DIR_GRAF / "07_boxplot_metricas_faixa_altitude.png", dpi=300)
plt.show()
plt.close(fig)


# ------------------------------------------------------------
# 8. EXPORTAÇÃO DOS PRODUTOS
# ------------------------------------------------------------
altitudes.to_csv(DIR_ALT / "altitude_estacoes.csv", index=False, encoding="utf-8-sig")
metricas_est_cont_alt.to_csv(DIR_ALT / "metricas_por_estacao_com_altitude.csv", index=False, encoding="utf-8-sig")
df_correlacoes.to_csv(DIR_ALT / "correlacoes_altitude.csv", index=False, encoding="utf-8-sig")

print("=" * 60)
print(f"Arquivos e correlações topográficas salvos com sucesso em:\n{DIR_ALT}")
print("=" * 60)
