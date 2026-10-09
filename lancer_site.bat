@echo off
cd /d "%~dp0"
python -m pip install -q -r requirements.txt
if not exist instances\generated python generateur\generateur.py --suite -o instances\generated
python site\app.py
pause
