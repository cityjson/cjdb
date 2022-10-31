.PHONY: doc,test

doc:
	sphinx-build -b html docs/config docs

test-cj2pgsql:
	pytest cj2pgsql -v

