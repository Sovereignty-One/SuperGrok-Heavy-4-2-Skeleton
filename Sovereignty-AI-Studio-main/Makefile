.PHONY: install test lint build deploy clean

install:
	pip install -r requirements.txt
	pip install -r backend/requirements.txt

test:
	PYTHONPATH=./backend pytest

lint:
	PYTHONPATH=./backend flake8 src/ --max-line-length=100

build:
	docker-compose build

deploy:
	docker-compose up -d

clean:
	docker-compose down
	rm -rf __pycache__ */__pycache__