# 004：加入 Shared Cache

## 狀態

已採用。

## 問題

Stage 03 使用 Database Replicas 分散讀取，但每次 `GET` 仍會查詢 Database。熱門資料被反覆讀取時，會產生重複查詢與額外延遲。

## 改動

- 保留 DNS、Load Balancer、三台 Web Servers、Database Primary 與兩台 Replicas。
- 加入所有 Web Servers 共用的 Shared Cache。
- 讀取採用 Cache-Aside：先查 Cache，Miss 時才查 Replica 並回填 Cache。
- 寫入先更新 Primary，成功後刪除對應的 Cache Key。
- Cache Entry 設定兩秒 TTL，避免舊資料永久留在 Cache。

## Request 流程

```text
Read:
Browser -> Load Balancer -> Web Server -> Shared Cache
                                      ├-> HIT  -> Response
                                      └-> MISS -> Database Replica
                                                   -> Cache SET
                                                   -> Response

Write:
Browser -> Load Balancer -> Web Server -> Database Primary
                                      -> Cache DELETE
                                      -> Response
```

## Cache-Aside

Application 負責管理 Cache：

1. `GET` 先讀取 Cache。
2. Cache Hit 時直接回傳。
3. Cache Miss 時讀取 Database Replica。
4. Database 有資料時將結果放入 Cache。
5. `POST` 或 `PUT` 成功寫入 Primary 後刪除 Cache Key。

本階段使用 Python dictionary 模擬 Shared Cache。實際系統可使用 Redis 或 Memcached 等獨立服務。

## 驗證順序

1. `POST Alice v1` 寫入 Primary，等待 Replicas 同步。
2. 第一次 `GET` 發生 Cache Miss，從 Replica 取得 `Alice v1` 並寫入 Cache。
3. 第二、三次 `GET` 由不同 Web Servers 命中相同 Shared Cache。
4. `PUT Alice v2` 更新 Primary 並刪除 Cache。
5. 立即 `GET` 發生 Miss；落後的 Replica 回傳 `Alice v1`，舊值被放回 Cache。
6. Replicas 追上後再次 `GET`，仍命中 Cache 中的舊值。
7. TTL 到期後 `GET`，重新從 Replica 取得 `Alice v2` 並更新 Cache。

這個流程刻意展示 Cache 可能延長 Replication Lag 的影響。TTL 限制舊資料存活時間，但不保證 Read-after-write Consistency。

## Response Headers

- `X-Served-By`：處理 Request 的 Web Server。
- `X-Cache`：`HIT`、`MISS`、`INVALIDATED` 或 `BYPASS`。
- `X-Data-Source`：Shared Cache、Database Primary 或實際 Replica。

## 啟動程式

```powershell
python src/stage04_cache.py
```

程式只使用 Python 標準函式庫。

## 本階段不處理

真實 Redis/Memcached 連線、Cache Cluster、Cache Failover、容量淘汰策略、Cache Stampede、Cache Penetration、Cache Avalanche、Distributed Lock、Write-through、Write-behind 與多層 Cache。

