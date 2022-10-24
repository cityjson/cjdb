.PHONY: docs,test

docs:
	sphinx-build -b html docs/config docs/content

test-cj2pgsql:
	pytest cj2pgsql -v

