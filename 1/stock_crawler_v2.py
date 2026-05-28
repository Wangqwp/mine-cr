#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
中国股市实时爬虫 - 可靠版本
"""

import requests
import json
import time
from datetime import datetime
from pathlib import Path
import logging
from typing import Dict, List, Optional

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('stock_crawler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class StockCrawler:
    """中国股市实时数据爬虫 - 多数据源版本"""
    
    def __init__(self, data_dir: str = './stock_data'):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
    def get_stocks_from_eastmoney(self, stock_codes: List[str]) -> Dict:
        """从东方财富获取股票数据（最稳定的方式）"""
        stocks_data = {}
        
        for stock_code in stock_codes:
            try:
                # 转换代码格式: sh600000 -> 1.600000, sz000001 -> 0.000001
                if stock_code.startswith('sh'):
                    em_code = f"1.{stock_code[2:]}"
                elif stock_code.startswith('sz'):
                    em_code = f"0.{stock_code[2:]}"
                else:
                    continue
                
                # 东方财富 API
                url = "https://push2.eastmoney.com/api/qt/stock/get"
                params = {
                    'secid': em_code,
                    'fields': 'f57,f58,f43,f44,f45,f46,f47,f48,f49,f50,f51,f52,f53,f54,f55,f56,f84'
                }
                
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
                
                response = requests.get(url, params=params, headers=headers, timeout=5)
                result = response.json()
                
                if result.get('data') and result['data']:
                    data = result['data']
                    
                    # f57: 名称, f43: 当前价, f44: 涨跌, f45: 涨跌幅
                    # f46: 最高, f47: 成交额, f48: 成交量, f49: 最低
                    # f50: 开盘, f51: 昨收
                    
                    name = data.get('f57', '未知')
                    current_price = data.get('f43', 0)
                    change_amount = data.get('f44', 0)
                    change_pct = data.get('f45', 0)
                    
                    # 数据可能需要除以 100 或 10000
                    if current_price > 10000:
                        current_price = current_price / 10000
                    if current_price < 0.1 and current_price > 0:
                        current_price = current_price * 100
                    
                    stocks_data[stock_code] = {
                        '代码': stock_code,
                        '名称': name,
                        '当前价': round(current_price, 2) if current_price else 0,
                        '今日涨跌': round(change_amount / 100, 2) if change_amount else 0,
                        '涨跌幅%': round(change_pct / 100, 2) if change_pct else 0,
                        '最高': round(data.get('f46', 0) / 10000, 2) if data.get('f46') else 0,
                        '最低': round(data.get('f49', 0) / 10000, 2) if data.get('f49') else 0,
                        '开盘': round(data.get('f50', 0) / 10000, 2) if data.get('f50') else 0,
                        '昨收': round(data.get('f51', 0) / 10000, 2) if data.get('f51') else 0,
                        '成交量': int(data.get('f48', 0)) if data.get('f48') else 0,
                        '成交额': int(data.get('f47', 0)) if data.get('f47') else 0,
                    }
                    logger.debug(f"✓ 获取 {stock_code} ({name})")
                    
            except Exception as e:
                logger.debug(f"✗ {stock_code} 失败: {str(e)[:50]}")
                continue
        
        return stocks_data
    
    def get_stocks_from_sina(self, stock_codes: List[str]) -> Dict:
        """从新浪财经获取股票数据"""
        stocks_data = {}
        
        for stock_code in stock_codes:
            try:
                url = f"https://hq.sinajs.cn/list={stock_code}"
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
                
                response = requests.get(url, headers=headers, timeout=5)
                response.encoding = 'gbk'
                text = response.text
                
                # 格式: var hq_str_sh600000="名称,当前价,今日涨跌,涨跌幅,...";
                if 'hq_str_' in text and '="' in text:
                    start = text.find('"') + 1
                    end = text.rfind('"')
                    data_str = text[start:end]
                    parts = data_str.split(',')
                    
                    if len(parts) >= 6:
                        stocks_data[stock_code] = {
                            '代码': stock_code,
                            '名称': parts[0],
                            '当前价': float(parts[1]) if parts[1] else 0,
                            '今日涨跌': float(parts[2]) if parts[2] else 0,
                            '涨跌幅%': float(parts[3].replace('%', '')) if parts[3] else 0,
                            '开盘': float(parts[4]) if len(parts) > 4 and parts[4] else 0,
                            '昨收': float(parts[5]) if len(parts) > 5 and parts[5] else 0,
                            '最高': float(parts[6]) if len(parts) > 6 and parts[6] else 0,
                            '最低': float(parts[7]) if len(parts) > 7 and parts[7] else 0,
                            '成交量': int(parts[8]) if len(parts) > 8 and parts[8] else 0,
                            '成交额': int(parts[9]) if len(parts) > 9 and parts[9] else 0,
                        }
                        logger.debug(f"✓ 获取 {stock_code} ({parts[0]})")
                        
            except Exception as e:
                logger.debug(f"✗ {stock_code} 失败: {str(e)[:50]}")
                continue
        
        return stocks_data
    
    def get_hot_stocks(self) -> List[str]:
        """获取热门股票代码"""
        return [
            'sh000001',  # 上证指数
            'sh600000',  # 浦发银行
            'sh600016',  # 民生银行
            'sh600030',  # 中信证券
            'sh601988',  # 中国银行
            'sh603993',  # 洛阳钼业
            'sz000001',  # 平安银行
            'sz000858',  # 五粮液
            'sz000651',  # 格力电器
            'sz000333',  # 美的集团
            'sz300750',  # 宁德时代
            'sz399001',  # 深证成指
            'sz399006',  # 创业板指
        ]
    
    def crawl_data(self) -> Dict:
        """爬取数据"""
        logger.info("开始爬取数据...")
        
        stocks = self.get_hot_stocks()
        
        # 优先用东方财富（最稳定）
        logger.info("尝试从东方财富获取数据...")
        data = self.get_stocks_from_eastmoney(stocks)
        
        # 如果数据不足，补充新浪数据
        if len(data) < len(stocks) / 2:
            logger.info("数据不足，从新浪财经补充...")
            sina_data = self.get_stocks_from_sina(stocks)
            for code, info in sina_data.items():
                if code not in data:
                    data[code] = info
        
        result = {
            '更新时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            '数据源': '东方财富 + 新浪财经',
            '股票数': len(data),
            '数据': data
        }
        
        logger.info(f"爬取完成，共 {len(data)} 只股票")
        return result
    
    def save_data(self, data: Dict, filename: Optional[str] = None):
        """保存数据"""
        try:
            if filename is None:
                filename = datetime.now().strftime('stock_data_%Y%m%d_%H%M%S.json')
            
            filepath = self.data_dir / filename
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            # 保存最新数据
            latest_path = self.data_dir / 'latest.json'
            with open(latest_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"数据已保存")
            return filepath
        except Exception as e:
            logger.error(f"保存失败: {e}")
            return None
    
    def print_data(self, data: Dict):
        """打印数据"""
        print("\n" + "="*70)
        print(f"更新时间: {data['更新时间']}")
        print(f"数据源: {data['数据源']}")
        print(f"股票数: {data['股票数']}")
        print("="*70)
        
        if data['数据']:
            print("\n【股票数据】")
            for i, (code, info) in enumerate(list(data['数据'].items())[:10], 1):
                name = info.get('名称', 'N/A')
                price = info.get('当前价', 'N/A')
                change = info.get('涨跌幅%', 'N/A')
                
                if isinstance(change, (int, float)):
                    print(f"{i:2}. {name:10} {price:8} ({change:+7.2f}%)")
                else:
                    print(f"{i:2}. {name:10} {price:8} ({change})")
        
        print("="*70 + "\n")
    
    def run_once(self):
        """运行一次"""
        data = self.crawl_data()
        self.save_data(data)
        self.print_data(data)
        return data
    
    def run_continuous(self, interval: int = 60):
        """连续运行"""
        logger.info(f"启动连续爬虫（每{interval}秒更新）")
        
        try:
            while True:
                try:
                    data = self.crawl_data()
                    self.save_data(data)
                    self.print_data(data)
                    
                    logger.info(f"等待 {interval} 秒...")
                    time.sleep(interval)
                except Exception as e:
                    logger.error(f"爬取出错: {e}")
                    time.sleep(interval)
        except KeyboardInterrupt:
            logger.info("爬虫已停止")


if __name__ == '__main__':
    crawler = StockCrawler()
    
    # 运行一次
    print("\n执行爬取...")
    crawler.run_once()
    
    # 或者连续运行
    # crawler.run_continuous(interval=60)
