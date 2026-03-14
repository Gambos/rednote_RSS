"""
小红书关键词抓取 + 时间筛选脚本（Playwright版）
用法：
  第一次运行（登录）：python xhs_scraper_public.py --login
  之后每次抓取：     python xhs_scraper_public.py
  每天定时运行：     python xhs_scraper_public.py --schedule
"""

import json
import time
import random
import os
import argparse
import asyncio
from datetime import datetime
from playwright.async_api import async_playwright

# ─────────────────────────────────────────────
# 配置
# ─────────────────────────────────────────────

SESSION_FILE  = "xhs_session.json"
SEEN_FILE     = "xhs_seen.json"
SCHEDULE_TIME = "23:00"  # 每天晚上 23:00 运行

KEYWORDS = [
    # 类别1
    "关键词1",
    "关键词2",
    # 类别2
    "关键词3",
    "关键词4"
]

# 关键词到分类的映射
KEYWORD_CATEGORY = {
    "类别1": "关键词1",
    "类别1": "关键词2",
    "类别2": "关键词3",
    "类别2": "关键词4"
}

# 按点赞数排序的分类（其余用综合排序）
SORT_BY_LIKES_CATEGORIES = {"类别1"}

# 博主主页（只抓最近24小时内的新帖）
# 格式：{"name": "博主名称", "id": "博主ID"}
# 从小红书博主主页链接获取 ID：xiaohongshu.com/user/profile/{id}
BLOGGERS = [
    # 在这里添加你想追踪的博主
    # {"name": "博主名", "id": "博主ID"},
]

NOISE_KEYWORDS = ["advertisement", "purchase"]

# ─────────────────────────────────────────────
# 工具函数
# ─────────────────────────────────────────────

def load_seen():
    if os.path.exists(SEEN_FILE):
        with open(SEEN_FILE, encoding="utf-8") as f:
            return set(json.load(f))
    return set()

def save_seen(seen):
    with open(SEEN_FILE, "w", encoding="utf-8") as f:
        json.dump(list(seen), f)

def is_relevant(title):
    text = title.lower()
    return not any(k.lower() in text for k in NOISE_KEYWORDS)

def format_digest(posts):
    if not posts:
        return "今日没有新的相关内容。"

    # 按分类分组
    groups = {}
    for p in posts:
        cat = p.get("category", "其他")
        groups.setdefault(cat, []).append(p)

    lines = [f"📌 小红书日报 · {datetime.now().strftime('%Y-%m-%d')}\n共 {len(posts)} 条\n"]
    for cat, items in groups.items():
        lines.append(f"\n{'━'*20}")
        lines.append(f"📂 {cat}（{len(items)}条）")
        lines.append(f"{'━'*20}")
        for p in items:
            lines.append(f"📝 {p['title']}")
            if p.get("author"):
                lines.append(f"   👤 {p['author']}")
            lines.append(f"   🔗 {p['url']}")
            lines.append("")
    return "\n".join(lines)

# ─────────────────────────────────────────────
# 登录（只需运行一次）
# ─────────────────────────────────────────────

async def login():
    print("🌐 打开浏览器，请手动扫码登录小红书...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        await page.goto("https://www.xiaohongshu.com")
        print("登录完成后按回车保存登录状态...")
        input()
        await context.storage_state(path=SESSION_FILE)
        await browser.close()
    print(f"✅ 登录状态已保存到 {SESSION_FILE}")

# ─────────────────────────────────────────────
# 抓取单个关键词
# ─────────────────────────────────────────────

async def scrape_blogger(page, blogger):
    posts = []
    name = blogger["name"]
    uid  = blogger["id"]
    print(f"👤 抓取博主：{name}")
    try:
        await page.goto(f"https://www.xiaohongshu.com/user/profile/{uid}", timeout=15000)
        await page.wait_for_selector("section.note-item", timeout=10000)
        await asyncio.sleep(random.uniform(1, 2))

        items = await page.query_selector_all("section.note-item")
        print(f"  → 找到 {len(items)} 个帖子")

        for item in items:
            try:
                title_el = await item.query_selector("a.title span")
                title = await title_el.inner_text() if title_el else ""

                link_el = await item.query_selector("a.cover")
                href = await link_el.get_attribute("href") if link_el else ""
                post_url = f"https://www.xiaohongshu.com{href}" if href else ""

                if not title or not post_url:
                    continue

                posts.append({
                    "id": href,
                    "title": title.strip(),
                    "url": post_url,
                    "author": name,
                    "category": f"博主·{name}",
                })
            except Exception:
                continue
    except Exception as e:
        print(f"  ⚠️ 抓取失败: {e}")
    return posts


async def scrape_keyword(page, keyword):
    posts = []
    category = KEYWORD_CATEGORY.get(keyword, "其他")
    use_likes_sort = category in SORT_BY_LIKES_CATEGORIES
    print(f"🔍 搜索：{keyword}{'（点赞排序）' if use_likes_sort else ''}")
    try:
        url = f"https://www.xiaohongshu.com/search_result?keyword={keyword}&type=51"
        await page.goto(url, timeout=15000)
        await page.wait_for_selector("section.note-item", timeout=10000)
        await asyncio.sleep(random.uniform(1, 2))

        # hover筛选按钮，点击"一天内"，按需点击"最多点赞"
        try:
            await page.hover("div.filter", timeout=5000)
            await asyncio.sleep(0.5)
            await page.click("div.tags span:text('一天内')", timeout=5000)
            await asyncio.sleep(0.5)
            if use_likes_sort:
                await page.click("div.tags span:text('最多点赞')", timeout=5000)
            print(f"  ✅ 筛选已设置")
            await asyncio.sleep(random.uniform(1, 2))
        except Exception:
            print(f"  ⚠️ 筛选按钮点击失败，使用全部结果")

        # 滚动加载更多
        for _ in range(3):
            await page.evaluate("window.scrollBy(0, 800)")
            await asyncio.sleep(random.uniform(1, 2))

        items = await page.query_selector_all("section.note-item")
        print(f"  → 找到 {len(items)} 个帖子")

        for item in items:
            try:
                title_el = await item.query_selector("a.title span")
                title = await title_el.inner_text() if title_el else ""

                link_el = await item.query_selector("a.cover")
                href = await link_el.get_attribute("href") if link_el else ""
                post_url = f"https://www.xiaohongshu.com{href}" if href else ""

                author_el = await item.query_selector("span.author-wrapper span.name")
                author = await author_el.inner_text() if author_el else ""

                if not title or not post_url:
                    continue
                if not is_relevant(title):
                    continue

                posts.append({
                    "id": href,
                    "title": title.strip(),
                    "url": post_url,
                    "author": author.strip(),
                    "category": KEYWORD_CATEGORY.get(keyword, "其他"),
                })
            except Exception:
                continue

    except Exception as e:
        print(f"  ⚠️ 搜索失败: {e}")

    return posts

# ─────────────────────────────────────────────
# 主流程
# ─────────────────────────────────────────────

async def run():
    if not os.path.exists(SESSION_FILE):
        print("❌ 未找到登录状态，请先运行：python xhs_scraper_public.py --login")
        return

    print(f"\n{'='*40}")
    print(f"开始抓取 · {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*40}")

    seen = load_seen()
    all_posts = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(storage_state=SESSION_FILE)
        page = await context.new_page()

        for kw in KEYWORDS:
            posts = await scrape_keyword(page, kw)
            for post in posts:
                if post["id"] not in seen:
                    all_posts.append(post)
                    seen.add(post["id"])
            await asyncio.sleep(random.uniform(3, 6))

        for blogger in BLOGGERS:
            posts = await scrape_blogger(page, blogger)
            for post in posts:
                if post["id"] not in seen:
                    all_posts.append(post)
                    seen.add(post["id"])
            await asyncio.sleep(random.uniform(3, 6))

        await browser.close()

    unique = list({p["id"]: p for p in all_posts}.values())
    digest = format_digest(unique)
    print("\n" + digest)
    save_seen(seen)

    with open("xhs_digest.txt", "w", encoding="utf-8") as f:
        f.write(digest)
    print(f"\n✅ 完成，新增 {len(unique)} 条，已保存到 xhs_digest.txt")

# ─────────────────────────────────────────────
# 入口
# ─────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--login", action="store_true", help="重新登录")
    parser.add_argument("--schedule", action="store_true", help="每天定时运行")
    args = parser.parse_args()

    if args.login:
        asyncio.run(login())
    elif args.schedule:
        import schedule as sch
        print(f"⏰ 定时模式：每天 {SCHEDULE_TIME} 运行")
        sch.every().day.at(SCHEDULE_TIME).do(lambda: asyncio.run(run()))
        asyncio.run(run())
        while True:
            sch.run_pending()
            time.sleep(60)
    else:
        asyncio.run(run())
