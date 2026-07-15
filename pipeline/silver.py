# !/usr/bin/env python3
# -*- coding: utf-8 -*-


from pathlib import Path
import pandas as pd


# Read all files in the bronze data directory
raw_path_str = '../data/bronze'
raw_path = Path(raw_path_str)

df_array = []

for item in raw_path.rglob('*'):
    if item.is_file():
        df = pd.read_parquet(item)
        df_array.append(df)

df = pd.concat(df_array, ignore_index=True)

for registro, df in df.groupby('registro'):
    nome_arquivo = f'sped_{registro.lower()}.parquet'

    if registro == 'C100':
        print(nome_arquivo)

        sped_df = (
            df['linha_raw'].str.split('|', expand=True) # Convert to string and split by '|' and expand into multiple columns
            .iloc[:, 1:-1] # Remove first and last columns (which are empty due to the split)
            .rename(
                columns={
                    1: 'REG',
                    2: 'IND_OPER', # É isso mesmo?
                    3: 'IND_EMIT', # É isso mesmo?
                    4: 'cnpj_estabelecimento',
                    5: 'COD_MOD', # É isso mesmo?
                    6: 'COD_SIT', # É isso mesmo?
                    7: 'num_doc',
                    8: '', # Não achei. São os 3 primeiros dígitos do "num_doc".
                    9: 'dt_emi', # É o "data_emissao", correto? Não está na documentação.
                    10: 'dt_sai', # Não está na documentação.
                    11: 'valor_total',
                    12: 'vl_bc_icms_total', # Na documentação há "VL_BC_ICMS" e "VL_BC_ICMS_ST". É a soma dos dois?.
                    13: 'vl_icms_total', # Na documentação há "VL_ICMS" e "VL_ICMS_ST". É a soma dos dois?.
                    14: '', # Não achei
                    15: '', # Não achei
                    16: '', # Não achei
                    17: '', # Não achei
                    18: '', # Não achei
                    19: '', # Não achei
                    20: '', # Não achei
                    21: '', # Não achei
                    22: 'part_cnpj' # É o cnpj_emitente ou o cnpj_destinatario?
                }
            )
        )

        print(sped_df)

    if registro == 'C170':
        print(nome_arquivo)

        sped_df = (
            df['linha_raw'].str.split('|', expand=True) # Convert to string and split by '|' and expand into multiple columns
            .iloc[:, 1:-1] # Remove first and last columns (which are empty due to the split)
            .rename(
                columns={
                    1: 'REG',
                    2: 'i', # Não achei
                    3: 'cod', # Não achei. É o "COD_ITEM"?
                    4: 'desc', # É o "DESCR_COMPL"?
                    5: 'qtd', # É o "QTD"?
                    6: '', # Não achei
                    7: 'VL_ITEM',
                    8: 'CFOP',
                    9: 'cst', # Não achei. Há vários CSTs na documentação. É a soma de tudo?
                    10: 'bc_icms', # Não achei. É o "VL_BC_ICMS" ou "VL_BC_ICMS_ST"?
                    11: 'aliq', # Não achei. Há vários ALIQs na documentação. É a soma de tudo?
                    12: 'vl_icms', # É o "VL_ICMS" ou "VL_ICMS_ST"?
                    13: '', # Não achei
                    14: '', # Não achei
                    15: '', # Não achei
                    16: '', # Não achei
                    17: '', # Não achei
                    18: '' # Não achei
                }
            )
        )

        print(sped_df)

    if registro == 'E100':
        print(nome_arquivo)

        sped_df = (
            df['linha_raw'].str.split('|', expand=True) # Convert to string and split by '|' and expand into multiple columns
            .iloc[:, 1:-1] # Remove first and last columns (which are empty due to the split)
            .rename(
                columns={
                    1: 'REG',
                    2: 'DT_INI',
                    3: 'DT_FIN',
                }
            )
        )

        print(sped_df)

    if registro == 'E110':
        print(nome_arquivo)

        sped_df = (
            df['linha_raw'].str.split('|', expand=True) # Convert to string and split by '|' and expand into multiple columns
            .iloc[:, 1:-1] # Remove first and last columns (which are empty due to the split)
            .rename(
                columns={
                    1: 'REG',
                    2: 'vl_tot_debitos', # O generate_sped.py está gerando duplicado
                    3: '', # Não achei
                    4: '', # Não achei
                    5: 'vl_tot_debitos', # O generate_sped.py está gerando duplicado
                    6: 'saldo_anterior', # é o "vl_saldo_credor_ant"?
                    7: '', # Não achei
                    8: '', # Não achei
                    9: '', # Não achei
                    10: '', # Não achei
                    11: '', # Não achei
                    12: 'vl_tot_creditos', # O generate_sped.py está gerando duplicado
                    13: 'vl_tot_creditos', # O generate_sped.py está gerando duplicado
                    14: '', # Não achei
                    15: '', # Não achei
                    16: '', # Não achei
                    17: 'vl_saldo_credor', # Não achei
                    18: '', # Não achei
                    19: '', # Não achei
                    20: '', # Não achei
                    21: '', # Não achei
                    22: 'vl_apurado'
                }
            )
        )

        print(sped_df)
