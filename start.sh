#!/usr/bin/env bash
set -e

# 切換到腳本所在目錄，確保在任何路徑執行都正常
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 檢查 .venv 是否存在，若不存在則自動建立並安裝依賴
if [ ! -d ".venv" ]; then
    echo "▶ 尚未建立虛擬環境，正在建立 .venv..."
    python3 -m venv .venv
    source .venv/bin/activate
    echo "▶ 正在安裝依賴套件..."
    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt
    else
        pip install pygame
    fi
else
    # 啟用現有的虛擬環境
    source .venv/bin/activate

    # 檢查 pygame 是否已安裝
    if ! python -c "import pygame" &>/dev/null; then
        echo "▶ 虛擬環境中缺少 pygame，正在自動安裝..."
        if [ -f "requirements.txt" ]; then
            pip install -r requirements.txt
        else
            pip install pygame
        fi
    fi
fi

# 執行遊戲
echo "▶ 正在啟動太空大戰 (app.py)..."
python app.py "$@"
