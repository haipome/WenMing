#!/usr/bin/env python3
"""从博客链接抓取文章，转为 Markdown 并添加到 mdBook 中

用法：
  python3 add_article.py <博客URL> <部分编号> [文章短名]   # 添加新文章
  python3 add_article.py <博客URL>                         # 更新已有文章（自动匹配标题）

示例：
  python3 add_article.py https://www.haipo.me/2026/03/blog-post_87.html 1
  python3 add_article.py https://www.haipo.me/2026/03/blog-post.html 2 新文章名
  python3 add_article.py https://www.haipo.me/2026/03/blog-post_11.html  # 更新
"""

import json
import os
import re
import sys
import urllib.request
import urllib.parse

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BOOK_SRC = os.path.join(BASE_DIR, "book", "src")
SUMMARY_PATH = os.path.join(BOOK_SRC, "SUMMARY.md")

FEED_URL = (
    "https://www.haipo.me/feeds/posts/default"
    "?alt=json&max-results=500"
)


def fetch_all_entries():
    """获取博客所有文章"""
    req = urllib.request.Request(FEED_URL, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return data["feed"].get("entry", [])


def find_entry_by_url(entries, target_url):
    """通过 URL 找到对应文章"""
    for entry in entries:
        for link in entry.get("link", []):
            if link.get("rel") == "alternate" and link.get("type") == "text/html":
                if link.get("href", "").rstrip("/") == target_url.rstrip("/"):
                    return entry
    return None


def html_to_markdown(html):
    """将 HTML 简单转换为 Markdown"""
    text = html

    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<p[^>]*>", "\n\n", text, flags=re.IGNORECASE)
    text = re.sub(r"</p>", "", text, flags=re.IGNORECASE)

    for level in range(1, 7):
        prefix = "#" * level + " "
        text = re.sub(
            rf"<h{level}[^>]*>(.*?)</h{level}>",
            lambda m, p=prefix: f"\n\n{p}{m.group(1).strip()}\n\n",
            text,
            flags=re.IGNORECASE | re.DOTALL,
        )

    text = re.sub(
        r'<a\s[^>]*href=["\']([^"\']*)["\'][^>]*>(.*?)</a>',
        r"[\2](\1)",
        text,
        flags=re.IGNORECASE | re.DOTALL,
    )

    text = re.sub(
        r'<img\s[^>]*src=["\']([^"\']*)["\'][^>]*/?>',
        r"![](\1)",
        text,
        flags=re.IGNORECASE,
    )

    text = re.sub(
        r"<(?:b|strong)[^>]*>(.*?)</(?:b|strong)>",
        r"**\1**",
        text,
        flags=re.IGNORECASE | re.DOTALL,
    )

    text = re.sub(
        r"<(?:i|em)[^>]*>(.*?)</(?:i|em)>",
        r"*\1*",
        text,
        flags=re.IGNORECASE | re.DOTALL,
    )

    text = re.sub(
        r"<blockquote[^>]*>(.*?)</blockquote>",
        lambda m: "\n" + "\n".join("> " + line for line in m.group(1).strip().splitlines()) + "\n",
        text,
        flags=re.IGNORECASE | re.DOTALL,
    )

    text = re.sub(r"</?[uo]l[^>]*>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(
        r"<li[^>]*>(.*?)</li>",
        r"- \1",
        text,
        flags=re.IGNORECASE | re.DOTALL,
    )

    text = re.sub(r"<div[^>]*>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"</div>", "\n", text, flags=re.IGNORECASE)

    text = re.sub(r"<[^>]+>", "", text)

    text = text.replace("&nbsp;", " ")
    text = text.replace("&amp;", "&")
    text = text.replace("&lt;", "<")
    text = text.replace("&gt;", ">")
    text = text.replace("&quot;", '"')
    text = text.replace("&#39;", "'")
    text = re.sub(r"&#(\d+);", lambda m: chr(int(m.group(1))), text)
    text = re.sub(r"&[a-zA-Z]+;", "", text)

    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def get_next_chapter_num():
    """扫描所有 part 目录，找到下一个章节编号"""
    max_num = 0
    for d in os.listdir(BOOK_SRC):
        part_dir = os.path.join(BOOK_SRC, d)
        if os.path.isdir(part_dir) and d.startswith("part"):
            for f in os.listdir(part_dir):
                m = re.match(r"(\d+)-", f)
                if m:
                    max_num = max(max_num, int(m.group(1)))
    return max_num + 1


def safe_filename(title):
    name = re.sub(r'[\\/:*?"<>|]', "", title)
    return name.strip()[:80] or "untitled"


def find_existing_file(title):
    """根据标题搜索已有的文章文件，返回文件路径或 None"""
    for d in os.listdir(BOOK_SRC):
        part_dir = os.path.join(BOOK_SRC, d)
        if not os.path.isdir(part_dir) or not d.startswith("part"):
            continue
        for f in os.listdir(part_dir):
            if not f.endswith(".md"):
                continue
            filepath = os.path.join(part_dir, f)
            with open(filepath, "r", encoding="utf-8") as fh:
                first_line = fh.readline().strip()
            # mdBook 格式：第一行是 # 标题
            if first_line == f"# {title}":
                return filepath
    return None


def update_summary(part_num, title, rel_path):
    """在 SUMMARY.md 的对应部分末尾添加新条目"""
    with open(SUMMARY_PATH, "r", encoding="utf-8") as f:
        lines = f.readlines()

    part_header = f"# 第{'一二三四五六七八九十'[part_num - 1]}部分"

    # 找到对应部分的位置
    part_start = -1
    for i, line in enumerate(lines):
        if line.strip().startswith(part_header):
            part_start = i
            break

    if part_start == -1:
        # 部分不存在，在末尾添加新部分
        part_names = {
            1: "文明的底层逻辑",
            2: "自由秩序的建立",
            3: "自由秩序的衰退",
            4: "重建与实验",
        }
        part_name = part_names.get(part_num, "新部分")
        lines.append(f"\n---\n\n# 第{'一二三四五六七八九十'[part_num - 1]}部分：{part_name}\n\n")
        lines.append(f"- [{title}]({rel_path})\n")
    else:
        # 找到该部分最后一个 `- [` 条目的位置
        insert_pos = part_start + 1
        for i in range(part_start + 1, len(lines)):
            line = lines[i].strip()
            if line.startswith("- ["):
                insert_pos = i + 1
            elif line.startswith("#") or line == "---":
                break

        lines.insert(insert_pos, f"- [{title}]({rel_path})\n")

    with open(SUMMARY_PATH, "w", encoding="utf-8") as f:
        f.writelines(lines)


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    blog_url = sys.argv[1]
    part_num = int(sys.argv[2]) if len(sys.argv) >= 3 else None
    short_name = sys.argv[3] if len(sys.argv) > 3 else None

    print(f"正在获取博客文章列表...")
    entries = fetch_all_entries()
    print(f"共获取 {len(entries)} 篇文章")

    entry = find_entry_by_url(entries, blog_url)
    if not entry:
        print(f"错误：找不到 URL 对应的文章: {blog_url}")
        sys.exit(1)

    title = entry["title"]["$t"]
    print(f"找到文章：{title}")

    content_html = ""
    if "content" in entry:
        content_html = entry["content"]["$t"]
    elif "summary" in entry:
        content_html = entry["summary"]["$t"]

    body = html_to_markdown(content_html)
    md_content = f"# {title}\n\n{body}\n"

    # 检查是否已有同名文章
    existing = find_existing_file(title)
    if existing:
        with open(existing, "w", encoding="utf-8") as f:
            f.write(md_content)
        print(f"已更新: {existing}")
        print(f"\n完成！git push 后 GitHub Pages 会自动更新")
        return

    # 新增模式：需要部分编号
    if part_num is None:
        print(f"错误：未找到已有文章，新增需要指定部分编号")
        print(f"用法：python3 add_article.py <URL> <部分编号>")
        sys.exit(1)

    chapter_num = get_next_chapter_num()
    file_short = short_name or safe_filename(title)
    filename = f"{chapter_num:02d}-{file_short}.md"
    part_dir = os.path.join(BOOK_SRC, f"part{part_num}")
    os.makedirs(part_dir, exist_ok=True)
    filepath = os.path.join(part_dir, filename)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(md_content)
    print(f"已保存: {filepath}")

    rel_path = f"part{part_num}/{filename}"
    update_summary(part_num, title, rel_path)
    print(f"已更新 SUMMARY.md")

    print(f"\n完成！别忘了：")
    print(f"  1. 更新 build_book.py 的 STRUCTURE（如果需要生成 PDF）")
    print(f"  2. git push 后 GitHub Pages 会自动更新")


if __name__ == "__main__":
    main()
