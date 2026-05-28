#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
直接测试各个数据源
"""
import requests

def test_sina():
    """测试新浪财经接口"""
    print("\n【测试新浪财经】")
    try:
        url = "https://hq.sinajs.cn/list=sh000001"
        headers = {'User-Agent': 'Mozilla/5.0'}
        resp = requests.get(url, headers=headers, timeout=5)
        resp.encoding = 'gbk'
        print(f"状态: {resp.status_code}")
        print(f"返回: {resp.text[:200]}")
        
        if 'hq_str_' in resp.text and '=' in resp.text:
            print("✓ 格式正确，可以解析")
            return True
        else:
            print("✗ 格式不符")
            return False
    except Exception as e:
        print(f"✗ 失败: {e}")
        return False

def test_eastmoney():
    """测试东方财富接口"""
    print("\n【测试东方财富】")
    try:
        url = "https://push2.eastmoney.com/api/qt/stock/get"
        params = {'secid': '1.000001', 'fields': 'f57,f58,f43,f44,f45'}
        headers = {'User-Agent': 'Mozilla/5.0'}
        resp = requests.get(url, params=params, headers=headers, timeout=5)
        data = resp.json()
        print(f"状态: {resp.status_code}")
        print(f"返回: {str(data)[:200]}")
        
        if data.get('data'):
            print("✓ 有数据返回")
            return True
        else:
            print("✗ 无数据")
            return False
    except Exception as e:
        print(f"✗ 失败: {e}")
        return False

if __name__ == '__main__':
    print("="*60)
    print("股市数据源测试")
    print("="*60)
    
    sina_ok = test_sina()
    em_ok = test_eastmoney()
    
    print("\n" + "="*60)
    print("测试结果:")
    print(f"  新浪财经: {'✓ 可用' if sina_ok else '✗ 不可用'}")
    print(f"  东方财富: {'✓ 可用' if em_ok else '✗ 不可用'}")
    print("="*60)
