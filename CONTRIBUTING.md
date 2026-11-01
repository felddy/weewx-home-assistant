# Welcome #

We're so glad you're thinking about contributing to this open source
project!  If you're unsure or afraid of anything, just ask or submit
the issue or pull request anyway.  The worst that can happen is that
you'll be politely asked to change something.  We appreciate any sort
of contribution, and don't want a wall of rules to get in the way of
that.

Before contributing, we encourage you to read our CONTRIBUTING policy
(you are here), our [LICENSE](LICENSE), and our [README](README.md),
all of which should be in this repository.

## Issues ##

If you want to report a bug or request a new feature, the most direct
method is to [create an
issue](https://github.com/felddy/weewx-home-assistant/issues) in
this repository.  We recommend that you first search through existing
issues (both open and closed) to check if your particular issue has
already been reported.  If it has then you might want to add a comment
to the existing issue.  If it hasn't then feel free to create a new
one.

## Pull requests ##

If you choose to [submit a pull
request](https://github.com/felddy/weewx-home-assistant/pulls),
you will notice that our continuous integration (CI) system runs a
fairly extensive set of linters, syntax checkers, system, and unit tests.
Your pull request may fail these checks, and that's OK.  If you want
you can stop there and wait for us to make the necessary corrections
to ensure your code passes the CI checks.

If you want to make the changes yourself, or if you want to become a
regular contributor, then you will want to set up
[pre-commit](https://pre-commit.com/) on your local machine.  Once you
do that, the CI checks will run locally before you even write your
commit message.  This speeds up your development cycle considerably.

### Setting up pre-commit ###

This project uses [uv](https://docs.astral.sh/uv/) to manage its
Python interpreter, virtual environment, and dependencies.

#### Installing uv ####

On macOS, we recommend installing [brew](https://brew.sh/). Then
installation is as simple as `brew install uv`. For Linux, Windows
Subsystem for Linux (WSL), or macOS without `brew`, use the
[standalone installer](https://docs.astral.sh/uv/getting-started/installation/).
There is no need to install Python separately: `uv` downloads a
suitable interpreter on demand.

#### Creating the Python virtual environment ####

Create the environment with the test and documentation dependency
groups, and activate it so the `pre-commit`, `pytest`, and `make`
commands below find their tools:

```console
cd weewx-home-assistant
uv sync --group test --group docs
source .venv/bin/activate
```

If you prefer not to activate the environment, prefix commands with
`uv run` instead (for example `uv run pytest`).

#### Installing the pre-commit hook ####

Now setting up pre-commit is as simple as:

```console
pre-commit install
```

At this point the pre-commit checks will run against any files that
you attempt to commit.  If you want to run the checks against the
entire repo, just execute `pre-commit run --all-files`.

### Running unit and system tests ###

In addition to the pre-commit checks the CI system will run the suite
of unit and system tests that are included with this project.  To run
these tests locally execute `pytest` from the root of the project.

We encourage any updates to these tests to improve the overall code
coverage.  If your pull request adds new functionality we would
appreciate it if you extend existing test cases, or add new ones to
exercise the newly added code.

## Public domain ##

This project is in the public domain within the United States, and
copyright and related rights in the work worldwide are waived through
the [CC0 1.0 Universal public domain
dedication](https://creativecommons.org/publicdomain/zero/1.0/).

All contributions to this project will be released under the CC0
dedication. By submitting a pull request, you are agreeing to comply
with this waiver of copyright interest.
