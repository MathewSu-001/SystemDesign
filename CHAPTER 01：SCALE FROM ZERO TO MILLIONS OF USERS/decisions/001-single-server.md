# 001：以單一 Web Server 作為第一個架構

## 狀態

已採用。

## 背景

Chapter 01 的目標是理解使用者從 DNS 取得 IP、建立 TCP 連線、發送 HTTP Request，直到收到 HTML 的基本流程。若一開始加入 Database、Cache、Load Balancer 或多台 Servers，會讓核心資料流變得不易辨識。

## 決策

- 使用單一 Web Server 處理所有請求。
- 使用 `www.mysite.com` 作為模擬網域。
- 使用 `15.125.23.214` 作為假設的公開 IP。
- DNS 由程式內的固定函式模擬，不進行真實 DNS Query。
- 因為公開 IP 未配置在本機，實際 TCP 連線映射至 `127.0.0.1:8080`。
- 使用 HTTP/1.1 傳送 `GET /index.html`。
- 成功時回傳靜態 HTML，找不到路徑時回傳 `404 Not Found`。
- 程式只處理一次請求，以維持範例精簡。

## 影響

這個設計能直接觀察 DNS、TCP、HTTP 和 HTML 的關係，且不需要外部套件或雲端資源。它不是正式 Production Server：沒有 HTTPS、並行請求、完整 HTTP Parser、安全防護、Database、Cache、高可用性或水平擴展能力。
