import requests
import json
import time
from datetime import datetime
from pathlib import Path
import logging
from typing import Dict, List, Optional
import pandas as pd

try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False

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
    """中国股市实时数据爬虫"""
    
    def __init__(self, data_dir: str = './stock_data'):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        # 常见的A股代码前缀
        self.sh_prefix = '1'  # 上海交易所
        self.sz_prefix = '0'  # 深圳交易所
        
    def get_stock_data_sina(self, stock_codes: List[str]) -> Dict:
        """从新浪财经获取股票数据"""
        try:
            stocks_data = {}
            
            for stock_code in stock_codes:
                try:
                    # 新浪财经 API
                    url = f"https://hq.sinajs.cn/list={stock_code}"
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                    }
                    
                    response = requests.get(url, headers=headers, timeout=5)
                    response.encoding = 'gbk'
                    text = response.text
                    
                    # 解析数据，格式: var hq_str_sh600000="浦发银行,8.95,+0.09,+1.02,123456,987654321,987654,987654,0,0";
                    if 'hq_str_' in text:
                        # 提取股票代码和数据
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
                                '成交量': int(parts[8]) if len(parts) > 8 and parts[8] else 0,
                                '成交额': int(parts[9]) if len(parts) > 9 and parts[9] else 0,
                                '最高': float(parts[5]) if len(parts) > 5 and parts[5] else 0,
                                '最低': float(parts[6]) if len(parts) > 6 and parts[6] else 0,
                                '开盘': float(parts[4]) if len(parts) > 4 and parts[4] else 0,
                                '昨收': float(parts[7]) if len(parts) > 7 and parts[7] else 0,
                            }
                            logger.debug(f"成功获取 {stock_code} 数据: {parts[0]}")
                except Exception as e:
                    logger.debug(f"获取 {stock_code} 失败: {e}")
                    continue
            
            return stocks_data
            
        except Exception as e:
            logger.error(f"新浪财经数据获取失败: {e}")
            return {}
    
    def get_stock_data_eastmoney(self, stock_codes: List[str]) -> Dict:
        """从东方财富获取股票数据（备选方案）"""
        try:
            stocks_data = {}
            
            for stock_code in stock_codes:
                try:
                    # 将代码转换为东方财富格式
                    # sh600000 -> 1.600000, sz000001 -> 0.000001
                    if stock_code.startswith('sh'):
                        em_code = f"1.{stock_code[2:]}"
                    elif stock_code.startswith('sz'):
                        em_code = f"0.{stock_code[2:]}"
                    else:
                        continue
                    
                    url = f"https://push2.eastmoney.com/api/qt/stock/get"
                    params = {
                        'secid': em_code,
                        'fields': 'f57,f58,f43,f44,f45,f46,f47,f48,f49,f50,f51,f52,f53,f54,f55,f56'
                    }
                    
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                    }
                    
                    response = requests.get(url, params=params, headers=headers, timeout=5)
                    result = response.json()
                    
                    if result.get('data'):
                        data = result['data']
                        name = data.get('f57', '未知')
                        price = data.get('f43', 0) / 100.0 if data.get('f43') else 0
                        change = data.get('f44', 0) / 100.0 if data.get('f44') else 0
                        change_pct = data.get('f45', 0) / 100.0 if data.get('f45') else 0
                        
                        stocks_data[stock_code] = {
                            '代码': stock_code,
                            '名称': name,
                            '当前价': price,
                            '今日涨跌': change,
                            '涨跌幅%': change_pct,
                            '成交量': data.get('f48', 0),
                            '成交额': data.get('f47', 0),
                            '最高': data.get('f46', 0) / 100.0 if data.get('f46') else 0,
                            '最低': data.get('f49', 0) / 100.0 if data.get('f49') else 0,
                            '开盘': data.get('f50', 0) / 100.0 if data.get('f50') else 0,
                            '昨收': data.get('f51', 0) / 100.0 if data.get('f51') else 0,
                        }
                        logger.debug(f"成功从东方财富获取 {stock_code}")
                except Exception as e:
                    logger.debug(f"东方财富获取 {stock_code} 失败: {e}")
                    continue
            
            return stocks_data
        
        except Exception as e:
            logger.error(f"东方财富数据获取失败: {e}")
            return {}
    
    def get_hot_stocks(self) -> List[str]:
        """获取热门股票代码"""
        # 包含沪深两市的一些知名股票代码示例
        hot_stocks = [
            'sh600000',  # 浦发银行
            'sh600016',  # 民生银行
            'sh600028',  # 中国石化
            'sh600030',  # 中信证券
            'sh601988',  # 中国银行
            'sh603993',  # 洛阳钼业
            'sz000001',  # 平安银行
            'sz000858',  # 五粮液
            'sz000651',  # 格力电器
            'sz000333',  # 美的集团
            'sz300750',  # 宁德时代
            'sz300059',  # 东方财富
            'sz000858',  # 五粮液
        ]
        return hot_stocks
    
    def get_index_data(self) -> Dict:
        """获取主要指数数据"""
        try:
            # 指数代码：沪指、深指、创业板指
            index_codes = ['sh000001', 'sz399001', 'sz399006']
            index_data = self.get_stock_data_sina(index_codes)
            
            index_names = {
                'sh000001': '上证指数',
                'sz399001': '深证成指',
                'sz399006': '创业板指'
            }
            
            for code, name in index_names.items():
                if code in index_data:
                    index_data[code]['名称'] = name
            
            return index_data
        
        except Exception as e:
            logger.error(f"指数数据获取失败: {e}")
            return {}
    
    def get_stock_data_yfinance(self, stock_codes: List[str]) -> Dict:
        """使用 yfinance 获取股票数据（最稳定的方式）"""
        if not YFINANCE_AVAILABLE:
            return {}
        
        try:
            stocks_data = {}
            
            # 转换代码格式：sh600000 -> 600000.SS, sz000001 -> 000001.SZ
            converted_codes = []
            code_map = {}
            
            for code in stock_codes:
                if code.startswith('sh'):
                    yf_code = f"{code[2:]}.SS"
                    code_map[yf_code] = code
                    converted_codes.append(yf_code)
                elif code.startswith('sz'):
                    yf_code = f"{code[2:]}.SZ"
                    code_map[yf_code] = code
                    converted_codes.append(yf_code)
            
            if not converted_codes:
                return {}
            
            # 批量获取数据
            for yf_code in converted_codes:
                try:
                    ticker = yf.Ticker(yf_code)
                    data = ticker.info
                    
                    if data and 'currentPrice' in data:
                        original_code = code_map[yf_code]
                        stocks_data[original_code] = {
                            '代码': original_code,
                            '名称': data.get('longName', data.get('shortName', 'N/A')),
                            '当前价': data.get('currentPrice', 0),
                            '今日涨跌': data.get('currentPrice', 0) - data.get('open', 0),
                            '涨跌幅%': (data.get('currentPrice', 0) - data.get('previousClose', 0)) / data.get('previousClose', 1) * 100 if data.get('previousClose') else 0,
                            '成交量': data.get('volume', 0),
                            '成交额': data.get('marketCap', 0),
                            '最高': data.get('dayHigh', 0),
                            '最低': data.get('dayLow', 0),
                            '开盘': data.get('open', 0),
                            '昨收': data.get('previousClose', 0),
                        }
                        logger.debug(f"成功从 yfinance 获取 {original_code}")
                except Exception as e:
                    logger.debug(f"yfinance 获取 {yf_code} 失败: {e}")
                    continue
            
            return stocks_data
        
        except Exception as e:
            logger.error(f"yfinance 数据获取失败: {e}")
            return {}
    
    def crawl_all_data(self) -> Dict:
        """爬取所有数据"""
        logger.info("开始爬取股市数据...")
        
        # 先尝试获取指数
        index_data = self.get_index_data()
        
        # 获取热门股票 - 多重备选方案
        hot_stocks = self.get_hot_stocks()
        stocks_data = self.get_stock_data_sina(hot_stocks)
        
        # 如果新浪数据为空或很少，尝试其他数据源
        if len(stocks_data) < len(hot_stocks) * 0.3:
            logger.info(f"新浪财经数据不足 ({len(stocks_data)}/{len(hot_stocks)})，尝试东方财富...")
            em_data = self.get_stock_data_eastmoney(hot_stocks)
            # 合并数据
            for code, info in em_data.items():
                if code not in stocks_data:
                    stocks_data[code] = info
        
        # 如果还是没数据，尝试 yfinance
        if len(stocks_data) < len(hot_stocks) * 0.3 and YFINANCE_AVAILABLE:
            logger.info(f"数据仍不足，尝试 yfinance...")
            yf_data = self.get_stock_data_yfinance(hot_stocks)
            for code, info in yf_data.items():
                if code not in stocks_data:
                    stocks_data[code] = info
        
        all_data = {
            '更新时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            '指数': index_data,
            '热门股票': stocks_data,
        }
        
        logger.info(f"成功爬取数据，包含指数: {len(all_data['指数'])} 个，股票: {len(all_data['热门股票'])} 个")
        return all_data
    
    def save_data(self, data: Dict, filename: Optional[str] = None):
        """保存数据到 JSON 文件"""
        try:
            if filename is None:
                filename = datetime.now().strftime('stock_data_%Y%m%d_%H%M%S.json')
            
            filepath = self.data_dir / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            # 同时保存最新的数据为 latest.json
            latest_path = self.data_dir / 'latest.json'
            with open(latest_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"数据已保存到: {filepath}")
            return filepath
        
        except Exception as e:
            logger.error(f"数据保存失败: {e}")
            return None
    
    def load_latest_data(self) -> Optional[Dict]:
        """加载最新保存的数据"""
        try:
            latest_path = self.data_dir / 'latest.json'
            if latest_path.exists():
                with open(latest_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return None
        
        except Exception as e:
            logger.error(f"数据加载失败: {e}")
            return None
    
    def print_summary(self, data: Dict):
        """打印数据摘要"""
        print("\n" + "="*60)
        print(f"股市数据更新时间: {data['更新时间']}")
        print("="*60)
        
        print("\n【主要指数】")
        for code, info in data['指数'].items():
            if isinstance(info, dict):
                print(f"  {info.get('名称', code)}: {info.get('当前价', 0):.2f} "
                      f"({info.get('涨跌幅%', 0):+.2f}%)")
        
        print("\n【热门股票 Top 5】")
        stocks = list(data['热门股票'].items())
        # 按涨幅排序
        stocks_sorted = sorted(stocks, 
                               key=lambda x: x[1].get('涨跌幅%', 0) if isinstance(x[1], dict) else 0, 
                               reverse=True)
        
        for i, (code, info) in enumerate(stocks_sorted[:5], 1):
            if isinstance(info, dict):
                print(f"  {i}. {info.get('名称', code)} ({code}): {info.get('当前价', 0):.2f} "
                      f"({info.get('涨跌幅%', 0):+.2f}%)")
        
        print("="*60 + "\n")
    
    def run_continuous(self, interval: int = 60):
        """连续运行爬虫，定时更新数据"""
        logger.info(f"爬虫启动，每 {interval} 秒更新一次数据")
        
        try:
            while True:
                try:
                    # 爬取数据
                    data = self.crawl_all_data()
                    
                    # 保存数据
                    self.save_data(data)
                    
                    # 打印摘要
                    self.print_summary(data)
                    
                    # 等待下一次更新
                    logger.info(f"等待 {interval} 秒后进行下一次更新...")
                    time.sleep(interval)
                
                except Exception as e:
                    logger.error(f"爬取过程中出错: {e}")
                    time.sleep(interval)
        
        except KeyboardInterrupt:
            logger.info("爬虫已停止")
    
    def run_once(self):
        """运行一次爬虫"""
        data = self.crawl_all_data()
        self.save_data(data)
        self.print_summary(data)
        return data


if __name__ == '__main__':
    # 创建爬虫实例
    crawler = StockCrawler()
    
    # 运行一次（测试）
    print("执行首次爬取...")
    crawler.run_once()
    
    # 或者连续运行（每分钟更新）
    # print("启动连续爬虫模式...")
    # crawler.run_continuous(interval=60)
