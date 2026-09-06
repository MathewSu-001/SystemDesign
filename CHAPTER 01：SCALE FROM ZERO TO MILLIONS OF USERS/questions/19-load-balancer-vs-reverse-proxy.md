# Load Balancer 和 Reverse Proxy 有什麼關係？

## 問題

如果 Load Balancer 是具有負載分配功能的 Reverse Proxy，為什麼系統還需要 Reverse Proxy？兩者一定是不同元件嗎？

## 短答案

不一定需要兩個元件。Reverse Proxy 描述「代表後方服務接收並轉送 Client 流量」的代理模式；Load Balancer 強調「將流量分配給多個目標」的功能。同一個 Layer 7 元件經常同時扮演 Reverse Proxy 與 Load Balancer。

## Reverse Proxy

```text
Client -> Reverse Proxy -> Backend Server
```

即使只有一台 Backend，Reverse Proxy 仍可能負責：

- TLS Termination。
- 隱藏 Backend 位址。
- Host／Path Routing。
- Authentication。
- Header 修改。
- Compression。
- Cache。
- Rate Limiting。
- WAF 或其他安全檢查。

所以 Reverse Proxy 不必然進行負載平衡。

## Load Balancer

```text
Client -> Load Balancer
              ├-> Backend 1
              ├-> Backend 2
              └-> Backend 3
```

Load Balancer 主要關心：

- Backend Health Check。
- Round Robin 或其他分配演算法。
- Backend Capacity。
- 故障節點移除。
- Connection 或 Request Distribution。

如果 Load Balancer 接收並重新轉送 HTTP Request，它也具有 Reverse Proxy 行為。

## 同一元件扮演兩種角色

Stage 02 的 Load Balancer：

1. 接收 Browser HTTP Request。
2. 以 Round Robin 選擇健康 Web Server。
3. 將 Request 轉送給該 Web Server。
4. 接收 Web Server Response。
5. 將 Response 傳回 Browser。

因此它同時是：

```text
Reverse Proxy + Load Balancer
```

本章不需要在 Load Balancer 前再加入一個功能重複的 Reverse Proxy。

## Layer 4 的例外

不是所有 Load Balancers 都是 HTTP Reverse Proxy：

- Layer 7 Load Balancer 理解 HTTP，可以根據 Host、Path 或 Header 路由，通常具有 HTTP Reverse Proxy 行為。
- Layer 4 Load Balancer 主要根據 IP、Port、TCP 或 UDP 分配 Connection，可能使用 NAT 或 Direct Server Return，不一定解析或重新建立 HTTP Request。

所以「Load Balancer 是具有負載分配功能的 Reverse Proxy」適合描述本章的 Layer 7 教學程式，但不是所有網路 Load Balancer 的完整定義。

## Stage 07 的選擇

Stage 07 的 Taipei 與 Virginia Load Balancers 都會接收 HTTP Request、選擇區域內 Web Server 並轉送 Response，因此同時扮演 Layer 7 Load Balancer 與 Reverse Proxy。

