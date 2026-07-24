# !/usr/bin/env python3
# -*- coding: utf-8 -*-


from pathlib import Path
import pandas as pd


# Read all files in the raw data directory
raw_path = Path('../data/raw')
bronze_path = '../data/bronze'

for item in raw_path.rglob('*'):
    if item.is_file() and not any(part.startswith(".gitkeep") for part in item.parts):
        with open(item, 'r') as file:
            register_rows = []
            raw_rows = []
            cnpj_rows = []
            period_rows = []
            ingestion_ts_rows = []

            for line in file:
                line_split = line.split('|')

                if line_split[1] == '0000':
                    cnpj = line_split[7]
                    periodo = f'{line_split[4][4:]}-{line_split[4][2:4]}'

                if line_split[1] in ['0000', '0150', 'C100', 'C170', 'E100', 'E110']:
                    register_rows.append(line_split[1])
                    raw_rows.append(line)
                    cnpj_rows.append(cnpj)
                    period_rows.append(periodo)
                    ingestion_ts_rows.append(pd.Timestamp.now())

        # Generate Pandas DataFrame
        df = pd.DataFrame({
            'registro': register_rows,
            'linha_raw': raw_rows,
            'cnpj': cnpj_rows,
            'periodo': period_rows,
            'ingestao_ts': ingestion_ts_rows
        })

        # Create CNPJ directory if it doesn't exist
        dir_path = Path(f'{bronze_path}/{cnpj}')
        dir_path.mkdir(parents=True, exist_ok=True)

        # Convert Pandas DataFrame to Parquet format and save it to the bronze directory
        parquet_path = f'{bronze_path}/{cnpj}/{periodo}.parquet'
        print(parquet_path)
        df.to_parquet(parquet_path, engine='pyarrow', compression='snappy')
