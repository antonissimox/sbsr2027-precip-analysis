# -*- coding: utf-8 -*-
"""
Aquisição e Recorte Espacial do GPM IMERG V07 (Final Run) para Goiás
Período: 01/01/2021 a 30/09/2025

Artigo: Validação Espacial do GPM IMERG V07 no Cerrado:
        Efeito da Altitude nos Vieses de Precipitação em Goiás (SBSR 2027)
Autores: Marco Antônio dos Santos, Klebber Teodomiro Martins Formiga
Repositório: https://github.com/antonioxbx/sbsr2027-precip-analysis
"""

import os
import gc
import shutil
from pathlib import Path
from datetime import datetime

import earthaccess
import numpy as np
import pandas as pd
import xarray as xr

# ==============================================================================
# CONFIGURAÇÕES E PARÂMETROS
# ==============================================================================
DATA_INICIAL = "2021-01-01"
DATA_FINAL   = "2025-09-30"

# Bounding box de Goiás com margem de segurança [Oeste, Sul, Leste, Norte]
BBOX_GOIAS = [-53.5, -19.0, -45.5, -12.0]

# Variáveis selecionadas do GPM IMERG V07 Final
VARIAVEIS = [
    "precipitation",
    "precipitation_cnt",
    "randomError",
    "probabilityLiquidPrecipitation"
]

# Diretórios locais (ajuste para o seu ambiente local ou Drive)
PASTA_BASE   = Path("./dados_imerg")
PASTA_RAW    = PASTA_BASE / "raw"
PASTA_DIARIO = PASTA_BASE / "diario"
PASTA_ANUAL  = PASTA_BASE / "anual"

PASTA_RAW.mkdir(parents=True, exist_ok=True)
PASTA_DIARIO.mkdir(parents=True, exist_ok=True)
PASTA_ANUAL.mkdir(parents=True, exist_ok=True)


def recortar_imerg(arquivo_bruto: Path, arquivo_saida: Path):
    """
    Abre o arquivo global diário do IMERG, recorta para o BBOX de Goiás,
    mantém apenas as variáveis necessárias e salva o NetCDF local.
    """
    with xr.open_dataset(arquivo_bruto, engine="netcdf4") as ds:
        ds_go = ds.sel(
            lat=slice(BBOX_GOIAS[1], BBOX_GOIAS[3]),
            lon=slice(BBOX_GOIAS[0], BBOX_GOIAS[2])
        )
        vars_presentes = [v for v in VARIAVEIS if v in ds_go.data_vars]
        ds_go = ds_go[vars_presentes]
        ds_go.to_netcdf(arquivo_saida, engine="netcdf4")

    gc.collect()


def consolidar_ano_netcdf(ano: int, pasta_diarios: Path, pasta_saida_anual: Path):
    """
    Une os arquivos diários recortados de um determinado ano em um arquivo
    único consolidado: IMERG_Goias_YYYY.nc
    """
    padrao = f"*{ano}*.nc"
    arquivos_ano = sorted(list(pasta_diarios.glob(padrao)))
    
    if not arquivos_ano:
        print(f"[{ano}] Nenhum recorte diário encontrado para consolidação.")
        return

    arq_anual = pasta_saida_anual / f"IMERG_Goias_{ano}.nc"
    print(f"\n[{ano}] Consolidando {len(arquivos_ano)} dias em: {arq_anual.name}...")
    
    datasets = [xr.open_dataset(f, engine="netcdf4") for f in arquivos_ano]
    ds_ano = xr.concat(datasets, dim="time").sortby("time")
    
    # Remover eventuais duplicações temporais
    _, indices_unicos = np.unique(ds_ano["time"].values, return_index=True)
    ds_ano = ds_ano.isel(time=np.sort(indices_unicos))
    
    ds_ano.to_netcdf(arq_anual, engine="netcdf4")
    
    for d in datasets:
        d.close()
    ds_ano.close()
    gc.collect()
    print(f"[{ano}] ✓ Arquivo anual finalizado com sucesso!")


def main():
    print("=" * 70)
    print("GPM IMERG V07 — DOWNLOAD E RECORTE REGIONAL (GOIÁS)")
    print("=" * 70)
    print(f"Período: {DATA_INICIAL} a {DATA_FINAL}")
    print(f"BBOX:    {BBOX_GOIAS}")
    print(f"Saída:   {PASTA_BASE.resolve()}\n")

    # Autenticação NASA Earthdata
    print("Autenticando via NASA Earthdata...")
    auth = earthaccess.login(persist=True)
    if not auth.authenticated:
        raise PermissionError("Falha na autenticação da NASA Earthdata. Verifique seu login.")
    print("✓ Autenticado com sucesso!\n")

    # Busca dos grânulos diários do produto Final Run V07
    print("Buscando grânulos GPM_3IMERGDF v07...")
    results = earthaccess.search_data(
        short_name="GPM_3IMERGDF",
        version="07",
        temporal=(DATA_INICIAL, DATA_FINAL),
        bounding_box=tuple(BBOX_GOIAS)
    )
    print(f"✓ Total de arquivos encontrados no catálogo da NASA: {len(results)}\n")

    if not results:
        print("Nenhum dado encontrado para o período especificado.")
        return

    # Processamento em lote (Download -> Recorte -> Exclusão do Bruto)
    print("Iniciando download e recorte espacial...")
    for i, granule in enumerate(results, 1):
        try:
            nome_esperado = granule["meta"]["native-id"]
        except Exception:
            nome_esperado = f"granule_{i}"

        recorte_nome = PASTA_DIARIO / f"{nome_esperado}_GOIAS.nc"
        
        # Pula se o dia já foi recortado anteriormente
        if recorte_nome.exists():
            continue

        # Baixa o grânulo global temporariamente
        arquivos_baixados = earthaccess.download([granule], local_path=str(PASTA_RAW))
        if not arquivos_baixados:
            continue

        arq_bruto = Path(arquivos_baixados[0])

        # Recorta para a malha de Goiás
        recortar_imerg(arq_bruto, recorte_nome)

        # Deleta o arquivo global bruto para poupar disco
        if arq_bruto.exists():
            os.remove(arq_bruto)

        if i % 50 == 0 or i == len(results):
            print(f"  Progresso: [{i}/{len(results)}] dias processados...")

    print("\n✓ Todos os recortes diários foram concluídos.")

    # Consolidação dos arquivos anuais (IMERG_Goias_2021.nc a 2025.nc)
    anos = range(int(DATA_INICIAL[:4]), int(DATA_FINAL[:4]) + 1)
    for ano in anos:
        consolidar_ano_netcdf(ano, PASTA_DIARIO, PASTA_ANUAL)

    print("\n" + "=" * 70)
    print("FLUXO DE DADOS ORBITAIS CONCLUÍDO COM SUCESSO!")
    print(f"Os arquivos anuais estão disponíveis em: {PASTA_ANUAL.resolve()}")
    print("=" * 70)


if __name__ == "__main__":
    main()
