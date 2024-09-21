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

clean:
	rm -rf Makefile.base pylintrc

PYLINT_ARGS := $(PYLINT_ARGS) --disable=missing-class-docstring --disable=missing-function-docstring --disable=missing-module-docstring
