"""
agents/task_manager/run.py
과제 관리 에이전트 — Google Sheets 버전
GitHub Actions에서 매일 오전 9시(KST)에 자동 실행됩니다.

필요 환경변수:
  GOOGLE_SERVICE_ACCOUNT_JSON  : Service Account JSON 전체 내용 (1줄 문자열)
  GOOGLE_SPREADSHEET_ID        : 스프레드시트 URL의 ID 부분
  JANDI_WEBHOOK_URL            : 잔디 Incoming Webhook URL

로컬 테스트:
  export GOOGLE_SERVICE_ACCOUNT_JSON='{"type":"service_account",...}'
  export GOOGLE_SPREADSHEET_ID="1ABC..."
  export JANDI_WEBHOOK_URL="https://wh.jandi.com/..."
  python agents/task_manager/run.py
"""

import sys
import os
from datetime import date, datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from core.sheets_client import read_all_tasks
from core.notifier import send_alert, send_jandi

SPREADSHEET_ID = os.environ.get("GOOGLE_SPREADSHEET_ID", "")
SHEET_NAME     = os.environ.get("SHEET_NAME", "과제목록")   # 시트 탭 이름 (기본값: 과제목록)
ALERT_DAYS     = 3   # 며칠 이내 마감을 알림에 포함할지


def parse_tasks(records: list) -> list:
    """
    Google Sheets 행 데이터(딕셔너리 리스트)를 알림용 과제 리스트로 변환합니다.
    """
    today = date.today()
    tasks = []

    for r in records:
        name   = str(r.get("과제명", "")).strip()
        status = str(r.get("상태", "")).strip()
        due_str = str(r.get("마감일", "")).strip()

        # 빈 행 / 완료 과제 건너뜀
        if not name or status == "완료":
            continue

        # 날짜 파싱
        try:
            due_date = datetime.strptime(due_str, "%Y-%m-%d").date()
        except ValueError:
            continue  # 날짜 형식이 잘못된 행은 건너뜀

        days_left = (due_date - today).days

        # ALERT_DAYS 초과는 알림 제외 (마감 초과는 포함)
        if days_left > ALERT_DAYS:
            continue

        tasks.append({
            "name":   name,
            "cat":    str(r.get("카테고리", "기타")).strip(),
            "owner":  str(r.get("담당 구분", "내 과제")).strip(),
            "person": str(r.get("담당자", "")).strip(),
            "imp":    str(r.get("중요도", "보통")).strip(),
            "urg":    str(r.get("시급도", "보통")).strip(),
            "due":    due_str,
            "days":   days_left,
        })

    return tasks


def run():
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M')}] 과제 관리 에이전트 시작 (Google Sheets)")

    if not SPREADSHEET_ID:
        print("[ERROR] GOOGLE_SPREADSHEET_ID 환경변수가 설정되지 않았습니다.")
        sys.exit(1)

    # Google Sheets에서 전체 과제 읽기
    print(f"[INFO] 스프레드시트 읽는 중... (시트: {SHEET_NAME})")
    records = read_all_tasks(SPREADSHEET_ID, SHEET_NAME)
    print(f"[INFO] 총 {len(records)}개 행 조회됨")

    # 알림 대상 필터링
    tasks = parse_tasks(records)
    print(f"[INFO] 알림 대상 과제: {len(tasks)}건")

    if tasks:
        send_alert(tasks)
    else:
        print("[INFO] 마감 임박 과제 없음 — 알림 미발송")

        # 자율 분석: 전체 현황 요약을 매주 월요일에 발송 (선택)
        if date.today().weekday() == 0:  # 0 = 월요일
            all_active = [r for r in records if str(r.get("상태", "")).strip() != "완료"]
            if all_active:
                summary = f"진행 중 과제 {len(all_active)}건 — 이번 주 마감 임박 없음"
                send_jandi("📊 동구밭 주간 과제 현황", summary, "#1D9E75")

    print("[DONE] 에이전트 실행 완료")


if __name__ == "__main__":
    run()
