"""Tests for package structure and imports."""
import pytest
import sys
from pathlib import Path


def test_maps_package_exists():
    """Test that the maps package exists and can be imported."""
    try:
        import maps
        assert True
    except ImportError:
        pytest.fail("maps package should be importable")


def test_maps_submodules_exist():
    """Test that all required submodules can be imported."""
    submodules = [
        'maps.client',
        'maps.geocoding', 
        'maps.directions',
        'maps.monitoring',
        'maps.config'
    ]
    
    for module in submodules:
        try:
            __import__(module)
        except ImportError:
            pytest.fail(f"{module} should be importable")


def test_package_structure():
    """Test that the package directory structure is correct."""
    project_root = Path(__file__).parent.parent
    maps_dir = project_root / "maps"
    
    assert maps_dir.exists(), "maps/ directory should exist"
    assert (maps_dir / "__init__.py").exists(), "maps/__init__.py should exist"
    
    expected_files = [
        "__init__.py",
        "client.py",
        "geocoding.py", 
        "directions.py",
        "monitoring.py",
        "config.py"
    ]
    
    for file in expected_files:
        assert (maps_dir / file).exists(), f"maps/{file} should exist"


def test_env_template_exists():
    """Test that environment template file exists."""
    project_root = Path(__file__).parent.parent
    env_template = project_root / ".env.template"
    
    assert env_template.exists(), ".env.template should exist"


def test_pyproject_toml_exists():
    """Test that pyproject.toml exists."""
    project_root = Path(__file__).parent.parent
    pyproject = project_root / "pyproject.toml"
    
    assert pyproject.exists(), "pyproject.toml should exist"