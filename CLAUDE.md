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
- `build_book.py` — PDF 构建脚本（从 book/src 读取源文件）
- `.github/workflows/deploy.yml` — GitHub Pages 自动部署
- `文明.pdf` — 生成的 PDF 文件

## 添加新文章流程

1. 在 `book/src/partN/` 下创建 `.md` 文件，格式为 `# 标题` + 正文
2. 更新 `book/src/SUMMARY.md` 加入条目
3. 更新 `build_book.py` 的 `STRUCTURE` 加入对应条目
4. 本地生成 PDF：`python3 build_book.py`
5. `git push` 后 GitHub Pages 自动更新

## 构建命令

- 在线版本：`mdbook build book`（或推送后 GitHub Actions 自动构建）
- PDF 版本：`python3 build_book.py`（需要 npx md-to-pdf、PyMuPDF）
- 本地预览：`mdbook serve book --open`
