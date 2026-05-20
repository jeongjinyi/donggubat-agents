"""
core/sheets_client.py
Google Sheets API 연결 모듈 — 모든 에이전트가 공유
Notion 대신 구글 스프레드시트를 데이터베이스로 사용합니다.

필요 패키지: gspread, google-auth
설치: pip install gspread google-auth --break-system-packages
"""

import json
import os
import gspread
from google.oauth2.service_account import Credentials

# 구글 API 스코프 (읽기 + 쓰기 모두)
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

# 스프레드시트 헤더 정의 (시트의 1행)
HEADERS = [
    "과제명",        # A
    "카테고리",      # B
    "담당 구분",     # C  내 과제 / 위임 과제
    "담당자",        # D
    "중요도",        # E  높음 / 보통 / 낮음
    "시급도",        # F  긴급 / 보통 / 여유
    "마감일",        # G  YYYY-MM-DD
    "상태",          # H  대기 / 진행중 / 완료 / 지연
    "관련 문서",     # I  URL
    "메모",          # J
    "상위 과제 ID",  # K  숫자 (행 번호 기준)
    "연결 방식",     # L  sequential / parallel / approval
    "완료일",        # M  YYYY-MM-DD
    "ID",            # N  자동 증가 정수 (추가 시 자동 부여)
]


def _get_client():
    """Service Account JSON으로 인증된 gspread 클라이언트 반환"""
    creds_json = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON", "")
    if not creds_json:
        raise ValueError(
            "GOOGLE_SERVICE_ACCOUNT_JSON 환경변수가 설정되지 않았습니다.\n"
            "GitHub Secrets에 Service Account JSON 전체 내용을 등록하세요."
        )
    creds_dict = json.loads(creds_json)
    creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    return gspread.authorize(creds)


def get_sheet(spreadsheet_id: str, sheet_name: str = "과제목록"):
    """
    특정 스프레드시트의 시트 객체 반환.
    시트가 없으면 자동으로 생성하고 헤더를 추가합니다.
    """
    client = _get_client()
    spreadsheet = client.open_by_key(spreadsheet_id)

    # 시트 이름으로 찾기, 없으면 생성
    try:
        sheet = spreadsheet.worksheet(sheet_name)
    except gspread.WorksheetNotFound:
        sheet = spreadsheet.add_worksheet(title=sheet_name, rows=1000, cols=20)
        sheet.append_row(HEADERS)
        print(f"[INFO] '{sheet_name}' 시트를 새로 만들고 헤더를 추가했습니다.")

    return sheet


def read_all_tasks(spreadsheet_id: str, sheet_name: str = "과제목록") -> list[dict]:
    """
    시트의 모든 행을 딕셔너리 리스트로 반환.
    1행(헤더)은 자동으로 키로 사용됩니다.
    """
    sheet = get_sheet(spreadsheet_id, sheet_name)
    records = sheet.get_all_records(expected_headers=HEADERS)
    return records


def append_task(spreadsheet_id: str, task: dict, sheet_name: str = "과제목록") -> int:
    """
    새 과제를 시트 맨 아래에 추가합니다.
    자동으로 ID를 부여하고, 추가된 행 번호를 반환합니다.
    """
    sheet = get_sheet(spreadsheet_id, sheet_name)
    existing = sheet.get_all_records(expected_headers=HEADERS)

    # ID 자동 증가
    max_id = max((int(r.get("ID", 0)) for r in existing if str(r.get("ID", "")).isdigit()), default=0)
    new_id = max_id + 1

    row = [
        task.get("과제명", ""),
        task.get("카테고리", "기타"),
        task.get("담당 구분", "내 과제"),
        task.get("담당자", ""),
        task.get("중요도", "보통"),
        task.get("시급도", "보통"),
        task.get("마감일", ""),
        task.get("상태", "대기"),
        task.get("관련 문서", ""),
        task.get("메모", ""),
        task.get("상위 과제 ID", ""),
        task.get("연결 방식", ""),
        task.get("완료일", ""),
        new_id,
    ]
    sheet.append_row(row, value_input_option="USER_ENTERED")
    print(f"[OK] 과제 추가: {task.get('과제명')} (ID: {new_id})")
    return new_id


def update_task_status(
    spreadsheet_id: str,
    task_id: int,
    status: str,
    done_date: str = "",
    sheet_name: str = "과제목록",
) -> bool:
    """
    ID로 과제를 찾아 상태(H열)와 완료일(M열)을 업데이트합니다.
    """
    sheet = get_sheet(spreadsheet_id, sheet_name)
    all_values = sheet.get_all_values()

    header = all_values[0]
    id_col = header.index("ID") + 1       # 1-indexed
    status_col = header.index("상태") + 1
    done_col = header.index("완료일") + 1

    for i, row in enumerate(all_values[1:], start=2):  # 2행부터 (1행=헤더)
        if str(row[id_col - 1]) == str(task_id):
            sheet.update_cell(i, status_col, status)
            if done_date:
                sheet.update_cell(i, done_col, done_date)
            print(f"[OK] 과제 ID {task_id} → 상태: {status}")
            return True

    print(f"[WARN] ID {task_id} 과제를 찾지 못했습니다.")
    return False


def ensure_headers(spreadsheet_id: str, sheet_name: str = "과제목록"):
    """
    시트에 헤더가 없거나 잘못된 경우 재설정합니다.
    기존 데이터는 유지됩니다.
    """
    sheet = get_sheet(spreadsheet_id, sheet_name)
    first_row = sheet.row_values(1)
    if first_row != HEADERS:
        sheet.insert_row(HEADERS, 1)
        print("[INFO] 헤더를 재설정했습니다.")
