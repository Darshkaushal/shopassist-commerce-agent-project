@echo off
echo Starting ShopAssist Commerce API...
python -m uvicorn backend.main:app --reload
pause
