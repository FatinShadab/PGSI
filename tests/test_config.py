"""
Tests for pgsi_analyzer.config module.

This test suite verifies configuration and default parameters.
"""

import pytest
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch, MagicMock

from pgsi_analyzer.config import (
    DEFAULT_PARAMS,
    get_default_params,
    resolve_config_path,
    DNA_ENV_VAR,
)


class TestDefaultParams:
    """Tests for DEFAULT_PARAMS constant."""

    def test_default_params_is_dict(self):
        """Test that DEFAULT_PARAMS is a dictionary."""
        assert isinstance(DEFAULT_PARAMS, dict)

    def test_default_params_has_algorithms(self):
        """Test that DEFAULT_PARAMS contains expected algorithms."""
        expected_algorithms = [
            "hanoi", "strassen", "spectral-norm", "sieve", "n-queens",
            "reverse_complement", "binary-trees", "knn", "pi_digits",
            "K_Nucleotide", "fannkuch_redux", "fasta", "mandelbrot",
            "nbody", "regex_redux"
        ]
        
        for algo in expected_algorithms:
            assert algo in DEFAULT_PARAMS, f"Algorithm {algo} not found in DEFAULT_PARAMS"

    def test_default_params_structure(self):
        """Test that each algorithm has test_n parameter."""
        for algo_name, params in DEFAULT_PARAMS.items():
            assert "test_n" in params, f"Algorithm {algo_name} missing 'test_n' parameter"
            assert isinstance(params["test_n"], int)

    def test_hanoi_params(self):
        """Test hanoi algorithm parameters."""
        params = DEFAULT_PARAMS["hanoi"]
        assert "test_n" in params
        assert "n" in params
        assert isinstance(params["n"], int)

    def test_k_nucleotide_has_file_path(self):
        """Test that K_Nucleotide has nucleotide_sequence_file."""
        params = DEFAULT_PARAMS["K_Nucleotide"]
        assert "nucleotide_sequence_file" in params
        assert isinstance(params["nucleotide_sequence_file"], Path)


class TestGetDefaultParams:
    """Tests for get_default_params function."""

    def test_get_default_params_success(self):
        """Test getting default parameters for valid algorithm."""
        params = get_default_params("hanoi")
        assert isinstance(params, dict)
        assert "test_n" in params
        assert "n" in params

    def test_get_default_params_returns_copy(self):
        """Test that get_default_params returns a copy (not reference)."""
        params1 = get_default_params("hanoi")
        params2 = get_default_params("hanoi")
        
        # Modify one copy
        params1["test_n"] = 999
        
        # Other copy should be unchanged
        assert params2["test_n"] != 999

    def test_get_default_params_unknown_algorithm(self):
        """Test that unknown algorithm raises KeyError."""
        with pytest.raises(KeyError, match="Unknown algorithm"):
            get_default_params("nonexistent_algorithm")

    def test_get_default_params_all_algorithms(self):
        """Test getting parameters for all known algorithms."""
        for algo_name in DEFAULT_PARAMS.keys():
            params = get_default_params(algo_name)
            assert isinstance(params, dict)
            assert len(params) > 0


class TestResolveConfigPath:
    """Tests for resolve_config_path function."""

    def test_resolve_config_path_basic(self):
        """Test basic config path resolution."""
        with patch('pgsi_analyzer.config.resolve_data_path') as mock_resolve:
            mock_resolve.return_value = Path("/test/data")
            
            result = resolve_config_path("subdir", "file.txt")
            
            assert isinstance(result, Path)
            assert result == Path("/test/data/subdir/file.txt")
            mock_resolve.assert_called_once()

    def test_resolve_config_path_multiple_parts(self):
        """Test config path resolution with multiple parts."""
        with patch('pgsi_analyzer.config.resolve_data_path') as mock_resolve:
            mock_resolve.return_value = Path("/test/data")
            
            result = resolve_config_path("dir1", "dir2", "file.txt")
            
            assert result == Path("/test/data/dir1/dir2/file.txt")


class TestDNAPathResolution:
    """Tests for DNA file path resolution."""

    def test_dna_path_from_env_var(self):
        """Test DNA path resolution from environment variable."""
        with TemporaryDirectory() as tmpdir:
            dna_file = Path(tmpdir) / "dna.txt"
            dna_file.write_text("ATGC")
            
            with patch.dict(os.environ, {DNA_ENV_VAR: str(dna_file)}):
                from pgsi_analyzer.config.defaults import _resolve_dna_path
                result = _resolve_dna_path()
                assert result == dna_file
                assert result.exists()

    @patch('pgsi_analyzer.config.defaults.resolve_data_path')
    def test_dna_path_from_data_dir(self, mock_resolve):
        """Test DNA path resolution from data directory."""
        with TemporaryDirectory() as tmpdir:
            data_dir = Path(tmpdir)
            dna_file = data_dir / "K-Nucleotide" / "dna.txt"
            dna_file.parent.mkdir(parents=True)
            dna_file.write_text("ATGC")
            
            mock_resolve.return_value = data_dir
            
            with patch.dict(os.environ, {}, clear=True):
                from pgsi_analyzer.config.defaults import _resolve_dna_path
                result = _resolve_dna_path()
                assert result == dna_file

    def test_dna_path_not_found_raises(self):
        """Test that missing DNA file raises FileNotFoundError."""
        with patch.dict(os.environ, {}, clear=True):
            with patch('pgsi_analyzer.config.defaults.resolve_data_path') as mock_resolve:
                mock_resolve.return_value = Path("/nonexistent/data")
                
                # Mock Path(__file__) for repo fallback
                with patch('pgsi_analyzer.config.defaults.Path') as mock_path_class:
                    # Make Path work normally for string paths
                    def path_side_effect(path_arg):
                        if isinstance(path_arg, str):
                            return Path(path_arg)
                        return path_arg
                    
                    mock_path_class.side_effect = path_side_effect
                    
                    # Mock __file__ resolution
                    mock_file = MagicMock()
                    mock_parents = [MagicMock(), MagicMock(), Path("/repo/root")]
                    mock_file.resolve.return_value.parents = mock_parents
                    mock_path_class.return_value = mock_file
                    
                    from pgsi_analyzer.config.defaults import _resolve_dna_path
                    with pytest.raises(FileNotFoundError, match="dna.txt not found"):
                        _resolve_dna_path()


class TestConfigIntegration:
    """Integration tests for config module."""

    def test_config_module_imports(self):
        """Test that config module can be imported."""
        from pgsi_analyzer.config import (
            DEFAULT_PARAMS,
            get_default_params,
            resolve_config_path,
        )
        assert True

    def test_backwards_compatibility_alias(self):
        """Test that __default__ alias exists for backwards compatibility."""
        from pgsi_analyzer.config import __default__
        assert __default__ == DEFAULT_PARAMS

    def test_get_default_params_modification_safe(self):
        """Test that modifying returned params doesn't affect DEFAULT_PARAMS."""
        original_test_n = DEFAULT_PARAMS["hanoi"]["test_n"]
        
        params = get_default_params("hanoi")
        params["test_n"] = 999
        
        # DEFAULT_PARAMS should be unchanged
        assert DEFAULT_PARAMS["hanoi"]["test_n"] == original_test_n

