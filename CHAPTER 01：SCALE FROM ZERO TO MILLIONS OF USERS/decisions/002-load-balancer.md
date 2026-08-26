# 002：加入 Load Balancer 與多台 Web Server

## 狀態

規劃中。

## 問題

Stage 01 只有一台 Web Server。所有流量都集中在同一台機器，而且該機器離線時，整個服務便無法使用。

## 改動

- DNS 改為回傳 Load Balancer 的公開 IP。
- 在 Load Balancer 後方加入多台 Web Server。
- Web Server 使用只有內部網路可以存取的 IP。
- Load Balancer 使用 Round Robin 將請求送往健康的 Web Server。
- Load Balancer 透過 Health Check 排除離線的 Web Server。

## Request 流程

```text
Browser
  -> DNS
  -> Load Balancer (public IP)
  -> Web Server 1, 2, or 3 (private IP)
  -> Load Balancer
  -> Browser
```

## 預定驗證

1. 連續發出多個請求，確認不同 Web Server 輪流處理。
2. 將一台 Web Server 標示為離線。
3. 再次發送請求，確認 Load Balancer 只選擇健康的 Server。

## 本階段不處理

Database、Database replication、Cache、CDN，以及 Load Balancer 本身的高可用性。
