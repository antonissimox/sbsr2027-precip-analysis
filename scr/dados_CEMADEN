# ============================================================
# BLOCO 1 — CONFIGURAÇÃO DO PROJETO
# CEMADEN × GPM IMERG V07 — Goiás (2021–2025)
# ============================================================

# ----------------------------
# 1. IMPORTAÇÕES
# ----------------------------
import os
import glob
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr

warnings.filterwarnings("ignore")


# ----------------------------
# 2. DEFINIÇÃO DINÂMICA DO DIRETÓRIO BASE
# ----------------------------
# Detecta automaticamente se está no Google Colab ou em ambiente local
IN_COLAB = "google.colab" in str(get_ipython()) if "get_ipython" in globals() else False

if IN_COLAB:
    from google.colab import drive
    drive.mount("/content/drive")
    # Ajuste o caminho no seu Drive pessoal aqui:
    BASE_DIR = Path("/content/drive/MyDrive/UFG/Doutorado/Artigos/SBSR")
else:
    # Em máquina local, assume a raiz do repositório
    BASE_DIR = Path(__file__).resolve().parent if "__file__" in globals() else Path.cwd()


# ----------------------------
# 3. DADOS CEMADEN
# ----------------------------
CEMADEN_DIR = BASE_DIR / "data" / "CEMADEN"

# Arquivo com os dados diários consolidados
CEMADEN_DIARIO = (
    CEMADEN_DIR / "processados" / "CEMADEN_Goias_diario_2021_2025.csv"
)

# Arquivo com informações das estações
CEMADEN_ESTACOES = (
    CEMADEN_DIR / "processados" / "CEMADEN_Goias_estacoes_2021_2025.csv"
)


# ----------------------------
# 4. DADOS IMERG V07
# ----------------------------
IMERG_DIR = BASE_DIR / "data" / "CBRS_IMERG_Goias"


# ----------------------------
# 5. PERÍODO DA ANÁLISE E CRITÉRIOS
# ----------------------------
DATA_INICIAL = pd.Timestamp("2021-01-01")
DATA_FINAL = pd.Timestamp("2025-12-31")
ANOS = range(2021, 2026)

LIMIAR_COMPLETUDE = 0.80  # Mínimo de 80% de dados válidos


# ----------------------------
# 6. DIRETÓRIOS DE SAÍDA (ESTRUTURA MODULAR)
# ----------------------------
SAIDA_DIR = BASE_DIR / "resultados_CEMADEN_IMERG"
SAIDA_DIR.mkdir(parents=True, exist_ok=True)

subpastas = [
    "01_auditoria",
    "02_estacoes_elegiveis",
    "03_metricas_anuais",
    "04_metricas_2021_2025",
    "05_altitude",
    "06_graficos",
    "07_mapas",
]

for pasta in subpastas:
    (SAIDA_DIR / pasta).mkdir(exist_ok=True)


# ----------------------------
# 7. RESUMO DA CONFIGURAÇÃO
# ----------------------------
print("=" * 60)
print("CONFIGURAÇÃO DO PROJETO | CEMADEN x GPM IMERG V07")
print("=" * 60)
print(f"Ambiente: {'Google Colab' if IN_COLAB else 'Execução Local'}")
print(f"Diretório Base: {BASE_DIR}")
print(f"Período: {DATA_INICIAL.date()} a {DATA_FINAL.date()}")
print(f"Critério de completude: ≥ {LIMIAR_COMPLETUDE:.0%}")
print(f"Saídas configuradas em: {SAIDA_DIR}")

print("\nVerificação de arquivos de entrada:")
print(f"  • Dados diários CEMADEN: {'[OK]' if CEMADEN_DIARIO.exists() else '[NÃO ENCONTRADO]'}")
print(f"  • Estações CEMADEN:     {'[OK]' if CEMADEN_ESTACOES.exists() else '[NÃO ENCONTRADO]'}")
print("=" * 60)
