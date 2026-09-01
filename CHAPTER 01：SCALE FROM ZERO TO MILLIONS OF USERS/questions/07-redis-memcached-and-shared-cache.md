# Redis、Memcached 與 Shared Cache 是什麼？

## 問題

Redis 和 Memcached 是什麼？實際系統是否也會讓多台 Web Servers 使用同一個 Shared Cache？

## 短答案

Redis 與 Memcached 都能作為獨立於 Web Server 的記憶體型 Shared Cache。多台 Web Servers 共用 Cache 是常見架構，因為任一 Web Server 建立的 Cache 都能被其他節點使用；實際系統也可能同時使用 Web Server Local Cache、Shared Cache、CDN 與 Browser Cache，形成多層快取。

## Redis

Redis 是記憶體型 Data Store，除了基本 Key-Value，還提供 Hash、List、Set、Sorted Set 等資料結構，也能設定 TTL。它除了作為 Cache，也常用於 Session、Counter、Rate Limiting 或其他需要快速存取的資料。

例如可以將使用者資料序列化後保存：

```text
Key:   profile:123
Value: {"name":"Alice"}
TTL:   300 seconds
```

Redis 可以提供持久化、Replication 與 Cluster 等能力，但使用哪些能力取決於部署設定。Cache 中的資料是否能在故障後恢復，也不能只因為使用 Redis 就自動假設。

## Memcached

Memcached 是較單純的分散式記憶體 Cache，主要使用 Key 取得一段 Value，適合暫存可以重新計算或重新查詢的資料。它的功能通常比 Redis 精簡，重點是快速、簡單的物件快取。

```text
profile:123 -> serialized profile data
```

## Local Cache 與 Shared Cache

Local Cache 存在單一 Web Server Process：

```text
Web Server 1 -> Local Cache 1
Web Server 2 -> Local Cache 2
Web Server 3 -> Local Cache 3
```

它不需要額外網路請求，但每台 Server 的內容可能不同，Invalidation 也必須傳到所有節點。

Shared Cache 則由多台 Web Servers 共用：

```text
Web Server 1 --┐
Web Server 2 --+-> Shared Redis or Memcached
Web Server 3 --┘
```

Request 即使經由 Load Balancer 分配到不同 Web Server，仍能使用同一份 Cache。代價是每次存取需要網路通訊，而且 Shared Cache 本身也需要容量管理、監控與高可用性設計。

## 多層 Cache

實際系統可以同時使用多層 Cache：

```text
Browser Cache
-> CDN
-> Web Server Local Cache
-> Shared Cache
-> Database
```

越靠近 Client 的 Cache 通常延遲越低，但資料同步與 Invalidation 會更加複雜。因此不是 Cache 層數越多越好，而是依資料更新頻率、延遲目標與一致性需求選擇。

## Stage 04 的選擇

Stage 04 使用一個 Thread-safe Python dictionary 模擬 Shared Cache，不需要安裝 Redis 或 Memcached。這個階段的重點是先理解 Cache-Aside、Hit、Miss、Invalidation 與 TTL。

