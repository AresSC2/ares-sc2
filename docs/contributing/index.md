# Contributors guidance

***

<b> Rough notes for now, this section of the docs needs work </b>

***

### Random bits explaining some decisions
 - Application layout - [Python Packaging Authority](https://packaging.python.org/en/latest/tutorials/packaging-projects/)
recommend the `src` layout
 - Standard to store version number in the package's `__init__.py` [PEP8](https://peps.python.org/pep-0008/)
 - Also store the version in `pyproject.toml`
 - `Makefile` contains most of the commonly used commands from this write-up. This file is used by GitHub workflow
 - Follow [semantic versioning](https://semver.org/) `MAJOR.MINOR.PATCH` 


### Setting up dev environment
- install `poetry`
- clone repo 
- run `poetry install --with docs lint test semver notebook`

### Linting and autoformatting
 - black for main autoformatting
 - isort for import formatting
 - flake8 for checking code base against coding style (PEP8)
 - mypy for checking type annotations 

isort and black don't agree on some things, add following to `pyproject.toml`
```
[tool.isort]
profile = "black"
```

flake8 also needs to use black settings, we do this with a `.flake8` settings file

For mypy we configure via `pyproject.toml`, see 
[docs](https://mypy.readthedocs.io/en/stable/config_file.html#using-a-pyproject-toml)
See more [here](https://mypy.readthedocs.io/en/stable/running_mypy.html)

#### Using these tools on command line

Can pass in `--check` for some of these

`isort .`
`black.`
`flake8 .`
`mypy .`

We put all these into a `makefile`, which allows us to do:
`make format`
`make lint`

However, using makefiles on Windows requires a bit more setup

#### Configure PyCharm to run these automatically
TODO: Put own guide here as link might die

black, isort and flake8 
[See guide here](https://johschmidt42.medium.com/automate-linting-formatting-in-pycharm-with-your-favourite-tools-de03e856ee17)

mypy - PyCharm will help with type annotations, just ensure they are being used, and run `mypy .` before committing
to ensure the github lint workflow tests pass


### Git commit guidelines
See [conventional commits](https://www.conventionalcommits.org/en/v1.0.0/), all commits and PR's should follow
these guidelines

A github workflow is setup to enforce this, [see here](https://github.com/amannn/action-semantic-pull-request)

Layout:
```
<type>(<scope>): <subject>
<BLANK LINE>
<body>
<BLANK LINE>
<footer>
```

Commit message no longer than 100 characters (scope is optional)

<subject> text
This is a very short description of the change.
 - use imperative, present tense: “change” not “changed” nor “changes”
 - don't capitalize first letter
 - no dot (.) at the end

Python Semantic Release will recognise the types of commits to automatically determine a new version

 - `fix:` commit is a PATCH
 - `feat:` commit is a MINOR
 - `BREAKING CHANGE` or `!` is a MAJOR
 - `build:`, `chore:`, `ci:`, `docs:`, `style:`, `refactor:`, `perf:`, `test:` do not increase version

A scope can also be added in parentheses. For example: `feat(combat): add kiting behavior`

Example of breaking change commit message
`feat(api)!: send an email to the customer when a product is shipped`


#### Github workflow
All formatters and linters are run in a github workflow, we use the `makefile` here.

### Unit tests
Read [this](https://realpython.com/pytest-python-testing/), no point repeating it here
`poetry add --group test pytest`

Each test should be small and self-contained

#### Coverage
Indicates how much code is covered by tests

Run coverage through `pytest`:
`pytest --cov=src --cov-report term-missing --cov-report=html`

Run specific tests
`pytest -v -s tests/managers/test_building_manager.py::TestBuildingManager::test_construct_gas`

[Offical docs](https://coverage.readthedocs.io/en/6.5.0/config.html)


### Automatic documentation
Using [mkdocs](https://www.mkdocs.org/) for no particular reason other than found a good tutorial using it

`poetry add --group docs mkdocs mkdocs-material`

Sphinx is another alternative

To build docs locally:
`mkdocs build`

Push to github pages: (shouldn't need to use this)
`mkdocs gh-deploy -m "docs: update documentation" -v --force`

#### Docstrings

Using numpy docstrings style

`poetry add --group docs "mkdocstrings[python]"`

At the relevant place in a markdown file add for example:
```
::: ares.example_docstrings
    options:
        show_root_heading: true
```
Where `ares.example_docstrings` is the python file containing numpy style docstrings

Pytest will run tests on any Examples in docstrings in Github workflow
`pytest --doctest-modules`

### Versioning and automatic releases
Use [Python Semantic Release](https://python-semantic-release.readthedocs.io/en/latest/) to create automatic releases
based on the commits, therefore git commits should follow the Angular commit style

`poetry add --group semver python-semantic-release`

#### Python Semantic Release commands

In general if Github actions is working, these shouldn't need to be manually called.

Get current version:
`semantic-release print-version --current`

Compute a version bump:
`semantic-release print-version --next`

Get current changelog:
`semantic-release changelog --released`

Generate a new changelog:
`semantic-release changelog --unreleased`

Publish a release:
`semantic-release publish --noop`

### Poetry
Takes care of env, dependency, building and publishing

#### Useful commands
See [Basic usage](https://python-poetry.org/docs/basic-usage/)

Init new project, generates `pyproject.toml` that contains the entire package configuration. Fine to edit this

```poetry init --name ares-sc2 --no-interaction```

Run in virtual env (poetry uses venv) [Managing poetry environments](https://python-poetry.org/docs/managing-environments/):

```poetry run python src/ares/main.py```

Run tests

```poetry run pytest```

Create and activate an environment (can also use PyCharm to create new env):

```poetry env use python```

On Linux possibly:
```poetry env use python3.10```

Find environment in file system:

```poetry env list --full-path```

Use this path to add existing env in PyCharm

Can get a shell into the environment:

```poetry shell```

Install dependencies:

```poetry add burnysc2```

Create a `lock` file. Should be added to git. Ensures all people working on project using the same library versions.
Automatically generated and shouldn't be edited

```poetry lock```

Install all dependencies based on the lock file

This command will read the TOML file, resolve all the dependencies and finally install them in a virtual environment 
that poetry will create by default under {cache-dir}/virtualenvs/. 

```poetry install```

Install without dev tools

```poetry install --without lint```

List all installed dependencies:

```poetry show```

List current and latest available version

```poetry show -l```

Same as above, but only show outdated

```poetry show -o```

Update dependencies:

```poetry update```

Poetry can organise dependencies by groups, since dev tools etc are not required in the package release, eg:

```poetry add --group lint isort black flake8 mypy```


#### Notes about `pyproject.toml`
 - what backend to build the package: build-system (Instead of setup.py/setup.cfg or others, the backend to build the package is poetry)
 - some metadata for the project: tool.poetry (the initial version of the package*, description etc.)
 - the dependencies for the app: tool.poetry.dependencies
 - gotcha - The name in `pyproject.toml` should be the same as the package

### Working with jupyter notebook
It's possible to run jupyter notebook using an existing poetry environment. Install the following
package at the global or user level:

`pip install --user poetry-kernel`

As long as `ares-sc2` was installed with the `notebook` dependencies, then when launching
jupyter notebook there should be an option to open a notebook with the poetry kernel

