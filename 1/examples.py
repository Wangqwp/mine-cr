#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
使用示例 - 展示如何使用 StockCrawler
"""

from stock_crawler_v2 import StockCrawler
import json

def example_1_basic():
    """示例 1: 基本使用 - 单次爬取"""
    print("\n" + "="*60)
    print("示例 1: 基本使用 - 单次爬取")
    print("="*60)
    
    crawler = StockCrawler()
    crawler.run_once()

def example_2_custom_path():
    """示例 2: 自定义数据路径"""
    print("\n" + "="*60)
    print("示例 2: 自定义数据路径")
    print("="*60)
    
    crawler = StockCrawler(data_dir='./my_stock_data')
    data = crawler.crawl_data()
    crawler.save_data(data)
    print(f"✓ 数据已保存到 ./my_stock_data/latest.json")

def example_3_continuous():
    """示例 3: 连续爬取"""
    print("\n" + "="*60)
    print("示例 3: 连续爬取（每30秒更新一次）")
    print("示例: 按 Ctrl+C 停止")
    print("="*60)
    
    crawler = StockCrawler()
    # crawler.run_continuous(interval=30)

def example_4_custom_stocks():
    """示例 4: 自定义股票列表"""
    print("\n" + "="*60)
    print("示例 4: 自定义股票列表")
    print("="*60)
    
    class CustomStockCrawler(StockCrawler):
        def get_hot_stocks(self):
            # 只爬取指定的股票
            return [
                'sh000001',  # 上证指数
                'sh600519',  # 贵州茅台
                'sh601398',  # 工商银行
                'sz000858',  # 五粮液
                'sz000333',  # 美的集团
                'sz300750',  # 宁德时代
            ]
    
    crawler = CustomStockCrawler()
    crawler.run_once()

def example_5_process_data():
    """示例 5: 处理爬取的数据"""
    print("\n" + "="*60)
    print("示例 5: 处理爬取的数据")
    print("="*60)
    
    crawler = StockCrawler()
    data = crawler.crawl_data()
    
    # 按涨跌幅排序
    stocks = data['数据'].items()
    stocks_sorted = sorted(stocks, 
                           key=lambda x: x[1].get('涨跌幅%', 0), 
                           reverse=True)
    
    print("\n【涨幅 TOP 5】")
    for i, (code, info) in enumerate(stocks_sorted[:5], 1):
        print(f"{i}. {info['名称']:12} {info['当前价']:8.2f} "
              f"({info['涨跌幅%']:+7.2f}%)")

def example_6_analyze_data():
    """示例 6: 数据分析"""
    print("\n" + "="*60)
    print("示例 6: 数据分析")
    print("="*60)
    
    crawler = StockCrawler()
    data = crawler.crawl_data()
    stocks = data['数据']
    
    # 计算统计数据
    if stocks:
        prices = [s['当前价'] for s in stocks.values() if s['当前价'] > 0]
        changes = [s['涨跌幅%'] for s in stocks.values()]
        
        print(f"\n统计数据:")
        print(f"  股票数量: {len(stocks)}")
        print(f"  平均价格: {sum(prices)/len(prices) if prices else 0:.2f}")
        print(f"  平均涨幅: {sum(changes)/len(changes) if changes else 0:.2f}%")
        print(f"  最大涨幅: {max(changes):.2f}%")
        print(f"  最大跌幅: {min(changes):.2f}%")

def example_7_save_custom():
    """示例 7: 自定义保存格式"""
    print("\n" + "="*60)
    print("示例 7: 自定义保存格式")
    print("="*60)
    
    crawler = StockCrawler()
    data = crawler.crawl_data()
    
    # 保存为 CSV 格式
    import csv
    from pathlib import Path
    
    csv_path = Path('./stock_data/stock_data.csv')
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['代码', '名称', '当前价', '涨跌幅%', '成交量'])
        
        for code, info in data['数据'].items():
            writer.writerow([
                code,
                info['名称'],
                info['当前价'],
                info['涨跌幅%'],
                info['成交量']
            ])
    
    print(f"✓ 数据已保存到 CSV: {csv_path}")

def example_8_filter_data():
    """示例 8: 数据过滤"""
    print("\n" + "="*60)
    print("示例 8: 数据过滤")
    print("="*60)
    
    crawler = StockCrawler()
    data = crawler.crawl_data()
    stocks = data['数据']
    
    # 找出涨幅超过 2% 的股票
    gainers = {k: v for k, v in stocks.items() 
               if v.get('涨跌幅%', 0) > 2}
    
    # 找出跌幅超过 1% 的股票
    losers = {k: v for k, v in stocks.items() 
              if v.get('涨跌幅%', 0) < -1}
    
    print(f"\n涨幅 > 2% 的股票 ({len(gainers)} 只):")
    for code, info in gainers.items():
        print(f"  {info['名称']:10} {info['涨跌幅%']:+7.2f}%")
    
    print(f"\n跌幅 > 1% 的股票 ({len(losers)} 只):")
    for code, info in losers.items():
        print(f"  {info['名称']:10} {info['涨跌幅%']:+7.2f}%")

def example_9_load_history():
    """示例 9: 加载历史数据"""
    print("\n" + "="*60)
    print("示例 9: 加载历史数据")
    print("="*60)
    
    try:
        from pathlib import Path
        
        # 列出所有历史数据文件
        data_dir = Path('./stock_data')
        files = sorted(data_dir.glob('stock_data_*.json'), reverse=True)
        
        print(f"\n找到 {len(files)} 个历史数据文件:\n")
        for i, f in enumerate(files[:5], 1):
            print(f"  {i}. {f.name}")
            
            # 加载并显示第一个文件
            if i == 1:
                with open(f, 'r', encoding='utf-8') as file:
                    data = json.load(file)
                    print(f"     更新时间: {data['更新时间']}")
                    print(f"     股票数: {data['股票数']}")
    except Exception as e:
        print(f"✗ 错误: {e}")

def example_10_error_handling():
    """示例 10: 错误处理"""
    print("\n" + "="*60)
    print("示例 10: 错误处理")
    print("="*60)
    
    try:
        crawler = StockCrawler(data_dir='./stock_data')
        data = crawler.crawl_data()
        
        if not data['数据']:
            print("⚠️ 警告: 没有获取到数据")
        else:
            print(f"✓ 成功获取 {data['股票数']} 只股票")
            
    except Exception as e:
        print(f"✗ 错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    print("\n╔════════════════════════════════════════════════════════╗")
    print("║          StockCrawler 使用示例                        ║")
    print("╚════════════════════════════════════════════════════════╝")
    
    print("\n可用的示例:")
    print("  1. 基本使用 - 单次爬取")
    print("  2. 自定义数据路径")
    print("  3. 连续爬取")
    print("  4. 自定义股票列表")
    print("  5. 处理爬取的数据")
    print("  6. 数据分析")
    print("  7. 自定义保存格式")
    print("  8. 数据过滤")
    print("  9. 加载历史数据")
    print("  10. 错误处理")
    print("  0. 退出\n")
    
    choice = input("选择示例 (0-10): ").strip()
    
    examples = {
        '1': example_1_basic,
        '2': example_2_custom_path,
        '3': example_3_continuous,
        '4': example_4_custom_stocks,
        '5': example_5_process_data,
        '6': example_6_analyze_data,
        '7': example_7_save_custom,
        '8': example_8_filter_data,
        '9': example_9_load_history,
        '10': example_10_error_handling,
    }
    
    if choice in examples:
        examples[choice]()
    elif choice == '0':
        print("退出")
    else:
        print("无效的选择")
