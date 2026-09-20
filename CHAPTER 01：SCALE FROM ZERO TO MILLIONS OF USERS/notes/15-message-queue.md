# Message Queue

## 一句話解釋

Message Queue 讓 Producer 將工作或事件交給 Broker 暫存，再由 Consumer 非同步處理，使 Web Server 不必在 HTTP Request 內等待所有後續工作完成。

## 核心概念

- Producer 建立並發布 Message；Stage 08 中是 Web Server。
- Broker 接收、保存與投遞 Message；Queue 是 Broker 內保存待處理 Message 的邏輯容器。
- Consumer 從 Queue 取得 Message 並執行工作，也常稱為 Worker。
- Consumer 成功後回傳 ACK，Broker 才將 Message 標記為完成。
- Consumer 暫時失敗時可以 Retry；超過重試上限的 Message 進入 Dead Letter Queue。
- Producer 與 Consumer 不必同時在線，也不必知道彼此部署在哪台 Server。
- Queue 可以吸收短時間流量尖峰，但不是無限容量。
- Message Queue 不取代 Database。Message 處理完成後可能被移除，正式訂單仍應保存在 Database。

## 購物下單流程

```text
Client -> Web Server
             |-> Database：INSERT order
             |-> Cache：INVALIDATE user orders
             `-> Broker：PUBLISH OrderCreated
                              |-> Email Queue -> Email Worker
                              |-> Inventory Queue -> Inventory Worker
                              `-> Analytics Queue -> Analytics Worker

Client <- 201 Created
```

Database 寫入是建立訂單成功的必要條件，因此 Web Server 必須等待。寄信與分析不必阻塞 HTTP Response，可以交給 Consumer 在背景處理。

`201 Created` 表示訂單已建立且 Message 已發布，不表示所有 Consumers 都已完成工作。

## 同步與非同步

同步操作位於 Request Path：

```text
Web Server -> Database / Cache
Web Server <- required result
Client     <- HTTP Response
```

非同步操作離開 Request Path：

```text
Web Server -> Broker：publish
Client     <- HTTP Response

稍後：Broker -> Consumer -> execute work -> ACK
```

判斷重點不是工作執行得快不快，而是本次 HTTP Response 是否必須取得結果，以及系統能否接受稍後完成。登入驗證必須立即知道結果；寄送訂單確認信通常可以非同步執行。

## Event 與 Work Queue

`OrderCreated` 表示「訂單已建立」的 Event。不同功能都需要知道時，Broker 將它送到各自的 Subscription：

```text
OrderCreated
|-> Email Subscription
|-> Inventory Subscription
`-> Analytics Subscription
```

每個 Subscription 分別 ACK。Email Worker 完成工作，不表示 Inventory Worker 也已完成。

同一種工作需要更高處理能力時，可以讓多個 Workers 競爭消費同一 Queue：

```text
Email Queue
|-> Email Worker 1
|-> Email Worker 2
`-> Email Worker 3
```

每則 Email Message 只交給其中一個 Worker，藉此水平擴展處理能力。

## 優點與代價

Message Queue 可以降低 Request Latency、隔離下游故障、吸收流量尖峰，並讓 Web Servers 與 Workers 分別擴展。

它也會增加系統複雜度：Message 可能延遲、重複或順序改變；系統必須設計 ACK、Retry、DLQ、冪等性與監控。若 Client 必須立即取得結果，通常仍適合同步處理。

## 程式對應位置

- [`Message`](../src/stage08_message_queue.py)：保存 Message ID、Event Type 與 Payload。
- [`MessageBroker`](../src/stage08_message_queue.py)：發布、ACK、Retry 與 DLQ。
- [`Subscription`](../src/stage08_message_queue.py)：Email、Inventory 與 Analytics 各自的 Queue。
- [`Consumer`](../src/stage08_message_queue.py)：取得 Message、執行 Handler 並 ACK。
- [`CheckoutService.create_order()`](../src/stage08_message_queue.py)：寫入 Database 後發布 `OrderCreated`。
- [`CheckoutService.get_orders()`](../src/stage08_message_queue.py)：訂單查詢仍使用 Cache／Database，而不是 Queue。
