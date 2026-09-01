# Cache TTL 是什麼？應該設定多久？

## 問題

TTL 如何控制 Cache Entry 的存活時間？TTL 應該設定得長還是短，能否依靠 TTL 保證資料一致？

## 短答案

TTL 是 Time To Live，表示 Cache Entry 在自動過期前可以存活多久。短 TTL 讓資料較快刷新，但會增加 Cache Miss 與 Database 負載；長 TTL 能提高 Hit Rate，卻可能讓舊資料保留更久。TTL 是避免舊資料永久存在的安全網，不等於一致性保證，也不能完全取代 Cache Invalidation。

## 過期流程

例如設定：

```text
10:00:00 SET profile:123 = Alice, TTL 60 seconds
10:00:30 GET -> HIT
10:01:00 Entry 到期
10:01:01 GET -> MISS -> Database -> SET 新 Entry
```

Cache 實作不一定在 TTL 歸零的瞬間立即從記憶體移除 Entry。有些系統會在讀取時發現過期並刪除，也可能在背景定期清理。對 Application 而言，已過期的 Entry 都必須視為不存在。

## 長短取捨

```text
較短 TTL
-> 資料較快刷新
-> Cache Miss 較多
-> Database 負載較高

較長 TTL
-> Cache Hit Rate 較高
-> Database 負載較低
-> 舊資料可能保留較久
```

TTL 應依資料特性決定。例如很少變動的公開設定可以保存較久；庫存、價格或權限等對正確性敏感的資料，則需要較短 TTL、更可靠的 Invalidation，甚至不應以 Cache 作為最終判斷來源。

## TTL 與 Invalidation

Database 更新時主動刪除 Cache，可以讓下一次讀取較快取得新資料。TTL 則處理 Invalidation 遺漏或失敗時，舊 Entry 不會永久存在。

```text
主要機制：Database 更新 -> Cache DELETE
保護機制：Cache Entry -> TTL 到期
```

即使設定 TTL，在到期前仍可能讀到舊資料，因此 TTL 不能保證 Read-after-write Consistency。

## Stage 04 的選擇

Stage 04 將 TTL 設為兩秒，只是為了在短時間內展示：

```text
Cache HIT old value
-> TTL EXPIRED
-> Cache MISS
-> Replica latest value
-> Cache SET latest value
```

這是教學時間，不代表正式系統都應使用兩秒 TTL。

