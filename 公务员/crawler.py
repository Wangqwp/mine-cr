#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
公务员招录信息爬虫
支持多数据源获取全国及各省公务员招考公告、职位信息
数据源: 华图教育、中公教育、百度搜索聚合

日期: 2026-05-30
"""

import argparse
import csv
import json
import logging
import os
import re
import sys
import time
import random
from datetime import datetime
from typing import Optional
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

# ===================== 配置 =====================

REQUEST_TIMEOUT = 20  # 秒
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

# ===================== 省份配置 =====================

PROVINCES = [
    "全国", "北京", "上海", "天津", "重庆",
    "河北", "山西", "辽宁", "吉林", "黑龙江",
    "江苏", "浙江", "安徽", "福建", "江西", "山东",
    "河南", "湖北", "湖南", "广东", "海南",
    "四川", "贵州", "云南", "陕西", "甘肃", "青海",
    "广西", "内蒙古", "西藏", "宁夏", "新疆",
]

# 省份关键词（用于标题匹配过滤）
PROVINCE_KEYWORDS = {
    "北京": ["北京", "京"],
    "上海": ["上海", "沪"],
    "天津": ["天津", "津"],
    "重庆": ["重庆", "渝"],
    "河北": ["河北", "石家庄", "唐山", "秦皇岛", "邯郸", "保定", "张家口", "承德", "沧州", "廊坊", "衡水", "邢台"],
    "山西": ["山西", "太原", "大同", "阳泉", "长治", "晋城", "朔州", "忻州", "吕梁", "晋中", "临汾", "运城"],
    "辽宁": ["辽宁", "沈阳", "大连", "鞍山", "抚顺", "本溪", "丹东", "锦州", "营口", "阜新", "辽阳", "盘锦", "铁岭", "朝阳", "葫芦岛"],
    "吉林": ["吉林", "长春", "四平", "辽源", "通化", "白山", "松原", "白城", "延边"],
    "黑龙江": ["黑龙江", "哈尔滨", "齐齐哈尔", "牡丹江", "佳木斯", "大庆", "鸡西", "双鸭山", "伊春", "七台河", "鹤岗", "黑河", "绥化"],
    "江苏": ["江苏", "南京", "无锡", "徐州", "常州", "苏州", "南通", "连云港", "淮安", "盐城", "扬州", "镇江", "泰州", "宿迁"],
    "浙江": ["浙江", "杭州", "宁波", "温州", "嘉兴", "湖州", "绍兴", "金华", "衢州", "舟山", "台州", "丽水"],
    "安徽": ["安徽", "合肥", "芜湖", "蚌埠", "淮南", "马鞍山", "淮北", "铜陵", "安庆", "黄山", "滁州", "阜阳", "宿州", "六安", "亳州", "池州", "宣城"],
    "福建": ["福建", "福州", "厦门", "莆田", "三明", "泉州", "漳州", "南平", "龙岩", "宁德"],
    "江西": ["江西", "南昌", "景德镇", "萍乡", "九江", "新余", "鹰潭", "赣州", "吉安", "宜春", "抚州", "上饶"],
    "山东": ["山东", "济南", "青岛", "淄博", "枣庄", "东营", "烟台", "潍坊", "济宁", "泰安", "威海", "日照", "临沂", "德州", "聊城", "滨州", "菏泽"],
    "河南": ["河南", "郑州", "开封", "洛阳", "平顶山", "安阳", "鹤壁", "新乡", "焦作", "濮阳", "许昌", "漯河", "三门峡", "南阳", "商丘", "信阳", "周口", "驻马店"],
    "湖北": ["湖北", "武汉", "黄石", "十堰", "宜昌", "襄阳", "鄂州", "荆门", "孝感", "荆州", "黄冈", "咸宁", "随州", "恩施"],
    "湖南": ["湖南", "长沙", "株洲", "湘潭", "衡阳", "邵阳", "岳阳", "常德", "张家界", "益阳", "郴州", "永州", "怀化", "娄底", "湘西"],
    "广东": ["广东", "广州", "深圳", "珠海", "汕头", "佛山", "韶关", "湛江", "肇庆", "江门", "茂名", "惠州", "梅州", "汕尾", "河源", "阳江", "清远", "东莞", "中山", "潮州", "揭阳", "云浮"],
    "海南": ["海南", "海口", "三亚", "三沙", "儋州"],
    "四川": ["四川", "成都", "自贡", "攀枝花", "泸州", "德阳", "绵阳", "广元", "遂宁", "内江", "乐山", "南充", "眉山", "宜宾", "广安", "达州", "雅安", "巴中", "资阳"],
    "贵州": ["贵州", "贵阳", "六盘水", "遵义", "安顺", "铜仁", "毕节", "黔东南", "黔南", "黔西南"],
    "云南": ["云南", "昆明", "曲靖", "玉溪", "保山", "昭通", "丽江", "普洱", "临沧", "楚雄", "红河", "文山", "西双版纳", "大理", "德宏", "怒江", "迪庆"],
    "陕西": ["陕西", "西安", "铜川", "宝鸡", "咸阳", "渭南", "延安", "汉中", "榆林", "安康", "商洛"],
    "甘肃": ["甘肃", "兰州", "嘉峪关", "金昌", "白银", "天水", "武威", "张掖", "平凉", "酒泉", "庆阳", "定西", "陇南", "临夏", "甘南"],
    "青海": ["青海", "西宁", "海东", "海北", "黄南", "海南州", "果洛", "玉树", "海西"],
    "广西": ["广西", "南宁", "柳州", "桂林", "梧州", "北海", "防城港", "钦州", "贵港", "玉林", "百色", "贺州", "河池", "来宾", "崇左"],
    "内蒙古": ["内蒙古", "呼和浩特", "包头", "乌海", "赤峰", "通辽", "鄂尔多斯", "呼伦贝尔", "巴彦淖尔", "乌兰察布", "兴安", "锡林郭勒", "阿拉善"],
    "西藏": ["西藏", "拉萨", "日喀则", "昌都", "林芝", "山南", "那曲", "阿里"],
    "宁夏": ["宁夏", "银川", "石嘴山", "吴忠", "固原", "中卫"],
    "新疆": ["新疆", "乌鲁木齐", "克拉玛依", "吐鲁番", "哈密", "阿克苏", "喀什", "和田", "伊犁", "塔城", "阿勒泰"],
}

# 华图教育省份子域名
HUATU_DOMAIN_MAP = {
    "全国": "www",
    "北京": "bj", "上海": "sh", "天津": "tj", "重庆": "cq",
    "河北": "he", "山西": "sx", "辽宁": "ln", "吉林": "jl", "黑龙江": "hlj",
    "江苏": "js", "浙江": "zj", "安徽": "ah", "福建": "fj", "江西": "jx", "山东": "sd",
    "河南": "henan", "湖北": "hb", "湖南": "hn", "广东": "gd", "海南": "hainan",
    "四川": "sc", "贵州": "gz", "云南": "yn", "陕西": "shanxi", "甘肃": "gs", "青海": "qh",
    "广西": "gx", "内蒙古": "nmg", "西藏": "xz", "宁夏": "nx", "新疆": "xj",
}

# ===================== HTTP 请求工具 =====================


def create_session():
    """创建带浏览器模拟 headers 的 Session"""
    session = requests.Session()
    session.headers.update({
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/125.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,"
                   "image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Connection": "keep-alive",
        "Cache-Control": "max-age=0",
        "Upgrade-Insecure-Requests": "1",
    })
    return session


def fetch_page(session, url, params=None, referer="") -> Optional[str]:
    """获取页面HTML，自动检测编码，带重试"""
    max_retries = 2
    for attempt in range(max_retries + 1):
        try:
            headers = {"Referer": referer} if referer else {}
            resp = session.get(url, params=params, headers=headers, timeout=REQUEST_TIMEOUT)

            if resp.status_code != 200:
                if resp.status_code == 403 and attempt < max_retries:
                    time.sleep(random.uniform(3, 5))
                    continue
                log.warning(f"HTTP {resp.status_code}: {url}")
                return None

            # 自动检测编码
            enc = resp.apparent_encoding
            if enc and enc.lower() in ("gb2312", "gbk", "gb18030"):
                resp.encoding = "gb18030"
            else:
                resp.encoding = "utf-8"

            return resp.text

        except requests.exceptions.Timeout:
            if attempt < max_retries:
                time.sleep(random.uniform(2, 4))
                continue
            log.warning(f"超时: {url}")
            return None
        except Exception as e:
            log.error(f"请求异常: {url} - {e}")
            return None
    return None


def extract_date(text: str) -> str:
    """提取日期，返回 YYYY-MM-DD 格式"""
    patterns = [
        (r"(\d{4})[-/年](\d{1,2})[-/月](\d{1,2})[日]?", "{}-{:02d}-{:02d}"),
        (r"(\d{4})[-/](\d{1,2})[-/](\d{1,2})$", "{}-{:02d}-{:02d}"),
    ]
    for pat, fmt in patterns:
        m = re.search(pat, text)
        if m:
            y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
            return fmt.format(y, mo, d)
    return ""


def extract_date_from_url(url: str) -> str:
    """从 URL 路径中提取日期: /2026/0227/ -> 2026-02-27"""
    m = re.search(r"/(\d{4})/(\d{2})(\d{2})/", url)
    if m:
        y, mo, d = m.group(1), m.group(2), m.group(3)
        return f"{y}-{mo}-{d}"
    return ""


def identify_type(title: str) -> str:
    """识别招录类型"""
    if any(kw in title for kw in ["国考", "中央机关", "国家公务员"]):
        return "国考"
    # 省考优先级高于"公务员考试"通用词（避免公考、辅警等被归入省考）
    if any(kw in title for kw in ["省考", "录用公务员", "公务员招考", "公务员招录"]):
        return "省考"
    if "选调" in title:
        return "选调生"
    if "事业单位" in title or "事业编" in title:
        return "事业单位"
    if any(kw in title for kw in ["遴选", "公开选拔"]):
        return "遴选/选调"
    if "军队文职" in title:
        return "军队文职"
    if any(kw in title for kw in ["三支一扶", "西部计划", "特岗教师"]):
        return "基层项目"
    if any(kw in title for kw in ["国企", "央企", "烟草", "电网", "铁路", "中石化", "中石油"]):
        return "国企招聘"
    if any(kw in title for kw in ["辅警", "警务辅助", "协管", "消防"]):
        return "辅警/消防"
    # 标题中含"公务员考试"但未匹配到上述关键词的
    if "公务员" in title or "公职" in title or "公考" in title:
        return "公务员（通用）"
    # 公考公告汇总
    if "公职考试招考公告" in title or "招考信息汇总" in title:
        return "公告汇总"
    if "省级机关" in title or "乡镇" in title or "公安" in title:
        return "省考"
    return "其他"


def is_valid_announcement(title: str) -> bool:
    """判断是否为有效的招考公告（过滤课程广告等）"""
    skip_patterns = [
        "辅导", "培训", "课程", "教材", "图书", "网课", "面授",
        "每日一练", "模拟题", "真题", "试题", "题库",
        "技巧", "备考", "经验", "心得", "指南",
        "讲座", "公开课", "峰会", "解读",
        "导航", "首页", "更多", "网站", "专题",
        "报名入口", "职位查询", "成绩查询", "准考证",
    ]
    for p in skip_patterns:
        if p in title:
            return False

    # 太短的标题不要
    if len(title) < 8:
        return False

    return True


def matches_province(title: str, province: str) -> bool:
    """判断标题是否与指定地区相关"""
    if province == "全国":
        return True
    keywords = PROVINCE_KEYWORDS.get(province, [province])
    return any(kw in title for kw in keywords)


# ===================== 华图教育爬虫 =====================

class HuatuCrawler:
    """华图教育 - 公务员招考信息爬虫"""

    def __init__(self, province: str = "全国", keyword: str = ""):
        self.province = province
        self.keyword = keyword
        code = HUATU_DOMAIN_MAP.get(province, "www")
        self.base_url = f"https://{code}.huatu.com"
        self.national_url = "https://www.huatu.com"  # 全国站固定URL
        self.session = create_session()
        log.info(f"[华图] 省级站: {self.base_url} | 全国站: {self.national_url}")

    def run(self, max_pages: int = 5) -> list:
        all_items = []
        log.info(f"[华图] 爬取: {self.province}, 最多{max_pages}页")

        # 始终从全国站爬取最全的公告（数据质量最高）
        items = self._crawl_national(max_pages)
        all_items.extend(items)

        # 如果指定了具体省份，还尝试从省级站补充
        if self.province != "全国":
            prov_items = self._crawl_province(max_pages)
            all_items.extend(prov_items)

        log.info(f"[华图] 完成, 共 {len(all_items)} 条")
        return all_items

    def _crawl_national(self, max_pages: int) -> list:
        """全国站: www.huatu.com/guojia/zhaokao/zkgg/
        如果指定了省份，按标题关键词过滤出该省相关公告"""
        all_items = []
        base_path = "/guojia/zhaokao/zkgg/"

        for page in range(1, max_pages + 1):
            if page == 1:
                url = f"{self.national_url}{base_path}"
            else:
                url = f"{self.national_url}{base_path}index_{page}.html"

            items = self._parse_national_list(url)
            if not items and page > 1:
                alt_url = f"{self.national_url}{base_path}list_{page}.html"
                items = self._parse_national_list(alt_url)
            if not items:
                break

            # 按地区过滤（仅当指定了具体省份）
            if self.province != "全国":
                before = len(items)
                items = [it for it in items if matches_province(it["title"], self.province)]
                log.info(f"[华图] 全国站 第{page}页: {before}→{len(items)} 条 (地区过滤: {self.province})")
            else:
                log.info(f"[华图] 全国站 第{page}页: {len(items)} 条")

            all_items.extend(items)
            time.sleep(random.uniform(1, 2))

        return all_items

    def _parse_national_list(self, url: str) -> list:
        """解析全国站公告列表"""
        html = fetch_page(self.session, url, referer="https://www.huatu.com/")
        if not html:
            return []

        soup = BeautifulSoup(html, "html.parser")
        items = []
        seen = set()

        # 查找所有符合条件的文章链接
        # 国考公告页的文章链接格式: https://www.huatu.com/2026/0227/2851657.html
        for a_tag in soup.find_all("a", href=True):
            href = a_tag.get("href", "").strip()
            title = a_tag.text.strip()

            if not re.search(r"/20\d{2}/\d{4}/\d+\.html", href):
                continue
            if not title or len(title) < 8:
                continue

            full_url = urljoin(self.national_url, href)

            # 去重
            if full_url in seen:
                continue
            seen.add(full_url)

            # 过滤非公告内容
            if not is_valid_announcement(title):
                continue

            # 关键词过滤
            if self.keyword and self.keyword not in title:
                continue

            # 提取日期：优先从 URL，其次从页面文本
            pub_date = extract_date_from_url(full_url)
            if not pub_date:
                # 找附近的日期文本
                parent = a_tag.parent
                if parent:
                    for s in parent.find_all(["span", "em", "i", "small"]):
                        d = extract_date(s.text)
                        if d:
                            pub_date = d
                            break

            rec_type = identify_type(title)

            items.append({
                "title": title,
                "url": full_url,
                "date": pub_date,
                "source": "华图教育",
                "province": self.province,
                "type": rec_type,
            })

        return items

    def _crawl_province(self, max_pages: int) -> list:
        """省级站: {code}.huatu.com/zhaokao/"""
        all_items = []
        paths = ["/zhaokao/"]

        for path in paths:
            for page in range(1, max_pages + 1):
                if page == 1:
                    url = f"{self.base_url}{path}"
                else:
                    url = f"{self.base_url}{path}list_{page}.html"

                items = self._parse_province_list(url)
                if not items:
                    break
                all_items.extend(items)
                log.info(f"[华图] 省级站 {path} 第{page}页: {len(items)} 条")
                time.sleep(random.uniform(1, 2))

        return all_items

    def _parse_province_list(self, url: str) -> list:
        """解析省级站列表"""
        html = fetch_page(self.session, url, referer=f"{self.base_url}/")
        if not html:
            return []

        soup = BeautifulSoup(html, "html.parser")
        items = []
        seen = set()

        # 尝试多种选择器
        containers = [
            soup.select(".list-con ul li"),
            soup.select(".art_list li"),
            soup.select(".news-list li"),
            soup.select("ul.list li"),
            soup.select(".gg-list li"),
            soup.find_all("li"),
        ]

        for container in containers:
            if not container:
                continue
            for li in container:
                try:
                    a_tag = li.find("a")
                    if not a_tag:
                        continue

                    title = (a_tag.get("title") or a_tag.text or "").strip()
                    href = a_tag.get("href", "")

                    if not title or len(title) < 6 or not href:
                        continue
                    if href.startswith("#") or href.startswith("javascript"):
                        continue
                    if not is_valid_announcement(title):
                        continue

                    full_url = urljoin(self.base_url, href)
                    if full_url in seen:
                        continue
                    seen.add(full_url)

                    if self.keyword and self.keyword not in title:
                        continue

                    # 日期
                    pub_date = extract_date_from_url(full_url)
                    if not pub_date:
                        date_text = li.get_text(separator=" ", strip=True)
                        pub_date = extract_date(date_text)

                    rec_type = identify_type(title)

                    items.append({
                        "title": title,
                        "url": full_url,
                        "date": pub_date,
                        "source": "华图教育",
                        "province": self.province,
                        "type": rec_type,
                    })
                except Exception:
                    continue
            if items:
                break

        return items


# ===================== 百度搜索聚合爬虫 =====================

class SearchAggregator:
    """通过百度搜索聚合公务员招考信息"""

    SEARCH_URL = "https://www.baidu.com/s"

    def __init__(self, province: str = "全国", keyword: str = ""):
        self.province = province
        self.keyword = keyword
        self.session = create_session()

    def run(self) -> list:
        items = []
        log.info(f"[搜索] 聚合: {self.province}")

        # 构建搜索词
        queries = [
            f"{self.province} 公务员 招考 公告 2026",
            f"{self.province} 省考 公告 职位表",
        ]
        if self.keyword:
            queries.insert(0, f"{self.province} {self.keyword} 公告 2026")

        for q in queries:
            try:
                results = self._search(q)
                items.extend(results)
                log.info(f"[搜索] '{q[:30]}': {len(results)} 条")
                time.sleep(random.uniform(2, 4))
            except Exception as e:
                log.error(f"[搜索] 异常: {e}")

        return self._dedup(items)

    def _search(self, query: str) -> list:
        params = {"wd": query, "rn": 15}
        html = fetch_page(self.session, self.SEARCH_URL, params=params,
                          referer="https://www.baidu.com/")
        if not html:
            return []

        soup = BeautifulSoup(html, "html.parser")
        items = []

        # 百度搜索结果容器
        for result in soup.select(".result, .c-container, .search-result"):
            try:
                h3 = result.find("h3")
                if not h3:
                    continue
                a = h3.find("a")
                if not a:
                    continue

                title = a.text.strip()
                href = a.get("href", "")

                if not title or len(title) < 8:
                    continue
                if not is_valid_announcement(title):
                    continue
                if self.keyword and self.keyword not in title:
                    continue
                # 按地区过滤标题
                if not matches_province(title, self.province):
                    continue

                # 提取日期
                abstract = result.text
                pub_date = extract_date(abstract)

                rec_type = identify_type(title)

                items.append({
                    "title": title,
                    "url": href,
                    "date": pub_date,
                    "source": "百度搜索",
                    "province": self.province,
                    "type": rec_type,
                })
            except Exception:
                continue

        return items

    def _dedup(self, items: list) -> list:
        seen = set()
        result = []
        for item in items:
            key = item["title"] + item["url"]
            if key not in seen:
                seen.add(key)
                result.append(item)
        return result


# ===================== 数据导出 =====================

def deduplicate(items: list) -> list:
    seen = set()
    result = []
    for item in items:
        key = item.get("title", "") + item.get("url", "")
        if key not in seen:
            seen.add(key)
            result.append(item)
    return result


def export_to_csv(items: list, filepath: str):
    if not items:
        return
    fields = ["type", "title", "province", "source", "date", "url"]
    headers = ["招录类型", "标题", "地区", "来源", "发布日期", "链接"]
    with open(filepath, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(headers)
        for item in items:
            w.writerow([item.get(k, "") for k in fields])
    log.info(f"CSV: {filepath}")


def export_to_json(items: list, filepath: str):
    data = {
        "update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "province": items[0].get("province", "") if items else "",
        "total": len(items),
        "items": items,
    }
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    log.info(f"JSON: {filepath}")


def export_to_markdown(items: list, filepath: str, province: str, keyword: str):
    lines = [
        f"# {province}公务员招录信息",
        "",
        f"> 抓取时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"> 地区: {province} | 关键词: {keyword or '全部'} | 数量: {len(items)}",
        "",
        "---",
        "",
    ]

    type_order = ["国考", "省考", "选调生", "事业单位", "遴选/选调",
                   "军队文职", "基层项目", "国企招聘", "辅警/消防", "其他"]
    grouped = {}
    for item in items:
        t = item.get("type", "其他")
        grouped.setdefault(t, []).append(item)

    for t in type_order:
        if t not in grouped:
            continue
        lines.append(f"## {t}\n")
        for i, item in enumerate(grouped[t], 1):
            lines.append(f"### {i}. {item.get('title', '')}")
            lines.append("")
            lines.append(f"- **来源**: {item.get('source', '')}  |  **地区**: {item.get('province', '')}")
            if item.get("date"):
                lines.append(f"- **发布日期**: {item['date']}")
            if item.get("url"):
                lines.append(f"- **链接**: [{item['url']}]({item['url']})")
            lines.append("")
            lines.append("---")
            lines.append("")

    with open(filepath, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    log.info(f"MD: {filepath}")


# ===================== 主程序 =====================

def main():
    parser = argparse.ArgumentParser(
        description="公务员招录信息爬虫",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python crawler.py -p 全国              # 全国公务员招考
  python crawler.py -p 广东              # 广东省招考
  python crawler.py -p 江苏泰州          # 指定省市 (智能识别)
  python crawler.py -p 泰州              # 直接指定城市
  python crawler.py -p 全国 -k 选调      # 搜索选调生
  python crawler.py -p 全国 -s search    # 搜索聚合模式
  python crawler.py -p 上海 -s huatu     # 仅华图源
  python crawler.py --list-provinces     # 省份列表
        """,
    )
    parser.add_argument("-p", "--province", default="全国",
                        help="地区/城市 (支持省市组合，如: 江苏泰州、深圳)")
    parser.add_argument("-k", "--keyword", default="", help="关键词筛选")
    parser.add_argument("--max-pages", type=int, default=3, help="最大页数 (默认: 3)")
    parser.add_argument("-s", "--source", default="all",
                        choices=["all", "huatu", "search"],
                        help="数据源 (默认: all)")
    parser.add_argument("-o", "--output", default="all",
                        choices=["all", "csv", "json", "md", "markdown"],
                        help="输出格式 (默认: all)")
    parser.add_argument("--list-provinces", action="store_true", help="列出省份")
    parser.add_argument("--no-export", action="store_true", help="不导出文件")

    args = parser.parse_args()

    if args.list_provinces:
        print("支持的省份/地区:")
        for p in PROVINCES:
            print(f"  - {p}")
        return

    # 智能识别地区：解析"江苏泰州" → 省份="江苏", 附加城市="泰州"
    raw_region = args.province
    province = raw_region
    extra_city = ""
    for prov in PROVINCES:
        if prov != "全国" and raw_region.startswith(prov) and len(raw_region) > len(prov):
            province = prov
            extra_city = raw_region[len(prov):]
            break

    # 如果无法识别为"省份+城市"，检查是否直接输入了城市名
    if not extra_city and province not in PROVINCES:
        for prov, cities in PROVINCE_KEYWORDS.items():
            if province in cities:
                extra_city = province
                province = prov
                log.info(f"[地区] 识别城市\"{extra_city}\"属于{prov}")
                break

    # 过滤函数：省份名 + 城市名 都要匹配
    def region_filter(title: str) -> bool:
        if province == "全国":
            return True
        if not matches_province(title, province):
            return False
        if extra_city and extra_city not in title:
            return False
        return True

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_filename = f"{raw_region}_{args.keyword or '全部'}_{timestamp}"

    log.info("=" * 56)
    log.info("  公务员招录信息爬虫")
    log.info(f"  地区: {raw_region} → 省={province}, 市={extra_city or '全部'}")
    log.info(f"  关键词: {args.keyword or '全部'}")
    log.info(f"  数据源: {args.source}")
    log.info(f"  页数: {args.max_pages}")
    log.info("=" * 56)

    # 搜索时合并城市名到关键词
    search_keyword = args.keyword
    if extra_city:
        search_keyword = f"{extra_city} {search_keyword}" if search_keyword else extra_city

    all_items = []

    if args.source in ("all", "huatu"):
        try:
            log.info("\n── [华图教育] ──")
            c = HuatuCrawler(province=province, keyword=search_keyword)
            items = c.run(max_pages=args.max_pages)
            if extra_city:
                before = len(items)
                items = [it for it in items if region_filter(it["title"])]
                if before - len(items) > 0:
                    log.info(f"[华图] 城市过滤: {before}→{len(items)} 条")
            all_items.extend(items)
            log.info(f"✓ 华图: {len(items)} 条")
        except Exception as e:
            log.error(f"✗ 华图失败: {e}")

    if args.source in ("all", "search"):
        try:
            log.info("\n── [搜索聚合] ──")
            c = SearchAggregator(province=province, keyword=search_keyword)
            items = c.run()
            if extra_city:
                items = [it for it in items if region_filter(it["title"])]
            all_items.extend(items)
            log.info(f"✓ 搜索: {len(items)} 条")
        except Exception as e:
            log.error(f"✗ 搜索失败: {e}")

    all_items = deduplicate(all_items)

    # 按日期排序（最新的在前）
    def sort_key(item):
        d = item.get("date", "")
        if d:
            # 转成可排序格式
            return d
        return "0000-00-00"
    all_items.sort(key=sort_key, reverse=True)

    log.info(f"\n{'=' * 56}")
    log.info(f"总计: {len(all_items)} 条公务员招录信息")
    log.info("=" * 56)

    for item in all_items[:20]:
        print(f"  [{item['type']}] {item['title'][:55]}")
    if len(all_items) > 20:
        print(f"  ... 还有 {len(all_items) - 20} 条")

    if not args.no_export and all_items:
        fmts = ["csv", "json", "md"] if args.output == "all" else [args.output.replace("markdown", "md")]
        for fmt in fmts:
            fp = os.path.join(OUTPUT_DIR, f"{base_filename}.{fmt}")
            if fmt == "csv":
                export_to_csv(all_items, fp)
            elif fmt == "json":
                export_to_json(all_items, fp)
            elif fmt == "md":
                export_to_markdown(all_items, fp, args.province, args.keyword)
        print(f"\n📁 文件保存到: {OUTPUT_DIR}/")
    elif not all_items:
        log.warning("未获取到数据，可尝试多页或换地区")


if __name__ == "__main__":
    if len(sys.argv) <= 1:
        sys.argv = ["crawler.py", "-p", "全国", "-s", "all", "--max-pages", "2"]
    main()
