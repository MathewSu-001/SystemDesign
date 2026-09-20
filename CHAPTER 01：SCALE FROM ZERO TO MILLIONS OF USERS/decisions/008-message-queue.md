# 008：加入 Message Queue 與背景 Workers

## 狀態

已採用。

## 問題

Stage 07 的 Web Server 會在 HTTP Request 內完成所有必要工作。若下單後還要寄送 Email、扣除庫存與記錄分析事件，Web Server 必須依序等待這些服務，造成 Response 變慢；任何一個下游服務故障，也可能使原本已成功建立的訂單回覆失敗。

流量突然增加時，同步呼叫還會把尖峰直接傳遞給下游服務。下游服務若每秒只能處理 100 件工作，上游每秒送入 1,000 件工作，就容易逾時或崩潰。

## 決策

在購物系統的下單流程加入 Message Broker：

- Web Server 同步驗證 Request，並把訂單寫入 Database。
- 寫入成功後清除該使用者的 Order Cache。
- Web Server 以 Producer 身分發布 `OrderCreated` Event。
- Email、Inventory 與 Analytics 各自擁有 Queue 和 Consumer。
- Web Server 不等待 Consumers 完成，而是立即回覆 `201 Created`。
- Consumer 成功後 ACK；暫時失敗時由 Broker 重新投遞。
- 超過最大處理次數的訊息移入 Dead Letter Queue（DLQ）。
- Consumer 以 `message_id` 實作冪等性，避免重複投遞造成重複副作用。

## 架構

```text
Client -> Load Balancer -> Web Server (Producer)
                              |-- synchronous --> Order Database
                              |-- invalidate ---> Order Cache
                              `-- publish ------> Message Broker
                                                     |-> Email Queue -> Email Worker
                                                     |-> Inventory Queue -> Inventory Worker
                                                     `-> Analytics Queue -> Analytics Worker
```

Database、Cache 與 Message Queue 不是三選一：

| 元件 | 本階段的用途 | Web Server 是否等待結果 |
| --- | --- | --- |
| Database | 永久保存正式訂單資料 | 是 |
| Cache | 加速讀取訂單資料 | 是 |
| Message Queue | 傳遞後續工作或已發生的事件 | 否 |

Queue 不是訂單的永久資料來源。即使訊息處理完成後被刪除，正式訂單仍保存在 Database。

## 下單流程

```text
1. Client -> POST /orders
2. Web Server -> Database: INSERT order
3. Web Server -> Cache: INVALIDATE user orders
4. Web Server -> Broker: PUBLISH OrderCreated
5. Web Server -> Client: 201 Created

6. Email Worker     <- Email Queue: send confirmation
7. Inventory Worker <- Inventory Queue: reserve stock
8. Analytics Worker <- Analytics Queue: record event
9. Consumers -> Broker: ACK
```

步驟 1 到 5 是同步 Request Path；步驟 6 以後是非同步背景工作。`201 Created` 只表示訂單已建立且事件已發布，不表示所有背景工作都已完成。

## Event 與 Work Queue

`OrderCreated` 是「訂單已建立」的事實，可能有多種功能需要知道，因此 Broker 將同一事件複製到三個訂閱 Queue：

```text
OrderCreated
|-> email queue
|-> inventory queue
`-> analytics queue
```

每個訂閱各自 ACK，Email Worker 完成工作不會替 Inventory Worker 移除訊息。若同一 Queue 有多個相同用途的 Workers，則由其中一個 Worker 處理每則訊息，以便水平擴展。

## At-least-once Delivery

本階段採用 at-least-once delivery。Consumer 可能已完成工作，但在 ACK 送達前故障：

```text
Consumer executes side effect
-> ACK is lost
-> Broker redelivers message
-> Consumer sees the same message again
```

因此 Consumer 保存已完成的 `message_id`。再次收到相同訊息時，不重複執行副作用，直接 ACK。正式系統通常會把冪等紀錄與業務結果放在具一致性保證的儲存層，而不是只存在 Worker 記憶體。

## Retry 與 Dead Letter Queue

Consumer 失敗時不 ACK，Broker 會重新排入相同 Queue：

```text
attempt 1 failed -> retry
attempt 2 failed -> retry
attempt 3 failed -> Dead Letter Queue
```

Retry 適合暫時性錯誤，例如網路逾時。永久錯誤若無限重試，會形成 poison message 並浪費資源，因此到達上限後移入 DLQ，交由監控、人工檢查或修正後重新投遞。

正式系統還應使用 exponential backoff 與 jitter，避免下游服務恢復前被密集 Retry 壓垮。本階段為縮短示範時間，使用立即 Retry。

## 削峰與獨立擴展

Queue 可以吸收短時間流量尖峰：

```text
Producer rate > Consumer rate -> Queue Depth increases
Producer rate < Consumer rate -> Workers drain the backlog
```

這不代表 Queue 擁有無限容量。系統仍需監控 Queue Depth、最老訊息年齡、處理延遲、Retry 次數與 DLQ 數量，並視情況增加 Workers 或限制 Producer 流量。

## 已知的一致性缺口

教學程式依序執行 Database Write 與 Message Publish，兩者不是同一個 Transaction：

```text
Database write succeeds
-> process crashes before publish
-> order exists, but no OrderCreated event
```

正式系統可使用 Transactional Outbox：在同一個 Database Transaction 內寫入訂單與 Outbox Event，再由 Outbox Publisher 可靠地發布至 Broker。本階段先聚焦 Producer、Broker、Consumer、ACK、Retry、DLQ 與冪等性。

## 驗證情境

1. Web Server 1 建立第一筆訂單並發布 `OrderCreated`。
2. Web Server 2 建立第二筆訂單，證明多個 Web Servers 都能成為 Producer。
3. Order Cache 第一次讀取為 MISS，第二次為 HIT。
4. Inventory Worker 第一次處理暫時失敗，重新投遞後成功。
5. Analytics Worker 完成副作用後模擬 ACK 遺失；重新投遞時以 `message_id` 跳過重複副作用。
6. 第二筆訂單使用無效 Email，重試達上限後進入 Email DLQ。

## 啟動程式

```powershell
python src/stage08_message_queue.py
```

程式只使用 Python 標準函式庫。

## 本階段不處理

真實 RabbitMQ、Kafka 或 SQS 連線、訊息持久化、Broker Cluster、Partition、嚴格順序、Schema Registry、延遲 Retry、Consumer Rebalancing、跨區域 Broker Replication、Transactional Outbox 與 exactly-once processing。
