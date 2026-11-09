# Makefile fragment for running tests and generating coverage reports

# Coverage
.PHONY: coverage
coverage: check-python-venv check-myauth-path
	@echo "Running tests and creating a coverage report…"
	@coverage run $(DJANGO__MYAUTH_PATH)/manage.py \
		test \
		$(GENERAL__PACKAGE) \
		--keepdb \
		--failfast; \
	tests_status=$$?; \
	coverage html; \
	coverage xml; \
	coverage report -m; \
	report_status=$$?; \
	if [ $$tests_status -ne 0 ]; then exit $$tests_status; fi; \
	exit $$report_status

# Build test
.PHONY: build-test
build-test: check-python-venv
	@echo "Building the package…"
	@$(PYTHON__EXECUTABLE) -m build

# Tox tests
.PHONY: tox-tests
tox-tests: check-python-venv
	@echo "Running tests with tox…"
	@export USE_MYSQL=False; \
	tox -v -e allianceauth-latest; \

# Tox tests against the Alliance Auth development (pre-release) version
.PHONY: tox-tests-development
tox-tests-development: check-python-venv
	@echo "Running tests with tox against the Alliance Auth development version…"
	@export USE_MYSQL=False; \
	tox -v -e allianceauth-development; \

# Help message
.PHONY: help
help::
	@echo "  $(TEXT_UNDERLINE)Tests:$(TEXT_UNDERLINE_END)"
	@echo "    build-test                  Build the package"
	@echo "    coverage                    Run tests and create a coverage report"
	@echo "    tox-tests                   Run tests with tox"
	@echo "    tox-tests-development       Run tests with tox against the Alliance Auth development version"
	@echo ""
