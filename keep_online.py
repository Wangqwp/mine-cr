"""网络保活 - 访问网关保持在线"""
import time, urllib.request, sys

URL = "http://10.9.1.3/"
INTERVAL = 30  # 秒

print(f"保活已启动，每 {INTERVAL}s 访问 {URL}")
print("按 Ctrl+C 停止\n")

count = 0
while True:
    count += 1
    try:
        urllib.request.urlopen(URL, timeout=5)
        print(f"[{time.strftime('%H:%M:%S')}] #{count} ✓")
    except Exception as e:
        print(f"[{time.strftime('%H:%M:%S')}] #{count} ✗ {e}")

    for i in range(INTERVAL, 0, -1):
        sys.stdout.write(f"\r下次: {i}s ")
        sys.stdout.flush()
        time.sleep(1)
