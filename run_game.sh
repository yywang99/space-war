#!/bin/bash
# Space War Automation Script by 小Go

PROJECT_DIR=$(pwd)
VENV_DIR="$PROJECT_DIR/.venv"

echo "🚀 小Go 正在為老大啟動 太空大戰..."

# 1. 檢查並建立虛擬環境
if [ ! -d "$VENV_DIR" ]; then
    echo "📦 第一次執行，正在建立專屬虛擬環境..."
    sudo DEBIAN_FRONTEND=noninteractive apt install -y python3-venv
    python3 -m venv "$VENV_DIR"
fi

# 2. 檢查並安裝依賴
echo "🛠️ 正在確認武器庫（依賴項）是否齊全..."
"$VENV_DIR/bin/pip" install -U pip > /dev/null
"$VENV_DIR/bin/pip" install -r "$PROJECT_DIR/requirements.txt" > /dev/null

# 3. 執行遊戲
echo "🎮 準備就緒！祝老大戰果輝煌！"
"$VENV_DIR/bin/python3" "$PROJECT_DIR/app.py"
