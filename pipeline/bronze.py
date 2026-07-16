# !/usr/bin/env python3
# -*- coding: utf-8 -*-


from pathlib import Path
import pandas as pd


# Read all files in the raw data directory
raw_path_str = '../data/raw'
raw_path = Path(raw_path_str)

for item in raw_path.rglob('*'):
    if item.is_file():
        with open(item, 'r') as file:
            registro_rows = []
            linha_raw_rows = []
            cnpj_rows = []
            periodo_rows = []
            ingestao_ts_rows = []

            for line in file:
                line_split = line.split('|')

                if line_split[1] == '0000':
                    cnpj = line_split[5]
                    periodo = f'{line_split[3][4:]}-{line_split[3][2:4]}'

                if line_split[1] in ['0000', '0150', 'C100', 'C170', 'E100', 'E110']:
                    registro_rows.append(line_split[1])
                    linha_raw_rows.append(line)
                    cnpj_rows.append(cnpj)
                    periodo_rows.append(periodo)
                    ingestao_ts_rows.append(pd.Timestamp.now())

        # Generate Pandas DataFrame
        df = pd.DataFrame({
            'registro': registro_rows,
            'linha_raw': linha_raw_rows,
            'cnpj': cnpj_rows,
            'periodo': periodo_rows,
            'ingestao_ts': ingestao_ts_rows
        })

        # Create CNPJ directory if it doesn't exist
        dir_path = Path(f'../data/bronze/{cnpj}')
        dir_path.mkdir(parents=True, exist_ok=True)

        # Convert Pandas DataFrame to Parquet format and save it to the bronze directory
        print(f'../data/bronze/{cnpj}/{periodo}.parquet')
        df.to_parquet(f'../data/bronze/{cnpj}/{periodo}.parquet', engine='pyarrow', compression='snappy')
