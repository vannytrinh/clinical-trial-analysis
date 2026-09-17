.PHONY: setup

setup:
	pip install --upgrade pip
	pip install -r requirements.txt

pipeline:
	python load_data.py