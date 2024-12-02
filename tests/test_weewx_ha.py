#!/usr/bin/env pytest -vs
"""Tests for weewx_ha."""

# Standard Python Libraries
import os

# Third-Party Libraries
import pytest

# Geekpad Libraries
import weewx_ha

# define sources of version strings
RELEASE_TAG = os.getenv("RELEASE_TAG")
PROJECT_VERSION = weewx_ha.__version__


@pytest.mark.skipif(
    RELEASE_TAG in [None, ""], reason="this is not a release (RELEASE_TAG not set)"
)
def test_release_version():
    """Verify that release tag version agrees with the module version."""
    assert (
        RELEASE_TAG == f"v{PROJECT_VERSION}"
    ), "RELEASE_TAG does not match the project version"
