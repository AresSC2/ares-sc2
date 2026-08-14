# Makefile
format-ruff:
	@ruff format .
lint-format:
	@ruff format --check .
lint-check:
	@ruff check .
lint-fix:
	@ruff check . --fix
lint-mypy:
	@mypy .
lint-mypy-report:
	@mypy ./src --html-report ./mypy_html

unit-tests:
	@pytest
unit-tests-cov:
	@pytest --doctest-modules --cov=src --cov-report term-missing --cov-report=html
unit-tests-cov-fail:
	@pytest --cov=src --cov-report term-missing --cov-report=html --cov-fail-under=49 --junitxml=pytest.xml | tee pytest-coverage.txt
clean-cov:
	@rm -rf .coverage
	@rm -rf htmlcov
	@rm -rf pytest.xml
	@rm -rf pytest-coverage.txt

format: format-ruff
lint: lint-format lint-check lint-mypy


##@ Documentation
docs-build: ## build documentation locally
	@mkdocs build
docs-deploy: ## build & deploy documentation to "gh-pages" branch
	@mkdocs gh-deploy -m "docs: update documentation" -v --force
clean-docs: ## remove output files from mkdocs
	@rm -rf site


##@ Releases

current-version: ## returns the current version
	@semantic-release print-version --current

next-version: ## returns the next version
	@semantic-release print-version --next

current-changelog: ## returns the current changelog
	@semantic-release changelog --released

next-changelog: ## returns the next changelog
	@semantic-release changelog --unreleased

publish-noop: ## publish command (no-operation mode)
	@semantic-release publish --noop
