# Makefile fragment for React-related tasks

# React Static Directory and Supervisor Configuration
REACT__STATIC_DIR ?= $(GENERAL__PACKAGE)/static/$(GENERAL__PACKAGE)
REACT__SUPERVISOR_SERVICE ?= auth:

# React Fast Build (Local tsc & vite build without supervisor/collectstatic)
.PHONY: react-build
react-build:
	@echo "Building React frontend"
	@cd $(REACT__EXECUTABLE) && npm run build
	@echo "React build completed"

# React Dev Server
.PHONY: react-dev
react-dev:
	@echo "Starting React development server"
	@cd $(REACT__EXECUTABLE) && npm run dev

# React Clean Build Artifacts
.PHONY: react-clean
react-clean:
	@echo "Cleaning React build artifacts"
	@rm -rf $(REACT__EXECUTABLE)/build
	@echo "React clean completed"

# React Copy Assets to Django static directory
.PHONY: react-copy-assets
react-copy-assets:
	@echo "Cleaning old assets in $(REACT__STATIC_DIR)"
	@rm -rf $(REACT__STATIC_DIR)/react
	@rm -f $(REACT__STATIC_DIR)/manifest.json
	@echo "Copying new assets to $(REACT__STATIC_DIR)"
	@mkdir -p $(REACT__STATIC_DIR)
	@cp $(REACT__EXECUTABLE)/build/static/.vite/manifest.json $(REACT__STATIC_DIR)/manifest.json
	@cp -r $(REACT__EXECUTABLE)/build/static/react $(REACT__STATIC_DIR)/react
	@echo "Assets copied successfully"

# React Copy Translations to Django static directory
.PHONY: react-copy-translations
react-copy-translations:
	@echo "Cleaning old translations in $(REACT__STATIC_DIR)/i18n"
	@rm -rf $(REACT__STATIC_DIR)/i18n
	@echo "Copying translations to $(REACT__STATIC_DIR)/i18n"
	@mkdir -p $(REACT__STATIC_DIR)
	@cp -r $(REACT__EXECUTABLE)/i18n $(REACT__STATIC_DIR)/i18n
	@echo "Translations copied successfully"

# React Translations Scanner
.PHONY: react-translations
react-translations:
	@echo "Scanning and building React translations"
	@cd $(REACT__EXECUTABLE) && npm run buildTranslations
	@echo "React translations completed"

# React Test Build (build, copy assets & translations, collectstatic, restart supervisor)
.PHONY: react-test-build
react-test-build: check-python-venv check-myauth-path react-build react-copy-assets react-copy-translations collectstatic
	@echo "React test build completed successfully"

# React Release Build (build, scan translations, copy assets & translations, collectstatic)
.PHONY: react-release
react-release: check-python-venv check-myauth-path react-build react-translations react-copy-assets react-copy-translations collectstatic
	@echo "React release build completed successfully"

# Export OpenAPI Schema from Django Ninja
.PHONY: react-export-openapi
react-export-openapi: check-python-venv check-myauth-path
	@echo "Exporting OpenAPI schema from Django Ninja"
	@$(PYTHON__EXECUTABLE) $(DJANGO__MYAUTH_PATH)/manage.py shell -c \
		"import json; from pathlib import Path; from django.utils.module_loading import import_string; from ninja.responses import NinjaJSONEncoder; api = import_string('$(GENERAL__PACKAGE).api.api'); Path('$(REACT__EXECUTABLE)/src/openapi.json').write_text(json.dumps(api.get_openapi_schema(), cls=NinjaJSONEncoder, indent=2), encoding='utf-8')"
	@echo "OpenAPI schema exported to $(REACT__EXECUTABLE)/src/openapi.json"

# React OpenAPI Migration (exports schema from Django Ninja and generates TypeScript types)
.PHONY: react-openapi
react-openapi: check-python-venv check-myauth-path react-export-openapi
	@echo "Starting React OpenAPI TypeScript generation"
	@cd $(REACT__EXECUTABLE) && npx openapi-typescript ./src/openapi.json -o src/Api/OpenApi.ts
	@echo "React OpenAPI migration completed"

# React ESLint with auto-fix
.PHONY: react-eslint
react-eslint:
	@echo "Running React ESLint check with auto-fix"
	@cd $(REACT__EXECUTABLE) && npx eslint . --fix
	@echo "React ESLint check completed"

# React Lint (read-only verification)
.PHONY: react-lint
react-lint:
	@echo "Running React lint verification"
	@cd $(REACT__EXECUTABLE) && npm run lint
	@echo "React lint verification completed"

# React Automated Tests
.PHONY: react-test
react-test:
	@echo "Running React tests"
	@cd $(REACT__EXECUTABLE) && npm test
	@echo "React tests completed"

# Help Message
.PHONY: help
help::
	@echo "  $(TEXT_UNDERLINE)React:$(TEXT_UNDERLINE_END)"
	@echo "    react-build         Run fast React build (tsc + vite)"
	@echo "    react-dev           Start React development server"
	@echo "    react-test-build    Run full React test build (build, copy, collectstatic, restart)"
	@echo "    react-release       Run full React release build (build, i18n, copy, collectstatic)"
	@echo "    react-copy-assets   Copy built Vite assets to Django static directory"
	@echo "    react-copy-translations Copy i18n translations to Django static directory"
	@echo "    react-openapi       Export schema and generate OpenAPI TypeScript types"
	@echo "    react-translations  Scan and extract i18n translations"
	@echo "    react-eslint        Run React ESLint check with auto-fix"
	@echo "    react-lint          Run React ESLint lint verification (read-only)"
	@echo "    react-test          Run React unit tests with Vitest"
	@echo "    react-clean         Clean React build folder"
	@echo ""
