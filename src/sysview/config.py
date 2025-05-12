"""
Configuration module for sysview
"""
from pathlib import Path
import json

DEFAULT_CONFIG = {
    "color_theme": "default",
    "theme_background": True,
    "truecolor": True,
    "shown_boxes": ["cpu", "mem", "net", "proc"],
    "update_ms": 1500,
    "proc_sorting": "cpu lazy",
    "proc_reversed": False,
    "proc_tree": False,
    "proc_colors": True,
    "proc_gradient": True,
    "proc_per_core": True,
    "proc_mem_bytes": True,
    "cpu_graph_upper": "total",
    "cpu_graph_lower": "total",
    "cpu_invert_lower": True,
    "cpu_single_graph": False,
    "show_uptime": True,
    "check_temp": True,
    "cpu_sensor": "Auto",
    "show_coretemp": True,
    "temp_scale": "celsius",
    "base_10_sizes": False,
    "show_cpu_freq": True,
    "clock_format": "%H:%M",
    "background_update": True,
    "custom_cpu_name": "",
    "disks_filter": "exclude=/boot",
    "mem_graphs": True,
    "show_swap": True,
    "swap_disk": True,
    "show_disks": True,
    "only_physical": True,
    "use_fstab": False,
    "show_io_stat": True,
    "io_mode": False,
    "io_graph_combined": False,
    "io_graph_speeds": "",
    "net_download": 100,
    "net_upload": 100,
    "net_auto": True,
    "net_sync": False,
    "net_iface": "Auto",
    "show_battery": True,
    "graph_symbol": "braille",  # braille, block, or tty
    "graph_symbol_cpu": "default",
    "graph_symbol_mem": "default",
    "graph_symbol_net": "default",
    "graph_symbol_proc": "default",
    "rounded_corners": True,
    "vim_keys": False
}

class Config:
    def __init__(self):
        self.config_dir = Path.home() / ".config" / "sysview"
        self.config_file = self.config_dir / "sysview.conf"
        self.config = DEFAULT_CONFIG.copy()
        self._load_config()

    def _load_config(self):
        """Load configuration from file"""
        if not self.config_dir.exists():
            self.config_dir.mkdir(parents=True)
        
        if self.config_file.exists():
            try:
                with open(self.config_file, "r") as f:
                    loaded_config = json.load(f)
                    self.config.update(loaded_config)
            except Exception:
                self.save_config()
        else:
            self.save_config()

    def save_config(self):
        """Save current configuration to file"""
        with open(self.config_file, "w") as f:
            json.dump(self.config, f, indent=4)

    def get(self, key, default=None):
        """Get configuration value"""
        return self.config.get(key, default)

    def set(self, key, value):
        """Set configuration value and save"""
        if key in self.config:
            self.config[key] = value
            self.save_config()

config = Config() 