# 003：加入 Database Replication 與讀寫分離

## 狀態

規劃中。

## 問題

Stage 02 擴充了 Web 層，但資料尚未持久化。若所有讀寫都集中至單一 Database，Database 會成為新的效能瓶頸與單點故障。

## 改動

- 保留 Load Balancer 與多台 Web Server。
- 加入一台 Database Primary，負責接受寫入。
- 加入多台 Database Replicas，負責讀取。
- Primary 將資料異步複製至 Replicas。

## Request 流程

```text
Read:  Browser -> Load Balancer -> Web Server -> Database Replica
Write: Browser -> Load Balancer -> Web Server -> Database Primary
                                             -> Replication -> Replicas
```

## 預定驗證

1. 確認讀取請求會送往 Replica。
2. 確認寫入請求只會送往 Primary。
3. 確認 Primary 的更新稍後會出現在 Replicas。
4. 觀察 replication lag 造成的短暫舊資料。

## 本階段不處理

Primary 自動故障轉移、強一致性交易、分片、Cache 與 CDN。
