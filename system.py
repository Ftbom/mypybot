import time
import psutil
import platform

def system_info():
    info = {}
    info['platform'] = platform.system()
    info['platform-release'] = platform.release()
    info['platform-version'] = platform.version()
    info['processor'] = platform.processor()
    info['ram'] = f"{int(psutil.virtual_memory().total / (1024.0 ** 3) * 10) / 10} GB"
    return f'''<b>系统</b>：{info['platform']}\n<b>发行版</b>：{info['platform-version']}\n<b>版本</b>：{info['platform-release']}
<b>处理器</b>：{info['processor']}\n<b>总内存</b>：{info['ram']}'''

def system_status():
    cpu_times = psutil.cpu_times()
    cpu_percent = psutil.cpu_percent(interval = 0.5)
    virtual_memory = psutil.virtual_memory()
    swap_memory = psutil.swap_memory()
    disk_usage = psutil.disk_usage('/')
    net_io_counter_last = psutil.net_io_counters()
    time.sleep(0.5)
    net_io_counter_now = psutil.net_io_counters()
    bytes_sent_speed = (net_io_counter_now.bytes_sent - net_io_counter_last.bytes_sent) / 0.5
    bytes_recv_speed = (net_io_counter_now.bytes_recv - net_io_counter_last.bytes_recv) / 0.5
    if (bytes_sent_speed >= 1024 ** 2):
        sent_speed = f"{int(bytes_sent_speed / (1024 ** 2) * 1000) / 1000}MB/s"
    else:
        sent_speed = f"{int(bytes_sent_speed / 1024 * 1000) / 1000}KB/s"
    if (bytes_recv_speed >= 1024 ** 2):
        recv_speed = f"{int(bytes_recv_speed / (1024 ** 2) * 1000) / 1000}MB/s"
    else:
        recv_speed = f"{int(bytes_recv_speed / 1024 * 1000) / 1000}KB/s"
    return f'''<b>CPU时间</b>\n开机时间：{psutil.boot_time()}s 系统：{cpu_times.system}s 用户：{cpu_times.user}s 空闲：{cpu_times.idle}s
<b>CPU使用率</b>：\nCPU数：{psutil.cpu_count()} 使用率：{cpu_percent}%
{'|' + int(cpu_percent / (100 / 68)) * 'l' + (68 - int(cpu_percent / (100 / 68))) * ' ' + '|'}
<b>内存使用率</b>：\n全部：{int(virtual_memory.total / (1024.0 ** 2) * 10) / 10}MB 可用：{int(virtual_memory.available / (1024.0 ** 2) * 10) / 10}MB 使用率：{int(((virtual_memory.total - virtual_memory.available) / virtual_memory.total) * 10000) / 100}%
{'|' + (68 - int((virtual_memory.available / virtual_memory.total) * 68)) * 'l' + int((virtual_memory.available / virtual_memory.total) * 68) * ' ' + '|'}
<b>交换内存使用率</b>：\n全部：{int(swap_memory.total / (1024.0 ** 2) * 10) / 10}MB 可用：{int(swap_memory.total * (100 - swap_memory.percent) / (1024.0 ** 2)) / 100}MB 使用率：{swap_memory.percent}%
{'|' + int(swap_memory.percent / (100 / 68)) * 'l' + (68 - int(swap_memory.percent / (100 / 68))) * ' ' + '|'}
<b>储存空间使用率</b>：\n全部：{int(disk_usage.total / (1024.0 ** 3) * 10) / 10}GB 已使用：{int(disk_usage.used / (1024.0 ** 3) * 100) / 100}GB 可用：{int(disk_usage.free / (1024.0 ** 3) * 100) / 100}GB 使用率：{disk_usage.percent}%
{'|' + int(disk_usage.percent / (100 / 68)) * 'l' + (68 - int(disk_usage.percent / (100 / 68))) * ' ' + '|'}
<b>网速</b>：\n发送：{sent_speed} 接收：{recv_speed}'''