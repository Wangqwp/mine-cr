#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def test_sina_api():
    """测试新浪 API"""
    print("=" * 60)
    print("测试新浪财经 API")
    print("=" * 60)
    
    test_codes = ['sh000001', 'sh600000', 'sz000001']
    
    for code in test_codes:
        try:
            url = f"https://hq.sinajs.cn/list={code}"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            print(f"\n正在请求: {code}")
            response = requests.get(url, headers=headers, timeout=5)
            response.encoding = 'gbk'
            
            print(f"状态码: {response.status_code}")
            print(f"响应内容: {response.text[:200]}")
            
            # 解析数据
            if 'hq_str_' in response.text:
                start = response.text.find('"') + 1
                end = response.text.rfind('"')
                data_str = response.text[start:end]
                parts = data_str.split(',')
                
                print(f"✓ 成功解析: 名称={parts[0]}, 价格={parts[1]}, 涨跌={parts[3]}")
            else:
                print(f"✗ 响应格式不正确")
                
        except Exception as e:
            print(f"✗ 请求失败: {e}")
    
    print("\n" + "=" * 60)

if __name__ == '__main__':
    test_sina_api()
