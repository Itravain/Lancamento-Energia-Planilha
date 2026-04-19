PYTHON ?= python

.PHONY: run test test-unit test-integration test-real

run:
	$(PYTHON) main.py

test:
	$(PYTHON) -m pytest

test-unit:
	$(PYTHON) -m pytest -m unit

test-integration:
	$(PYTHON) -m pytest -m integration

test-real:
	RUN_APSYSTEM_INTEGRATION=true $(PYTHON) -m pytest -m integration_real
