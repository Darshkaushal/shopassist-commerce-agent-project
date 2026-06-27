@echo off
echo Starting ShopAssist Commerce Admin Backend Panel...
set SHOPASSIST_API_URL=http://127.0.0.1:8000
set SHOPASSIST_ADMIN_KEY=shopassist-admin-2026
python -m streamlit run admin_panel.py
pause
