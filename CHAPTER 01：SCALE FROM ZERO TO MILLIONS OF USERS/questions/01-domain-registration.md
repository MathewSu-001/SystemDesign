# 網域名稱與 IP 的對應是否需要全球註冊？

## 問題

`www.mysite.com` 與 IP 位址的對應是否都需要進行全球註冊？如果不需要，DNS 如何建立映射？

## 短答案

需要在公開 DNS 中維持全球唯一的是可註冊網域，例如 `mysite.com`；`www.mysite.com → IP` 則由該網域的管理者在 Authoritative DNS 中建立 DNS Record，不需要逐筆向全球機構申請，而且網域與 IP 不必一對一。

## 詳細說明

實際部署通常先取得一個確實配置給 Server 或 Load Balancer 的公開 IP，再向 Registrar 註冊尚未被使用的網域，例如 `mysite.com`。Registry 保存註冊資料，並將這個網域委派給指定的 Authoritative DNS Servers。

網域管理者接著在 DNS 服務中建立紀錄：

```dns
www.mysite.com.    A    15.125.23.214
api.mysite.com.    A    15.125.23.214
```

DNS Resolver 查詢時，會沿著 Root DNS、`.com` DNS，最後找到 `mysite.com` 的 Authoritative DNS，取得上述紀錄。DNS 的全球階層和委派機制讓 Resolver 知道應向誰取得答案，而不是將每一筆子網域紀錄集中登記在單一全球資料庫。

映射不必一對一：多個名稱可以指向同一個 IP；一個名稱也可以擁有多筆 A Records。CNAME 還能將一個名稱設定成另一個名稱的別名。

本章的 `15.125.23.214` 只是教學假設。實際部署不能任意使用未配置給自己的公開 IP。
