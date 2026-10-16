# -*- coding: utf-8 -*-
"""
Validação Espacial do GPM IMERG V07 no Cerrado:
Efeito da Altitude nos Vieses de Precipitação em Goiás (SBSR 2027)

"""

import os
import glob
import numpy as np
import pandas as pd
import xarray as xr
from scipy import stats
from scipy.stats import pearsonr, spearmanr, linregress
from sklearn.metrics import mean_absolute_error, mean_squared_error
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.colors import TwoSlopeNorm
import geopandas as gpd

# ==============================================================================
# CONFIGURAÇÕES E DIRETÓRIOS
# ==============================================================================
BASE_DIR = "/content/drive/MyDrive/UFG/Doutorado/Artigos/SBSR/IMERG_Goias_CEMADEN"
PASTA_NC = "/content/drive/MyDrive/UFG/Doutorado/Artigos/SBSR/CBRS_IMERG_Goias/IMERG_Goias"

ARQ_LIMPO     = os.path.join(BASE_DIR, "CEMADEN_Goias_diario_limpo_2021_2025.xlsx")
ARQ_AUDITORIA = os.path.join(BASE_DIR, "CEMADEN_Goias_auditoria_estacoes_2021_2025.xlsx")
ARQ_COORDS    = os.path.join(BASE_DIR, "estacoes_41_coords.csv")
ARQ_ALT       = os.path.join(BASE_DIR, "estacoes_41_altitude.csv")
ARQ_PARES     = os.path.join(BASE_DIR, "pares_diarios_obs_sim_2021_2025.csv")
ARQ_METRICAS  = os.path.join(BASE_DIR, "metricas_pooled_41_estacoes_completo.csv")

# ==============================================================================
# 1. CONTROLE DE QUALIDADE E CRITÉRIO DUPLO (A ∩ B) -> 41 ESTAÇÕES
# ==============================================================================
print("1. Processando controle de qualidade CEMADEN...")
df_cemaden = pd.read_excel(ARQ_LIMPO)
df_cemaden["data"] = pd.to_datetime(df_cemaden["data"])
df_cemaden["precipitacao_mm"] = pd.to_numeric(df_cemaden["precipitacao_mm"], errors="coerce")
df_cemaden = df_cemaden.dropna(subset=["data", "precipitacao_mm"])

auditoria = pd.read_excel(ARQ_AUDITORIA, sheet_name="auditoria_estacao_ano")

# Critério A: completude >= 80% em pelo menos 4 anos
crit_A = set(auditoria.groupby("codigo")["elegivel_80"].sum().loc[lambda x: x >= 4].index)

# Critério B: completude pooled >= 80% no período 2021-2025
agg = auditoria.groupby("codigo").agg(dv=("dias_validos", "sum"), de=("dias_esperados", "sum"))
agg["pct"] = agg["dv"] / agg["de"] * 100
crit_B = set(agg[agg["pct"] >= 80].index)

estacoes_41 = sorted(crit_A & crit_B)
print(f"Estações elegíveis (A ∩ B): {len(estacoes_41)}")

df_cemaden_41 = df_cemaden[df_cemaden["codigo"].isin(estacoes_41)].copy()
df_cemaden_41["codigo"] = df_cemaden_41["codigo"].astype(str)

coords_41 = (
    df_cemaden_41[["codigo", "estacao", "latitude", "longitude"]]
    .drop_duplicates(subset=["codigo"])
    .reset_index(drop=True)
)
coords_41.to_csv(ARQ_COORDS, index=False)

# ==============================================================================
# 2. EXTRAÇÃO DA ALTITUDE (SRTM 30m VIA GOOGLE EARTH ENGINE)
# ==============================================================================
if not os.path.exists(ARQ_ALT):
    print("\n2. Extraindo altitude das 41 estações via GEE (SRTM 30m)...")
    import ee
    try:
        ee.Initialize()
    except Exception:
        ee.Authenticate(auth_mode='notebook')
        ee.Initialize()

    srtm = ee.Image("USGS/SRTMGL1_003")
    features = [
        ee.Feature(
            ee.Geometry.Point([float(r["longitude"]), float(r["latitude"])]),
            {"codigo": str(r["codigo"])}
        )
        for _, r in coords_41.iterrows()
    ]
    amostra = srtm.sampleRegions(collection=ee.FeatureCollection(features), scale=30, geometries=False)
    dados = amostra.getInfo()["features"]
    df_alt = pd.DataFrame([{"codigo": str(f["properties"]["codigo"]), "altitude_m": f["properties"]["elevation"]} for f in dados])
    df_alt_full = coords_41.merge(df_alt, on="codigo", how="left")
    df_alt_full.to_csv(ARQ_ALT, index=False)
else:
    print("\n2. Arquivo de altitude já existente.")
    df_alt_full = pd.read_csv(ARQ_ALT, dtype={"codigo": str})

# ==============================================================================
# 3. PAREAMENTO ESPAÇO-TEMPORAL CEMADEN × IMERG V07 (NEAREST NEIGHBOR)
# ==============================================================================
if not os.path.exists(ARQ_PARES):
    print("\n3. Realizando pareamento espaço-temporal com arquivos NetCDF do IMERG...")
    pares_diarios = []
    coords = pd.read_csv(ARQ_COORDS, dtype={"codigo": str})

    for ano in range(2021, 2026):
        arq_nc = os.path.join(PASTA_NC, f"IMERG_Goias_{ano}.nc")
        if not os.path.exists(arq_nc):
            continue

        ds = xr.open_dataset(arq_nc)
        var = next((v for v in ds.data_vars if "precip" in v.lower()), list(ds.data_vars)[0])
        df_ano = df_cemaden_41[df_cemaden_41["data"].dt.year == ano]

        for _, row in coords.iterrows():
            cod = str(row["codigo"])
            lat, lon = float(row["latitude"]), float(row["longitude"])
            df_est = df_ano[df_ano["codigo"] == cod]
            if df_est.empty:
                continue

            try:
                serie = ds.sel(lon=lon, lat=lat, method="nearest")
                df_sat = serie[[var]].to_dataframe().reset_index()
                df_sat = df_sat.rename(columns={"time": "data", var: "chuva_imerg"})
                df_sat["data"] = pd.to_datetime(df_sat["data"]).dt.normalize()

                df_merge = pd.merge(
                    df_est[["codigo", "data", "precipitacao_mm"]],
                    df_sat[["data", "chuva_imerg"]],
                    on="data", how="inner"
                ).dropna()
                df_merge["ano"] = ano
                pares_diarios.append(df_merge)
            except Exception as e:
                print(f"Erro na estação {cod}: {e}")
        ds.close()

    df_pares = pd.concat(pares_diarios, ignore_index=True)
    df_pares.to_csv(ARQ_PARES, index=False)
else:
    print("\n3. Carregando pares diários já consolidados...")
    df_pares = pd.read_csv(ARQ_PARES, dtype={"codigo": str})
    df_pares["data"] = pd.to_datetime(df_pares["data"])

print(f"Total de pares diários analisados: {len(df_pares):,}")

# ==============================================================================
# 4. FUNÇÕES DE MÉTRICAS E ESTATÍSTICA GLOBAL
# ==============================================================================
def calc_kge(obs, sim):
    if len(obs) < 2 or np.std(obs) == 0 or np.std(sim) == 0:
        return np.nan
    r = np.corrcoef(obs, sim)[0, 1]
    alpha = np.std(sim) / np.std(obs)
    beta = np.mean(sim) / np.mean(obs)
    return 1.0 - np.sqrt((r - 1.0)**2 + (alpha - 1.0)**2 + (beta - 1.0)**2)

def calc_nse(obs, sim):
    denom = np.sum((obs - np.mean(obs))**2)
    return 1.0 - (np.sum((sim - obs)**2) / denom) if denom > 0 else np.nan

obs_g = df_pares["precipitacao_mm"].values
sim_g = df_pares["chuva_imerg"].values

r_g, _ = pearsonr(obs_g, sim_g)
pbias_g = ((sim_g.sum() - obs_g.sum()) / obs_g.sum()) * 100
rmse_g = np.sqrt(mean_squared_error(obs_g, sim_g))
mae_g = mean_absolute_error(obs_g, sim_g)
kge_g = calc_kge(obs_g, sim_g)
nse_g = calc_nse(obs_g, sim_g)
slope_g, intercept_g, _, _, _ = linregress(obs_g, sim_g)

print("\n" + "="*60 + "\nMÉTRICAS GLOBAIS (ARTIGO - SEÇÃO 3)\n" + "="*60)
print(f"Pares diários: {len(df_pares):,}")
print(f"Pearson r:     {r_g:.3f} (R² = {r_g**2:.3f})")
print(f"KGE:           {kge_g:.3f}")
print(f"NSE:           {nse_g:.3f}")
print(f"PBIAS:         {pbias_g:+.2f} %")
print(f"MAE:           {mae_g:.2f} mm/dia")
print(f"RMSE:          {rmse_g:.2f} mm/dia")
print(f"Ajuste linear: sim = {slope_g:.3f}·obs + {intercept_g:.2f}")

# Tabela 1: Índices Categóricos por Limiar
limiares = [0.1, 1.0, 10.0, 20.0, 50.0]
linhas_cat = []
n_tot = len(obs_g)
for lim in limiares:
    hits = int(np.sum((obs_g >= lim) & (sim_g >= lim)))
    miss = int(np.sum((obs_g >= lim) & (sim_g < lim)))
    fa   = int(np.sum((obs_g < lim) & (sim_g >= lim)))
    corr = int(np.sum((obs_g < lim) & (sim_g < lim)))
    pod  = hits / (hits + miss) if (hits + miss) > 0 else np.nan
    far  = fa / (hits + fa) if (hits + fa) > 0 else np.nan
    csi  = hits / (hits + miss + fa) if (hits + miss + fa) > 0 else np.nan
    hr   = (hits + miss) * (hits + fa) / n_tot
    ets  = (hits - hr) / (hits + miss + fa - hr) if (hits + miss + fa - hr) > 0 else np.nan
    hss  = 2 * (hits * corr - miss * fa) / ((hits + miss)*(miss + corr) + (hits + fa)*(fa + corr))
    linhas_cat.append({"Limiar (mm/dia)": lim, "POD": round(pod, 2), "FAR": round(far, 2),
                       "CSI": round(csi, 2), "ETS": round(ets, 2), "HSS": round(hss, 2)})

df_cat = pd.DataFrame(linhas_cat)
print("\nTabela 1 — Índices Categóricos:")
print(df_cat.to_string(index=False))

# ==============================================================================
# 4.1. ANÁLISE SAZONAL (HEMISFÉRIO SUL)
# ==============================================================================
def classificar_estacao(mes):
    if mes in (12, 1, 2): return "Verão"
    if mes in (3, 4, 5):  return "Outono"
    if mes in (6, 7, 8):  return "Inverno"
    return "Primavera"

df_pares["estacao_ano"] = df_pares["data"].dt.month.apply(classificar_estacao)

linhas_saz = []
for est in ["Verão", "Outono", "Inverno", "Primavera"]:
    sub = df_pares[df_pares["estacao_ano"] == est]
    o, s = sub["precipitacao_mm"].values, sub["chuva_imerg"].values
    if len(o) < 30: continue
    
    r_s = np.corrcoef(o, s)[0, 1] if (o.std() > 0 and s.std() > 0) else np.nan
    soma_o = np.sum(o)
    pbias_s = ((np.sum(s) - soma_o) / soma_o) * 100 if soma_o > 0 else np.nan
    rmse_s = np.sqrt(mean_squared_error(o, s))
    
    linhas_saz.append({
        "Estação": est,
        "Média obs. (mm/dia)": round(o.mean(), 2),
        "r": round(r_s, 2),
        "PBIAS (%)": round(pbias_s, 1),
        "RMSE (mm/dia)": round(rmse_s, 2),
        "KGE": round(calc_kge(o, s), 2)
    })

df_sazonal = pd.DataFrame(linhas_saz)
print("\nMétricas Sazonais (Artigo - Seção 3):")
print(df_sazonal.to_string(index=False))

# ==============================================================================
# 5. MÉTRICAS CONSOLIDADAS POR ESTAÇÃO
# ==============================================================================
linhas_est = []
for cod, grp in df_pares.groupby("codigo"):
    o, s = grp["precipitacao_mm"].values, grp["chuva_imerg"].values
    if len(o) < 100:
        continue
    r_val, _ = pearsonr(o, s) if np.std(o) > 0 and np.std(s) > 0 else (np.nan, np.nan)
    soma_o = np.sum(o)
    linhas_est.append({
        "codigo": str(cod),
        "n_dias": len(o),
        "obs_total_mm": soma_o,
        "sim_total_mm": np.sum(s),
        "PBIAS_%": ((np.sum(s) - soma_o) / soma_o) * 100 if soma_o > 0 else np.nan,
        "RMSE_mm": np.sqrt(mean_squared_error(o, s)),
        "MAE_mm": mean_absolute_error(o, s),
        "Pearson_r": r_val,
        "KGE": calc_kge(o, s),
        "NSE": calc_nse(o, s)
    })

df_metricas = pd.DataFrame(linhas_est).merge(df_alt_full[["codigo", "estacao", "latitude", "longitude", "altitude_m"]], on="codigo", how="left")
df_metricas.to_csv(ARQ_METRICAS, index=False)

# Relação Altitude x PBIAS e Altitude x RMSE
r_pbias, p_pbias = pearsonr(df_metricas["altitude_m"], df_metricas["PBIAS_%"])
r_rmse, p_rmse   = pearsonr(df_metricas["altitude_m"], df_metricas["RMSE_mm"])
print(f"\nAltitude × PBIAS: r = {r_pbias:+.2f} (p = {p_pbias:.4f})")
print(f"Altitude × RMSE:  r = {r_rmse:+.2f} (p = {p_rmse:.4f})")

# Tabela 2: Faixas Altimétricas
df_metricas["faixa_alt"] = pd.cut(df_metricas["altitude_m"], bins=[0, 600, 800, 1000, 2000],
                                  labels=["< 600 m", "600–800 m", "800–1000 m", "> 1000 m"])
tabela_faixas = df_metricas.groupby("faixa_alt", observed=True).agg(
    N=("codigo", "count"),
    PBIAS_mediano=("PBIAS_%", "median"),
    RMSE_mediano=("RMSE_mm", "median"),
    r_mediano=("Pearson_r", "median")
).reset_index()
print("\nTabela 2 — Faixas Altimétricas:")
print(tabela_faixas.round(2).to_string(index=False))

# Tabela 3: Mesorregiões do IBGE
try:
    import geobr
    meso = geobr.read_meso_region(code_meso=52, year=2022)
    gdf = gpd.GeoDataFrame(df_metricas, geometry=gpd.points_from_xy(df_metricas["longitude"], df_metricas["latitude"]), crs="EPSG:4674")
    gdf_meso = gpd.sjoin(gdf, meso[["name_meso", "geometry"]], how="left", predicate="within").rename(columns={"name_meso": "mesorregiao"})
    tab_meso = gdf_meso.groupby("mesorregiao").agg(
        N=("codigo", "count"),
        altitude_media=("altitude_m", "mean"),
        obs_total=("obs_total_mm", "sum"),
        sim_total=("sim_total_mm", "sum"),
        RMSE_medio=("RMSE_mm", "mean")
    ).reset_index()
    tab_meso["PBIAS_pooled_%"] = ((tab_meso["sim_total"] - tab_meso["obs_total"]) / tab_meso["obs_total"]) * 100
    tab_meso = tab_meso.sort_values("altitude_media", ascending=False)
    print("\nTabela 3 — Mesorregiões:")
    print(tab_meso[["mesorregiao", "N", "altitude_media", "PBIAS_pooled_%", "RMSE_medio"]].round(2).to_string(index=False))
except Exception as e:
    print(f"Aviso geobr/mesorregiões: {e}")

# ==============================================================================
# 6. GERAÇÃO DAS FIGURAS FINAIS DO ARTIGO
# ==============================================================================
sns.set_theme(style="ticks", context="paper", font_scale=1.2)

# --- FIGURA 2: Série Temporal Mensal ---
df_pares["ano_mes"] = df_pares["data"].dt.to_period("M")
mensal = df_pares.groupby("ano_mes").agg(
    obs_media=("precipitacao_mm", "mean"),
    sim_media=("chuva_imerg", "mean")
).reset_index()
mensal["data"] = mensal["ano_mes"].dt.to_timestamp()

plt.figure(figsize=(11, 4.5))
plt.plot(mensal["data"], mensal["obs_media"], color="royalblue", lw=1.8, marker="o", ms=3, label="CEMADEN (obs.)")
plt.plot(mensal["data"], mensal["sim_media"], color="darkorange", lw=1.8, marker="s", ms=3, label="GPM IMERG V07")
plt.xlabel("Data")
plt.ylabel("Precipitação média mensal (mm/dia)")
plt.title("Série temporal mensal — média das 41 estações (2021–2025)", fontweight="bold")
plt.legend(loc="upper right")
plt.grid(alpha=0.3)
sns.despine()
plt.tight_layout()
plt.savefig(os.path.join(BASE_DIR, "FIG2_serie_mensal.png"), dpi=300, bbox_inches="tight")
plt.close()

# --- FIGURA 3: Mapas Espaciais (PBIAS, RMSE, Pearson r, KGE) ---
try:
    goias = geobr.read_state(code_state="GO", year=2020)
    goias_meso = geobr.read_meso_region(code_meso=52, year=2022)
    fig, axes = plt.subplots(2, 2, figsize=(13, 12))
    configs = [
        ("PBIAS_%", "PBIAS (%)", "RdBu", -30, 30, 0),
        ("RMSE_mm", "RMSE (mm/dia)", "YlOrRd", 6, 10.5, None),
        ("Pearson_r", "Pearson r", "RdYlGn", 0.55, 0.75, None),
        ("KGE", "KGE", "RdYlGn", 0.15, 0.70, None),
    ]
    for ax, (col, lbl, cmap, vmin, vmax, center) in zip(axes.flat, configs):
        goias.boundary.plot(ax=ax, edgecolor="black", linewidth=1.2)
        goias_meso.boundary.plot(ax=ax, edgecolor="gray", linewidth=0.5, linestyle="--")
        norm = TwoSlopeNorm(vmin=vmin, vcenter=center, vmax=vmax) if center is not None else plt.Normalize(vmin=vmin, vmax=vmax)
        sc = ax.scatter(df_metricas["longitude"], df_metricas["latitude"], c=df_metricas[col],
                        s=90, cmap=cmap, norm=norm, edgecolor="black", linewidth=0.6, zorder=5)
        cbar = plt.colorbar(sc, ax=ax, shrink=0.7, pad=0.03)
        cbar.set_label(lbl)
        ax.set_title(lbl, fontweight="bold")
        ax.set_xlim(-53.5, -45.5)
        ax.set_ylim(-19.5, -12.0)
        ax.grid(alpha=0.2)
    plt.tight_layout()
    plt.savefig(os.path.join(BASE_DIR, "FIG3_mapas_metricas.png"), dpi=300, bbox_inches="tight")
    plt.close()
except Exception as e:
    print(f"Aviso Figura 3: {e}")

# --- FIGURA 4: Altitude × PBIAS e Altitude × RMSE ---
fig, axes = plt.subplots(1, 2, figsize=(13, 5))
xfit = np.linspace(df_metricas["altitude_m"].min(), df_metricas["altitude_m"].max(), 50)

# Painel PBIAS
s1, i1, _, _, _ = linregress(df_metricas["altitude_m"], df_metricas["PBIAS_%"])
axes[0].scatter(df_metricas["altitude_m"], df_metricas["PBIAS_%"], s=80, alpha=0.75, color="royalblue", edgecolor="black", linewidth=0.5)
axes[0].plot(xfit, s1*xfit + i1, color="firebrick", lw=2)
axes[0].axhline(0, color="black", ls="--", lw=1)
axes[0].set_xlabel("Altitude (m)")
axes[0].set_ylabel("PBIAS (%)")
axes[0].set_title(f"Altitude × PBIAS\nr = {r_pbias:+.2f}, p = {p_pbias:.3f}", fontweight="bold")

# Painel RMSE
s2, i2, _, _, _ = linregress(df_metricas["altitude_m"], df_metricas["RMSE_mm"])
axes[1].scatter(df_metricas["altitude_m"], df_metricas["RMSE_mm"], s=80, alpha=0.75, color="darkorange", edgecolor="black", linewidth=0.5)
axes[1].plot(xfit, s2*xfit + i2, color="firebrick", lw=2)
axes[1].set_xlabel("Altitude (m)")
axes[1].set_ylabel("RMSE (mm/dia)")
axes[1].set_title(f"Altitude × RMSE\nr = {r_rmse:+.2f}, p = {p_rmse:.3f}", fontweight="bold")

sns.despine()
plt.tight_layout()
plt.savefig(os.path.join(BASE_DIR, "FIG4_altitude_pbias_rmse.png"), dpi=300, bbox_inches="tight")
plt.close()

print("\nProcessamento concluído com sucesso. Todas as tabelas e figuras foram salvas!")
