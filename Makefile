.PHONY: quality test test_norecord test_novcr vcr_rerecord qa clean_docs build_docs docs cleandoc install-hooks uninstall-hooks

quality:
	./checkstyle.sh

test:
	coverage run -m py.test -v .

test_norecord:
	# error if VCR recording for a web request is missing (useful on CI)
	coverage run -m py.test -v . --vcr-record=none

test_novcr:
	# disable VCR completely; useful to check if recordings are outdated
	coverage run -m py.test -v . --disable-vcr

vcr_rerecord:
	# clear VCR cassettes and run tests to record fresh ones
	rm -rf ./test/vcr/*
	coverage run -m py.test -v . --vcr-record=all

qa: quality test

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
