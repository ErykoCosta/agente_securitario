"""
app.py
Agente Jurídico Securitário — Escritório Dra. Salviana Lima da Silva
OAB/SP 519.390 | Osasco/SP

Interface corporativa em Streamlit para análise e redação de peças jurídicas
em matéria de Direito Securitário, com foco na defesa de segurados,
beneficiários e vítimas.
"""

from __future__ import annotations

import io
import os
import json
from datetime import date, datetime
from typing import Optional

import streamlit as st
from dotenv import load_dotenv

# Carrega variáveis de ambiente do .env (se existir)
load_dotenv()

# ---------------------------------------------------------------------------
# CONFIGURAÇÃO DA PÁGINA — DEVE SER O PRIMEIRO COMANDO STREAMLIT
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Agente Jurídico Securitário | Dra. Salviana Lima",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help": None,
        "Report a bug": None,
        "About": (
            "**Agente Jurídico Securitário**\n\n"
            "Desenvolvido exclusivamente para o escritório da\n"
            "Dra. Salviana Lima da Silva — OAB/SP 519.390\n\n"
            "Osasco/SP — Direito Securitário"
        ),
    },
)

# ---------------------------------------------------------------------------
# CSS CORPORATIVO
# ---------------------------------------------------------------------------
st.markdown("""
<style>
/* Importar fonte Inter do Google Fonts */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

/* Reset e base */
html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

/* Fundo principal */
.stApp {
    background: linear-gradient(135deg, #0f0f1a 0%, #1a1a2e 50%, #16213e 100%);
    color: #e8eaf6;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0d0d1a 0%, #1a1433 100%);
    border-right: 1px solid rgba(103, 58, 183, 0.3);
}

section[data-testid="stSidebar"] .block-container {
    padding-top: 1.5rem;
}

/* Header do escritório */
.header-escritorio {
    background: linear-gradient(135deg, rgba(103, 58, 183, 0.25) 0%, rgba(63, 81, 181, 0.25) 100%);
    border: 1px solid rgba(103, 58, 183, 0.5);
    border-radius: 16px;
    padding: 1.5rem 2rem;
    margin-bottom: 1.5rem;
    text-align: center;
    backdrop-filter: blur(10px);
}

.header-escritorio h1 {
    font-size: 1.4rem;
    font-weight: 800;
    color: #b39ddb;
    margin: 0 0 0.25rem 0;
    letter-spacing: -0.02em;
}

.header-escritorio p {
    font-size: 0.82rem;
    color: #9e9e9e;
    margin: 0;
}

/* Cards de status/alerta de prescrição */
.prescricao-ok {
    background: linear-gradient(135deg, rgba(76, 175, 80, 0.15) 0%, rgba(56, 142, 60, 0.15) 100%);
    border: 1px solid rgba(76, 175, 80, 0.5);
    border-left: 4px solid #4caf50;
    border-radius: 8px;
    padding: 1rem 1.2rem;
    margin: 0.8rem 0;
}

.prescricao-urgente {
    background: linear-gradient(135deg, rgba(255, 152, 0, 0.15) 0%, rgba(230, 119, 0, 0.15) 100%);
    border: 1px solid rgba(255, 152, 0, 0.5);
    border-left: 4px solid #ff9800;
    border-radius: 8px;
    padding: 1rem 1.2rem;
    margin: 0.8rem 0;
    animation: pulse-orange 2s infinite;
}

.prescricao-expirada {
    background: linear-gradient(135deg, rgba(244, 67, 54, 0.20) 0%, rgba(198, 40, 40, 0.20) 100%);
    border: 1px solid rgba(244, 67, 54, 0.6);
    border-left: 4px solid #f44336;
    border-radius: 8px;
    padding: 1rem 1.2rem;
    margin: 0.8rem 0;
    animation: pulse-red 1.5s infinite;
}

@keyframes pulse-orange {
    0%, 100% { box-shadow: 0 0 0 0 rgba(255, 152, 0, 0.3); }
    50% { box-shadow: 0 0 0 6px rgba(255, 152, 0, 0); }
}

@keyframes pulse-red {
    0%, 100% { box-shadow: 0 0 0 0 rgba(244, 67, 54, 0.4); }
    50% { box-shadow: 0 0 0 8px rgba(244, 67, 54, 0); }
}

/* Score de viabilidade */
.score-alta {
    background: linear-gradient(135deg, rgba(76, 175, 80, 0.2) 0%, rgba(27, 94, 32, 0.2) 100%);
    border: 2px solid rgba(76, 175, 80, 0.6);
    border-radius: 12px;
    padding: 1.2rem;
    text-align: center;
    font-weight: 700;
    color: #81c784;
    font-size: 1.1rem;
}

.score-media {
    background: linear-gradient(135deg, rgba(255, 193, 7, 0.2) 0%, rgba(245, 127, 23, 0.2) 100%);
    border: 2px solid rgba(255, 193, 7, 0.6);
    border-radius: 12px;
    padding: 1.2rem;
    text-align: center;
    font-weight: 700;
    color: #ffd54f;
    font-size: 1.1rem;
}

.score-baixa {
    background: linear-gradient(135deg, rgba(255, 87, 34, 0.2) 0%, rgba(183, 28, 28, 0.2) 100%);
    border: 2px solid rgba(255, 87, 34, 0.6);
    border-radius: 12px;
    padding: 1.2rem;
    text-align: center;
    font-weight: 700;
    color: #ff8a65;
    font-size: 1.1rem;
}

.score-inviavel {
    background: linear-gradient(135deg, rgba(244, 67, 54, 0.25) 0%, rgba(74, 20, 20, 0.25) 100%);
    border: 2px solid rgba(244, 67, 54, 0.7);
    border-radius: 12px;
    padding: 1.2rem;
    text-align: center;
    font-weight: 700;
    color: #ef9a9a;
    font-size: 1.1rem;
}

/* Abas */
.stTabs [data-baseweb="tab-list"] {
    background: rgba(26, 20, 51, 0.6);
    border-radius: 12px;
    padding: 4px;
    gap: 4px;
    border: 1px solid rgba(103, 58, 183, 0.3);
}

.stTabs [data-baseweb="tab"] {
    border-radius: 8px;
    color: #9e9e9e;
    font-weight: 500;
    padding: 0.5rem 1.2rem;
    transition: all 0.2s ease;
}

.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, #673ab7 0%, #3f51b5 100%) !important;
    color: #ffffff !important;
    box-shadow: 0 4px 15px rgba(103, 58, 183, 0.4);
}

/* Botões primários */
.stButton > button[kind="primary"],
.stButton > button {
    background: linear-gradient(135deg, #673ab7 0%, #3f51b5 100%);
    color: white;
    border: none;
    border-radius: 10px;
    font-weight: 600;
    padding: 0.6rem 1.5rem;
    transition: all 0.3s ease;
    box-shadow: 0 4px 15px rgba(103, 58, 183, 0.3);
}

.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 25px rgba(103, 58, 183, 0.5);
}

/* Inputs e selects */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea,
.stSelectbox > div > div {
    background: rgba(26, 20, 51, 0.7) !important;
    border: 1px solid rgba(103, 58, 183, 0.4) !important;
    border-radius: 8px !important;
    color: #e8eaf6 !important;
}

/* Upload */
.stFileUploader {
    background: rgba(26, 20, 51, 0.5);
    border: 2px dashed rgba(103, 58, 183, 0.4);
    border-radius: 12px;
}

/* Expanders */
.streamlit-expanderHeader {
    background: rgba(26, 20, 51, 0.6);
    border: 1px solid rgba(103, 58, 183, 0.3);
    border-radius: 8px;
    color: #b39ddb;
}

/* Métricas */
[data-testid="stMetric"] {
    background: rgba(103, 58, 183, 0.1);
    border: 1px solid rgba(103, 58, 183, 0.3);
    border-radius: 10px;
    padding: 0.75rem 1rem;
}

/* Divisor */
hr {
    border-color: rgba(103, 58, 183, 0.3);
}

/* Texto de output jurídico */
.output-juridico {
    background: rgba(15, 15, 30, 0.8);
    border: 1px solid rgba(103, 58, 183, 0.3);
    border-radius: 12px;
    padding: 1.5rem;
    font-family: 'Inter', serif;
    font-size: 0.9rem;
    line-height: 1.7;
    color: #e0e0e0;
    white-space: pre-wrap;
    max-height: 600px;
    overflow-y: auto;
}

/* Chip de ramo */
.chip-ramo {
    display: inline-block;
    background: linear-gradient(135deg, rgba(103, 58, 183, 0.3) 0%, rgba(63, 81, 181, 0.3) 100%);
    border: 1px solid rgba(103, 58, 183, 0.5);
    border-radius: 20px;
    padding: 0.2rem 0.8rem;
    font-size: 0.75rem;
    font-weight: 600;
    color: #b39ddb;
    margin: 0.2rem;
}

/* Scrollbar customizada */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: rgba(26, 20, 51, 0.5); }
::-webkit-scrollbar-thumb { background: rgba(103, 58, 183, 0.5); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: rgba(103, 58, 183, 0.8); }
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# IMPORTS INTERNOS (após set_page_config)
# ---------------------------------------------------------------------------
try:
    from core.agent import AgenteSecuritario, criar_agente, listar_modelos, MODELOS_DISPONIVEIS, Provedor
    from core.extractor import ProcessadorDocumento, processar_multiplos_pdfs
    from core.calculator import (
        calcular_diferenca_capital_segurado,
        calcular_invalidez_parcial_susep,
        calcular_prestamista,
        calcular_prescricao,
        listar_lesoes_susep,
        TABELA_SUSEP_INVALIDEZ,
    )
    MODULOS_OK = True
except ImportError as e:
    MODULOS_OK = False
    ERRO_IMPORT = str(e)

try:
    from docx import Document
    from docx.shared import Pt, Inches, RGBColor
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    HAS_DOCX = True
except ImportError:
    HAS_DOCX = False


# ---------------------------------------------------------------------------
# UTILITÁRIOS DE SESSÃO
# ---------------------------------------------------------------------------

def init_session():
    """Inicializa variáveis de sessão."""
    defaults = {
        "agente": None,
        "api_key_validada": False,
        "provedor_selecionado": "Anthropic Claude",
        "modelo_selecionado": "claude-3-5-sonnet-latest",
        "texto_documentos": "",
        "resumos_documentos": [],
        "dados_extraidos": {},
        "parecer_gerado": "",
        "peticao_gerada": "",
        "quesitos_gerados": "",
        "replica_gerada": "",
        "dados_caso": {},
        "ramo_selecionado": "Vida/AP",
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def obter_agente() -> Optional[AgenteSecuritario]:
    """Retorna o agente da sessão, se válido."""
    return st.session_state.get("agente")


def gerar_docx(texto: str, titulo: str = "Peça Jurídica") -> bytes:
    """Gera um arquivo .docx a partir do texto da peça."""
    if not HAS_DOCX:
        return texto.encode("utf-8")

    doc = Document()

    # Margens
    for section in doc.sections:
        section.top_margin = Inches(1.18)
        section.bottom_margin = Inches(1.18)
        section.left_margin = Inches(1.57)
        section.right_margin = Inches(1.18)

    # Título
    titulo_p = doc.add_heading(titulo, level=1)
    titulo_p.alignment = WD_ALIGN_PARAGRAPH.CENTER

    doc.add_paragraph()

    # Conteúdo
    for linha in texto.split("\n"):
        if linha.strip().startswith("=") and len(linha.strip()) > 10:
            continue  # pular linhas de separador
        p = doc.add_paragraph(linha)
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        run = p.runs[0] if p.runs else p.add_run()
        run.font.size = Pt(12)
        run.font.name = "Arial"

    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


def formatar_brl(valor: float) -> str:
    """Formata valor em R$ no padrão brasileiro."""
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


# ---------------------------------------------------------------------------
# SIDEBAR
# ---------------------------------------------------------------------------

def renderizar_sidebar():
    """Renderiza a barra lateral com configurações e upload de arquivos."""

    with st.sidebar:
        # Header do escritório
        st.markdown("""
        <div class="header-escritorio">
            <h1>⚖️ Agente Jurídico Securitário</h1>
            <p>Dra. Salviana Lima da Silva</p>
            <p><strong>OAB/SP 519.390</strong> | Osasco/SP</p>
        </div>
        """, unsafe_allow_html=True)

        # ── SELETOR DE PROVEDOR E MODELO ────────────────────────────────
        st.markdown("### 🤖 Provedor de IA")

        # Ícones e descrições dos provedores
        INFO_PROVEDORES = {
            "Anthropic Claude": {
                "icone": "🟠",
                "descricao": "Melhor para redação jurídica longa",
                "placeholder_key": "sk-ant-...",
                "env_key": "ANTHROPIC_API_KEY",
                "link": "console.anthropic.com",
            },
            "OpenAI": {
                "icone": "🟢",
                "descricao": "GPT-4o e modelos de raciocínio (o1/o3)",
                "placeholder_key": "sk-...",
                "env_key": "OPENAI_API_KEY",
                "link": "platform.openai.com",
            },
            "Google Gemini": {
                "icone": "🔵",
                "descricao": "Contexto longo, ideal para documentos extensos",
                "placeholder_key": "AIza...",
                "env_key": "GEMINI_API_KEY",
                "link": "aistudio.google.com",
            },
        }

        provedores_disponiveis = list(INFO_PROVEDORES.keys())
        provedor_idx = provedores_disponiveis.index(
            st.session_state.provedor_selecionado
        ) if st.session_state.provedor_selecionado in provedores_disponiveis else 0

        provedor_escolhido = st.selectbox(
            "Provedor",
            options=provedores_disponiveis,
            index=provedor_idx,
            format_func=lambda p: f"{INFO_PROVEDORES[p]['icone']} {p}",
            key="sel_provedor",
            help="Selecione o provedor de IA que deseja usar.",
        )

        # Resetar modelo se o provedor mudou
        if provedor_escolhido != st.session_state.provedor_selecionado:
            st.session_state.provedor_selecionado = provedor_escolhido
            st.session_state.api_key_validada = False
            st.session_state.agente = None
            primeiro_modelo = MODELOS_DISPONIVEIS[provedor_escolhido][0]["id"]
            st.session_state.modelo_selecionado = primeiro_modelo

        info = INFO_PROVEDORES[provedor_escolhido]
        st.caption(f"💡 {info['descricao']} · [Obter chave]({info['link']})")

        # ── SELETOR DE MODELO ───────────────────────────────────────────
        modelos_prov = MODELOS_DISPONIVEIS[provedor_escolhido]
        labels_modelo = [m["label"] for m in modelos_prov]
        ids_modelo    = [m["id"]    for m in modelos_prov]

        modelo_atual = st.session_state.modelo_selecionado
        modelo_idx = ids_modelo.index(modelo_atual) if modelo_atual in ids_modelo else 0

        modelo_label = st.selectbox(
            "Modelo",
            options=labels_modelo,
            index=modelo_idx,
            key="sel_modelo",
            help="Modelos marcados como 'recomendado' são a melhor escolha para peças jurídicas.",
        )
        modelo_escolhido = ids_modelo[labels_modelo.index(modelo_label)]
        st.session_state.modelo_selecionado = modelo_escolhido

        # Chip com o modelo ativo
        st.markdown(
            f'<span class="chip-ramo">⚙️ {modelo_escolhido}</span>',
            unsafe_allow_html=True,
        )

        # ── CHAVE API ───────────────────────────────────────────────────
        st.markdown("### 🔑 Chave de API")

        api_key_env = os.getenv(info["env_key"], "")
        api_key_input = st.text_input(
            f"Chave {provedor_escolhido}",
            value=api_key_env,
            type="password",
            placeholder=info["placeholder_key"],
            key="api_key_input",
            help=(
                f"Insira a chave de API do {provedor_escolhido}. "
                "Ela é usada apenas nesta sessão e não é salva em disco."
            ),
        )

        if st.button("🔗 Conectar", use_container_width=True):
            if not api_key_input or len(api_key_input.strip()) < 8:
                st.warning("Insira uma chave de API válida antes de conectar.")
            else:
                with st.spinner(f"Conectando ao {provedor_escolhido}…"):
                    try:
                        agente = criar_agente(
                            api_key=api_key_input.strip(),
                            modelo=modelo_escolhido,
                            provedor=provedor_escolhido,
                        )
                        ok, msg = agente.testar_conexao()
                        if ok:
                            st.session_state.agente = agente
                            st.session_state.api_key_validada = True
                            st.success(msg)
                        else:
                            st.session_state.api_key_validada = False
                            st.error(msg)
                    except Exception as e:
                        st.session_state.api_key_validada = False
                        st.error(f"Erro ao conectar: {e}")

        if st.session_state.api_key_validada:
            agente_atual = st.session_state.agente
            provedor_badge = agente_atual.provedor if agente_atual else ""
            modelo_badge   = agente_atual.modelo   if agente_atual else ""
            st.success(f"✅ Conectado · {provedor_badge} · {modelo_badge}")
        else:
            st.info("ℹ️ Selecione o provedor, o modelo e cole a chave API.")

        st.divider()

        # ── RAMO DO SEGURO ──────────────────────────────────────────────
        st.markdown("### 🏷️ Ramo do Seguro")

        ramos = [
            "Vida/AP",
            "Prestamista",
            "Habitacional (SFH/SFI)",
            "Auto",
            "Residencial/Empresarial",
            "Responsabilidade Civil",
            "DPVAT/SPVAT",
        ]

        ramo = st.selectbox(
            "Selecione o ramo:",
            options=ramos,
            index=ramos.index(st.session_state.ramo_selecionado),
            help="O ramo determina as súmulas e teses aplicáveis.",
        )
        st.session_state.ramo_selecionado = ramo

        # Chip informativo
        prazo_prescricional = "3 anos" if "DPVAT" in ramo else "1 ano"
        st.markdown(
            f'<span class="chip-ramo">⏱️ Prescrição: {prazo_prescricional}</span>',
            unsafe_allow_html=True
        )

        st.divider()

        # ── UPLOAD DE DOCUMENTOS ────────────────────────────────────────
        st.markdown("### 📄 Documentos do Caso")

        tipos_upload = {
            "Apólice / Certificado": "apolice",
            "Carta de Recusa / Negativa": "recusa",
            "Laudos / Documentos Médicos": "laudo",
            "Contrato de Empréstimo": "contrato",
            "Contestação da Seguradora": "contestacao",
            "Outros": "outros",
        }

        arquivos_carregados = []

        for label, tipo in tipos_upload.items():
            uploaded = st.file_uploader(
                label,
                type=["pdf"],
                key=f"upload_{tipo}",
                help=f"Envie o PDF do(a) {label.lower()}",
            )
            if uploaded:
                arquivos_carregados.append((uploaded.name, uploaded.read(), tipo))

        if arquivos_carregados and st.button("⚙️ Processar Documentos", use_container_width=True):
            with st.spinner(f"Processando {len(arquivos_carregados)} documento(s)..."):
                try:
                    texto_consolidado, resumos = processar_multiplos_pdfs(
                        [(nome, dados) for nome, dados, _ in arquivos_carregados]
                    )
                    st.session_state.texto_documentos = texto_consolidado
                    st.session_state.resumos_documentos = resumos
                    st.success(f"✅ {len(resumos)} documento(s) processados com sucesso!")

                    # Extrair dados automaticamente se agente disponível
                    if st.session_state.api_key_validada and st.session_state.agente:
                        with st.spinner("Extraindo dados com IA..."):
                            dados = st.session_state.agente.extrair_dados_documento(
                                texto_consolidado[:20000]
                            )
                            if "erro" not in dados:
                                st.session_state.dados_extraidos = dados
                                st.success("✅ Dados extraídos automaticamente!")
                except Exception as e:
                    st.error(f"Erro ao processar documentos: {str(e)}")

        # Exibir resumo dos documentos carregados
        if st.session_state.resumos_documentos:
            st.markdown("**Documentos carregados:**")
            for r in st.session_state.resumos_documentos:
                st.caption(
                    f"📄 {r['arquivo']} — {r.get('tipo', 'N/D')} ({r.get('tamanho_kb', 0)} KB)"
                )


# ---------------------------------------------------------------------------
# ABA 1: PARECER DE VIABILIDADE E PRESCRIÇÃO
# ---------------------------------------------------------------------------

def aba_parecer():
    st.markdown("## 📋 Parecer de Viabilidade & Prescrição")
    st.caption(
        "Análise completa do caso: regime legal aplicável, filtro de prescrição, "
        "refutação da negativa e score de viabilidade."
    )

    col_form, col_result = st.columns([1, 1], gap="large")

    with col_form:
        st.markdown("### 👤 Dados do Caso")

        with st.form("form_parecer"):
            nome_segurado = st.text_input("Nome do Segurado/Beneficiário", placeholder="Ex: João da Silva")
            nome_seguradora = st.text_input("Seguradora", placeholder="Ex: Bradesco Seguros")

            col1, col2 = st.columns(2)
            with col1:
                data_sinistro = st.date_input("Data do Sinistro", value=None, max_value=date.today())
            with col2:
                data_negativa = st.date_input("Data da Negativa/Ciência", value=None, max_value=date.today())

            col3, col4 = st.columns(2)
            with col3:
                capital_segurado = st.number_input(
                    "Capital Segurado (R$)", min_value=0.0, value=0.0, format="%.2f"
                )
            with col4:
                data_contrato = st.date_input("Data do Contrato", value=None)

            motivo_negativa = st.text_area(
                "Motivo da Negativa (conforme carta)",
                placeholder="Descreva o motivo alegado pela seguradora...",
                height=100,
            )

            col5, col6 = st.columns(2)
            with col5:
                data_protocolo_adm = st.date_input("Protocolo Administrativo (se houver)", value=None)
            with col6:
                data_encerramento_adm = st.date_input("Encerramento Administrativo", value=None)

            informacoes_adicionais = st.text_area(
                "Informações Adicionais",
                placeholder="Outros fatos relevantes, histórico médico, etc.",
                height=80,
            )

            btn_parecer = st.form_submit_button("⚖️ Gerar Parecer", use_container_width=True)

        # Pré-visualização do alerta de prescrição (calculado localmente, sem IA)
        if data_negativa:
            st.markdown("#### ⏱️ Pré-visualização da Prescrição")
            prazo = 3 if "DPVAT" in st.session_state.ramo_selecionado else 1
            resultado_prescricao = calcular_prescricao(
                data_negativa_ou_ciencia=data_negativa,
                prazo_anos=prazo,
                data_protocolo_adm=data_protocolo_adm if data_protocolo_adm else None,
                data_encerramento_adm=data_encerramento_adm if data_encerramento_adm else None,
            )

            cor = resultado_prescricao["cor"]
            css_class = {
                "green": "prescricao-ok",
                "orange": "prescricao-urgente",
                "red": "prescricao-expirada",
            }.get(cor, "prescricao-ok")

            st.markdown(
                f'<div class="{css_class}"><strong>{resultado_prescricao["alerta"]}</strong></div>',
                unsafe_allow_html=True,
            )

            col_m1, col_m2, col_m3 = st.columns(3)
            col_m1.metric("Prazo (anos)", str(prazo))
            col_m2.metric(
                "Vencimento",
                resultado_prescricao["vencimento_com_suspensao"].strftime("%d/%m/%Y"),
            )
            col_m3.metric(
                "Dias Restantes",
                str(resultado_prescricao["dias_restantes"]),
                delta=None,
            )

            if resultado_prescricao["dias_suspensao"] > 0:
                st.info(
                    f"✅ Suspensão computada: {resultado_prescricao['dias_suspensao']} dias "
                    f"(Súmula 229, STJ)"
                )

    with col_result:
        st.markdown("### 📜 Resultado")

        # Processamento do formulário
        if btn_parecer:
            if not st.session_state.api_key_validada:
                st.warning("⚠️ Configure e conecte a chave API primeiro (sidebar).")
            elif not nome_segurado or not nome_seguradora:
                st.warning("⚠️ Preencha pelo menos o nome do segurado e da seguradora.")
            else:
                dados_caso = {
                    "nome_segurado": nome_segurado,
                    "nome_seguradora": nome_seguradora,
                    "ramo": st.session_state.ramo_selecionado,
                    "data_sinistro": str(data_sinistro) if data_sinistro else None,
                    "data_negativa": str(data_negativa) if data_negativa else None,
                    "data_contrato": str(data_contrato) if data_contrato else None,
                    "capital_segurado": capital_segurado,
                    "motivo_negativa": motivo_negativa,
                    "informacoes_adicionais": informacoes_adicionais,
                    "dados_extraidos_documentos": st.session_state.dados_extraidos,
                }
                st.session_state.dados_caso = dados_caso

                with st.spinner("🤖 Gerando Parecer de Viabilidade..."):
                    try:
                        placeholder = st.empty()
                        texto_completo = ""

                        stream = st.session_state.agente.gerar_parecer(
                            dados_caso=dados_caso,
                            texto_documentos=st.session_state.texto_documentos,
                            data_negativa=data_negativa,
                            ramo=st.session_state.ramo_selecionado,
                            streaming=True,
                        )

                        for chunk in stream:
                            texto_completo += chunk
                            placeholder.markdown(
                                f'<div class="output-juridico">{texto_completo}</div>',
                                unsafe_allow_html=True,
                            )

                        st.session_state.parecer_gerado = texto_completo
                        st.success("✅ Parecer gerado com sucesso!")
                    except Exception as e:
                        st.error(f"Erro ao gerar parecer: {str(e)}")

        # Exibir parecer já gerado
        elif st.session_state.parecer_gerado:
            st.markdown(
                f'<div class="output-juridico">{st.session_state.parecer_gerado}</div>',
                unsafe_allow_html=True,
            )

        # Botões de ação
        if st.session_state.parecer_gerado:
            col_d1, col_d2 = st.columns(2)
            with col_d1:
                st.download_button(
                    "⬇️ Download .txt",
                    data=st.session_state.parecer_gerado.encode("utf-8"),
                    file_name=f"parecer_{date.today().strftime('%Y%m%d')}.txt",
                    mime="text/plain",
                    use_container_width=True,
                )
            with col_d2:
                if HAS_DOCX:
                    docx_bytes = gerar_docx(
                        st.session_state.parecer_gerado,
                        titulo="Parecer de Viabilidade Securitária"
                    )
                    st.download_button(
                        "⬇️ Download .docx",
                        data=docx_bytes,
                        file_name=f"parecer_{date.today().strftime('%Y%m%d')}.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        use_container_width=True,
                    )
                else:
                    st.caption("python-docx não instalado")

        else:
            st.info(
                "Preencha os dados do caso e clique em **⚖️ Gerar Parecer** para "
                "iniciar a análise jurídica."
            )


# ---------------------------------------------------------------------------
# ABA 2: PETIÇÃO INICIAL
# ---------------------------------------------------------------------------

def aba_peticao():
    st.markdown("## 📝 Minuta de Petição Inicial")
    st.caption(
        "Geração da peça completa: qualificação, CDC, tese de mérito refutando a negativa, "
        "tutela de urgência e pedidos liquidados."
    )

    col_form, col_result = st.columns([1, 1], gap="large")

    with col_form:
        st.markdown("### ⚙️ Configuração da Petição")

        with st.form("form_peticao"):
            foro = st.text_input(
                "Foro/Comarca", value="Osasco/SP", placeholder="Ex: Osasco/SP"
            )
            vara = st.selectbox(
                "Vara/Justiça",
                options=[
                    "Vara Cível",
                    "Vara do Consumidor",
                    "Juizado Especial Cível",
                    "Vara de Fazenda Pública",
                    "Outra",
                ],
            )
            incluir_tutela = st.checkbox(
                "Incluir Tutela de Urgência",
                value=False,
                help="Marque se há risco de perecimento ou necessidade vital urgente.",
            )
            incluir_danos_morais = st.checkbox(
                "Incluir Pedido de Danos Morais",
                value=True,
                help="Aplicável quando a recusa é injustificada ou abusiva (Súmula 402, STJ).",
            )
            valor_danos_morais = st.number_input(
                "Valor dos Danos Morais (R$)",
                min_value=0.0,
                value=10000.0,
                format="%.2f",
                disabled=not incluir_danos_morais,
            )
            observacoes_peticao = st.text_area(
                "Instruções Adicionais para a Petição",
                placeholder="Alguma particularidade do caso, argumento específico a enfatizar...",
                height=80,
            )

            btn_peticao = st.form_submit_button(
                "📝 Gerar Petição Inicial", use_container_width=True
            )

        # Verificar se há parecer como base
        if not st.session_state.parecer_gerado:
            st.warning(
                "⚠️ Recomendado: Gere o **Parecer de Viabilidade** (Aba 1) antes da petição. "
                "O agente usará o parecer como base jurídica."
            )

    with col_result:
        st.markdown("### 📜 Petição Inicial")

        if btn_peticao:
            if not st.session_state.api_key_validada:
                st.warning("⚠️ Configure e conecte a chave API primeiro (sidebar).")
            elif not st.session_state.dados_caso:
                st.warning("⚠️ Preencha os dados do caso na Aba 1 primeiro.")
            else:
                dados_atualizados = {
                    **st.session_state.dados_caso,
                    "incluir_tutela_urgencia": incluir_tutela,
                    "incluir_danos_morais": incluir_danos_morais,
                    "valor_danos_morais": valor_danos_morais if incluir_danos_morais else 0,
                    "observacoes_peticao": observacoes_peticao,
                    "foro": foro,
                    "vara": vara,
                }

                with st.spinner("🤖 Redigindo Petição Inicial..."):
                    try:
                        placeholder = st.empty()
                        texto_completo = ""

                        stream = st.session_state.agente.gerar_peticao_inicial(
                            dados_caso=dados_atualizados,
                            parecer_referencia=st.session_state.parecer_gerado,
                            foro=foro,
                            vara=vara,
                            ramo=st.session_state.ramo_selecionado,
                            streaming=True,
                        )

                        for chunk in stream:
                            texto_completo += chunk
                            placeholder.markdown(
                                f'<div class="output-juridico">{texto_completo}</div>',
                                unsafe_allow_html=True,
                            )

                        st.session_state.peticao_gerada = texto_completo
                        st.success("✅ Petição gerada com sucesso!")
                    except Exception as e:
                        st.error(f"Erro ao gerar petição: {str(e)}")

        elif st.session_state.peticao_gerada:
            st.markdown(
                f'<div class="output-juridico">{st.session_state.peticao_gerada}</div>',
                unsafe_allow_html=True,
            )

        if st.session_state.peticao_gerada:
            col_d1, col_d2 = st.columns(2)
            with col_d1:
                st.download_button(
                    "⬇️ Download .txt",
                    data=st.session_state.peticao_gerada.encode("utf-8"),
                    file_name=f"peticao_inicial_{date.today().strftime('%Y%m%d')}.txt",
                    mime="text/plain",
                    use_container_width=True,
                )
            with col_d2:
                if HAS_DOCX:
                    docx_bytes = gerar_docx(
                        st.session_state.peticao_gerada,
                        titulo="Petição Inicial — Ação de Cobrança de Seguro"
                    )
                    st.download_button(
                        "⬇️ Download .docx",
                        data=docx_bytes,
                        file_name=f"peticao_inicial_{date.today().strftime('%Y%m%d')}.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        use_container_width=True,
                    )
        else:
            st.info(
                "Configure as opções e clique em **📝 Gerar Petição Inicial** para redigir a peça."
            )


# ---------------------------------------------------------------------------
# ABA 3: QUESITOS PERICIAIS
# ---------------------------------------------------------------------------

def aba_quesitos():
    st.markdown("## 🔬 Quesitos Periciais & Engenharia de Prova")
    st.caption(
        "Formulação de quesitos estratégicos fechados para perícia médica ou de engenharia."
    )

    col_form, col_result = st.columns([1, 1], gap="large")

    with col_form:
        st.markdown("### ⚙️ Tipo de Perícia")

        with st.form("form_quesitos"):
            tipo_pericia = st.selectbox(
                "Tipo de Perícia",
                options=["Médica", "Engenharia/Avaliação de Danos", "Contábil/Financeira", "Automotiva"],
                help="Define o conjunto de quesitos a formular.",
            )
            especialidade_medica = st.text_input(
                "Especialidade Médica (se aplicável)",
                placeholder="Ex: Ortopedia, Cardiologia, Psiquiatria...",
            )
            atividade_profissional = st.text_input(
                "Atividade Profissional Habitual do Segurado",
                placeholder="Ex: Pedreiro, Motorista, Bancário...",
                help="Crucial para quesitos de invalidez laboral.",
            )
            patologia_alegada = st.text_input(
                "Patologia / Lesão Alegada",
                placeholder="Ex: Hérnia de disco L4-L5, IAM, Fratura de fêmur...",
            )
            observacoes_quesitos = st.text_area(
                "Particularidades do Caso para os Quesitos",
                placeholder="Ex: Seguradora alegou preexistência de HAS. Requerer datação da CID.",
                height=80,
            )

            btn_quesitos = st.form_submit_button(
                "🔬 Gerar Quesitos", use_container_width=True
            )

    with col_result:
        st.markdown("### 📜 Quesitos Periciais")

        if btn_quesitos:
            if not st.session_state.api_key_validada:
                st.warning("⚠️ Configure e conecte a chave API primeiro (sidebar).")
            else:
                dados_quesitos = {
                    **st.session_state.dados_caso,
                    "tipo_pericia": tipo_pericia,
                    "especialidade_medica": especialidade_medica,
                    "atividade_profissional": atividade_profissional,
                    "patologia_alegada": patologia_alegada,
                    "observacoes_quesitos": observacoes_quesitos,
                }

                with st.spinner("🤖 Formulando Quesitos Periciais..."):
                    try:
                        placeholder = st.empty()
                        texto_completo = ""

                        stream = st.session_state.agente.gerar_quesitos(
                            dados_caso=dados_quesitos,
                            tipo_pericia=tipo_pericia.lower(),
                            ramo=st.session_state.ramo_selecionado,
                            streaming=True,
                        )

                        for chunk in stream:
                            texto_completo += chunk
                            placeholder.markdown(
                                f'<div class="output-juridico">{texto_completo}</div>',
                                unsafe_allow_html=True,
                            )

                        st.session_state.quesitos_gerados = texto_completo
                        st.success("✅ Quesitos gerados!")
                    except Exception as e:
                        st.error(f"Erro ao gerar quesitos: {str(e)}")

        elif st.session_state.quesitos_gerados:
            st.markdown(
                f'<div class="output-juridico">{st.session_state.quesitos_gerados}</div>',
                unsafe_allow_html=True,
            )

        if st.session_state.quesitos_gerados:
            st.download_button(
                "⬇️ Download Quesitos (.txt)",
                data=st.session_state.quesitos_gerados.encode("utf-8"),
                file_name=f"quesitos_periciais_{date.today().strftime('%Y%m%d')}.txt",
                mime="text/plain",
                use_container_width=True,
            )
        else:
            st.info(
                "Preencha as informações e clique em **🔬 Gerar Quesitos** para "
                "formular os quesitos estratégicos."
            )


# ---------------------------------------------------------------------------
# ABA 4: CALCULADORA DE LIQUIDAÇÃO
# ---------------------------------------------------------------------------

def aba_calculadora():
    st.markdown("## 💰 Calculadora de Diferença / Liquidação")
    st.caption(
        "Calcule a diferença devida corrigida com base nos valores da apólice. "
        "Fundamento: Súmula 632, STJ — correção desde o evento."
    )

    tipo_calculo = st.radio(
        "Tipo de Cálculo",
        options=["Capital Segurado (Diferença)", "Invalidez Parcial (Tabela SUSEP)", "Prestamista"],
        horizontal=True,
    )

    st.divider()

    if tipo_calculo == "Capital Segurado (Diferença)":
        _calc_diferenca()

    elif tipo_calculo == "Invalidez Parcial (Tabela SUSEP)":
        _calc_invalidez_susep()

    else:  # Prestamista
        _calc_prestamista()

    # Tabela SUSEP de referência
    with st.expander("📊 Tabela SUSEP de Invalidez Permanente Parcial (Referência)"):
        import pandas as pd
        df_susep = pd.DataFrame(listar_lesoes_susep())
        df_susep.columns = ["Código", "Descrição da Lesão", "% sobre Capital"]
        df_susep["% sobre Capital"] = df_susep["% sobre Capital"].apply(lambda x: f"{x:.1f}%")
        st.dataframe(df_susep, use_container_width=True, hide_index=True)
        st.caption(
            "Fonte: Tabela SUSEP de Invalidez Permanente Parcial. "
            "[CONFERIR: resolução CNSP vigente na data do sinistro]"
        )


def _calc_diferenca():
    col1, col2 = st.columns(2)
    with col1:
        capital = st.number_input("Capital Segurado (R$)", min_value=0.0, value=100000.0, format="%.2f")
        pago_adm = st.number_input("Valor Pago Administrativamente (R$)", min_value=0.0, value=0.0, format="%.2f")
    with col2:
        data_evento = st.date_input("Data do Evento (Sinistro)", value=date(2023, 1, 1))
        data_calculo = st.date_input("Data Base do Cálculo", value=date.today())
        taxa_correcao = st.slider("Taxa de Correção Anual (%)", 2.0, 12.0, 5.0, 0.5)
        usar_juros = st.checkbox("Incluir Juros de Mora (1% a.m.)", value=True)

    if st.button("🔢 Calcular", use_container_width=True):
        resultado = calcular_diferenca_capital_segurado(
            capital_segurado=capital,
            valor_pago_administrativo=pago_adm,
            data_evento=data_evento,
            data_calculo=data_calculo,
            usar_juros_mora=usar_juros,
            taxa_correcao_anual=taxa_correcao / 100,
        )
        _exibir_resultado_calculo(resultado)


def _calc_invalidez_susep():
    lesoes = listar_lesoes_susep()
    opcoes = {f"{l['descricao']} ({l['percentual']}%)": l["codigo"] for l in lesoes}

    col1, col2 = st.columns(2)
    with col1:
        capital = st.number_input("Capital Segurado (R$)", min_value=0.0, value=100000.0, format="%.2f")
        lesao_selecionada = st.selectbox("Lesão (Tabela SUSEP)", list(opcoes.keys()))
        pago_adm = st.number_input("Valor Pago Administrativamente (R$)", min_value=0.0, value=0.0, format="%.2f")
    with col2:
        data_evento = st.date_input("Data do Evento (Sinistro)", value=date(2023, 1, 1))
        data_calculo = st.date_input("Data Base do Cálculo", value=date.today())

    codigo_lesao = opcoes[lesao_selecionada]
    percentual = next(l["percentual"] for l in lesoes if l["codigo"] == codigo_lesao)

    st.info(
        f"📊 Capital segurado: {formatar_brl(capital)} × {percentual:.1f}% = "
        f"**{formatar_brl(capital * percentual / 100)}** (valor devido pela SUSEP)"
    )

    if st.button("🔢 Calcular Invalidez SUSEP", use_container_width=True):
        resultado = calcular_invalidez_parcial_susep(
            capital_segurado=capital,
            codigo_lesao=codigo_lesao,
            valor_pago_administrativo=pago_adm,
            data_evento=data_evento,
            data_calculo=data_calculo,
        )
        _exibir_resultado_calculo(resultado)


def _calc_prestamista():
    col1, col2 = st.columns(2)
    with col1:
        saldo_devedor = st.number_input(
            "Saldo Devedor na Data do Sinistro (R$)", min_value=0.0, value=50000.0, format="%.2f"
        )
        valor_parcela = st.number_input(
            "Valor da Parcela Mensal (R$)", min_value=0.0, value=1200.0, format="%.2f"
        )
        n_parcelas = st.number_input(
            "Nº de Parcelas Indevidas (pós-sinistro)", min_value=0, value=12, step=1
        )
    with col2:
        data_sinistro = st.date_input("Data do Sinistro", value=date(2023, 1, 1))
        data_calculo = st.date_input("Data Base do Cálculo", value=date.today())
        taxa_correcao = st.slider("Taxa de Correção Anual (%)", 2.0, 12.0, 5.0, 0.5)

    if st.button("🔢 Calcular Prestamista", use_container_width=True):
        resultado = calcular_prestamista(
            saldo_devedor_data_sinistro=saldo_devedor,
            valor_parcela_mensal=valor_parcela,
            numero_parcelas_indevidas=n_parcelas,
            data_sinistro=data_sinistro,
            data_calculo=data_calculo,
            taxa_correcao_anual=taxa_correcao / 100,
        )

        st.markdown("### 📊 Resultado")
        col_m1, col_m2, col_m3 = st.columns(3)
        col_m1.metric("Indeniz. Principal", formatar_brl(float(resultado.indenizacao_principal)))
        col_m2.metric("Repetição de Indébito", formatar_brl(float(resultado.repeticao_indebito)))
        col_m3.metric("TOTAL DEVIDO", formatar_brl(float(resultado.total_devido)))

        with st.expander("📋 Detalhamento completo"):
            st.text(resultado.resumo())

        st.download_button(
            "⬇️ Exportar Cálculo (.txt)",
            data=resultado.resumo().encode("utf-8"),
            file_name=f"calc_prestamista_{date.today().strftime('%Y%m%d')}.txt",
            mime="text/plain",
        )


def _exibir_resultado_calculo(resultado):
    """Exibe o resultado de um cálculo de diferença de capital segurado."""
    st.markdown("### 📊 Resultado do Cálculo")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Capital Segurado", formatar_brl(float(resultado.capital_segurado)))
    col2.metric("Pago Adm.", formatar_brl(float(resultado.valor_pago_administrativo)))
    col3.metric("Diferença Bruta", formatar_brl(float(resultado.diferenca_bruta)))
    col4.metric("TOTAL DEVIDO", formatar_brl(float(resultado.valor_total_devido)))

    with st.expander("📋 Detalhamento completo"):
        st.text(resultado.resumo())

    if resultado.observacoes:
        for obs in resultado.observacoes:
            if "[CONFERIR" in obs:
                st.warning(f"⚠️ {obs}")
            else:
                st.info(f"ℹ️ {obs}")

    st.download_button(
        "⬇️ Exportar Cálculo (.txt)",
        data=resultado.resumo().encode("utf-8"),
        file_name=f"calculo_liquidacao_{date.today().strftime('%Y%m%d')}.txt",
        mime="text/plain",
    )


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

def main():
    init_session()

    if not MODULOS_OK:
        st.error(
            f"❌ Erro ao importar módulos internos: {ERRO_IMPORT}\n\n"
            "Execute: `pip install -r requirements.txt`"
        )
        st.stop()

    renderizar_sidebar()

    # Abas principais
    aba1, aba2, aba3, aba4 = st.tabs([
        "⚖️ Parecer & Prescrição",
        "📝 Petição Inicial",
        "🔬 Quesitos Periciais",
        "💰 Calculadora",
    ])

    with aba1:
        aba_parecer()

    with aba2:
        aba_peticao()

    with aba3:
        aba_quesitos()

    with aba4:
        aba_calculadora()

    # Footer
    st.divider()
    st.markdown(
        "<div style='text-align:center;color:#616161;font-size:0.75rem;padding:0.5rem;'>"
        "⚖️ Agente Jurídico Securitário — Dra. Salviana Lima da Silva | OAB/SP 519.390 | Osasco/SP<br>"
        "⚠️ Esta ferramenta é auxiliar e não substitui o juízo profissional da advogada titular. "
        "Sempre revise os outputs antes do protocolo."
        "</div>",
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
