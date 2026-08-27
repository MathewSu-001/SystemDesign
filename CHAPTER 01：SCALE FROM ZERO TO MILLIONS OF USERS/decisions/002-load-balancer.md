# 002：加入 Load Balancer 與多台 Web Server

## 狀態

已採用。

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

## 本機模擬位址

架構 IP 無法直接綁定在一般本機環境，所以使用不同的 localhost Port 模擬：

| 元件 | 架構位址 | 本機模擬位址 |
| --- | --- | --- |
| Load Balancer | `15.125.23.214:80` | `127.0.0.1:8080` |
| Web Server 1 | `10.0.1.11:80` | `127.0.0.1:9001` |
| Web Server 2 | `10.0.1.12:80` | `127.0.0.1:9002` |
| Web Server 3 | `10.0.1.13:80` | `127.0.0.1:9003` |

公開 IP 與私有 IP 不會合併。Browser 與 Load Balancer 建立第一條 TCP 連線，Load Balancer 再與選中的 Web Server 建立第二條 TCP 連線。

## 啟動程式

```powershell
python src/stage02_load_balancer.py
```

程式只使用 Python 標準函式庫，不需要安裝額外套件。

## 驗證

程式會發出六個 Request。前三個 Request 應依序分配給 Server 1、2、3；接著 Server 2 被模擬為離線，後三個 Request 只會在 Server 1 與 Server 3 之間分配：

```text
Request 1 -> Web Server 1
Request 2 -> Web Server 2
Request 3 -> Web Server 3
Web Server 2 offline
Request 4 -> Web Server 1
Request 5 -> Web Server 3
Request 6 -> Web Server 1
```

每次分配前，Load Balancer 都會呼叫各 Server 的 `/health`，只把 Request 送給回傳 `200 OK` 的節點。Response 的 `X-Served-By` Header 會讓 Browser 顯示實際處理 Request 的 Server。

## 本階段不處理

Database、Database replication、Cache、CDN，以及 Load Balancer 本身的高可用性。
