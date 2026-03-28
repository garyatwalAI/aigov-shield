# Contributing to aigov-shield

Thank you for your interest in contributing to aigov-shield! This guide will help you get started.

## How to Report Bugs

If you find a bug, please open an issue on [GitHub Issues](https://github.com/garyatwalAI/aigov-shield/issues) with the following information:

- A clear, descriptive title
- Steps to reproduce the issue
- Expected behavior vs. actual behavior
- Python version and operating system
- aigov-shield version (`pip show aigov-shield`)
- Relevant logs, tracebacks, or screenshots

## How to Suggest Features

Feature requests are welcome! Please open an issue on [GitHub Issues](https://github.com/garyatwalAI/aigov-shield/issues) and include:

- A clear description of the feature and the problem it solves
- Example use cases
- Any relevant references (papers, standards, existing implementations)

Label your issue with `enhancement` if possible.

## Development Setup

1. **Fork and clone the repository:**

   ```bash
   git clone https://github.com/<your-username>/aigov-shield.git
   cd aigov-shield
   ```

2. **Create a virtual environment:**

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install development dependencies:**

   ```bash
   pip install -e ".[dev]"
   ```

4. **Run the test suite:**

   ```bash
   pytest
   ```

5. **Run the linter:**

   ```bash
   ruff check .
   ```

## Code Style

- Follow the [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)
- Use [ruff](https://docs.astral.sh/ruff/) for linting and formatting
- Add type hints to all function signatures
- Write docstrings for all public modules, classes, and functions
- Keep functions focused and concise

Run the formatter before committing:

```bash
ruff format .
ruff check --fix .
```

## Testing Requirements

- Write tests for all new functionality using [pytest](https://docs.pytest.org/)
- Maintain a minimum of **90% code coverage**
- Place tests in the `tests/` directory, mirroring the source structure
- Use descriptive test names that explain the behavior being tested
- Run the full suite before submitting a PR:

```bash
pytest --cov=aigov_shield --cov-report=term-missing
```

## Pull Request Process

1. **Fork** the repository and create a new branch from `main`:

   ```bash
   git checkout -b feat/your-feature-name
   ```

2. **Make your changes** in small, focused commits following the commit message convention below.

3. **Ensure all tests pass** and coverage remains at or above 90%.

4. **Push** your branch to your fork:

   ```bash
   git push origin feat/your-feature-name
   ```

5. **Open a Pull Request** against `main` on the upstream repository.

6. **Describe your changes** in the PR description, linking any related issues.

7. Address any review feedback promptly.

## Commit Message Convention

This project follows [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <short summary>

<optional body>

<optional footer>
```

**Types:**

| Type       | Description                                      |
|------------|--------------------------------------------------|
| `feat`     | A new feature                                    |
| `fix`      | A bug fix                                        |
| `docs`     | Documentation changes only                       |
| `style`    | Code style changes (formatting, no logic change) |
| `refactor` | Code change that neither fixes a bug nor adds a feature |
| `test`     | Adding or updating tests                         |
| `chore`    | Build process, tooling, or dependency changes    |
| `perf`     | Performance improvements                         |

**Examples:**

```
feat(prevention): add GroundingGuard for hallucination prevention
fix(measurement): correct bias score normalization
docs: update installation instructions in README
test(accountability): add chain of custody verification tests
```

## Code of Conduct

This project follows the [Contributor Covenant Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code. Please report unacceptable behavior to garyatwal2017@gmail.com.
