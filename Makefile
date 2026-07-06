.PHONY: help install update uninstall test check-updates

help: ## Show this help
	@grep -E '^[a-z-]+:.*##' $(MAKEFILE_LIST) | sed 's/:.*##/\t/' | sort

install: ## Install watch-vault into ~/.claude/skills (interactive)
	@./install.sh

update: ## Pull latest and re-install the skill
	@./update.sh

uninstall: ## Remove the skill + config (keeps your vault)
	@./uninstall.sh

test: ## Run the smoke tests
	@bash tests/run_tests.sh

check-updates: ## Report whether a newer release exists
	@python3 skills/watch-vault/scripts/check_updates.py
