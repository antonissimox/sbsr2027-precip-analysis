# ============================================================
# BLOCO 9 — MÉTRICAS ESTATÍSTICAS GLOBAIS
# Validação Hidrológica e de Detecção: CEMADEN × IMERG V07 (2021–2025)
# ============================================================

import numpy as np
import pandas as pd
from scipy import stats

print("=" * 60)
print("CÁLCULO DAS MÉTRICAS ESTATÍSTICAS GLOBAIS (2021–2025)")
print("=" * 60)


# ------------------------------------------------------------
# 1. FUNÇÕES DE MÉTRICAS CONTÍNUAS
# ------------------------------------------------------------
def calcular_metricas_continuas(obs, est):
    """
    Calcula métricas contínuas entre observações de referência (in situ)
    e estimativas de satélite (IMERG).

    Parâmetros:
        obs (array-like): Precipitação observada de referência (mm/dia).
        est (array-like): Precipitação estimada por satélite (mm/dia).

    Retorna:
        dict: Métricas de erro, correlação e eficiência hidrológica.
    """
    obs = np.asarray(obs, dtype=float)
    est = np.asarray(est, dtype=float)

    # Filtragem estrita de valores finitos
    mascara = np.isfinite(obs) & np.isfinite(est)
    obs = obs[mascara]
    est = est[mascara]

    n = len(obs)
    if n < 2:
        return {k: np.nan for k in [
            "n", "media_obs", "media_est", "desvio_obs", "desvio_est",
            "pearson_r", "pearson_p", "spearman_r", "spearman_p", "r2",
            "bias", "pbias", "mae", "rmse", "nrmse", "nse", "kge", "slope", "intercept"
        ]}

    media_obs = float(np.mean(obs))
    media_est = float(np.mean(est))
    desvio_obs = float(np.std(obs, ddof=1))
    desvio_est = float(np.std(est, ddof=1))

    # Correlações lineares e monotônicas
    if desvio_obs > 0 and desvio_est > 0:
        pearson_r, pearson_p = stats.pearsonr(obs, est)
        spearman_r, spearman_p = stats.spearmanr(obs, est)
    else:
        pearson_r = pearson_p = spearman_r = spearman_p = np.nan

    r2 = pearson_r**2 if np.isfinite(pearson_r) else np.nan

    # Erros absolutos e volumétricos
    erros = est - obs
    bias = float(np.mean(erros))
    pbias = float(100.0 * bias / media_obs) if media_obs > 0 else np.nan
    mae = float(np.mean(np.abs(erros)))
    rmse = float(np.sqrt(np.mean(erros**2)))
    nrmse = float(100.0 * rmse / media_obs) if media_obs > 0 else np.nan

    # Coeficiente de Eficiência de Nash-Sutcliffe (NSE)
    sq_tot = np.sum((obs - media_obs)**2)
    sq_res = np.sum(erros**2)
    nse = float(1.0 - (sq_res / sq_tot)) if sq_tot > 0 else np.nan

    # Kling-Gupta Efficiency (KGE, Gupta et al., 2009)
    if desvio_obs > 0 and media_obs > 0 and np.isfinite(pearson_r):
        alpha = desvio_est / desvio_obs
        beta = media_est / media_obs
        kge = float(1.0 - np.sqrt((pearson_r - 1.0)**2 + (alpha - 1.0)**2 + (beta - 1.0)**2))
    else:
        kge = np.nan

    # Ajuste linear simples
    if desvio_obs > 0:
        reg = stats.linregress(obs, est)
        slope, intercept = float(reg.slope), float(reg.intercept)
    else:
        slope = intercept = np.nan

    return {
        "n": int(n),
        "media_obs": media_obs,
        "media_est": media_est,
        "desvio_obs": desvio_obs,
        "desvio_est": desvio_est,
        "pearson_r": pearson_r,
        "pearson_p": pearson_p,
        "spearman_r": spearman_r,
        "spearman_p": spearman_p,
        "r2": r2,
        "bias": bias,
        "pbias": pbias,
        "mae": mae,
        "rmse": rmse,
        "nrmse": nrmse,
        "nse": nse,
        "kge": kge,
        "slope": slope,
        "intercept": intercept
    }


# ------------------------------------------------------------
# 2. FUNÇÕES DE MÉTRICAS CATEGÓRICAS (ÍNDICES DE CONTINGÊNCIA)
# ------------------------------------------------------------
def calcular_metricas_categoricas(obs, est, limiar):
    """
    Calcula índices de contingência e acurácia de detecção para um dado limiar pluviométrico.
    """
    obs = np.asarray(obs, dtype=float)
    est = np.asarray(est, dtype=float)

    mascara = np.isfinite(obs) & np.isfinite(est)
    obs = obs[mascara]
    est = est[mascara]

    obs_chuva = obs >= limiar
    est_chuva = est >= limiar

    hits = int(np.sum(obs_chuva & est_chuva))
    misses = int(np.sum(obs_chuva & ~est_chuva))
    false_alarms = int(np.sum(~obs_chuva & est_chuva))
    correct_negatives = int(np.sum(~obs_chuva & ~est_chuva))

    total = hits + misses + false_alarms + correct_negatives

    # Métricas de tabela de contingência 2x2
    pod = hits / (hits + misses) if (hits + misses) > 0 else np.nan
    far = false_alarms / (hits + false_alarms) if (hits + false_alarms) > 0 else np.nan
    csi = hits / (hits + misses + false_alarms) if (hits + misses + false_alarms) > 0 else np.nan
    bias_freq = (hits + false_alarms) / (hits + misses) if (hits + misses) > 0 else np.nan
    acc = (hits + correct_negatives) / total if total > 0 else np.nan

    # Equitable Threat Score (ETS)
    if total > 0:
        hits_random = ((hits + misses) * (hits + false_alarms)) / total
        denom_ets = hits + misses + false_alarms - hits_random
        ets = (hits - hits_random) / denom_ets if denom_ets > 0 else np.nan
    else:
        ets = np.nan

    # Heidke Skill Score (HSS)
    if total > 0:
        expected = ((hits + misses) * (hits + false_alarms) + (correct_negatives + misses) * (correct_negatives + false_alarms)) / total
        denom_hss = total - expected
        hss = (hits + correct_negatives - expected) / denom_hss if denom_hss > 0 else np.nan
    else:
        hss = np.nan

    # F1-Score
    denom_f1 = (2 * hits) + misses + false_alarms
    f1 = (2 * hits) / denom_f1 if denom_f1 > 0 else np.nan

    return {
        "limiar_mm": float(limiar),
        "hits": hits,
        "misses": misses,
        "false_alarms": false_alarms,
        "correct_negatives": correct_negatives,
        "total": total,
        "POD": pod,
        "FAR": far,
        "CSI": csi,
        "BIAS_freq": bias_freq,
        "ACC": acc,
        "ETS": ets,
        "HSS": hss,
        "F1": f1
    }


# ------------------------------------------------------------
# 3. EXECUÇÃO GLOBAL
# ------------------------------------------------------------
obs_global = base_validacao["precipitacao_cemaden"].values
est_global = base_validacao["precipitacao_imerg"].values

metricas_globais = calcular_metricas_continuas(obs_global, est_global)

limiares = [0.1, 1.0, 10.0, 20.0, 50.0]
df_cat_globais = pd.DataFrame([
    calcular_metricas_categoricas(obs_global, est_global, lim)
    for lim in limiares
])


# ------------------------------------------------------------
# 4. RELATÓRIOS E FORMATAÇÃO VISUAL
# ------------------------------------------------------------
print("\n" + "=" * 60)
print("SÍNTESE DAS MÉTRICAS CONTÍNUAS (2021–2025)")
print("=" * 60)
for k, v in metricas_globais.items():
    if isinstance(v, float):
        print(f"  • {k:<15s}: {v:12.4f}")
    else:
        print(f"  • {k:<15s}: {v}")

print("\n" + "=" * 60)
print("SÍNTESE DAS MÉTRICAS CATEGÓRICAS POR LIMIAR")
print("=" * 60)

# Formatação percentual para facilitar a leitura visual
df_cat_exibicao = df_cat_globais.copy()
for col in ["POD", "FAR", "CSI", "ACC", "ETS", "HSS", "F1"]:
    df_cat_exibicao[col] = df_cat_exibicao[col].map(lambda x: f"{x:.3f}" if np.isfinite(x) else "-")
df_cat_exibicao["BIAS_freq"] = df_cat_exibicao["BIAS_freq"].map(lambda x: f"{x:.2f}" if np.isfinite(x) else "-")

try:
    display(df_cat_exibicao[["limiar_mm", "hits", "misses", "false_alarms", "POD", "FAR", "CSI", "BIAS_freq", "ETS", "HSS"]])
except NameError:
    print(df_cat_exibicao[["limiar_mm", "hits", "misses", "false_alarms", "POD", "FAR", "CSI", "BIAS_freq", "ETS", "HSS"]].to_string(index=False))


# ------------------------------------------------------------
# 5. EXPORTAÇÃO
# ------------------------------------------------------------
pasta_saida_metricas = SAIDA_DIR / "04_metricas_2021_2025"

pd.DataFrame([metricas_globais]).to_csv(
    pasta_saida_metricas / "metricas_globais_continuas.csv",
    index=False,
    encoding="utf-8-sig"
)

df_cat_globais.to_csv(
    pasta_saida_metricas / "metricas_globais_categoricas.csv",
    index=False,
    encoding="utf-8-sig"
)

print("\n" + "=" * 60)
print(f"Métricas globais exportadas com sucesso em:\n{pasta_saida_metricas}")
print("=" * 60)
