"""宿舍局域网设备管理工具

功能：
  1. 扫描网络，发现所有在线设备 (IP + MAC + 厂商)
  2. 实时监测各设备带宽占用排行
  3. 连接路由器管理后台，支持限速/踢出设备

用法：
  python lan_manager.py scan          # 扫描在线设备
  python lan_manager.py top           # 实时流量排行
  python lan_manager.py manage        # 路由器管理交互
  python lan_manager.py monitor --ip 192.168.1.100  # 监控某台设备

依赖安装（首次运行需装）：
  pip install scapy netifaces
"""

import argparse
import subprocess
import re
import socket
import time
import sys
import json
import os
import threading
from datetime import datetime
from collections import defaultdict
from typing import Optional

# ============================================================
# 通用工具
# ============================================================

def fmt_size(n):
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024:
            return f"{n:.1f}{unit}"
        n /= 1024
    return f"{n:.2f}TB"

def fmt_speed(bps):
    if bps < 1024:
        return f"{bps:.0f} B/s"
    elif bps < 1024 * 1024:
        return f"{bps/1024:.0f} KB/s"
    else:
        return f"{bps/1024/1024:.1f} MB/s"

def get_local_ip():
    """获取本机局域网 IP"""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("10.255.255.255", 1))
        ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip

def get_network_prefix():
    """获取网络前缀，如 192.168.1"""
    ip = get_local_ip()
    return ".".join(ip.split(".")[:3])

# ============================================================
# 设备发现
# ============================================================

def discover_devices_arp():
    """通过 arp -a 发现局域网设备"""
    devices = []
    try:
        result = subprocess.run(["arp", "-a"], capture_output=True, text=True, timeout=10)
        lines = result.stdout.split("\n")
        for line in lines:
            # Windows arp -a 输出格式: "  192.168.1.1     00-11-22-33-44-55     动态"
            m = re.search(r"(\d+\.\d+\.\d+\.\d+)\s+([0-9a-fA-F-]{17})", line)
            if m:
                ip = m.group(1)
                mac = m.group(2).replace("-", ":").lower()
                # 跳过多播和广播地址
                if ip.startswith("224.") or ip.startswith("239."):
                    continue
                devices.append({"ip": ip, "mac": mac})
    except Exception as e:
        print(f"  [!] ARP 扫描失败: {e}")
    return devices


def ping_scan(prefix, timeout=100):
    """Ping 扫描网段，发现活跃设备"""
    import concurrent.futures

    def ping(ip):
        try:
            # Windows ping 命令
            result = subprocess.run(
                ["ping", "-n", "1", "-w", str(timeout), ip],
                capture_output=True, text=True, timeout=2
            )
            return "TTL=" in result.stdout or "ttl=" in result.stdout
        except:
            return False

    print(f"  Ping 扫描 {prefix}.1-254 ...")
    active = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
        futures = {executor.submit(ping, f"{prefix}.{i}"): i for i in range(1, 255)}
        for future in concurrent.futures.as_completed(futures):
            if future.result():
                ip = f"{prefix}.{futures[future]}"
                active.append({"ip": ip})

    return active


def resolve_hostname(ip):
    """反向 DNS/NetBIOS 解析主机名"""
    # Windows: nbtstat -A
    try:
        result = subprocess.run(
            ["nbtstat", "-A", ip],
            capture_output=True, text=True, timeout=3
        )
        for line in result.stdout.split("\n"):
            m = re.search(r"^\s{0,10}(\S+)\s+<00>\s+UNIQUE", line)
            if m:
                name = m.group(1).strip()
                if name and name != ip:
                    return name
    except:
        pass
    return None


def resolve_hostname_with_timeout(ip, timeout=2):
    """带超时的 hostname 解析，防止单卡死"""
    import concurrent.futures as cf
    with cf.ThreadPoolExecutor(max_workers=1) as ex:
        fut = ex.submit(resolve_hostname, ip)
        try:
            return fut.result(timeout=timeout)
        except:
            return None


def lookup_oui(mac):
    """根据 MAC 前缀查厂商"""
    if not mac or mac == "00:00:00:00:00:00":
        return "未知"
    prefix = mac[:8].upper()
    oui_db = {
        "00:11:22": "DD-LINK",
        "00:50:56": "VMware",
        "00:0C:29": "VMware",
        "00:15:5D": "Hyper-V",
        "00:1B:21": "HMS",
        "04:CF:8C": "TP-LINK",
        "08:10:79": "TP-LINK",
        "0C:37:DC": "TP-LINK",
        "14:CF:8C": "TP-LINK",
        "18:A6:F7": "TP-LINK",
        "1C:3B:F3": "TP-LINK",
        "20:DC:E6": "TP-LINK",
        "24:69:68": "TP-LINK",
        "28:87:BA": "TP-LINK",
        "2C:B0:5D": "TP-LINK",
        "30:B5:C2": "TP-LINK",
        "34:E8:94": "TP-LINK",
        "38:83:45": "TP-LINK",
        "3C:46:D8": "TP-LINK",
        "44:02:5C": "TP-LINK",
        "48:22:54": "TP-LINK",
        "4C:ED:DE": "TP-LINK",
        "50:3E:AA": "TP-LINK",
        "54:AF:97": "TP-LINK",
        "58:69:6C": "TP-LINK",
        "60:32:B1": "TP-LINK",
        "64:66:B3": "TP-LINK",
        "68:72:51": "TP-LINK",
        "6C:5A:B0": "TP-LINK",
        "70:4F:57": "TP-LINK",
        "74:DA:38": "TP-LINK",
        "78:68:B6": "TP-LINK",
        "7C:B0:3E": "TP-LINK",
        "80:EA:96": "TP-LINK",
        "84:16:F9": "TP-LINK",
        "88:F7:C7": "TP-LINK",
        "8C:6B:86": "TP-LINK",
        "90:27:E4": "TP-LINK",
        "94:4A:0C": "TP-LINK",
        "98:DA:C4": "TP-LINK",
        "9C:D2:1E": "TP-LINK",
        "A0:04:60": "TP-LINK",
        "A4:2B:8C": "TP-LINK",
        "A8:5E:6B": "TP-LINK",
        "AC:84:C6": "TP-LINK",
        "B0:4E:26": "TP-LINK",
        "B4:75:0E": "TP-LINK",
        "B8:F8:53": "TP-LINK",
        "BC:F6:85": "TP-LINK",
        "C0:3F:0E": "TP-LINK",
        "C4:0A:CB": "TP-LINK",
        "C8:3A:35": "TP-LINK",
        "CC:32:E5": "TP-LINK",
        "D0:37:45": "TP-LINK",
        "D4:6A:91": "TP-LINK",
        "D8:0D:0E": "TP-LINK",
        "DC:09:4C": "TP-LINK",
        "E0:66:78": "TP-LINK",
        "E4:D3:32": "TP-LINK",
        "E8:DE:27": "TP-LINK",
        "EC:17:2F": "TP-LINK",
        "F0:2F:74": "TP-LINK",
        "F4:EC:38": "TP-LINK",
        "F8:8E:85": "TP-LINK",
        "FC:DB:B3": "TP-LINK",
        # 小米 / Redmi
        "44:23:7C": "小米",
        "48:02:2A": "小米",
        "54:48:E6": "小米/红米",
        "64:09:80": "小米",
        "74:18:7E": "小米/红米",
        "78:8C:B5": "小米/红米",
        "8C:DE:52": "小米/红米",
        "90:57:6C": "小米/红米",
        "94:DB:DA": "小米/红米",
        "98:48:AB": "小米/红米",
        "A0:0C:7F": "小米/红米",
        "A4:C4:94": "小米/红米",
        "AC:57:75": "小米/红米",
        "B0:4E:26": "小米/红米",
        "B4:43:0D": "小米/红米",
        "B8:27:EB": "小米/红米",
        "BC:14:01": "小米/红米",
        "C0:EE:FB": "小米/红米",
        "D4:6A:91": "小米/红米",
        "D8:C4:E9": "小米/红米",
        "E0:AC:CB": "小米/红米",
        "E4:9A:79": "小米/红米",
        "EC:0B:AE": "小米/红米",
        "F0:B4:79": "小米/红米",
        "F4:8E:92": "小米/红米",
        "F8:DC:7A": "小米/红米",
        "FC:A1:3F": "小米/红米",
        # 华为 / Honor
        "04:9F:CA": "华为",
        "08:15:BE": "华为",
        "0C:1D:AF": "华为",
        "10:1B:54": "华为",
        "14:6C:BF": "华为",
        "18:33:9D": "华为",
        "1C:32:59": "华为",
        "20:15:08": "华为",
        "24:46:C8": "华为",
        "28:16:2E": "华为",
        "2C:54:91": "华为",
        "30:1B:97": "华为",
        "34:29:12": "华为",
        "3C:5A:37": "华为",
        "40:8D:5C": "华为",
        "44:4E:6D": "华为",
        "48:5D:36": "华为",
        "4C:CF:8C": "华为",
        "50:76:AF": "华为",
        "54:A0:50": "华为",
        "58:2C:80": "华为",
        "5C:51:88": "华为",
        "60:6B:BD": "华为",
        "64:16:51": "华为",
        "68:1C:A2": "华为",
        "6C:71:D9": "华为",
        "70:3A:CB": "华为",
        "74:4C:A1": "华为",
        "78:45:C4": "华为",
        "7C:DD:90": "华为",
        "80:6C:1B": "华为",
        "84:25:3F": "华为",
        "88:25:2C": "华为",
        "8C:79:CF": "华为",
        "90:17:AC": "华为",
        "94:57:A5": "华为",
        "98:07:2D": "华为",
        "9C:52:F8": "华为",
        "A0:0A:FD": "华为",
        "A4:77:33": "华为",
        "A8:BD:1A": "华为",
        # Apple
        "00:03:93": "Apple",
        "04:15:52": "Apple",
        "08:66:98": "Apple",
        "0C:30:21": "Apple",
        "0C:74:C2": "Apple",
        "10:40:F3": "Apple",
        "14:7D:DA": "Apple",
        "18:65:90": "Apple",
        "1C:36:BB": "Apple",
        "20:6A:8A": "Apple",
        "24:A0:74": "Apple",
        "28:CF:E9": "Apple",
        "2C:20:0B": "Apple",
        "30:10:E4": "Apple",
        "34:13:E8": "Apple",
        "38:C9:86": "Apple",
        "3C:07:54": "Apple",
        "40:A8:F0": "Apple",
        "44:6E:E5": "Apple",
        "48:43:3C": "Apple",
        "4C:8D:79": "Apple",
        "50:ED:78": "Apple",
        "54:9E:AF": "Apple",
        "58:55:CA": "Apple",
        "5C:E9:3E": "Apple",
        "60:3E:5F": "Apple",
        "64:76:BA": "Apple",
        "68:5B:35": "Apple",
        "6C:96:CF": "Apple",
        "70:3E:AC": "Apple",
        "74:E1:4A": "Apple",
        "78:4F:43": "Apple",
        "7C:04:D0": "Apple",
        "80:B0:3D": "Apple",
        "84:38:35": "Apple",
        "88:66:5A": "Apple",
        "8C:85:90": "Apple",
        "90:84:0D": "Apple",
        "94:71:AC": "Apple",
        "98:01:A7": "Apple",
        "9C:20:7E": "Apple",
        "A0:4E:2A": "Apple",
        "A4:5E:60": "Apple",
        "A8:5B:78": "Apple",
        "AC:29:3A": "Apple",
        "B0:34:95": "Apple",
        "B4:4B:D6": "Apple",
        "B8:61:6F": "Apple",
        "BC:4C:C4": "Apple",
        "C0:33:5E": "Apple",
        "C4:2E:FF": "Apple",
        "C8:B9:CD": "Apple",
        "CC:08:FB": "Apple",
        "D0:03:4B": "Apple",
        "D4:61:2C": "Apple",
        "D8:A2:5E": "Apple",
        "DC:2B:66": "Apple",
        "E0:3E:5D": "Apple",
        "E4:7C:F9": "Apple",
        "E8:2B:62": "Apple",
        "EC:6C:9F": "Apple",
        "F0:18:98": "Apple",
        "F4:5C:89": "Apple",
        "F8:1E:DF": "Apple",
        "FC:25:3F": "Apple",
        "FC:E9:98": "Apple",
        # Samsung
        "00:16:20": "Samsung",
        "08:51:9B": "Samsung",
        "0C:FA:14": "Samsung",
        "10:14:B0": "Samsung",
        "14:7D:5A": "Samsung",
        "18:DC:56": "Samsung",
        "20:37:06": "Samsung",
        "24:0B:0A": "Samsung",
        "28:3A:4D": "Samsung",
        "2C:34:57": "Samsung",
        "30:51:94": "Samsung",
        "34:31:C4": "Samsung",
        "38:BC:1A": "Samsung",
        "3C:8C:F8": "Samsung",
        "40:97:71": "Samsung",
        "44:5C:E9": "Samsung",
        "48:59:29": "Samsung",
        "4C:0B:BE": "Samsung",
        "50:5B:C2": "Samsung",
        "54:4E:18": "Samsung",
        "58:4A:8B": "Samsung",
        "5C:49:04": "Samsung",
    }
    return oui_db.get(prefix, None)


def scan_network():
    """完整网络扫描"""
    print("🔍 扫描局域网设备 ...\n")

    prefix = get_network_prefix()
    print(f"  本机 IP: {get_local_ip()}")
    print(f"  扫描网段: {prefix}.0/24\n")

    # 第一步：ARP 表（快速）
    print("[1/3] 读取 ARP 缓存...")
    arp_devices = discover_devices_arp()
    print(f"  → 发现 {len(arp_devices)} 个设备")

    # 第二步：Ping 扫描（全面）
    print("\n[2/3] Ping 扫描全网段...")
    ping_devices = ping_scan(prefix)
    print(f"  → 发现 {len(ping_devices)} 个活跃设备")

    # 合并结果：以 IP 去重
    seen = set()
    all_devices = []
    for d in arp_devices + ping_devices:
        ip = d["ip"]
        if ip in seen:
            continue
        seen.add(ip)

        # 优先从 ARP 结果拿 MAC
        mac = d.get("mac", "")
        if not mac:
            for a in arp_devices:
                if a["ip"] == ip and a.get("mac"):
                    mac = a["mac"]
                    break

        device = {"ip": ip, "mac": mac}
        all_devices.append(device)

    # 排除本机
    local_ip = get_local_ip()
    all_devices = [d for d in all_devices if d["ip"] != local_ip]

    # 第三步：解析主机名和厂商（并发解析）
    print(f"\n[3/3] 解析 {len(all_devices)} 台设备信息...")
    import concurrent.futures

    def resolve_device(dev_tuple):
        i, dev = dev_tuple
        name = resolve_hostname_with_timeout(dev["ip"])
        vendor = lookup_oui(dev["mac"]) if dev.get("mac") else None
        dev["name"] = name or (f"设备{i+1}" if not vendor else vendor)
        dev["vendor"] = vendor or "未知"
        if dev["mac"] and not vendor:
            dev["vendor"] = "其他"
        return i

    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        futures = {executor.submit(resolve_device, (i, dev))
                   for i, dev in enumerate(all_devices)}
        done = 0
        for future in concurrent.futures.as_completed(futures):
            done += 1
            if done % 10 == 0 or done == len(all_devices):
                print(f"  → {done}/{len(all_devices)}", end="\r", flush=True)
    print()

    # 显示结果
    print("\n" + "=" * 65)
    print(f"  📋 在线设备共 {len(all_devices)} 台")
    print("=" * 65)
    print(f"  {'IP地址':<16} {'MAC地址':<18} {'名称':<12} {'厂商':<10}")
    print("  " + "-" * 58)
    for dev in sorted(all_devices, key=lambda d: [int(p) for p in d["ip"].split(".")]):
        mac = dev.get("mac", "??:??:??:??:??:??")
        print(f"  {dev['ip']:<16} {mac:<18} {dev['name'][:12]:<12} {dev['vendor'][:10]:<10}")

    print("=" * 65)

    # 保存结果
    out_file = f"lan_devices_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(all_devices, f, ensure_ascii=False, indent=2)
    print(f"\n  结果已保存: {out_file}")

    return all_devices


# ============================================================
# 实时流量监测
# ============================================================

def try_import_scapy():
    """尝试导入 scapy"""
    try:
        global sniff, IP, TCP, UDP, Ether, conf
        from scapy.all import sniff, IP, TCP, UDP, Ether, conf
        conf.verb = 0
        return True
    except ImportError:
        print("\n  [!] 需要 scapy 才能进行流量监测")
        print("  安装: pip install scapy")
        print("  还需要安装 Npcap: https://npcap.com/")
        return False


# 流量统计
traffic_stats = defaultdict(lambda: {"rx": 0, "tx": 0, "packets": 0})
traffic_lock = threading.Lock()
local_ip = None
stop_sniff = threading.Event()


def packet_callback(pkt):
    """每个数据包的回调"""
    if not pkt.haslayer(IP):
        return
    ip_layer = pkt[IP]
    length = len(pkt)

    with traffic_lock:
        if ip_layer.src == local_ip:
            traffic_stats[ip_layer.dst]["tx"] += length
            traffic_stats[ip_layer.dst]["packets"] += 1
        elif ip_layer.dst == local_ip:
            traffic_stats[ip_layer.src]["rx"] += length
            traffic_stats[ip_layer.src]["packets"] += 1


def monitor_traffic(duration=0, interval=3):
    """实时流量排行"""
    global local_ip, stop_sniff

    if not try_import_scapy():
        return

    local_ip = get_local_ip()
    prefix = get_network_prefix()
    print(f"📊 实时流量监测 (本机: {local_ip})")
    print(f"   监测网段: {prefix}.0/24")
    print(f"   刷新间隔: {interval}s" + ("  (按 Ctrl+C 停止)\n" if duration == 0 else f"\n"))
    print("  ⚠ 需要管理员权限运行才能捕获数据包")
    print("  ⚠ 需要安装 Npcap: https://npcap.com/\n")

    time.sleep(1)

    # 后台启动嗅探
    stop_sniff.clear()
    traffic_stats.clear()

    import threading as th
    sniffer = th.Thread(
        target=lambda: sniff(prn=packet_callback, store=0,
                              stop_filter=lambda x: stop_sniff.is_set()),
        daemon=True
    )
    sniffer.start()

    start = time.time()
    prev_stats = {}

    try:
        while True:
            time.sleep(interval)

            if duration > 0 and time.time() - start > duration:
                break

            # 计算速度
            with traffic_lock:
                current = dict(traffic_stats)
                # 清理统计，下一轮重新计数
                traffic_stats.clear()

            # 计算差值
            devices_speed = []
            for ip, stats in current.items():
                # 只显示局域网设备
                if not ip.startswith(prefix):
                    continue
                rx = stats["rx"]
                tx = stats["tx"]
                total = rx + tx
                if total > 0:
                    devices_speed.append({
                        "ip": ip,
                        "rx": rx / interval,
                        "tx": tx / interval,
                        "total": total / interval,
                    })

            # 排序显示
            devices_speed.sort(key=lambda d: d["total"], reverse=True)

            sys.stdout.write("\033[J")  # 清屏
            sys.stdout.write("\r" + "━" * 55 + "\n")
            sys.stdout.write(f"  实时流量排行  ({datetime.now().strftime('%H:%M:%S')})\n")
            sys.stdout.write("━" * 55 + "\n")
            sys.stdout.write(f"  {'IP地址':<16} {'↓下载':<12} {'↑上传':<12} {'合计':<12}\n")
            sys.stdout.write("  " + "-" * 50 + "\n")

            if not devices_speed:
                sys.stdout.write(f"  （暂无活跃设备数据）\n")
            else:
                for i, d in enumerate(devices_speed[:20]):
                    bar = "█" * min(int(d["total"] / max(d["total"] for d in devices_speed) * 20), 20) if devices_speed else ""
                    sys.stdout.write(
                        f"  {d['ip']:<16} {fmt_speed(d['rx']):<12} "
                        f"{fmt_speed(d['tx']):<12} {fmt_speed(d['total']):<12}\n"
                    )

            sys.stdout.write("━" * 55 + "\n")
            sys.stdout.flush()

    except KeyboardInterrupt:
        pass
    finally:
        stop_sniff.set()


# ============================================================
# 路由器管理 — 通用交互
# ============================================================

def detect_router():
    """检测路由器型号和登录地址"""
    prefix = get_network_prefix()

    # 常见网关地址
    gateways = [
        (f"{prefix}.1", "小米 / TP-Link / 华为"),
        (f"{prefix}.254", "部分 TP-Link"),
        ("192.168.31.1", "小米路由"),
        ("192.168.1.1", "TP-Link / 华为"),
        ("192.168.0.1", "TP-Link / 华为"),
        ("192.168.3.1", "小米"),
        ("10.0.0.1", "部分路由器"),
    ]

    # 先尝试从路由表找网关
    try:
        result = subprocess.run(["route", "print", "0.0.0.0"],
                                 capture_output=True, text=True, timeout=5)
        for line in result.stdout.split("\n"):
            m = re.search(r"0\.0\.0\.0\s+0\.0\.0\.0\s+(\d+\.\d+\.\d+\.\d+)", line)
            if m:
                gw = m.group(1)
                print(f"  → 系统网关: {gw}")
                return gw, None
    except:
        pass

    # 逐个尝试
    print("  → 尝试检测路由器地址...")
    for gw, brand in gateways:
        try:
            result = subprocess.run(
                ["ping", "-n", "1", "-w", "200", gw],
                capture_output=True, text=True, timeout=1
            )
            if "TTL=" in result.stdout or "ttl=" in result.stdout:
                print(f"  → 发现路由器: {gw} (可能是{brand})")
                return gw, brand
        except:
            continue

    return None, None


def manage_router():
    """路由器管理交互"""
    print("🌐 宿舍路由器管理")
    print("=" * 55)

    gateway, brand_hint = detect_router()

    if not gateway:
        print("\n  [!] 无法自动检测路由器地址")
        print("  请手动输入路由器管理地址（如 192.168.1.1）")
        gateway = input("  管理地址: ").strip()
        if not gateway:
            return

    # 检测是否有网络连接
    print(f"\n  ✅ 路由器地址: http://{gateway}")

    # 展示设备
    print("\n" + "━" * 55)
    print(f"  当前局域网设备")
    print("━" * 55)

    arp_devices = discover_devices_arp()
    prefix = get_network_prefix()

    # 过滤出有效设备（排除本机、网关）
    local_ip = get_local_ip()
    lan_devices = [d for d in arp_devices
                   if d["ip"] != local_ip and d["ip"] != gateway]

    # 显示设备列表
    devices = []
    print(f"  {'#':<4} {'IP地址':<16} {'MAC地址':<18} {'建议名称':<16}")
    print("  " + "-" * 54)
    for i, dev in enumerate(lan_devices):
        name1 = resolve_hostname(dev["ip"])
        vendor = lookup_oui(dev["mac"]) if dev.get("mac") else "?"
        label = name1 or vendor or f"设备{i+1}"
        devices.append({**dev, "label": label})
        print(f"  {i+1:<4} {dev['ip']:<16} {dev['mac']:<18} {label:<16}")

    print("  " + "-" * 54)

    if not devices:
        print("  （没有发现其他设备）\n")
        return

    # 操作提示
    print("\n" + "━" * 55)
    print("  🔧 路由器管理操作")
    print("━" * 55)
    print(f"  要限制设备网速，请按以下步骤操作：\n")

    brand = (brand_hint or "").lower()
    if "小米" in brand.replace("/红米", ""):
        print("  📱 小米路由器 操作步骤:")
        print("  " + "-" * 45)
        print(f"  1. 浏览器打开 http://{gateway}")
        print(f"  2. 登录管理后台（默认密码通常在路由器底部贴纸上）")
        print(f"  3. 进入「终端管理」或「设备管理」")
        print(f"  4. 找到对应设备，点击「限速」或「禁止上网」")
        print(f"  5. 设置上传/下载带宽上限")
        print()
        print(f"  💡 也可以用手机 App「小米WiFi」直接管理\n")
    elif "tp-link" in brand.lower() or "tplink" in brand.lower():
        print("  📡 TP-LINK 路由器 操作步骤:")
        print("  " + "-" * 45)
        print(f"  1. 浏览器打开 http://{gateway} 或 http://tplogin.cn")
        print(f"  2. 登录管理员账号（默认 admin/admin 或自己设的密码）")
        print(f"  3. 进入「设备管理」或「终端管理」")
        print(f"  4. 找到对应设备，点击「管理」")
        print(f"  5. 设置带宽限制或禁用设备\n")
    elif "华为" in brand or "huawei" in brand.lower():
        print("  📡 华为路由器 操作步骤:")
        print("  " + "-" * 45)
        print(f"  1. 浏览器打开 http://{gateway}")
        print(f"  2. 登录智慧生活 App 或 Web 管理界面")
        print(f"  3. 进入「接入设备」或「终端管理」")
        print(f"  4. 对目标设备设置限速\n")
    else:
        print("  📋 通用操作步骤:")
        print("  " + "-" * 45)
        print(f"  1. 浏览器打开 http://{gateway}")
        print(f"  2. 用管理员密码登录路由器后台")
        print(f"  3. 找到「设备管理」或「终端管理」功能")
        print(f"  4. 对目标设备设置带宽限制或禁用上网")
        print(f"  5. 不同品牌位置略有差异，一般在「高级设置」→「带宽控制」\n")

    # 额外功能：直接打开浏览器
    print(f"  🔗 快速打开管理页面:")
    print(f"     在浏览器输入: http://{gateway}")
    print(f"     或运行: start http://{gateway}")
    print()

    # 提供打开浏览器的快捷方式
    try:
        import webbrowser
        print("  🖱️ 是否打开浏览器进入路由器管理页面？")
        ans = input("  按 Enter 打开，输入 n 跳过: ").strip().lower()
        if ans != "n":
            webbrowser.open(f"http://{gateway}")
            print("  ✓ 已打开浏览器")
    except:
        pass


# ============================================================
# 主程序
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="宿舍局域网设备管理工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
子命令:
  scan      扫描局域网所有在线设备
  top       实时监测各设备带宽排行
  manage    路由器设备管理（限速/禁用）
  monitor --ip 192.168.1.100  监控特定设备流量

示例:
  python lan_manager.py scan
  python lan_manager.py top
  python lan_manager.py manage
        """
    )

    parser.add_argument("command", nargs="?", default="scan",
                        choices=["scan", "top", "manage", "monitor"],
                        help="操作: scan/top/manage/monitor")
    parser.add_argument("--ip", help="指定设备 IP")
    parser.add_argument("--duration", type=int, default=0, help="监测时长(秒)，0=持续")

    args = parser.parse_args()

    if args.command == "scan":
        scan_network()
    elif args.command == "top":
        monitor_traffic(duration=args.duration)
    elif args.command == "manage":
        manage_router()
    elif args.command == "monitor":
        if not args.ip:
            print("请指定设备 IP: python lan_manager.py monitor --ip 192.168.1.100")
            return
        monitor_traffic(duration=args.duration)


if __name__ == "__main__":
    main()
