# Session Store、Database 與 Cache 是同一個東西嗎？

## 問題

Session Store 是否就是前面使用的 Primary／Replica Database，只是保存不同資料？它和 Shared Application Cache 又有什麼差別？

## 短答案

Session 可以保存在既有 Database，但 Session Store 不必等於業務 Database。Session Store 描述「保存登入 Session」的用途；Primary／Replica 描述資料如何寫入與複寫。Session Store 本身也可以使用 Primary、Replicas 或 Cluster。流量增加後，Session 常放在支援低延遲 Key-Value 查詢與 TTL 的獨立系統，例如 Redis。

## 使用同一個 Database

小型系統可以在既有 Database 建立 Sessions Table：

```text
sessions
------------------------------------------------
session_id | user_id | created_at | expires_at
```

優點：

- 不需要維護新的資料系統。
- 可以沿用既有備份、權限與複寫機制。
- 適合初期流量或較低的 Session 讀寫量。

缺點：

- 幾乎每個登入 Request 都可能增加 Database 查詢。
- Session 通常數量多、生命週期短且讀寫頻繁。
- 過期資料清理會增加 Database 工作。
- Session 負載可能和訂單、帳戶等正式業務查詢競爭資源。

## 使用獨立 Session Store

較大的系統可能拆分為：

```text
Web Servers
├-> Shared Session Store
├-> Shared Application Cache
└-> Primary / Replica Database
```

Session Store 常需要：

- 以 Session ID 進行快速 Key-Value 查詢。
- 高頻率讀寫。
- 自動 TTL。
- 支援 Replication、Failover 或 Sharding。

Redis 是常見選擇，但不是唯一選擇；Database、Distributed Cache 或其他 Key-Value Store 也可以扮演 Session Store。

## 三種元件的責任

| 元件 | 保存內容 | 是否正式資料 | Miss／遺失後的結果 |
| --- | --- | --- | --- |
| Shared Session Store | 登入身分與少量短期狀態 | 通常不是長期業務紀錄 | 使用者可能需要重新登入 |
| Shared Application Cache | Database 查詢結果的副本 | 否 | 回到 Database 查詢 |
| Primary／Replica Database | Profile、訂單等長期資料 | 是 | 可能造成正式資料不可用或遺失 |

Session Store 和 Application Cache 都可能使用 Redis，但用途與資料遺失後的影響不同。產品相同不代表架構角色相同。

## Primary／Replica 描述的是拓樸

以下兩套系統都可以有 Primary 與 Replica：

```text
Business Database
├-> Primary
└-> Replicas

Session Store
├-> Primary
└-> Replicas
```

因此「Session Store」與「Primary／Replica」不是互斥選項：前者描述保存什麼以及為何保存，後者描述節點之間如何寫入、複寫與故障轉移。

## Stage 06 的選擇

Stage 06 使用 Thread-safe dictionary 模擬獨立 Shared Session Store，沒有將 Session 寫入 Stage 03 的 Replicated Database。這是為了讓 Session Store 與長期業務資料的責任容易觀察，並不表示正式系統一定要使用兩種不同產品。

