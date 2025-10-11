import sys
from pathlib import Path

# Ensure local src/ is importable before any mdxlate imports
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from typer.testing import CliRunner

from mdxlate.cli import app

runner = CliRunner()


def test_init_creates_default_prompt_file(tmp_path):
    prompt_path = tmp_path / "translation_instruction.txt"
    
    result = runner.invoke(app, ["init", "--prompt-path", str(prompt_path)])
    
    assert result.exit_code == 0
    assert prompt_path.exists()
    assert "✓ Created prompt template at:" in result.stdout
    assert str(prompt_path) in result.stdout
    assert "Edit this file to customize translations" in result.stdout
    assert "Use: mdx run ... --prompt-path" in result.stdout
    
    # Verify content
    content = prompt_path.read_text(encoding="utf-8")
    assert "world-class technical translator" in content


def test_init_creates_nested_directory(tmp_path):
    prompt_path = tmp_path / "nested" / "dir" / "prompt.txt"
    
    result = runner.invoke(app, ["init", "--prompt-path", str(prompt_path)])
    
    assert result.exit_code == 0
    assert prompt_path.exists()
    assert prompt_path.parent.exists()


def test_init_help_shows_documentation():
    result = runner.invoke(app, ["init", "--help"])
    
    assert result.exit_code == 0
    assert "Initialize editable translation prompt file" in result.stdout
    assert "prompt" in result.stdout.lower() and "path" in result.stdout.lower()


def test_run_help_shows_prompt_path_option():
    result = runner.invoke(app, ["run", "--help"])
    
    assert result.exit_code == 0
    # Check for the option name and description
    output_lower = result.stdout.lower()
    assert "prompt" in output_lower and "path" in output_lower
    assert "custom" in output_lower and "translation" in output_lower


def test_run_help_shows_force_option():
    result = runner.invoke(app, ["run", "--help"])
    
    assert result.exit_code == 0
    # Check for the option name and description
    output_lower = result.stdout.lower()
    assert "force" in output_lower
    assert "cache" in output_lower
