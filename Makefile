install:
	pip install -r requirements.txt

run:
	python agent.py

ui:
	streamlit run app.py

admin:
	streamlit run admin_panel.py

api:
	uvicorn backend.main:app --reload

test:
	pytest -q
