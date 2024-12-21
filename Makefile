# Makefile for Python project

# Variables
VENV_DIR = venv
PYTHON = $(VENV_DIR)/bin/python
PIP = $(VENV_DIR)/bin/pip

# Targets
.PHONY: all venv install clean

all: venv install

venv:
	python3 -m venv $(VENV_DIR)

install: venv
	$(PIP) install -r requirements.txt

clean:
	rm -rf $(VENV_DIR)

dcr:
	docker build -t bda .
	docker run --name bda -dit bda
