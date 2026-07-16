"""
generate_sped.py
Gera arquivos SPED Fiscal (EFD ICMS-IPI) sintéticos para uso em desafios técnicos.

Uso:
    python generate_sped.py --output ./data/raw

Saída:
    Um arquivo .txt por empresa/mês no formato:
    {output}/{cnpj}/{YYYYMM}.txt

Características dos dados gerados:
    - 3 empresas fictícias, 3 meses cada (9 arquivos)
    - ~500 notas por mês por empresa, com 1-5 itens cada
    - Divergências de apuração intencionais em ~10% dos períodos
    - Linhas malformadas intencionais (~0.5% dos registros C170)
"""

import argparse
import os
import random
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Optional

# ── Seed para reprodutibilidade ───────────────────────────────
SEED = 40
random.seed(SEED)


# ── Empresas fictícias ────────────────────────────────────────
@dataclass
class Empresa:
    cnpj: str
    razao_social: str
    uf: str
    ie: str
    municipio: str
    cod_mun: str


EMPRESAS = [
    Empresa("12345678000195", "ALPHA COMERCIO DE PECAS LTDA",    "SP", "111111111111", "SAO PAULO",       "3550308"),
    Empresa("98765432000188", "BETA INDUSTRIA METALURGICA SA",   "MG", "222222222222", "BELO HORIZONTE",  "3106200"),
    Empresa("11223344000166", "GAMMA DISTRIBUIDORA EIRELI",      "RS", "333333333333", "PORTO ALEGRE",    "4314902"),
]

# Participantes (fornecedores/clientes compartilhados)
PARTICIPANTES = [
    ("55512312300010", "FORNECEDOR NACIONAL LTDA",       "SP", "444444444444"),
    ("77788899000177", "CLIENTE VAREJO SA",              "RJ", "555555555555"),
    ("33366699000100", "DISTRIBUIDORA CENTRO OESTE",     "GO", "666666666666"),
    ("22244466000133", "INDUSTRIA DO NORTE LTDA",        "PA", "777777777777"),
    ("99900011000155", "ATACADO SUL COMERCIO",           "SC", "888888888888"),
]

# CFOPs usados (entradas e saídas)
CFOPS_SAIDA  = ["5101", "5102", "5401", "5403", "6101", "6102"]
CFOPS_ENTRADA= ["1101", "1102", "1401", "1403", "2101", "2102"]

# CSTs de ICMS
CSTS = ["00", "10", "20", "30", "40", "41", "50", "51", "60", "70", "90"]

# Alíquotas ICMS por UF (simplificado)
ALIQUOTAS = {"SP": 0.12, "MG": 0.12, "RS": 0.12, "RJ": 0.12, "GO": 0.12, "PA": 0.12, "SC": 0.12}

# Produtos
PRODUTOS = [
    ("PROD001", "PECA MECANICA TIPO A",  50.0,  120.0),
    ("PROD002", "COMPONENTE ELETRICO B", 30.0,   85.0),
    ("PROD003", "MATERIAL BRUTO C",     200.0,  350.0),
    ("PROD004", "PRODUTO ACABADO D",    500.0,  980.0),
    ("PROD005", "INSUMO INDUSTRIAL E",   15.0,   42.0),
    ("PROD006", "EMBALAGEM PADRAO F",     5.0,   12.0),
    ("PROD007", "PARTE SOBRESSALENTE G", 80.0,  160.0),
    ("PROD008", "CONJUNTO MONTADO H",   700.0, 1400.0),
]


# ── Utilitários ───────────────────────────────────────────────
def fmt_valor(v: float) -> str:
    return f"{v:.2f}"

def fmt_data(d: date) -> str:
    return d.strftime("%d%m%Y")

def rand_date(year: int, month: int) -> date:
    import calendar
    last_day = calendar.monthrange(year, month)[1]
    return date(year, month, random.randint(1, last_day))

def rand_num_doc(seq: int) -> str:
    return str(seq).zfill(9)

def rand_participante() -> tuple:
    return random.choice(PARTICIPANTES)

def rand_cfop(saida: bool = True) -> str:
    return random.choice(CFOPS_SAIDA if saida else CFOPS_ENTRADA)

def rand_cst() -> str:
    # Peso maior para CSTs comuns
    return random.choices(CSTS, weights=[30,10,10,5,20,5,5,3,5,3,4])[0]


# ── Geração de registros ──────────────────────────────────────

def reg_0000(empresa: Empresa, ano: int, mes: int) -> str:
    dt_ini = date(ano, mes, 1).strftime("%d%m%Y")
    import calendar
    dt_fin = date(ano, mes, calendar.monthrange(ano, mes)[1]).strftime("%d%m%Y")
    return f"|0000|LEIAUTE 17|{dt_ini}|{dt_fin}|{empresa.cnpj}|{empresa.razao_social}|{empresa.uf}|{empresa.ie}||{empresa.municipio}|{empresa.cod_mun}|0|0|"

def reg_0001() -> str:
    return "|0001|0|"

def reg_0005(empresa: Empresa) -> str:
    return f"|0005|{empresa.razao_social}|XX.XXX.XXX/XXXX-XX|{empresa.cnpj}|contato@empresa.com.br|(11) 0000-0000|"

def reg_0150(participantes: list) -> list[str]:
    linhas = []
    for cnpj, nome, uf, ie in participantes:
        linhas.append(f"|0150|{cnpj}|{nome}|{uf}|{ie}||||{cnpj}||")
    return linhas

def reg_0990(total: int) -> str:
    return f"|0990|{total}|"

def reg_c001() -> str:
    return "|C001|0|"

def gerar_nota(
    seq: int,
    empresa: Empresa,
    ano: int,
    mes: int,
    aliq: float,
    introduzir_erro: bool = False
) -> tuple[str, list[str], float]:
    """Retorna (linha_c100, linhas_c170, total_icms_itens)."""

    part_cnpj, part_nome, part_uf, part_ie = rand_participante()
    num_doc = rand_num_doc(seq)
    dt_emi  = rand_date(ano, mes)
    dt_sai  = dt_emi + timedelta(days=random.randint(0, 3))
    cfop    = rand_cfop(saida=True)

    n_itens = random.randint(1, 5)
    itens   = random.choices(PRODUTOS, k=n_itens)

    vl_total = 0.0
    vl_bc_icms_total = 0.0
    vl_icms_total = 0.0

    linhas_c170 = []
    for i, (cod, desc, custo, preco) in enumerate(itens, start=1):
        qtd   = round(random.uniform(1, 50), 3)
        vl_un = round(random.uniform(custo, preco), 2)
        vl_item = round(qtd * vl_un, 2)
        cst   = rand_cst()

        # Só calcula ICMS para CSTs tributados
        if cst in ("00", "10", "20", "51", "90"):
            bc_icms = round(vl_item * random.uniform(0.85, 1.0), 2)
            vl_icms = round(bc_icms * aliq, 2)
        else:
            bc_icms = 0.0
            vl_icms = 0.0

        vl_total     += vl_item
        vl_bc_icms_total += bc_icms
        vl_icms_total    += vl_icms

        linha_c170 = (
            f"|C170|{i}|{cod}|{desc}|{fmt_valor(qtd)}|UN|"
            f"{fmt_valor(vl_item)}|{cfop}|{cst}|"
            f"{fmt_valor(bc_icms)}|{fmt_valor(aliq * 100)}|{fmt_valor(vl_icms)}|"
            f"0.00|0.00|0.00|0.00|0.00|0.00|"
        )

        # Introduz linha malformada (faltam campos)
        if introduzir_erro and i == 1:
            linha_c170 = f"|C170|{i}|{cod}|LINHA_CORROMPIDA|"

        linhas_c170.append(linha_c170)

    vl_total = round(vl_total, 2)

    c100 = (
        f"|C100|1|0|{empresa.cnpj}|55|00|{num_doc}|{num_doc[:3]}|"
        f"{fmt_data(dt_emi)}|{fmt_data(dt_sai)}|{fmt_valor(vl_total)}|"
        f"{fmt_valor(vl_bc_icms_total)}|{fmt_valor(vl_icms_total)}|"
        f"0.00|0.00|0.00|0.00|0.00|0.00|0.00|0|{part_cnpj}|"
    )

    return c100, linhas_c170, vl_icms_total

def reg_c990(total: int) -> str:
    return f"|C990|{total}|"

def reg_e001() -> str:
    return "|E001|0|"

def reg_e100(ano: int, mes: int) -> str:
    import calendar
    dt_ini = date(ano, mes, 1).strftime("%d%m%Y")
    dt_fin = date(ano, mes, calendar.monthrange(ano, mes)[1]).strftime("%d%m%Y")
    return f"|E100|{dt_ini}|{dt_fin}|"

def reg_e110(
    vl_tot_debitos: float,
    vl_tot_creditos: float,
    saldo_anterior: float = 0.0,
    introduzir_divergencia: bool = False,
) -> str:
    """
    Gera registro E110 de apuração.
    Se introduzir_divergencia=True, o valor declarado difere do calculado bottom-up.
    """
    vl_apurado = round(max(vl_tot_debitos - vl_tot_creditos - saldo_anterior, 0), 2)
    vl_saldo_credor = round(max(vl_tot_creditos + saldo_anterior - vl_tot_debitos, 0), 2)

    if introduzir_divergencia:
        # Subtrai ou soma um valor aleatório ao apurado (simula erro de apuração)
        delta = round(random.uniform(50, 500), 2)
        if random.random() > 0.5:
            vl_apurado = round(vl_apurado + delta, 2)
        else:
            vl_apurado = round(max(vl_apurado - delta, 0), 2)

    return (
        f"|E110|{fmt_valor(vl_tot_debitos)}|0.00|0.00|{fmt_valor(vl_tot_debitos)}|"
        f"{fmt_valor(saldo_anterior)}|0.00|0.00|0.00|0.00|0.00|"
        f"{fmt_valor(vl_tot_creditos)}|{fmt_valor(vl_tot_creditos)}|"
        f"0.00|0.00|0.00|{fmt_valor(vl_saldo_credor)}|"
        f"0.00|0.00|0.00|0.00|{fmt_valor(vl_apurado)}|"
    )

def reg_e990(total: int) -> str:
    return f"|E990|{total}|"

def reg_9001() -> str:
    return "|9001|0|"

def reg_9900(registros: dict[str, int]) -> list[str]:
    return [f"|9900|{reg}|{qtd}|" for reg, qtd in sorted(registros.items())]

def reg_9990(total: int) -> str:
    return f"|9990|{total}|"

def reg_9999(total: int) -> str:
    return f"|9999|{total}|"


# ── Montagem do arquivo ───────────────────────────────────────

def gerar_sped(empresa: Empresa, ano: int, mes: int, n_notas: int = 500) -> list[str]:
    """Monta todas as linhas de um arquivo SPED para uma empresa/período."""

    aliq = ALIQUOTAS.get(empresa.uf, 0.12)

    # Decide aleatoriamente se este período terá divergência ou linhas com erro
    introduzir_divergencia = random.random() < 0.10
    # ~0.5% das notas terão item com linha malformada
    notas_com_erro = set(random.sample(range(1, n_notas + 1), max(1, int(n_notas * 0.005))))

    linhas: list[str] = []
    contagem: dict[str, int] = {}

    def add(linha: str):
        linhas.append(linha)
        reg = linha.split("|")[1]
        contagem[reg] = contagem.get(reg, 0) + 1

    # ── Bloco 0 ──
    add(reg_0000(empresa, ano, mes))
    add(reg_0001())
    add(reg_0005(empresa))
    for l in reg_0150(PARTICIPANTES):
        add(l)

    total_bloco_0 = len(linhas) + 1  # +1 pelo 0990
    add(reg_0990(total_bloco_0))

    # ── Bloco C ──
    inicio_c = len(linhas)
    add(reg_c001())

    total_icms_debito = 0.0

    for seq in range(1, n_notas + 1):
        tem_erro = seq in notas_com_erro
        c100, c170s, vl_icms = gerar_nota(seq, empresa, ano, mes, aliq, introduzir_erro=tem_erro)
        add(c100)
        for c170 in c170s:
            add(c170)
        total_icms_debito += vl_icms

    total_bloco_c = len(linhas) - inicio_c + 1
    add(reg_c990(total_bloco_c))

    # ── Bloco E ──
    inicio_e = len(linhas)
    add(reg_e001())
    add(reg_e100(ano, mes))

    # Créditos: simula ~30% do débito como crédito de entradas
    vl_creditos = round(total_icms_debito * random.uniform(0.20, 0.40), 2)
    saldo_ant   = round(random.uniform(0, 200), 2)

    add(reg_e110(
        vl_tot_debitos=round(total_icms_debito, 2),
        vl_tot_creditos=vl_creditos,
        saldo_anterior=saldo_ant,
        introduzir_divergencia=introduzir_divergencia,
    ))

    total_bloco_e = len(linhas) - inicio_e + 1
    add(reg_e990(total_bloco_e))

    # ── Bloco 9 ──
    inicio_9 = len(linhas)
    add(reg_9001())
    for l in reg_9900(contagem):
        add(l)
    total_bloco_9 = len(linhas) - inicio_9 + 2  # +9990 +9999
    add(reg_9990(total_bloco_9))

    total_arquivo = len(linhas) + 1  # +9999
    add(reg_9999(total_arquivo))

    return linhas


# ── CLI ───────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Gera arquivos SPED Fiscal sintéticos para desafios técnicos."
    )
    parser.add_argument(
        "--output", "-o",
        default="./data/raw",
        help="Diretório de saída (default: ./data/raw)"
    )
    parser.add_argument(
        "--notas", "-n",
        type=int,
        default=500,
        help="Número de notas por arquivo (default: 500)"
    )
    parser.add_argument(
        "--meses", "-m",
        type=int,
        default=3,
        help="Quantos meses gerar, retroativos a partir de 2024-03 (default: 3)"
    )
    args = parser.parse_args()

    # Períodos: jan/2024 a mar/2024 (ou conforme --meses)
    periodos = []
    ano, mes = 2024, 1
    for _ in range(args.meses):
        periodos.append((ano, mes))
        mes += 1
        if mes > 12:
            mes = 1
            ano += 1

    total_arquivos = 0
    total_linhas   = 0

    for empresa in EMPRESAS:
        for ano, mes in periodos:
            linhas = gerar_sped(empresa, ano, mes, n_notas=args.notas)

            # Caminho: {output}/{cnpj}/{YYYYMM}.txt
            pasta = os.path.join(args.output, empresa.cnpj)
            os.makedirs(pasta, exist_ok=True)
            nome_arquivo = f"{ano}{str(mes).zfill(2)}.txt"
            caminho = os.path.join(pasta, nome_arquivo)

            with open(caminho, "w", encoding="utf-8") as f:
                f.write("\n".join(linhas) + "\n")

            total_arquivos += 1
            total_linhas   += len(linhas)
            print(f"  [OK] {empresa.cnpj} / {ano}-{str(mes).zfill(2)} → {caminho}  ({len(linhas):,} linhas)")

    print(f"\n{total_arquivos} arquivos gerados | {total_linhas:,} linhas no total")
    print(f"Diretório de saída: {os.path.abspath(args.output)}")


if __name__ == "__main__":
    main()
