# iPhone 版游泳成績助手

這是一個 **iPhone 友善版 Web App**：
- 用 Safari 開啟
- 可「加入主畫面」
- 介面已調整成手機操作
- 可建立選手、手動記錄成績、貼公開成績網址自動匯入

## 這個版本是什麼
這不是原生 iOS `.ipa`，而是比較快能上手的 **手機版網頁 App（PWA 風格）**。
它很適合先驗證流程，之後再升級成正式 iPhone App。

## 啟動方式

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd backend
python app.py
```

打開：

```text
http://127.0.0.1:5000
```

## iPhone 使用方式
1. 先把這個程式部署到一個可公開連線的網址，例如 Render、Railway、Fly.io 或自己的主機。
2. 用 iPhone Safari 開啟網址。
3. 按分享按鈕。
4. 選「加入主畫面」。
5. 之後就可以像 App 一樣直接點圖示開啟。

## 已有功能
- 新增選手
- 手動新增成績
- 從公開成績網址嘗試抓表格
- 自動標示 PB
- SQLite 本地資料庫儲存

## 下一步最值得加的功能
- 依選手姓名自動搜尋公開成績
- 同一賽事去重複
- 達標提醒
- 圖表看進步曲線
- LINE Notify / Email 通知
- 登入帳號後多裝置同步
- 正式包成原生 iPhone App

## 建議升級路線
### 路線 A：先上線就好
保留 Flask 後端，部署成網址，iPhone 直接加入主畫面。

### 路線 B：做成真正 iPhone App
把前端改成 React / Vue，再用 Capacitor 包成 iOS App。
這樣可以：
- 有原生 App 圖示
- 可做推播
- 可接相機、通知、檔案

## 注意
各賽事成績頁格式不一定完全一樣，所以目前抓取器是通用版，可能需要再針對泳協實際頁面微調。
