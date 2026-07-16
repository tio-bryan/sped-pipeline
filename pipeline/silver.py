# !/usr/bin/env python3
# -*- coding: utf-8 -*-


import sys
from pathlib import Path
import pandas as pd
from functions import save_parquet_idempotent


# Add the parent directory of the current file to sys.path for function imports
sys.path.append(str(Path(__file__).resolve().parent))

# Read all files in the bronze data directory
raw_path_str = '../data/bronze'
raw_path = Path(raw_path_str)

df_array = []

for item in raw_path.rglob('*'):
    if item.is_file():
        df = pd.read_parquet(item)
        df_array.append(df)

# Concatenate all DFs in the df_array
df = pd.concat(df_array, ignore_index=True)

for registro, df in df.groupby('registro'):
    nome_arquivo = f'../data/silver/sped_{registro.lower()}.parquet'

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
                    8: '8', # Não achei. São os 3 primeiros dígitos do "num_doc".
                    9: 'dt_emi', # É o "data_emissao", correto? Não está na documentação.
                    10: 'dt_sai', # Não está na documentação.
                    11: 'valor_total',
                    12: 'vl_bc_icms_total', # Na documentação há "VL_BC_ICMS" e "VL_BC_ICMS_ST". É a soma dos dois?.
                    13: 'vl_icms_total', # Na documentação há "VL_ICMS" e "VL_ICMS_ST". É a soma dos dois?.
                    14: '14', # Não achei
                    15: '15', # Não achei
                    16: '16', # Não achei
                    17: '17', # Não achei
                    18: '18', # Não achei
                    19: '19', # Não achei
                    20: '20', # Não achei
                    21: '21', # Não achei
                    22: 'part_cnpj' # É o cnpj_emitente ou o cnpj_destinatario?
                }
            )
        )

        # Insert 'cnpj' and 'periodo' columns from df into the sped_df
        sped_df.insert(0, 'cnpj', df['cnpj'])
        sped_df.insert(1, 'periodo', df['periodo'])

        # Resets the index of "sped_df", as it retained the index from the old df.
        sped_df = sped_df.reset_index(drop=True)

        # Parse 'dt_emi' and 'dt_sai' columns to datetime format
        sped_df['dt_emi'] = pd.to_datetime(sped_df['dt_emi'], format='%d%m%Y')
        sped_df['dt_sai'] = pd.to_datetime(sped_df['dt_sai'], format='%d%m%Y')

        # Define column types
        sped_df = sped_df.astype({
            'cnpj': str,
            'periodo': 'datetime64[ns]',
            'REG': str,
            'IND_OPER': int,
            'IND_EMIT': int,
            'cnpj_estabelecimento': str,
            'COD_MOD': str,
            'COD_SIT': int,
            'num_doc': int,
            '8': str,
            'dt_emi': 'datetime64[ns]',
            'dt_sai': 'datetime64[ns]',
            'valor_total': float,
            'vl_bc_icms_total': float,
            'vl_icms_total': float,
            '14': float,
            '15': float,
            '16': float,
            '17': float,
            '18': float,
            '19': float,
            '20': float,
            '21': str, # Verificar
            'part_cnpj': str
        })

        # Validation rules
        valid_condition = (
            sped_df['cnpj'].notna() &
            sped_df['periodo'].notna() &
            sped_df['REG'].notna() &
            sped_df['IND_OPER'].notna() &
            sped_df['IND_EMIT'].notna() &
            sped_df['cnpj_estabelecimento'].notna() &
            sped_df['COD_MOD'].notna() &
            sped_df['COD_SIT'].notna() &
            sped_df['num_doc'].notna() &
            sped_df['8'].notna() &
            sped_df['dt_emi'].notna() &
            sped_df['dt_sai'].notna() &
            sped_df['valor_total'].notna() &
            sped_df['vl_bc_icms_total'].notna() &
            sped_df['vl_icms_total'].notna() &
            sped_df['14'].notna() &
            sped_df['15'].notna() &
            sped_df['16'].notna() &
            sped_df['17'].notna() &
            sped_df['18'].notna() &
            sped_df['19'].notna() &
            sped_df['20'].notna() &
            sped_df['21'].notna() &
            sped_df['part_cnpj'].notna()
        )

        # Split into two separate DataFrames
        sped_df_valid = sped_df[valid_condition].copy()
        sped_df_invalid = sped_df[~valid_condition].copy()

        sped_df_invalid['motivo_erro'] = 'Linha contém valor nulo em uma das colunas obrigatórias'

        print(sped_df_valid)
        print(sped_df_invalid)

        save_parquet_idempotent(sped_df_valid, nome_arquivo)
        save_parquet_idempotent(sped_df_invalid, f'{nome_arquivo}_invalid')

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
                    4: 'descr', # É o "DESCR_COMPL"?
                    5: 'qtd', # É o "QTD"?
                    6: '6', # Não achei
                    7: 'VL_ITEM',
                    8: 'CFOP',
                    9: 'cst', # Não achei. Há vários CSTs na documentação. É a soma de tudo?
                    10: 'bc_icms', # Não achei. É o "VL_BC_ICMS" ou "VL_BC_ICMS_ST"?
                    11: 'aliq', # Não achei. Há vários ALIQs na documentação. É a soma de tudo?
                    12: 'vl_icms', # É o "VL_ICMS" ou "VL_ICMS_ST"?
                    13: '13', # Não achei
                    14: '14', # Não achei
                    15: '15', # Não achei
                    16: '16', # Não achei
                    17: '17', # Não achei
                    18: '18' # Não achei
                }
            )
        )

        # Insert 'cnpj' and 'periodo' columns from df into the sped_df
        sped_df.insert(0, 'cnpj', df['cnpj'])
        sped_df.insert(1, 'periodo', df['periodo'])

        # Resets the index of "sped_df", as it retained the index from the old df.
        sped_df = sped_df.reset_index(drop=True)

        # Define column types
        sped_df = sped_df.astype({
            'cnpj': str,
            'periodo': 'datetime64[ns]',
            'REG': str,
            'i': int,
            'cod': str,
            'descr': str,
            'qtd': str, # Verificar
            '6': str,
            'VL_ITEM': float,
            'CFOP': str, # Verificar
            'cst': str,
            'bc_icms': float,
            'aliq': float,
            'vl_icms': float,
            '13': float,
            '14': float,
            '15': float,
            '16': float,
            '17': float,
            '18': str # Verificar
        })

        # Validation rules
        valid_condition = (
            sped_df['cnpj'].notna() &
            sped_df['periodo'].notna() &
            sped_df['REG'].notna() &
            sped_df['i'].notna() &
            sped_df['cod'].notna() &
            sped_df['descr'].notna() &
            sped_df['qtd'].notna() &
            sped_df['6'].notna() &
            sped_df['VL_ITEM'].notna() &
            sped_df['CFOP'].notna() &
            sped_df['cst'].notna() &
            sped_df['bc_icms'].notna() &
            sped_df['aliq'].notna() &
            sped_df['vl_icms'].notna() &
            sped_df['13'].notna() &
            sped_df['14'].notna() &
            sped_df['15'].notna() &
            sped_df['16'].notna() &
            sped_df['17'].notna() &
            sped_df['18'].notna()
        )

        # Split into two separate DataFrames
        sped_df_valid = sped_df[valid_condition].copy()
        sped_df_invalid = sped_df[~valid_condition].copy()

        sped_df_invalid['motivo_erro'] = 'Linha contém valor nulo em uma das colunas obrigatórias'

        print(sped_df_valid)
        print(sped_df_invalid)

        save_parquet_idempotent(sped_df_valid, nome_arquivo)
        save_parquet_idempotent(sped_df_invalid, f'{nome_arquivo}_invalid')

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

        # Insert 'cnpj' and 'periodo' columns from df into the sped_df
        sped_df.insert(0, 'cnpj', df['cnpj'])
        sped_df.insert(1, 'periodo', df['periodo'])

        # Resets the index of "sped_df", as it retained the index from the old df.
        sped_df = sped_df.reset_index(drop=True)

        # Parse 'DT_INI' and 'DT_FIN' columns to datetime format
        sped_df['DT_INI'] = pd.to_datetime(sped_df['DT_INI'], format='%d%m%Y')
        sped_df['DT_FIN'] = pd.to_datetime(sped_df['DT_FIN'], format='%d%m%Y')

        # Define column types
        sped_df = sped_df.astype({
            'cnpj': str,
            'periodo': 'datetime64[ns]',
            'REG': str,
            'DT_INI': 'datetime64[ns]',
            'DT_FIN': 'datetime64[ns]'
        })

        # Validation rules
        valid_condition = (
            sped_df['cnpj'].notna() &
            sped_df['periodo'].notna() &
            sped_df['REG'].notna() &
            sped_df['DT_INI'].notna() &
            sped_df['DT_FIN'].notna()
        )

        # Split into two separate DataFrames
        sped_df_valid = sped_df[valid_condition].copy()
        sped_df_invalid = sped_df[~valid_condition].copy()

        sped_df_invalid['motivo_erro'] = 'Linha contém valor nulo em uma das colunas obrigatórias'

        print(sped_df_valid)
        print(sped_df_invalid)

        save_parquet_idempotent(sped_df_valid, nome_arquivo)
        save_parquet_idempotent(sped_df_invalid, f'{nome_arquivo}_invalid')

    if registro == 'E110':
        print(nome_arquivo)

        sped_df = (
            df['linha_raw'].str.split('|', expand=True) # Convert to string and split by '|' and expand into multiple columns
            .iloc[:, 1:-1] # Remove first and last columns (which are empty due to the split)
            .rename(
                columns={
                    1: 'REG',
                    2: 'vl_tot_debitos', # O generate_sped.py está gerando duplicado
                    3: '3', # Não achei
                    4: '4', # Não achei
                    5: 'vl_tot_debitos2', # O generate_sped.py está gerando duplicado
                    6: 'saldo_anterior', # é o "vl_saldo_credor_ant"?
                    7: '7', # Não achei
                    8: '8', # Não achei
                    9: '9', # Não achei
                    10: '10', # Não achei
                    11: '11', # Não achei
                    12: 'vl_tot_creditos', # O generate_sped.py está gerando duplicado
                    13: 'vl_tot_creditos2', # O generate_sped.py está gerando duplicado
                    14: '14', # Não achei
                    15: '15', # Não achei
                    16: '16', # Não achei
                    17: 'vl_saldo_credor', # Não achei
                    18: '18', # Não achei
                    19: '19', # Não achei
                    20: '20', # Não achei
                    21: '21', # Não achei
                    22: 'vl_apurado'
                }
            )
        )

        # Insert 'cnpj' and 'periodo' columns from df into the sped_df
        sped_df.insert(0, 'cnpj', df['cnpj'])
        sped_df.insert(1, 'periodo', df['periodo'])

        # Resets the index of "sped_df", as it retained the index from the old df.
        sped_df = sped_df.reset_index(drop=True)

        # Parse 'periodo' column to datetime format
        sped_df['periodo'] = pd.to_datetime(sped_df['periodo'], format='%Y-%m')

        # Define column types
        sped_df = sped_df.astype({
            'cnpj': str,
            'periodo': 'datetime64[ns]',
            'REG': str,
            'vl_tot_debitos': float,
            '3': float,
            '4': float,
            'vl_tot_debitos2': float,
            'saldo_anterior': float,
            '7': float,
            '8': float,
            '9': float,
            '10': float,
            '11': float,
            'vl_tot_creditos': float,
            'vl_tot_creditos2': float,
            '14': float,
            '15': float,
            '16': float,
            'vl_saldo_credor': float,
            '18': float,
            '19': float,
            '20': float,
            '21': float,
            'vl_apurado': float
        })

        # Validation rules
        valid_condition = (
            sped_df['cnpj'].notna() &
            sped_df['periodo'].notna() &
            sped_df['REG'].notna() &
            sped_df['vl_tot_debitos'].notna() &
            sped_df['3'].notna() &
            sped_df['4'].notna() &
            sped_df['vl_tot_debitos2'].notna() &
            sped_df['saldo_anterior'].notna() &
            sped_df['7'].notna() &
            sped_df['8'].notna() &
            sped_df['9'].notna() &
            sped_df['10'].notna() &
            sped_df['11'].notna() &
            sped_df['vl_tot_creditos'].notna() &
            sped_df['vl_tot_creditos2'].notna() &
            sped_df['14'].notna() &
            sped_df['15'].notna() &
            sped_df['16'].notna() &
            sped_df['vl_saldo_credor'].notna() &
            sped_df['18'].notna() &
            sped_df['19'].notna() &
            sped_df['20'].notna() &
            sped_df['21'].notna() &
            sped_df['vl_apurado'].notna()
        )

        # Split into two separate DataFrames
        sped_df_valid = sped_df[valid_condition].copy()
        sped_df_invalid = sped_df[~valid_condition].copy()

        sped_df_invalid['motivo_erro'] = 'Linha contém valor nulo em uma das colunas obrigatórias'

        print(sped_df_valid)
        print(sped_df_invalid)

        save_parquet_idempotent(sped_df_valid, nome_arquivo)
        save_parquet_idempotent(sped_df_invalid, f'{nome_arquivo}_invalid')
