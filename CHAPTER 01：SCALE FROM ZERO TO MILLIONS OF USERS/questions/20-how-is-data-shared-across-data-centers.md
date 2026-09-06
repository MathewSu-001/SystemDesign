# 多個 Data Centers 如何共享 Session、Cache 與 Database？

## 問題

Stage 07 的 Taipei 與 Virginia Web Servers 都能使用相同 Session Store、Application Cache 與 Database。真實系統也會讓所有 Data Centers 直接連線到同一套資料服務嗎？

## 短答案

不一定。Stage 07 的 Global Shared Store 是教學簡化，用來先觀察 Data Center Routing 與 DNS Failover。真實系統可能使用單一資料主區域、跨區域 Replication、每區獨立 Cache、Session Replication 或 Multi-Primary Database；每種選擇都需要在延遲、可用性、一致性與複雜度之間取捨。

## 單一資料主區域

```text
Taipei Web Servers ----+
                       +-> Virginia Database Primary
Virginia Web Servers --+
```

優點：

- 寫入順序與一致性較容易管理。
- 不需要處理多個 Primary 的寫入衝突。

缺點：

- Taipei 的每次資料存取可能跨區域。
- 網路延遲較高。
- Data Center 間網路中斷時，Taipei Application 可能無法存取資料。
- 資料主區域可能成為故障風險。

## 跨區域 Replication

```text
Taipei Database Replica <---- Replication ---- Virginia Primary
```

每個 Data Center 可以就近讀取 Replica，但寫入仍送往 Primary。需要處理：

- Replication Lag。
- Stale Read。
- Read-after-write Consistency。
- Primary Region 故障時的 Promotion。
- Failover 過程中的資料遺失範圍。

## 每個 Data Center 使用自己的 Cache

```text
Taipei Web Servers   -> Taipei Cache
Virginia Web Servers -> Virginia Cache
```

Cache 通常可以每區獨立，因為 Cache Miss 還能回到 Database；但來源資料更新後，必須考慮各區 Cache Invalidation、TTL 與 Stale Data。

讓所有 Data Centers 共用單一遠端 Cache，可能讓 Cache 查詢本身承受跨區域延遲，失去使用 Cache 降低延遲的部分價值。

## Session 的選擇

Session 可以採用：

- 集中 Session Store：容易理解，但遠端 Data Center 查詢延遲較高。
- 每區 Session Store 加 Replication：Failover 時可能遇到 Replication Lag。
- 使用者切換 Data Center 後重新登入：簡單但體驗較差。
- 將部分驗證狀態放入簽章 Token：減少 Store 查詢，但撤銷、更新與 Token 洩漏需要不同設計。

不論採用哪種方式，都不應讓 Session 只存在某台 Web Server 的本機記憶體，否則無法維持 Stateless Web Tier。

## Multi-Primary Database

多個 Data Centers 都接受寫入可以降低遠端寫入延遲：

```text
Taipei Primary   <----> Virginia Primary
```

但相同資料在兩區同時修改時，需要處理 Conflict Resolution、全域唯一 ID、交易限制與一致性模型。Multi-Primary 不是只增加一台 Primary 就能完成。

## 主要取捨

| 問題 | 需要考慮的選擇 |
| --- | --- |
| Latency | 資料是否存在 Client 所在區域 |
| Availability | 某個 Region 或跨區網路故障後是否仍可服務 |
| Consistency | Replicas 是否允許短暫不一致 |
| Conflict | 多區同時寫入如何合併 |
| Capacity | Failover Data Center 是否能承接額外流量 |
| Data Residency | 資料是否允許離開指定地理區域 |

## Stage 07 的選擇

Stage 07 讓兩個 Data Centers 共用 Python Process 內的 Session Store、Application Cache 與 Replicated Database，因此 Failover 至 Virginia 後仍能讀取 Asia Browser 的 Session。

這不代表正式系統應直接部署一套全球共用的 in-memory dictionary。跨資料中心資料放置與同步是獨立且更大的主題，本階段刻意不與 GeoDNS 一起實作。

