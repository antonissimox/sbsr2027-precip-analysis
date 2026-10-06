# ============================================================
# BLOCO 3 — SELEÇÃO DAS ESTAÇÕES ELEGÍVEIS
# Critério: ≥ 80% de completude no período 2021–2025
# ============================================================

print("=" * 60)
print("SELEÇÃO E AUDITORIA DE ESTAÇÕES ELEGÍVEIS")
print("=" * 60)


# ------------------------------------------------------------
# 1. PARÂMETROS TEMPORAIS
# ------------------------------------------------------------
dias_esperados = (DATA_FINAL - DATA_INICIAL).days + 1

print(f"Período de avaliação: {DATA_INICIAL.date()} a {DATA_FINAL.date()}")
print(f"Total de dias esperados por estação: {dias_esperados}")
print(f"Critério de elegibilidade: completude ≥ {LIMIAR_COMPLETUDE:.0%}")


# ------------------------------------------------------------
# 2. CÁLCULO DE COMPLETUDE POR ESTAÇÃO
# ------------------------------------------------------------
resumo_estacoes = (
    cemaden.groupby("codestacao")
    .agg(
        municipio=("municipio", "first"),
        nomeestacao=("nomeestacao", "first"),
        latitude=("latitude", "first"),
        longitude=("longitude", "first"),
        registros=("data", "count"),
        validos=("observacao_valida", "sum")
    )
    .reset_index()
)

# Taxa de completude sobre o total de dias teóricos da série
resumo_estacoes["completude"] = resumo_estacoes["validos"] / dias_esperados
resumo_estacoes["elegivel"] = resumo_estacoes["completude"] >= LIMIAR_COMPLETUDE


# ------------------------------------------------------------
# 3. SEGMENTAÇÃO DAS SÉRIES
# ------------------------------------------------------------
estacoes_elegiveis = (
    resumo_estacoes[resumo_estacoes["elegivel"]]
    .copy()
    .sort_values("completude", ascending=False)
)

estacoes_nao_elegiveis = (
    resumo_estacoes[~resumo_estacoes["elegivel"]]
    .copy()
    .sort_values("completude", ascending=True)
)

# Filtrar a base diária apenas para as estações selecionadas
cemaden_elegivel = cemaden[
    cemaden["codestacao"].isin(estacoes_elegiveis["codestacao"])
].copy()


# ------------------------------------------------------------
# 4. RESUMO EXECUTIVO
# ------------------------------------------------------------
total_estacoes = len(resumo_estacoes)
n_elegiveis = len(estacoes_elegiveis)
n_excluidas = len(estacoes_nao_elegiveis)

print("\n" + "=" * 60)
print("RESULTADO DO FILTRO DE QUALIDADE")
print("=" * 60)
print(f"Estações avaliadas: {total_estacoes}")
print(f"Estações elegíveis: {n_elegiveis} ({n_elegiveis / total_estacoes:.1%})")
print(f"Estações excluídas: {n_excluidas} ({n_excluidas / total_estacoes:.1%})")
print(f"Registros diários retidos: {len(cemaden_elegivel):,}")


# ------------------------------------------------------------
# 5. VISUALIZAÇÃO DAS AMOSTRAS
# ------------------------------------------------------------
cols_excluidas = ["codestacao", "municipio", "nomeestacao", "registros", "validos", "completude"]
cols_elegiveis = ["codestacao", "municipio", "nomeestacao", "latitude", "longitude", "registros", "validos", "completude"]

def exibir_tabela(df, colunas, titulo):
    print(f"\n--- {titulo} ---")
    df_show = df[colunas].copy()
    df_show["completude"] = df_show["completude"].map(lambda x: f"{x:.1%}")
    try:
        display(df_show)
    except NameError:
        print(df_show.to_string(index=False))

if n_excluidas > 0:
    exibir_tabela(estacoes_nao_elegiveis, cols_excluidas, "ESTAÇÕES EXCLUÍDAS (< 80% COMPLETUDE)")

exibir_tabela(estacoes_elegiveis, cols_elegiveis, "ESTAÇÕES ELEGÍVEIS SELECIONADAS (≥ 80% COMPLETUDE)")


# ------------------------------------------------------------
# 6. EXPORTAÇÃO DOS ARQUIVOS CONSOLIDADOS
# ------------------------------------------------------------
pasta_auditoria = SAIDA_DIR / "01_auditoria"
pasta_elegiveis = SAIDA_DIR / "02_estacoes_elegiveis"

resumo_estacoes.to_csv(
    pasta_auditoria / "completude_estacoes_CEMADEN.csv",
    index=False,
    encoding="utf-8-sig"
)

estacoes_elegiveis.to_csv(
    pasta_elegiveis / "estacoes_elegiveis_CEMADEN.csv",
    index=False,
    encoding="utf-8-sig"
)

estacoes_nao_elegiveis.to_csv(
    pasta_elegiveis / "estacoes_excluidas_CEMADEN.csv",
    index=False,
    encoding="utf-8-sig"
)

cemaden_elegivel.to_csv(
    pasta_elegiveis / "CEMADEN_dados_estacoes_elegiveis.csv",
    index=False,
    encoding="utf-8-sig"
)

print("\n" + "=" * 60)
print("ARQUIVOS EXPORTADOS COM SUCESSO:")
print(f"  • Auditoria: {pasta_auditoria}")
print(f"  • Elegíveis: {pasta_elegiveis}")
print("=" * 60)
