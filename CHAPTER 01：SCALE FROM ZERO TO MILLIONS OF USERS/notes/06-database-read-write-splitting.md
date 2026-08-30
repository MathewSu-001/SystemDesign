# Database Read/Write Splitting

## 一句話解釋

Database Read/Write Splitting 是將讀取送往 Replicas、將會改變資料的操作送往 Primary，以降低 Primary 的讀取負載。

## 核心概念

- `SELECT` 通常可以送往 Replica；`INSERT`、`UPDATE`、`DELETE` 必須送往 Primary。
- HTTP Method 不必然等同 Database Operation；Stage 03 使用 `GET`、`POST`、`PUT` 判斷路由只是教學簡化。
- Replica 的選擇可以考慮 Round Robin、連線數、節點健康狀態、網路距離與 Replication Lag。
- Load Balancer 負責選擇 Web Server，Web Server 或 Database Proxy 才負責選擇 Primary 或 Replica。
- 剛完成寫入後立即讀取 Replica，可能違反 Read-after-write Consistency。
- 需要立即讀到自己更新的資料時，可以暫時讀取 Primary，或只選擇已追上特定複製位置的 Replica。
- Transaction 中的多個查詢通常固定使用同一個 Primary Connection，避免不同節點的資料版本不一致。
- 讀寫分離能擴充讀取能力，但不能直接解決 Primary 的大量寫入瓶頸。

## 程式對應位置

- [`run_web_server()`](../src/stage03_database_replication.py)：將 `POST`、`PUT` 送往 Primary，將 `GET` 送往 Replica。
- [`ReplicatedDatabase.read()`](../src/stage03_database_replication.py)：輪流選擇 Replica 1 與 Replica 2。
- [`run_load_balancer()`](../src/stage03_database_replication.py)：只分配 Web Server，不參與 Database 讀寫路由。
- [`X-Database-Node`](../src/stage03_database_replication.py)：在 Response 中標示實際處理操作的資料庫節點。

