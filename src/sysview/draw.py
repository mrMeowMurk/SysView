"""
Drawing utilities for sysview
"""
from rich.style import Style
from rich.progress import ProgressBar
from rich.table import Table
from rich.panel import Panel
from rich import box
from rich.text import Text
from typing import List, Dict, Union, Optional
import time

class Drawer:
    BRAILLE_CHARS = [
        '⠀', '⠁', '⠂', '⠃', '⠄', '⠅', '⠆', '⠇',
        '⠈', '⠉', '⠊', '⠋', '⠌', '⠍', '⠎', '⠏',
        '⠐', '⠑', '⠒', '⠓', '⠔', '⠕', '⠖', '⠗',
        '⠘', '⠙', '⠚', '⠛', '⠜', '⠝', '⠞', '⠟',
        '⠠', '⠡', '⠢', '⠣', '⠤', '⠥', '⠦', '⠧',
        '⠨', '⠩', '⠪', '⠫', '⠬', '⠭', '⠮', '⠯',
        '⠰', '⠱', '⠲', '⠳', '⠴', '⠵', '⠶', '⠷',
        '⠸', '⠹', '⠺', '⠻', '⠼', '⠽', '⠾', '⠿'
    ]

    BLOCK_CHARS = ['▁', '▂', '▃', '▄', '▅', '▆', '▇', '█']
    TTY_CHARS = ['_', '▄', '█']

    def __init__(self, config, theme):
        self.config = config
        self.theme = theme
        self.graph_chars = {
            'braille': self.BRAILLE_CHARS,
            'block': self.BLOCK_CHARS,
            'tty': self.TTY_CHARS
        }
        self.graph_width = 50
        self.graph_history = {}

    def _format_bytes(self, bytes: Optional[int]) -> str:
        """Format bytes to human readable format"""
        if bytes is None:
            return "N/A"
            
        bytes = float(bytes)
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes < 1024:
                return f"{bytes:.1f}{unit}"
            bytes /= 1024
        return f"{bytes:.1f}PB"
        
    def _format_speed(self, bytes_per_sec: float) -> str:
        """Format network speed"""
        return f"{self._format_bytes(bytes_per_sec)}/s"

    def create_table(self, title: str) -> Table:
        """Create a styled table"""
        return Table(
            title=f"[bold cyan]{title}[/bold cyan]",
            box=box.ROUNDED if self.config.get("rounded_corners") else box.SQUARE,
            title_style=Style(color="cyan", bold=True),
            header_style=Style(color="magenta", bold=True),
            expand=True
        )

    def create_progress_bar(self, value: float, total: float = 100, width: int = 25) -> ProgressBar:
        """Create a styled progress bar"""
        style = Style(color="red" if value > 80 else "yellow" if value > 60 else "green")
        return ProgressBar(value, total, width=width, style=style)

    def create_graph(self, values: List[float], width: int = 30, height: int = 8) -> List[str]:
        """Create a graph using braille, block or tty characters"""
        graph_type = self.config.get("graph_symbol", "braille")
        chars = self.graph_chars[graph_type]
        
        if not values:
            return [" " * width] * height

        # Convert deque to list and get the last 'width' values
        values_list = list(values)
        if len(values_list) > width:
            values_list = values_list[-width:]

        # Normalize values to height
        max_val = max(values_list)
        if max_val == 0:
            return [" " * width] * height

        # Pad with zeros if not enough values
        if len(values_list) < width:
            values_list = [0] * (width - len(values_list)) + values_list

        # Create the graph
        normalized = [min(height - 1, int((v / max_val) * height)) for v in values_list]
        
        graph = []
        for y in range(height - 1, -1, -1):
            line = ""
            for x in range(width):
                val = normalized[x]
                if val >= y:
                    line += chars[-1]
                else:
                    line += chars[0]
            graph.append(line)

        return graph

    def format_size(self, size: float) -> str:
        """Format size in bytes to human readable format"""
        base = 1000 if self.config.get("base_10_sizes") else 1024
        units = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']
        
        for unit in units:
            if size < base:
                return f"{size:.1f} {unit}"
            size /= base
        return f"{size:.1f} {units[-1]}"

    def draw_cpu(self, stats: Dict) -> Panel:
        """Draw CPU section with history graph"""
        # Создаем таблицу с двумя колонками: информация и график
        layout = Table.grid(expand=True)
        layout.add_column("info", ratio=2)
        layout.add_column("graph", ratio=3)
        
        # Колонка с информацией
        cpu_table = Table(box=box.SIMPLE, expand=True, show_header=False)
        cpu_table.add_column("Name")
        cpu_table.add_column("Usage", justify="right")
        cpu_table.add_column("Bar")
        
        # Total CPU
        progress = ProgressBar(total=100, completed=stats['total'], 
                             style="red" if stats['total'] > 90 else "yellow" if stats['total'] > 70 else "green")
        cpu_table.add_row("Total CPU", f"{stats['total']}%", progress)
        
        # Per CPU cores
        for i, usage in enumerate(stats['per_cpu']):
            progress = ProgressBar(total=100, completed=usage, 
                                 style="red" if usage > 90 else "yellow" if usage > 70 else "blue")
            cpu_table.add_row(f"Core {i}", f"{usage}%", progress)
        
        # Колонка с графиком
        history_graph = self.create_graph(stats['history'], width=50, height=10)
        graph = "\n".join(history_graph)
        
        # Добавляем информацию и график в layout
        layout.add_row(cpu_table, Text(graph))
        
        # Добавляем информацию о частоте и температуре
        info_text = []
        if stats.get('freq_current'):
            info_text.append(f"Frequency: {stats['freq_current']:.1f}MHz")
        if stats.get('temp'):
            temp = stats['temp']
            temp_style = "red" if temp > 80 else "yellow" if temp > 60 else "green"
            info_text.append(f"Temperature: [{temp_style}]{temp}°C[/]")
        
        return Panel(
            layout,
            title="[bold blue]CPU[/bold blue]",
            subtitle=" | ".join(info_text) if info_text else None,
            border_style="blue"
        )
        
    def draw_memory(self, stats: Dict) -> Panel:
        """Draw memory section with detailed information and history graph"""
        layout = Table.grid(expand=True)
        layout.add_column("info", ratio=2)
        layout.add_column("graph", ratio=3)
        
        # Колонка с информацией
        mem_table = Table(box=box.SIMPLE, expand=True, show_header=False)
        mem_table.add_column("Type")
        mem_table.add_column("Usage", justify="right")
        mem_table.add_column("Bar")
        
        # RAM с детальной информацией
        ram_text = f"{self._format_bytes(stats['used'])} / {self._format_bytes(stats['total'])}"
        ram_progress = ProgressBar(total=100, completed=stats['percent'],
                                 style="red" if stats['percent'] > 90 else "yellow" if stats['percent'] > 70 else "green")
        mem_table.add_row("RAM", ram_text, ram_progress)
        
        # Добавляем детальную информацию о памяти
        available_text = f"Available: {self._format_bytes(stats['available'])}"
        mem_table.add_row("", available_text, "")

        # Добавляем информацию о кэше и буферах только если они доступны
        if stats.get('cached') is not None:
            cached_text = f"Cached: {self._format_bytes(stats['cached'])}"
            mem_table.add_row("", cached_text, "")
            
        if stats.get('buffers') is not None:
            buffers_text = f"Buffers: {self._format_bytes(stats['buffers'])}"
            mem_table.add_row("", buffers_text, "")
        
        # Swap с процентами
        if stats['swap_total'] > 0:
            swap_text = f"{self._format_bytes(stats['swap_used'])} / {self._format_bytes(stats['swap_total'])}"
            swap_progress = ProgressBar(total=100, completed=stats['swap_percent'],
                                      style="red" if stats['swap_percent'] > 50 else "yellow" if stats['swap_percent'] > 25 else "blue")
            mem_table.add_row("Swap", swap_text, swap_progress)
            swap_free = f"Free: {self._format_bytes(stats['swap_total'] - stats['swap_used'])}"
            mem_table.add_row("", swap_free, "")
        
        # График использования памяти
        history_graph = self.create_graph(stats['history'], width=50, height=8)
        graph_panel = Panel(
            Text("\n".join(history_graph)),
            title="[blue]Memory Usage History[/blue]",
            border_style="blue"
        )
        
        # Добавляем информацию и график в layout
        layout.add_row(mem_table, graph_panel)
        
        return Panel(
            layout,
            title="[bold magenta]Memory[/bold magenta]",
            subtitle=f"Used: {stats['percent']}% of {self._format_bytes(stats['total'])}",
            border_style="magenta"
        )
        
    def draw_network(self, stats: Dict) -> Panel:
        """Draw network section with detailed statistics"""
        layout = Table.grid(expand=True)
        layout.add_column("info", ratio=2)
        layout.add_column("graph", ratio=3)
        
        # Колонка с информацией
        net_table = Table(box=box.SIMPLE, expand=True, show_header=False)
        net_table.add_column("Type", width=12)
        net_table.add_column("Current", justify="right")
        net_table.add_column("Total", justify="right")
        net_table.add_column("Packets", justify="right")
        
        # Upload statistics
        up_speed = stats['send_speed']
        up_style = "red" if up_speed > 1024*1024*10 else "yellow" if up_speed > 1024*1024 else "green"
        net_table.add_row(
            "[bold green]Upload ↑[/]",
            f"[{up_style}]{self._format_speed(up_speed)}[/]",
            self._format_bytes(stats['bytes_sent']),
            f"{stats['packets_sent']:,}"
        )
        
        # Download statistics
        down_speed = stats['recv_speed']
        down_style = "red" if down_speed > 1024*1024*10 else "yellow" if down_speed > 1024*1024 else "green"
        net_table.add_row(
            "[bold blue]Download ↓[/]",
            f"[{down_style}]{self._format_speed(down_speed)}[/]",
            self._format_bytes(stats['bytes_recv']),
            f"{stats['packets_recv']:,}"
        )
        
        # Добавляем информацию о пиковых скоростях
        if 'peak_send_speed' in stats:
            net_table.add_row(
                "Peak Upload",
                self._format_speed(stats['peak_send_speed']),
                "", ""
            )
        if 'peak_recv_speed' in stats:
            net_table.add_row(
                "Peak Download",
                self._format_speed(stats['peak_recv_speed']),
                "", ""
            )
        
        # Создаем графики для загрузки и скачивания
        upload_history = [x[0] for x in stats['history']]
        download_history = [x[1] for x in stats['history']]
        
        # График загрузки
        up_graph = self.create_graph(upload_history, width=50, height=4)
        up_panel = Panel(
            Text("\n".join(up_graph)),
            title="[green]Upload History[/green]",
            border_style="green"
        )
        
        # График скачивания
        down_graph = self.create_graph(download_history, width=50, height=4)
        down_panel = Panel(
            Text("\n".join(down_graph)),
            title="[blue]Download History[/blue]",
            border_style="blue"
        )
        
        # Объединяем графики в одну панель
        graphs_layout = Table.grid()
        graphs_layout.add_row(up_panel)
        graphs_layout.add_row(down_panel)
        
        # Добавляем информацию и графики в layout
        layout.add_row(net_table, graphs_layout)
        
        # Вычисляем общую скорость для подзаголовка
        total_speed = self._format_speed(up_speed + down_speed)
        
        return Panel(
            layout,
            title="[bold green]Network[/bold green]",
            subtitle=f"Total Speed: {total_speed}",
            border_style="green"
        )
        
    def draw_disks(self, stats: List[Dict]) -> Panel:
        """Draw disks section"""
        disk_table = Table(box=box.SIMPLE, expand=True)
        disk_table.add_column("Drive")
        disk_table.add_column("Label")
        disk_table.add_column("Type", justify="center")
        disk_table.add_column("Usage", justify="right")
        disk_table.add_column("Free", justify="right")
        disk_table.add_column("Total", justify="right")
        
        for disk in stats:
            # Создаем прогресс-бар для использования
            progress = ProgressBar(
                total=100,
                completed=disk['percent'],
                style="red" if disk['percent'] > 90 else "yellow" if disk['percent'] > 70 else "green"
            )
            
            # Получаем тип диска и его цвет
            disk_type = disk.get('type', 'Unknown')
            type_colors = {
                'Fixed': 'green',
                'Removable': 'yellow',
                'Network': 'blue',
                'CDROM': 'magenta',
                'RAM disk': 'cyan'
            }
            type_color = type_colors.get(disk_type, 'white')
            
            disk_table.add_row(
                disk['mountpoint'],
                disk.get('label', ''),
                f"[{type_color}]{disk_type}[/{type_color}]",
                progress,
                self._format_bytes(disk['free']),
                self._format_bytes(disk['total'])
            )
            
        return Panel(
            disk_table,
            title="[bold yellow]Disks[/bold yellow]",
            border_style="yellow"
        )
        
    def draw_processes(self, stats: List[Dict], scroll_position: int = 0) -> Panel:
        """Draw processes section with scrolling support"""
        proc_table = Table(box=box.SIMPLE, expand=True)
        proc_table.add_column("PID", justify="right", style="dim")
        proc_table.add_column("Name", width=30)
        proc_table.add_column("CPU%", justify="right")
        proc_table.add_column("MEM%", justify="right")
        proc_table.add_column("Status", width=10)
        proc_table.add_column("Threads", justify="right", width=8)
        
        # Sort by CPU usage
        sorted_procs = sorted(stats, key=lambda x: x['cpu_percent'], reverse=True)
        
        # Calculate visible range based on scroll position
        start_idx = scroll_position
        end_idx = min(start_idx + 30, len(sorted_procs))
        
        # Adjust scroll position if needed
        if start_idx >= len(sorted_procs):
            start_idx = max(0, len(sorted_procs) - 30)
            end_idx = len(sorted_procs)
        
        for proc in sorted_procs[start_idx:end_idx]:
            status_style = {
                'running': self.theme['progress_low'],
                'sleeping': self.theme['cpu'],
                'stopped': self.theme['progress_high'],
                'zombie': self.theme['progress_high'],
                'disk-sleep': self.theme['progress_medium'],
                'tracing-stop': self.theme['progress_medium'],
            }.get(proc['status'].lower(), self.theme['text'])
            
            # Форматируем имя процесса
            name = proc['name']
            if len(name) > 30:
                name = name[:27] + "..."
            
            # Определяем стиль для значений CPU и Memory
            cpu_value = proc['cpu_percent']
            mem_value = proc['memory_percent']
            
            cpu_style = (
                self.theme['progress_high'] if cpu_value > 50 else
                self.theme['progress_medium'] if cpu_value > 20 else
                self.theme['progress_low']
            )
            
            mem_style = (
                self.theme['progress_high'] if mem_value > 50 else
                self.theme['progress_medium'] if mem_value > 20 else
                self.theme['progress_low']
            )
            
            proc_table.add_row(
                str(proc['pid']),
                name,
                f"[{cpu_style}]{cpu_value:.1f}[/]",
                f"[{mem_style}]{mem_value:.1f}[/]",
                Text(proc['status'], style=status_style),
                str(proc.get('num_threads', 'N/A'))
            )
        
        total_procs = len(sorted_procs)
        shown_range = f"{start_idx + 1}-{end_idx}"
        
        return Panel(
            proc_table,
            title=f"[{self.theme['title']}]Processes[/]",
            subtitle=f"Showing {shown_range} of {total_procs} processes (↑↓ to scroll, PgUp/PgDn for faster scroll)",
            border_style=self.theme['border']
        )