# 正常系統只有一台 Primary 嗎？寫入會不會成為瓶頸？

## 問題

資料庫是否通常只有一台 Primary？如果只有一台可以執行 `INSERT`、`UPDATE` 與 `DELETE`，大量寫入時是否會成為瓶頸？

## 短答案

Single-primary 是常見而且相對容易維持一致性的架構，一台 Primary 不代表只能有一台資料庫機器：讀取可以分散到多台 Replicas。當單一 Primary 的寫入能力不足時，可以先改善資料模型、Index、批次寫入與硬體，再依資料範圍進行 Sharding。Multi-primary 允許多個節點接受寫入，但必須額外處理同一份資料的寫入衝突、順序與網路分區。

## Single-primary

```text
Write -> Primary
          ├-> Replica 1
          └-> Replica 2

Read  -> Replica 1 or Replica 2
```

所有資料變更先經過同一個 Primary，因此比較容易決定寫入順序、執行 Transaction，以及避免兩台節點同時修改相同資料。若系統以讀取為主，把讀取送到 Replicas 後，Primary 可能只需承擔少部分流量。

Single-primary 的限制是寫入能力受單一節點約束，而且 Primary 故障時必須進行 Failover。常見改善方式包含批次寫入、減少不必要的 Index、Connection Pool、較快的儲存裝置，以及把非即時工作放入 Message Queue。

## Multi-primary

```text
Client A -> Primary 1
Client B -> Primary 2
```

如果兩台 Primary 同時修改相同資料，系統必須決定哪個版本有效：

```text
Primary 1：profile = Alice
Primary 2：profile = Bob
```

因此 Multi-primary 需要衝突偵測、衝突解決、版本資訊、Quorum 或其他協調機制。它適合特定的跨區域或高寫入需求，但不能視為增加一台 Primary 就能直接取得兩倍寫入能力。

## Sharding

大型系統也可以讓不同 Primary 負責不同資料：

```text
User 1-1,000,000         -> Shard A Primary
User 1,000,001-2,000,000 -> Shard B Primary
```

整個系統存在多台 Primary，但每一筆資料通常仍有明確的負責節點。這能分散寫入，同時降低同一份資料在多個 Primary 間發生衝突的機會。

## Stage 03 的選擇

Stage 03 使用 Single-primary，因為本階段要先理解讀寫分離、Replication Lag 與最終一致性。Multi-primary、衝突解決和 Sharding 留待後續階段處理。

