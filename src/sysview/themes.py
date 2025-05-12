"""
Color themes for sysview
"""
from typing import Dict

THEMES: Dict[str, Dict[str, str]] = {
    "default": {
        "header": "white on blue",
        "footer": "white on blue",
        "border": "white",
        "title": "white",
        "text": "white",
        "highlight": "cyan",
        "cpu": "blue",
        "memory": "magenta",
        "network": "green",
        "disk": "yellow",
        "process": "cyan",
        "graph": "blue",
        "progress_low": "green",
        "progress_medium": "yellow",
        "progress_high": "red"
    },
    "nord": {
        "header": "black on cyan",
        "footer": "black on cyan",
        "border": "#81A1C1",  # Nord Frost
        "title": "#88C0D0",   # Nord Frost
        "text": "#D8DEE9",    # Nord Snow
        "highlight": "#81A1C1",# Nord Frost
        "cpu": "#5E81AC",     # Nord Frost
        "memory": "#B48EAD",  # Nord Purple
        "network": "#A3BE8C", # Nord Green
        "disk": "#EBCB8B",    # Nord Yellow
        "process": "#88C0D0", # Nord Frost
        "graph": "#81A1C1",   # Nord Frost
        "progress_low": "#A3BE8C",    # Nord Green
        "progress_medium": "#EBCB8B",  # Nord Yellow
        "progress_high": "#BF616A"     # Nord Red
    },
    "dracula": {
        "header": "white on purple",
        "footer": "white on purple",
        "border": "#BD93F9",  # Purple
        "title": "#FF79C6",   # Pink
        "text": "#F8F8F2",    # Foreground
        "highlight": "#8BE9FD",# Cyan
        "cpu": "#BD93F9",     # Purple
        "memory": "#FF79C6",  # Pink
        "network": "#50FA7B", # Green
        "disk": "#F1FA8C",   # Yellow
        "process": "#8BE9FD", # Cyan
        "graph": "#BD93F9",   # Purple
        "progress_low": "#50FA7B",    # Green
        "progress_medium": "#FFB86C",  # Orange
        "progress_high": "#FF5555"     # Red
    },
    "gruvbox": {
        "header": "black on yellow",
        "footer": "black on yellow",
        "border": "#928374",  # Gray
        "title": "#b8bb26",   # Green
        "text": "#ebdbb2",    # Light
        "highlight": "#83a598",# Blue
        "cpu": "#458588",     # Blue
        "memory": "#b16286",  # Purple
        "network": "#98971a", # Green
        "disk": "#d79921",   # Yellow
        "process": "#83a598", # Blue
        "graph": "#928374",   # Gray
        "progress_low": "#98971a",    # Green
        "progress_medium": "#d79921",  # Yellow
        "progress_high": "#cc241d"     # Red
    }
} 