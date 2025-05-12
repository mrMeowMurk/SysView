"""
Main application module for sysview
"""
import time
import signal
import sys
import msvcrt
from rich.live import Live
from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.text import Text
import click

from .system import SystemStats
from .config import config
from .draw import Drawer
from .themes import THEMES

class SysView:
    def __init__(self, theme="default"):
        self.console = Console()
        self.stats = SystemStats(config)
        self.theme = THEMES.get(theme, THEMES["default"])
        self.drawer = Drawer(config, self.theme)
        self.layout = Layout()
        self.running = True
        self.paused = False
        self.current_layout = 0
        self.overlay = None
        self.process_sort_key = 'cpu_percent'
        self.process_sort_reverse = True
        self.process_filter = ''
        self.filter_buffer = ''
        self.selected_process = None
        self.overlay_time = 0
        self.overlay_duration = 3
        self.process_scroll = 0  # Текущая позиция прокрутки
        self.cached_stats = {
            'cpu': None,
            'memory': None,
            'disk': None,
            'network': None,
            'processes': None,
            'system': None,
            'battery': None
        }
        self.setup_layout()
        
    def setup_layout(self):
        """Setup the initial layout"""
        self.layout.split(
            Layout(name="header", size=3),
            Layout(name="main"),
            Layout(name="footer", size=3)
        )
        
        self.layout["main"].split_row(
            Layout(name="left", ratio=2),
            Layout(name="right", ratio=3),
        )
        
        self.layout["left"].split_column(
            Layout(name="cpu", ratio=2),
            Layout(name="memory", ratio=2),
            Layout(name="network", ratio=2),
            Layout(name="disks", ratio=3),
        )
        
        self.layout["right"].split_column(
            Layout(name="processes", ratio=1),
        )
        
        # Применяем стили темы
        self.layout["header"].style = self.theme["header"]
        self.layout["footer"].style = self.theme["footer"]
        self.layout["cpu"].style = self.theme["text"]
        self.layout["memory"].style = self.theme["text"]
        self.layout["network"].style = self.theme["text"]
        self.layout["disks"].style = self.theme["text"]
        self.layout["processes"].style = self.theme["text"]
        
    def handle_keyboard(self):
        """Handle keyboard input when available"""
        if msvcrt.kbhit():
            try:
                key = msvcrt.getch()
                if key == b'\xe0':  # Специальная клавиша
                    key = msvcrt.getch()
                    if key == b'H':  # Стрелка вверх
                        self.scroll_processes(-1)
                    elif key == b'P':  # Стрелка вниз
                        self.scroll_processes(1)
                    elif key == b'I':  # Page Up
                        self.scroll_processes(-10)
                    elif key == b'Q':  # Page Down
                        self.scroll_processes(10)
                else:
                    key = key.decode('utf-8').lower()
                    if key == 'q':
                        self.running = False
                    elif key == 'p':
                        self.toggle_pause()
                    elif key == 'h':
                        self.toggle_help()
                    elif key == 'm':
                        self.toggle_menu()
                    elif key == 's':
                        self.toggle_sort()
                    elif key == 'f':
                        self.toggle_process_filter()
                    elif key in '12345':
                        self.change_layout(int(key))
                    elif self.overlay and self.overlay['type'] == 'filter':
                        if key == '\r':  # Enter
                            self.process_filter = self.filter_buffer
                            self.overlay = None
                        elif key == '\x1b':  # Escape
                            self.overlay = None
                        elif key == '\x08':  # Backspace
                            self.filter_buffer = self.filter_buffer[:-1]
                        else:
                            self.filter_buffer += key
            except Exception:
                pass

    def scroll_processes(self, delta: int):
        """Scroll process list by delta amount"""
        self.process_scroll = max(0, self.process_scroll + delta)

    def quit(self):
        """Exit the application"""
        self.running = False
        
    def toggle_help(self):
        """Toggle help overlay"""
        if self.overlay and self.overlay['type'] == 'help':
            self.overlay = None
        else:
            help_text = """
            Горячие клавиши:
            q: Выход
            h: Показать/скрыть справку
            m: Показать/скрыть меню
            p: Поставить/возобновить паузу
            s: Сортировать процессы
            f: Фильтровать процессы
            1-5: Переключение layout'ов
            """
            self.show_overlay("Справка", help_text, 'help')
        
    def toggle_menu(self):
        """Toggle menu overlay"""
        if self.overlay and self.overlay['type'] == 'menu':
            self.overlay = None
        else:
            menu_text = """
            Меню:
            1. Изменить тему
            2. Настроить графики
            3. Настроить обновление
            4. Настроить фильтры
            """
            self.show_overlay("Меню", menu_text, 'menu')
        
    def toggle_pause(self):
        """Toggle pause state"""
        self.paused = not self.paused

    def toggle_sort(self):
        """Toggle process sorting between CPU and memory"""
        if self.process_sort_key == 'cpu_percent':
            self.process_sort_key = 'memory_percent'
        else:
            self.process_sort_key = 'cpu_percent'

    def toggle_process_filter(self):
        """Toggle process filter input"""
        if self.overlay and self.overlay['type'] == 'filter':
            self.overlay = None
        else:
            filter_text = """
            Enter process filter:
            (current: {})
            
            Press Enter to apply
            Press Esc to cancel
            """.format(self.process_filter or 'none')
            self.show_overlay("Filter Processes", filter_text, 'filter')

    def show_overlay(self, title: str, content: str, overlay_type: str):
        """Show an overlay panel"""
        self.overlay = {
            'panel': Panel(
                content.strip(),
                title=f"[bold cyan]{title}[/bold cyan]",
                border_style="cyan"
            ),
            'type': overlay_type,
            'time': time.time()
        }

    def change_layout(self, layout_num: int):
        """Change current layout preset"""
        self.current_layout = layout_num - 1
        layouts = config.get("presets", [])
        if 0 <= self.current_layout < len(layouts):
            # Apply layout configuration
            pass

    def update(self):
        """Update the display"""
        # Получаем или используем кэшированные данные
        if not self.paused:
            self.cached_stats.update({
                'cpu': self.stats.get_cpu_stats(),
                'memory': self.stats.get_memory_stats(),
                'disk': self.stats.get_disk_stats(),
                'network': self.stats.get_network_stats(),
                'processes': self.stats.get_process_stats(),
                'system': self.stats.get_system_info(),
                'battery': self.stats.get_battery_info()
            })

        # Используем кэшированные данные
        cpu_stats = self.cached_stats['cpu']
        mem_stats = self.cached_stats['memory']
        disk_stats = self.cached_stats['disk']
        net_stats = self.cached_stats['network']
        proc_stats = self.cached_stats['processes']
        sys_info = self.cached_stats['system']
        battery = self.cached_stats['battery']

        # Update layout sections
        self.layout["header"].update(
            Panel(
                f"SysView - {sys_info['hostname']} - Uptime: {int(sys_info['uptime'] // 3600)}h {int((sys_info['uptime'] % 3600) // 60)}m" +
                (" [bold red](PAUSED)[/]" if self.paused else ""),
                style=self.theme["header"]
            )
        )

        # Если есть активный оверлей, показываем его поверх основного контента
        if self.overlay:
            if self.overlay['type'] == 'filter':
                self.overlay['panel'] = Panel(
                    f"""
                    Enter process filter:
                    (current: {self.filter_buffer or 'none'})
                    
                    Press Enter to apply
                    Press Esc to cancel
                    """.strip(),
                    title=f"[{self.theme['highlight']}]Filter Processes: {self.filter_buffer}[/]",
                    border_style=self.theme['border']
                )
            return self.overlay['panel']

        self.layout["cpu"].update(
            self.drawer.draw_cpu(cpu_stats)
        )

        self.layout["memory"].update(
            self.drawer.draw_memory(mem_stats)
        )

        self.layout["network"].update(
            self.drawer.draw_network(net_stats)
        )

        self.layout["disks"].update(
            self.drawer.draw_disks(disk_stats)
        )

        # Фильтруем и сортируем процессы
        if self.process_filter:
            proc_stats = [p for p in proc_stats if self.process_filter.lower() in p['name'].lower()]
        
        self.layout["processes"].update(
            self.drawer.draw_processes(proc_stats, self.process_scroll)
        )

        if battery:
            battery_text = f"🔋 {battery['percent']}% {'🔌' if battery['power_plugged'] else ''}"
        else:
            battery_text = ""

        # Добавляем информацию о горячих клавишах в футер
        keys_help = [
            "q:Quit",
            "h:Help",
            "m:Menu",
            "p:Pause",
            "s:Sort",
            "f:Filter"
        ]
        
        self.layout["footer"].update(
            Panel(
                f"{battery_text} | {' | '.join(keys_help)}",
                style=self.theme["footer"]
            )
        )

        return self.layout

@click.command()
@click.option('-i', '--interval', default=1.0, help='Интервал обновления в секундах')
@click.option('-t', '--theme', default='default', help='Тема оформления')
def main(interval: float, theme: str):
    """System resource monitor"""
    def signal_handler(sig, frame):
        app.running = False
    
    signal.signal(signal.SIGINT, signal_handler)
    
    config.set("color_theme", theme)
    app = SysView(theme)
    
    with Live(
        app.update(),
        refresh_per_second=1/interval,
        screen=True,  # Use alternate screen
        transient=True  # Prevent flickering
    ) as live:
        while app.running:
            app.handle_keyboard()  # Обработка клавиатуры
            live.update(app.update())
            time.sleep(interval)

if __name__ == "__main__":
    main() 