#!/usr/bin/env python3
"""Render Jinja2 documentation templates using version values.

The renderer operates in one of two modes:

  render_docs.py --all [version]
      Discover every ``*.j2`` template in the repository and render each one
      to a sibling file with the ``.j2`` suffix removed.  This keeps the
      README and any other rendered document in lock-step with the version.

  render_docs.py --check [version]
      Render every template in memory and compare it against the committed
      output on disk.  Prints a unified diff and exits non-zero if any output
      is stale or missing.  Nothing is written.

When ``version`` is omitted it is read from the ``[project]`` table of
``pyproject.toml``, the single source of truth maintained by release-please.
Templates receive ``version`` and ``major_version`` variables.
"""

from __future__ import annotations

# Standard Python Libraries
import difflib
from pathlib import Path
import re
import sys

# Third-Party Libraries
from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape
import semver

# Directory names that never contain documentation templates.  Skipping these
# keeps discovery fast and avoids rendering anything under vendored or cache
# directories.
EXCLUDED_DIRS = frozenset(
    {
        ".git",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        ".tox",
        ".venv",
        "__pycache__",
        "node_modules",
        "venv",
    }
)

USAGE = (
    "usage:\n"
    "  render_docs.py --all [version]\n"
    "  render_docs.py --check [version]\n"
    "When version is omitted it is read from pyproject.toml."
)


def project_version() -> str:
    """Read the project version from pyproject.toml."""
    pyproject = Path("pyproject.toml")
    if not pyproject.exists():
        print("ERROR: pyproject.toml not found.", file=sys.stderr)
        sys.exit(1)
    match = re.search(
        r'^version = "(.*)"$', pyproject.read_text(encoding="utf-8"), re.M
    )
    if not match:
        print("ERROR: no version field found in pyproject.toml.", file=sys.stderr)
        sys.exit(1)
    return match.group(1)


def version_context(version_string: str) -> dict[str, str]:
    """Build the template variable context from a semver string.

    Exits with a clear error if the version is not valid semver.
    """
    try:
        version = semver.Version.parse(version_string)
    except ValueError as error:
        print(
            f"ERROR: version must be valid semver (x.y.z); "
            f"got {version_string!r}: {error}",
            file=sys.stderr,
        )
        sys.exit(1)
    return {
        "major_version": str(version.major),
        "version": version_string,
    }


def render(template_path: Path, context: dict[str, str]) -> str:
    """Render a single template file to a string."""
    env = Environment(
        autoescape=select_autoescape(),
        keep_trailing_newline=True,
        loader=FileSystemLoader(str(template_path.parent)),
        lstrip_blocks=True,
        trim_blocks=True,
        undefined=StrictUndefined,
    )
    return env.get_template(template_path.name).render(**context)


def discover_templates(root: Path) -> list[Path]:
    """Return all ``*.j2`` templates under root, skipping excluded directories."""
    templates = []
    for path in sorted(root.rglob("*.j2")):
        if EXCLUDED_DIRS.intersection(path.parts):
            continue
        templates.append(path)
    return templates


def output_path(template_path: Path) -> Path:
    """Map a template path to its rendered output path (drop the .j2 suffix)."""
    return template_path.with_suffix("")


def render_all(version_string: str) -> None:
    """Render every discovered template to its sibling output file.

    All templates are rendered in memory before anything is written, so a
    failing template cannot leave the repository partially regenerated.
    """
    context = version_context(version_string)
    templates = discover_templates(Path("."))
    if not templates:
        print("WARNING: no '*.j2' templates found.", file=sys.stderr)
        return
    rendered_outputs: list[tuple[Path, Path, str]] = []
    for template_path in templates:
        rendered = render(template_path, context)
        rendered_outputs.append((template_path, output_path(template_path), rendered))
    for template_path, out, rendered in rendered_outputs:
        out.write_text(rendered, encoding="utf-8", newline="\n")
        print(f"rendered {template_path} -> {out}")


def check_all(version_string: str) -> None:
    """Verify every rendered output is in sync with its template.

    Prints a unified diff for each stale or missing output and exits non-zero
    when any are found.  Writes nothing.
    """
    context = version_context(version_string)
    templates = discover_templates(Path("."))
    stale: list[Path] = []
    for template_path in templates:
        out = output_path(template_path)
        rendered = render(template_path, context)
        committed = out.read_text(encoding="utf-8") if out.exists() else None
        if committed == rendered:
            continue
        stale.append(out)
        committed_lines = (committed or "").splitlines(keepends=True)
        print(f"ERROR: {out} is out of sync with {template_path}.", file=sys.stderr)
        diff = difflib.unified_diff(
            committed_lines,
            rendered.splitlines(keepends=True),
            fromfile=f"{out} (committed)",
            tofile=f"{out} (rendered)",
        )
        sys.stderr.writelines(diff)
        print("", file=sys.stderr)
    if stale:
        print(
            "Regenerate with 'make docs' and commit the result.",
            file=sys.stderr,
        )
        sys.exit(1)


def main() -> None:
    """Dispatch to the requested render mode based on command-line arguments."""
    args = sys.argv[1:]
    if len(args) in (1, 2) and args[0] in ("--all", "--check"):
        version_string = args[1] if len(args) == 2 else project_version()
        if args[0] == "--all":
            render_all(version_string)
        else:
            check_all(version_string)
    else:
        print(USAGE, file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
