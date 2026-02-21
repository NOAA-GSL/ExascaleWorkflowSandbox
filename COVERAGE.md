# Test Coverage Guide

This project uses `pytest-cov` to measure and enforce test coverage.

## Coverage Threshold

**Minimum required coverage: 80%**

Pull requests must meet this threshold to pass CI checks.

## Running Coverage Locally

### Basic Coverage Run
```bash
source .chiltepin/bin/activate
pytest --cov=src/chiltepin --cov-report=term
```

### Generate HTML Report
```bash
pytest --cov=src/chiltepin --cov-report=html
# Open htmlcov/index.html in your browser
```

### Generate All Reports
```bash
pytest --cov=src/chiltepin --cov-report=term --cov-report=html --cov-report=xml
```

### Check Coverage Threshold
```bash
# Threshold is automatically enforced from pyproject.toml
pytest --cov=src/chiltepin
```

## Coverage Configuration

Coverage settings are configured in `pyproject.toml`:

- **Source**: `src/chiltepin/` (only code in this directory is measured)
- **Omits**: Test files, cache directories, virtual environments
- **Threshold**: 80% minimum coverage required
- **Reports**: Terminal output shows missing lines

## Understanding Coverage Reports

### Terminal Report
Shows percentage coverage per module and highlights missing line numbers:
```
Name                    Stmts   Miss  Cover   Missing
-----------------------------------------------------
src/chiltepin/cli.py       45      5    89%   23-27
src/chiltepin/tasks.py     38      0   100%
-----------------------------------------------------
TOTAL                      83      5    94%
```

### HTML Report
- Opens in browser with detailed line-by-line coverage
- Green = covered, red = not covered
- Shows branch coverage and complexity

## CI/CD Integration

The GitHub workflow automatically:
1. Runs tests with coverage on both AMD64 and ARM64 platforms
2. Fails the build if coverage drops below 80%
3. Uploads coverage reports as artifacts (available for 30 days)
4. Generates both XML and HTML reports for inspection

## Tips for Improving Coverage

1. **Identify uncovered code**: Check the HTML report or terminal output
2. **Write targeted tests**: Focus on uncovered lines and branches
3. **Test edge cases**: Error handling, boundary conditions, special cases
4. **Exclude intentional gaps**: Use `# pragma: no cover` for unreachable code

```python
def debug_only_function():  # pragma: no cover
    """Only used during development, not in production."""
    pass
```

## Adjusting the Threshold

To change the coverage threshold, edit the `fail_under` setting in `pyproject.toml`:

```toml
[tool.coverage.report]
fail_under = 80  # Change this value
```

The GitHub workflow will automatically use this threshold setting - no workflow changes needed.
