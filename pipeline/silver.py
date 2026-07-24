# !/usr/bin/env python3
# -*- coding: utf-8 -*-


import sys
from pathlib import Path
import pandas as pd
import itertools
from functions import save_parquet_idempotent


# Add the parent directory of the current file to sys.path for function imports
sys.path.append(str(Path(__file__).resolve().parent))

# Read all files in the bronze data directory
raw_path = Path('../data/bronze')

df_array = []

for item in raw_path.rglob('*'): # Iterates over all files except .gitkeep and merges all parquet files
    if item.is_file() and not any(part.startswith(".gitkeep") for part in item.parts):
        df = pd.read_parquet(item)
        df_array.append(df)

# Concatenate all DFs in the df_array
df = pd.concat(df_array, ignore_index=True)

for register, df in df.groupby('registro'):
    file_path = '../data/silver/'
    file_name = f'sped_{register.lower()}'

    if register in ['C100', 'C170', 'E100', 'E110']:
        columns = {
            'C100': {
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
            },
            'C170': {
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
            },
            'E100': {
                'cnpj': str,
                'periodo': 'datetime64[ns]',
                'REG': str,
                'DT_INI': 'datetime64[ns]',
                'DT_FIN': 'datetime64[ns]'
            },
            'E110': {
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
            }
        }

        sped_df = (
            df['linha_raw'].str.split('|', expand=True) # Convert to string and split by '|' and expand into multiple columns
            .iloc[:, 1:-1] # Remove first and last columns (which are empty due to the split)
            .rename(columns={ x: y for x, y in enumerate(dict(itertools.islice(columns[register].items(), 2, len(columns[register]))), start=1) }) # Removes the first two items from each register
        )

        # Insert 'cnpj' and 'periodo' columns from df into the sped_df
        sped_df.insert(0, 'cnpj', df['cnpj'])
        sped_df.insert(1, 'periodo', df['periodo'])

        # Resets the index of "sped_df", as it retained the index from the old df.
        sped_df = sped_df.reset_index(drop=True)

        # Validation rules
        valid_condition = sped_df[list(columns[register])].notna().all(axis=1) # Checks if there is any NaN in the row

        # Split into two separate DataFrames
        sped_df_valid = sped_df[valid_condition].copy()

        # Parse columns to datetime format
        if register == 'C100':
            sped_df_valid['DT_DOC'] = pd.to_datetime(sped_df_valid['DT_DOC'], format='%d%m%Y')
            sped_df_valid['DT_E_S'] = pd.to_datetime(sped_df_valid['DT_E_S'], format='%d%m%Y')
        if register == 'E100':
            sped_df_valid['DT_INI'] = pd.to_datetime(sped_df_valid['DT_INI'], format='%d%m%Y')
            sped_df_valid['DT_FIN'] = pd.to_datetime(sped_df_valid['DT_FIN'], format='%d%m%Y')

        # Define column types
        sped_df_valid = sped_df_valid.astype(columns[register])

        print(f'\n{file_name}.parquet\n')
        print(sped_df_valid)
        save_parquet_idempotent(sped_df_valid, f'{file_path}{file_name}.parquet')

        sped_df_invalid = sped_df[~valid_condition].copy()
        sped_df_invalid['motivo_erro'] = 'Linha contém valor nulo em uma das colunas obrigatórias'

        print(f'\n{file_name}_invalid.parquet\n')
        print(sped_df_invalid)
        save_parquet_idempotent(sped_df_invalid, f'{file_path}{file_name}_invalid.parquet')
