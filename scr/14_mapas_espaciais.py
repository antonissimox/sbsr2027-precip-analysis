# ============================================================
# BLOCO 14 — MAPAS ESPACIAIS DAS MÉTRICAS CARTOGRÁFICAS
# Representação Geográfica com Cartopy e Matplotlib (300 DPI)
# ============================================================

import sys
import warnings
from pathlib import Path

# Verificação amigável de instalação do Cartopy
try:
    import cartopy.crs as ccrs
    import cartopy.feature as cfeature
    from cartopy.mpl.gridliner import LATITUDE_FORMATTER, LONGITUDE_FORMATTER
except ImportError:
    print("[AVISO] Cartopy não encontrado. Instalando dependência geoespacial...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "cartopy"])
    import cartopy.crs as ccrs
    import cartopy.feature as cfeature
    from cartopy.mpl.gridliner import LATITUDE_FORMATTER, LONGITUDE_FORMATTER

import matplotlib.pyplot as plt
from matplotlib.colors import TwoSlopeNorm
import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

plt.rcParams["figure.dpi"] = 110
plt.rcParams["savefig.dpi"] = 300
plt.rcParams["font.sans-serif"] = "DejaVu Sans"

DIR_MAPAS = SAIDA_DIR / "07_mapas"
DIR_MAPAS.mkdir(parents=True, exist_ok=True)


# ------------------------------------------------------------
# 1. FUNÇÃO CARTOGRÁFICA MODULAR
# ------------------------------------------------------------
def plotar_mapa_metrica(
    tabela,
    coluna,
    titulo,
    cmap="RdYlGn",
    vmin=None,
    vmax=None,
    center=None,
    arquivo_saida=None,
    rotulo_cbar=None
):
    """
    Plota um mapa cartográfico de Goiás com as estações coloridas
    pelo valor da métrica estatística selecionada.
    """
    fig = plt.figure(figsize=(8.5, 8.0))
    ax = fig.add_subplot(1, 1, 1, projection=ccrs.PlateCarree())

    # Extensão geográfica de Goiás e Distrito Federal com margem
    ax.set_extent([-53.5, -45.5, -19.8, -12.2], crs=ccrs.PlateCarree())

    # Feições geográficas básicas
    ax.add_feature(cfeature.LAND, facecolor="#f8f9fa", zorder=1)
    ax.add_feature(cfeature.OCEAN, facecolor="#e9ecef", zorder=1)
    
    # Limites estaduais e internacionais
    try:
        estados = cfeature.NaturalEarthFeature(
            category="cultural",
            name="admin_1_states_provinces_lines",
            scale="50m",
            facecolor="none"
        )
        ax.add_feature(estados, edgecolor="#495057", linewidth=0.7, zorder=2)
    except Exception:
        ax.add_feature(cfeature.STATES, edgecolor="#495057", linewidth=0.7, zorder=2)

    ax.add_feature(cfeature.BORDERS, edgecolor="#212529", linewidth=0.9, zorder=2)
    ax.add_feature(cfeature.RIVERS, edgecolor="#a5d8ff", linewidth=0.4, zorder=2)

    # Normalização da escala de cores
    if center is not None:
        val_min = vmin if vmin is not None else float(tabela[coluna].min())
        val_max = vmax if vmax is not None else float(tabela[coluna].max())
        norm = TwoSlopeNorm(vmin=val_min, vcenter=center, vmax=val_max)
    else:
        norm = plt.Normalize(vmin=vmin, vmax=vmax)

    # Plotagem dos pontos in situ
    sc = ax.scatter(
        tabela["longitude"],
        tabela["latitude"],
        c=tabela[coluna],
        s=85,
        cmap=cmap,
        norm=norm,
        edgecolor="#1a1a1a",
        linewidth=0.6,
        alpha=0.92,
        transform=ccrs.PlateCarree(),
        zorder=5
    )

    # Barra de cores vertical
    cbar = fig.colorbar(
        sc, ax=ax, orientation="vertical",
        fraction=0.035, pad=0.04, shrink=0.75
    )
    cbar.set_label(rotulo_cbar or coluna, fontsize=10, fontweight="bold")
    cbar.ax.tick_params(labelsize=9)

    # Grade de coordenadas com anotações formatadas
    gl = ax.gridlines(
        crs=ccrs.PlateCarree(),
        draw_labels=True,
        linewidth=0.4,
        color="#ced4da",
        linestyle="--",
        zorder=3
    )
    gl.top_labels = False
    gl.right_labels = False
    gl.xformatter = LONGITUDE_FORMATTER
    gl.yformatter = LATITUDE_FORMATTER
    gl.xlabel_style = {"size": 8.5, "color": "#495057"}
    gl.ylabel_style = {"size": 8.5, "color": "#495057"}

    ax.set_title(titulo, fontsize=11, fontweight="bold", pad=10)

    if arquivo_saida:
        fig.savefig(arquivo_saida, bbox_inches="tight", dpi=300)
    
    plt.show()
    plt.close(fig)


# ------------------------------------------------------------
# 2. MAPA 1 — CORRELAÇÃO DE PEARSON (r)
# ------------------------------------------------------------
plotar_mapa_metrica(
    metricas_est_cont,
    coluna="pearson_r",
    titulo="Correlação de Pearson (r) — CEMADEN × GPM IMERG V07 (2021–2025)",
    cmap="YlGnBu",
    vmin=0.35, vmax=0.75,
    arquivo_saida=DIR_MAPAS / "01_mapa_pearson_r.png",
    rotulo_cbar="Pearson r"
)


# ------------------------------------------------------------
# 3. MAPA 2 — VIÉS VOLUMÉTRICO PERCENTUAL (PBIAS)
# ------------------------------------------------------------
# RdBu_r: tons quentes (vermelho) = subestimação / seca; azul = superestimação
plotar_mapa_metrica(
    metricas_est_cont,
    coluna="pbias",
    titulo="Viés Percentual PBIAS (%) — CEMADEN × GPM IMERG V07 (2021–2025)",
    cmap="RdBu_r",
    vmin=-30.0, vmax=30.0, center=0.0,
    arquivo_saida=DIR_MAPAS / "02_mapa_pbias.png",
    rotulo_cbar="PBIAS (%)"
)


# ------------------------------------------------------------
# 4. MAPA 3 — ERRO MÉDIO QUADRÁTICO (RMSE)
# ------------------------------------------------------------
plotar_mapa_metrica(
    metricas_est_cont,
    coluna="rmse",
    titulo="Erro Quadrático Médio (RMSE) — CEMADEN × GPM IMERG V07 (2021–2025)",
    cmap="YlOrRd",
    vmin=6.0, vmax=16.0,
    arquivo_saida=DIR_MAPAS / "03_mapa_rmse.png",
    rotulo_cbar="RMSE (mm/dia)"
)


# ------------------------------------------------------------
# 5. MAPA 4 — EFICIÊNCIA DE KLING-GUPTA (KGE)
# ------------------------------------------------------------
plotar_mapa_metrica(
    metricas_est_cont,
    coluna="kge",
    titulo="Eficiência de Kling–Gupta (KGE) — CEMADEN × GPM IMERG V07 (2021–2025)",
    cmap="Viridis",
    vmin=0.10, vmax=0.70,
    arquivo_saida=DIR_MAPAS / "04_mapa_kge.png",
    rotulo_cbar="KGE"
)

print("=" * 60)
print(f"Mapas cartográficos em 300 DPI gerados com sucesso em:\n{DIR_MAPAS}")
print("=" * 60)
