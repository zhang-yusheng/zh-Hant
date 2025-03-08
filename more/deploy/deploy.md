# 本地部署指南

## 前置要求

- Git
- Node.js 20 或更高版本

## 安裝步驟

### 1. 安裝 Git

1. 從 [Git 官方網站](https://git-scm.com/downloads) 下載並安裝 Git
2. 驗證安裝：

```bash
git --version
```

### 2. 安裝 Node.js

1. 從 [Node.js 官方網站](https://nodejs.org/) 下載並安裝 Node.js
2. 安裝 20.x 或更高的 LTS 版本
3. 驗證安裝（確保版本號爲 20.x 或更高）：

```bash
node --version
npm --version
```

### 3. 克隆項目

```bash
git clone https://github.com/zhang-yusheng/zhang-yusheng.github.io.git
cd zhang-yusheng.github.io
```

### 4. 安裝 docsify-cli

```bash
npm i docsify-cli -g
```

### 5. 運行項目

```bash
docsify serve
```

啓動服務後，請查看終端輸出。docsify 會提供一個本地訪問鏈接。使用 Ctrl+ 點擊（或 Cmd+ 點擊）終端中的鏈接來在瀏覽器中打開項目。

注意：
- 實際使用的端口可能會因本地環境而異。始終使用終端中提供的鏈接來訪問項目。
- 如果您想指定一個特定的端口，可以使用 `-p` 參數，例如：

```bash
docsify serve -p 4000
```

這將使用端口 4000 來運行服務。

## 構建電子書（可選）

如果您需要構建電子書版本，請按照以下步驟操作：

### 1. 配置 Git 環境

確保 Git 的 bin 目錄（通常是 `C:\Program Files\Git\bin`）已添加到系統的 PATH 環境變量中。這是爲了能夠使用 `sh` 命令。驗證配置：

```bash
sh --version
```

### 2. 安裝相關依賴

```bash
sh ./scripts/install_packages.sh
```

### 3. 構建電子書

使用以下命令構建不同格式的電子書：

|      命令      |    描述    |
| :------------: | :--------: |
|  `honkit pdf`  |  生成 PDF  |
| `honkit epub`  | 生成 EPUB  |
| `honkit mobi`  | 生成 MOBI  |