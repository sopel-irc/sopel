.PHONY: quality test coverage_html coverage_report travis clean_doc build_doc

quality:
	./checkstyle.sh

test:
	coverage run -m py.test -v .

coverage_report:
	coverage report

coverage_html:
	coverage html

coverages: coverage_report coverage_html

qa: quality test coverages

travis: quality test coverage_report

clean_doc:
	$(MAKE) -C docs clean

build_doc:
	$(MAKE) -C docs html

doc: clean_doc build_doc
