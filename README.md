# 高性价比人生指南（重排阅读版）

线上地址：<https://ychaojie.github.io/>

这是《高性价比人生指南》的重新排版阅读版：34 章、765 条建议，每条说明成本、收益、证据等级和原始出处。

## 引用与许可

- 原文：《高性价比人生指南》，作者 eternity4719
- 原仓库：<https://github.com/eternity4719/HowToLiveBetter>
- 许可证：<https://creativecommons.org/licenses/by/4.0/>（CC BY 4.0）
- 本页面对原书做了重新排版与目录重组；条目文字以原仓库为准，同步自 2026-10-17 的版本。

## 目录结构

- `index.html`：指南首页与重排目录
- `01.html` ~ `34.html`：各章节阅读页
- `css/guide.css`：页面样式
- `js/guide.js`：页面脚本
- `tools/build-guide.py`：从原仓库的 `book/*.md` 重新生成页面

## 重新生成

```bash
git clone https://github.com/eternity4719/HowToLiveBetter.git /tmp/HowToLiveBetter
python tools/build-guide.py /tmp/HowToLiveBetter
```
