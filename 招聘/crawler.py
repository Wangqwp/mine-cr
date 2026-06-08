#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
实习/校园招聘信息爬虫
使用 Playwright 无头浏览器抓取猎聘网招聘数据
"""

import argparse
import csv
import json
import logging
import os
import sys
import time
from datetime import datetime
from typing import Optional

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

# ===================== 配置 =====================

REQUEST_TIMEOUT = 30000  # 毫秒
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(OUTPUT_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(os.path.join(BASE_DIR, "crawler.log"), encoding="utf-8"),
    ],
)
log = logging.getLogger(__name__)

# ===================== 城市代码映射（猎聘网） =====================

LIEQIN_CITY_MAP = {
    "北京": "010",
    "上海": "020",
    "广州": "050",
    "深圳": "040",
    "杭州": "070",
    "成都": "090",
    "南京": "060",
    "武汉": "160",
    "西安": "240",
    "重庆": "100",
    "长沙": "180",
    "苏州": "080",
    "天津": "030",
    "厦门": "300",
    "福州": "290",
    "合肥": "210",
    "郑州": "150",
    "青岛": "120",
    "大连": "220",
    "昆明": "250",
    "沈阳": "230",
    "济南": "110",
    "哈尔滨": "280",
    "长春": "270",
    "石家庄": "140",
    "太原": "130",
    "南昌": "260",
    "南宁": "310",
    "海口": "320",
    "贵阳": "330",
    "兰州": "170",
    "银川": "350",
    "西宁": "380",
    "拉萨": "390",
    "呼和浩特": "340",
    "乌鲁木齐": "360",
}

# ===================== 猎聘网爬虫 =====================

class LiepinCrawler:
    """猎聘网爬虫 - 使用 Playwright 无头浏览器"""

    BASE_URL = "https://www.liepin.com"
    SEARCH_URL = "https://www.liepin.com/zhaopin/"

    def __init__(self, city: str, keyword: str, headless: bool = True):
        self.city = city
        self.keyword = keyword
        self.headless = headless
        self.results = []
        self.city_code = LIEQIN_CITY_MAP.get(city, "010")

    def run(self, max_pages: int = 3) -> list:
        all_jobs = []
        log.info(f"[猎聘网] 启动浏览器，开始爬取: 城市={self.city}, 关键词={self.keyword}")

        with sync_playwright() as p:
            browser = p.chromium.launch(
                channel="chrome",
                headless=self.headless,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                ],
            )
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
                viewport={"width": 1920, "height": 1080},
                locale="zh-CN",
            )
            page = context.new_page()

            try:
                for page_num in range(1, max_pages + 1):
                    log.info(f"[猎聘网] 正在爬取第 {page_num}/{max_pages} 页...")
                    items = self._fetch_page(page, page_num)
                    if items is None:
                        log.warning(f"[猎聘网] 第 {page_num} 页出错，结束")
                        break
                    if not items:
                        log.info(f"[猎聘网] 第 {page_num} 页无数据，结束")
                        break
                    all_jobs.extend(items)
                    time.sleep(2)
            except Exception as e:
                log.error(f"[猎聘网] 爬取异常: {e}")
            finally:
                browser.close()

        log.info(f"[猎聘网] 完成，共获取 {len(all_jobs)} 条记录")
        self.results = all_jobs
        return all_jobs

    def _fetch_page(self, page, page_num: int) -> Optional[list]:
        try:
            if page_num == 1:
                url = f"{self.SEARCH_URL}?city={self.city_code}&key={self.keyword}"
            else:
                url = f"{self.SEARCH_URL}?city={self.city_code}&key={self.keyword}&curPage={page_num - 1}"

            log.info(f"[猎聘网] 访问: {url}")

            page.goto(url, wait_until="domcontentloaded", timeout=REQUEST_TIMEOUT)

            # 等待职位卡片加载
            try:
                page.wait_for_selector(".job-card-pc-container", timeout=15000)
            except PlaywrightTimeout:
                log.warning("[猎聘网] 等待职位卡片超时，检查页面状态")
                try:
                    page.wait_for_selector("[class*=job-card]", timeout=5000)
                except PlaywrightTimeout:
                    pass

            # 额外等待确保渲染完成
            time.sleep(2)

            # 执行 JS 提取所有职位数据
            jobs_data = page.evaluate("""() => {
                const items = [];
                
                // 猎聘网职位卡片容器（基于实际HTML结构）
                const cards = document.querySelectorAll('.job-card-pc-container, [class*="job-card"], [class*="sojob-item"]');
                
                cards.forEach(card => {
                    try {
                        // 职位名称 - 从 ellipsis-1 带 title 属性的 div 获取
                        const titleEl = card.querySelector('.ellipsis-1[title]');
                        const title = titleEl ? titleEl.getAttribute('title') || titleEl.textContent.trim() : '';
                        
                        // 详情链接
                        const linkEl = card.querySelector('a[href*="/lptjob/"]');
                        let link = '';
                        if (linkEl) {
                            link = linkEl.href;
                        }
                        
                        // 薪资
                        const salaryEls = card.querySelectorAll('[class*="E8PWS"], [class*="salary"], [class*="money"]');
                        let salary = '';
                        for (const el of salaryEls) {
                            const text = el.textContent.trim();
                            if (text && /[0-9]/.test(text) && /元|K|k|万/.test(text)) {
                                salary = text;
                                break;
                            }
                        }
                        if (!salary) {
                            salary = card.querySelector('[class*="E8PWS"]')?.textContent?.trim() || '';
                        }
                        
                        // 城市
                        const cityEl = card.querySelector('[class*="__9nJ"] .ellipsis-1');
                        const city = cityEl ? cityEl.textContent.trim() : '';
                        
                        // 标签（实习、月数、学历等）
                        const tagEls = card.querySelectorAll('[class*="hJbMl"], [class*="tag"]');
                        const tags = [];
                        tagEls.forEach(el => {
                            const t = el.textContent.trim();
                            if (t) tags.push(t);
                        });
                        
                        // 公司名称
                        const companyEl = card.querySelector('[class*="K6Y1c"], [class*="company-name"]');
                        const company = companyEl ? companyEl.textContent.trim() : '';
                        
                        // 公司信息（行业、规模等）
                        const companyInfoEl = card.querySelector('[class*="hFeAm"]');
                        const companyInfo = companyInfoEl ? companyInfoEl.textContent.trim() : '';
                        
                        // 招聘者
                        const recruiterEl = card.querySelector('[class*="jHFC5"]');
                        const recruiter = recruiterEl ? recruiterEl.textContent.trim() : '';
                        
                        // 在线状态
                        const onlineEl = card.querySelector('[class*="WbQER"]');
                        const online = onlineEl ? onlineEl.textContent.trim() : '';
                        
                        if (title) {
                            items.push({
                                title: title,
                                company: company,
                                companyInfo: companyInfo,
                                salary: salary,
                                city: city,
                                tags: tags,
                                recruiter: recruiter,
                                online: online,
                                url: link,
                            });
                        }
                    } catch(e) {
                        // 单个卡片解析异常，跳过
                    }
                });
                
                return items;
            }""")

            if not jobs_data:
                log.info(f"[猎聘网] 第{page_num}页 JS 提取无数据")
                return []

            log.info(f"[猎聘网] 第{page_num}页提取到 {len(jobs_data)} 个职位")

            # 格式化为统一输出
            items = []
            for job in jobs_data:
                item = self._format_job(job)
                if item:
                    items.append(item)

            return items

        except Exception as e:
            log.error(f"[猎聘网] 第{page_num}页请求异常: {e}")
            return None

    def _format_job(self, job: dict) -> Optional[dict]:
        try:
            # 从 tags 中分离出学历、经验等信息
            tags = job.get("tags", [])
            edu = ""
            exp = ""
            duration = ""
            job_type = ""
            for t in tags:
                if "本科" in t or "硕士" in t or "博士" in t or "大专" in t or "不限" in t or "学历" in t:
                    edu = t
                elif "个月" in t or "月" in t:
                    duration = t
                elif "实习" in t or "全职" in t or "兼职" in t:
                    job_type = t
                elif "提供转正" in t:
                    exp = t
                else:
                    # 尝试识别经验要求
                    if "年" in t and ("以上" in t or t.replace("年","").strip().isdigit()):
                        exp = t

            return {
                "平台": "猎聘网",
                "职位名称": job.get("title", ""),
                "公司名称": job.get("company", ""),
                "公司信息": job.get("companyInfo", ""),
                "工作城市": job.get("city", self.city),
                "薪资待遇": job.get("salary", ""),
                "学历要求": edu,
                "经验要求": exp,
                "实习时长": duration,
                "岗位类型": job_type,
                "联系人": job.get("recruiter", ""),
                "在线状态": job.get("online", ""),
                "详情链接": job.get("url", ""),
            }
        except Exception as e:
            log.warning(f"格式化职位数据异常: {e}")
            return None


# ===================== 数据导出 =====================

def export_to_csv(jobs: list, filepath: str):
    if not jobs:
        log.warning("无数据可导出 CSV")
        return
    all_keys = []
    for job in jobs:
        for k in job:
            if k not in all_keys:
                all_keys.append(k)
    with open(filepath, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(all_keys)
        for job in jobs:
            row = [job.get(k, "") for k in all_keys]
            writer.writerow(row)
    log.info(f"CSV 已导出: {filepath}")


def export_to_json(jobs: list, filepath: str):
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(jobs, f, ensure_ascii=False, indent=2)
    log.info(f"JSON 已导出: {filepath}")


def export_to_markdown(jobs: list, filepath: str, city: str, keyword: str):
    lines = [
        f"# {city}{keyword}招聘信息",
        "",
        f"> 抓取时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"> 城市: {city} | 关键词: {keyword} | 记录数: {len(jobs)}",
        "",
        "---",
        "",
    ]
    for i, job in enumerate(jobs, 1):
        lines.append(f"## {i}. {job.get('职位名称', '未知')}")
        lines.append(f"")
        lines.append(f"- **公司**: {job.get('公司名称', '未知')}")
        lines.append(f"- **平台**: {job.get('平台', '未知')}")
        lines.append(f"- **薪资**: {job.get('薪资待遇', '面议')}")
        lines.append(f"- **城市**: {job.get('工作城市', city)}")
        lines.append(f"- **学历**: {job.get('学历要求', '不限')}")
        lines.append(f"- **经验**: {job.get('经验要求', '不限')}")
        if job.get("公司信息"):
            lines.append(f"- **公司信息**: {job['公司信息']}")
        if job.get("实习时长"):
            lines.append(f"- **实习时长**: {job['实习时长']}")
        if job.get("联系人"):
            lines.append(f"- **联系人**: {job['联系人']}")
        if job.get("详情链接"):
            lines.append(f"- **链接**: {job['详情链接']}")
        lines.append("")
        lines.append("---")
        lines.append("")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    log.info(f"Markdown 已导出: {filepath}")


# ===================== 主程序 =====================

def main():
    parser = argparse.ArgumentParser(
        description="实习/校园招聘信息爬虫 - 猎聘网",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 爬取北京的实习岗位
  python crawler.py -c 北京 -k 实习

  # 爬取上海的人工智能岗位，输出 JSON
  python crawler.py -c 上海 -k 人工智能 -o json

  # 爬取 5 页数据
  python crawler.py -c 深圳 -k 游戏 --max-pages 5

  # 列出支持的城市
  python crawler.py --list-cities
        """,
    )
    parser.add_argument("-c", "--city", default="北京", help="目标城市")
    parser.add_argument("-k", "--keyword", default="实习", help="搜索关键词/行业")
    parser.add_argument("--max-pages", type=int, default=3, help="最大页数 (默认3)")
    parser.add_argument("-o", "--output", default="all", choices=["all", "csv", "json", "md", "markdown"], help="输出格式")
    parser.add_argument("--list-cities", action="store_true", help="列出支持的城市")
    parser.add_argument("--no-export", action="store_true", help="不导出文件，仅终端输出")
    parser.add_argument("--visible", action="store_true", help="显示浏览器窗口（调试用）")

    args = parser.parse_args()

    if args.list_cities:
        print("支持的城市: ")
        for c in LIEQIN_CITY_MAP:
            print(f"  - {c}")
        return

    # 验证城市
    if args.city not in LIEQIN_CITY_MAP:
        log.warning(f"不支持的城市: {args.city}，将使用北京")
        args.city = "北京"

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_filename = f"{args.city}_{args.keyword}_{timestamp}"

    log.info("=" * 60)
    log.info("招聘信息爬虫 启动")
    log.info(f"城市: {args.city}")
    log.info(f"关键词: {args.keyword}")
    log.info(f"最大页数: {args.max_pages}")
    log.info("=" * 60)

    # 使用猎聘网爬虫
    crawler = LiepinCrawler(args.city, args.keyword, headless=not args.visible)

    try:
        jobs = crawler.run(max_pages=args.max_pages)
    except Exception as e:
        log.error(f"爬取失败: {e}")
        jobs = []

    log.info(f"\n共获取 {len(jobs)} 条招聘信息")

    for job in jobs:
        print(f"  [{job.get('平台','?')}] {job.get('职位名称','?')} - {job.get('公司名称','?')} {job.get('薪资待遇','?')}")

    if not args.no_export and jobs:
        output_formats = ["csv", "json", "md"] if args.output == "all" else [args.output]
        for fmt in output_formats:
            fmt = fmt.replace("markdown", "md")
            fp = os.path.join(OUTPUT_DIR, f"{base_filename}.{fmt}")
            if fmt == "csv":
                export_to_csv(jobs, fp)
            elif fmt == "json":
                export_to_json(jobs, fp)
            elif fmt == "md":
                export_to_markdown(jobs, fp, args.city, args.keyword)
        print(f"\n文件已保存到: {OUTPUT_DIR}")
    elif not jobs:
        log.warning("未获取到任何数据，可尝试 --visible 参数查看浏览器行为")


if __name__ == "__main__":
    # 在 VS Code 中直接按 ▶ 运行时，使用默认参数爬取北京的实习岗位
    if len(sys.argv) <= 1:
        sys.argv = ["crawler.py", "-c", "北京", "-k", "实习"]
    main()
