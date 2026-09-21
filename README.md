# ⚖️ Agente Jurídico Securitário

**Escritório Dra. Salviana Lima da Silva — OAB/SP 519.390 | Osasco/SP**

Sistema de IA especializado na defesa de segurados, beneficiários e vítimas contra seguradoras, estipulantes, bancos e corretoras.

---

## 🚀 Como Usar

### Opção 1 — Clique Duplo (Windows)
Execute `run_app.bat` — ele cria o ambiente, instala dependências e abre o navegador automaticamente.

### Opção 2 — Terminal
```powershell
# Criar e ativar ambiente virtual
python -m venv .venv
.\.venv\Scripts\activate

# Instalar dependências
pip install -r requirements.txt

# Iniciar o sistema
streamlit run app.py
```

---

## ⚙️ Configuração

1. Copie `.env.example` para `.env`
2. Insira sua chave API da Anthropic em `ANTHROPIC_API_KEY`
3. Ou configure a chave diretamente na sidebar do sistema

---

## 📁 Estrutura do Projeto

```
securitario_app/
├── app.py                          # Interface Streamlit principal
├── requirements.txt                # Dependências Python
├── run_app.bat                     # Launcher Windows (clique duplo)
├── .env.example                    # Exemplo de configuração
├── core/
│   ├── agent.py                    # Orquestração Claude 3.5 Sonnet
│   ├── calculator.py               # Cálculos de liquidação (SUSEP, prescrição)
│   ├── extractor.py                # Parsing de PDFs
│   └── prompts.py                  # System prompt + tabela de refutações
├── knowledge/
│   ├── sumulas_stj.json            # 11 súmulas securitárias validadas
│   └── teses_ramos/
│       └── teses_principais.json   # Teses por ramo de seguro
└── templates/
    └── modelos_pecas/              # Minutas-base (futuras expansões)
```

---

## 🔑 Funcionalidades

| Aba | Função |
|-----|--------|
| **⚖️ Parecer & Prescrição** | Análise de viabilidade com alerta de prescrição, score e regime legal |
| **📝 Petição Inicial** | Geração da peça completa com CDC, súmulas e pedidos liquidados |
| **🔬 Quesitos Periciais** | Quesitos fechados estratégicos para perícia médica ou engenharia |
| **💰 Calculadora** | Diferença de capital, tabela SUSEP e liquidação prestamista |

---

## ⚖️ Súmulas STJ no Catálogo

| Nº | Tema |
|----|------|
| 609 | Doença preexistente sem exame médico |
| 620 | Embriaguez em seguro de vida |
| 610 | Suicídio (2 anos de carência) |
| 616 | Juros de mora desde o evento |
| 402 | Danos morais por recusa abusiva |
| 465 | Transferência de veículo |
| 632 | Correção monetária |
| 229 | Suspensão de prescrição por protocolo |
| 278 | Início da prescrição por invalidez |
| 101 | Prescrição anual — seguro grupo |
| 405 | Prescrição trienal — DPVAT |

---

## ⚠️ Aviso Legal

Esta ferramenta é auxiliar e não substitui o juízo profissional da Dra. Salviana Lima da Silva. Todos os outputs devem ser revisados antes do protocolo judicial.
