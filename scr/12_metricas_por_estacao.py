# ============================================================
# BLOCO 12 — MÉTRICAS ESPACIAIS POR ESTAÇÃO PLUVIOMÉTRICA
# CEMADEN × GPM IMERG V07 (2021–2025)
# ============================================================

print("=" * 60)
print("DECOMPOSIÇÃO ESPACIAL: MÉTRICAS INDIVIDUAIS POR ESTAÇÃO")
print("=" * 60)


# ------------------------------------------------------------
# 1. METADADOS DAS ESTAÇÕES ELEGÍVEIS
# ------------------------------------------------------------
cols_estacoes = [
    "codestacao",
    "municipio",
    "nomeestacao",
    "latitude",
    "longitude",
    "completude"
]
info_estacoes = estacoes_elegiveis[cols_estacoes].copy()


# ------------------------------------------------------------
# 2. MÉTRICAS CONTÍNUAS POR ESTAÇÃO
# ------------------------------------------------------------
registros_est_cont = []

for cod, grupo in base_validacao.groupby("codestacao"):
    obs = grupo["precipitacao_cemaden"].values
    est = grupo["precipitacao_imerg"].values
    
    m = calcular_metricas_continuas(obs, est)
    m["codestacao"] = cod
    registros_est_cont.append(m)

df_metricas_cont = pd.DataFrame(registros_est_cont)

# Junção com os metadados geográficos
metricas_est_cont = pd.merge(
    info_estacoes,
    df_metricas_cont,
    on="codestacao",
    how="inner"
)

# Ordenação decrescente por correlação de Pearson
metricas_est_cont = metricas_est_cont.sort_values("pearson_r", ascending=False).reset_index(drop=True)


# ------------------------------------------------------------
# 3. MÉTRICAS CATEGÓRICAS POR ESTAÇÃO E LIMIAR
# ------------------------------------------------------------
registros_est_cat = []
limiares_padrao = globals().get("limiares", [0.1, 1.0, 10.0, 20.0, 50.0])

for cod, grupo in base_validacao.groupby("codestacao"):
    obs = grupo["precipitacao_cemaden"].values
    est = grupo["precipitacao_imerg"].values
    
    for lim in limiares_padrao:
        m = calcular_metricas_categoricas(obs, est, lim)
        m["codestacao"] = cod
        registros_est_cat.append(m)

df_metricas_cat = pd.DataFrame(registros_est_cat)

# Associar metadados também às métricas categóricas
metricas_est_cat = pd.merge(
    info_estacoes,
    df_metricas_cat,
    on="codestacao",
    how="inner"
)

cols_cat_primeiras = ["codestacao", "municipio", "nomeestacao", "latitude", "longitude", "limiar_mm", "hits", "misses", "false_alarms", "POD", "FAR", "CSI", "BIAS_freq", "ETS", "HSS"]
cols_cat_restantes = [c for c in metricas_est_cat.columns if c not in cols_cat_primeiras]
metricas_est_cat = metricas_est_cat[cols_cat_primeiras + cols_cat_restantes]


# ------------------------------------------------------------
# 4. SÍNTESE E INSPEÇÃO VISUAL
# ------------------------------------------------------------
cols_exibicao = ["codestacao", "municipio", "n", "pearson_r", "rmse", "pbias", "kge"]

def exibir_tabela_formatada(df, titulo):
    print(f"\n--- {titulo} ---")
    df_format = df[cols_exibicao].copy()
    df_format["pearson_r"] = df_format["pearson_r"].map(lambda x: f"{x:.3f}")
    df_format["rmse"] = df_format["rmse"].map(lambda x: f"{x:.2f}")
    df_format["pbias"] = df_format["pbias"].map(lambda x: f"{x:+.1f}%")
    df_format["kge"] = df_format["kge"].map(lambda x: f"{x:.3f}")
    try:
        display(df_format)
    except NameError:
        print(df_format.to_string(index=False))

exibir_tabela_formatada(metricas_est_cont.head(5), "TOP 5 ESTAÇÕES (MAIOR CORRELAÇÃO DE PEARSON)")
exibir_tabela_formatada(metricas_est_cont.tail(5), "BOTTOM 5 ESTAÇÕES (MENOR CORRELAÇÃO DE PEARSON)")

print("\n" + "=" * 60)
print("DISTRIBUIÇÃO ESTATÍSTICA ESPACIAL DAS MÉTRICAS (n = %d estações)" % len(metricas_est_cont))
print("=" * 60)
resumo_estatistico = metricas_est_cont[["pearson_r", "rmse", "pbias", "kge", "nse"]].describe().T[["mean", "std", "min", "25%", "50%", "75%", "max"]]
resumo_estatistico.columns = ["Média", "Desv. Pad.", "Mín.", "Q1 (25%)", "Mediana", "Q3 (75%)", "Máx."]
print(resumo_estatistico.round(3).to_string())


# ------------------------------------------------------------
# 5. EXPORTAÇÃO DOS ARQUIVOS ESPACIAIS
# ------------------------------------------------------------
pasta_saida = SAIDA_DIR / "04_metricas_2021_2025"
pasta_saida.mkdir(parents=True, exist_ok=True)

arq_est_cont = pasta_saida / "metricas_por_estacao_continuas.csv"
arq_est_cat = pasta_saida / "metricas_por_estacao_categoricas.csv"

metricas_est_cont.to_csv(arq_est_cont, index=False, encoding="utf-8-sig")
metricas_est_cat.to_csv(arq_est_cat, index=False, encoding="utf-8-sig")

print("\n" + "=" * 60)
print(f"Arquivos por estação exportados com sucesso em:\n{pasta_saida}")
print("=" * 60)
