#!/bin/bash

# 目标时间（10:02）
TARGET_TIME="10:02"

# 循环检查当前时间
while true; do
    # 获取当前时间
    CURRENT_TIME=$(date +"%H:%M")

    # 如果当前时间等于目标时间，运行命令并退出循环
     echo "$CURRENT_TIME | checking ..."
    if [[ "$CURRENT_TIME" == "$TARGET_TIME" ]]; then
        echo "$CURRENT_TIME | 执行 python main.py..."
        python main.py
        break
    fi

    # 每隔 60 秒检查一次时间
    sleep 60
done