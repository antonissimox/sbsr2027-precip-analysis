# ============================================================
# BLOCO 8 — AUDITORIA DE COMPLETUDE DO PAREAMENTO
# Avaliação de Retenção Amostral (2021–2025)
# ============================================================

print("=" * 60)
print("AUDITORIA DE COMPLETUDE EFETIVA DO PAREAMENTO")
print("=" * 60)


# ------------------------------------------------------------
# 1. PARÂMETRO TEÓRICO DO PERÍODO
# ------------------------------------------------------------
dias_esperados = (DATA_FINAL - DATA_INICIAL).days + 1
print(f"Período: {DATA_INICIAL.date()} a {DATA_FINAL.date()} ({dias_esperados} dias teóricos)")


# ------------------------------------------------------------
# 2. CONTAGEM DE DIAS PAREADOS POR ESTAÇÃO
# ------------------------------------------------------------
completude_pareamento = (
    base_validacao.groupby("codestacao")
    .agg(
        dias_pareados=("data", "nunique"),
        dias_cemaden_validos=("precipitacao_cemaden", "count"),
        dias_imerg_validos=("precipitacao_imerg", "count")
    )
    .reset_index()
)

# Taxa de completude efetiva em relação ao total de dias do estudo
completude_pareamento["completude_efetiva"] = (
    completude_pareamento["dias_pareados"] / dias_esperados
)


# ------------------------------------------------------------
# 3. ASSOCIAÇÃO COM OS METADADOS DAS ESTAÇÕES
# ------------------------------------------------------------
cols_meta = [
    "codestacao",
    "municipio",
    "nomeestacao",
    "latitude",
    "longitude",
    "completude"
]

completude_pareamento = pd.merge(
    completude_pareamento,
    estacoes_elegiveis[cols_meta].rename(columns={"completude": "completude_cemaden_bruta"}),
    on="codestacao",
    how="left"
)

# Diferença de retenção (avaliar se houve descarte por falha no satélite)
completude_pareamento["diferenca_retencao"] = (
    completude_pareamento["completude_efetiva"] - completude_pareamento["completude_cemaden_bruta"]
)

# Ordenar da menor completude efetiva para a maior
completude_pareamento = completude_pareamento.sort_values("completude_efetiva").reset_index(drop=True)


# ------------------------------------------------------------
# 4. SÍNTESE E DIAGNÓSTICO
# ------------------------------------------------------------
comp_media = completude_pareamento["completude_efetiva"].mean()
comp_min = completude_pareamento["completude_efetiva"].min()
comp_max = completude_pareamento["completude_efetiva"].max()

print("\n" + "=" * 60)
print("DIAGNÓSTICO DE RETENÇÃO TEMPORAL")
print("=" * 60)
print(f"Estações auditadas:           {len(completude_pareamento)}")
print(f"Completude média pós-pareamento: {comp_media:.2%}")
print(f"Completude mínima pós-pareamento: {comp_min:.2%}")
print(f"Completude máxima pós-pareamento: {comp_max:.2%}")

if (completude_pareamento["diferenca_retencao"].abs() < 1e-4).all():
    print("\n✓ Integridade perfeita: nenhuma data válida do CEMADEN foi perdida por ausência de dados no IMERG.")
else:
    print("\n! Atenção: foram identificadas lacunas pontuais de sobreposição entre CEMADEN e IMERG.")


# ------------------------------------------------------------
# 5. VISUALIZAÇÃO FORMATADA
# ------------------------------------------------------------
tabela_vis = completude_pareamento[[
    "codestacao",
    "municipio",
    "nomeestacao",
    "dias_pareados",
    "completude_cemaden_bruta",
    "completude_efetiva"
]].copy()

tabela_vis["completude_cemaden_bruta"] = tabela_vis["completude_cemaden_bruta"].map(lambda x: f"{x:.1%}")
tabela_vis["completude_efetiva"] = tabela_vis["completude_efetiva"].map(lambda x: f"{x:.1%}")

print("\nTabela de completude por estação:")
try:
    display(tabela_vis)
except NameError:
    print(tabela_vis.to_string(index=False))


# ------------------------------------------------------------
# 6. EXPORTAÇÃO
# ------------------------------------------------------------
caminho_csv = SAIDA_DIR / "01_auditoria" / "completude_pareamento_CEMADEN_IMERG.csv"
completude_pareamento.to_csv(caminho_csv, index=False, encoding="utf-8-sig")

print("\n" + "=" * 60)
print(f"Auditoria de completude exportada:\n{caminho_csv}")
print("=" * 60)
