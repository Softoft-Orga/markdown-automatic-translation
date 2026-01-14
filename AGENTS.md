# AGENTS.md

Information for AI Agents working on this project.

## Scripts

### Tests

To run the test suite, use `pytest`:

```bash
pytest
```

Make sure you have the package installed in editable mode:

```bash
pip install -e .
```

### Documentation

The documentation is located in the `docs/` directory and uses Jekyll. To preview documentation
locally:

```bash
cd docs
jekyll serve
```

## Important Requirements

When making changes to the codebase, you **must** update the following accordingly:

- **Tests**: Update or add new tests in the `tests/` directory to cover your changes.
- **Documentation**: Update the relevant Markdown files in the `docs/` directory if your changes
  affect the CLI, API, or general behavior of the tool.

