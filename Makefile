.PHONY: qa
qa: lint test coverages

.PHONY: lint lint-style lint-type
lint: lint-style lint-type

lint-style:
	flake8 sopel/ test/

lint-type:
	mypy --check-untyped-defs --disallow-incomplete-defs sopel

.PHONY: test test_norecord test_novcr vcr_rerecord
test:
	coverage run -m pytest -v

test_norecord:
	# error if VCR recording for a web request is missing (useful on CI)
	coverage run -m pytest -v --vcr-record=none

test_novcr:
	# disable VCR completely; useful to check if recordings are outdated
	coverage run -m pytest -v --disable-vcr

vcr_rerecord:
	# clear VCR cassettes and run tests to record fresh ones
	rm -rf ./test/vcr/*
	coverage run -m pytest -v --vcr-record=all

.PHONY: coverage_report coverage_html coverages
coverage_report:
	coverage report

coverage_html:
	coverage html

coverages: coverage_report coverage_html

.PHONY: clean_docs build_docs docs cleandoc
clean_docs:
	$(MAKE) -C docs clean

build_docs:
	$(MAKE) -C docs html

docs: build_docs

cleandoc: clean_docs build_docs

.PHONY: install-hooks uninstall-hooks
install-hooks:
	@./contrib/githooks/install-hooks.sh

uninstall-hooks:
	@./contrib/githooks/uninstall-hooks.sh
