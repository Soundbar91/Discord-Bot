#!/usr/bin/env bash
# Droplet 에서 실행되는 배포 스크립트.
# GitHub Actions 가 SSH 접속해서 이 파일을 실행합니다.
set -euo pipefail

cd "$(dirname "$(readlink -f "$0")")"

echo "▶ git pull"
git pull origin main

echo "▶ 가상환경 확인"
if [ ! -d .venv ]; then
    python3 -m venv .venv
fi

echo "▶ 의존성 설치"
.venv/bin/pip install -q --upgrade pip
.venv/bin/pip install -q -r requirements.txt

echo "▶ systemd 서비스 재시작"
sudo systemctl restart study-bot

echo "✓ 배포 완료"
sudo systemctl status study-bot --no-pager -n 10
