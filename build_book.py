#!/usr/bin/env python3
"""将文明系列文章组装成结构化册子，输出 Markdown 和 PDF"""

import os
import re
import subprocess

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BOOK_SRC = os.path.join(BASE_DIR, "book", "src")

STRUCTURE = [
    ("第一部分：文明的底层逻辑", [
        ("part1/01-意识的阶梯.md", "意识的阶梯：理解社会的底层逻辑"),
        ("part1/02-发展可能从来不是文明的目的.md", "发展可能从来不是文明的目的"),
        ("part1/03-儒学.md", "儒学：一套文明的操作系统"),
    ]),
    ("第二部分：自由秩序的建立", [
        ("part2/04-自由的力量.md", "自由的力量"),
        ("part2/05-伟大的核武器.md", "伟大的核武器"),
    ]),
    ("第三部分：自由秩序的衰退", [
        ("part3/06-拆掉栅栏的人.md", "拆掉栅栏的人"),
        ("part3/07-失去中产阶级的自由社会.md", "失去中产阶级的自由社会"),
        ("part3/08-灯塔的熄灭.md", "灯塔的熄灭"),
    ]),
    ("第四部分：重建与实验", [
        ("part4/09-稳定的共和.md", "稳定的共和"),
        ("part4/10-区块链.md", "区块链：一场硬核的自由主义实验"),
    ]),
]

CSS = """\
<style>
  @page {
    size: A4;
    margin: 2.5cm 2cm;
  }

  body {
    font-family: "PingFang SC", "Noto Sans CJK SC", "Microsoft YaHei", sans-serif;
    font-size: 12pt;
    line-height: 2;
    color: #1a1a1a;
  }

  /* ── 封面（占位，后续用 PyMuPDF 替换） ── */
  .cover {
    page-break-after: always;
    text-align: center;
  }
  .cover-img {
    width: 100%;
    max-height: 82vh;
    object-fit: contain;
    display: block;
  }

  /* ── 目录 ── */
  .toc {
    page-break-after: always;
  }
  .toc-heading {
    text-align: center;
    font-size: 22pt;
    font-weight: 700;
    margin-bottom: 1.2em;
    letter-spacing: 0.2em;
  }
  .toc-part {
    font-size: 11.5pt;
    font-weight: 700;
    margin-top: 1.6em;
    margin-bottom: 0.2em;
    color: #333;
  }
  .toc-item {
    font-size: 10.5pt;
    line-height: 2.2;
    padding-left: 1.5em;
    color: #444;
    display: flex;
    justify-content: space-between;
  }
  .toc-item a {
    color: #444;
    text-decoration: none;
  }
  .toc-page {
    flex-shrink: 0;
    padding-left: 0.5em;
    color: #888;
  }

  /* ── 部分扉页 ── */
  .part-page {
    text-align: center;
    padding-top: 35vh;
    page-break-before: always;
    page-break-after: always;
  }
  .part-page-title {
    font-size: 22pt;
    font-weight: 700;
    letter-spacing: 0.15em;
    color: #222;
  }

  /* ── 文章标题 ── */
  .chapter-title {
    font-size: 20pt;
    font-weight: 700;
    margin-top: 0;
    padding-top: 0.5em;
    padding-bottom: 0.5em;
    margin-bottom: 1.2em;
    border-bottom: 2px solid #ddd;
    page-break-before: always;
    color: #111;
  }

  /* ── 文章内标题 ── */
  h3 {
    font-size: 14pt;
    font-weight: 700;
    margin-top: 2.5em;
    margin-bottom: 0.6em;
    color: #222;
  }

  h4 {
    font-size: 12pt;
    font-weight: 700;
    margin-top: 2em;
    margin-bottom: 0.5em;
    color: #333;
  }

  p {
    text-align: justify;
    margin: 0.8em 0;
  }

  blockquote {
    border-left: 3px solid #ccc;
    margin: 1.2em 0;
    padding: 0.4em 1em;
    color: #555;
    background: #fafafa;
  }

  hr {
    border: none;
    border-top: 1px solid #e0e0e0;
    margin: 2em 0;
  }

  a { color: #1a1a1a; text-decoration: none; }
  strong { font-weight: 700; }

  /* 避免标题和段落分离 */
  h3, h4 { page-break-after: avoid; }
</style>
"""


def read_chapter(rel_path):
    """从 book/src 读取章节，跳过第一行 # 标题"""
    filepath = os.path.join(BOOK_SRC, rel_path)
    with open(filepath, "r", encoding="utf-8") as f:
        text = f.read()
    lines = text.splitlines()
    # 跳过第一行 # 标题和紧随的空行
    start = 0
    if lines and lines[0].startswith("# "):
        start = 1
        while start < len(lines) and lines[start].strip() == "":
            start += 1
    return "\n".join(lines[start:]).strip()


FRONTMATTER = """\
---
pdf_options:
  format: A4
  margin:
    top: "2.5cm"
    bottom: "2cm"
    left: "2cm"
    right: "2cm"
---
"""


def build_markdown(toc_pages=None):
    out = []

    # Front-matter
    out.append(FRONTMATTER)

    # CSS
    out.append(CSS)

    # 封面（用 AI 生成的图片）
    out.append("""\
<div class="cover">
  <img src="book/src/cover.png" class="cover-img">
</div>
""")

    # 目录
    out.append('<div class="toc">')
    out.append('<div class="toc-heading">目 录</div>')
    chapter_num = 0
    for part_title, articles in STRUCTURE:
        out.append(f'<div class="toc-part">{part_title}</div>')
        for _, display_title in articles:
            chapter_num += 1
            page_str = ""
            if toc_pages and chapter_num in toc_pages:
                page_str = f'<span class="toc-page">{toc_pages[chapter_num]}</span>'
            out.append(f'<div class="toc-item"><a href="#chapter-{chapter_num}">{chapter_num}. {display_title}</a>{page_str}</div>')
    out.append('</div>\n')

    # 正文
    chapter_num = 0
    for part_title, articles in STRUCTURE:
        # 部分扉页
        out.append(f'<div class="part-page"><div class="part-page-title">{part_title}</div></div>\n')

        for rel_path, display_title in articles:
            chapter_num += 1
            body = read_chapter(rel_path)
            # 文章标题（HTML 控制样式）
            out.append(f'<div class="chapter-title" id="chapter-{chapter_num}">{display_title}</div>\n')
            out.append(body)
            out.append("\n")

    return "\n".join(out)


def write_md(md_content):
    md_path = os.path.join(BASE_DIR, "文明.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_content)
    return md_path


def gen_pdf(md_path):
    pdf_path = md_path.replace(".md", ".pdf")
    subprocess.run(["npx", "md-to-pdf@5.2.5", md_path], check=True)
    return pdf_path


def find_content_start(pdf_path):
    """找到正文起始页（第一个部分扉页），返回 0-based 页索引"""
    import fitz
    doc = fitz.open(pdf_path)
    first_part_title = STRUCTURE[0][0]  # "第一部分：文明的底层逻辑"
    for page_num in range(len(doc)):
        page = doc[page_num]
        if page.search_for(first_part_title):
            # 跳过目录页中的匹配
            if page_num >= 2:
                doc.close()
                return page_num
    doc.close()
    return 2  # fallback


def extract_toc_pages(pdf_path, offset):
    """从 PDF 中查找各章标题所在的页码（减去 offset 后从 1 开始）"""
    import fitz
    doc = fitz.open(pdf_path)
    toc_pages = {}
    chapter_titles = {}
    chapter_num = 0
    for _, articles in STRUCTURE:
        for _, display_title in articles:
            chapter_num += 1
            chapter_titles[chapter_num] = display_title
    for chapter_num, title in chapter_titles.items():
        for page_num in range(len(doc)):
            page = doc[page_num]
            if page.search_for(title):
                if page_num >= offset:
                    toc_pages[chapter_num] = page_num - offset + 1
                    break
    doc.close()
    return toc_pages


def replace_cover_page(pdf_path):
    """用 PyMuPDF 将第一页替换为铺满整页的封面图片"""
    import fitz
    cover_img = os.path.join(BOOK_SRC, "cover.png")
    doc = fitz.open(pdf_path)
    # 删除原封面页
    doc.delete_page(0)
    # 在最前面插入空白 A4 页
    page = doc.new_page(pno=0, width=595.28, height=841.89)  # A4 in points
    # 将封面图片铺满整页
    page.insert_image(page.rect, filename=cover_img)
    tmp_path = pdf_path + ".tmp"
    doc.save(tmp_path, encryption=0)
    doc.close()
    os.replace(tmp_path, pdf_path)


def stamp_page_numbers(pdf_path, content_start):
    """用 PyMuPDF 在正文页底部添加页码，从 1 开始编号"""
    import fitz
    doc = fitz.open(pdf_path)
    for page_idx in range(content_start, len(doc)):
        page = doc[page_idx]
        page_number = page_idx - content_start + 1
        rect = page.rect
        # 页面底部居中
        text_point = fitz.Point(rect.width / 2, rect.height - 28)
        page.insert_text(
            text_point,
            str(page_number),
            fontsize=9,
            fontname="helv",
            color=(0.6, 0.6, 0.6),
            render_mode=0,
        )
    doc.save(pdf_path, incremental=True, encryption=0)
    doc.close()


def main():
    # 第一遍：不带目录页码，生成 PDF 以确定各章页码
    md_content = build_markdown()
    md_path = write_md(md_content)
    print(f"第一遍: 已生成 {md_path}")
    pdf_path = gen_pdf(md_path)
    print(f"第一遍: 已生成 {pdf_path}")

    # 找到正文起始页
    content_start = find_content_start(pdf_path)
    print(f"正文起始页: 第 {content_start + 1} 页 (0-based: {content_start})")

    # 提取各章页码（相对于正文起始）
    toc_pages = extract_toc_pages(pdf_path, content_start)
    print(f"各章页码: {toc_pages}")

    # 第二遍：带目录页码重新生成
    md_content = build_markdown(toc_pages=toc_pages)
    md_path = write_md(md_content)
    print(f"第二遍: 已生成 {md_path}")
    pdf_path = gen_pdf(md_path)
    print(f"第二遍: 已生成 {pdf_path}")

    # 替换封面页为铺满整页的图片
    replace_cover_page(pdf_path)
    print("已替换封面页")

    # 添加页码到正文页
    content_start = find_content_start(pdf_path)
    stamp_page_numbers(pdf_path, content_start)
    print(f"已添加页码（从正文第 {content_start + 1} 页开始）")


if __name__ == "__main__":
    main()
