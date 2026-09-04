# Session 應該保存什麼，容量會不會用完？

## 問題

Session 是否用來記住使用者之前看到的畫面？如果每位使用者都有 Session，Session Store 會不會因資料太多而爆掉？

## 短答案

Session 通常記住使用者身分與少量、短期、跨 Request 所需的狀態，而不是完整瀏覽畫面。Session Store 的容量確實可能用完，因此需要限制每筆 Session 大小、設定 TTL、清除過期資料、監控容量，並在需要時進行 Replication 或 Sharding。

## Session 不等於完整畫面

Session 可以記錄少量流程資訊：

```text
session abc123 -> {
    user_id: 42,
    checkout_step: 2,
    expires_at: ...
}
```

Web Server 再根據這些識別資訊取得正式資料並產生畫面：

```text
Cookie session_id
-> Session Store 取得 user_id=42
-> Database 取得 Profile、Orders
-> Web Server 產生 HTTP Response
-> Browser 顯示畫面
```

如果前端是 Single-Page Application，部分畫面狀態也可能只存在 Browser 記憶體、URL 或 Local Storage，不必全部送到 Server-side Session。

## 適合保存的資料

- `user_id`。
- Session 建立時間與到期時間。
- 少量角色或權限版本資訊。
- CSRF Token。
- OAuth 登入流程的暫時 State。
- 少量結帳步驟或多頁表單進度。
- 少量語系或顯示偏好。

## 不適合保存的資料

- 完整 HTML 畫面。
- 完整 Profile 與大量訂單。
- 圖片、影片與文件 Bytes。
- 大型商品目錄或聊天紀錄。
- 可以用 ID 從 Database 查詢的所有資料副本。
- 密碼、信用卡號等敏感資料。
- 必須長期保存與稽核的正式業務紀錄。

原則是 Session 保存「這是誰，以及目前少量短期狀態」，Database 保存「這位使用者的正式業務資料」。

## 容量估算

簡化估算：

```text
平均 Session 大小 × 同時有效 Session 數量 × 副本數
```

例如每筆 Session 原始資料平均 1 KB，共有 1,000,000 筆有效 Session，單一副本的原始資料約為 1 GB。實際記憶體還要計算：

- Session Key。
- 資料結構額外成本。
- TTL Metadata。
- 記憶體碎片。
- Replicas。
- 系統保留空間。

所以實際需求通常高於原始 Payload 大小。

## 避免 Session 無限增長

### 設定 TTL

```text
session abc123 -> TTL 30 minutes
```

使用者直接關閉 Browser 時通常不會送出 `/logout`，因此不能只依賴登出刪除，Session Store 必須能清除過期資料。

### 保持 Session 小型

推薦：

```text
session_id -> user_id + expires_at
```

避免：

```text
session_id -> 完整 Profile + 全部 Orders + 圖片 + 完整頁面
```

### 限制每位使用者的 Session 數量

例如每位使用者最多保留五個有效登入裝置；建立第六個 Session 時撤銷最舊的 Session。

### 監控與擴展

應監控：

- 有效 Session 數量。
- 平均及最大 Session 大小。
- 記憶體使用率。
- Session Hit／Miss Rate。
- Expiration 與 Eviction 數量。
- 查詢延遲與錯誤率。

單一 Session Store 不足時，可以加入 Replicas 提高可用性，或根據 Session ID 進行 Sharding：

```text
hash(session_id) -> Session Store Shard 1、2 或 3
```

## Stage 06 的選擇

Stage 06 每筆 Session 只保存 `user_id` 與 `expires_at`，並設定 30 秒教學用 TTL。Cookie 只保存隨機 Session ID，因此不會在每個 HTTP Request 傳送完整使用者資料。

