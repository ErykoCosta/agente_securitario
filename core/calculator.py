"""
core/calculator.py
Escritório Dra. Salviana Lima da Silva — OAB/SP 519.390

Funções de cálculo de liquidação prévia securitária:
  - Diferença de capital segurado (valor devido − valor pago administrativamente)
  - Correção monetária (IGPM/INPC) + juros de mora (1% a.m.)
  - Cálculo prestamista: saldo devedor + repetição de indébito
  - Tabela SUSEP de invalidez parcial por membro
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional
import math


# ---------------------------------------------------------------------------
# TABELA SUSEP DE INVALIDEZ PERMANENTE PARCIAL
# Percentuais sobre o capital segurado conforme resolução CNSP
# ---------------------------------------------------------------------------
TABELA_SUSEP_INVALIDEZ: dict[str, dict] = {
    # MEMBROS SUPERIORES
    "perda_total_braco_dominant": {"descricao": "Perda total do braço dominante", "percentual": 70.0},
    "perda_total_braco_nao_dominant": {"descricao": "Perda total do braço não dominante", "percentual": 60.0},
    "perda_total_mao_dominant": {"descricao": "Perda total da mão dominante", "percentual": 60.0},
    "perda_total_mao_nao_dominant": {"descricao": "Perda total da mão não dominante", "percentual": 50.0},
    "perda_4_dedos_dominant": {"descricao": "Perda de 4 dedos da mão dominante", "percentual": 50.0},
    "perda_polegar_dominant": {"descricao": "Perda do polegar dominante", "percentual": 25.0},
    "perda_indicador_dominant": {"descricao": "Perda do indicador dominante", "percentual": 15.0},
    # MEMBROS INFERIORES
    "perda_total_perna": {"descricao": "Perda total da perna (coxa)", "percentual": 60.0},
    "perda_total_pe": {"descricao": "Perda total do pé", "percentual": 40.0},
    "perda_todos_dedos_pe": {"descricao": "Perda de todos os dedos do pé", "percentual": 15.0},
    "perda_halux": {"descricao": "Perda do hálux (1° artelho)", "percentual": 5.0},
    # VISÃO
    "perda_total_visao_ambos": {"descricao": "Perda total da visão em ambos os olhos", "percentual": 100.0},
    "perda_total_visao_um": {"descricao": "Perda total da visão em um olho", "percentual": 30.0},
    # AUDIÇÃO
    "perda_total_audicao_ambos": {"descricao": "Perda total da audição em ambos os ouvidos", "percentual": 50.0},
    "perda_total_audicao_um": {"descricao": "Perda total da audição em um ouvido", "percentual": 15.0},
    # OUTRAS
    "invalidez_permanente_total": {"descricao": "Invalidez Permanente Total (IPT)", "percentual": 100.0},
    "paralisia_total": {"descricao": "Paralisia total e permanente", "percentual": 100.0},
    "perda_coluna_total": {"descricao": "Perda total e permanente do uso da coluna", "percentual": 70.0},
}


# ---------------------------------------------------------------------------
# ÍNDICES DE CORREÇÃO MONETÁRIA (simplificados — substituir por API real)
# Para ambiente de produção, conectar à API do IBGE (INPC/IPCA) ou FGV (IGPM).
# ---------------------------------------------------------------------------
# Valores mensais aproximados de INPC acumulado (2020–2025) — PLACEHOLDER
# Em produção, buscar via requests da API do IBGE.
INPC_MENSAL_PLACEHOLDER = {
    "2020": 1.0524,  # acumulado 2020
    "2021": 1.1014,  # acumulado 2021
    "2022": 1.1193,  # acumulado 2022
    "2023": 1.0493,  # acumulado 2023
    "2024": 1.0450,  # acumulado 2024 (estimativa)
    "2025": 1.0300,  # acumulado 2025 (estimativa)
}

TAXA_JUROS_MORA_MENSAL = Decimal("0.01")  # 1% ao mês (art. 406, CC c/c art. 161, §1°, CTN)
TAXA_JUROS_MORA_DIARIA = Decimal("0.01") / Decimal("30")


# ---------------------------------------------------------------------------
# DATACLASSES
# ---------------------------------------------------------------------------

@dataclass
class ResultadoCalculo:
    """Resultado padronizado de um cálculo de liquidação."""
    descricao: str
    capital_segurado: Decimal
    valor_pago_administrativo: Decimal
    diferenca_bruta: Decimal
    correcao_monetaria: Decimal
    juros_mora: Decimal
    valor_total_devido: Decimal
    periodo_correcao_dias: int
    data_evento: date
    data_calculo: date
    taxa_correcao_aplicada: str
    observacoes: list[str] = field(default_factory=list)

    def formatar_brl(self, valor: Decimal) -> str:
        return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    def resumo(self) -> str:
        linhas = [
            "=" * 60,
            f"CÁLCULO DE LIQUIDAÇÃO — {self.descricao}",
            "=" * 60,
            f"Capital Segurado:            {self.formatar_brl(self.capital_segurado)}",
            f"(-) Valor pago adm.:         {self.formatar_brl(self.valor_pago_administrativo)}",
            f"(=) Diferença bruta:         {self.formatar_brl(self.diferenca_bruta)}",
            f"(+) Correção monetária:      {self.formatar_brl(self.correcao_monetaria)}",
            f"    ({self.taxa_correcao_aplicada})",
            f"(+) Juros de mora (1% a.m.): {self.formatar_brl(self.juros_mora)}",
            f"(=) TOTAL DEVIDO:            {self.formatar_brl(self.valor_total_devido)}",
            "-" * 60,
            f"Período de correção: {self.data_evento} → {self.data_calculo} ({self.periodo_correcao_dias} dias)",
        ]
        if self.observacoes:
            linhas.append("\nOBSERVAÇÕES:")
            for obs in self.observacoes:
                linhas.append(f"  • {obs}")
        linhas.append("=" * 60)
        return "\n".join(linhas)


@dataclass
class ResultadoPrestamista:
    """Resultado do cálculo de seguro prestamista."""
    saldo_devedor_data_sinistro: Decimal
    parcelas_descontadas_apos_sinistro: Decimal
    numero_parcelas_indevidas: int
    valor_parcela_mensal: Decimal
    correcao_monetaria_parcelas: Decimal
    juros_mora_parcelas: Decimal
    indenizacao_principal: Decimal  # cobertura do saldo devedor
    repeticao_indebito: Decimal  # parcelas descontadas indevidamente
    total_devido: Decimal
    observacoes: list[str] = field(default_factory=list)

    def formatar_brl(self, valor: Decimal) -> str:
        return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    def resumo(self) -> str:
        linhas = [
            "=" * 65,
            "CÁLCULO PRESTAMISTA — LIQUIDAÇÃO DO SINISTRO",
            "=" * 65,
            "I. COBERTURA DO SALDO DEVEDOR",
            f"   Saldo devedor na data do sinistro: {self.formatar_brl(self.saldo_devedor_data_sinistro)}",
            "",
            "II. REPETIÇÃO DE INDÉBITO (parcelas descontadas após sinistro)",
            f"   Parcelas indevidas: {self.numero_parcelas_indevidas}x {self.formatar_brl(self.valor_parcela_mensal)}",
            f"   Subtotal bruto:     {self.formatar_brl(self.parcelas_descontadas_apos_sinistro)}",
            f"   (+) Correção:       {self.formatar_brl(self.correcao_monetaria_parcelas)}",
            f"   (+) Juros mora:     {self.formatar_brl(self.juros_mora_parcelas)}",
            f"   Repetição líquida:  {self.formatar_brl(self.repeticao_indebito)}",
            "",
            f"INDENIZAÇÃO PRINCIPAL:  {self.formatar_brl(self.indenizacao_principal)}",
            f"REPETIÇÃO DE INDÉBITO:  {self.formatar_brl(self.repeticao_indebito)}",
            f"{'=' * 65}",
            f"TOTAL DEVIDO:           {self.formatar_brl(self.total_devido)}",
        ]
        if self.observacoes:
            linhas.append("\nOBSERVAÇÕES:")
            for obs in self.observacoes:
                linhas.append(f"  • {obs}")
        linhas.append("=" * 65)
        return "\n".join(linhas)


# ---------------------------------------------------------------------------
# FUNÇÕES PRINCIPAIS
# ---------------------------------------------------------------------------

def calcular_diferenca_capital_segurado(
    capital_segurado: float,
    valor_pago_administrativo: float,
    data_evento: date,
    data_calculo: Optional[date] = None,
    usar_juros_mora: bool = True,
    taxa_correcao_anual: float = 0.05,  # 5% ao ano como fallback
    descricao: str = "Seguro de Vida/AP",
) -> ResultadoCalculo:
    """
    Calcula a diferença entre o capital segurado devido e o valor pago
    administrativamente pela seguradora, com correção monetária e juros de mora.

    Args:
        capital_segurado: Valor total do capital segurado na apólice (R$).
        valor_pago_administrativo: Valor efetivamente pago pela seguradora (R$).
        data_evento: Data do sinistro (início da correção — Súmula 632, STJ).
        data_calculo: Data base do cálculo (padrão: hoje).
        usar_juros_mora: Aplicar juros de mora de 1% a.m.
        taxa_correcao_anual: Taxa de correção monetária anual (fallback sem índice oficial).
        descricao: Descrição do cálculo para o relatório.

    Returns:
        ResultadoCalculo com todos os valores detalhados.
    """
    if data_calculo is None:
        data_calculo = date.today()

    cs = Decimal(str(capital_segurado)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    pago = Decimal(str(valor_pago_administrativo)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    diferenca = (cs - pago).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    # Calcular período em dias
    delta = (data_calculo - data_evento).days
    delta_meses = Decimal(str(delta)) / Decimal("30")

    # Correção monetária (aplicada sobre a diferença bruta)
    taxa_correcao_diaria = Decimal(str(taxa_correcao_anual)) / Decimal("365")
    fator_correcao = (Decimal("1") + taxa_correcao_diaria) ** Decimal(str(delta)) - Decimal("1")
    correcao = (diferenca * fator_correcao).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    # Juros de mora (1% a.m. sobre a diferença bruta — CC art. 406)
    juros = Decimal("0")
    if usar_juros_mora:
        juros = (diferenca * TAXA_JUROS_MORA_MENSAL * delta_meses).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

    total = (diferenca + correcao + juros).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    obs = []
    if diferenca <= 0:
        obs.append(
            "⚠️ Valor pago igual ou superior ao capital segurado. Verificar se houve "
            "pagamento a menor por aplicação de percentual de invalidez parcial incorreto."
        )
    obs.append(
        "[CONFERIR: índice de correção monetária — utilizar INPC/IGPM oficial do período "
        "via API do IBGE para o cálculo definitivo]"
    )
    obs.append(
        "Juros de mora incidem desde o evento danoso (Súmula 616, STJ) ou desde a "
        "recusa/inadimplemento, a depender do entendimento do Juízo."
    )

    return ResultadoCalculo(
        descricao=descricao,
        capital_segurado=cs,
        valor_pago_administrativo=pago,
        diferenca_bruta=diferenca,
        correcao_monetaria=correcao,
        juros_mora=juros,
        valor_total_devido=total,
        periodo_correcao_dias=delta,
        data_evento=data_evento,
        data_calculo=data_calculo,
        taxa_correcao_aplicada=f"Taxa estimada {taxa_correcao_anual*100:.1f}% a.a. (substituir por INPC/IGPM)",
        observacoes=obs,
    )


def calcular_invalidez_parcial_susep(
    capital_segurado: float,
    codigo_lesao: str,
    percentual_customizado: Optional[float] = None,
    valor_pago_administrativo: float = 0.0,
    data_evento: Optional[date] = None,
    data_calculo: Optional[date] = None,
) -> ResultadoCalculo:
    """
    Calcula o valor devido para invalidez permanente parcial com base na
    tabela SUSEP. Compara com o valor pago administrativamente.

    Args:
        capital_segurado: Capital segurado total da apólice.
        codigo_lesao: Código da lesão conforme TABELA_SUSEP_INVALIDEZ.
        percentual_customizado: Percentual específico se a lesão não constar na tabela.
        valor_pago_administrativo: Valor pago pela seguradora.
        data_evento: Data do sinistro.
        data_calculo: Data base do cálculo.
    """
    if data_evento is None:
        data_evento = date.today()
    if data_calculo is None:
        data_calculo = date.today()

    obs = []
    if codigo_lesao in TABELA_SUSEP_INVALIDEZ:
        entrada = TABELA_SUSEP_INVALIDEZ[codigo_lesao]
        percentual = entrada["percentual"]
        descricao_lesao = entrada["descricao"]
    elif percentual_customizado is not None:
        percentual = percentual_customizado
        descricao_lesao = f"Lesão customizada ({percentual:.1f}%)"
        obs.append(
            "[CONFERIR: percentual de invalidez não consta na tabela SUSEP padrão. "
            "Verificar resolução CNSP vigente para a data do sinistro.]"
        )
    else:
        raise ValueError(
            f"Código de lesão '{codigo_lesao}' não encontrado na tabela SUSEP. "
            f"Códigos disponíveis: {list(TABELA_SUSEP_INVALIDEZ.keys())}"
        )

    capital_devido = Decimal(str(capital_segurado)) * Decimal(str(percentual)) / Decimal("100")
    capital_devido = capital_devido.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    obs.append(
        f"Percentual SUSEP aplicado: {percentual:.1f}% sobre capital de "
        f"R$ {capital_segurado:,.2f} = R$ {float(capital_devido):,.2f}"
    )

    return calcular_diferenca_capital_segurado(
        capital_segurado=float(capital_devido),
        valor_pago_administrativo=valor_pago_administrativo,
        data_evento=data_evento,
        data_calculo=data_calculo,
        descricao=f"Invalidez Parcial — {descricao_lesao}",
    )


def calcular_prestamista(
    saldo_devedor_data_sinistro: float,
    valor_parcela_mensal: float,
    numero_parcelas_indevidas: int,
    data_sinistro: date,
    data_calculo: Optional[date] = None,
    taxa_correcao_anual: float = 0.05,
) -> ResultadoPrestamista:
    """
    Calcula a liquidação de seguro prestamista:
    (1) Cobertura do saldo devedor na data do sinistro.
    (2) Repetição de indébito das parcelas descontadas indevidamente após o sinistro.

    Args:
        saldo_devedor_data_sinistro: Saldo devedor do contrato na data do sinistro.
        valor_parcela_mensal: Valor da parcela mensal do contrato.
        numero_parcelas_indevidas: Número de parcelas descontadas após o sinistro.
        data_sinistro: Data do sinistro (óbito, invalidez, etc.).
        data_calculo: Data base do cálculo (padrão: hoje).
        taxa_correcao_anual: Taxa de correção monetária anual (fallback).
    """
    if data_calculo is None:
        data_calculo = date.today()

    saldo = Decimal(str(saldo_devedor_data_sinistro)).quantize(Decimal("0.01"))
    parcela = Decimal(str(valor_parcela_mensal)).quantize(Decimal("0.01"))
    n_parcelas = numero_parcelas_indevidas

    # Total bruto de parcelas indevidas
    total_parcelas_brutas = (parcela * Decimal(str(n_parcelas))).quantize(Decimal("0.01"))

    # Calcular correção e juros médios sobre as parcelas
    # (simplificação: cada parcela tem período diferente — aqui usamos a média)
    delta_total = (data_calculo - data_sinistro).days
    delta_medio = Decimal(str(delta_total)) / Decimal("2")  # período médio

    taxa_correcao_diaria = Decimal(str(taxa_correcao_anual)) / Decimal("365")
    fator_correcao = (Decimal("1") + taxa_correcao_diaria) ** delta_medio - Decimal("1")
    correcao_parcelas = (total_parcelas_brutas * fator_correcao).quantize(Decimal("0.01"))

    delta_meses_medio = delta_medio / Decimal("30")
    juros_parcelas = (total_parcelas_brutas * TAXA_JUROS_MORA_MENSAL * delta_meses_medio).quantize(Decimal("0.01"))

    repeticao_liquida = (total_parcelas_brutas + correcao_parcelas + juros_parcelas).quantize(Decimal("0.01"))
    total_devido = (saldo + repeticao_liquida).quantize(Decimal("0.01"))

    obs = [
        "O saldo devedor deve ser apurado na DATA DO SINISTRO (óbito/invalidez), "
        "conforme extrato bancário do período — solicitar via diligência.",
        "As parcelas indevidas devem ser individualizadas para cálculo preciso; "
        "este cálculo utiliza período médio (simplificação).",
        "[CONFERIR: índice de correção — utilizar INPC/IGPM oficial via API IBGE]",
        "Fundamento da repetição de indébito: art. 42, parágrafo único, CDC "
        "(devolução em dobro se cobrado indevidamente com má-fé) — avaliar aplicabilidade.",
    ]

    return ResultadoPrestamista(
        saldo_devedor_data_sinistro=saldo,
        parcelas_descontadas_apos_sinistro=total_parcelas_brutas,
        numero_parcelas_indevidas=n_parcelas,
        valor_parcela_mensal=parcela,
        correcao_monetaria_parcelas=correcao_parcelas,
        juros_mora_parcelas=juros_parcelas,
        indenizacao_principal=saldo,
        repeticao_indebito=repeticao_liquida,
        total_devido=total_devido,
        observacoes=obs,
    )


def calcular_prescricao(
    data_negativa_ou_ciencia: date,
    data_referencia: Optional[date] = None,
    prazo_anos: int = 1,
    data_protocolo_adm: Optional[date] = None,
    data_encerramento_adm: Optional[date] = None,
) -> dict:
    """
    Calcula o prazo prescricional e retorna status de alerta.

    Args:
        data_negativa_ou_ciencia: Data da recusa ou da ciência do segurado.
        data_referencia: Data de referência (padrão: hoje).
        prazo_anos: Prazo prescricional em anos (1 para seguro geral, 3 para DPVAT).
        data_protocolo_adm: Data do protocolo administrativo (suspende o prazo).
        data_encerramento_adm: Data do encerramento do procedimento administrativo.

    Returns:
        Dicionário com status, dias restantes, data de vencimento e mensagem de alerta.
    """
    if data_referencia is None:
        data_referencia = date.today()

    # Calcular vencimento base (sem suspensão)
    try:
        vencimento_base = data_negativa_ou_ciencia.replace(
            year=data_negativa_ou_ciencia.year + prazo_anos
        )
    except ValueError:
        # 29/02 em ano não bissexto
        vencimento_base = data_negativa_ou_ciencia.replace(
            year=data_negativa_ou_ciencia.year + prazo_anos, day=28
        )

    # Calcular dias de suspensão por protocolo administrativo (Súmula 229, STJ)
    dias_suspensao = 0
    if data_protocolo_adm and data_encerramento_adm:
        dias_suspensao = max(0, (data_encerramento_adm - data_protocolo_adm).days)
        vencimento_final = date.fromordinal(vencimento_base.toordinal() + dias_suspensao)
    elif data_protocolo_adm and not data_encerramento_adm:
        # Protocolo sem encerramento: suspensão ainda em curso
        dias_suspensao = (data_referencia - data_protocolo_adm).days
        vencimento_final = date.fromordinal(vencimento_base.toordinal() + dias_suspensao)
    else:
        vencimento_final = vencimento_base

    dias_restantes = (vencimento_final - data_referencia).days
    prescrito = dias_restantes < 0

    # Mensagem de alerta
    if prescrito:
        status = "PRESCRITO"
        alerta = (
            f"🔴 ALERTA DE PRESCRIÇÃO: PRAZO EXPIRADO HÁ {abs(dias_restantes)} DIAS — "
            "ação não recomendada sem análise específica de causas suspensivas/interruptivas."
        )
        cor = "red"
    elif dias_restantes <= 60:
        status = "URGENTE"
        alerta = (
            f"🟡 ATENÇÃO: PRAZO PRESCRICIONAL VENCE EM {dias_restantes} DIAS — "
            "providências URGENTES."
        )
        cor = "orange"
    else:
        status = "EM_CURSO"
        alerta = (
            f"🟢 PRESCRIÇÃO: Prazo em curso. Vencimento estimado em "
            f"{vencimento_final.strftime('%d/%m/%Y')} ({dias_restantes} dias restantes)."
        )
        cor = "green"

    return {
        "status": status,
        "prescrito": prescrito,
        "dias_restantes": dias_restantes,
        "data_negativa": data_negativa_ou_ciencia,
        "vencimento_base": vencimento_base,
        "vencimento_com_suspensao": vencimento_final,
        "dias_suspensao": dias_suspensao,
        "prazo_anos": prazo_anos,
        "data_referencia": data_referencia,
        "alerta": alerta,
        "cor": cor,
        "mensagem_sumulas": (
            "Súmulas aplicáveis: 229 (suspensão por protocolo adm.), "
            "278 (início na ciência da invalidez), 101 (prescrição 1 ano — seguro grupo)"
        ),
    }


def listar_lesoes_susep() -> list[dict]:
    """Retorna a tabela SUSEP formatada para exibição em UI."""
    return [
        {
            "codigo": k,
            "descricao": v["descricao"],
            "percentual": v["percentual"],
        }
        for k, v in TABELA_SUSEP_INVALIDEZ.items()
    ]
