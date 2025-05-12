"""
Theme loader for sysview
"""
import os
import configparser
from typing import Dict, Optional

class ThemeLoader:
    def __init__(self, themes_dir: str = "themes"):
        self.themes_dir = themes_dir
        self.themes: Dict[str, Dict[str, Dict[str, str]]] = {}
        self.load_themes()

    def load_themes(self):
        """Load all theme files from themes directory"""
        if not os.path.exists(self.themes_dir):
            return

        for file in os.listdir(self.themes_dir):
            if file.endswith('.theme'):
                theme_name = os.path.splitext(file)[0]
                theme_path = os.path.join(self.themes_dir, file)
                self.themes[theme_name] = self.load_theme_file(theme_path)

    def load_theme_file(self, path: str) -> Dict[str, Dict[str, str]]:
        """Load a single theme file"""
        config = configparser.ConfigParser()
        config.read(path)

        theme = {}
        colors = {}

        # Загружаем основные цвета
        if 'main' in config:
            colors = dict(config['main'])

        # Загружаем настройки для каждой секции
        for section in config.sections():
            if section != 'main':
                section_name = section.replace('theme[', '').replace(']', '')
                theme[section_name] = {}
                for key, value in config[section].items():
                    # Если значение ссылается на цвет из main, используем его
                    theme[section_name][key] = colors.get(value, value)

        return theme

    def get_theme(self, name: str) -> Optional[Dict[str, Dict[str, str]]]:
        """Get theme by name"""
        return self.themes.get(name)

    def get_theme_names(self) -> list:
        """Get list of available themes"""
        return list(self.themes.keys())

    def convert_to_rich_theme(self, theme: Dict[str, Dict[str, str]]) -> Dict[str, str]:
        """Convert theme to format compatible with Rich"""
        rich_theme = {
            "header": f"black on {theme['main'].get('cyan', '#88c0d0')}",
            "footer": f"black on {theme['main'].get('cyan', '#88c0d0')}",
            "border": theme['main'].get('foreground', '#d8dee9'),
            "title": theme['main'].get('cyan', '#88c0d0'),
            "text": theme['main'].get('foreground', '#d8dee9'),
            "highlight": theme['main'].get('cyan', '#88c0d0'),
            "cpu": theme['cpu'].get('border', '#81a1c1'),
            "memory": theme['mem'].get('border', '#b48ead'),
            "network": theme['net'].get('border', '#a3be8c'),
            "disk": theme['disk'].get('border', '#ebcb8b'),
            "process": theme['proc'].get('border', '#88c0d0'),
            "graph": theme['main'].get('blue', '#81a1c1'),
            "progress_low": theme['main'].get('green', '#a3be8c'),
            "progress_medium": theme['main'].get('yellow', '#ebcb8b'),
            "progress_high": theme['main'].get('red', '#bf616a')
        }
        return rich_theme 