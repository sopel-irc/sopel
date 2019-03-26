.PHONY: quality test coverage clean_doc build_doc

quality:
	./checkstyle.sh

test:
	coverage run -m py.test -v .

coverage:
	coverage report
	coverage html

qa: quality test coverage

clean_doc:
	$(MAKE) -C docs clean

build_doc:
	$(MAKE) -C docs html

doc: clean_doc build_doc
