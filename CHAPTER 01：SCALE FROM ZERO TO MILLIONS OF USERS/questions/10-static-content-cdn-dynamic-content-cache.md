# 靜態內容走 CDN、動態資料走 Shared Cache，這個理解正確嗎？

## 問題

如果 Browser 需要靜態內容，就會從地理位置最近的 CDN 取得；如果需要動態資料，就會透過 Shared Cache 取得。這個理解是否正確？

## 短答案

大致正確，但 Browser 不會直接使用 Shared Cache。靜態內容通常先向 CDN Edge 請求，Hit 時直接回傳，Miss 時才向 Origin 取得。動態 Request 通常經過 CDN Bypass 進入 Web Server，再由 Web Server 決定查 Shared Cache、Database 或其他服務。Shared Cache 是動態資料可能經過的一層，不是所有動態資料的固定來源。

## 靜態內容流程

```text
Browser
-> CDN Edge
   ├-> HIT  -> Browser
   └-> MISS -> Origin -> CDN -> Browser
```

Browser 只對 URL 發送 HTTP Request，不需要知道 Edge Cache 中是否已有內容。CDN 會依 DNS、Anycast 或供應商的流量調度，將 Request 導向網路路徑合適且可用的 Edge。地理距離通常是考量之一，但網路延遲、ISP 路由、負載與健康狀態也會影響選擇。

## 動態內容流程

```text
Browser
-> CDN BYPASS
-> Load Balancer
-> Web Server
   ├-> Shared Cache HIT
   ├-> Shared Cache MISS -> Database
   └-> Other Service
```

Redis 或 Memcached 通常存在 Private Network，由 Web Server 存取，不會直接暴露給 Browser。Web Server 也可能因一致性需求直接讀 Primary，或呼叫其他服務，而完全不使用 Shared Cache。

例如建立訂單通常是寫入操作：

```text
POST /orders
-> Web Server
-> Database Primary
```

它不會因為是動態資料，就一定先查 Shared Cache。

## 兩種 Cache 的位置

```text
Browser
-> CDN Cache
-> Origin Web Server
-> Shared Application Cache
-> Database
```

CDN 快取靠近 Client 的 HTTP Response；Shared Cache 快取 Web Server 執行 Application Logic 時使用的資料或查詢結果。

## Stage 05 的選擇

Stage 05 將 `GET /static/*` 視為 CDN Cacheable，將 `/profile` 視為 CDN Bypass。Web Server 處理 `/profile` 時，仍保留 Stage 04 的 Shared Application Cache。

