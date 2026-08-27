# Chapter 01：從零開始——單一伺服器架構

## 架構演進

```text
Stage 01：單一 Web Server
    ↓
Stage 02：Load Balancer + 多台 Web Server
    ↓
Stage 03：Database Primary + Replicas（讀寫分離）
```

| Stage | 程式 | 架構決策 | 狀態 |
| --- | --- | --- | --- |
| 01 | [`stage01_single_server.py`](./src/stage01_single_server.py) | [`001-single-server.md`](./decisions/001-single-server.md) | 已完成 |
| 02 | [`stage02_load_balancer.py`](./src/stage02_load_balancer.py) | [`002-load-balancer.md`](./decisions/002-load-balancer.md) | 已完成 |
| 03 | [`stage03_database_replication.py`](./src/stage03_database_replication.py) | [`003-database-replication.md`](./decisions/003-database-replication.md) | 骨架 |

## 目標

本章先從最簡單的系統架構開始：所有使用者請求都由一台 Web Server 處理。

使用者在瀏覽器輸入網域名稱後，會先透過 DNS 取得伺服器的 IP 位址 `15.125.23.214`，接著向該伺服器發送 HTTP 請求，最後取得 HTML 並顯示網頁。

本章只討論靜態 HTML，不包含資料庫、快取、負載平衡器或多台伺服器。

## 系統架構

![單一 Web Server 系統架構](./assets/figure1.jpg)

圖中的 Web Browser 或 Mobile App 先向 DNS 查詢網域名稱，取得本章假設的 IP 位址 `15.125.23.214`，之後再連線至同一台 Web Server。Web Browser 請求網站內容，Mobile App 則通常透過 API 存取服務。

## 完整運作流程

### 1. 使用者輸入網址

假設使用者在瀏覽器輸入：

```text
http://example.com/index.html
```

瀏覽器會解析出：

- Protocol：`http`
- Domain：`example.com`
- Path：`/index.html`
- Port：`80`（HTTP 預設值）

### 2. DNS 解析網域名稱

瀏覽器需要先將容易閱讀的網域名稱轉換成電腦可連線的 IP 位址：

```text
example.com → 15.125.23.214
```

瀏覽器與作業系統會先檢查 DNS 快取。如果沒有找到紀錄，才會向 DNS Resolver 查詢。DNS 回應會包含 IP 位址與 TTL；TTL 決定這筆結果可以被快取多久。

在本章的模擬中，不實作真正的 DNS 查詢，而是由 DNS 元件直接回傳固定 IP：

```text
15.125.23.214
```

### 3. 建立 TCP 連線

取得 IP 後，瀏覽器會連線至：

```text
15.125.23.214:80
```

HTTP/1.1 使用 TCP 傳輸。傳送 HTTP Request 前，Client 與 Server 會先完成 TCP 三向交握：

```text
Browser                         Web Server
   │ -------- SYN -----------------> │
   │ <------- SYN + ACK ------------ │
   │ -------- ACK -----------------> │
```

TCP 負責可靠傳輸，確保資料依序抵達，並在封包遺失時重新傳送。

### 4. 發送 HTTP Request

連線建立後，瀏覽器發送 HTTP Request：

```http
GET /index.html HTTP/1.1
Host: example.com
Accept: text/html
Connection: keep-alive
```

其中：

- `GET` 表示讀取資源。
- `/index.html` 是要求的資源路徑。
- `Host` 表示目標網域。
- `Accept` 表示 Client 希望收到 HTML。
- `Connection: keep-alive` 表示完成這次請求後，可暫時保留 TCP 連線供後續請求使用。

### 5. Web Server 處理請求

Web Server 在 Port `80` 監聽連線。收到資料後會：

1. 接受 TCP 連線。
2. 解析 HTTP Method、Path 與 Headers。
3. 檢查請求方法是否支援。
4. 將 `/index.html` 對應到伺服器上的靜態檔案。
5. 讀取檔案內容。
6. 建立 HTTP Response。

路徑對應可以簡化成：

```text
GET /            → index.html
GET /index.html  → index.html
其他路徑          → 404 Not Found
```

### 6. 回傳 HTTP Response

找到檔案後，Server 回傳狀態碼、Headers 與 HTML：

```http
HTTP/1.1 200 OK
Content-Type: text/html; charset=utf-8
Content-Length: 79
Connection: keep-alive

<!doctype html>
<html>
  <body>
    <h1>Hello World</h1>
  </body>
</html>
```

HTTP Response 包含三個部分：

1. Status Line：例如 `HTTP/1.1 200 OK`。
2. Response Headers：描述內容類型、大小與連線方式。
3. Response Body：本次回傳的 HTML。

如果要求的檔案不存在，Server 應回傳：

```http
HTTP/1.1 404 Not Found
Content-Type: text/html; charset=utf-8

<h1>404 Not Found</h1>
```

### 7. 瀏覽器顯示 HTML

瀏覽器收到 Response 後會：

1. 根據狀態碼判斷請求是否成功。
2. 根據 `Content-Type` 判斷內容為 HTML。
3. 解析 HTML 並建立 DOM。
4. 計算頁面版面並繪製畫面。

如果 HTML 還引用 CSS、JavaScript 或圖片，瀏覽器會為每個資源繼續發送 HTTP Request。本章暫時只回傳單一 HTML，因此不模擬額外資源。

## 單一伺服器的責任

這個架構中，唯一的 Web Server 同時負責：

- 接受所有使用者連線。
- 解析所有 HTTP Requests。
- 儲存並讀取靜態 HTML。
- 建立並回傳 HTTP Responses。
- 處理錯誤，例如不存在的路徑。

它的優點是架構簡單、容易理解與部署；缺點是伺服器一旦故障，整個服務就無法使用，而且 CPU、記憶體、網路頻寬與連線數都受限於單一機器。

## Chapter 01 模擬範圍

第一版程式預計模擬：

- DNS 將 `example.com` 解析為固定 IP `15.125.23.214`。
- Browser 建立 `GET /index.html` Request。
- Web Server 解析 Request。
- Web Server 根據路徑讀取靜態 HTML。
- 成功時回傳 `200 OK` 與 HTML。
- 路徑不存在時回傳 `404 Not Found`。
- Browser 顯示 Response 狀態與 HTML。

第一版暫不處理：

- 真實 DNS 網路查詢。
- HTTPS 與 TLS。
- Database。
- Cache。
- Load Balancer。
- 多台 Web Servers。
- CSS、JavaScript 與圖片等額外資源。

核心資料流為：

```text
Domain → DNS → IP → TCP Connection → HTTP Request
       → Web Server → HTTP Response → HTML
```

## 執行最小模擬程式

本章的 [`stage01_single_server.py`](./src/stage01_single_server.py) 使用 Python 標準函式庫模擬完整流程，不需要安裝額外套件。

```powershell
cd "CHAPTER 01：SCALE FROM ZERO TO MILLIONS OF USERS"
python src/stage01_single_server.py
```

程式中的 `15.125.23.214` 是系統架構所假設的公開 IP。因為這個 IP 並未配置在開發電腦上，實際的本機 TCP 連線會映射到 `127.0.0.1:8080`。

程式執行時會依序顯示：

1. DNS 將 `www.mysite.com` 解析為 `15.125.23.214`。
2. Browser 與 Web Server 建立 TCP 連線。
3. Browser 發送 `GET /index.html`。
4. Web Server 回傳 `200 OK` 與 HTML。
5. Browser 顯示收到的狀態和 HTML。

## 執行 Load Balancer 模擬程式

```powershell
python src/stage02_load_balancer.py
```

Stage 02 會啟動三台本機 Web Server 與一個 Load Balancer，連續發出六個 Request。前三次使用 Round Robin 分配至 Server 1、2、3；接著模擬 Server 2 離線，確認後續 Request 只會送往通過 Health Check 的 Server 1 與 Server 3。完整設計與預期輸出請參考 [002 Load Balancer 架構決策](./decisions/002-load-balancer.md)。

## 延伸閱讀

- [術語表](./glossary.md)
- [DNS 筆記](./notes/01-dns.md)
- [TCP 筆記](./notes/02-tcp.md)
- [HTTP 筆記](./notes/03-http.md)
- [Load Balancer 筆記](./notes/04-load-balancer.md)
- [網域註冊與 IP 對應](./questions/01-domain-registration.md)
- [`www` 與 `api` 子網域的用途](./questions/02-www-and-api.md)
- [除了 Round Robin，Load Balancer 如何分配伺服器？](./questions/03-load-balancing-algorithms.md)
- [單一伺服器架構決策](./decisions/001-single-server.md)
- [Load Balancer 架構決策](./decisions/002-load-balancer.md)
