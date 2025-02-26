# Contributing to This Project

Thank you for considering contributing to our project! Here are some guidelines to help you get started.

## Getting Started

1. **Fork the repository**: Click the "Fork" button at the top right of the repository page.

1. **Clone your fork**: Clone your forked repository to your local machine.

   ```sh
   git clone https://github.com/geuthur/aa-ledger.git
   ```

1. **Set up the upstream remote**: Add the original repository as a remote to keep your fork up to date.

   ```sh
   git remote add upstream https://github.com/geuthur/aa-ledger.git
   ```

1. **Set up Alliance Auth Development Environment**

   To develop and test your change, you need a development environment from Alliance Auth on your local machine.
   Ensure you can use pre-commit checks and tox tests on your local machine.

   AA Guide to create a WSL [AA Dev Env](https://allianceauth.readthedocs.io/en/latest/development/dev_setup/aa-dev-setup-wsl-vsc-v2.html#)

## Pre-commit Hooks

We use pre-commit hooks to ensure code quality and consistency. Please make sure you have pre-commit installed and set up.

1. **Install pre-commit**: If you don't have pre-commit installed, you can install it using pip.

   ```sh
   pip install pre-commit
   ```

1. **Install the hooks**: Run the following command to install the pre-commit hooks.

   ```sh
   pre-commit install
   ```

1. **Use Pre Commit**

   Check all files

   ```sh
   pre-commit run --all-files
   ```

   If you want only one of the hooks like `eslint`

   ```sh
   pre-commit run eslint
   ```

## Branching und Contributing via Pull Requests

Before creating a pull request, make sure that you have forked the repository and are working on your fork. This ensures that your changes are isolated and do not affect the original repository until they are reviewed and merged.

The `master` branch should always be kept up to date to avoid conflicts. This means that all changes integrated into the `master` branch should be thoroughly reviewed and tested before being merged. Regular updates and synchronizations with the `master` branch help to identify and resolve potential conflicts early.

Before creating a new feature, an issue should always be opened first. This serves to start a discussion about the planned feature and ensure that all team members are informed about the planned changes. Through discussion, potential problems and improvements can be identified and considered early. This promotes a collaborative working approach and contributes to the quality and consistency of the project.

## Tests

We use several testing tools and frameworks to ensure the quality and reliability of our codebase. Below is a list of the main tools we use:

- [django-webtest](https://github.com/django-webtest/django-webtest)
- [request-mock](https://requests-mock.readthedocs.io/en/latest/)
- [tox](https://tox.wiki/en/latest/index.html)
- [coverage](https://coverage.readthedocs.io/en/latest/#)

We also use Django's built-in [`TestCase`](https://docs.djangoproject.com/en/5.1/topics/testing/overview/)class to write unit tests for our Django applications. The `TestCase` class provides a framework for writing and running tests, including setup and teardown methods to prepare the test environment and clean up afterward.
