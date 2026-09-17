.PHONY: setup

setup:
	pip install --upgrade pip
	pip install -r requirements.txt

pipeline:
	python load_data.py
	python pipeline.py

dashboard:
	streamlit run app.py --server.port=8501 --server.address=0.0.0.0