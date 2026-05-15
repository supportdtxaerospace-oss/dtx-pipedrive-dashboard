@echo off
cd /d "C:\Projetos\7. Project - Pipedrive - Sandro & Comercial"
echo [%date% %time%] Iniciando sync... >> sync_log.txt
python sync.py >> sync_log.txt 2>&1
echo [%date% %time%] Sync finalizado. >> sync_log.txt
echo. >> sync_log.txt
