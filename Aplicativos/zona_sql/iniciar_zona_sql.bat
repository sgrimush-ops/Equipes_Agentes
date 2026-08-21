@echo off
title Zona SQL - Simulador e Mentor Consinco (Oracle ERP)
cd /d "%~dp0"

echo =======================================================
echo    ZONA SQL - SIMULADOR E MENTOR CONSINCO (ORACLE)
echo =======================================================
echo.

if not exist "database\banco_simulador_consinco.db" (
    echo [1/2] Gerando banco de dados do simulador com dados reais...
    python database\seed_data.py
    echo.
)

echo [2/2] Abrindo interface no navegador e iniciando servidor...
start http://127.0.0.1:8550
python server.py

pause
