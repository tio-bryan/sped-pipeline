# !/usr/bin/env python3
# -*- coding: utf-8 -*-


import duckdb


# duckdb.sql("SELECT * FROM '../data/silver/sped_c170.parquet'").show()
# duckdb.sql("SELECT COUNT(*) FROM '../data/silver/sped_c170.parquet'").show()

# icms_por_cfop
duckdb.sql("SELECT cnpj, periodo, CFOP, SUM(vl_icms) FROM '../data/silver/sped_c170.parquet' GROUP BY cnpj, periodo, CFOP").show()

# divergencias_apuracao
# duckdb.sql("SELECT cnpj, periodo, SUM(vl_icms) FROM '../data/silver/sped_c170.parquet' GROUP BY cnpj, periodo").show()
# duckdb.sql("SELECT cnpj, periodo, SUM(vl_apurado) FROM '../data/silver/sped_e110.parquet' GROUP BY cnpj, periodo").show()

duckdb.sql(
    """
    COPY (
        SELECT
            a.cnpj,
            a.periodo,
            a.sum_vl_icms,
            b.sum_vl_apurado,
            (a.sum_vl_icms - b.sum_vl_apurado) as diferenca
        FROM (
            SELECT
                cnpj,
                periodo,
                SUM(vl_icms) as sum_vl_icms
            FROM '../data/silver/sped_c170.parquet'
            GROUP BY cnpj, periodo
        ) as A JOIN (
            SELECT
                cnpj,
                periodo,
                SUM(vl_apurado) as sum_vl_apurado
            FROM '../data/silver/sped_e110.parquet'
            GROUP BY cnpj, periodo
        ) as B ON A.cnpj = B.cnpj AND A.periodo = B.periodo
    )
    TO '../data/gold/divergencias_apuracao.parquet'
    (FORMAT PARQUET);
    """
)

