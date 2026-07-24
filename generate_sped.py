"""
generate_sped.py
Gera arquivos SPED Fiscal (EFD ICMS-IPI) sintéticos para uso em desafios técnicos.

Uso:
    python generate_sped.py --output ./data/raw

Saída:
    Um arquivo .txt por empresa/mês no formato:
    {output}/{cnpj}/{YYYYMM}.txt

Layout:
    Os registros seguem o leiaute da EFD ICMS/IPI (Guia Prático), incluindo os
    registros obrigatórios 0190/0200 (unidade e item), C190 (analítico do
    documento) e a contagem correta do Bloco 9 (9900 conta os próprios
    registros 9001/9900/9990/9999).

Características dos dados gerados (intencionais, para o desafio):
    - 3 empresas fictícias, 3 meses cada (9 arquivos)
    - ~500 notas por mês por empresa, com 1-5 itens cada
    - Divergências de apuração intencionais em ~10% dos períodos (E110)
    - Linhas C170 malformadas intencionais (~0.5% das notas)
"""

import argparse
import calendar
import os
import random
from dataclasses import dataclass
from datetime import date, timedelta

# ── Seed para reprodutibilidade ───────────────────────────────
SEED = 42
random.seed(SEED)

# Código do país (Brasil) na tabela do SPED
COD_PAIS_BR = "01058"

# Códigos de UF (IBGE) — usados na composição da chave da NF-e
COD_UF = {
    "SP": "35", "MG": "31", "RS": "43", "RJ": "33",
    "GO": "52", "PA": "15", "SC": "42",
}


# ── Empresas fictícias ────────────────────────────────────────
@dataclass
class Empresa:
    cnpj: str
    razao_social: str
    fantasia: str
    uf: str
    ie: str
    cod_mun: str          # código IBGE do município (7 dígitos)
    cep: str
    endereco: str
    numero: str
    bairro: str
    fone: str
    ind_ativ: str         # 0 = industrial/equiparado, 1 = outros


EMPRESAS = [
    Empresa("12345678000195", "ALPHA COMERCIO DE PECAS LTDA", "ALPHA PECAS",
            "SP", "111111111111", "3550308", "01310100", "AV PAULISTA", "1000", "BELA VISTA", "1130000000", "1"),
    Empresa("98765432000188", "BETA INDUSTRIA METALURGICA SA", "BETA METAL",
            "MG", "222222222222", "3106200", "30140071", "AV AFONSO PENA", "2500", "CENTRO", "3130000000", "0"),
    Empresa("11223344000166", "GAMMA DISTRIBUIDORA EIRELI", "GAMMA DIST",
            "RS", "333333333333", "4314902", "90010150", "RUA DOS ANDRADAS", "500", "CENTRO HISTORICO", "5130000000", "1"),
]

# Participantes (fornecedores/clientes compartilhados)
# (cnpj, nome, uf, ie, cod_mun)
PARTICIPANTES = [
    ("55512312300010", "FORNECEDOR NACIONAL LTDA",    "SP", "444444444444", "3550308"),
    ("77788899000177", "CLIENTE VAREJO SA",           "RJ", "555555555555", "3304557"),
    ("33366699000100", "DISTRIBUIDORA CENTRO OESTE",   "GO", "666666666666", "5208707"),
    ("22244466000133", "INDUSTRIA DO NORTE LTDA",      "PA", "777777777777", "1501402"),
    ("99900011000155", "ATACADO SUL COMERCIO",         "SC", "888888888888", "4205407"),
]

# CFOPs usados (entradas e saídas)
CFOPS_SAIDA   = ["5101", "5102", "5401", "5403", "6101", "6102"]
CFOPS_ENTRADA = ["1101", "1102", "1401", "1403", "2101", "2102"]

# CSTs de ICMS (2 dígitos; a origem é prefixada em runtime → 3 dígitos)
CSTS = ["00", "10", "20", "30", "40", "41", "50", "51", "60", "70", "90"]
# CSTs que geram base/valor de ICMS próprio
CSTS_TRIBUTADOS = {"00", "10", "20", "51", "70", "90"}

# Origens da mercadoria (0 = nacional é a mais comum)
ORIGENS = ["0", "1", "2", "3", "4", "5", "6", "7", "8"]

# Alíquotas ICMS por UF (simplificado)
ALIQUOTAS = {"SP": 0.18, "MG": 0.18, "RS": 0.17, "RJ": 0.20, "GO": 0.17, "PA": 0.19, "SC": 0.17}

# Produtos: (cod, descricao, custo, preco, ncm)
PRODUTOS = [
    ("PROD001", "PECA MECANICA TIPO A",   50.0,  120.0, "84829900"),
    ("PROD002", "COMPONENTE ELETRICO B",  30.0,   85.0, "85369090"),
    ("PROD003", "MATERIAL BRUTO C",      200.0,  350.0, "72161000"),
    ("PROD004", "PRODUTO ACABADO D",     500.0,  980.0, "84314900"),
    ("PROD005", "INSUMO INDUSTRIAL E",    15.0,   42.0, "38249999"),
    ("PROD006", "EMBALAGEM PADRAO F",      5.0,   12.0, "48191000"),
    ("PROD007", "PARTE SOBRESSALENTE G",  80.0,  160.0, "84841000"),
    ("PROD008", "CONJUNTO MONTADO H",    700.0, 1400.0, "84799090"),
]

# Unidade de medida única usada nos itens
UNIDADE = "UN"


# ── Utilitários ───────────────────────────────────────────────
def fmt_valor(v: float) -> str:
    """Formata valor no padrão SPED: ponto decimal, 2 casas, sem separador de milhar."""
    return f"{v:.2f}"

def fmt_data(d: date) -> str:
    return d.strftime("%d%m%Y")

def rand_date(year: int, month: int) -> date:
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
    return random.choices(CSTS, weights=[30, 10, 10, 5, 20, 5, 5, 3, 5, 3, 4])[0]

def rand_origem() -> str:
    # Origem nacional (0) predominante
    return random.choices(ORIGENS, weights=[60, 8, 8, 4, 4, 4, 4, 4, 4])[0]

def dv_mod11(chave43: str) -> str:
    """Dígito verificador (módulo 11) da chave de acesso da NF-e."""
    pesos = [2, 3, 4, 5, 6, 7, 8, 9]
    soma = 0
    for i, dig in enumerate(reversed(chave43)):
        soma += int(dig) * pesos[i % 8]
    resto = soma % 11
    dv = 11 - resto
    return "0" if dv in (0, 1, 10, 11) else str(dv)

def gerar_chave_nfe(empresa: Empresa, ano: int, mes: int, serie: str, num_doc: str) -> str:
    """Compõe uma chave de acesso de NF-e (44 dígitos) plausível."""
    cuf   = COD_UF.get(empresa.uf, "35")
    aamm  = f"{ano % 100:02d}{mes:02d}"
    mod   = "55"
    ser   = serie.zfill(3)
    nnf   = num_doc.zfill(9)
    tpemis = "1"
    cnf   = "".join(random.choices("0123456789", k=8))
    chave43 = cuf + aamm + empresa.cnpj + mod + ser + nnf + tpemis + cnf
    return chave43 + dv_mod11(chave43)


# ── Bloco 0 ───────────────────────────────────────────────────

def reg_0000(empresa: Empresa, ano: int, mes: int) -> str:
    dt_ini = date(ano, mes, 1).strftime("%d%m%Y")
    dt_fin = date(ano, mes, calendar.monthrange(ano, mes)[1]).strftime("%d%m%Y")
    # |0000|COD_VER|COD_FIN|DT_INI|DT_FIN|NOME|CNPJ|CPF|UF|IE|COD_MUN|IM|SUFRAMA|IND_PERFIL|IND_ATIV|
    return (
        f"|0000|017|0|{dt_ini}|{dt_fin}|{empresa.razao_social}|{empresa.cnpj}||"
        f"{empresa.uf}|{empresa.ie}|{empresa.cod_mun}|||A|{empresa.ind_ativ}|"
    )

def reg_0001() -> str:
    # |0001|IND_MOV|  (0 = bloco com dados)
    return "|0001|0|"

def reg_0005(empresa: Empresa) -> str:
    # |0005|FANTASIA|CEP|END|NUM|COMPL|BAIRRO|FONE|FAX|EMAIL|
    return (
        f"|0005|{empresa.fantasia}|{empresa.cep}|{empresa.endereco}|{empresa.numero}||"
        f"{empresa.bairro}|{empresa.fone}||contato@empresa.com.br|"
    )

def reg_0150(participantes: list) -> list:
    # |0150|COD_PART|NOME|COD_PAIS|CNPJ|CPF|IE|COD_MUN|SUFRAMA|END|NUM|COMPL|BAIRRO|
    linhas = []
    for cnpj, nome, _uf, ie, cod_mun in participantes:
        linhas.append(
            f"|0150|{cnpj}|{nome}|{COD_PAIS_BR}|{cnpj}||{ie}|{cod_mun}||ENDERECO PARTICIPANTE|0||CENTRO|"
        )
    return linhas

def reg_0190() -> list:
    # |0190|UNID|DESCR|
    return [f"|0190|{UNIDADE}|UNIDADE|"]

def reg_0200(produtos: list) -> list:
    # |0200|COD_ITEM|DESCR_ITEM|COD_BARRA|COD_ANT_ITEM|UNID_INV|TIPO_ITEM|COD_NCM|EX_IPI|COD_GEN|COD_LST|ALIQ_ICMS|CEST|
    linhas = []
    for cod, desc, _custo, _preco, ncm in produtos:
        linhas.append(f"|0200|{cod}|{desc}|||{UNIDADE}|00|{ncm}||||||")
    return linhas

def reg_0990(qtd_lin: int) -> str:
    return f"|0990|{qtd_lin}|"


# ── Bloco C ───────────────────────────────────────────────────

def reg_c001() -> str:
    return "|C001|0|"

def gerar_nota(
    seq: int,
    empresa: Empresa,
    ano: int,
    mes: int,
    aliq: float,
    introduzir_erro: bool = False,
) -> tuple:
    """
    Gera uma NF-e de saída (emissão própria).
    Retorna (linha_c100, linhas_c170, linhas_c190, vl_icms_total).
    """
    part_cnpj, part_nome, part_uf, part_ie, part_mun = rand_participante()
    num_doc = rand_num_doc(seq)
    serie   = "1"
    dt_emi  = rand_date(ano, mes)
    dt_sai  = dt_emi + timedelta(days=random.randint(0, 3))
    cfop    = rand_cfop(saida=True)
    chave   = gerar_chave_nfe(empresa, ano, mes, serie, num_doc)
    ind_pgto = random.choice(["0", "1"])
    aliq_pct = round(aliq * 100, 2)

    n_itens = random.randint(1, 5)
    itens   = random.choices(PRODUTOS, k=n_itens)

    vl_merc_total    = 0.0
    vl_bc_icms_total = 0.0
    vl_icms_total    = 0.0

    linhas_c170 = []
    # Agrupamento para o C190: chave = (cst_icms_3, cfop, aliq)
    grupos: dict = {}

    for i, (cod, desc, custo, preco, _ncm) in enumerate(itens, start=1):
        qtd     = round(random.uniform(1, 50), 3)
        vl_un   = round(random.uniform(custo, preco), 2)
        vl_item = round(qtd * vl_un, 2)
        cst2    = rand_cst()
        origem  = rand_origem()
        cst3    = origem + cst2

        if cst2 in CSTS_TRIBUTADOS:
            bc_icms = round(vl_item * random.uniform(0.85, 1.0), 2)
            vl_icms = round(bc_icms * aliq, 2)
        else:
            bc_icms = 0.0
            vl_icms = 0.0

        vl_merc_total    += vl_item
        vl_bc_icms_total += bc_icms
        vl_icms_total    += vl_icms

        # Registro C170 — 38 campos (incl. REG). Construído a partir de uma
        # lista explícita para garantir a ordem e a quantidade exatas.
        campos_c170 = [
            "C170",
            str(i),                 # NUM_ITEM
            cod,                    # COD_ITEM
            "",                     # DESCR_COMPL
            fmt_valor(qtd),         # QTD
            UNIDADE,                # UNID
            fmt_valor(vl_item),     # VL_ITEM
            "0.00",                 # VL_DESC
            "0",                    # IND_MOV
            cst3,                   # CST_ICMS (origem + CST)
            cfop,                   # CFOP
            "",                     # COD_NAT
            fmt_valor(bc_icms),     # VL_BC_ICMS
            fmt_valor(aliq_pct),    # ALIQ_ICMS
            fmt_valor(vl_icms),     # VL_ICMS
            "0.00",                 # VL_BC_ICMS_ST
            "0.00",                 # ALIQ_ST
            "0.00",                 # VL_ICMS_ST
            "0",                    # IND_APUR
            "",                     # CST_IPI
            "",                     # COD_ENQ
            "0.00",                 # VL_BC_IPI
            "0.00",                 # ALIQ_IPI
            "0.00",                 # VL_IPI
            "",                     # CST_PIS
            "0.00",                 # VL_BC_PIS
            "0.00",                 # ALIQ_PIS (%)
            "0.000",                # QUANT_BC_PIS
            "0.0000",               # ALIQ_PIS (R$)
            "0.00",                 # VL_PIS
            "",                     # CST_COFINS
            "0.00",                 # VL_BC_COFINS
            "0.00",                 # ALIQ_COFINS (%)
            "0.000",                # QUANT_BC_COFINS
            "0.0000",               # ALIQ_COFINS (R$)
            "0.00",                 # VL_COFINS
            "",                     # COD_CTA
            "0.00",                 # VL_ABAT_NT
        ]
        linha_c170 = "|" + "|".join(campos_c170) + "|"

        # Introduz linha malformada intencional (faltam campos) — característica do desafio
        if introduzir_erro and i == 1:
            linha_c170 = f"|C170|{i}|{cod}|LINHA_CORROMPIDA|"

        linhas_c170.append(linha_c170)

        # Acumula no grupo do C190 (usa sempre os valores corretos, mesmo se a
        # linha C170 acima estiver corrompida de propósito)
        chave_grupo = (cst3, cfop, aliq_pct)
        g = grupos.setdefault(chave_grupo, {"vl_opr": 0.0, "vl_bc": 0.0, "vl_icms": 0.0})
        g["vl_opr"]  += vl_item
        g["vl_bc"]   += bc_icms
        g["vl_icms"] += vl_icms

    vl_merc_total = round(vl_merc_total, 2)
    vl_doc        = vl_merc_total
    vl_bc_icms_total = round(vl_bc_icms_total, 2)
    vl_icms_total    = round(vl_icms_total, 2)

    # |C100|IND_OPER|IND_EMIT|COD_PART|COD_MOD|COD_SIT|SER|NUM_DOC|CHV_NFE|DT_DOC|DT_E_S|VL_DOC|IND_PGTO|
    #       VL_DESC|VL_ABAT_NT|VL_MERC|IND_FRT|VL_FRT|VL_SEG|VL_OUT_DA|VL_BC_ICMS|VL_ICMS|
    #       VL_BC_ICMS_ST|VL_ICMS_ST|VL_IPI|VL_PIS|VL_COFINS|VL_PIS_ST|VL_COFINS_ST|
    c100 = (
        f"|C100|1|0|{part_cnpj}|55|00|{serie}|{num_doc}|{chave}|"
        f"{fmt_data(dt_emi)}|{fmt_data(dt_sai)}|{fmt_valor(vl_doc)}|{ind_pgto}|"
        f"0.00|0.00|{fmt_valor(vl_merc_total)}|9|0.00|0.00|0.00|"
        f"{fmt_valor(vl_bc_icms_total)}|{fmt_valor(vl_icms_total)}|"
        f"0.00|0.00|0.00|0.00|0.00|0.00|0.00|"
    )

    # C190 — registro analítico (um por combinação CST/CFOP/alíquota)
    linhas_c190 = []
    for (cst3, cfop_g, aliq_g), g in sorted(grupos.items()):
        # |C190|CST_ICMS|CFOP|ALIQ_ICMS|VL_OPR|VL_BC_ICMS|VL_ICMS|VL_BC_ICMS_ST|VL_ICMS_ST|VL_RED_BC|VL_IPI|COD_OBS|
        linhas_c190.append(
            f"|C190|{cst3}|{cfop_g}|{fmt_valor(aliq_g)}|"
            f"{fmt_valor(round(g['vl_opr'], 2))}|{fmt_valor(round(g['vl_bc'], 2))}|"
            f"{fmt_valor(round(g['vl_icms'], 2))}|0.00|0.00|0.00|0.00||"
        )

    return c100, linhas_c170, linhas_c190, vl_icms_total

def reg_c990(qtd_lin: int) -> str:
    return f"|C990|{qtd_lin}|"


# ── Bloco E ───────────────────────────────────────────────────

def reg_e001() -> str:
    return "|E001|0|"

def reg_e100(ano: int, mes: int) -> str:
    dt_ini = date(ano, mes, 1).strftime("%d%m%Y")
    dt_fin = date(ano, mes, calendar.monthrange(ano, mes)[1]).strftime("%d%m%Y")
    return f"|E100|{dt_ini}|{dt_fin}|"

def reg_e110(
    vl_tot_debitos: float,
    vl_tot_creditos: float,
    saldo_credor_ant: float = 0.0,
    introduzir_divergencia: bool = False,
) -> str:
    """
    Registro E110 — Apuração do ICMS (15 campos).
    Se introduzir_divergencia=True, o saldo apurado / ICMS a recolher é
    perturbado para simular erro de apuração (característica do desafio).
    """
    vl_sld_apurado  = round(max(vl_tot_debitos - vl_tot_creditos - saldo_credor_ant, 0), 2)
    vl_sld_credor_transp = round(max(vl_tot_creditos + saldo_credor_ant - vl_tot_debitos, 0), 2)
    vl_icms_recolher = vl_sld_apurado  # sem deduções

    if introduzir_divergencia:
        delta = round(random.uniform(50, 500), 2)
        if random.random() > 0.5:
            vl_sld_apurado = round(vl_sld_apurado + delta, 2)
        else:
            vl_sld_apurado = round(max(vl_sld_apurado - delta, 0), 2)
        vl_icms_recolher = vl_sld_apurado

    # |E110|VL_TOT_DEBITOS|VL_AJ_DEBITOS|VL_TOT_AJ_DEBITOS|VL_ESTORNOS_CRED|VL_TOT_CREDITOS|
    #       VL_AJ_CREDITOS|VL_TOT_AJ_CREDITOS|VL_ESTORNOS_DEB|VL_SLD_CREDOR_ANT|VL_SLD_APURADO|
    #       VL_TOT_DED|VL_ICMS_RECOLHER|VL_SLD_CREDOR_TRANSPORTAR|DEB_ESP|
    return (
        f"|E110|{fmt_valor(vl_tot_debitos)}|0.00|0.00|0.00|{fmt_valor(vl_tot_creditos)}|"
        f"0.00|0.00|0.00|{fmt_valor(saldo_credor_ant)}|{fmt_valor(vl_sld_apurado)}|"
        f"0.00|{fmt_valor(vl_icms_recolher)}|{fmt_valor(vl_sld_credor_transp)}|0.00|"
    )

def reg_e990(qtd_lin: int) -> str:
    return f"|E990|{qtd_lin}|"


# ── Bloco 9 ───────────────────────────────────────────────────

def reg_9001() -> str:
    return "|9001|0|"

def reg_9990(qtd_lin: int) -> str:
    return f"|9990|{qtd_lin}|"

def reg_9999(qtd_lin: int) -> str:
    return f"|9999|{qtd_lin}|"


# ── Montagem do arquivo ───────────────────────────────────────

def gerar_sped(empresa: Empresa, ano: int, mes: int, n_notas: int = 500) -> list:
    """Monta todas as linhas de um arquivo SPED para uma empresa/período."""

    aliq = ALIQUOTAS.get(empresa.uf, 0.18)

    # Decide aleatoriamente se este período terá divergência de apuração
    introduzir_divergencia = random.random() < 0.10
    # ~0.5% das notas terão item com linha C170 malformada
    notas_com_erro = set(random.sample(range(1, n_notas + 1), max(1, int(n_notas * 0.005))))

    linhas: list = []
    contagem: dict = {}

    def add(linha: str):
        linhas.append(linha)
        reg = linha.split("|")[1]
        contagem[reg] = contagem.get(reg, 0) + 1

    # ── Bloco 0 ──
    inicio_0 = len(linhas)
    add(reg_0000(empresa, ano, mes))
    add(reg_0001())
    add(reg_0005(empresa))
    for l in reg_0150(PARTICIPANTES):
        add(l)
    for l in reg_0190():
        add(l)
    for l in reg_0200(PRODUTOS):
        add(l)
    qtd_lin_0 = len(linhas) - inicio_0 + 1  # +1 pelo próprio 0990
    add(reg_0990(qtd_lin_0))

    # ── Bloco C ──
    inicio_c = len(linhas)
    add(reg_c001())

    total_icms_debito = 0.0

    for seq in range(1, n_notas + 1):
        tem_erro = seq in notas_com_erro
        c100, c170s, c190s, vl_icms = gerar_nota(
            seq, empresa, ano, mes, aliq, introduzir_erro=tem_erro
        )
        add(c100)
        for c170 in c170s:
            add(c170)
        for c190 in c190s:
            add(c190)
        total_icms_debito += vl_icms

    qtd_lin_c = len(linhas) - inicio_c + 1  # +1 pelo próprio C990
    add(reg_c990(qtd_lin_c))

    # ── Bloco E ──
    inicio_e = len(linhas)
    add(reg_e001())
    add(reg_e100(ano, mes))

    total_icms_debito = round(total_icms_debito, 2)
    # Créditos: simula ~20-40% do débito como crédito de entradas
    vl_creditos = round(total_icms_debito * random.uniform(0.20, 0.40), 2)
    saldo_credor_ant = round(random.uniform(0, 200), 2)

    add(reg_e110(
        vl_tot_debitos=total_icms_debito,
        vl_tot_creditos=vl_creditos,
        saldo_credor_ant=saldo_credor_ant,
        introduzir_divergencia=introduzir_divergencia,
    ))

    qtd_lin_e = len(linhas) - inicio_e + 1  # +1 pelo próprio E990
    add(reg_e990(qtd_lin_e))

    # ── Bloco 9 ──
    # O 9900 precisa contar TODOS os registros do arquivo, inclusive os do
    # próprio Bloco 9 (9001, 9900, 9990, 9999).
    cont9 = dict(contagem)
    cont9["9001"] = 1
    cont9["9990"] = 1
    cont9["9999"] = 1
    # Número de linhas 9900 = quantidade de tipos de registro distintos,
    # incluindo o próprio tipo "9900".
    num_9900 = len(cont9) + 1
    cont9["9900"] = num_9900

    linhas_9: list = [reg_9001()]
    for reg, qtd in sorted(cont9.items()):
        linhas_9.append(f"|9900|{reg}|{qtd}|")

    qtd_lin_9 = 1 + num_9900 + 1 + 1  # 9001 + linhas 9900 + 9990 + 9999
    linhas_9.append(reg_9990(qtd_lin_9))

    qtd_lin_total = len(linhas) + len(linhas_9) + 1  # +1 pelo próprio 9999
    linhas_9.append(reg_9999(qtd_lin_total))

    linhas.extend(linhas_9)

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
        help="Quantos meses gerar, a partir de 2024-01 (default: 3)"
    )
    args = parser.parse_args()

    # Períodos: jan/2024 em diante (conforme --meses)
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

            pasta = os.path.join(args.output, empresa.cnpj)
            os.makedirs(pasta, exist_ok=True)
            nome_arquivo = f"{ano}{str(mes).zfill(2)}.txt"
            caminho = os.path.join(pasta, nome_arquivo)

            with open(caminho, "w", encoding="utf-8") as f:
                f.write("\n".join(linhas) + "\n")

            total_arquivos += 1
            total_linhas   += len(linhas)
            print(f"  [OK] {empresa.cnpj} / {ano}-{str(mes).zfill(2)} -> {caminho}  ({len(linhas):,} linhas)")

    print(f"\n{total_arquivos} arquivos gerados | {total_linhas:,} linhas no total")
    print(f"Diretório de saída: {os.path.abspath(args.output)}")


if __name__ == "__main__":
    main()
