#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
实习/校园招聘信息爬虫
支持平台: 实习僧、BOSS直聘、拉勾网
可根据地区和行业类型爬取招聘信息
"""

import argparse
import csv
import json
import logging
import os
import random
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import Optional
from urllib.parse import quote, urlencode

import requests
from bs4 import BeautifulSoup

# ===================== 配置 =====================

REQUEST_TIMEOUT = 15
MAX_RETRIES = 3
RETRY_DELAY = 2
CONCURRENCY = 5
REQUEST_DELAY = (1, 3)

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

# ===================== 平台支持的城市映射 =====================

CITY_MAP = {
    "北京": "北京",
    "上海": "上海",
    "广州": "广州",
    "深圳": "深圳",
    "杭州": "杭州",
    "成都": "成都",
    "南京": "南京",
    "武汉": "武汉",
    "西安": "西安",
    "重庆": "重庆",
    "长沙": "长沙",
    "苏州": "苏州",
    "天津": "天津",
    "厦门": "厦门",
    "福州": "福州",
    "合肥": "合肥",
    "郑州": "郑州",
    "青岛": "青岛",
    "大连": "大连",
    "昆明": "昆明",
    "沈阳": "沈阳",
    "济南": "济南",
    "哈尔滨": "哈尔滨",
    "长春": "长春",
    "石家庄": "石家庄",
    "太原": "太原",
    "南昌": "南昌",
    "南宁": "南宁",
    "海口": "海口",
    "贵阳": "贵阳",
    "兰州": "兰州",
    "银川": "银川",
    "西宁": "西宁",
    "拉萨": "拉萨",
    "呼和浩特": "呼和浩特",
    "乌鲁木齐": "乌鲁木齐",
}

# 行业分类（可根据需要扩展）
INDUSTRY_MAP = {
    "互联网": "互联网",
    "金融": "金融",
    "教育": "教育",
    "医疗": "医疗",
    "房地产": "房地产",
    "制造业": "制造业",
    "通信": "通信",
    "电子": "电子",
    "新能源": "新能源",
    "生物医药": "生物医药",
    "人工智能": "人工智能",
    "大数据": "大数据",
    "游戏": "游戏",
    "电商": "电商",
    "物流": "物流",
    "汽车": "汽车",
    "传媒": "传媒",
    "法律": "法律",
    "咨询": "咨询",
    "会计": "会计",
    "建筑": "建筑",
    "化工": "化工",
    "农业": "农业",
    "环保": "环保",
    "旅游": "旅游",
    "餐饮": "餐饮",
    "零售": "零售",
}

# ===================== 通用工具 =====================

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
]


def get_headers(referer: str = "") -> dict:
    headers = {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
    }
    if referer:
        headers["Referer"] = referer
    return headers


def random_delay():
    time.sleep(random.uniform(*REQUEST_DELAY))


def safe_request(url: str, headers: dict = None, params: dict = None, timeout: int = REQUEST_TIMEOUT) -> Optional[requests.Response]:
    if headers is None:
        headers = get_headers()
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = requests.get(url, headers=headers, params=params, timeout=timeout)
            resp.raise_for_status()
            return resp
        except requests.exceptions.Timeout:
            log.warning(f"[{attempt}/{MAX_RETRIES}] 请求超时: {url}")
        except requests.exceptions.ConnectionError as e:
            log.warning(f"[{attempt}/{MAX_RETRIES}] 连接错误: {e}")
        except requests.exceptions.HTTPError as e:
            status = e.response.status_code if e.response is not None else "?"
            log.warning(f"[{attempt}/{MAX_RETRIES}] HTTP {status}: {url}")
            if status in (403, 404):
                break
        except Exception as e:
            log.warning(f"[{attempt}/{MAX_RETRIES}] 请求异常: {e}")
        if attempt < MAX_RETRIES:
            time.sleep(RETRY_DELAY * attempt)
    return None


def clean_text(text: str) -> str:
    if not text:
        return ""
    return re.sub(r"\s+", " ", text).strip()


def parse_salary(text: str) -> dict:
    if not text:
        return {"min": 0, "max": 0, "unit": "元/天"}
    text = clean_text(text)
    nums = re.findall(r"(\d+(?:\.\d+)?)", text)
    if "K" in text or "k" in text:
        unit = "K/月"
    elif "天" in text or "日" in text:
        unit = "元/天"
    elif "月" in text:
        unit = "元/月"
    elif "年" in text:
        unit = "万/年"
    else:
        unit = "元/月"
    if len(nums) >= 2:
        return {"min": float(nums[0]), "max": float(nums[1]), "unit": unit}
    elif len(nums) == 1:
        return {"min": float(nums[0]), "max": float(nums[0]), "unit": unit}
    return {"min": 0, "max": 0, "unit": unit}


# ===================== 实习僧爬虫 =====================

class ShixisengCrawler:
    """实习僧爬虫 - 专注实习/校招的垂直平台"""

    BASE_URL = "https://www.shixiseng.com"
    API_URL = "https://api.shixiseng.com/api/jobs"

    def __init__(self, city: str, keyword: str, job_type: str = "intern"):
        self.city = city
        self.keyword = keyword
        self.job_type = job_type  # intern 实习, campus 校招, practice 兼职
        self.session = requests.Session()
        self.results = []

    def _build_params(self, page: int = 1) -> dict:
        city_code = CITY_MAP.get(self.city, self.city)
        params = {
            "keyword": self.keyword,
            "city": city_code,
            "type": self.job_type,
            "p": page,
            "ps": "20",
            "order": "0",
        }
        return params

    def fetch_page(self, page: int = 1) -> list:
        params = self._build_params(page)
        headers = get_headers(referer=f"{self.BASE_URL}/intern")
        resp = safe_request(self.API_URL, headers=headers, params=params)

        if not resp:
            return []

        try:
            data = resp.json()
        except Exception:
            log.error(f"实习僧 API 返回非 JSON 数据 (第{page}页)")
            return []

        if data.get("code") != 0:
            log.warning(f"实习僧 API 返回异常: {data.get('msg', '未知错误')}")
            return []

        jobs = data.get("data", {}).get("list", [])
        items = []
        for job in jobs:
            try:
                item = self._parse_job(job)
                if item:
                    items.append(item)
            except Exception as e:
                log.warning(f"解析职位信息异常: {e}")
                continue
        return items

    def _parse_job(self, job: dict) -> Optional[dict]:
        try:
            name = job.get("name", "")
            if not name:
                return None

            company_name = job.get("company_name", "") or job.get("enterprise", {}).get("shortName", "") or ""
            company_size = job.get("company_size", "") or job.get("enterprise", {}).get("sizeName", "") or ""
            company_type = job.get("industry", "") or job.get("enterprise", {}).get("industry", "") or ""
            company_stage = job.get("company_stage", "") or job.get("enterprise", {}).get("stageName", "") or ""

            salary_text = job.get("salary", "")
            salary = parse_salary(salary_text)

            city = job.get("cityName", "") or job.get("city", "") or ""
            district = job.get("district", "") or ""

            edu = job.get("education", "") or job.get("educationName", "") or ""
            exp = job.get("experience", "") or job.get("experienceName", "") or ""

            tags = job.get("tags", []) or []
            if isinstance(tags, str):
                tags = tags.split(",") if tags else []

            welfare = job.get("welfare", "") or job.get("benefits", "") or ""

            days_per_week = job.get("weekTime", "") or job.get("daysPerWeek", "") or ""
            months = job.get("months", "") or job.get("duration", "") or ""

            detail_url = job.get("link", "") or f"{self.BASE_URL}/intern/{job.get('id', '')}"
            publish_time = job.get("createTime", "") or job.get("updatedAt", "") or ""
            gender = job.get("gender", "") or ""
            deadline = job.get("deadline", "") or ""

            return {
                "平台": "实习僧",
                "职位名称": name,
                "公司名称": company_name,
                "公司规模": company_size,
                "公司类型": company_type,
                "融资阶段": company_stage,
                "工作城市": city,
                "工作区域": district,
                "薪资待遇": salary_text,
                "薪资结构": salary,
                "学历要求": edu,
                "经验要求": exp,
                "职位标签": "、".join(tags) if tags else "",
                "福利待遇": welfare,
                "每周天数": days_per_week,
                "实习月数": months,
                "性别要求": gender,
                "报名截止": deadline,
                "发布时间": publish_time,
                "详情链接": detail_url,
                "岗位类型": self.job_type,
            }
        except Exception as e:
            log.warning(f"实习僧 解析职位异常: {e}")
            return None

    def run(self, max_pages: int = 3) -> list:
        all_jobs = []
        log.info(f"[实习僧] 开始爬取: 城市={self.city}, 关键词={self.keyword}, 类型={self.job_type}")

        for page in range(1, max_pages + 1):
            log.info(f"[实习僧] 正在爬取第 {page}/{max_pages} 页...")
            items = self.fetch_page(page)
            if not items:
                log.info(f"[实习僧] 第 {page} 页无数据，结束")
                break
            all_jobs.extend(items)
            random_delay()

        log.info(f"[实习僧] 完成，共获取 {len(all_jobs)} 条记录")
        self.results = all_jobs
        return all_jobs


# ===================== BOSS直聘爬虫 =====================

class BossZhipinCrawler:
    """BOSS直聘爬虫"""

    BASE_URL = "https://www.zhipin.com"
    SEARCH_URL = "https://www.zhipin.com/web/geek/job"

    def __init__(self, city: str, keyword: str):
        self.city = city
        self.keyword = keyword
        self.session = requests.Session()
        self.results = []

    def _get_city_code(self) -> str:
        mapping = {
            "北京": "101010100",
            "上海": "101020100",
            "广州": "101280100",
            "深圳": "101280600",
            "杭州": "101210100",
            "成都": "101270100",
            "南京": "101190100",
            "武汉": "101200100",
            "西安": "101110100",
            "重庆": "101040100",
            "长沙": "101250100",
            "苏州": "101190400",
            "天津": "101030100",
            "厦门": "101230200",
            "福州": "101230100",
            "合肥": "101220100",
            "郑州": "101180100",
            "青岛": "101120200",
            "大连": "101070200",
            "昆明": "101290100",
            "沈阳": "101070100",
            "济南": "101120100",
            "哈尔滨": "101050100",
            "长春": "101060100",
            "石家庄": "101090100",
            "太原": "101100100",
            "南昌": "101240100",
            "南宁": "101300100",
            "海口": "101310100",
            "贵阳": "101260100",
            "兰州": "101160100",
        }
        return mapping.get(self.city, self.city)

    def fetch_page(self, page: int = 1) -> list:
        params = {
            "city": self._get_city_code(),
            "query": self.keyword,
            "page": page,
            "experience": "102",  # 经验不限/应届
        }
        url = f"{self.SEARCH_URL}?{urlencode(params, quote_via=quote)}"
        headers = get_headers(referer=self.BASE_URL)
        resp = safe_request(url, headers=headers)

        if not resp:
            return []

        soup = BeautifulSoup(resp.text, "html.parser")
        job_cards = soup.select("div.job-card-wrapper, div.job-list li, div.card-wrapper")
        if not job_cards:
            job_cards = soup.select("[class*=job-card], [class*=job-item], li.job-item")

        items = []
        for card in job_cards:
            try:
                item = self._parse_card(card)
                if item:
                    items.append(item)
            except Exception as e:
                log.warning(f"BOSS 解析卡片异常: {e}")
                continue
        return items

    def _parse_card(self, card) -> Optional[dict]:
        try:
            title_el = card.select_one("span.job-name, a.job-name, [class*=job-name] a, .job-title a")
            if not title_el:
                title_el = card.select_one("a[class*=job-title]")
            if not title_el:
                title_el = card.select_one("a")
            name = clean_text(title_el.get_text(strip=True)) if title_el else ""

            company_el = card.select_one("a.company-name, span.company-name, [class*=company-name] a, .company-info a")
            if not company_el:
                company_el = card.select_one("a[class*=company]")
            company_name = clean_text(company_el.get_text(strip=True)) if company_el else ""

            salary_el = card.select_one("span.salary, [class*=salary], .job-salary")
            salary_text = clean_text(salary_el.get_text(strip=True)) if salary_el else ""

            info_el = card.select_one("ul.job-tag-list, div.job-tags, [class*=job-tag], .tag-list")
            tags = []
            if info_el:
                for tag in info_el.select("li, span, .tag-item"):
                    t = clean_text(tag.get_text(strip=True))
                    if t:
                        tags.append(t)

            city_el = card.select_one("span.job-area, [class*=job-area], .city")
            city = clean_text(city_el.get_text(strip=True)) if city_el else self.city

            welfare_el = card.select_one("div.job-welfare, [class*=welfare]")
            welfare = clean_text(welfare_el.get_text(strip=True)) if welfare_el else ""

            link_el = card.select_one("a[href*=job_detail], a[href*=geek]")
            link = ""
            if link_el:
                href = link_el.get("href", "")
                if href:
                    link = self.BASE_URL + href if href.startswith("/") else href

            time_el = card.select_one("span.job-time, [class*=time], .pub-time")
            pub_time = clean_text(time_el.get_text(strip=True)) if time_el else ""

            company_info_el = card.select_one("div.company-tag-list, [class*=company-tag]")
            company_tags = []
            if company_info_el:
                for ct in company_info_el.select("li, span"):
                    t = clean_text(ct.get_text(strip=True))
                    if t:
                        company_tags.append(t)

            salary = parse_salary(salary_text)

            return {
                "平台": "BOSS直聘",
                "职位名称": name,
                "公司名称": company_name,
                "公司标签": "、".join(company_tags),
                "工作城市": city,
                "薪资待遇": salary_text,
                "薪资结构": salary,
                "职位标签": "、".join(tags),
                "福利待遇": welfare,
                "发布时间": pub_time,
                "详情链接": link,
            }
        except Exception as e:
            log.warning(f"BOSS 解析异常: {e}")
            return None

    def run(self, max_pages: int = 3) -> list:
        all_jobs = []
        log.info(f"[BOSS直聘] 开始爬取: 城市={self.city}, 关键词={self.keyword}")

        for page in range(1, max_pages + 1):
            log.info(f"[BOSS直聘] 正在爬取第 {page}/{max_pages} 页...")
            items = self.fetch_page(page)
            if not items:
                log.info(f"[BOSS直聘] 第 {page} 页无数据，结束")
                break
            all_jobs.extend(items)
            random_delay()

        log.info(f"[BOSS直聘] 完成，共获取 {len(all_jobs)} 条记录")
        self.results = all_jobs
        return all_jobs


# ===================== 拉勾网爬虫 =====================

class LagouCrawler:
    """拉勾网爬虫"""

    API_URL = "https://www.lagou.com/jobs/positionAjax.json"
    BASE_URL = "https://www.lagou.com"

    def __init__(self, city: str, keyword: str):
        self.city = city
        self.keyword = keyword
        self.session = requests.Session()
        self.results = []
        self.cookies = {}

    def _init_cookies(self):
        try:
            resp = requests.get(
                f"{self.BASE_URL}/",
                headers=get_headers(),
                timeout=REQUEST_TIMEOUT,
            )
            self.cookies = dict(resp.cookies)
        except Exception:
            pass

    def fetch_page(self, page: int = 1) -> list:
        if not self.cookies:
            self._init_cookies()

        city_code = CITY_MAP.get(self.city, self.city)
        headers = get_headers(referer=f"{self.BASE_URL}/jobs/list_{self.keyword}?city={quote(city_code)}")
        headers["Content-Type"] = "application/x-www-form-urlencoded; charset=UTF-8"
        headers["X-Requested-With"] = "XMLHttpRequest"
        headers["Referer"] = f"{self.BASE_URL}/jobs/list_{quote(self.keyword)}?city={quote(city_code)}"
        headers["Origin"] = self.BASE_URL

        params = {
            "px": "new",
            "city": city_code,
            "needAddtionalResult": "false",
        }

        data = {
            "first": "true" if page == 1 else "false",
            "pn": page,
            "kd": self.keyword,
        }

        resp = safe_request(
            self.API_URL,
            headers=headers,
            params=params,
        )
        if not resp:
            return []

        try:
            json_data = resp.json()
        except Exception:
            log.error(f"拉勾 API 返回非 JSON: {resp.text[:200]}")
            return []

        content = json_data.get("content", {})
        if not content:
            log.warning(f"拉勾 第{page}页无 content")
            return []

        results = content.get("positionResult", {}).get("result", [])
        if not results:
            return []

        items = []
        for job in results:
            try:
                item = self._parse_job(job)
                if item:
                    items.append(item)
            except Exception as e:
                log.warning(f"拉勾 解析异常: {e}")
                continue
        return items

    def _parse_job(self, job: dict) -> Optional[dict]:
        try:
            name = job.get("positionName", "") or job.get("jobName", "")

            salary_text = job.get("salary", "")
            salary = parse_salary(salary_text)

            city = job.get("city", "") or job.get("workCity", "") or ""
            district = job.get("district", "") or ""

            edu = job.get("education", "") or ""
            exp = job.get("workYear", "") or job.get("experience", "") or ""

            company_name = job.get("companyFullName", "") or job.get("companyShortName", "") or ""
            company_size = job.get("companySize", "") or ""
            industry = job.get("industryField", "") or job.get("industry", "") or ""
            finance = job.get("financeStage", "") or ""

            tags_str = job.get("positionAdvantage", "") or job.get("advantage", "") or ""
            tags = [t.strip() for t in tags_str.split() if t.strip()]

            skill_labels = job.get("skillLables", []) or job.get("skillLabels", []) or []
            skills = "、".join(skill_labels) if skill_labels else ""

            detail_id = job.get("positionId", "") or job.get("jobId", "")
            detail_url = f"{self.BASE_URL}/jobs/{detail_id}.html" if detail_id else ""

            create_time = job.get("createTime", "") or ""
            approve_time = job.get("approveTime", "") or ""

            subway = job.get("subwayline", "") or ""
            station = job.get("stationname", "") or ""

            return {
                "平台": "拉勾网",
                "职位名称": name,
                "公司名称": company_name,
                "公司规模": company_size,
                "所属行业": industry,
                "融资阶段": finance,
                "工作城市": city,
                "工作区域": district,
                "薪资待遇": salary_text,
                "薪资结构": salary,
                "学历要求": edu,
                "经验要求": exp,
                "职位福利": tags_str,
                "技能要求": skills,
                "地铁线路": subway,
                "附近地铁站": station,
                "发布时间": create_time or approve_time,
                "详情链接": detail_url,
            }
        except Exception as e:
            log.warning(f"拉勾 解析职位异常: {e}")
            return None

    def run(self, max_pages: int = 3) -> list:
        all_jobs = []
        log.info(f"[拉勾网] 开始爬取: 城市={self.city}, 关键词={self.keyword}")

        for page in range(1, max_pages + 1):
            log.info(f"[拉勾网] 正在爬取第 {page}/{max_pages} 页...")
            items = self.fetch_page(page)
            if not items:
                log.info(f"[拉勾网] 第 {page} 页无数据，结束")
                break
            all_jobs.extend(items)
            random_delay()

        log.info(f"[拉勾网] 完成，共获取 {len(all_jobs)} 条记录")
        self.results = all_jobs
        return all_jobs


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

    base_keys = [k for k in all_keys if k != "薪资结构"]
    base_keys.append("薪资结构")

    with open(filepath, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(base_keys)
        for job in jobs:
            row = []
            for k in base_keys:
                val = job.get(k, "")
                if isinstance(val, (dict, list)):
                    val = json.dumps(val, ensure_ascii=False)
                row.append(val)
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
        lines.append(f"- **城市**: {job.get('工作城市', self.city)}")
        lines.append(f"- **学历**: {job.get('学历要求', '不限')}")
        lines.append(f"- **经验**: {job.get('经验要求', '不限')}")
        if job.get("职位标签"):
            lines.append(f"- **标签**: {job['职位标签']}")
        if job.get("福利待遇"):
            lines.append(f"- **福利**: {job['福利待遇']}")
        if job.get("技能要求"):
            lines.append(f"- **技能**: {job['技能要求']}")
        if job.get("详情链接"):
            lines.append(f"- **链接**: {job['详情链接']}")
        lines.append("")
        lines.append("---")
        lines.append("")

    with open(filepath, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    log.info(f"Markdown 已导出: {filepath}")


# ===================== 主程序 =====================

PLATFORM_MAP = {
    "shixiseng": ShixisengCrawler,
    "boss": BossZhipinCrawler,
    "lagou": LagouCrawler,
}

JOB_TYPE_MAP = {
    "intern": "intern",
    "实习": "intern",
    "campus": "campus",
    "校招": "campus",
    "all": "intern",
}


def main():
    parser = argparse.ArgumentParser(
        description="实习/校园招聘信息爬虫",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 爬取北京的互联网实习岗位（默认所有平台）
  python crawler.py -c 北京 -k 互联网

  # 爬取上海的人工智能岗位，输出 JSON
  python crawler.py -c 上海 -k 人工智能 -o json

  # 仅爬取实习僧平台的深圳游戏实习岗
  python crawler.py -c 深圳 -k 游戏 -p shixiseng -t intern

  # 爬取校招信息
  python crawler.py -c 北京 -k 金融 -t campus

  # 多城市联合查询
  python crawler.py -c 北京,上海,深圳 -k "Java"

  # 查看更多城市和行业
  python crawler.py --list-cities
  python crawler.py --list-industries
        """,
    )
    parser.add_argument("-c", "--city", default="北京", help="目标城市（支持多个，用逗号分隔）")
    parser.add_argument("-k", "--keyword", default="实习", help="搜索关键词/行业")
    parser.add_argument("-p", "--platform", default="all", choices=["all", "shixiseng", "boss", "lagou"], help="目标平台")
    parser.add_argument("-t", "--type", default="all", choices=["all", "intern", "campus", "实习", "校招"], help="岗位类型")
    parser.add_argument("--max-pages", type=int, default=3, help="每平台每页最大页数 (默认3)")
    parser.add_argument("-o", "--output", default="all", choices=["all", "csv", "json", "md", "markdown"], help="输出格式")
    parser.add_argument("--concurrency", type=int, default=CONCURRENCY, help="并发数 (默认5)")
    parser.add_argument("--list-cities", action="store_true", help="列出支持的城市")
    parser.add_argument("--list-industries", action="store_true", help="列出支持的行业")
    parser.add_argument("--no-export", action="store_true", help="不导出文件，仅终端输出")

    args = parser.parse_args()

    if args.list_cities:
        print("支持的城市: ")
        for c in CITY_MAP:
            print(f"  - {c}")
        return

    if args.list_industries:
        print("支持的行业: ")
        for ind in INDUSTRY_MAP:
            print(f"  - {ind}")
        return

    job_type = JOB_TYPE_MAP.get(args.type, "intern")

    cities = [c.strip() for c in args.city.split(",") if c.strip()]
    if not cities:
        cities = ["北京"]

    platforms_to_use = ["shixiseng", "boss", "lagou"] if args.platform == "all" else [args.platform]

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_city = "".join(cities)
    safe_keyword = args.keyword.replace(" ", "_")
    base_filename = f"{safe_city}_{safe_keyword}_{timestamp}"

    all_jobs = []

    log.info("=" * 60)
    log.info("实习/校园招聘信息爬虫 启动")
    log.info(f"城市: {', '.join(cities)}")
    log.info(f"关键词: {args.keyword}")
    log.info(f"平台: {args.platform}")
    log.info(f"岗位类型: {args.type}")
    log.info(f"最大页数: {args.max_pages}")
    log.info("=" * 60)

    for city in cities:
        for platform_name in platforms_to_use:
            platform_cls = PLATFORM_MAP.get(platform_name)
            if not platform_cls:
                continue

            if platform_name == "shixiseng":
                crawler = platform_cls(city, args.keyword, job_type=job_type)
            else:
                crawler = platform_cls(city, args.keyword)

            try:
                jobs = crawler.run(max_pages=args.max_pages)
                all_jobs.extend(jobs)
            except Exception as e:
                log.error(f"[{platform_name}] 爬取失败: {e}")
                continue

    log.info(f"\n共获取 {len(all_jobs)} 条招聘信息")

    for job in all_jobs:
        print(f"  [{job.get('平台','?')}] {job.get('职位名称','?')} - {job.get('公司名称','?')} {job.get('薪资待遇','?')}")

    if not args.no_export and all_jobs:
        output_formats = ["csv", "json", "md"] if args.output == "all" else [args.output]
        for fmt in output_formats:
            fmt = fmt.replace("markdown", "md")
            fp = os.path.join(OUTPUT_DIR, f"{base_filename}.{fmt}")
            if fmt == "csv":
                export_to_csv(all_jobs, fp)
            elif fmt == "json":
                export_to_json(all_jobs, fp)
            elif fmt == "md":
                export_to_markdown(all_jobs, fp, args.city, args.keyword)
        print(f"\n文件已保存到: {OUTPUT_DIR}")
    elif not all_jobs:
        log.warning("未获取到任何数据，请检查网络/参数后重试")


if __name__ == "__main__":
    main()
