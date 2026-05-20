"""
core/notifier.py
잔디 Incoming Webhook 알림 모듈 — 모든 에이전트가 공유
"""
import os
import requests
from datetime import datetime

JANDI_WEBHOOK_URL = os.environ.get("JANDI_WEBHOOK_URL", "")


def send_jandi(title: str, body: str, color: str = "#1D9E75") -> bool:
    """
    잔디로 메시지를 전송합니다.
    color: #1D9E75 (초록=정상) | #E24B4A (빨강=긴급) | #EF9F27 (노랑=경고)
    """
    if not JANDI_WEBHOOK_URL:
        print("[WARN] JANDI_WEBHOOK_URL 환경변수가 설정되지 않았습니다.")
        return False

    payload = {
        "body": title,
        "connectColor": color,
        "connectInfo": [
            {"title": "📋 상세 내용", "description": body},
            {"title": "🕐 발송 시각", "description": datetime.now().strftime("%Y-%m-%d %H:%M")},
        ],
    }
    try:
        res = requests.post(JANDI_WEBHOOK_URL, json=payload, timeout=10)
        res.raise_for_status()
        print(f"[OK] 잔디 전송 완료: {title}")
        return True
    except Exception as e:
        print(f"[ERROR] 잔디 전송 실패: {e}")
        return False


def send_alert(tasks: list) -> None:
    """
    마감 임박 과제 목록을 받아 잔디 알림 메시지를 구성하고 전송합니다.
    """
    if not tasks:
        return

    overdue   = [t for t in tasks if t["days"] < 0]
    today     = [t for t in tasks if t["days"] == 0]
    tomorrow  = [t for t in tasks if t["days"] == 1]
    in_3_days = [t for t in tasks if 2 <= t["days"] <= 3]

    lines = []
    if overdue:
        lines.append("🚨 *마감 초과*")
        for t in overdue:
            owner = "내 과제" if t["owner"] == "내 과제" else f"위임({t['person']})"
            lines.append(f"  • [{t['cat']}] {t['name']} — {t['due']} ({owner})")

    if today:
        lines.append("\n🔴 *오늘 마감*")
        for t in today:
            owner = "내 과제" if t["owner"] == "내 과제" else f"위임({t['person']})"
            lines.append(f"  • [{t['cat']}] {t['name']} ({owner})")

    if tomorrow:
        lines.append("\n🟠 *내일 마감*")
        for t in tomorrow:
            owner = "내 과제" if t["owner"] == "내 과제" else f"위임({t['person']})"
            lines.append(f"  • [{t['cat']}] {t['name']} ({owner})")

    if in_3_days:
        lines.append("\n🟡 *3일 이내 마감*")
        for t in in_3_days:
            owner = "내 과제" if t["owner"] == "내 과제" else f"위임({t['person']})"
            lines.append(f"  • [{t['cat']}] {t['name']} — D-{t['days']} ({owner})")

    body = "\n".join(lines)
    color = "#E24B4A" if (overdue or today) else "#EF9F27"
    send_jandi(
        title=f"📋 동구밭 과제 마감 알림 ({len(tasks)}건)",
        body=body,
        color=color,
    )
