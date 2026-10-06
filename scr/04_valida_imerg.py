# ============================================================
# BLOCO 4 — LOCALIZAÇÃO E VALIDAÇÃO DO IMERG V07
# ============================================================

print("=" * 60)
print("VALIDAÇÃO DOS DADOS GPM IMERG V07")
print("=" * 60)


# ------------------------------------------------------------
# 1. LOCALIZAR ARQUIVOS .NC / .NC4
# ------------------------------------------------------------
extensoes_suportadas = ["*.nc", "*.nc4", "*.NC", "*.NC4"]
arquivos_imerg = []

for ext in extensoes_suportadas:
    arquivos_imerg.extend(IMERG_DIR.rglob(ext))

arquivos_imerg = sorted(list(set(arquivos_imerg)))
total_arquivos = len(arquivos_imerg)

print(f"Diretório base: {IMERG_DIR}")
print(f"Arquivos NetCDF encontrados: {total_arquivos:,}")

if total_arquivos == 0:
    raise FileNotFoundError(
        f"Nenhum arquivo NetCDF (.nc/.nc4) localizado em:\n{IMERG_DIR}"
    )


# ------------------------------------------------------------
# 2. AMOSTRAGEM DE ARQUIVOS
# ------------------------------------------------------------
print("\nExemplo dos primeiros arquivos indexados:")
for arq in arquivos_imerg[:5]:
    print(f"  • {arq.name}")

if total_arquivos > 5:
    print(f"  ... e outros {total_arquivos - 5} arquivos.")


# ------------------------------------------------------------
# 3. INSPEÇÃO DETALHADA DO DATASET DE TESTE
# ------------------------------------------------------------
arquivo_teste = arquivos_imerg[0]

print("\n" + "=" * 60)
print(f"INSPEÇÃO DE METADADOS: {arquivo_teste.name}")
print("=" * 60)

with xr.open_dataset(arquivo_teste) as ds_teste:
    print("Dimensões detectadas:")
    for dim, tam in ds_teste.dims.items():
        print(f"  - {dim}: {tam}")

    print("\nCoordenadas disponíveis:")
    for coord in ds_teste.coords:
        print(f"  - {coord}")

    print("\nVariáveis de dados:")
    for var in ds_teste.data_vars:
        print(f"  - {var}")

    # ------------------------------------------------------------
    # 4. RESOLUÇÃO E LIMITES ESPACIAIS
    # ------------------------------------------------------------
    coord_lat = next((c for c in ["lat", "latitude"] if c in ds_teste.coords), None)
    coord_lon = next((c for c in ["lon", "longitude"] if c in ds_teste.coords), None)

    print("\nCobertura Geográfica:")
    if coord_lat and coord_lon:
        lats = ds_teste[coord_lat].values
        lons = ds_teste[coord_lon].values
        print(f"  • Latitude:  [{np.nanmin(lats):.4f} a {np.nanmax(lats):.4f}] (n = {len(lats)})")
        print(f"  • Longitude: [{np.nanmin(lons):.4f} a {np.nanmax(lons):.4f}] (n = {len(lons)})")
    else:
        print("  [AVISO] Nomes padrão de latitude/longitude não identificados diretamente.")

    # ------------------------------------------------------------
    # 5. MAPEAMENTO DA VARIÁVEL DE PRECIPITAÇÃO E TEMPO
    # ------------------------------------------------------------
    prioridade_vars = ["precipitationCal", "precipitation", "precipitationUncal"]
    var_precip = next((v for v in prioridade_vars if v in ds_teste.data_vars), None)

    if not var_precip:
        raise ValueError(
            "Nenhuma variável conhecida de precipitação encontrada "
            f"(tentativas: {prioridade_vars})."
        )

    coord_tempo = next((c for c in ["time", "datetime", "date"] if c in ds_teste.coords), None)

    da_precip = ds_teste[var_precip]
    unidade = da_precip.attrs.get("units", "unidade não especificada")
    ordem_dims = da_precip.dims

    print("\nVariável de Precipitação Selecionada:")
    print(f"  • Nome: {var_precip}")
    print(f"  • Unidade: {unidade}")
    print(f"  • Ordem das dimensões: {ordem_dims}")
    print(f"  • Shape: {da_precip.shape}")
    print(f"  • Coordenada temporal: {coord_tempo or 'Não identificada como coordenada direta'}")

# ------------------------------------------------------------
# 6. CONFIGURAÇÃO GLOBAL PARA OS PRÓXIMOS BLOCOS
# ------------------------------------------------------------
CONFIG_IMERG = {
    "var_precip": var_precip,
    "coord_lat": coord_lat,
    "coord_lon": coord_lon,
    "coord_tempo": coord_tempo,
}

print("\n" + "=" * 60)
print("VALIDAÇÃO CONCLUÍDA COM SUCESSO")
print(f"Variável-alvo pronta para extração: '{var_precip}'")
print("=" * 60)
