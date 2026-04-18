# RS-Paper-Hub

arXiv 遥感 (Remote Sensing) 论文爬取工具。自动从 arXiv `cs.CV` 分类检索 2022 年至今的遥感领域论文，提取结构化元数据并支持 PDF 批量下载。支持断点续传，中断后自动从上次进度恢复。

## 安装

```bash
pip install -r requirements.txt
```

依赖：`arxiv`, `requests`, `pandas`, `tqdm`

## 快速开始

```bash
# 爬取少量论文测试
python main.py --max-results 20

# 爬取全部论文（2022至今），仅获取元数据
python main.py

# 爬取并下载 PDF
python main.py --max-results 50 --download

# 查看当前进度
python main.py --status
```

## 使用说明

### 基础爬取

```bash
# 默认爬取 cs.CV 中 2022-2026 遥感论文，输出到 output/
python main.py

# 指定年份范围
python main.py --start-year 2023 --end-year 2025

# 限制数量（调试用）
python main.py --max-results 100
```

### 断点续传

所有进度自动记录在 `output/progress.json` 中。无论爬取还是下载，中断后重新运行即可自动跳过已完成的部分：

```bash
# 第一次运行，爬了一半中断了
python main.py --download
# Ctrl+C

# 再次运行，自动从断点继续
python main.py --download

# 查看当前进度
python main.py --status
# Scraped: 1234 papers (up to 2024-03) | Downloaded: 800, Failed: 2

# 如需完全重新开始，删除进度文件
rm output/progress.json
```

### PDF 下载

```bash
# 爬取元数据同时下载 PDF
python main.py --download

# 仅下载 PDF（基于已有的 output/papers.csv，不重新爬取）
python main.py --download-only
```

PDF 按年份存放在 `output/pdfs/` 目录下：

```
output/pdfs/
├── 2022/
│   ├── 2201.00769v2_InSAR_Phase_Denoising.pdf
│   └── ...
├── 2023/
├── 2024/
└── ...
```

### 增量爬取

```bash
# 跳过已有论文，只爬取新增
python main.py --incremental
```

### 代码仓库查询（可选）

默认不查询代码链接。如需从 Papers With Code 获取代码仓库：

```bash
python main.py --with-code
```

### 全部参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--start-year` | 起始年份 | 2022 |
| `--end-year` | 结束年份 | 2026 |
| `--max-results` | 最大论文数量 | 无限制 |
| `--output-dir` | 输出目录 | `output` |
| `--download` | 下载 PDF 到本地 | 关 |
| `--download-only` | 仅下载 PDF（跳过爬取） | 关 |
| `--with-code` | 查询 Papers With Code 代码链接 | 关 |
| `--incremental` | 增量模式，跳过已有论文 | 关 |
| `--status` | 显示当前进度并退出 | - |
| `-v, --verbose` | 详细日志输出 | 关 |

## 输出格式

同时输出 CSV 和 JSON 两种格式到 `output/` 目录。

### 字段说明

| 字段 | 说明 | 示例 |
|------|------|------|
| Type | arXiv 主分类 | Computer Vision |
| Subtype | 其他分类 | Image and Video Processing |
| Month | 发表月份 | 3 |
| Year | 发表年份 | 2023 |
| Institute | 第一作者机构 | (arXiv 数据有限，可能为空) |
| Title | 论文标题 | Hybrid Attention Network for... |
| abbr. | 标题中的缩写 | HMANet |
| Paper_link | arXiv 链接 | http://arxiv.org/abs/2301.12345 |
| Abstract | 摘要 | ... |
| code | 代码仓库链接 | (需 `--with-code`) |
| Publication | 发表期刊/会议 | CVPR 2023 |
| BibTex | BibTeX 引用 | @article{...} |
| Authors | 作者列表 | Alice, Bob, Charlie |

## 搜索范围

当前搜索 arXiv `cs.CV`（计算机视觉）分类中标题或摘要包含 "remote sensing" 的论文。

如需调整搜索关键词或分类，编辑 `config.py` 中的 `SEARCH_QUERY`。例如扩展到多个分类：

```python
SEARCH_QUERY = (
    '(ti:"remote sensing" OR abs:"remote sensing")'
    ' AND (cat:cs.CV OR cat:eess.IV OR cat:eess.SP)'
)
```

## 速率限制

| 操作 | 限制 | 说明 |
|------|------|------|
| 查询元数据 | ~3 秒/请求 | 每次返回最多 100 条，实际吞吐量较高 |
| 下载 PDF | ~3 秒/文件 | 逐个下载，较慢，建议用 `--download-only` 分开处理 |

建议工作流：先只查询元数据（速度快），确认结果无误后再单独下载 PDF。

## 项目结构

```
rs-paper-hub/
├── main.py            # CLI 入口
├── config.py          # 搜索配置（关键词、日期、分类）
├── scraper.py         # arXiv API 爬虫（按月分批，断点续传）
├── parser.py          # 数据解析与 BibTeX 生成
├── downloader.py      # PDF 下载器（断点续传）
├── progress.py        # 进度追踪器
├── pwc_client.py      # Papers With Code 客户端（可选）
├── requirements.txt   # Python 依赖
└── output/            # 输出目录
    ├── papers.csv
    ├── papers.json
    ├── progress.json  # 进度记录（自动生成）
    └── pdfs/          # PDF 文件（按年份分目录）
```

## 网页可视化

启动本地服务器浏览论文数据：

```bash
cd /Users/jianchengpan/Projects/rs-paper-hub
python3 -m http.server 8080
```

打开浏览器访问 http://localhost:8080 即可查看。支持搜索、筛选、排序、图表统计、BibTeX 复制和 LaTeX 公式渲染。

## 注意事项

- `Institute` 字段依赖 arXiv 提供的 affiliation 信息，大部分论文未提供，可能为空
- 已下载的 PDF 和已爬取的月份不会重复处理
- 进度文件 `progress.json` 采用原子写入，中断不会损坏
