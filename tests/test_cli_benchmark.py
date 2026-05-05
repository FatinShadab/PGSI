"""
Tests for CLI benchmark commands.
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

from pgsi_analyzer.cli.main import main


class TestCLIBenchmarkList:
    """Test benchmark list command."""

    def test_benchmark_list_all(self, capsys):
        """Test listing all algorithms and methods."""
        with patch('sys.argv', ['pgsi-analyzer', 'benchmark', 'list']):
            result = main(['benchmark', 'list'])
            
            assert result == 0
            captured = capsys.readouterr()
            assert "Available algorithms" in captured.out
            assert "Available execution methods" in captured.out

    def test_benchmark_list_algorithms_only(self, capsys):
        """Test listing only algorithms."""
        with patch('sys.argv', ['pgsi-analyzer', 'benchmark', 'list', '--algorithms']):
            result = main(['benchmark', 'list', '--algorithms'])
            
            assert result == 0
            captured = capsys.readouterr()
            assert "Available algorithms" in captured.out
            assert "hanoi" in captured.out

    def test_benchmark_list_methods_only(self, capsys):
        """Test listing only methods."""
        with patch('sys.argv', ['pgsi-analyzer', 'benchmark', 'list', '--methods']):
            result = main(['benchmark', 'list', '--methods'])
            
            assert result == 0
            captured = capsys.readouterr()
            assert "Available execution methods" in captured.out
            assert "cpython" in captured.out

    def test_benchmark_list_with_external_benchmarks_dir(self, capsys, tmp_path):
        """Test listing algorithms includes externally discovered benchmark."""
        custom_main = tmp_path / "user-benchmarks" / "demo-algo" / "cpython" / "main.py"
        custom_main.parent.mkdir(parents=True)
        custom_main.write_text("print('demo')\n")

        result = main([
            'benchmark', 'list',
            '--algorithms',
            '--benchmarks-dir', str(tmp_path / "user-benchmarks"),
        ])

        assert result == 0
        captured = capsys.readouterr()
        assert "demo-algo" in captured.out

    def test_benchmark_list_autodetects_local_benchmarks_registry(self, capsys, tmp_path):
        benchmarks_dir = tmp_path / "benchmarks"
        custom_main = benchmarks_dir / "auto-algo" / "cpython" / "main.py"
        custom_main.parent.mkdir(parents=True)
        custom_main.write_text("print('demo')\n")
        (benchmarks_dir / "pgsi_registry.json").write_text(
            '{"benchmarks":{"auto-algo":{"cpython":"auto-algo/cpython/main.py"}}}',
            encoding="utf-8",
        )

        with patch("pathlib.Path.cwd", return_value=tmp_path):
            result = main(['benchmark', 'list', '--algorithms'])

        assert result == 0
        captured = capsys.readouterr()
        assert "auto-algo" in captured.out


class TestCLIBenchmarkRun:
    """Test benchmark run command."""

    @patch('pgsi_analyzer.benchmark.orchestrator.run_benchmark_suite')
    def test_benchmark_run_basic(self, mock_run_suite):
        """Test basic benchmark run command."""
        mock_run_suite.return_value = Path("/test/GreenScore.csv")
        
        result = main([
            'benchmark', 'run',
            '--algorithms', 'hanoi',
            '--methods', 'cpython',
            '--runs', '5',
            '--output', '/test/results'
        ])
        
        assert result == 0
        mock_run_suite.assert_called_once()
        call_args = mock_run_suite.call_args
        assert call_args[1]['algorithms'] == ['hanoi']
        assert call_args[1]['methods'] == ['cpython']
        assert call_args[1]['runs'] == 5
        assert call_args[1]['output_dir'] == Path('/test/results')

    @patch('pgsi_analyzer.benchmark.orchestrator.run_benchmark_suite')
    def test_benchmark_run_all_algorithms(self, mock_run_suite):
        """Test benchmark run with all algorithms."""
        mock_run_suite.return_value = Path("/test/GreenScore.csv")
        
        result = main([
            'benchmark', 'run',
            '--algorithms', 'all',
            '--methods', 'cpython',
            '--runs', '10'
        ])
        
        assert result == 0
        mock_run_suite.assert_called_once()
        call_args = mock_run_suite.call_args
        assert call_args[1]['algorithms'] == ['all']

    @patch('pgsi_analyzer.benchmark.orchestrator.run_benchmark_suite')
    def test_benchmark_run_custom_weights(self, mock_run_suite):
        """Test benchmark run with custom GreenScore weights."""
        mock_run_suite.return_value = Path("/test/GreenScore.csv")
        
        result = main([
            'benchmark', 'run',
            '--algorithms', 'hanoi',
            '--methods', 'cpython',
            '--runs', '5',
            '--alpha', '0.5',
            '--beta', '0.3',
            '--gamma', '0.2'
        ])
        
        assert result == 0
        call_args = mock_run_suite.call_args
        assert call_args[1]['alpha'] == 0.5
        assert call_args[1]['beta'] == 0.3
        assert call_args[1]['gamma'] == 0.2

    @patch('pgsi_analyzer.benchmark.orchestrator.run_benchmark_suite')
    def test_benchmark_run_custom_carbon_intensity(self, mock_run_suite):
        """Test benchmark run with custom carbon intensity."""
        mock_run_suite.return_value = Path("/test/GreenScore.csv")
        
        result = main([
            'benchmark', 'run',
            '--algorithms', 'hanoi',
            '--methods', 'cpython',
            '--runs', '5',
            '--carbon-intensity', '0.0005'
        ])
        
        assert result == 0
        call_args = mock_run_suite.call_args
        assert call_args[1]['carbon_intensity'] == 0.0005

    @patch('pgsi_analyzer.benchmark.orchestrator.run_benchmark_suite')
    def test_benchmark_run_algorithm_runs_override(self, mock_run_suite):
        """Test benchmark run with per-algorithm run overrides."""
        mock_run_suite.return_value = Path("/test/GreenScore.csv")

        result = main([
            'benchmark', 'run',
            '--algorithms', 'hanoi', 'sieve',
            '--methods', 'cpython',
            '--runs', '5',
            '--algorithm-runs', 'hanoi=9', 'sieve=3',
        ])

        assert result == 0
        call_args = mock_run_suite.call_args
        assert call_args[1]['algorithm_runs'] == {'hanoi': 9, 'sieve': 3}

    @patch('pgsi_analyzer.benchmark.orchestrator.run_benchmark_suite')
    def test_benchmark_run_error_handling(self, mock_run_suite):
        """Test benchmark run error handling."""
        mock_run_suite.side_effect = ValueError("Invalid algorithm")
        
        result = main([
            'benchmark', 'run',
            '--algorithms', 'invalid',
            '--methods', 'cpython',
            '--runs', '5'
        ])
        
        assert result == 1

    @patch('pgsi_analyzer.benchmark.orchestrator.run_benchmark_suite')
    def test_benchmark_run_with_external_benchmarks_dir(self, mock_run_suite, tmp_path):
        """Test external benchmarks directory is forwarded to orchestrator."""
        mock_run_suite.return_value = Path("/test/GreenScore.csv")
        custom_benchmarks = tmp_path / "my_benchmarks"
        custom_benchmarks.mkdir()

        result = main([
            'benchmark', 'run',
            '--algorithms', 'hanoi',
            '--methods', 'cpython',
            '--runs', '2',
            '--benchmarks-dir', str(custom_benchmarks),
        ])

        assert result == 0
        call_args = mock_run_suite.call_args
        assert call_args[1]['benchmarks_dir'] == custom_benchmarks

    @patch('pgsi_analyzer.benchmark.orchestrator.run_benchmark_suite')
    def test_benchmark_run_autodetects_local_benchmarks_registry(self, mock_run_suite, tmp_path):
        mock_run_suite.return_value = Path("/test/GreenScore.csv")
        benchmarks_dir = tmp_path / "benchmarks"
        benchmarks_dir.mkdir()
        (benchmarks_dir / "pgsi_registry.json").write_text('{"benchmarks":{}}', encoding="utf-8")

        with patch("pathlib.Path.cwd", return_value=tmp_path):
            result = main([
                'benchmark', 'run',
                '--algorithms', 'hanoi',
                '--methods', 'cpython',
                '--runs', '2',
            ])

        assert result == 0
        call_args = mock_run_suite.call_args
        assert call_args[1]['benchmarks_dir'] == benchmarks_dir

    def test_benchmark_run_no_command(self, capsys):
        """Test benchmark command without subcommand shows help."""
        result = main(['benchmark'])
        
        assert result == 1
        captured = capsys.readouterr()
        assert "help" in captured.out.lower() or "usage" in captured.out.lower()


class TestCLIBenchmarkTemplate:
    """Test benchmark template scaffold command."""

    def test_benchmark_init_template_generates_structure(self, tmp_path):
        output_dir = tmp_path / "pgsi-template"

        result = main([
            'benchmark', 'init-template',
            '--output', str(output_dir),
            '--algorithms', 'hanoi',
        ])

        assert result == 0
        assert (output_dir / "README.md").exists()
        assert (output_dir / "hanoi" / "cpython" / "main.py").exists()
        assert (output_dir / "hanoi" / "pypy" / "main.py").exists()
        assert (output_dir / "hanoi" / "py_compile" / "main.py").exists()
        assert (output_dir / "hanoi" / "cython" / "main.py").exists()
        assert (output_dir / "hanoi" / "cython" / "raw.pyx").exists()
        assert (output_dir / "hanoi" / "cython" / "setup.py").exists()
        assert (output_dir / "hanoi" / "ctypes" / "main.py").exists()
        assert any((output_dir / "hanoi" / "ctypes").glob("*.c"))

    def test_benchmark_init_template_non_empty_without_force_fails(self, tmp_path):
        output_dir = tmp_path / "pgsi-template"
        output_dir.mkdir()
        (output_dir / "existing.txt").write_text("keep", encoding="utf-8")

        result = main([
            'benchmark', 'init-template',
            '--output', str(output_dir),
            '--algorithms', 'hanoi',
        ])

        assert result == 1


class TestCLIStartProject:
    """Test Django-style startproject command."""

    def test_startproject_generates_structure(self, tmp_path):
        project_dir = tmp_path / "my-benchmarks"

        result = main([
            'startproject',
            str(project_dir),
            '--algorithms', 'hanoi',
        ])

        assert result == 0
        assert (project_dir / "README.md").exists()
        assert (project_dir / "hanoi" / "cpython" / "main.py").exists()
        assert (project_dir / "hanoi" / "cython" / "raw.pyx").exists()
        assert any((project_dir / "hanoi" / "ctypes").glob("*.c"))
        content = (project_dir / "hanoi" / "cpython" / "main.py").read_text(encoding="utf-8")
        assert "Towers of Hanoi" in content

    def test_startproject_non_empty_without_force_fails(self, tmp_path):
        project_dir = tmp_path / "my-benchmarks"
        project_dir.mkdir()
        (project_dir / "existing.txt").write_text("keep", encoding="utf-8")

        result = main([
            'startproject',
            str(project_dir),
            '--algorithms', 'hanoi',
        ])

        assert result == 1


class TestCLICreateBenchmark:
    """Test create benchmark command."""

    def test_create_benchmark_creates_scaffold_and_registry(self, tmp_path):
        benchmarks_dir = tmp_path / "benchmarks"
        result = main([
            'create', 'benchmark',
            '--name', 'A1',
            '--benchmarks-dir', str(benchmarks_dir),
        ])
        assert result == 0
        assert (benchmarks_dir / "A1" / "cpython" / "main.py").exists()
        assert (benchmarks_dir / "A1" / "cython" / "raw.pyx").exists()
        assert (benchmarks_dir / "pgsi_registry.json").exists()

    def test_create_benchmark_invalid_name_fails(self, tmp_path):
        benchmarks_dir = tmp_path / "benchmarks"
        result = main([
            'create', 'benchmark',
            '--name', 'A*',
            '--benchmarks-dir', str(benchmarks_dir),
        ])
        assert result == 1


class TestCLIDefaultBootstrap:
    """Test running pgsi-analyzer with no command bootstraps project."""

    def test_no_command_bootstraps_benchmarks_project(self, tmp_path):
        with patch("pathlib.Path.cwd", return_value=tmp_path):
            result = main([])

        assert result == 0
        assert (tmp_path / "benchmarks" / "README.md").exists()
        assert (tmp_path / "benchmarks" / "hanoi" / "cpython" / "main.py").exists()

