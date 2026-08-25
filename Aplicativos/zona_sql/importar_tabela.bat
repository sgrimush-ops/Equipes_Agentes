@echo off
chcp 65001 >nul
cls
cd /d "%~dp0"
echo =======================================================
echo        IMPORTADOR UNIVERSAL DE TABELAS - ZONA SQL      
echo =======================================================
echo.

if "%~1"=="" (
    python importar_tabela_txt.py
) else (
    python importar_tabela_txt.py "%~1"
)

echo.
pause
