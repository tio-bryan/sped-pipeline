# !/usr/bin/env python3
# -*- coding: utf-8 -*-


import sys
from pathlib import Path
import pandas as pd
from functions import save_parquet_idempotent


# Add the parent directory of the current file to sys.path for function imports
sys.path.append(str(Path(__file__).resolve().parent))

# Read all files in the bronze data directory
raw_path = Path('../data/bronze')

df_array = []

for item in raw_path.rglob('*'):
    if item.is_file() and not any(part.startswith(".gitkeep") for part in item.parts):
        df = pd.read_parquet(item)
        df_array.append(df)

# Concatenate all DFs in the df_array
df = pd.concat(df_array, ignore_index=True)

for registro, df in df.groupby('registro'):
    path_arquivo = '../data/silver/'
    nome_arquivo = f'sped_{registro.lower()}'

    if registro == 'C100':
        sped_df = (
            df['linha_raw'].str.split('|', expand=True) # Convert to string and split by '|' and expand into multiple columns
            .iloc[:, 1:-1] # Remove first and last columns (which are empty due to the split)
            .rename(
                columns={
                    1: 'REG',
                    2: 'IND_OPER',
                    3: 'IND_EMIT',
                    4: 'COD_PART', # cnpj_estabelecimento
                    5: 'COD_MOD',
                    6: 'COD_SIT',
                    7: 'SER',
                    8: 'NUM_DOC', # num_doc
                    9: 'CHV_NFE',
                    10: 'DT_DOC', # data_emissao
                    11: 'DT_E_S',
                    12: 'VL_DOC', # valor_total
                    13: 'IND_PGTO',
                    14: 'VL_DESC',
                    15: 'VL_ABAT_NT',
                    16: 'VL_MERC',
                    17: 'IND_FRT',
                    18: 'VL_FRT',
                    19: 'VL_SEG',
                    20: 'VL_OUT_DA',
                    21: 'VL_BC_ICMS',
                    22: 'VL_ICMS',
                    23: 'VL_BC_ICMS_ST',
                    24: 'VL_ICMS_ST',
                    25: 'VL_IPI',
                    26: 'VL_PIS',
                    27: 'VL_COFINS',
                    28: 'VL_PIS_ST',
                    29: 'VL_COFINS_ST'
                }
            )
        )

        # Insert 'cnpj' and 'periodo' columns from df into the sped_df
        sped_df.insert(0, 'cnpj', df['cnpj'])
        sped_df.insert(1, 'periodo', df['periodo'])

        # Resets the index of "sped_df", as it retained the index from the old df.
        sped_df = sped_df.reset_index(drop=True)

        # Validation rules
        valid_condition = (
            sped_df['cnpj'].notna() &
            sped_df['periodo'].notna() &
            sped_df['REG'].notna() &
            sped_df['IND_OPER'].notna() &
            sped_df['IND_EMIT'].notna() &
            sped_df['COD_PART'].notna() &
            sped_df['COD_MOD'].notna() &
            sped_df['COD_SIT'].notna() &
            sped_df['SER'].notna() &
            sped_df['NUM_DOC'].notna() &
            sped_df['CHV_NFE'].notna() &
            sped_df['DT_DOC'].notna() &
            sped_df['DT_E_S'].notna() &
            sped_df['VL_DOC'].notna() &
            sped_df['IND_PGTO'].notna() &
            sped_df['VL_DESC'].notna() &
            sped_df['VL_ABAT_NT'].notna() &
            sped_df['VL_MERC'].notna() &
            sped_df['IND_FRT'].notna() &
            sped_df['VL_FRT'].notna() &
            sped_df['VL_SEG'].notna() &
            sped_df['VL_OUT_DA'].notna() &
            sped_df['VL_BC_ICMS'].notna() &
            sped_df['VL_ICMS'].notna() &
            sped_df['VL_BC_ICMS_ST'].notna() &
            sped_df['VL_ICMS_ST'].notna() &
            sped_df['VL_IPI'].notna() &
            sped_df['VL_PIS'].notna() &
            sped_df['VL_COFINS'].notna() &
            sped_df['VL_PIS_ST'].notna() &
            sped_df['VL_COFINS_ST'].notna()
        )

        # Split into two separate DataFrames
        sped_df_valid = sped_df[valid_condition].copy()

        # Parse 'DT_DOC' and 'DT_E_S' columns to datetime format
        sped_df_valid['DT_DOC'] = pd.to_datetime(sped_df_valid['DT_DOC'], format='%d%m%Y')
        sped_df_valid['DT_E_S'] = pd.to_datetime(sped_df_valid['DT_E_S'], format='%d%m%Y')

        # Define column types
        sped_df_valid = sped_df_valid.astype({
            'cnpj': str,
            'periodo': 'datetime64[ns]',
            'REG': str,
            'IND_OPER': int,
            'IND_EMIT': int,
            'COD_PART': str,
            'COD_MOD': str,
            'COD_SIT': int,
            'SER': str,
            'NUM_DOC': int,
            'CHV_NFE': str, # I couldn't cast it because the number is too large
            'DT_DOC': 'datetime64[ns]',
            'DT_E_S': 'datetime64[ns]',
            'VL_DOC': float,
            'IND_PGTO': int,
            'VL_DESC': float,
            'VL_ABAT_NT': float,
            'VL_MERC': float,
            'IND_FRT': int,
            'VL_FRT': float,
            'VL_SEG': float,
            'VL_OUT_DA': float,
            'VL_BC_ICMS': float,
            'VL_ICMS': float,
            'VL_BC_ICMS_ST': float,
            'VL_ICMS_ST': float,
            'VL_IPI': float,
            'VL_PIS': float,
            'VL_COFINS': float,
            'VL_PIS_ST': float,
            'VL_COFINS_ST': float
        })

        print(f'\n{nome_arquivo}.parquet\n')
        print(sped_df_valid)
        save_parquet_idempotent(sped_df_valid, f'{path_arquivo}{nome_arquivo}.parquet')

        sped_df_invalid = sped_df[~valid_condition].copy()
        sped_df_invalid['motivo_erro'] = 'Linha contém valor nulo em uma das colunas obrigatórias'

        print(f'\n{nome_arquivo}_invalid.parquet\n')
        print(sped_df_invalid)
        save_parquet_idempotent(sped_df_invalid, f'{path_arquivo}{nome_arquivo}_invalid.parquet')

    if registro == 'C170':
        print(df['linha_raw'].str.split('|', expand=True).iloc[:, 1:-1])
        sped_df = (
            df['linha_raw'].str.split('|', expand=True) # Convert to string and split by '|' and expand into multiple columns
            .iloc[:, 1:-1] # Remove first and last columns (which are empty due to the split)
            .rename(
                columns={
                    1: 'REG',
                    2: 'NUM_ITEM',
                    3: 'COD_ITEM',
                    4: 'DESCR_COMPL',
                    5: 'QTD',
                    6: 'UNID',
                    7: 'VL_ITEM',
                    8: 'VL_DESC',
                    9: 'IND_MOV',
                    10: 'CST_ICMS',
                    11: 'CFOP',
                    12: 'COD_NAT',
                    13: 'VL_BC_ICMS',
                    14: 'ALIQ_ICMS',
                    15: 'VL_ICMS',
                    16: 'VL_BC_ICMS_ST',
                    17: 'ALIQ_ST',
                    18: 'VL_ICMS_ST',
                    19: 'IND_APUR',
                    20: 'CST_IPI',
                    21: 'COD_ENQ',
                    22: 'VL_BC_IPI',
                    23: 'ALIQ_IPI',
                    24: 'VL_IPI',
                    25: 'CST_PIS',
                    26: 'VL_BC_PIS',
                    27: 'ALIQ_PIS_PERCENTUAL',
                    28: 'QUANT_BC_PIS',
                    29: 'ALIQ_PIS_REAIS',
                    30: 'VL_PIS',
                    31: 'CST_COFINS',
                    32: 'VL_BC_COFINS',
                    33: 'ALIQ_COFINS_PERCENTUAL',
                    34: 'QUANT_BC_COFINS',
                    35: 'ALIQ_COFINS_REAIS',
                    36: 'VL_COFINS',
                    37: 'COD_CTA',
                    38: 'VL_ABAT_NT'
                }
            )
        )

        # Insert 'cnpj' and 'periodo' columns from df into the sped_df
        sped_df.insert(0, 'cnpj', df['cnpj'])
        sped_df.insert(1, 'periodo', df['periodo'])

        # Resets the index of "sped_df", as it retained the index from the old df.
        sped_df = sped_df.reset_index(drop=True)

        # Validation rules
        valid_condition = (
            sped_df['cnpj'].notna() &
            sped_df['periodo'].notna() &
            sped_df['REG'].notna() &
            sped_df['NUM_ITEM'].notna() &
            sped_df['COD_ITEM'].notna() &
            sped_df['DESCR_COMPL'].notna() &
            sped_df['QTD'].notna() &
            sped_df['UNID'].notna() &
            sped_df['VL_ITEM'].notna() &
            sped_df['VL_DESC'].notna() &
            sped_df['IND_MOV'].notna() &
            sped_df['CST_ICMS'].notna() &
            sped_df['CFOP'].notna() &
            sped_df['COD_NAT'].notna() &
            sped_df['VL_BC_ICMS'].notna() &
            sped_df['ALIQ_ICMS'].notna() &
            sped_df['VL_ICMS'].notna() &
            sped_df['VL_BC_ICMS_ST'].notna() &
            sped_df['ALIQ_ST'].notna() &
            sped_df['VL_ICMS_ST'].notna() &
            sped_df['IND_APUR'].notna() &
            sped_df['CST_IPI'].notna() &
            sped_df['COD_ENQ'].notna() &
            sped_df['VL_BC_IPI'].notna() &
            sped_df['ALIQ_IPI'].notna() &
            sped_df['VL_IPI'].notna() &
            sped_df['CST_PIS'].notna() &
            sped_df['VL_BC_PIS'].notna() &
            sped_df['ALIQ_PIS_PERCENTUAL'].notna() &
            sped_df['QUANT_BC_PIS'].notna() &
            sped_df['ALIQ_PIS_REAIS'].notna() &
            sped_df['VL_PIS'].notna() &
            sped_df['CST_COFINS'].notna() &
            sped_df['VL_BC_COFINS'].notna() &
            sped_df['ALIQ_COFINS_PERCENTUAL'].notna() &
            sped_df['QUANT_BC_COFINS'].notna() &
            sped_df['ALIQ_COFINS_REAIS'].notna() &
            sped_df['VL_COFINS'].notna() &
            sped_df['COD_CTA'].notna() &
            sped_df['VL_ABAT_NT'].notna()
        )

        # Split into two separate DataFrames
        sped_df_valid = sped_df[valid_condition].copy()

        # Define column types
        sped_df_valid = sped_df_valid.astype({
            'cnpj': str,
            'periodo': 'datetime64[ns]',
            'REG': str,
            'NUM_ITEM': str,
            'COD_ITEM': str,
            'DESCR_COMPL': str,
            'QTD': float,
            'UNID': str,
            'VL_ITEM': float,
            'VL_DESC': float,
            'IND_MOV': str,
            'CST_ICMS': int,
            'CFOP': int,
            'COD_NAT': str,
            'VL_BC_ICMS': float,
            'ALIQ_ICMS': float,
            'VL_ICMS': float,
            'VL_BC_ICMS_ST': float,
            'ALIQ_ST': float,
            'VL_ICMS_ST': float,
            'IND_APUR': str,
            'CST_IPI': str,
            'COD_ENQ': str,
            'VL_BC_IPI': float,
            'ALIQ_IPI': float,
            'VL_IPI': float,
            'CST_PIS': str,
            'VL_BC_PIS': float,
            'ALIQ_PIS_PERCENTUAL': float,
            'QUANT_BC_PIS': float,
            'ALIQ_PIS_REAIS': float,
            'VL_PIS': float,
            'CST_COFINS': str,
            'VL_BC_COFINS': float,
            'ALIQ_COFINS_PERCENTUAL': float,
            'QUANT_BC_COFINS': float,
            'ALIQ_COFINS_REAIS': float,
            'VL_COFINS': float,
            'COD_CTA': str,
            'VL_ABAT_NT': float
        })

        print(f'\n{nome_arquivo}.parquet\n')
        print(sped_df_valid)
        save_parquet_idempotent(sped_df_valid, f'{path_arquivo}{nome_arquivo}.parquet')

        sped_df_invalid = sped_df[~valid_condition].copy()
        sped_df_invalid['motivo_erro'] = 'Linha contém valor nulo em uma das colunas obrigatórias'

        print(f'\n{nome_arquivo}_invalid.parquet\n')
        print(sped_df_invalid)
        save_parquet_idempotent(sped_df_invalid, f'{path_arquivo}{nome_arquivo}_invalid.parquet')

    if registro == 'E100':
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

        # Parse 'DT_INI' and 'DT_FIN' columns to datetime format
        sped_df_valid['DT_INI'] = pd.to_datetime(sped_df_valid['DT_INI'], format='%d%m%Y')
        sped_df_valid['DT_FIN'] = pd.to_datetime(sped_df_valid['DT_FIN'], format='%d%m%Y')

        # Define column types
        sped_df_valid = sped_df_valid.astype({
            'cnpj': str,
            'periodo': 'datetime64[ns]',
            'REG': str,
            'DT_INI': 'datetime64[ns]',
            'DT_FIN': 'datetime64[ns]'
        })

        print(f'\n{nome_arquivo}.parquet\n')
        print(sped_df_valid)
        save_parquet_idempotent(sped_df_valid, f'{path_arquivo}{nome_arquivo}.parquet')

        sped_df_invalid = sped_df[~valid_condition].copy()
        sped_df_invalid['motivo_erro'] = 'Linha contém valor nulo em uma das colunas obrigatórias'

        print(f'\n{nome_arquivo}_invalid.parquet\n')
        print(sped_df_invalid)
        save_parquet_idempotent(sped_df_invalid, f'{path_arquivo}{nome_arquivo}_invalid.parquet')

    if registro == 'E110':
        print(df['linha_raw'].str.split('|', expand=True).iloc[:, 1:-1])
        sped_df = (
            df['linha_raw'].str.split('|', expand=True) # Convert to string and split by '|' and expand into multiple columns
            .iloc[:, 1:-1] # Remove first and last columns (which are empty due to the split)
            .rename(
                columns={
                    1: 'REG',
                    2: 'VL_TOT_DEBITOS',
                    3: 'VL_AJ_DEBITOS',
                    4: 'VL_TOT_AJ_DEBITOS',
                    5: 'VL_ESTORNOS_CRED',
                    6: 'VL_TOT_CREDITOS',
                    7: 'VL_AJ_CREDITOS',
                    8: 'VL_TOT_AJ_CREDITOS',
                    9: 'VL_ESTORNOS_DEB',
                    10: 'VL_SLD_CREDOR_ANT',
                    11: 'VL_SLD_APURADO',
                    12: 'VL_TOT_DED',
                    13: 'VL_ICMS_RECOLHER',
                    14: 'VL_SLD_CREDOR_TRANSPORTAR',
                    15: 'DEB_ESP'
                }
            )
        )

        # Insert 'cnpj' and 'periodo' columns from df into the sped_df
        sped_df.insert(0, 'cnpj', df['cnpj'])
        sped_df.insert(1, 'periodo', df['periodo'])

        # Resets the index of "sped_df", as it retained the index from the old df.
        sped_df = sped_df.reset_index(drop=True)

        # Validation rules
        valid_condition = (
            sped_df['cnpj'].notna() &
            sped_df['periodo'].notna() &
            sped_df['REG'].notna() &
            sped_df['VL_TOT_DEBITOS'].notna() &
            sped_df['VL_AJ_DEBITOS'].notna() &
            sped_df['VL_TOT_AJ_DEBITOS'].notna() &
            sped_df['VL_ESTORNOS_CRED'].notna() &
            sped_df['VL_TOT_CREDITOS'].notna() &
            sped_df['VL_AJ_CREDITOS'].notna() &
            sped_df['VL_TOT_AJ_CREDITOS'].notna() &
            sped_df['VL_ESTORNOS_DEB'].notna() &
            sped_df['VL_SLD_CREDOR_ANT'].notna() &
            sped_df['VL_SLD_APURADO'].notna() &
            sped_df['VL_TOT_DED'].notna() &
            sped_df['VL_ICMS_RECOLHER'].notna() &
            sped_df['VL_SLD_CREDOR_TRANSPORTAR'].notna() &
            sped_df['DEB_ESP'].notna()
        )

        # Split into two separate DataFrames
        sped_df_valid = sped_df[valid_condition].copy()

        # Define column types
        sped_df = sped_df.astype({
            'cnpj': str,
            'periodo': 'datetime64[ns]',
            'REG': str,
            'VL_TOT_DEBITOS': float,
            'VL_AJ_DEBITOS': float,
            'VL_TOT_AJ_DEBITOS': float,
            'VL_ESTORNOS_CRED': float,
            'VL_TOT_CREDITOS': float,
            'VL_AJ_CREDITOS': float,
            'VL_TOT_AJ_CREDITOS': float,
            'VL_ESTORNOS_DEB': float,
            'VL_SLD_CREDOR_ANT': float,
            'VL_SLD_APURADO': float,
            'VL_TOT_DED': float,
            'VL_ICMS_RECOLHER': float,
            'VL_SLD_CREDOR_TRANSPORTAR': float,
            'DEB_ESP': float
        })

        print(f'\n{nome_arquivo}.parquet\n')
        print(sped_df_valid)
        save_parquet_idempotent(sped_df_valid, f'{path_arquivo}{nome_arquivo}.parquet')

        sped_df_invalid = sped_df[~valid_condition].copy()
        sped_df_invalid['motivo_erro'] = 'Linha contém valor nulo em uma das colunas obrigatórias'
        
        print(f'\n{nome_arquivo}_invalid.parquet\n')
        print(sped_df_invalid)
        save_parquet_idempotent(sped_df_invalid, f'{path_arquivo}{nome_arquivo}_invalid.parquet')
