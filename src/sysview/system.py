"""
System information gathering module
"""
import psutil
import time
from typing import Dict, List, Optional, Tuple
from collections import deque
import platform

class SystemStats:
    def __init__(self, config):
        self.config = config
        self.cpu_history = deque(maxlen=100)
        self.memory_history = deque(maxlen=100)
        self.net_history = deque(maxlen=100)
        self.last_net_io = None
        self.last_disk_io = {}
        self.last_cpu_percent = None
        self.process_cpu_history = {}
        self.prev_net_io = psutil.net_io_counters()
        self.prev_time = time.time()
        self.peak_send_speed = 0
        self.peak_recv_speed = 0
        self.update_interval = 1.0  # seconds

    def get_cpu_stats(self) -> Dict:
        """Get CPU statistics"""
        cpu_percent = psutil.cpu_percent(interval=0.1)
        per_cpu = psutil.cpu_percent(interval=0.1, percpu=True)
        
        try:
            freq = psutil.cpu_freq()
            freq_current = freq.current if freq else 0
            freq_min = freq.min if freq else 0
            freq_max = freq.max if freq else 0
        except Exception:
            freq_current = freq_min = freq_max = 0

        # Get CPU temperature if available
        temp = None
        if self.config.get("check_temp"):
            try:
                temps = psutil.sensors_temperatures()
                if temps:
                    for name, entries in temps.items():
                        if name.lower() in ['coretemp', 'cpu_thermal', 'k10temp']:
                            temp = entries[0].current
                            break
            except Exception:
                pass

        self.cpu_history.append(cpu_percent)
        
        return {
            'total': cpu_percent,
            'per_cpu': per_cpu,
            'freq_current': freq_current,
            'freq_min': freq_min,
            'freq_max': freq_max,
            'temp': temp,
            'history': list(self.cpu_history)
        }

    def get_memory_stats(self) -> Dict:
        """Get detailed memory statistics"""
        mem = psutil.virtual_memory()
        swap = psutil.swap_memory()
        
        # Добавляем значение в историю
        self.memory_history.append(mem.percent)
        if len(self.memory_history) > 100:
            self.memory_history.pop(0)
            
        return {
            'total': mem.total,
            'available': mem.available,
            'used': mem.used,
            'free': mem.free,
            'percent': mem.percent,
            'cached': getattr(mem, 'cached', None),  # Может отсутствовать в Windows
            'buffers': getattr(mem, 'buffers', None),  # Может отсутствовать в Windows
            'swap_total': swap.total,
            'swap_used': swap.used,
            'swap_free': swap.free,
            'swap_percent': swap.percent,
            'history': self.memory_history
        }

    def get_disk_stats(self) -> List[Dict]:
        """Get disk statistics"""
        disks = []
        
        if platform.system() == 'Windows':
            # Получаем все доступные буквы дисков в Windows
            import string
            import ctypes
            
            # Получаем битовую маску подключенных дисков
            bitmask = ctypes.windll.kernel32.GetLogicalDrives()
            
            # Проверяем каждую букву диска
            for letter in string.ascii_uppercase:
                if bitmask & (1 << (ord(letter) - ord('A'))):
                    drive = f"{letter}:\\"
                    try:
                        # Проверяем, готов ли диск
                        usage = psutil.disk_usage(drive)
                        
                        # Получаем тип диска
                        drive_type = ctypes.windll.kernel32.GetDriveTypeW(drive)
                        drive_types = {
                            0: "Unknown",
                            1: "Invalid",
                            2: "Removable",
                            3: "Fixed",
                            4: "Network",
                            5: "CDROM",
                            6: "RAM disk"
                        }
                        drive_type_str = drive_types.get(drive_type, "Unknown")
                        
                        # Получаем метку диска
                        try:
                            volume_info = psutil.disk_partitions(all=True)
                            for part in volume_info:
                                if part.device.startswith(drive[0]):
                                    label = part.mountpoint
                                    break
                            else:
                                label = f"Disk {letter}"
                        except:
                            label = f"Disk {letter}"
                        
                        disk_data = {
                            'device': drive,
                            'mountpoint': drive,
                            'fstype': 'NTFS',
                            'label': label,
                            'type': drive_type_str,
                            'total': usage.total,
                            'used': usage.used,
                            'free': usage.free,
                            'percent': usage.percent
                        }
                        
                        # Получаем информацию о I/O
                        try:
                            io = psutil.disk_io_counters(perdisk=True)
                            for disk_name, disk_io in io.items():
                                if disk_name.lower().startswith(letter.lower()):
                                    disk_data.update({
                                        'read_bytes': disk_io.read_bytes,
                                        'write_bytes': disk_io.write_bytes,
                                        'read_count': disk_io.read_count,
                                        'write_count': disk_io.write_count
                                    })
                                    break
                        except:
                            pass

                        disks.append(disk_data)
                    except:
                        continue
        else:
            # Linux/Unix логика
            for partition in psutil.disk_partitions(all=True):
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    
                    disk_data = {
                        'device': partition.device,
                        'mountpoint': partition.mountpoint,
                        'fstype': partition.fstype,
                        'label': partition.mountpoint,
                        'type': 'Fixed',
                        'total': usage.total,
                        'used': usage.used,
                        'free': usage.free,
                        'percent': usage.percent
                    }

                    try:
                        io = psutil.disk_io_counters(perdisk=True)
                        device_name = partition.device.split('/')[-1]
                        if device_name in io:
                            disk_data.update({
                                'read_bytes': io[device_name].read_bytes,
                                'write_bytes': io[device_name].write_bytes,
                                'read_count': io[device_name].read_count,
                                'write_count': io[device_name].write_count
                            })
                    except:
                        pass

                    disks.append(disk_data)
                except:
                    continue

        return disks

    def get_network_stats(self) -> Dict:
        """Get detailed network statistics with peak speeds"""
        current_net_io = psutil.net_io_counters()
        current_time = time.time()
        
        # Вычисляем скорости
        time_delta = current_time - self.prev_time
        bytes_sent = current_net_io.bytes_sent - self.prev_net_io.bytes_sent
        bytes_recv = current_net_io.bytes_recv - self.prev_net_io.bytes_recv
        
        send_speed = bytes_sent / time_delta
        recv_speed = bytes_recv / time_delta
        
        # Обновляем пиковые скорости
        self.peak_send_speed = max(self.peak_send_speed, send_speed)
        self.peak_recv_speed = max(self.peak_recv_speed, recv_speed)
        
        # Добавляем значения в историю
        self.net_history.append((send_speed, recv_speed))
        if len(self.net_history) > 100:
            self.net_history.pop(0)
            
        # Сохраняем значения для следующего вычисления
        self.prev_net_io = current_net_io
        self.prev_time = current_time
        
        return {
            'bytes_sent': current_net_io.bytes_sent,
            'bytes_recv': current_net_io.bytes_recv,
            'packets_sent': current_net_io.packets_sent,
            'packets_recv': current_net_io.packets_recv,
            'send_speed': send_speed,
            'recv_speed': recv_speed,
            'peak_send_speed': self.peak_send_speed,
            'peak_recv_speed': self.peak_recv_speed,
            'history': list(self.net_history)
        }

    def get_process_stats(self) -> List[Dict]:
        """Get process statistics"""
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'username', 'cpu_percent', 'memory_percent', 
                                       'create_time', 'status', 'num_threads']):
            try:
                pinfo = proc.info
                pid = pinfo['pid']
                
                # Update CPU history for process
                if pid not in self.process_cpu_history:
                    self.process_cpu_history[pid] = deque(maxlen=10)
                self.process_cpu_history[pid].append(pinfo['cpu_percent'])
                
                pinfo['cpu_history'] = list(self.process_cpu_history[pid])
                
                # Get memory info
                try:
                    mem_info = proc.memory_info()
                    pinfo['memory_rss'] = mem_info.rss
                    pinfo['memory_vms'] = mem_info.vms
                except Exception:
                    pinfo['memory_rss'] = 0
                    pinfo['memory_vms'] = 0
                
                # Get command line
                try:
                    pinfo['cmdline'] = ' '.join(proc.cmdline())
                except Exception:
                    pinfo['cmdline'] = ''
                
                processes.append(pinfo)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
            
        # Clean up process history for dead processes
        current_pids = {p['pid'] for p in processes}
        dead_pids = set(self.process_cpu_history.keys()) - current_pids
        for pid in dead_pids:
            del self.process_cpu_history[pid]
            
        return processes

    def get_system_info(self) -> Dict:
        """Get general system information"""
        boot_time = psutil.boot_time()
        uptime = time.time() - boot_time
        
        return {
            'hostname': platform.node(),
            'platform': platform.system(),
            'platform_release': platform.release(),
            'platform_version': platform.version(),
            'architecture': platform.machine(),
            'processor': platform.processor(),
            'boot_time': boot_time,
            'uptime': uptime
        }

    def get_battery_info(self) -> Optional[Dict]:
        """Get battery information if available"""
        try:
            battery = psutil.sensors_battery()
            if battery:
                return {
                    'percent': battery.percent,
                    'power_plugged': battery.power_plugged,
                    'seconds_left': battery.secsleft if battery.secsleft != psutil.POWER_TIME_UNLIMITED else None
                }
        except Exception:
            pass
        return None 