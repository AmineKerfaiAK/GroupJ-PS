#!/bin/bash
cd "$(dirname "$0")"
python3 -m pip install -q -r requirements.txt --break-system-packages 2>/dev/null || python3 -m pip install -q -r requirements.txt
[ -d instances/generated ] || python3 generateur/generateur.py --suite -o instances/generated
python3 site/app.py
