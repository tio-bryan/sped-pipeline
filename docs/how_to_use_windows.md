# Como usar (Windows)

- Abrir terminal
- Clonar repositório:
```
git clone https://github.com/tio-bryan/sped-pipeline.git
```
- Entrar no diretório do projeto:
```
dir sped-pipeline
```
- Criar ambiente virtual:
```
python -m venv venv
```
- Ativar ambiente virtual:
    - Prompt de Comando:
    ```
    venv\Scripts\activate.bat
    ```
    - PowerShell:
    ```
    .\venv\Scripts\Activate.ps1
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
dir pipeline
```
- Executar os scripts na seguinte sequência:
```
python bronze.py
python silver.py
python gold.py
```
- Ou para executar tudo de uma vez:
```
python run_all.py
```