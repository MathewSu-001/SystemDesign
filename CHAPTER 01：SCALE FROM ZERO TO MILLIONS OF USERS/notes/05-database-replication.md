# Database Replication

## 一句話解釋

Database Replication 是將 Primary 的資料變更複製到一台或多台 Replicas，讓系統擁有額外資料副本並可分散讀取流量。

## 核心概念

- Primary 接受 `INSERT`、`UPDATE`、`DELETE` 等會改變資料的操作。
- Replicas 接收 Primary 的變更，通常用來處理 `SELECT` 等讀取操作。
- 非同步複製會先讓 Primary 回覆寫入成功，再由背景工作更新 Replicas。
- Primary 已更新但 Replica 尚未追上時，兩者之間的差距稱為 Replication Lag。
- 從落後的 Replica 查詢可能暫時找不到新資料，或讀到更新前的舊資料。
- Replicas 最後追上 Primary 的模型稱為最終一致性，不代表每個時間點都完全一致。
- 同步複製可以降低已確認資料遺失的風險，但寫入必須等待其他節點確認，因此延遲較高。
- Primary 故障時，可以將資料較新的 Replica 提升為新 Primary；自動選舉與故障切換不在本階段實作。

## 程式對應位置

- [`DatabaseNode`](../src/stage03_database_replication.py)：以獨立 dictionary 模擬一台 Primary 或 Replica 的資料。
- [`ReplicatedDatabase.write()`](../src/stage03_database_replication.py)：只寫入 Primary，並將變更放入 Replication Queue。
- [`ReplicatedDatabase.read()`](../src/stage03_database_replication.py)：以 Round Robin 從兩台 Replicas 讀取。
- [`ReplicatedDatabase.replicate()`](../src/stage03_database_replication.py)：在背景延遲一秒後，把 Primary 的變更套用至 Replicas。
- [`REPLICATION_DELAY`](../src/stage03_database_replication.py)：刻意建立 Replication Lag，方便觀察舊資料。

