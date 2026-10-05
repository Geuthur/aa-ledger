# Makefile fragment for EVE Online ESI tasks

ESI__META_URL := https://esi.evetech.net/meta

# Fetch compatibility dates from ESI API and allow user to select one
.PHONY: get-compatibility-dates
get-compatibility-dates: check-python-venv check-myauth-path
	@echo "Fetching compatibility dates for ESI API…"; \
	response=$$(curl -s "$(ESI__META_URL)/compatibility-dates"); \
	dates=$$(echo "$$response" | grep -o '[0-9]\{4\}-[0-9]\{2\}-[0-9]\{2\}'); \
	if [ -z "$$dates" ]; then \
		echo ""; \
		echo "$(TEXT_COLOR_RED)$(TEXT_BOLD)ERROR:$(TEXT_RESET) Failed to fetch compatibility dates or invalid response"; \
		echo ""; \
		exit 1; \
	fi; \
	echo ""; \
	echo "Available ESI compatibility dates:"; \
	echo "=================================================="; \
	counter=1; \
	while IFS= read -r date; do \
		formatted_date=$$(date -d "$$date" "+%B %d, %Y" 2>/dev/null || echo "$$date"); \
		printf "%2d. %s (%s)\n" "$$counter" "$$date" "$$formatted_date"; \
		counter=$$((counter + 1)); \
	done <<< "$$dates"; \
	echo ""; \
	read -p "Select a date (1-$$((counter-1))) or press Enter to use the latest date: " choice; \
	if [ -z "$$choice" ]; then \
		latest_date=$$(echo "$$dates" | head -n 1); \
		echo "Using latest date: $$latest_date"; \
		echo "$$latest_date" > .esi-compatibility-date; \
	else \
		if ! [[ "$$choice" =~ ^[0-9]+$$ ]] || [ "$$choice" -lt 1 ] || [ "$$choice" -gt $$((counter-1)) ]; then \
			echo ""; \
			echo "$(TEXT_COLOR_RED)Invalid selection. Please run again.$(TEXT_RESET)"; \
			echo ""; \
			exit 1; \
		fi; \
		selected_date=$$(echo "$$dates" | sed -n "$${choice}p"); \
		echo ""; \
		echo "$(TEXT_BOLD)Selected:$(TEXT_BOLD_END) $$selected_date"; \
		echo "$$selected_date" > .esi-compatibility-date; \
		echo ""; \
	fi

# Download ESI OpenAPI specification for the selected compatibility date
.PHONY: generate-esi-openapi
generate-esi-openapi: check-python-venv check-myauth-path get-compatibility-dates
	@DATE=$$(cat .esi-compatibility-date 2>/dev/null); \
	if [ -z "$$DATE" ]; then \
		echo "$(TEXT_COLOR_RED)Error: No compatibility date specified in .esi-compatibility-date$(TEXT_RESET)"; \
		exit 1; \
	fi; \
	echo "Downloading OpenAPI specification for $$DATE…"; \
	curl -s "$(ESI__META_URL)/openapi.json?compatibility_date=$$DATE" -o "$(GENERAL__PACKAGE)/openapi_$$DATE.json"; \
	if [ ! -s "$(GENERAL__PACKAGE)/openapi_$$DATE.json" ]; then \
		echo "$(TEXT_COLOR_RED)Error: Downloaded OpenAPI specification is empty or failed$(TEXT_RESET)"; \
		exit 1; \
	fi; \
	echo "Saved OpenAPI specification to $(TEXT_COLOR_GREEN)$(GENERAL__PACKAGE)/openapi_$$DATE.json$(TEXT_RESET)"; \
	find $(GENERAL__PACKAGE) -maxdepth 1 -name "openapi_*.json" ! -name "openapi_$$DATE.json" -delete

# Update the compatibility date in the package __init__.py and download OpenAPI spec
.PHONY: update-compatibility-date
update-compatibility-date: generate-esi-openapi check-python-venv check-myauth-path
	@DATE=$$(cat .esi-compatibility-date 2>/dev/null); \
	if [ -z "$$DATE" ]; then \
		echo "$(TEXT_COLOR_RED)Error: No compatibility date found in .esi-compatibility-date$(TEXT_RESET)"; \
		exit 1; \
	fi; \
	if [ -f "$(GENERAL__PACKAGE)/__init__.py" ]; then \
		sed -i -E "s/__esi_compatibility_date__ = \"[0-9]{4}-[0-9]{2}-[0-9]{2}\"/__esi_compatibility_date__ = \"$$DATE\"/" $(GENERAL__PACKAGE)/__init__.py; \
		echo "Updated __esi_compatibility_date__ in $(TEXT_COLOR_GREEN)$(GENERAL__PACKAGE)/__init__.py$(TEXT_RESET) to $(TEXT_COLOR_GREEN)$$DATE$(TEXT_RESET)"; \
	fi; \
	rm -f .esi-compatibility-date; \
	echo "$(TEXT_COLOR_GREEN)EVE ESI compatibility date update completed successfully!$(TEXT_RESET)"

.PHONY: help
help::
	@echo "  $(TEXT_UNDERLINE)EVE Online ESI:$(TEXT_UNDERLINE_END)"
	@echo "    get-compatibility-dates     Fetch available compatibility dates and select one"
	@echo "    generate-esi-openapi        Download OpenAPI specification for the selected date"
	@echo "    update-compatibility-date   Full workflow: select date, download OpenAPI spec and update __init__.py"
	@echo ""
