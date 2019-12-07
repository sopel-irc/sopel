.PHONY: quality test coverage_html coverage_report travis clean_doc build_doc install-hooks uninstall-hooks

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

clean_docs:
	$(MAKE) -C docs clean

build_docs:
	$(MAKE) -C docs html

docs: build_docs

cleandoc: clean_docs build_docs

install-hooks:
	@./contrib/githooks/install-hooks.sh

uninstall-hooks:
	@./contrib/githooks/uninstall-hooks.sh
