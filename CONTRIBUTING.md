# Contributing to This Project

There are many ways to Contribute to this Project:

- Reporting bugs
- Translating the app
- Suggestions
- Optimize Code

and many more feel free to make a pull request.

- [Test Utilities](#test-utilities)
- [Branching and Pull Requests](#branching-and-pull-requests)
- [Translation](#translation)
- [Development](#development)
  - [Licence Agreements](#licence)
  - [Code of Conduct](#code-of-conduct)
  - [Enviroment](#enviroment)
  - [Makefile System](#makefile-system)
    - [General Commands](#general-commands)
    - [Migration Handling](#migration-handling)
    - [Translation Handling](#translation-handling)
    - [Git Handling](#git-handling)
    - [Pre-Commit](#pre-commit)
    - [Redis](#redis)
    - [Tests](#tests)

#### Test Utilities<a name="test-utilities"></a>

Please add new unit tests or update existing ones to cover any changes you make. Pull
requests that decrease overall test coverage may be rejected.

The project uses the Python [Python Unittest] framework together with Django's `TestCase` for
all tests. We also make use of the following third-party testing tools:

- django-webtest / [WebTest] — for testing the web user interface
- [requests-mock] — for mocking external HTTP calls made with the `requests` library
- [tox] — for running the test suite across environments
- [coverage] — for measuring test coverage

### Branching and Pull Requests<a name="branching-and-pull-requests"></a>

To submit code changes, fork the repository and create your branches from `master`.
We recommend using a separate branch for each feature or change. Keep your fork's
`master` branch up to date with the main repository to reduce merge conflicts.

If you're planning a new feature, open an Issue (type: Feature Request) first to
discuss and confirm that the idea fits the project.

You can open a merge request early to indicate you're working on something. If a
merge request is not ready for review, mark it as DRAFT. Remove the DRAFT status
when the request is ready for review.

## Translation<a name="translation"></a>

This app supports full translation, with all translations managed on my [Weblate] instance. If you would like to contribute or improve an existing translation, please feel free to register and get started.

## Development<a name="development"></a>

### Licence<a name="licence"></a>

This project is licensed under the GNU General Public License v3.0 (GPLv3). See the
[LICENSE](LICENSE) file for the full terms and conditions.

By contributing code to this project, you agree to license your contributions under
the same GPLv3 license that covers the project. In other words, your submitted
code will be made available under GPLv3 as part of the project.

### Code of Conduct<a name="code-of-conduct"></a>

The project's contributor behaviour is governed by a Code of Conduct. Please read the
[CODE_OF_CONDUCT](CODE_OF_CONDUCT.md) file for the full policy and expectations.

By contributing to this project you agree to abide by the Code of Conduct. If you observe
behaviour that violates the Code of Conduct, please follow the reporting instructions
contained in `CODE_OF_CONDUCT.md` so the project maintainers can address the issue.

### Enviroment<a name="enviroment"></a>

To develop and test your changes you should set up a local development environment. There
are several ways to do this, but please make sure you can run the project's pre-commit
hooks and execute the test suite locally using tox before submitting changes.

If you are using Windows or Linux, please follow the [AA Dev Enviroment Guide]
for step-by-step instructions.

### Makefile System<a name="makefile-system"></a>

The project uses a `Makefile` to simplify common tasks. Run `make` in the project root to list all available targets.

Some Make targets that run Django management commands rely on `manage.py`.
To make those targets work, the Makefile needs to know the absolute path to your auth directory.
You can do so by providing a `.make/myauth-path` file in the project root with the following content:

```makefile
/absolute/path/to/myauth
```

#### General Commands<a name="general-commands"></a>

- `make help` - Show all available make targets
- `make graph-models` - Create a graph of all models

#### Migration Handling<a name="migration-handling"></a>

- `make migrate` - Apply migrations
- `make migrations` - Create new migrations for changed models

#### Translation Handling<a name="translation-handling"></a>

- `make pot` - Create or update the translation template file

#### Git Handling<a name="git-handling"></a>

- `make git-prune` - Prune all unreachable objects from the local repository
- `make git-reset-soft` - Resetting HEAD to the previous commit (soft)
- `make git-force-push` - Forcing push to the remote repository without checks
- `make git-clean-untracked` - Cleaning untracked files and directories from the working tree
- `make git-garbage-collection` - Cleanup unnecessary files and optimize the local repository
- `make git-housekeeping` - Run all git housekeeping commands

#### Pre-Commit<a name="pre-commit"></a>

- `make pre-commit-install` - Install pre-commit hooks
- `make pre-commit-uninstall` - Uninstall pre-commit hooks
- `make pre-commit-update` - Update pre-commit hooks
- `make pre-commit-checks` - Run all pre-commit checks

#### Redis<a name="redis"></a>

- `make redis-flushall` - Flush all data from the Redis database
- `make redis-status` - Check the Redis server status

#### Tests<a name="tests"></a>

- `make build-test` - Build the package
- `make coverage` - Run the test suite with coverage

<!-- Links -->

[aa dev enviroment guide]: https://allianceauth.readthedocs.io/en/latest/development/dev_setup/aa-dev-setup-wsl-vsc-v2.html "AA Dev Enviroment Guide"
[python unittest]: https://docs.python.org/3/library/unittest.html "Python Unittest"
[weblate]: https://weblate.voices-of-war.de/ "Weblate"
