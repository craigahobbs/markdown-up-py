# Licensed under the MIT License
# https://github.com/craigahobbs/markdown-up-py/blob/main/LICENSE


# Download python-build
PYTHON_BUILD_DIR ?= ../python-build
define WGET
ifeq '$$(wildcard $(notdir $(1)))' ''
$$(info Downloading $(notdir $(1)))
$$(shell [ -f $(PYTHON_BUILD_DIR)/$(notdir $(1)) ] && cp $(PYTHON_BUILD_DIR)/$(notdir $(1)) . || $(call WGET_CMD, $(1)))
endif
endef
WGET_CMD = if command -v wget >/dev/null 2>&1; then wget -q -c $(1); else curl -f -Os $(1); fi
$(eval $(call WGET, https://craigahobbs.github.io/python-build/Makefile.base))
$(eval $(call WGET, https://craigahobbs.github.io/python-build/pylintrc))


# Specify the documentation directory
GHPAGES_SRC := build/doc/


# Include python-build
include Makefile.base


# Disable pylint docstring warnings
PYLINT_ARGS := $(PYLINT_ARGS) --disable=missing-class-docstring --disable=missing-function-docstring --disable=missing-module-docstring


help:
	@echo "            [test-app]"


clean:
	rm -rf Makefile.base pylintrc


doc: $(DEFAULT_VENV_BUILD)
	mkdir -p build/doc
	cp -R static/* build/doc
	cp README.md build/doc
	$(DEFAULT_VENV_PYTHON) -c 'import json; from markdown_up.main import CONFIG_TYPES; print(json.dumps(CONFIG_TYPES, indent=4))' > build/doc/config.json
	$(DEFAULT_VENV_BIN)/baredoc src/markdown_up/api.py -o build/doc/api.json


.PHONY: test-app
commit: test-app
test-app: $(DEFAULT_VENV_BUILD)
	$(DEFAULT_VENV_BIN)/bare -s src/markdown_up/static/*.bare src/markdown_up/static/test/*.bare
	$(DEFAULT_VENV_BIN)/bare -d -m -v vUnittestReport true src/markdown_up/static/test/runTests.bare$(if $(TEST), -v vUnittestTest "'$(TEST)'")


.PHONY: run
run: $(DEFAULT_VENV_BUILD)
	$(DEFAULT_VENV_BIN)/markdown-up$(if $(ARGS), $(ARGS))
