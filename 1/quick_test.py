#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
快速测试爬虫是否能获取到数据
"""

from stock_crawler import StockCrawler
import json

print("=" * 70)
print("股市爬虫数据获取测试")
print("=" * 70)

# 创建爬虫
crawler = StockCrawler()

# 测试单个股票
print("\n【测试 1】尝试获取上证指数...")
result = crawler.get_stock_data_sina(['sh000001'])
print(f"结果: {len(result)} 条数据")
if result:
    for code, data in result.items():
        print(f"  ✓ {data['名称']}: {data['当前价']} ({data['涨跌幅%']:+.2f}%)")

# 测试热门股票
print("\n【测试 2】尝试获取热门股票...")
result = crawler.get_stock_data_sina(crawler.get_hot_stocks()[:3])
print(f"结果: {len(result)} 条数据")
if result:
    for code, data in result.items():
        print(f"  ✓ {data['名称']}: {data['当前价']} ({data['涨跌幅%']:+.2f}%)")

# 完整爬取
print("\n【测试 3】执行完整爬取...")
data = crawler.crawl_all_data()

print(f"\n爬取结果摘要:")
print(f"  - 更新时间: {data['更新时间']}")
print(f"  - 指数数量: {len(data['指数'])}")
print(f"  - 股票数量: {len(data['热门股票'])}")

# 显示数据
if data['指数']:
    print(f"\n【指数数据】")
    for code, info in data['指数'].items():
        if isinstance(info, dict) and '名称' in info:
            print(f"  {info['名称']}: {info.get('当前价', 'N/A')} ({info.get('涨跌幅%', 'N/A'):+.2f}%)" if isinstance(info.get('涨跌幅%', 'N/A'), (int, float)) else f"  {info['名称']}: {info.get('当前价', 'N/A')}")

if data['热门股票']:
    print(f"\n【热门股票】")
    for i, (code, info) in enumerate(list(data['热门股票'].items())[:5], 1):
        if isinstance(info, dict) and '名称' in info:
            print(f"  {i}. {info['名称']}: {info.get('当前价', 'N/A')} ({info.get('涨跌幅%', 'N/A'):+.2f}%)" if isinstance(info.get('涨跌幅%', 'N/A'), (int, float)) else f"  {i}. {info['名称']}")

print("\n" + "=" * 70)
print("✓ 测试完成！如果上面看到数据，说明爬虫正常工作。")
print("=" * 70)
