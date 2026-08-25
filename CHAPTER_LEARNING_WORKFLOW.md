# System Design Chapter 學習流程

這份文件定義每個 Chapter 共用的架構演進與程式整理方式。目標是讓每個階段都能獨立閱讀、獨立執行，同時清楚看出系統如何從上一個階段延伸。

## 核心原則

1. 每次只加入一個主要架構概念。
2. 保留上一階段的程式，不直接覆寫。
3. 每個階段都是完整、可獨立執行的範例。
4. 階段程式之間原則上不互相引用。
5. 可接受少量重複程式碼，以換取容易閱讀與比較。
6. 共用的正式實作只有在重複內容明顯增加時，才抽到 `common/`。

## 建議目錄

每個 Chapter 延續相同分類：

```text
CHAPTER XX/
├── README.md
├── src/
│   ├── stage01_<topic>.py
│   ├── stage02_<topic>.py
│   └── stage03_<topic>.py
├── decisions/
│   ├── 001-<topic>.md
│   ├── 002-<topic>.md
│   └── 003-<topic>.md
├── notes/
├── questions/
└── assets/
    ├── 01-<topic>.jpg
    ├── 02-<topic>.jpg
    └── 03-<topic>.jpg
```

使用 `stage01_` 而不是單純的 `01_`，是因為 Python 模組名稱若以數字開頭，未來不方便匯入。

## 階段延伸方式

假設架構依序演進：

```text
Stage 01：單一伺服器
    ↓
Stage 02：多台 Web Server + Load Balancer
    ↓
Stage 03：加入 Cache
    ↓
Stage 04：加入 CDN
```

程式可整理為：

```text
src/
├── stage01_single_server.py
├── stage02_load_balancer.py
├── stage03_cache.py
└── stage04_cdn.py
```

`stage02_load_balancer.py` 是第二階段的完整版本。它可以從第一階段複製後修改，但不引用或改動 `stage01_single_server.py`。第三階段同樣保留負載平衡架構，再加入 Cache。

## 每個階段要記錄的內容

每新增一個階段，在對應的 decision 文件中回答：

1. 上一階段遇到什麼問題？
2. 這一階段新增什麼元件？
3. Request 的流向如何改變？
4. 如何啟動程式？
5. 如何確認新元件有作用？
6. 這個階段暫時不處理什麼？

範例：

```md
# 002：加入 Load Balancer

## 問題
單一 Web Server 無法分散流量，故障時服務也會中斷。

## 改動
增加第二台 Web Server，並在前方加入 Load Balancer。

## Request 流程
User → Load Balancer → Web Server 1 或 Web Server 2

## 驗證
連續發送多次請求，確認不同 Web Server 都有收到請求。

## 本階段不處理
Cache、CDN 與 Database replication。
```

## README 的角色

每個 Chapter 的 `README.md` 是導覽頁，不需要塞入所有實作細節。建議列出：

- Chapter 的學習目標
- 架構演進順序
- 每個階段的程式連結
- 對應的架構決策與圖片
- 建議閱讀與執行順序

## 何時抽出共用程式

學習初期優先保持每個階段獨立。如果相同程式已經很長，且重複內容開始妨礙理解，再整理為：

```text
src/
├── common/
│   └── web_server.py
├── stage01_single_server.py
├── stage02_load_balancer.py
└── stage03_cache.py
```

即使抽出共用程式，每個 `stageXX` 檔案仍應是清楚的執行入口，讓讀者可以直接知道該階段新增了哪些元件。

## 建議閱讀方式

1. 先看該 Chapter 的 `README.md`。
2. 看 Stage 01 的架構圖、decision 與程式。
3. 一次只往下一個 Stage 前進。
4. 比較前後兩個 Stage，找出新增或改變的部分。
5. 執行程式並按照 decision 文件驗證結果。

最重要的原則是：保留每一步的完整樣貌，讓最後的架構即使變複雜，也能隨時回到最初階段重新理解。
