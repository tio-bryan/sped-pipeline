# Schemas

## bronze.py
- registro: string — código do registro (ex: 'C100')
- linha_raw: string — conteúdo completo da linha original
- cnpj: string — extraído do registro 0000
- periodo: string — YYYY-MM, extraído do registro 0000
- ingestao_ts: timestamp — momento da leitura

## silver.py
- C100:
    - cnpj: string — gerado no `bronze.py`
    - periodo: string — gerado no `bronze.py`
    - REG: string — 
    - IND_OPER: string — 
    - IND_EMIT: string — 
    - cnpj_estabelecimento: string — 
    - COD_MOD: string — 
    - COD_SIT: string — 
    - num_doc: string — 
    - 8: string — 
    - dt_emi: string — 
    - dt_sai: string — 
    - valor_total: string — 
    - vl_bc_icms_total: string — 
    - vl_icms_total: string — 
    - 14: string — 
    - 15: string — 
    - 16: string — 
    - 17: string — 
    - 18: string — 
    - 19: string — 
    - 20: string — 
    - 21: string — 
    - part_cnpj: string — 
- 