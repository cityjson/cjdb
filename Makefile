.PHONY: docs

docs:
	sphinx-build -b html docs/config docs/content
