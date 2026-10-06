# ============================================================
# BLOCO 13 — GERAÇÃO DOS GRÁFICOS PRINCIPAIS
# Visualização Científica de Alta Resolução (300 DPI)
# ============================================================

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
import numpy as np
import pandas as pd
from scipy import stats

print("=" * 60)
print("GERANDO FIGURAS CIENTÍFICAS DE ALTA RESOLUÇÃO")
print("=" * 60)

# Configurações visuais e tipográficas
sns.set_theme(style="ticks", context="paper", font_scale=1.1)
plt.rcParams["figure.dpi"] = 110
plt.rcParams["savefig.dpi"] = 300
plt.rcParams["savefig.bbox"] = "tight"
plt.rcParams["font.sans-serif"] = "DejaVu Sans"

DIR_GRAF = SAIDA_DIR / "06_graficos"
DIR_GRAF.mkdir(parents=True, exist_ok=True)

n_estacoes_ativas = metricas_est_cont["codestacao"].nunique()


# ------------------------------------------------------------
# 1. DISPERSÃO GLOBAL (CEMADEN × GPM IMERG)
# ------------------------------------------------------------
fig, ax = plt.subplots(figsize=(6.5, 6.5))

obs = base_validacao["precipitacao_cemaden"]
est = base_validacao["precipitacao_imerg"]

# Scatter com transparência para mitigar overplotting
ax.scatter(obs, est, s=6, alpha=0.15, color="#1f77b4", edgecolor="none", rasterized=True)

# Limites dinâmicos
lim_max = 85
ax.plot([0, lim_max], [0, lim_max], color="#d62728", linestyle="--", lw=1.5, label="Linha 1:1 (Ideal)")

# Reta de regressão linear
slope = metricas_globais.get("slope", 1.0)
intercept = metricas_globais.get("intercept", 0.0)
x_reg = np.array([0, lim_max])
ax.plot(
    x_reg, slope * x_reg + intercept,
    color="#2ca02c", lw=1.6,
    label=f"Ajuste Linear: y = {slope:.2f}x + {intercept:.2f}"
)

# Caixa de anotação com métricas de desempenho
texto_metricas = (
    f"r = {metricas_globais['pearson_r']:.3f}\n"
    f"KGE = {metricas_globais['kge']:.3f}\n"
    f"RMSE = {metricas_globais['rmse']:.2f} mm/dia\n"
    f"PBIAS = {metricas_globais['pbias']:+.1f}%"
)
ax.text(
    0.05, 0.95, texto_metricas,
    transform=ax.transAxes, verticalalignment="top",
    bbox=dict(boxstyle="round,pad=0.5", facecolor="white", alpha=0.85, edgecolor="#cccccc")
)

ax.set_xlim(-1, lim_max)
ax.set_ylim(-1, lim_max)
ax.set_xlabel("Precipitação Observada - CEMADEN (mm/dia)", fontweight="bold")
ax.set_ylabel("Precipitação Estimada - IMERG V07 (mm/dia)", fontweight="bold")
ax.set_title("Dispersão Diária: CEMADEN × GPM IMERG V07 (2021–2025)", pad=12, fontweight="bold")
ax.legend(loc="lower right", frameon=True)
sns.despine()

fig.savefig(DIR_GRAF / "01_dispersao_global_CEMADEN_IMERG.png")
plt.show()
plt.close(fig)


# ------------------------------------------------------------
# 2. BOXPLOT DAS MÉTRICAS ENTRE ESTAÇÕES
# ------------------------------------------------------------
fig, axes = plt.subplots(1, 3, figsize=(13, 4.5))

paleta = ["#4a90e2", "#e94e77", "#50e3c2"]

sns.boxplot(y=metricas_est_cont["pearson_r"], ax=axes[0], color=paleta[0], width=0.35)
axes[0].set_title("Correlação de Pearson (r)", fontweight="bold")
axes[0].set_ylabel("r")

sns.boxplot(y=metricas_est_cont["pbias"], ax=axes[1], color=paleta[1], width=0.35)
axes[1].axhline(0, color="black", linestyle="--", lw=1)
axes[1].set_title("Viés Percentual - PBIAS (%)", fontweight="bold")
axes[1].set_ylabel("PBIAS (%)")

sns.boxplot(y=metricas_est_cont["rmse"], ax=axes[2], color=paleta[2], width=0.35)
axes[2].set_title("Erro Médio Quadrático - RMSE", fontweight="bold")
axes[2].set_ylabel("RMSE (mm/dia)")

for ax in axes:
    sns.despine(ax=ax)

fig.suptitle(f"Variabilidade Espacial das Métricas de Validação (n = {n_estacoes_ativas} estações)", y=1.03, fontweight="bold")
fig.savefig(DIR_GRAF / "02_boxplot_metricas_por_estacao.png")
plt.show()
plt.close(fig)


# ------------------------------------------------------------
# 3. HEATMAP: PEARSON r POR ESTAÇÃO × ANO
# ------------------------------------------------------------
def calcular_pearson_seguro(df):
    x = df["precipitacao_cemaden"].values
    y = df["precipitacao_imerg"].values
    m = np.isfinite(x) & np.isfinite(y)
    if np.sum(m) > 5 and np.std(x[m]) > 0 and np.std(y[m]) > 0:
        return stats.pearsonr(x[m], y[m])[0]
    return np.nan

# Agrupamento seguro sem warning de depreciação do pandas
pearson_ano = (
    base_validacao.groupby(["codestacao", "ano"])
    .apply(calcular_pearson_seguro, include_groups=False)
    .rename("pearson_r")
    .reset_index()
)

matriz_pearson = pearson_ano.pivot(index="codestacao", columns="ano", values="pearson_r")
matriz_pearson = matriz_pearson.loc[matriz_pearson.mean(axis=1).sort_values(ascending=False).index]

altura_fig = max(8, len(matriz_pearson) * 0.25)
fig, ax = plt.subplots(figsize=(7, altura_fig))

sns.heatmap(
    matriz_pearson, annot=True, fmt=".2f",
    cmap="YlGnBu", vmin=0.3, vmax=0.9,
    cbar_kws={"label": "Correlação de Pearson (r)"}, ax=ax, linewidths=0.5
)
ax.set_title("Estabilidade Interanual de Desempenho (Pearson r)", pad=12, fontweight="bold")
ax.set_xlabel("Ano de Monitoramento", fontweight="bold")
ax.set_ylabel("Código da Estação CEMADEN", fontweight="bold")

fig.savefig(DIR_GRAF / "03_heatmap_pearson_estacao_ano.png")
plt.show()
plt.close(fig)


# ------------------------------------------------------------
# 4. SÉRIE TEMPORAL MENSAL (REGIME HIDROLÓGICO REGIONAL)
# ------------------------------------------------------------
mensal = (
    base_validacao
    .set_index("data")
    .groupby(pd.Grouper(freq="ME"))[["precipitacao_cemaden", "precipitacao_imerg"]]
    .mean()
    .reset_index()
)

fig, ax = plt.subplots(figsize=(12, 4.5))
ax.plot(mensal["data"], mensal["precipitacao_cemaden"], label="CEMADEN (In situ)", color="#1f77b4", lw=2.0)
ax.plot(mensal["data"], mensal["precipitacao_imerg"], label="IMERG V07 (Satélite)", color="#ff7f0e", lw=2.0, linestyle="--")

ax.xaxis.set_major_locator(mdates.YearLocator())
ax.xaxis.set_minor_locator(mdates.MonthLocator((1, 4, 7, 10)))
ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))

ax.set_ylabel("Precipitação Média Diária (mm/dia)", fontweight="bold")
ax.set_title(f"Ciclo Hidrológico Regional Médio (n = {n_estacoes_ativas} estações)", pad=12, fontweight="bold")
ax.legend(frameon=True, loc="upper right")
sns.despine()

fig.savefig(DIR_GRAF / "04_serie_mensal_media.png")
plt.show()
plt.close(fig)


# ------------------------------------------------------------
# 5. ÍNDICES CATEGÓRICOS POR LIMIAR PLUVIOMÉTRICO
# ------------------------------------------------------------
fig, ax = plt.subplots(figsize=(9, 4.5))

x = np.arange(len(metricas_cat_globais))
largura = 0.25

ax.bar(x - largura, metricas_cat_globais["POD"], largura, label="POD (Probabilidade de Detecção)", color="#2b5c8f")
ax.bar(x,           metricas_cat_globais["FAR"], largura, label="FAR (Razão de Alarme Falso)", color="#d9534f")
ax.bar(x + largura, metricas_cat_globais["CSI"], largura, label="CSI (Índice de Sucesso Crítico)", color="#2e8540")

ax.set_xticks(x)
ax.set_xticklabels([f"≥ {l:.1f} mm" for l in metricas_cat_globais["limiar_mm"]], fontweight="medium")
ax.set_ylim(0, 1.05)
ax.set_ylabel("Valor do Índice", fontweight="bold")
ax.set_xlabel("Limiar Diário de Precipitação", fontweight="bold")
ax.set_title("Desempenho Categórico por Intensidade Pluviométrica", pad=12, fontweight="bold")
ax.legend(frameon=True, loc="upper right")
sns.despine()

fig.savefig(DIR_GRAF / "05_barras_categoricas_por_limiar.png")
plt.show()
plt.close(fig)

print("=" * 60)
print(f"Todas as 5 figuras foram salvas com sucesso em 300 DPI em:\n{DIR_GRAF}")
print("=" * 60)
