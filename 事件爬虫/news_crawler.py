import requests
import json
import time
from datetime import datetime
from pathlib import Path
import logging
from typing import Dict, List, Optional
import re
import random

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('news_crawler.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class NewsCrawler:
    """实时国内重大事件爬虫"""

    def __init__(self, data_dir: str = './news_data'):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/html, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Referer': 'https://www.baidu.com/',
        })

    def _request(self, url: str, headers: Optional[Dict] = None, params: Optional[Dict] = None, timeout: int = 10) -> Optional[requests.Response]:
        try:
            h = {**self.session.headers}
            if headers:
                h.update(headers)
            response = self.session.get(url, headers=h, params=params, timeout=timeout)
            response.encoding = 'utf-8'
            return response
        except Exception as e:
            logger.debug(f"请求失败 [{url}]: {e}")
            return None

    def get_weibo_hot(self) -> List[Dict]:
        """获取微博热搜榜"""
        try:
            url = "https://weibo.com/ajax/side/hotSearch"
            resp = self._request(url, headers={'Referer': 'https://weibo.com/'})
            if not resp:
                return []

            data = resp.json()
            items = []
            for item in data.get('data', {}).get('realtime', []):
                items.append({
                    '标题': item.get('word', ''),
                    '热度': item.get('raw_hot', 0) or item.get('num', 0),
                    '排名': item.get('rank', 0),
                    '来源': '微博热搜',
                    '链接': f"https://s.weibo.com/weibo?q={item.get('word_scheme', item.get('word', ''))}",
                    '标签': item.get('flag_desc', ''),
                })
            logger.info(f"微博热搜 获取成功: {len(items)} 条")
            return items
        except Exception as e:
            logger.warning(f"微博热搜获取失败: {e}")
            return []

    def get_baidu_hot(self) -> List[Dict]:
        """获取百度热搜榜"""
        try:
            url = "https://top.baidu.com/api/board?tab=realtime"
            resp = self._request(url, headers={'Referer': 'https://top.baidu.com/'})
            if not resp:
                return []

            data = resp.json()
            items = []
            cards = data.get('data', {}).get('cards', [])
            for card in cards:
                for item in card.get('content', []):
                    word = item.get('word', item.get('query', ''))
                    items.append({
                        '标题': word,
                        '热度': item.get('hotScore', 0) or item.get('heat', 0),
                        '排名': item.get('index', len(items) + 1),
                        '来源': '百度热搜',
                        '链接': item.get('linkUrl', f"https://www.baidu.com/s?wd={word}"),
                        '摘要': item.get('desc', ''),
                    })
            if not items:
                items = self._get_baidu_hot_fallback()
            logger.info(f"百度热搜 获取成功: {len(items)} 条")
            return items
        except Exception as e:
            logger.warning(f"百度热搜获取失败: {e}")
            return self._get_baidu_hot_fallback()

    def _get_baidu_hot_fallback(self) -> List[Dict]:
        """百度热搜备用方案：解析热搜页面"""
        try:
            url = "https://top.baidu.com/board?tab=realtime"
            resp = self._request(url)
            if not resp:
                return []

            html = resp.text
            pattern = r'"word":"(.*?)".*?"hotScore":(\d+)'
            matches = re.findall(pattern, html)
            items = []
            for i, (word, score) in enumerate(matches[:50], 1):
                items.append({
                    '标题': word,
                    '热度': int(score),
                    '排名': i,
                    '来源': '百度热搜',
                    '链接': f"https://www.baidu.com/s?wd={word}",
                })
            return items
        except Exception as e:
            logger.warning(f"百度热搜备用方案也失败: {e}")
            return []

    def get_163_news(self) -> List[Dict]:
        """获取网易新闻热点"""
        try:
            url = "https://c.m.163.com/nc/api/v1/feed/headline"
            resp = self._request(url, params={'offset': 0, 'size': 30, 'from': 'news'})
            if not resp:
                return self._get_163_news_parse()

            data = resp.json()
            items = []
            entries = data if isinstance(data, list) else data.get('data', {}).get('list', data.get('list', []))
            for item in entries:
                if isinstance(item, dict) and item.get('title'):
                    items.append({
                        '标题': item.get('title', ''),
                        '来源': '网易新闻',
                        '链接': item.get('url', item.get('link', item.get('pUrl', ''))),
                        '摘要': item.get('digest', item.get('abstract', '')),
                        '热度': item.get('pvCount', 0) or item.get('voteCount', 0),
                        '排名': len(items) + 1,
                    })
            if items:
                logger.info(f"网易新闻 获取成功: {len(items)} 条")
                return items[:30]
            return self._get_163_news_parse()
        except Exception as e:
            logger.debug(f"网易新闻API失败: {e}")
            return self._get_163_news_parse()

    def _get_163_news_parse(self) -> List[Dict]:
        try:
            resp = self._request("https://news.163.com/")
            if not resp:
                return []
            html = resp.text
            pattern = r'<a[^>]*href="(https?://news\.163\.com/\d+/\d+/\d+/[^"]*)"[^>]*>(.*?)</a>'
            matches = re.findall(pattern, html)
            items = []
            seen = set()
            for link, title in matches:
                title = re.sub(r'<[^>]+>', '', title).strip()
                if title and len(title) > 4 and title not in seen:
                    seen.add(title)
                    items.append({
                        '标题': title,
                        '来源': '网易新闻',
                        '链接': link,
                        '热度': 0,
                        '排名': len(items) + 1,
                    })
            logger.info(f"网易新闻(解析) 获取成功: {len(items)} 条")
            return items[:30]
        except Exception as e:
            logger.debug(f"网易新闻解析也失败: {e}")
            return []

            data = resp.json()
            items = []
            entries = data if isinstance(data, list) else data.get('data', {}).get('list', data.get('list', []))
            for item in entries:
                if isinstance(item, dict) and item.get('title'):
                    items.append({
                        '标题': item.get('title', ''),
                        '来源': '网易新闻',
                        '链接': item.get('url', item.get('link', item.get('pUrl', ''))),
                        '摘要': item.get('digest', item.get('abstract', '')),
                        '热度': item.get('pvCount', 0) or item.get('voteCount', 0) or item.get('clickCount', 0),
                        '排名': len(items) + 1,
                    })
            if items:
                logger.info(f"网易新闻 API 备用获取成功: {len(items)} 条")
            return items
        except Exception as e:
            logger.debug(f"网易新闻 API 备用也失败: {e}")
            return self._get_163_news_rss()

    def _get_163_news_rss(self) -> List[Dict]:
        try:
            resp = self._request("https://news.163.com/special/cm_guonei_01/")
            if not resp:
                return []
            html = resp.text
            pattern = r'<a[^>]*href="(https?://news\.163\.com/\d+/\d+/\d+/[^"]+)"[^>]*>(.*?)</a>'
            matches = re.findall(pattern, html)
            items = []
            seen = set()
            for link, title in matches:
                title = re.sub(r'<[^>]+>', '', title).strip()
                if title and len(title) > 4 and title not in seen:
                    seen.add(title)
                    items.append({
                        '标题': title,
                        '来源': '网易新闻',
                        '链接': link,
                        '热度': 0,
                        '排名': len(items) + 1,
                    })
            logger.info(f"网易新闻(解析) 获取成功: {len(items)} 条")
            return items[:30]
        except Exception as e:
            logger.debug(f"网易新闻解析也失败: {e}")
            return []

    def get_tencent_news(self) -> List[Dict]:
        """获取腾讯新闻热点"""
        try:
            resp = self._request(
                "https://i.news.qq.com/trpc.qqnews_web.kv_srv.kv_srv_http_proxy/list",
                params={"sub_srv_id": "24hours", "offset": 0, "limit": 20}
            )
            if not resp:
                return []

            data = resp.json()
            items = []
            for item in data.get('data', {}).get('list', []):
                items.append({
                    '标题': item.get('title', ''),
                    '来源': '腾讯新闻',
                    '链接': item.get('url', item.get('vurl', '')),
                    '摘要': item.get('abstract', ''),
                    '热度': item.get('readCount', 0) or item.get('commentCount', 0),
                    '排名': len(items) + 1,
                })
            logger.info(f"腾讯新闻 获取成功: {len(items)} 条")
            return items
        except Exception as e:
            logger.debug(f"腾讯新闻接口失败: {e}")
            return self._get_tencent_news_fallback()

    def _get_tencent_news_fallback(self) -> List[Dict]:
        try:
            url = "https://news.qq.com/"
            resp = self._request(url)
            if not resp:
                return []
            html = resp.text
            pattern = r'<a[^>]*href="(https?://news\.qq\.com/omn/\d+/\d+[^"]*)"[^>]*>(.*?)</a>'
            matches = re.findall(pattern, html)
            items = []
            seen = set()
            for link, title in matches:
                title = re.sub(r'<[^>]+>', '', title).strip()
                if title and len(title) > 4 and title not in seen:
                    seen.add(title)
                    items.append({
                        '标题': title,
                        '来源': '腾讯新闻',
                        '链接': link,
                        '热度': 0,
                        '排名': len(items) + 1,
                    })
            logger.info(f"腾讯新闻(备用) 获取成功: {len(items)} 条")
            return items[:30]
        except Exception as e:
            logger.warning(f"腾讯新闻备用也失败: {e}")
            return []

    def get_zhihu_hot(self) -> List[Dict]:
        """获取知乎热搜"""
        try:
            url = "https://www.zhihu.com/api/v3/feed/topstory/hot-lists/total"
            resp = self._request(url, headers={
                'Referer': 'https://www.zhihu.com/',
            }, params={'limit': '50', 'desktop': 'true'})
            if not resp:
                return []

            data = resp.json()
            items = []
            for item in data.get('data', []):
                target = item.get('target', {})
                title = target.get('title', '') or item.get('target', {}).get('question', {}).get('title', '')
                id_str = str(target.get('id', ''))
                items.append({
                    '标题': title,
                    '来源': '知乎热搜',
                    '链接': f"https://www.zhihu.com/question/{id_str}" if id_str else '',
                    '热度': target.get('voteup_count', 0) or target.get('heat', 0),
                    '排名': len(items) + 1,
                    '摘要': target.get('excerpt', ''),
                })
            if items:
                logger.info(f"知乎热搜 获取成功: {len(items)} 条")
                return items
            return self._get_zhihu_hot_fallback()
        except Exception as e:
            logger.warning(f"知乎热搜获取失败: {e}")
            return self._get_zhihu_hot_fallback()

    def _get_zhihu_hot_fallback(self) -> List[Dict]:
        try:
            resp = self._request("https://www.zhihu.com/hot")
            if not resp:
                return []
            html = resp.text
            pattern = r'"title":\s*"((?:[^"\\]|\\.)*)"'
            matches = re.findall(pattern, html)
            items = []
            seen = set()
            for title in matches:
                title = title.replace('\\"', '"').replace('\\n', '').strip()
                if title and len(title) > 4 and title not in seen:
                    seen.add(title)
                    items.append({
                        '标题': title,
                        '来源': '知乎热搜',
                        '链接': 'https://www.zhihu.com/hot',
                        '热度': 0,
                        '排名': len(items) + 1,
                    })
            logger.info(f"知乎热搜(备用) 获取成功: {len(items)} 条")
            return items[:30]
        except Exception as e:
            logger.debug(f"知乎热搜备用也失败: {e}")
            return []

    def crawl_all(self) -> Dict:
        """从所有来源爬取重大事件"""
        logger.info("=" * 50)
        logger.info("开始爬取实时国内重大事件...")
        logger.info("=" * 50)

        sources = [
            ('微博热搜', self.get_weibo_hot),
            ('百度热搜', self.get_baidu_hot),
            ('知乎热搜', self.get_zhihu_hot),
            ('网易新闻', self.get_163_news),
            ('腾讯新闻', self.get_tencent_news),
        ]

        all_events = {}
        total = 0
        for name, func in sources:
            try:
                items = func()
                if items:
                    all_events[name] = items
                    total += len(items)
                    logger.info(f"  ✓ {name}: {len(items)} 条")
                else:
                    logger.warning(f"  ✗ {name}: 获取为空")
                time.sleep(random.uniform(0.5, 1.5))
            except Exception as e:
                logger.error(f"  ✗ {name}: 出错 - {e}")

        result = {
            '更新时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            '来源数': len(all_events),
            '事件总数': total,
            '数据': all_events,
        }

        logger.info(f"爬取完成，共 {total} 条事件")
        return result

    def merge_and_sort(self, data: Dict, top_n: int = 50) -> List[Dict]:
        """合并所有来源并按热度排序"""
        all_items = []
        seen_titles = set()

        for source, items in data.get('数据', {}).items():
            for item in items:
                title = item.get('标题', '').strip()
                if not title or title in seen_titles:
                    continue
                seen_titles.add(title)
                item['综合来源'] = source
                all_items.append(item)

        def sort_key(item):
            hot = item.get('热度', 0)
            if isinstance(hot, str):
                try:
                    hot = int(hot)
                except ValueError:
                    hot = 0
            return -hot

        all_items.sort(key=sort_key)
        for i, item in enumerate(all_items[:top_n], 1):
            item['综合排名'] = i

        return all_items[:top_n]

    def save_data(self, data: Dict, filename: Optional[str] = None):
        """保存原始数据"""
        if filename is None:
            filename = datetime.now().strftime('news_data_%Y%m%d_%H%M%S.json')
        filepath = self.data_dir / filename
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        latest_path = self.data_dir / 'latest.json'
        with open(latest_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info(f"数据已保存: {filepath}")
        return filepath

    def save_sorted(self, items: List[Dict], filename: Optional[str] = None):
        """保存排序后的事件列表"""
        if filename is None:
            filename = datetime.now().strftime('hot_events_%Y%m%d_%H%M%S.json')
        filepath = self.data_dir / filename
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(items, f, ensure_ascii=False, indent=2)
        print(f"\n排序后的事件已保存: {filepath}")
        return filepath

    def print_events(self, items: List[Dict], top_n: int = 30):
        """打印事件列表"""
        print("\n" + "=" * 70)
        print(f"  🔥 实时国内重大事件榜  (更新: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')})")
        print("=" * 70)

        for i, item in enumerate(items[:top_n], 1):
            title = item.get('标题', '')
            source = item.get('综合来源', item.get('来源', ''))
            hot = item.get('热度', 0)
            rank = item.get('综合排名', i)

            try:
                hot_int = int(hot)
                hot_str = f"🔥 {hot_int:,}"
            except (ValueError, TypeError):
                hot_str = f"🔥 {hot}" if hot else ""
            label = ""
            if rank <= 3:
                label = " 🏆"
            elif rank <= 10:
                label = " ⭐"

            print(f"\n  {rank:2d}. {title}{label}")
            print(f"      📰 {source}  {hot_str}")

        print("\n" + "=" * 70)

    def run_once(self):
        """运行一次爬虫"""
        data = self.crawl_all()
        self.save_data(data)
        sorted_items = self.merge_and_sort(data, top_n=50)
        self.save_sorted(sorted_items)
        self.print_events(sorted_items, top_n=30)
        return data, sorted_items

    def run_continuous(self, interval: int = 300):
        """持续运行爬虫"""
        logger.info(f"🔄 实时事件监控启动，每 {interval} 秒更新一次")
        try:
            while True:
                try:
                    data = self.crawl_all()
                    self.save_data(data)
                    sorted_items = self.merge_and_sort(data)
                    self.save_sorted(sorted_items)
                    self.print_events(sorted_items)
                    logger.info(f"⏳ 等待 {interval} 秒后更新...")
                    time.sleep(interval)
                except Exception as e:
                    logger.error(f"运行出错: {e}")
                    time.sleep(interval)
        except KeyboardInterrupt:
            logger.info("爬虫已停止")


if __name__ == '__main__':
    crawler = NewsCrawler()

    import sys
    if len(sys.argv) > 1 and sys.argv[1] == '--continuous':
        interval = int(sys.argv[2]) if len(sys.argv) > 2 else 300
        print(f"持续监控模式，更新间隔: {interval} 秒")
        crawler.run_continuous(interval)
    else:
        print("单次运行模式，爬取实时国内重大事件...")
        crawler.run_once()
