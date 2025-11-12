"""
Configuration Utilities

Centralized path loading and platform-specific path conversion.
All paths are defined in config/paths_config.yaml and automatically
converted to the correct format (Windows vs WSL) based on the current platform.

Usage:
    from config_utils import PathConfig

    config = PathConfig()
    price_data = config.get_price_data_path()
    monthly_data_dir = config.get_monthly_reference_dir()
"""

import sys
import yaml
from pathlib import Path
from typing import Optional, List


class PathConfig:
    """Centralized path configuration loader with platform-aware conversions"""

    def __init__(self, config_file: str = "config/paths_config.yaml"):
        """
        Initialize path configuration.

        Args:
            config_file: Path to paths_config.yaml (relative to project root)

        Raises:
            FileNotFoundError: If config file not found
            yaml.YAMLError: If config file is malformed
        """
        config_path = Path(config_file)

        if not config_path.exists():
            raise FileNotFoundError(
                f"Path configuration file not found: {config_path.absolute()}\n"
                f"Expected location: {config_path}"
            )

        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)

        if not self.config:
            raise ValueError(f"Path configuration is empty: {config_path}")

    @staticmethod
    def convert_windows_to_wsl(windows_path: str) -> str:
        """
        Convert Windows path to WSL path if running on WSL/Linux.

        Args:
            windows_path: Path in Windows format (e.g., C:/Users/...)

        Returns:
            Path in native format (WSL format on Linux, unchanged on Windows)
        """
        if sys.platform == 'win32':
            # Running on Windows - return as-is
            return windows_path

        # Running on WSL/Linux - convert Windows path to WSL mount path
        windows_path = windows_path.replace('\\', '/')  # Normalize backslashes
        if windows_path.startswith('C:/') or windows_path.startswith('C:\\'):
            return '/mnt/c' + windows_path[2:]

        return windows_path

    def _resolve_path(self, path_str: str) -> str:
        """
        Resolve a single path string, converting to appropriate format.

        Args:
            path_str: Path string from config

        Returns:
            Resolved path in native format
        """
        if not path_str:
            return None
        return self.convert_windows_to_wsl(path_str)

    def _resolve_path_list(self, path_list: List[str]) -> List[str]:
        """
        Resolve a list of paths, converting each to appropriate format.

        Args:
            path_list: List of path strings from config

        Returns:
            List of resolved paths in native format
        """
        if not path_list:
            return []
        return [self.convert_windows_to_wsl(p) for p in path_list if p]

    # ========== OneDrive Directories ==========

    def get_onedrive_options_data_dir(self) -> str:
        """Get OneDrive OptionsData directory"""
        return self._resolve_path(self.config['onedrive']['options_data'])

    def get_onedrive_nasdaq_stock_data_dir(self) -> str:
        """Get OneDrive Nasdaq Stock Data directory"""
        return self._resolve_path(self.config['onedrive']['nasdaq_stock_data'])

    # ========== Price Data ==========

    def get_price_data_path(self) -> str:
        """
        Get the best available price data path.

        Returns the first available path from the preference order:
        1. OneDrive parquet (primary storage)
        2. CSV fallback

        Returns:
            Path to price data file
        """
        sources = self.config['price_data_strategy']['sources']
        resolved_sources = self._resolve_path_list(sources)

        for source in resolved_sources:
            if Path(source).exists():
                return source

        # If none exist, return the preferred one (OneDrive parquet)
        return self._resolve_path(sources[0])

    def get_price_data_parquet(self) -> str:
        """Get price data parquet file (OneDrive location)"""
        return self._resolve_path(self.config['input_data']['price_data_parquet'])

    def get_price_data_csv_legacy(self) -> str:
        """Get legacy CSV price data file (fallback only)"""
        return self._resolve_path(
            self.config['price_data_strategy']['sources'][-1]  # Last source (CSV)
        )

    # ========== Options Data ==========

    def get_options_data_parquet(self) -> str:
        """Get options data parquet file (OneDrive location)"""
        return self._resolve_path(self.config['input_data']['options_data_parquet'])

    # ========== IV Historical Data ==========

    def get_iv_historical_parquet(self) -> str:
        """Get IV historical parquet file (OneDrive location)"""
        return self._resolve_path(self.config['input_data']['iv_historical_parquet'])

    # ========== Drawdown Data ==========

    def get_drawdown_parquet(self) -> str:
        """Get drawdown parquet file (OneDrive location)"""
        return self._resolve_path(self.config['input_data']['drawdown_parquet'])

    # ========== Output Data ==========

    def get_main_analysis_output(self) -> str:
        """Get main analysis output file"""
        return self._resolve_path(self.config['output_data']['main_analysis'])

    def get_iv_potential_decline_output(self) -> str:
        """Get IV Potential Decline output file"""
        return self._resolve_path(self.config['output_data']['iv_potential_decline'])

    def get_stock_data_output(self) -> str:
        """Get stock data output file"""
        return self._resolve_path(self.config['output_data']['stock_data'])

    def get_probability_history_output(self) -> str:
        """Get probability history output file"""
        return self._resolve_path(self.config['output_data']['probability_history'])

    def get_last_updated_metadata(self) -> str:
        """Get last updated metadata file"""
        return self._resolve_path(self.config['output_data']['last_updated_metadata'])

    # ========== Monthly Data ==========

    def get_monthly_stats_file(self) -> str:
        """Get monthly statistics file"""
        return self._resolve_path(self.config['monthly_data']['monthly_stats'])

    def get_volatility_data_file(self) -> str:
        """Get volatility data file"""
        return self._resolve_path(self.config['monthly_data']['volatility_data'])

    def get_monthly_reference_dir(self) -> str:
        """Get monthly reference data directory"""
        return self._resolve_path(self.config['monthly_data']['reference_data_dir'])

    def get_options_available_file(self) -> str:
        """Get options available reference file"""
        return self._resolve_path(self.config['monthly_data']['options_available'])

    def get_mfn_links_file(self) -> str:
        """Get MFN links reference file"""
        return self._resolve_path(self.config['monthly_data']['mfn_links'])

    def get_previous_events_file(self) -> str:
        """Get previous events reference file"""
        return self._resolve_path(self.config['monthly_data']['previous_events'])

    def get_name_mapping_file(self) -> str:
        """Get name mapping reference file"""
        return self._resolve_path(self.config['monthly_data']['name_mapping'])

    # ========== Weekly Maintenance ==========

    def get_weekly_maintenance_dir(self) -> str:
        """Get weekly maintenance data directory"""
        return self._resolve_path(self.config['weekly_maintenance']['data_dir'])

    # ========== Probability History ==========

    def get_probability_history_onedrive_dir(self) -> str:
        """Get OneDrive directory for probability history"""
        return self._resolve_path(self.config['probability_history']['onedrive_dir'])

    # ========== Backup Paths ==========

    def get_backup_onedrive_dir(self) -> str:
        """Get backup directory on OneDrive"""
        return self._resolve_path(self.config['backup']['onedrive_dir'])

    def get_backup_timestamped_dir(self) -> str:
        """Get timestamped backups directory"""
        return self._resolve_path(self.config['backup']['timestamped_backups'])

    def get_files_to_backup(self) -> List[str]:
        """Get list of files to backup"""
        return self._resolve_path_list(self.config['backup']['files'])

    def get_backup_retention_days(self) -> int:
        """Get backup retention period in days"""
        return self.config['backup']['retention_days']

    # ========== Project Directories ==========

    def get_logs_dir(self) -> str:
        """Get logs directory"""
        return self._resolve_path(self.config['project_dirs']['logs'])

    def get_input_dir(self) -> str:
        """Get input directory"""
        return self._resolve_path(self.config['project_dirs']['input'])

    def get_output_dir(self) -> str:
        """Get output directory"""
        return self._resolve_path(self.config['project_dirs']['output'])

    def get_config_dir(self) -> str:
        """Get config directory"""
        return self._resolve_path(self.config['project_dirs']['config'])

    def get_archive_dir(self) -> str:
        """Get archive directory"""
        return self._resolve_path(self.config['project_dirs']['archive'])


def get_path_config() -> PathConfig:
    """
    Convenience function to get PathConfig instance.

    Returns:
        PathConfig instance

    Example:
        config = get_path_config()
        price_data = config.get_price_data_path()
    """
    return PathConfig()
