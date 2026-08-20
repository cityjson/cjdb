# Releasing a new version of cjdb

This document describes how to release a new version of `cjdb`. It is meant for the maintainers.

## Versioning

- cjdb follows [Semantic Versioning](https://semver.org/) (`MAJOR.MINOR.PATCH`).
- The version lives in a single place: the `version` field in [`pyproject.toml`](pyproject.toml). `cjdb.__version__` reads it via `importlib.metadata`, so nothing else needs to change.
- Releases are tagged `v<version>` (e.g. `v2.2.0`) on the `main` branch.
- `main` only contains release commits; development happens on `develop` and feature branches.

## Prerequisites

- Maintainer access to the `cityjson/cjdb` GitHub repository.
- An account on [PyPI](https://pypi.org) that is a maintainer of the `cjdb` project, with credentials set up for [twine](https://twine.readthedocs.io/) (e.g. a `~/.pypirc` or an API token in `TWINE_PASSWORD`).
- Access to the container registry the Docker image is published to (see [Docker image](#4-build-and-publish-the-docker-image)).

## Release checklist

Perform the checks below from the repository root.

### 0. Verify the release branch is ready

```bash
git checkout develop
git pull
```

Make sure the CI workflows pass on `develop` (they run on every push/PR):

- **Lint** (`.github/workflows/lint.yml`): ruff lint, ruff format, mypy.
- **Test** (`.github/workflows/test.yml`): the full pytest suite against a PostgreSQL/PostGIS instance.

Run the same checks locally as a final gate:

```bash
make test          # pytest (needs a local PostgreSQL/PostGIS) + mypy
uv run ruff check cjdb tests
uv run ruff format --check cjdb tests
```

### 1. Bump the version

Edit the `version` field in [`pyproject.toml`](pyproject.toml):

```toml
version = "2.3.0"
```

### 2. Update the changelog

Add an entry at the top of [`CHANGELOG.md`](CHANGELOG.md), following the
[Keep a Changelog](https://keepachangelog.com/en/1.0.0/) format already in use:

```markdown
## [2.3.0] - YYYY-MM-DD
`Added`
- new feature

`Changed`
- behavioural change

`Fixed`
- bug fix
```

### 3. Open a PR and merge to `main`

Commit the version bump and changelog, open a pull request `develop` → `main`,
wait for the CI checks to go green, and merge it.

Then:

```bash
git checkout main
git pull
```

### 4. Rebuild and commit the docs

The online docs (https://cityjson.github.io/cjdb) are built with Sphinx from
the `sphinx/` directory and committed as static HTML in `docs/` (served via
GitHub Pages). Rebuild them so they reflect the new version:

```bash
cd sphinx
uv run sphinx-build -b html . ../docs
cd ..
git add docs/
git commit -m "update docs for v2.3.0"
git push
```

### 5. Tag the release

```bash
git tag -a v2.3.0 -m "cjdb v2.3.0"
git push origin v2.3.0
```

### 6. Publish to PyPI

Build the wheel and source distribution, then upload them. There is no CI
workflow for publishing, so this is done manually:

```bash
uv build
uvx twine upload dist/*
```

Verify the package installs from PyPI:

```bash
pip install --index-url https://test.pypi.org/simple cjdb  # or, once live:
pip install -U cjdb
cjdb --help
```

### 7. Build and publish the Docker image

There is no CI workflow for the image either; build and push it manually.
Tag it with the version and, for convenience, `latest`:

```bash
docker build -t cjdb:2.3.0 -t cjdb:latest .
docker tag cjdb:2.3.0 <registry>/cityjson/cjdb:2.3.0
docker tag cjdb:latest <registry>/cityjson/cjdb:latest
docker push <registry>/cityjson/cjdb:2.3.0
docker push <registry>/cityjson/cjdb:latest
```

### 8. Create the GitHub release

Go to https://github.com/cityjson/cjdb/releases/new, choose the `v2.3.0` tag,
and paste the changelog entry for this version into the release notes.

### 9. Prepare `develop` for the next cycle (optional)

If the next release is likely to be a feature release, you can leave the
version as-is and bump it at release time. If you prefer to keep `develop`
ahead, bump it to the next `MINOR` version after tagging:

```bash
git checkout develop
# edit version to "2.4.0" in pyproject.toml
git commit -am "bump version to 2.4.0"
git push
```

## Rollback

- **PyPI**: versions cannot be deleted; release a new `PATCH` version with the
  fix instead. You can `yank` a broken release from
  https://pypi.org/project/cjdb.
- **GitHub release / tag**: delete and re-create the tag and release, then
  force-push the corrected `main`.
- **Docker image**: overwrite the `latest` tag with the previous version and
  keep the broken version tag in place for provenance.