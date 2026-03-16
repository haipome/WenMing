# CLAUDE.md

## 项目概述

《文明》系列文章合集，作者杨海坡。包含在线阅读（mdBook + GitHub Pages）和 PDF 两种版本。

## 项目结构

- `book/` — mdBook 项目
  - `book/src/SUMMARY.md` — 目录结构
  - `book/src/cover.md` — 封面页
  - `book/src/cover.png` — 封面图片
  - `book/src/custom.css` — 自定义样式
  - `book/src/part{1-4}/` — 各部分文章（Markdown）
  - `book/book.toml` — mdBook 配置
- `add_article.py` — 从博客（haipo.me）抓取文章，自动转 Markdown 并添加到 mdBook
- `build_book.py` — PDF 构建脚本（从 book/src 读取源文件）
- `README.md` — 项目说明文档
- `文明.md` — PDF 构建的中间产物（由 build_book.py 生成）
- `文明.pdf` — 生成的 PDF 文件
- `.github/workflows/deploy.yml` — GitHub Pages 自动部署

## 添加新文章流程

**方式一（推荐）：使用脚本自动抓取**

```
python3 add_article.py <博客URL> <部分编号>
```

脚本会自动创建 `.md` 文件并更新 `SUMMARY.md`，之后手动更新 `build_book.py` 的 `STRUCTURE` 即可生成 PDF。

**方式二：手动添加**

1. 在 `book/src/partN/` 下创建 `.md` 文件，格式为 `# 标题` + 正文
2. 更新 `book/src/SUMMARY.md` 加入条目
3. 更新 `build_book.py` 的 `STRUCTURE` 加入对应条目
4. 本地生成 PDF：`python3 build_book.py`
5. `git push` 后 GitHub Pages 自动更新

## 构建命令

- 在线版本：`mdbook build book`（或推送后 GitHub Actions 自动构建）
- PDF 版本：`python3 build_book.py`（需要 npx md-to-pdf、PyMuPDF）
- 本地预览：`mdbook serve book --open`
