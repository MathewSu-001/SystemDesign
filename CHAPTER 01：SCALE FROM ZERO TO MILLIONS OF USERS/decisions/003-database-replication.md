# 003：加入 Database Replication 與讀寫分離

## 狀態

已採用。

## 問題

Stage 02 擴充了 Web 層，但若資料層只有一台 Database，所有讀寫仍集中在同一節點。查詢量增加時，Database 會成為新的效能瓶頸。

## 改動

- 保留 DNS、Load Balancer 與三台 Web Server。
- 加入一台 Database Primary，唯一接受寫入。
- 加入兩台 Database Replica，輪流承擔讀取。
- Primary 的變更經由背景 Queue 延遲一秒複製至所有 Replicas。

## Request 流程

```text
寫入：Browser -> Load Balancer -> Web Server -> Database Primary
                                                   |
                                                   +-> async replication
                                                              -> Replica 1
                                                              -> Replica 2

讀取：Browser -> Load Balancer -> Web Server -> Database Replica 1 or 2
```

Load Balancer 只選擇 Web Server。Web Server 再依 HTTP method 決定資料庫路徑：

- `POST` / `PUT` → Primary
- `GET` → Replica

## 本機模擬位址

| 元件 | 架構位址 | 本機模擬 |
| --- | --- | --- |
| Load Balancer | `15.125.23.214:80` | `127.0.0.1:8080` |
| Web Server 1 | `10.0.1.11:80` | `127.0.0.1:9001` |
| Web Server 2 | `10.0.1.12:80` | `127.0.0.1:9002` |
| Web Server 3 | `10.0.1.13:80` | `127.0.0.1:9003` |
| Database Primary | `10.0.2.10` | 程式內記憶體節點 |
| Database Replica 1 | `10.0.2.11` | 程式內記憶體節點 |
| Database Replica 2 | `10.0.2.12` | 程式內記憶體節點 |

Database 使用 dictionary 模擬。本階段重點是讀寫路由與 replication lag，而不是特定資料庫產品。

## 啟動程式

```powershell
python src/stage03_database_replication.py
```

程式只使用 Python 標準函式庫。

## 驗證順序

1. `POST Alice v1` 寫入 Primary。
2. 立即 `GET`：Replica 尚未同步，回傳 `profile not found`。
3. 等待後 `GET`：Replica 回傳 `Alice v1`。
4. `PUT Alice v2` 更新 Primary。
5. 立即 `GET`：Replica 仍回傳舊值 `Alice v1`。
6. 等待後 `GET`：Replica 回傳新值 `Alice v2`。

Response 中的 `X-Served-By` 與 `X-Database-Node` 會顯示實際處理請求的 Web Server 和 Database Node。

## 本階段不處理

Primary 自動故障轉移、強一致性交易、分片、Cache、CDN，以及 Load Balancer 本身的高可用性。
