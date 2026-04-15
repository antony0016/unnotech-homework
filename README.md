# Unnotech Backend Engineer 徵才小專案

實作 UDN NBA 焦點新聞爬蟲，含完整的後端 API、前端頁面、定時排程與即時推播功能。

**Demo：<http://18.183.140.212/>**

## Features

- **爬蟲引擎**：`requests` + `BeautifulSoup` 抓取 UDN NBA 輪播焦點新聞（標題、圖片、圖說、內文、作者、發佈時間），URL 去重避免重複寫入，請求間隨機 jitter 防偵測
- **RESTful API**：DRF `ReadOnlyModelViewSet`，列表支援分頁（5/10/20 筆切換），詳情含完整內文
- **前端頁面**：Vanilla JS + Django template，列表頁分頁 + 筆數選擇，詳情頁全文展示，`escapeHtml` 防 XSS
- **定時排程**：`supercronic` 每 30 分鐘觸發 `scrape_news`，container 啟動時先跑一次
- **WebSocket 即時推播**：Django Channels + Redis Channel Layer，爬蟲抓到新資料時跨 container 廣播，前端 toast 提示 + 自動 refetch
- **Redis 快取**：列表 API `cache_page` 快取（TTL 300s），寫入時 `delete_pattern` 主動 invalidate
- **SQLite WAL**：開啟 WAL + IMMEDIATE transaction mode，web / cron 共用 db file 讀寫可並行
- **一鍵部署**：`deploy/lightsail-bootstrap.sh` 在 Amazon Linux 2023 自動裝 Docker、產生 `.env`、`docker compose up`

## Architecture

```plaintext
┌───────────────┐    ┌───────────────┐    ┌───────────┐
│  Browser      │◄──►│  web (daphne) │◄──►│  Redis    │
│  (vanilla JS) │    │  HTTP + WS    │    │  cache/ch │
└───────────────┘    └───────────────┘    └───────────┘
                     ┌────────────────┐         ▲
                     │  cron          │─────────┘
                     │  (supercronic) │  broadcast via
                     │  scrape_news   │  Channel Layer
                     └────────────────┘
                            │
                     ┌───────────────┐
                     │  SQLite (WAL) │
                     │  shared vol   │
                     └───────────────┘
```

## Tech Stack

| Layer | Technology |
| --- | --- |
| Language | Python 3.12 |
| Framework | Django 6.0 + DRF |
| WebSocket | Django Channels + channels-redis |
| Cache | django-redis |
| Database | SQLite (WAL mode) |
| Scraping | requests + BeautifulSoup4 + lxml |
| Task Scheduling | supercronic |
| Package Manager | uv |
| Deployment | Docker Compose |

## Completed Requirements

### 基本要求

- [x] 爬取 UDN NBA 焦點新聞（輪播區塊）
- [x] 儲存至 Django Model（title, url, image_url, image_caption, content, author, published_at）
- [x] DRF API：列表（分頁）+ 詳情
- [x] 前端頁面：列表頁 + 詳情頁（vanilla JS fetch API）

### 進階要求

- [x] Crontab 定時爬取（每 30 分鐘）
- [x] WebSocket 即時通知前端有新新聞
- [x] 部署至伺服器並可正確運行
- [x] 新聞列表 API 可承受 100 QPS 壓力測試

### 額外完成

- [x] Redis 快取 + 主動 invalidation
- [x] Docker Compose 一鍵啟動（web / redis / cron）
- [x] Lightsail 一鍵部署腳本（Amazon Linux 2023）
- [x] SQLite WAL mode 避免跨 container 寫入鎖
- [x] XSS 防護（escapeHtml）
- [x] URL 去重（去除 tracking query string）

## Load Test Results

> AWS Lightsail（2 vCPU / 2GB Memory），測試工具：ApacheBench

| Endpoint | Concurrency | RPS | P50 | P99 | Error Rate |
| --- | --- | --- | --- | --- | --- |
| `GET /api/news/` (cache hit) | 100 | **181 req/s** | 533ms | 797ms | 0% |
| `GET /api/news/1/` | 50 | **144 req/s** | 326ms | 448ms | 0% |

延遲含台灣→東京網路來回（~40ms RTT），server 實際處理 5-7ms。

## How to Run

```bash
# Docker Compose 本機啟動
cd unnotech-homework
docker compose up -d --build
# open http://localhost:8000

# Lightsail 一鍵部署（Amazon Linux 2023）
sudo bash deploy/lightsail-bootstrap.sh
# 記得到 Networking 開放 80/tcp
```

## API Endpoints

| Method | Path | Description |
| --- | --- | --- |
| GET | `/api/news/` | 焦點新聞列表（分頁，支援 `?page=` & `?page_size=`） |
| GET | `/api/news/{id}/` | 焦點新聞詳情 |
| WS | `/ws/news/` | WebSocket，接收新新聞即時通知 |
