@echo off
title FastBite - docker compose
REM Levanta todo FastBite (RabbitMQ, usuarios, menu, pedidos, notificaciones y gateway)
cd /d "%~dp0docker"
echo Levantando FastBite con Docker... (Ctrl+C para detener)
docker compose up --build
pause
