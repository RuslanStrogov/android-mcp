# Contributing

## Workflow

`feature/*` → PR → `dev` → PR → `main`. Never push directly to `main` or `dev`.

```bash
git checkout dev && git pull
git checkout -b feat/my-thing
# ... commit ...
git push -u origin feat/my-thing
gh pr create --base dev --head feat/my-thing
```

## Conventions

- Conventional commits: `feat(scope): ...`, `fix(scope): ...`, `docs: ...`, `ci: ...`.
- Branch prefixes: `feat/`, `fix/`, `docs/`, `ci/`, `chore/`.
- Every fix = one commit; every build = one release tag.

## Local checks

```bash
pip install -e ".[dev]"
ruff check .
pytest
```

## Standards

- Python 3.11+, type hints everywhere.
- No blocking subprocess calls — use the async helpers in `adb.py`.
- No hardcoded paths — go through `config.py`.
- Screenshots are returned as image content, not file paths.
