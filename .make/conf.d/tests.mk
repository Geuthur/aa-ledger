# Make targets for tests

# Coverage
.PHONY: coverage
coverage: check-python-venv
	@echo "Running tests and creating a coverage report …"
	@rm -rf htmlcov
	@coverage run ../auth/manage.py \
		test \
		$(package) \
		--keepdb \
		--failfast; \
	coverage html; \
	coverage report -m

# Build test
.PHONY: build_test
build_test: check-python-venv
	@echo "Building the package …"
	@rm -rf dist
	@python3 -m build

# Help message
.PHONY: help
help::
	@echo "  $(TEXT_UNDERLINE)Tests:$(TEXT_UNDERLINE_END)"
	@echo "    build_test                  Build the package"
	@echo "    coverage                    Run tests and create a coverage report"
	@echo ""
