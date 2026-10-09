# ============================================================
# BLOCO 1 — Seleção das estações CEMADEN elegíveis
# ============================================================
# Aplica critério duplo de elegibilidade sobre a base CEMADEN
# pré-processada (limpeza física + filtro 250 mm/dia já aplicados
# em etapa anterior):
#   (A) completude anual ≥80% em pelo menos 4 dos 5 anos;
#   (B) completude agregada ≥80% no período completo (2021–2025).
#
# Entrada: CEMADEN_Goias_diario_limpo_2021_2025.xlsx
#          CEMADEN_Goias_auditoria_estacoes_2021_2025.xlsx
# Saída:   estacoes_41_coords.csv
# ============================================================

import os
import pandas as pd

# Caminhos (ajustar conforme ambiente)
PASTA_DADOS = os.environ.get("SBSR_DATA_DIR", "data/processed")
ARQ_LIMPO     = os.path.join(PASTA_DADOS, "CEMADEN_Goias_diario_limpo_2021_2025.xlsx")
ARQ_AUDITORIA = os.path.join(PASTA_DADOS, "CEMADEN_Goias_auditoria_estacoes_2021_2025.xlsx")
ARQ_SAIDA     = os.path.join(PASTA_DADOS, "estacoes_41_coords.csv")

assert os.path.exists(ARQ_LIMPO), f"Arquivo não encontrado: {ARQ_LIMPO}"
assert os.path.exists(ARQ_AUDITORIA), f"Arquivo não encontrado: {ARQ_AUDITORIA}"

# ------------------------------------------------------------------
# 1. Carregar base diária limpa
# ------------------------------------------------------------------
df_cemaden = pd.read_excel(ARQ_LIMPO)
df_cemaden["data"] = pd.to_datetime(df_cemaden["data"])
df_cemaden["precipitacao_mm"] = pd.to_numeric(df_cemaden["precipitacao_mm"], errors="coerce")
df_cemaden = df_cemaden.dropna(subset=["data", "precipitacao_mm"])

print(f"Registros carregados: {len(df_cemaden):,}")
print(f"Estações:             {df_cemaden['codigo'].nunique()}")

# ------------------------------------------------------------------
# 2. Critério duplo de elegibilidade
# ------------------------------------------------------------------
auditoria = pd.read_excel(ARQ_AUDITORIA, sheet_name="auditoria_estacao_ano")

# Critério A — completude anual ≥80% em pelo menos 4 dos 5 anos
crit_A = auditoria.groupby("codigo")["elegivel_80"].sum()
crit_A = set(crit_A[crit_A >= 4].index)

# Critério B — completude agregada ≥80% no período completo
agg = auditoria.groupby("codigo").agg(
    dias_validos=("dias_validos", "sum"),
    dias_esperados=("dias_esperados", "sum"),
)
agg["completude_pct"] = agg["dias_validos"] / agg["dias_esperados"] * 100
crit_B = set(agg[agg["completude_pct"] >= 80].index)

estacoes_elegiveis = sorted(crit_A & crit_B)

print(f"\nEstações elegíveis:")
print(f"  Critério A (≥80% em ≥4 anos): {len(crit_A)}")
print(f"  Critério B (≥80% pooled)     : {len(crit_B)}")
print(f"  Interseção A ∩ B             : {len(estacoes_elegiveis)}")

# ------------------------------------------------------------------
# 3. Aplicar filtro e extrair coordenadas
# ------------------------------------------------------------------
df_filtrado = df_cemaden[df_cemaden["codigo"].isin(estacoes_elegiveis)].copy()

print(f"\nApós filtro:")
print(f"  Registros: {len(df_filtrado):,}")
print(f"  Estações : {df_filtrado['codigo'].nunique()}")

coords = (
    df_filtrado[["codigo", "estacao", "latitude", "longitude"]]
    .drop_duplicates(subset=["codigo"])
    .reset_index(drop=True)
)
coords.to_csv(ARQ_SAIDA, index=False)

print(f"\nCoordenadas salvas em: {ARQ_SAIDA} ({len(coords)} estações)")
