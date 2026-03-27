@echo off
chcp 65001 > nul
cd /d "%~dp0"

echo ========================================
echo Inicializando o projeto...
echo ========================================

IF NOT EXIST ".venv\" (
    echo [INFO] Ambiente virtual não encontrado. Criando...
    python -m venv .venv
    
    echo [INFO] Ativando ambiente virtual...
    call .venv\Scripts\activate.bat
    
    IF EXIST "requirements.txt" (
        echo [INFO] Instalando dependências...
        pip install -r requirements.txt
    )
) ELSE (
    echo [INFO] Ativando ambiente virtual existente...
    call .venv\Scripts\activate.bat
)

echo [INFO] Executando main.py...
python main.py

echo.
echo [INFO] Script finalizado.
pause
