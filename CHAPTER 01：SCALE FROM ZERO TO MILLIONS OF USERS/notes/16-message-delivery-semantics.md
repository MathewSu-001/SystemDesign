# Message Delivery Semantics

## 一句話解釋

Delivery Semantics 描述發生故障時，一則 Message 可能被投遞幾次；常見選擇是 at-most-once、at-least-once 與 exactly-once。

## 核心概念

- At-most-once 是零次或一次，可能遺失，但 Broker 不主動重複投遞。
- At-least-once 是一次或多次，降低遺失風險，但 Consumer 可能收到重複 Message。
- Exactly-once 必須明確限定保證範圍；Broker 只處理一次，不等於外部 Database、Email 或 Payment 副作用也只發生一次。
- Stage 08 採用 at-least-once delivery，Consumer 完成工作後才 ACK。
- At-least-once Consumer 必須把重複 Message 視為正常情況，並以冪等設計避免重複副作用。

## At-most-once

如果 Consumer 在執行工作前就 ACK：

```text
Broker -> Consumer
Consumer -> ACK
Consumer -> execute work
             `-> crash
```

Consumer 故障後 Broker 不再投遞，因此工作可能永遠沒有完成。這種方式適合能接受遺失，而且希望避免重複的情境。

## At-least-once

Consumer 完成工作後才 ACK：

```text
Broker -> Consumer
Consumer -> execute work
Consumer -> ACK
```

但工作完成與 ACK 之間存在故障窗口：

```text
Consumer 完成副作用
-> ACK 傳送前故障，或 ACK 在網路中遺失
-> Broker 認為 Message 尚未完成
-> Broker 重新投遞
```

Broker 無法確定副作用是否已完成，只能重新投遞以降低遺失風險，因此 Consumer 可能再次收到相同 Message。

## Idempotent Consumer

冪等表示同一操作執行多次，有效結果仍與執行一次相同：

```text
收到 message_id=msg-123
-> 是否已成功處理？
   |-> 是：跳過副作用並 ACK
   `-> 否：執行副作用、記錄完成、ACK
```

例如相同的庫存 Message 重送時，不應再次扣除庫存。正式系統可以使用 Message ID、Order ID、Database Unique Constraint 或 Inbox Table 判斷是否已完成。

Stage 08 只將已處理的 Message ID 放在 Consumer 記憶體中，用來展示概念。真實 Worker 重啟後記憶體會消失，因此需要可靠儲存，並盡可能讓業務結果與冪等紀錄位於同一個 Transaction。

## Exactly-once 的範圍

Exactly-once 必須先說明是 Broker 投遞、Consumer 處理、Database 更新，還是外部 API 副作用只發生一次。即使 Broker 對自己的 Log 與 Offset 提供 exactly-once，也不代表 Email Provider 或 Payment API 自動具有相同保證。

實務上經常採用：

```text
At-least-once delivery
+ Idempotent Consumer
+ Unique Constraint / Transaction
= 業務結果只生效一次
```

## Retry 與 Dead Letter Queue

暫時性錯誤可以 Retry，例如網路逾時：

```text
attempt 1 failed -> retry
attempt 2 failed -> retry
attempt 3 succeeded -> ACK
```

正式系統通常使用 Exponential Backoff 與 Jitter，避免大量 Message 同時重試。資料格式錯誤等永久性問題若一直重試只會浪費資源，因此超過上限後移入 DLQ：

```text
Main Queue -> retry -> retry -> Dead Letter Queue
```

DLQ 需要監控與告警，並由系統或人員修正原因後決定是否重新投遞。

## 程式對應位置

- [`MessageBroker.ack()`](../src/stage08_message_queue.py)：記錄處理成功。
- [`MessageBroker.reject()`](../src/stage08_message_queue.py)：重新投遞或移入 DLQ。
- [`Consumer`](../src/stage08_message_queue.py)：工作完成後 ACK，並以 Message ID 避免重複副作用。
- [`AcknowledgementLost`](../src/stage08_message_queue.py)：模擬副作用完成但 ACK 未送達。
- [`main()`](../src/stage08_message_queue.py)：展示 Inventory Retry、Analytics 冪等處理與 Email DLQ。
