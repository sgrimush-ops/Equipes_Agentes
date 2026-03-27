@echo off
:: Muda o diretório atual para a pasta onde este arquivo .bat está localizado
cd /d "%~dp0"

:: Inicia o menu Python (usando pythonw para não segurar a janela preta do terminal aberta)
start "" pythonw app_menu.py
