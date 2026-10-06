# ============================================================
# BLOCO 10 — MÉTRICAS ESTATÍSTICAS ANUAIS (2021–2025)
# Avaliação da Estabilidade Temporal Interanual
# ============================================================

print("=" * 60)
print("DECOMPOSIÇÃO TEMPORAL: MÉTRICAS ANUAIS (2021–2025)")
print("=" * 60)


# ------------------------------------------------------------
# 1. ATRIBUIÇÃO TEMPORAL DO ANO
# ------------------------------------------------------------
if "ano" not in base_validacao.columns:
    base_validacao["ano"] = pd.to_datetime(base_validacao["data"]).dt.year


# ------------------------------------------------------------
# 2. CÁLCULO DAS MÉTRICAS CONTÍNUAS ANUAIS
# ------------------------------------------------------------
registros_continuos_ano = []

for ano, grupo in base_validacao.groupby("ano"):
    obs = grupo["precipitacao_cemaden"].values
    est = grupo["precipitacao_imerg"].values
    
    m = calcular_metricas_continuas(obs, est)
    m["ano"] = int(ano)
    registros_continuos_ano.append(m)

metricas_ano_continuas = pd.DataFrame(registros_continuos_ano)

# Reordenar para manter o ano como primeira coluna
cols_primeiras = ["ano", "n", "media_obs", "media_est", "pearson_r", "rmse", "pbias", "kge", "nse"]
cols_restantes = [c for c in metricas_ano_continuas.columns if c not in cols_primeiras]
metricas_ano_continuas = metricas_ano_continuas[cols_primeiras + cols_restantes]


# ------------------------------------------------------------
# 3. CÁLCULO DAS MÉTRICAS CATEGÓRICAS ANUAIS
# ------------------------------------------------------------
registros_cat_ano = []
limiares_padrao = globals().get("limiares", [0.1, 1.0, 10.0, 20.0, 50.0])

for ano, grupo in base_validacao.groupby("ano"):
    obs = grupo["precipitacao_cemaden"].values
    est = grupo["precipitacao_imerg"].values
    
    for lim in limiares_padrao:
        m = calcular_metricas_categoricas(obs, est, lim)
        m["ano"] = int(ano)
        registros_cat_ano.append(m)

metricas_ano_cat = pd.DataFrame(registros_cat_ano)

cols_cat_primeiras = ["ano", "limiar_mm", "hits", "misses", "false_alarms", "POD", "FAR", "CSI", "BIAS_freq", "ETS", "HSS"]
cols_cat_restantes = [c for c in metricas_ano_cat.columns if c not in cols_cat_primeiras]
metricas_ano_cat = metricas_ano_cat[cols_cat_primeiras + cols_cat_restantes]


# ------------------------------------------------------------
# 4. EXIBIÇÃO FORMATADA E SÍNTESE
# ------------------------------------------------------------
print("\n" + "=" * 60)
print("SÍNTESE DAS MÉTRICAS CONTÍNUAS POR ANO")
print("=" * 60)

tabela_resumo_cont = metricas_ano_continuas[
    ["ano", "n", "media_obs", "media_est", "pearson_r", "rmse", "pbias", "kge"]
].copy()

tabela_resumo_cont["media_obs"] = tabela_resumo_cont["media_obs"].map(lambda x: f"{x:.2f}")
tabela_resumo_cont["media_est"] = tabela_resumo_cont["media_est"].map(lambda x: f"{x:.2f}")
tabela_resumo_cont["pearson_r"] = tabela_resumo_cont["pearson_r"].map(lambda x: f"{x:.3f}")
tabela_resumo_cont["rmse"] = tabela_resumo_cont["rmse"].map(lambda x: f"{x:.2f}")
tabela_resumo_cont["pbias"] = tabela_resumo_cont["pbias"].map(lambda x: f"{x:+.1f}%")
tabela_resumo_cont["kge"] = tabela_resumo_cont["kge"].map(lambda x: f"{x:.3f}")

try:
    display(tabela_resumo_cont)
except NameError:
    print(tabela_resumo_cont.to_string(index=False))

print("\n" + "=" * 60)
print("DETECÇÃO DE CHUVA (LIMIAR = 1.0 mm/dia) POR ANO")
print("=" * 60)

tabela_resumo_cat1mm = metricas_ano_cat[metricas_ano_cat["limiar_mm"] == 1.0][
    ["ano", "hits", "misses", "false_alarms", "POD", "FAR", "CSI", "BIAS_freq"]
].copy()

for col in ["POD", "FAR", "CSI"]:
    tabela_resumo_cat1mm[col] = tabela_resumo_cat1mm[col].map(lambda x: f"{x:.3f}")
tabela_resumo_cat1mm["BIAS_freq"] = tabela_resumo_cat1mm["BIAS_freq"].map(lambda x: f"{x:.2f}")

try:
    display(tabela_resumo_cat1mm)
except NameError:
    print(tabela_resumo_cat1mm.to_string(index=False))


# ------------------------------------------------------------
# 5. EXPORTAÇÃO DOS DADOS CONSOLIDADOS
# ------------------------------------------------------------
pasta_saida_anuais = SAIDA_DIR / "03_metricas_anuais"
pasta_saida_anuais.mkdir(parents=True, exist_ok=True)

arq_cont = pasta_saida_anuais / "metricas_anuais_continuas.csv"
arq_cat = pasta_saida_anuais / "metricas_anuais_categoricas.csv"

metricas_ano_continuas.to_csv(arq_cont, index=False, encoding="utf-8-sig")
metricas_ano_cat.to_csv(arq_cat, index=False, encoding="utf-8-sig")

print("\n" + "=" * 60)
print(f"Arquivos salvos com sucesso em:\n{pasta_saida_anuais}")
print("=" * 60)
