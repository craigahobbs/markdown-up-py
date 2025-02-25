# Licensed under the MIT License
# https://github.com/craigahobbs/markdown-up-py/blob/main/LICENSE


# Download python-build
define WGET
ifeq '$$(wildcard $(notdir $(1)))' ''
$$(info Downloading $(notdir $(1)))
_WGET := $$(shell $(call WGET_CMD, $(1)))
endif
endef
WGET_CMD = if which wget; then wget -q -c $(1); else curl -f -Os $(1); fi
$(eval $(call WGET, https://craigahobbs.github.io/python-build/Makefile.base))
$(eval $(call WGET, https://craigahobbs.github.io/python-build/pylintrc))


# Include python-build
include Makefile.base


# Development dependencies
TESTS_REQUIRE := bare-script


# Disable pylint docstring warnings
PYLINT_ARGS := $(PYLINT_ARGS) --disable=missing-class-docstring --disable=missing-function-docstring --disable=missing-module-docstring


help:
	@echo "            [test-app]"


clean:
	rm -rf Makefile.base pylintrc


.PHONY: test-app
commit: test-app
test-app: $(DEFAULT_VENV_BUILD)
	$(DEFAULT_VENV_BIN)/bare -s src/markdown_up/static/*.bare src/markdown_up/static/test/*.bare
	$(DEFAULT_VENV_BIN)/bare -m src/markdown_up/static/test/runTests.bare$(if $(DEBUG), -d)$(if $(TEST), -v vTest "'$(TEST)'")


.PHONY: run
run: $(DEFAULT_VENV_BUILD)
	$(DEFAULT_VENV_BIN)/markdown-up$(if $(ARGS), $(ARGS))


.PHONY: markdown-up
markdown-up:
	cd src/markdown_up/static && $(call WGET_CMD, https://craigahobbs.github.io/markdown-up/markdown-up.tar.gz)
