"""
core/extractor.py
Escritório Dra. Salviana Lima da Silva — OAB/SP 519.390

Leitura, extração e parsing de documentos PDF:
  - Apólices e certificados de seguro
  - Cartas de recusa/negativa
  - Laudos médicos e documentos de sinistro
  - Contratos de empréstimo/financiamento
"""

from __future__ import annotations

import io
import re
from pathlib import Path
from typing import Optional, Union

# Importações com fallback gracioso
try:
    import pdfplumber
    HAS_PDFPLUMBER = True
except ImportError:
    HAS_PDFPLUMBER = False

try:
    import fitz  # pymupdf
    HAS_PYMUPDF = True
except ImportError:
    HAS_PYMUPDF = False

try:
    from pypdf import PdfReader
    HAS_PYPDF = True
except ImportError:
    HAS_PYPDF = False


# ---------------------------------------------------------------------------
# EXTRAÇÃO DE TEXTO DE PDF
# ---------------------------------------------------------------------------

def extrair_texto_pdf(
    arquivo: Union[bytes, str, Path],
    metodo: str = "auto",
    max_paginas: int = 50,
) -> str:
    """
    Extrai texto de um PDF usando a melhor biblioteca disponível.

    Args:
        arquivo: bytes do arquivo, caminho (str/Path) ou objeto file-like.
        metodo: 'pdfplumber', 'pymupdf', 'pypdf' ou 'auto' (tentativa em cascata).
        max_paginas: Número máximo de páginas a processar.

    Returns:
        Texto extraído como string.
    """
    if isinstance(arquivo, (str, Path)):
        with open(arquivo, "rb") as f:
            dados = f.read()
    else:
        dados = arquivo

    if metodo == "auto":
        for tentativa in ["pdfplumber", "pymupdf", "pypdf"]:
            try:
                return _extrair_com_metodo(dados, tentativa, max_paginas)
            except Exception:
                continue
        raise RuntimeError("Nenhuma biblioteca de PDF disponível. Instale pdfplumber ou pymupdf.")
    else:
        return _extrair_com_metodo(dados, metodo, max_paginas)


def _extrair_com_metodo(dados: bytes, metodo: str, max_paginas: int) -> str:
    if metodo == "pdfplumber" and HAS_PDFPLUMBER:
        return _extrair_pdfplumber(dados, max_paginas)
    elif metodo == "pymupdf" and HAS_PYMUPDF:
        return _extrair_pymupdf(dados, max_paginas)
    elif metodo == "pypdf" and HAS_PYPDF:
        return _extrair_pypdf(dados, max_paginas)
    else:
        raise ImportError(f"Biblioteca '{metodo}' não disponível.")


def _extrair_pdfplumber(dados: bytes, max_paginas: int) -> str:
    with pdfplumber.open(io.BytesIO(dados)) as pdf:
        partes = []
        for i, pagina in enumerate(pdf.pages[:max_paginas]):
            texto = pagina.extract_text(x_tolerance=3, y_tolerance=3) or ""
            partes.append(f"[Página {i+1}]\n{texto}")
        return "\n\n".join(partes)


def _extrair_pymupdf(dados: bytes, max_paginas: int) -> str:
    doc = fitz.open(stream=dados, filetype="pdf")
    partes = []
    for i in range(min(max_paginas, len(doc))):
        pagina = doc[i]
        texto = pagina.get_text("text")
        partes.append(f"[Página {i+1}]\n{texto}")
    doc.close()
    return "\n\n".join(partes)


def _extrair_pypdf(dados: bytes, max_paginas: int) -> str:
    reader = PdfReader(io.BytesIO(dados))
    partes = []
    for i, pagina in enumerate(reader.pages[:max_paginas]):
        texto = pagina.extract_text() or ""
        partes.append(f"[Página {i+1}]\n{texto}")
    return "\n\n".join(partes)


# ---------------------------------------------------------------------------
# PRÉ-PROCESSAMENTO E LIMPEZA DE TEXTO
# ---------------------------------------------------------------------------

def limpar_texto(texto: str) -> str:
    """
    Limpa e normaliza o texto extraído de PDF:
    - Remove caracteres de controle
    - Colapsa espaços múltiplos
    - Remove linhas em branco excessivas
    - Normaliza quebras de linha
    """
    # Remover caracteres de controle (exceto \n e \t)
    texto = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", " ", texto)
    # Colapsar espaços múltiplos dentro de uma linha
    texto = re.sub(r"[ \t]+", " ", texto)
    # Normalizar quebras de linha (máximo 2 consecutivas)
    texto = re.sub(r"\n{3,}", "\n\n", texto)
    # Remover espaços no início/fim de cada linha
    linhas = [l.strip() for l in texto.split("\n")]
    texto = "\n".join(linhas)
    return texto.strip()


def truncar_texto(texto: str, max_chars: int = 40000) -> str:
    """
    Trunca o texto para não exceder o limite de tokens da API.
    Preserva o início (identificação) e o final (assinatura/valores) do documento.
    """
    if len(texto) <= max_chars:
        return texto
    meio = max_chars // 2
    inicio = texto[:meio]
    fim = texto[-(max_chars - meio):]
    return f"{inicio}\n\n[... TEXTO TRUNCADO — {len(texto) - max_chars} caracteres omitidos ...]\n\n{fim}"


# ---------------------------------------------------------------------------
# DETECÇÃO DO TIPO DE DOCUMENTO
# ---------------------------------------------------------------------------

PADROES_TIPO_DOC = {
    "carta_recusa": [
        r"(?i)recusa(mos)?.*cober(tura)?",
        r"(?i)indeferim",
        r"(?i)n[aã]o.*cober(tura)?",
        r"(?i)improcedente.*sinistro",
        r"(?i)declara(mos)?.*(n[aã]o|neg)",
        r"(?i)carta.*recusa",
        r"(?i)negativa.*sinistro",
    ],
    "apolice": [
        r"(?i)ap[oó]lice.*n[oú]mero",
        r"(?i)certificado.*seguro",
        r"(?i)vigente.*de.*at[eé]",
        r"(?i)pr[eê]mio.*mensal",
        r"(?i)capital.*segurado",
        r"(?i)contrat(ant|o).*segura",
    ],
    "laudo_medico": [
        r"(?i)laudo.*m[eé]dic",
        r"(?i)atestado.*m[eé]dic",
        r"(?i)diagn[oó]stic",
        r"(?i)CID[\-\s]\d",
        r"(?i)incapacidade.*laboral",
        r"(?i)invalidez.*permanente",
    ],
    "contrato_emprestimo": [
        r"(?i)contrato.*cr[eé]dito",
        r"(?i)cedula.*cr[eé]dito",
        r"(?i)saldo.*devedor",
        r"(?i)taxa.*juros.*a\.m",
        r"(?i)parcela.*mensal.*R\$",
        r"(?i)financiament",
    ],
    "comprovante_pagamento": [
        r"(?i)comprovante.*pagamento",
        r"(?i)recibo.*pagamento",
        r"(?i)dep[oó]sito.*realizado",
        r"(?i)transfer[eê]ncia.*realizada",
        r"(?i)pago.*em.*\d{2}\/\d{2}",
    ],
}


def detectar_tipo_documento(texto: str) -> str:
    """
    Detecta o tipo de documento com base em padrões regex.

    Returns:
        Um dos tipos: 'carta_recusa', 'apolice', 'laudo_medico',
        'contrato_emprestimo', 'comprovante_pagamento', 'outro'.
    """
    pontuacoes = {tipo: 0 for tipo in PADROES_TIPO_DOC}
    for tipo, padroes in PADROES_TIPO_DOC.items():
        for padrao in padroes:
            if re.search(padrao, texto):
                pontuacoes[tipo] += 1

    melhor_tipo = max(pontuacoes, key=pontuacoes.get)
    if pontuacoes[melhor_tipo] == 0:
        return "outro"
    return melhor_tipo


# ---------------------------------------------------------------------------
# EXTRAÇÃO DE CAMPOS ESTRUTURADOS (regex rápido — complementar à IA)
# ---------------------------------------------------------------------------

def extrair_campos_basicos(texto: str) -> dict:
    """
    Extrai campos básicos de documentos securitários via regex.
    Esta extração é complementar à extração via LLM (core/agent.py).
    """
    resultado = {
        "cpf": None,
        "cnpj_seguradora": None,
        "numero_apolice": None,
        "capital_segurado": None,
        "data_sinistro": None,
        "data_negativa": None,
        "valor_monetario_principal": None,
    }

    # CPF
    m = re.search(r"\d{3}[\.\-]?\d{3}[\.\-]?\d{3}[\.\-]?\d{2}", texto)
    if m:
        resultado["cpf"] = m.group()

    # CNPJ
    m = re.search(r"\d{2}[\.\-]?\d{3}[\.\-]?\d{3}[\/\-]?\d{4}[\.\-]?\d{2}", texto)
    if m:
        resultado["cnpj_seguradora"] = m.group()

    # Número de apólice/certificado (padrões comuns)
    m = re.search(r"(?i)(?:ap[oó]lice|certificado|n[oú]mero)[\s\:\#]*(\d[\d\-\.\/]+)", texto)
    if m:
        resultado["numero_apolice"] = m.group(1).strip()

    # Capital segurado / valores monetários em R$
    valores = re.findall(r"R\$\s*[\d\.]+,\d{2}", texto)
    if valores:
        resultado["valor_monetario_principal"] = valores[0]
        # Tentar identificar "capital segurado"
        m = re.search(r"(?i)capital\s+segurado[\s\:\=]*R\$\s*([\d\.]+,\d{2})", texto)
        if m:
            resultado["capital_segurado"] = m.group(1)

    # Datas no formato DD/MM/AAAA
    datas = re.findall(r"\d{2}\/\d{2}\/\d{4}", texto)
    if datas:
        resultado["datas_encontradas"] = datas[:10]  # máx 10 datas

    return resultado


# ---------------------------------------------------------------------------
# PROCESSADOR PRINCIPAL
# ---------------------------------------------------------------------------

class ProcessadorDocumento:
    """
    Classe principal para processar um documento PDF securitário.
    Extrai, limpa, detecta o tipo e prepara o texto para análise pela IA.
    """

    def __init__(self, nome_arquivo: str = "documento.pdf"):
        self.nome_arquivo = nome_arquivo
        self.texto_bruto: str = ""
        self.texto_limpo: str = ""
        self.tipo_detectado: str = "outro"
        self.campos_basicos: dict = {}
        self.num_paginas: int = 0
        self.tamanho_bytes: int = 0

    def processar(self, dados: bytes) -> "ProcessadorDocumento":
        """
        Pipeline completo: extrai → limpa → detecta → extrai campos.

        Args:
            dados: bytes do arquivo PDF.

        Returns:
            Self para encadeamento.
        """
        self.tamanho_bytes = len(dados)

        # 1. Extrair texto
        self.texto_bruto = extrair_texto_pdf(dados)

        # 2. Contar páginas (aproximado pelo número de marcadores [Página N])
        self.num_paginas = len(re.findall(r"\[Página \d+\]", self.texto_bruto))

        # 3. Limpar
        self.texto_limpo = limpar_texto(self.texto_bruto)

        # 4. Detectar tipo
        self.tipo_detectado = detectar_tipo_documento(self.texto_limpo)

        # 5. Extrair campos básicos
        self.campos_basicos = extrair_campos_basicos(self.texto_limpo)

        return self

    def texto_para_ia(self, max_chars: int = 35000) -> str:
        """
        Retorna o texto preparado para envio à IA (truncado se necessário).
        Inclui metadados do documento como prefixo.
        """
        prefixo = (
            f"=== DOCUMENTO: {self.nome_arquivo} ===\n"
            f"Tipo detectado: {self.tipo_detectado}\n"
            f"Páginas: {self.num_paginas}\n"
            f"CPF detectado: {self.campos_basicos.get('cpf', 'N/D')}\n"
            f"Apólice/Certificado detectado: {self.campos_basicos.get('numero_apolice', 'N/D')}\n"
            f"Capital segurado detectado: {self.campos_basicos.get('capital_segurado', 'N/D')}\n"
            "=" * 50 + "\n\n"
        )
        texto_truncado = truncar_texto(self.texto_limpo, max_chars - len(prefixo))
        return prefixo + texto_truncado

    def resumo(self) -> dict:
        return {
            "arquivo": self.nome_arquivo,
            "tipo": self.tipo_detectado,
            "paginas": self.num_paginas,
            "tamanho_kb": round(self.tamanho_bytes / 1024, 1),
            "campos": self.campos_basicos,
        }


def processar_multiplos_pdfs(
    arquivos: list[tuple[str, bytes]]
) -> tuple[str, list[dict]]:
    """
    Processa múltiplos PDFs e retorna o texto consolidado e os resumos.

    Args:
        arquivos: Lista de tuplas (nome_arquivo, bytes).

    Returns:
        Tuple (texto_consolidado, lista_de_resumos).
    """
    textos = []
    resumos = []

    for nome, dados in arquivos:
        try:
            proc = ProcessadorDocumento(nome_arquivo=nome)
            proc.processar(dados)
            textos.append(proc.texto_para_ia())
            resumos.append(proc.resumo())
        except Exception as e:
            textos.append(f"=== ERRO ao processar {nome}: {str(e)} ===\n")
            resumos.append({"arquivo": nome, "tipo": "erro", "erro": str(e)})

    texto_consolidado = "\n\n" + ("=" * 70) + "\n\n".join(textos)
    return texto_consolidado, resumos
