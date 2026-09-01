@echo off
cd /d "%~dp0"
title GPU Hunter Pro - Monitor de Precos RTX 5000
echo ========================================================
echo   Iniciando GPU Hunter Pro ^& Servidor Web...
echo   Lojas: KaBuM!, Pichau e TerabyteShop
echo   Placas: RTX 5070 e RTX 5070 Ti
echo   O navegador sera aberto automaticamente!
echo ========================================================
echo.
python server.py
pause

