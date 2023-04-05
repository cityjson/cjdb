.PHONY: doc,test

doc:
	sphinx-build -b html docs/config docs

test-cjdb:
	pytest cjdb -v

