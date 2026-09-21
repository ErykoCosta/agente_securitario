"""
core/agent.py
Escritório Dra. Salviana Lima da Silva — OAB/SP 519.390

Orquestrador multi-provedor de IA:
  • Anthropic Claude  (claude-3-5-sonnet-latest, claude-3-opus, claude-3-5-haiku…)
  • OpenAI            (gpt-4o, gpt-4o-mini, o3-mini, o1…)
  • Google Gemini     (gemini-2.5-pro, gemini-2.0-flash, gemini-1.5-pro…)

Interface unificada para todos os 4 outputs jurídicos securitários.
"""

from __future__ import annotations

import json
from datetime import date
from enum import Enum
from typing import Generator, Optional

from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from core.prompts import (
    get_system_prompt,
    PROMPT_PARECER,
    PROMPT_PETICAO,
    PROMPT_QUESITOS,
    PROMPT_REPLICA,
    PROMPT_EXTRACAO,
    FEW_SHOT_PRESCRICAO,
    FEW_SHOT_REFUTACAO_609,
)

# ---------------------------------------------------------------------------
# CATÁLOGO DE PROVEDORES E MODELOS
# ---------------------------------------------------------------------------

class Provedor(str, Enum):
    ANTHROPIC = "Anthropic Claude"
    OPENAI    = "OpenAI"
    GEMINI    = "Google Gemini"


# Modelos disponíveis por provedor — exibidos na UI exatamente nessa ordem
MODELOS_DISPONIVEIS: dict[str, list[dict]] = {
    Provedor.ANTHROPIC: [
        {"id": "claude-3-5-sonnet-latest", "label": "Claude 3.5 Sonnet (recomendado)"},
        {"id": "claude-3-5-haiku-latest",  "label": "Claude 3.5 Haiku (rápido)"},
        {"id": "claude-opus-4-5",          "label": "Claude Opus 4.5 (mais capaz)"},
        {"id": "claude-3-opus-latest",     "label": "Claude 3 Opus"},
    ],
    Provedor.OPENAI: [
        {"id": "gpt-4o",       "label": "GPT-4o (recomendado)"},
        {"id": "gpt-4o-mini",  "label": "GPT-4o Mini (rápido)"},
        {"id": "o3-mini",      "label": "o3-mini (raciocínio)"},
        {"id": "o1",           "label": "o1 (raciocínio avançado)"},
        {"id": "gpt-4-turbo",  "label": "GPT-4 Turbo"},
    ],
    Provedor.GEMINI: [
        {"id": "gemini-2.5-pro-preview-06-05", "label": "Gemini 2.5 Pro (recomendado)"},
        {"id": "gemini-2.0-flash",             "label": "Gemini 2.0 Flash (rápido)"},
        {"id": "gemini-2.0-flash-lite",        "label": "Gemini 2.0 Flash Lite"},
        {"id": "gemini-1.5-pro-latest",        "label": "Gemini 1.5 Pro"},
        {"id": "gemini-1.5-flash-latest",      "label": "Gemini 1.5 Flash"},
    ],
}

# Modelos que usam "reasoning" na OpenAI (não aceitam temperature)
OPENAI_REASONING_MODELS = {"o1", "o1-mini", "o3", "o3-mini", "o1-preview"}

# Configurações de tokens
MAX_TOKENS_PADRAO  = 8000
MAX_TOKENS_PETICAO = 12000
TEMPERATURA_PADRAO  = 0.1
TEMPERATURA_CRIATIVA = 0.3


# ---------------------------------------------------------------------------
# ADAPTADORES POR PROVEDOR
# ---------------------------------------------------------------------------

class _AnthropicAdapter:
    """Adaptador para a API Anthropic (Claude)."""

    def __init__(self, api_key: str, modelo: str):
        import anthropic as _anthropic
        self._anthropic = _anthropic
        self.cliente = _anthropic.Anthropic(api_key=api_key)
        self.modelo = modelo

    def chamar(self, system: str, mensagens: list[dict],
               max_tokens: int, temperatura: float) -> str:
        resp = self.cliente.messages.create(
            model=self.modelo,
            max_tokens=max_tokens,
            temperature=temperatura,
            system=system,
            messages=mensagens,
        )
        return resp.content[0].text

    def stream(self, system: str, mensagens: list[dict],
               max_tokens: int, temperatura: float) -> Generator[str, None, None]:
        with self.cliente.messages.stream(
            model=self.modelo,
            max_tokens=max_tokens,
            temperature=temperatura,
            system=system,
            messages=mensagens,
        ) as s:
            yield from s.text_stream

    def testar(self) -> tuple[bool, str]:
        try:
            self.cliente.messages.create(
                model=self.modelo,
                max_tokens=10,
                messages=[{"role": "user", "content": "OK"}],
            )
            return True, f"✅ Anthropic — {self.modelo}"
        except self._anthropic.AuthenticationError:
            return False, "❌ Chave Anthropic inválida ou expirada."
        except self._anthropic.APIConnectionError:
            return False, "❌ Sem conexão com a API da Anthropic."
        except Exception as e:
            return False, f"❌ Erro Anthropic: {e}"


class _OpenAIAdapter:
    """Adaptador para a API OpenAI (GPT-4o, o1, o3…)."""

    def __init__(self, api_key: str, modelo: str):
        from openai import OpenAI as _OpenAI, AuthenticationError, APIConnectionError
        self._AuthError = AuthenticationError
        self._ConnError = APIConnectionError
        self.cliente = _OpenAI(api_key=api_key)
        self.modelo = modelo
        self._is_reasoning = modelo in OPENAI_REASONING_MODELS

    def _build_messages(self, system: str, mensagens: list[dict]) -> list[dict]:
        """Converte formato Anthropic para formato OpenAI."""
        msgs = [{"role": "system", "content": system}]
        msgs.extend(mensagens)
        return msgs

    def chamar(self, system: str, mensagens: list[dict],
               max_tokens: int, temperatura: float) -> str:
        kwargs: dict = dict(
            model=self.modelo,
            messages=self._build_messages(system, mensagens),
        )
        if self._is_reasoning:
            kwargs["max_completion_tokens"] = max_tokens
        else:
            kwargs["max_tokens"] = max_tokens
            kwargs["temperature"] = temperatura

        resp = self.cliente.chat.completions.create(**kwargs)
        return resp.choices[0].message.content or ""

    def stream(self, system: str, mensagens: list[dict],
               max_tokens: int, temperatura: float) -> Generator[str, None, None]:
        kwargs: dict = dict(
            model=self.modelo,
            messages=self._build_messages(system, mensagens),
            stream=True,
        )
        if self._is_reasoning:
            kwargs["max_completion_tokens"] = max_tokens
        else:
            kwargs["max_tokens"] = max_tokens
            kwargs["temperature"] = temperatura

        for chunk in self.cliente.chat.completions.create(**kwargs):
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta

    def testar(self) -> tuple[bool, str]:
        try:
            self.cliente.chat.completions.create(
                model=self.modelo,
                max_tokens=10,
                messages=[{"role": "user", "content": "OK"}],
            )
            return True, f"✅ OpenAI — {self.modelo}"
        except self._AuthError:
            return False, "❌ Chave OpenAI inválida ou expirada."
        except self._ConnError:
            return False, "❌ Sem conexão com a API da OpenAI."
        except Exception as e:
            return False, f"❌ Erro OpenAI: {e}"


class _GeminiAdapter:
    """Adaptador para a API Google Gemini (SDK google-genai >= 1.0)."""

    def __init__(self, api_key: str, modelo: str):
        from google import genai
        from google.genai import types as genai_types
        self._genai = genai
        self._types = genai_types
        self.cliente = genai.Client(api_key=api_key)
        self.modelo_id = modelo

    def _build_contents(self, mensagens: list[dict]):
        """Converte mensagens para o formato Content do google-genai."""
        conteudos = []
        for m in mensagens:
            role = "user" if m["role"] == "user" else "model"
            conteudos.append(
                self._types.Content(
                    role=role,
                    parts=[self._types.Part(text=m["content"])],
                )
            )
        return conteudos

    def _config(self, system: str, max_tokens: int, temperatura: float):
        return self._types.GenerateContentConfig(
            system_instruction=system,
            max_output_tokens=max_tokens,
            temperature=temperatura,
        )

    def chamar(self, system: str, mensagens: list[dict],
               max_tokens: int, temperatura: float) -> str:
        conteudos = self._build_contents(mensagens)
        resp = self.cliente.models.generate_content(
            model=self.modelo_id,
            contents=conteudos,
            config=self._config(system, max_tokens, temperatura),
        )
        return resp.text or ""

    def stream(self, system: str, mensagens: list[dict],
               max_tokens: int, temperatura: float) -> Generator[str, None, None]:
        conteudos = self._build_contents(mensagens)
        for chunk in self.cliente.models.generate_content_stream(
            model=self.modelo_id,
            contents=conteudos,
            config=self._config(system, max_tokens, temperatura),
        ):
            if chunk.text:
                yield chunk.text

    def testar(self) -> tuple[bool, str]:
        try:
            resp = self.cliente.models.generate_content(
                model=self.modelo_id,
                contents="OK",
                config=self._types.GenerateContentConfig(max_output_tokens=10),
            )
            _ = resp.text
            return True, f"✅ Google Gemini — {self.modelo_id}"
        except Exception as e:
            msg = str(e)
            if "API_KEY" in msg.upper() or "api key" in msg.lower() or "403" in msg:
                return False, "❌ Chave Gemini inválida ou sem permissão."
            return False, f"❌ Erro Gemini: {msg}"


# ---------------------------------------------------------------------------
# AGENTE UNIFICADO
# ---------------------------------------------------------------------------

class AgenteSecuritario:
    """
    Agente securitário com suporte a múltiplos provedores de IA.
    Interface idêntica independente do provedor selecionado.
    """

    def __init__(self, api_key: str, modelo: str, provedor: str):
        self.provedor = provedor
        self.modelo = modelo
        self._historico: list[dict] = []
        self._adaptador = self._criar_adaptador(api_key, modelo, provedor)

    def _criar_adaptador(self, api_key: str, modelo: str, provedor: str):
        if provedor == Provedor.ANTHROPIC:
            return _AnthropicAdapter(api_key, modelo)
        elif provedor == Provedor.OPENAI:
            return _OpenAIAdapter(api_key, modelo)
        elif provedor == Provedor.GEMINI:
            return _GeminiAdapter(api_key, modelo)
        else:
            raise ValueError(f"Provedor desconhecido: {provedor}")

    def _limpar_historico(self):
        self._historico = []

    def _construir_few_shot(self, ramo: str) -> str:
        return "\n\n".join([
            "=== EXEMPLOS DE REFERÊNCIA (uso interno) ===",
            FEW_SHOT_PRESCRICAO,
            FEW_SHOT_REFUTACAO_609,
            "=== FIM DOS EXEMPLOS ===",
        ])

    def _chamar(self, mensagens: list[dict], system: str,
                max_tokens: int = MAX_TOKENS_PADRAO,
                temperatura: float = TEMPERATURA_PADRAO) -> str:
        return self._adaptador.chamar(system, mensagens, max_tokens, temperatura)

    def _stream(self, mensagens: list[dict], system: str,
                max_tokens: int = MAX_TOKENS_PADRAO,
                temperatura: float = TEMPERATURA_PADRAO) -> Generator[str, None, None]:
        yield from self._adaptador.stream(system, mensagens, max_tokens, temperatura)

    def testar_conexao(self) -> tuple[bool, str]:
        return self._adaptador.testar()

    # -----------------------------------------------------------------------
    # OUTPUT A: PARECER DE VIABILIDADE
    # -----------------------------------------------------------------------
    def gerar_parecer(
        self,
        dados_caso: dict,
        texto_documentos: str,
        data_negativa: Optional[date] = None,
        ramo: str = "Vida/AP",
        streaming: bool = False,
    ) -> str | Generator:
        self._limpar_historico()
        system = get_system_prompt(ramo)
        few_shot = self._construir_few_shot(ramo)
        prompt = PROMPT_PARECER.format(
            dados_caso=json.dumps(dados_caso, ensure_ascii=False, indent=2),
            texto_documentos=texto_documentos[:30000],
            data_negativa=str(data_negativa) if data_negativa else "Não informada",
            data_atual=str(date.today()),
            ramo=ramo,
        )
        mensagens = [{"role": "user", "content": f"{few_shot}\n\n{prompt}"}]
        if streaming:
            return self._stream(mensagens, system, MAX_TOKENS_PADRAO)
        resp = self._chamar(mensagens, system, MAX_TOKENS_PADRAO)
        self._historico = mensagens + [{"role": "assistant", "content": resp}]
        return resp

    # -----------------------------------------------------------------------
    # OUTPUT B: PETIÇÃO INICIAL
    # -----------------------------------------------------------------------
    def gerar_peticao_inicial(
        self,
        dados_caso: dict,
        parecer_referencia: str,
        foro: str = "Osasco/SP",
        vara: str = "Vara Cível",
        ramo: str = "Vida/AP",
        streaming: bool = False,
    ) -> str | Generator:
        system = get_system_prompt(ramo)
        prompt = PROMPT_PETICAO.format(
            dados_caso=json.dumps(dados_caso, ensure_ascii=False, indent=2),
            parecer_referencia=parecer_referencia[:5000],
            foro=foro,
            vara=vara,
        )
        mensagens = self._historico + [{"role": "user", "content": prompt}]
        if not mensagens:
            mensagens = [{"role": "user", "content": prompt}]
        if streaming:
            return self._stream(mensagens, system, MAX_TOKENS_PETICAO)
        resp = self._chamar(mensagens, system, MAX_TOKENS_PETICAO)
        self._historico = mensagens + [{"role": "assistant", "content": resp}]
        return resp

    # -----------------------------------------------------------------------
    # OUTPUT C: QUESITOS PERICIAIS
    # -----------------------------------------------------------------------
    def gerar_quesitos(
        self,
        dados_caso: dict,
        tipo_pericia: str = "médica",
        ramo: str = "Vida/AP",
        streaming: bool = False,
    ) -> str | Generator:
        system = get_system_prompt(ramo)
        prompt = PROMPT_QUESITOS.format(
            dados_caso=json.dumps(dados_caso, ensure_ascii=False, indent=2),
            tipo_pericia=tipo_pericia,
            ramo=ramo,
        )
        mensagens = [{"role": "user", "content": prompt}]
        if streaming:
            return self._stream(mensagens, system, MAX_TOKENS_PADRAO, TEMPERATURA_CRIATIVA)
        return self._chamar(mensagens, system, MAX_TOKENS_PADRAO, TEMPERATURA_CRIATIVA)

    # -----------------------------------------------------------------------
    # OUTPUT D: RÉPLICA
    # -----------------------------------------------------------------------
    def gerar_replica(
        self,
        texto_contestacao: str,
        sumario_inicial: str,
        ramo: str = "Vida/AP",
        streaming: bool = False,
    ) -> str | Generator:
        system = get_system_prompt(ramo)
        prompt = PROMPT_REPLICA.format(
            texto_contestacao=texto_contestacao[:20000],
            sumario_inicial=sumario_inicial[:5000],
        )
        mensagens = [{"role": "user", "content": prompt}]
        if streaming:
            return self._stream(mensagens, system, MAX_TOKENS_PADRAO, TEMPERATURA_CRIATIVA)
        return self._chamar(mensagens, system, MAX_TOKENS_PADRAO, TEMPERATURA_CRIATIVA)

    # -----------------------------------------------------------------------
    # EXTRAÇÃO ESTRUTURADA
    # -----------------------------------------------------------------------
    def extrair_dados_documento(self, texto_documento: str) -> dict:
        prompt = PROMPT_EXTRACAO.format(texto_documento=texto_documento[:15000])
        system = (
            "Você é um extrator de dados jurídicos. Retorne APENAS JSON válido, "
            "sem markdown, sem texto adicional. Nunca invente valores — use null "
            "para campos não encontrados."
        )
        mensagens = [{"role": "user", "content": prompt}]
        try:
            # temperatura 0 para extração determinística
            resp = self._chamar(mensagens, system, max_tokens=1500, temperatura=0.0)
            resp_limpa = resp.strip()
            if resp_limpa.startswith("```"):
                linhas = resp_limpa.split("\n")
                resp_limpa = "\n".join(linhas[1:-1])
            return json.loads(resp_limpa)
        except Exception as e:
            return {"erro": str(e)}


# ---------------------------------------------------------------------------
# FACTORY
# ---------------------------------------------------------------------------

def criar_agente(api_key: str, modelo: str, provedor: str) -> AgenteSecuritario:
    """Cria e retorna uma instância configurada do AgenteSecuritario."""
    return AgenteSecuritario(api_key=api_key, modelo=modelo, provedor=provedor)


def listar_modelos(provedor: str) -> list[dict]:
    """Retorna a lista de modelos disponíveis para o provedor."""
    return MODELOS_DISPONIVEIS.get(provedor, [])
