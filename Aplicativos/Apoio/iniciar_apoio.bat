@echo off
title Painel de Apoio - Inicializador
cd /d "%~dp0"
echo Iniciando Painel de Apoio...
python app_apoio.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Ocorreu um erro ao executar o aplicativo.
    pause
)
