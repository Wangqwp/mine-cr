#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
交互式菜单 - 使用可靠的爬虫版本
"""

from stock_crawler_v2 import StockCrawler

def main():
    crawler = StockCrawler(data_dir='./stock_data')
    
    print("\n╔════════════════════════════════════════════════════════════╗")
    print("║       中国股市实时爬虫 v2.0 - Stock Market Crawler          ║")
    print("║          支持多数据源，数据更加稳定可靠                      ║")
    print("╚════════════════════════════════════════════════════════════╝\n")
    
    print("选择运行模式:\n")
    print("  1. 单次爬取 (执行一次后退出)")
    print("  2. 连续爬取 (每分钟更新一次)")
    print("  3. 自定义间隔 (自定义更新频率)")
    print("  0. 退出\n")
    
    choice = input("请选择 (0-3): ").strip()
    
    if choice == '1':
        print("\n执行单次爬取...\n")
        crawler.run_once()
    
    elif choice == '2':
        print("\n启动连续爬虫 (每分钟更新一次)")
        print("按 Ctrl+C 停止爬虫\n")
        crawler.run_continuous(interval=60)
    
    elif choice == '3':
        interval_str = input("请输入更新间隔（秒，最少10秒）: ").strip()
        try:
            interval = int(interval_str)
            if interval < 10:
                print("警告: 间隔太短，调整为 10 秒")
                interval = 10
            
            print(f"\n启动连续爬虫 (每{interval}秒更新一次)")
            print("按 Ctrl+C 停止爬虫\n")
            crawler.run_continuous(interval=interval)
        except ValueError:
            print("错误: 请输入有效的数字")
    
    elif choice == '0':
        print("退出程序")
    
    else:
        print("无效的选择")


if __name__ == '__main__':
    main()
