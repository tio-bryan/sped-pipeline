# !/usr/bin/env python3
# -*- coding: utf-8 -*-


import duckdb


duckdb.sql("SELECT * FROM '../data/silver/sped_c170.parquet'").show()