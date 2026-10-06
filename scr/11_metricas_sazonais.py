# ============================================================
# BLOCO 11 — MÉTRICAS ESTATÍSTICAS SAZONAIS
# Climatologia do Hemisfério Sul: DJF, MAM, JJA, SON (2021–2025)
# ============================================================

print("=" * 60)
print("DECOMPOSIÇÃO CLIMATOLÓGICA: MÉTRICAS SAZONAIS")
print("=" * 60)


# ------------------------------------------------------------
# 1. CLASSIFICAÇÃO SAZONAL VETORIZADA (HEMISFÉRIO SUL)
# ------------------------------------------------------------
# Verão    (DJF): Dezembro, Janeiro, Fevereiro (Pico chuvoso)
# Outono   (MAM): Março, Abril, Maio (Transição úmido -> seco)
# Inverno  (JJA): Junho, Julho, Agosto (Estiagem rigorosa)
# Primavera(SON): Setembro, Outubro, Novembro (Transição seco -> chuvoso)

mapa_estacoes = {
    12: "Verão (DJF)", 1: "Verão (DJF)", 2: "Verão (DJF)",
    3: "Outono (MAM)", 4: "Outono (MAM)", 5: "Outono (MAM)",
    6: "Inverno (JJA)", 7: "Inverno (JJA)", 8: "Inverno (JJA)",
    9: "Primavera (SON)", 10: "Primavera (SON)", 11: "Primavera (SON)"
}

ordem_estacoes = ["Verão (DJF)", "Outono (MAM)", "Inverno (JJA)", "Primavera (SON)"]

meses = pd.to_datetime(base_validacao["data"]).dt.month
base_validacao["estacao"] = pd.Categorical(
    meses.map(mapa_estacoes),
    categories=ordem_estacoes,
    ordered=True
)


# ------------------------------------------------------------
# 2. MÉTRICAS CONTÍNUAS POR ESTAÇÃO DO ANO
# ------------------------------------------------------------
registros_sazonais_cont = []

for est, grupo in base_validacao.groupby("estacao", observed=True):
    obs = grupo["precipitacao_cemaden"].values
    est_sat = grupo["precipitacao_imerg"].values
    
    m = calcular_metricas_continuas(obs, est_sat)
    m["estacao"] = str(est)
    registros_sazonais_cont.append(m)

metricas_sazonais_cont = pd.DataFrame(registros_sazonais_cont)

cols_cont_ordem = ["estacao", "n", "media_obs", "media_est", "pearson_r", "rmse", "pbias", "kge", "nse"]
cols_restantes = [c for c in metricas_sazonais_cont.columns if c not in cols_cont_ordem]
metricas_sazonais_cont = metricas_sazonais_cont[cols_cont_ordem + cols_restantes]


# ------------------------------------------------------------
# 3. MÉTRICAS CATEGÓRICAS POR ESTAÇÃO DO ANO
# ------------------------------------------------------------
registros_sazonais_cat = []
limiares_padrao = globals().get("limiares", [0.1, 1.0, 10.0, 20.0, 50.0])

for est, grupo in base_validacao.groupby("estacao", observed=True):
    obs = grupo["precipitacao_cemaden"].values
    est_sat = grupo["precipitacao_imerg"].values
    
    for lim in limiares_padrao:
        m = calcular_metricas_categoricas(obs, est_sat, lim)
        m["estacao"] = str(est)
        registros_sazonais_cat.append(m)

metricas_sazonais_cat = pd.DataFrame(registros_sazonais_cat)

cols_cat_ordem = ["estacao", "limiar_mm", "hits", "misses", "false_alarms", "POD", "FAR", "CSI", "BIAS_freq", "ETS", "HSS"]
cols_cat_restantes = [c for c in metricas_sazonais_cat.columns if c not in cols_cat_ordem]
metricas_sazonais_cat = metricas_sazonais_cat[cols_cat_ordem + cols_cat_restantes]


# ------------------------------------------------------------
# 4. SÍNTESE E FORMATAÇÃO VISUAL
# ------------------------------------------------------------
print("\n" + "=" * 60)
print("COMPORTAMENTO SAZONAL: MÉTRICAS CONTÍNUAS")
print("=" * 60)

tabela_sazonal_resumo = metricas_sazonais_cont[
    ["estacao", "n", "media_obs", "media_est", "pearson_r", "rmse", "pbias", "kge"]
].copy()

tabela_sazonal_resumo["media_obs"] = tabela_sazonal_resumo["media_obs"].map(lambda x: f"{x:.2f}")
tabela_sazonal_resumo["media_est"] = tabela_sazonal_resumo["media_est"].map(lambda x: f"{x:.2f}")
tabela_sazonal_resumo["pearson_r"] = tabela_sazonal_resumo["pearson_r"].map(lambda x: f"{x:.3f}")
tabela_sazonal_resumo["rmse"] = tabela_sazonal_resumo["rmse"].map(lambda x: f"{x:.2f}")
tabela_sazonal_resumo["pbias"] = tabela_sazonal_resumo["pbias"].map(lambda x: f"{x:+.1f}%")
tabela_sazonal_resumo["kge"] = tabela_sazonal_resumo["kge"].map(lambda x: f"{x:.3f}")

try:
    display(tabela_sazonal_resumo)
except NameError:
    print(tabela_sazonal_resumo.to_string(index=False))

print("\n" + "=" * 60)
print("DETECÇÃO DE CHUVA (LIMIAR = 1.0 mm/dia) POR ESTAÇÃO")
print("=" * 60)

tabela_sazonal_cat1mm = metricas_sazonais_cat[metricas_sazonais_cat["limiar_mm"] == 1.0][
    ["estacao", "hits", "misses", "false_alarms", "POD", "FAR", "CSI", "BIAS_freq"]
].copy()

for col in ["POD", "FAR", "CSI"]:
    tabela_sazonal_cat1mm[col] = tabela_sazonal_cat1mm[col].map(lambda x: f"{x:.3f}")
tabela_sazonal_cat1mm["BIAS_freq"] = tabela_sazonal_cat1mm["BIAS_freq"].map(lambda x: f"{x:.2f}")

try:
    display(tabela_sazonal_cat1mm)
except NameError:
    print(tabela_sazonal_cat1mm.to_string(index=False))


# ------------------------------------------------------------
# 5. EXPORTAÇÃO DOS DADOS SAZONAIS
# ------------------------------------------------------------
pasta_saida_sazonais = SAIDA_DIR / "04_metricas_2021_2025"
pasta_saida_sazonais.mkdir(parents=True, exist_ok=True)

arq_sazonal_cont = pasta_saida_sazonais / "metricas_sazonais_continuas.csv"
arq_sazonal_cat = pasta_saida_sazonais / "metricas_sazonais_categoricas.csv"

metricas_sazonais_cont.to_csv(arq_sazonal_cont, index=False, encoding="utf-8-sig")
metricas_sazonais_cat.to_csv(arq_sazonal_cat, index=False, encoding="utf-8-sig")

print("\n" + "=" * 60)
print(f"Arquivos sazonais salvos em:\n{pasta_saida_sazonais}")
print("=" * 60)
