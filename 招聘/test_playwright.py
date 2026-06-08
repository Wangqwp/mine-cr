#!/usr/bin/env python3
"""快速测试 Playwright 是否能启动浏览器并抓取猎聘网"""
import sys, os, time
sys.stdout.reconfigure(encoding='utf-8')

from playwright.sync_api import sync_playwright

try:
    with sync_playwright() as p:
        print("Playwright 启动成功")
        browser = p.chromium.launch(
            channel="chrome",
            headless=True,
            args=["--disable-blink-features=AutomationControlled"]
        )
        print("浏览器启动成功")
        
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080},
            locale="zh-CN",
        )
        page = context.new_page()
        
        # 监听网络请求
        requests_caught = []
        page.on("response", lambda resp: requests_caught.append(resp.url) if "api" in resp.url.lower() or "liepin" in resp.url.lower() else None)
        
        print("正在访问猎聘网...")
        page.goto("https://www.liepin.com/zhaopin/?city=010&key=实习", 
                   wait_until="networkidle", 
                   timeout=60000)
        
        # 等待额外渲染时间
        time.sleep(3)
        
        print(f"页面标题: {page.title()}")
        print(f"页面URL: {page.url}")
        
        # 检查所有API请求
        print(f"\n捕获到 {len(requests_caught)} 个相关请求:")
        for url in requests_caught[:15]:
            print(f"  - {url[:120]}")
        
        # 获取页面所有可见文本长度
        body_text = page.inner_text("body")
        print(f"\n页面可见文本长度: {len(body_text)}")
        
        # 尝试多种方式提取职位数据
        result = page.evaluate("""() => {
            // 1. 检查 ant-spin 是否还在（加载中）
            const isLoading = document.querySelector('.ant-spin-spinning') !== null;
            
            // 2. 尝试 select 职位卡片
            const selectors = [
                '.job-card', '.sojob-item', '[class*=job-card]', 
                '.job-list-item', '.list-item', '.position-card',
                '.ant-card', '.job-title-box', '[class*=jobTitle]',
                '.job-item', '.resume-list-item'
            ];
            
            let cards = [];
            for (const sel of selectors) {
                const found = document.querySelectorAll(sel);
                if (found.length > 0) {
                    cards = Array.from(found);
                    break;
                }
            }
            
            // 3. 检查是否有 React 渲染的容器
            const rootEls = document.querySelectorAll('#root, #app, [data-reactroot]');
            
            return {
                isLoading: isLoading,
                jobCardsCount: cards.length,
                allDivs: document.querySelectorAll('div').length,
                rootEls: rootEls.length,
                sampleText: document.body.innerText.substring(0, 500),
            };
        }""")
        
        print(f"\n页面分析: {result}")
        
        # 等待更长时间看看是否数据加载
        if result['isLoading']:
            print("\n页面仍在加载中，等待额外5秒...")
            time.sleep(5)
            
            result2 = page.evaluate("""() => {
                const isLoading = document.querySelector('.ant-spin-spinning') !== null;
                const cards = document.querySelectorAll('[class*=job]');
                return {
                    isLoading: isLoading,
                    jobLikeElements: cards.length,
                    text: document.body.innerText.substring(0, 300)
                };
            }""")
            print(f"再次检查: {result2}")
        
        # 保存最终页面快照
        with open(os.path.join(os.path.dirname(__file__), "liepin_final.html"), "w", encoding="utf-8") as f:
            f.write(page.content())
        print("最终页面已保存")
        
        browser.close()
        print("测试完成！")
        
except Exception as e:
    print(f"错误: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()