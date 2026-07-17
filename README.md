# Pipeline Fiscal com Arquitetura Medalhão

## Visão Geral

### O que é?
Pipeline para ingestão de arquivos SPED feito com Arquitetura Medalhão.

Arquitetura Medalhão consiste em 3 camadas: Bronze, silver, gold.

- Bronze: Reter os dados exatamente como eles vêm da fonte;
- Silver: Refinar os dados da bronze, fazendo o _parsing_, normalização, e validação de campos irregulares;
- Gold: Visões prontos para o negócio, focado em áreas específicas como estratégia, vendas, marketing, RH, etc.

Sobre as escolhas das bibliotecas para este projeto, optei pelo mais básico, simples e direto possível, utilizando o Pandas para montar os data frames e gerar os arquivos Parquets (com a engine PyArrow) e o DuckDB para realizar as queries no Ouro.

### O que cada código faz?
Todos os códigos relevantes deste projeto estão situados diretório `/pipeline`. Cada código de cada camada irá salvar seus Parquets nos seus respectivos diretórios situados no `/data`.
- O código `generate_sped.py` gera arquivos SPED Fiscal (EFD ICMS-IPI) sintéticos e salva no diretório `/data/raw`.
- O `bronze.py` lê os dados gerados pelo script `generate_sped.py` e salva os dados brutos em Parquets.
- O `silver.py` lê os Parquets gerados pelo `bronze.py` e realiza o parsing e a normalização dos dados apenas dos registros C100, C170, E100 e E110. É gerado um Parquet para cada tipo de registro. Caso a linha contenha informações inválidas, esse script separa esses dados para um outro arquivo com o mesmo nome com o sufixo `_invalid`.
- O `gold.py` irá ler os Parquets gerados pelo `silver.py` com o DuckDB para realizar as seguintes queries e em seguida salvar elas em Parquet:
    - `icms_apuracao_mensal`: ICMS apurado por estabelecimento e período, consolidando
débitos, créditos e saldo;
    - `icms_por_cfop`: Total de ICMS destacado nos itens (C170) agrupado por CNPJ,
período e CFOP;
    - `divergencias_apuracao`: Diferença entre ICMS calculado bottom-up (soma de C170)
e o declarado no E110, por estabelecimento e período.

Schemas dos arquivos gerados por cada etapa: [Schemas](docs/schemas.md)

## Pré-requisitos
- Python 3.14.6+
- Obs: Testado no sistema operacional Fedora 44

## Como Instalar e Usar
- Abrir terminal
- Clonar repositório:
```
git clone https://github.com/tio-bryan/sped-pipeline.git
```
- Entrar no diretório do projeto:
```
cd sped-pipeline
```
- Criar ambiente virtual:
```
python -m venv venv
```
- Ativar ambiente virtual:
```
source venv/bin/activate
```
- Instalar dependências:
```
pip install -r requirements.txt
```
- Gerar dados fictícios:
```
python generate_sped.py
```
- Entrar no diretório pipeline:
```
cd pipeline
```
- Executar os scripts na seguinte sequência (caso contrário irá quebrar):
```
python bronze.py
python silver.py
python gold.py
```
- Ou para executar tudo de uma vez:
```
python run_all.py
```

Instruções para [Windows](docs/how_to_use_windows.md)

## To be Done
- Verificar os campos no Silver:
    - Confirmar e resolver todos os campos comentados;
    - Validar o `vl_apurado` do E110. Nesse campo há chance do valor declarado ser diferente do calculado bottom-up.
- Suporte a reprocessamento parcial por período ou empresa.