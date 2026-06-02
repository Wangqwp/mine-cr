"""校园网流量消耗工具 — 硬件友好版

特点：
  • 间歇工作 — 跑一会儿歇一会儿，硬件有冷却时间
  • 低 CPU 占用 — 减少线程数 + 主动休眠
  • 零磁盘写入 — 全在内存，不伤 SSD
  • 进程优先级低 — 不影响你正常用电脑

使用方法：
    python consume_bandwidth.py                  # 默认消耗 10GB
    python consume_bandwidth.py --target 50       # 消耗 50GB
    python consume_bandwidth.py --target 0        # 无限模式，Ctrl+C 停止
    python consume_bandwidth.py --gentle          # 最温柔模式（1线程+长休息）
    python consume_bandwidth.py --speed-only      # 只测速
"""

import argparse
import threading
import time
import sys
import signal
import urllib.request
import socket
from datetime import datetime, timedelta

# ============================================================
# 下载源
# ============================================================
TEST_FILES = [
    "https://speed.cloudflare.com/__down?bytes=104857600",
    "http://speedtest.tele2.net/100MB.zip",
    "http://speedtest.tele2.net/1GB.zip",
    "http://cachefly.cachefly.net/100mb.test",
    "http://speedtest.fremont.linode.com/100MB-fremont.bin",
    "http://speedtest.dallas.linode.com/100MB-dallas.bin",
    "http://speedtest.singapore.linode.com/100MB-singapore.bin",
    "https://proof.ovh.net/files/100Mb.dat",
    "https://speed.aliyun.com/100MB.bin",
    "http://mirrors.ustc.edu.cn/ubuntu-releases/24.04/ubuntu-24.04-desktop-amd64.iso",
    "http://mirrors.tuna.tsinghua.edu.cn/ubuntu-releases/24.04/ubuntu-24.04-desktop-amd64.iso",
    "http://mirrors.aliyun.com/ubuntu-releases/24.04/ubuntu-24.04-desktop-amd64.iso",
    "http://mirrors.huaweicloud.com/ubuntu-releases/24.04/ubuntu-24.04-desktop-amd64.iso",
]

# ============================================================
# 全局统计
# ============================================================
stats = {"downloaded": 0, "start_time": None, "active_now": 0, "fails": 0}
stats_lock = threading.Lock()

TARGET_BYTES = 0  # 将在 main 中设置


def fmt_size(n):
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} PB"


def fmt_speed(bps):
    if bps < 1024:
        return f"{bps:.0f} B/s"
    elif bps < 1024 * 1024:
        return f"{bps/1024:.0f} KB/s"
    elif bps < 1024 * 1024 * 1024:
        return f"{bps/1024/1024:.1f} MB/s"
    else:
        return f"{bps/1024/1024/1024:.2f} GB/s"


def download_worker(urls, stop_event):
    """单个下载线程：串行循环下载，每次下载后休息一下"""
    import random
    idx = 0
    while not stop_event.is_set():
        # 选一个源
        url = urls[idx % len(urls)]
        idx += 1

        try:
            req = urllib.request.Request(url, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                              "AppleWebKit/537.36 (KHTML, like Gecko) "
                              "Chrome/125.0.0.0 Safari/537.36",
                "Accept-Encoding": "identity",
            })
            resp = urllib.request.urlopen(req, timeout=20)

            with stats_lock:
                stats["active_now"] += 1

            # 限制单次连接最大读取量，避免一个连接跑太久
            max_per_conn = 50 * 1024 * 1024  # 50MB
            read_this_conn = 0

            while not stop_event.is_set():
                chunk = resp.read(65536)  # 64KB 小片读取
                if not chunk:
                    break
                n = len(chunk)
                read_this_conn += n
                with stats_lock:
                    stats["downloaded"] += n
                    # 检查是否达到总目标
                    if TARGET_BYTES > 0 and stats["downloaded"] >= TARGET_BYTES:
                        stop_event.set()
                        break

                # 单连接达到上限，断开换源（避免一个源太慢拖累整体）
                if read_this_conn >= max_per_conn:
                    break

            resp.close()

            with stats_lock:
                stats["active_now"] -= 1

        except Exception:
            with stats_lock:
                stats["fails"] += 1
                stats["active_now"] = max(0, stats["active_now"] - 1)

        # === 线程内冷却 ===
        # 每次下载完成后休息 2-5 秒，让 CPU 和网卡降温
        if not stop_event.is_set():
            cool_down = random.uniform(2.0, 5.0)
            # 分小段 sleep，以便能快速响应停止信号
            for _ in range(int(cool_down * 10)):
                if stop_event.is_set():
                    break
                time.sleep(0.1)


def progress_printer(stop_event):
    """进度显示 + 自动暂停逻辑"""
    last_bytes = 0
    last_time = time.time()
    speeds = []

    stats["start_time"] = time.time()
    work_start = time.time()

    while not stop_event.is_set():
        time.sleep(3)

        with stats_lock:
            now = stats["downloaded"]
            active = stats["active_now"]
            fails = stats["fails"]
        now_time = time.time()
        dt = now_time - last_time

        speed = (now - last_bytes) / dt if dt > 0 else 0
        speeds.append(speed)
        if len(speeds) > 3:
            speeds.pop(0)
        avg = sum(speeds) / len(speeds)

        elapsed = now_time - stats["start_time"]
        eta = ""
        if TARGET_BYTES > 0 and avg > 0:
            remaining = TARGET_BYTES - now
            eta_sec = remaining / avg
            eta = f" | ETA {str(timedelta(seconds=int(eta_sec)))}"

        # 清屏写状态
        pct = min(100, now / TARGET_BYTES * 100) if TARGET_BYTES > 0 else 0
        bar_len = 30
        filled = int(bar_len * pct / 100) if TARGET_BYTES > 0 else 0
        bar = "█" * filled + "░" * (bar_len - filled)

        sys.stdout.write("\033[J")  # 清下方
        sys.stdout.write("\r" + "━" * 55 + "\n")
        sys.stdout.write(f"  [流量] {fmt_size(now)}")
        if TARGET_BYTES > 0:
            sys.stdout.write(f" / {fmt_size(TARGET_BYTES)} ({pct:.1f}%)\n")
            sys.stdout.write(f"  [进度] {bar}\n")
        else:
            sys.stdout.write(" (无限模式)\n")
        sys.stdout.write(f"  [速度] {fmt_speed(avg)} (峰值 {fmt_speed(max(speeds) if speeds else 0)}){eta}\n")
        sys.stdout.write(f"  [线程] {active} 活跃 | [失败] {fails} | [已运行] {str(timedelta(seconds=int(elapsed)))}\n")

        # 如果平均速度极低，提示
        if avg < 1024 * 10 and elapsed > 30:
            sys.stdout.write(f"  ⚠ 速度偏低，可能是校园网限速或源不可用\n")

        sys.stdout.write("━" * 55 + "\n")
        sys.stdout.flush()

        last_bytes = now
        last_time = now_time


def check_network():
    """网络连通性检查 + 快速测速"""
    print("\n[*] 检查网络连通性...")
    hosts = [("百度", "www.baidu.com"), ("Cloudflare", "speed.cloudflare.com")]
    ok = False
    for name, host in hosts:
        try:
            ip = socket.getaddrinfo(host, 80)[0][4][0]
            print(f"  ✓ {name} 可达 ({ip})")
            ok = True
        except Exception as e:
            print(f"  ✗ {name} 不可达: {e}")

    if not ok:
        print("  [!] 网络不通，退出")
        return False

    # 快速测速 5MB
    print("\n[*] 快速测速 (5MB)...")
    try:
        url = "https://speed.cloudflare.com/__down?bytes=5242880"
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0", "Accept-Encoding": "identity"})
        t0 = time.time()
        resp = urllib.request.urlopen(req, timeout=15)
        total = 0
        while True:
            c = resp.read(65536)
            if not c:
                break
            total += len(c)
        t = time.time() - t0
        spd = total / t if t > 0 else 0
        print(f"  ↓ 测速结果: {fmt_size(total)} / {t:.1f}s = {fmt_speed(spd)}")
        print(f"  → 按此速度，每小时约消耗 {fmt_size(spd*3600)}")
    except Exception as e:
        print(f"  ✗ 测速失败: {e}")

    return True


def main():
    global TARGET_BYTES

    parser = argparse.ArgumentParser(
        description="校园网流量消耗工具 — 硬件友好版",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""示例:
  %(prog)s                   # 默认 10GB
  %(prog)s --target 30       # 30GB
  %(prog)s --target 0        # 无限模式
  %(prog)s --gentle          # 最温柔（1线程，多休息）
  %(prog)s --speed-only      # 只测速""")

    parser.add_argument("--target", type=float, default=10, help="目标 GB (0=无限)")
    parser.add_argument("--threads", type=int, default=0, help="线程数 (默认自动)")
    parser.add_argument("--gentle", action="store_true", help="最温柔模式")
    parser.add_argument("--speed-only", action="store_true", help="只测速")
    args = parser.parse_args()

    TARGET_BYTES = int(args.target * 1024**3)

    # 硬件友好策略 — 线程数选择
    if args.gentle:
        num_threads = 1
        work_min = 30   # 跑 30 秒
        rest_min = 120  # 歇 2 分钟
    elif args.threads > 0:
        num_threads = args.threads
        work_min = 120
        rest_min = 60
    else:
        # 自动：2-3 线程，平衡速度和发热
        num_threads = 2
        work_min = 90
        rest_min = 45  # 工作1.5分钟，休息45秒 ≈ 66% 占空比

    print("━" * 55)
    print("  校园网流量消耗工具 · 硬件友好版")
    print("━" * 55)
    if args.speed_only:
        check_network()
        return

    print(f"  目标: {'∞ 无限' if TARGET_BYTES == 0 else fmt_size(TARGET_BYTES)}")
    print(f"  线程: {num_threads}")
    print(f"  策略: 工作 {work_min}s → 休息 {rest_min}s (循环)")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("━" * 55)

    if not check_network():
        sys.exit(1)

    # 组建 URL 池
    urls = list(TEST_FILES)

    print(f"\n[*] 下载源: {len(urls)} 个 | 线程: {num_threads}")
    print("[*] 按 Ctrl+C 安全停止\n")

    stop_event = threading.Event()

    def on_sigint(s, f):
        print("\n\n[!] 正在停止... 等待线程退出")
        stop_event.set()
    signal.signal(signal.SIGINT, on_sigint)

    # 启动进度线程
    prog = threading.Thread(target=progress_printer, args=(stop_event,), daemon=True)
    prog.start()

    # === 主循环：间歇工作 ===
    workers = []
    try:
        while not stop_event.is_set():
            # 检查是否达到目标
            if TARGET_BYTES > 0:
                with stats_lock:
                    if stats["downloaded"] >= TARGET_BYTES:
                        break

            # === 工作时段 ===
            # 启动线程
            workers.clear()
            for i in range(num_threads):
                t = threading.Thread(target=download_worker, args=(urls, stop_event), daemon=True)
                t.start()
                workers.append(t)

            # 等待工作时段结束 或 达到目标
            work_end = time.time() + work_min
            while time.time() < work_end and not stop_event.is_set():
                if TARGET_BYTES > 0:
                    with stats_lock:
                        if stats["downloaded"] >= TARGET_BYTES:
                            stop_event.set()
                            break
                time.sleep(0.5)

            # 停止工作线程
            stop_event.set()
            for t in workers:
                t.join(timeout=3)

            # 检查是否完成
            if TARGET_BYTES > 0:
                with stats_lock:
                    if stats["downloaded"] >= TARGET_BYTES:
                        break

            # === 休息时段 ===
            if not stop_event.is_set():
                # 重置 stop_event 以便下一轮
                stop_event.clear()

                # 显示休息倒计时
                rest_end = time.time() + rest_min
                while time.time() < rest_end and not stop_event.is_set():
                    remaining = int(rest_end - time.time())
                    sys.stdout.write(f"\r  ☕ 休息中... {remaining}s 后继续工作  ")
                    sys.stdout.flush()
                    time.sleep(1)
                sys.stdout.write("\n\n")
                sys.stdout.flush()

    except KeyboardInterrupt:
        stop_event.set()

    # 最终停止
    stop_event.set()
    time.sleep(0.5)

    elapsed = time.time() - stats["start_time"]
    total = stats["downloaded"]
    speed = total / elapsed if elapsed > 0 else 0

    print("\n" + "━" * 55)
    print(f"  运行结束")
    print(f"  运行时间: {str(timedelta(seconds=int(elapsed)))}")
    print(f"  总消耗:   {fmt_size(total)}")
    print(f"  平均速度: {fmt_speed(speed)}")
    print(f"  失败次数: {stats['fails']}")
    print("━" * 55)


if __name__ == "__main__":
    main()
