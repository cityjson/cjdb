.PHONY: docs,test

docs:
	sphinx-build -b html docs/config docs

test-cj2pgsql:
	pytest cj2pgsql -v

