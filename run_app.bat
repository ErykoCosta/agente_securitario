@echo off
chcp 65001 > nul
title Agente Juridico Securitario - Dra. Salviana Lima

echo.
echo  ===============================================================
echo   Agente Juridico Securitario
echo   Escritorio Dra. Salviana Lima da Silva - OAB/SP 519.390
echo  ===============================================================
echo.

:: Verificar se Python esta instalado
python --version > nul 2>&1
if errorlevel 1 (
    echo [ERRO] Python nao encontrado. Instale o Python 3.10+ em https://www.python.org/
    pause
    exit /b 1
)

:: Definir pasta do projeto
set PROJETO_DIR=%~dp0
cd /d "%PROJETO_DIR%"

:: Criar/verificar ambiente virtual
if not exist ".venv\Scripts\activate.bat" (
    echo [INFO] Criando ambiente virtual Python...
    python -m venv .venv
    if errorlevel 1 (
        echo [ERRO] Falha ao criar ambiente virtual.
        pause
        exit /b 1
    )
    echo [OK] Ambiente virtual criado.
)

:: Ativar ambiente virtual
call .venv\Scripts\activate.bat
echo [OK] Ambiente virtual ativado.

:: Instalar/atualizar dependencias
echo [INFO] Verificando dependencias (pode demorar na primeira execucao)...
pip install -q -r requirements.txt
if errorlevel 1 (
    echo [ERRO] Falha ao instalar dependencias.
    pause
    exit /b 1
)
echo [OK] Dependencias verificadas.

:: Copiar .env.example para .env se nao existir
if not exist ".env" (
    if exist ".env.example" (
        copy ".env.example" ".env" > nul
        echo [AVISO] Arquivo .env criado a partir do .env.example.
        echo [AVISO] Configure sua ANTHROPIC_API_KEY no arquivo .env
        echo.
    )
)

:: Iniciar aplicacao Streamlit
echo.
echo [INFO] Iniciando o Agente Juridico Securitario...
echo [INFO] O navegador abrira automaticamente em http://localhost:8501
echo [INFO] Para encerrar, pressione CTRL+C nesta janela.
echo.

streamlit run app.py --server.port 8501 --server.headless false --browser.gatherUsageStats false --theme.base dark --theme.primaryColor "#673ab7" --theme.backgroundColor "#0f0f1a" --theme.secondaryBackgroundColor "#1a1a2e" --theme.textColor "#e8eaf6"

if errorlevel 1 (
    echo.
    echo [ERRO] A aplicacao encerrou com erro.
    pause
)
