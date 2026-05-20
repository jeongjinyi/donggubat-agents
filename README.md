# 동구밭 AI 에이전트 허브 — Google Sheets 버전

Notion 대신 Google Sheets를 데이터베이스로 사용합니다.

---

## 폴더 구조

```
donggubal-agents/
├── core/
│   ├── sheets_client.py     # Google Sheets API 연결 (Notion 대체)
│   └── notifier.py          # 잔디 Webhook 알림 (변경 없음)
├── agents/
│   └── task_manager/
│       └── run.py           # 과제 관리 에이전트
└── .github/workflows/
    └── daily_task_alert.yml # GitHub Actions 스케줄
```

---

## 초기 세팅 (3단계)

### 1단계 — Google Sheets 준비

1. **구글 드라이브**에서 새 스프레드시트 생성
2. 시트 탭 이름을 `과제목록`으로 변경
3. 1행에 아래 헤더를 순서대로 입력 (또는 에이전트 첫 실행 시 자동 생성)

| A | B | C | D | E | F | G | H | I | J | K | L | M | N |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 과제명 | 카테고리 | 담당 구분 | 담당자 | 중요도 | 시급도 | 마감일 | 상태 | 관련 문서 | 메모 | 상위 과제 ID | 연결 방식 | 완료일 | ID |

**선택 필드 값 (정확히 동일하게 입력)**

- 카테고리: `회의` / `신제품` / `마케팅` / `영업이익` / `매출` / `팀 운영` / `기타`
- 담당 구분: `내 과제` / `위임 과제`
- 중요도: `높음` / `보통` / `낮음`
- 시급도: `긴급` / `보통` / `여유`
- 상태: `대기` / `진행중` / `완료` / `지연`
- 연결 방식: `sequential` / `parallel` / `approval`

---

### 2단계 — Google Service Account 발급

1. [Google Cloud Console](https://console.cloud.google.com) 접속
2. 새 프로젝트 생성 (또는 기존 프로젝트 사용)
3. **API 및 서비스 → 라이브러리**에서 아래 두 API 활성화:
   - `Google Sheets API`
   - `Google Drive API`
4. **API 및 서비스 → 사용자 인증 정보 → 사용자 인증 정보 만들기 → 서비스 계정**
5. 서비스 계정 생성 후 → **키 탭 → 키 추가 → JSON** 다운로드
6. 다운로드된 JSON 파일을 열어 **전체 내용을 한 줄**로 복사 (GitHub Secret에 등록할 값)

#### 스프레드시트에 서비스 계정 공유

JSON 파일 안의 `client_email` 값(예: `agent@project.iam.gserviceaccount.com`)을
스프레드시트 **공유 → 편집자**로 추가해야 합니다.

---

### 3단계 — GitHub Secrets 등록

저장소 → Settings → Secrets and variables → Actions → New repository secret

| Secret 이름 | 값 |
|------------|-----|
| `GOOGLE_SERVICE_ACCOUNT_JSON` | JSON 파일 전체 내용 (1줄로 붙여넣기) |
| `GOOGLE_SPREADSHEET_ID` | 스프레드시트 URL의 ID 부분 |
| `JANDI_WEBHOOK_URL` | 잔디 Incoming Webhook URL |

> **스프레드시트 ID 찾는 법**  
> URL: `https://docs.google.com/spreadsheets/d/[여기가_ID]/edit`

---

## 로컬 테스트

```bash
pip install gspread google-auth requests

export GOOGLE_SERVICE_ACCOUNT_JSON='{"type":"service_account","project_id":"...전체JSON내용...}'
export GOOGLE_SPREADSHEET_ID="1ABC..."
export JANDI_WEBHOOK_URL="https://wh.jandi.com/..."

python agents/task_manager/run.py
```

성공 로그:
```
[2026-05-20 09:00] 과제 관리 에이전트 시작 (Google Sheets)
[INFO] 스프레드시트 읽는 중... (시트: 과제목록)
[INFO] 총 10개 행 조회됨
[INFO] 알림 대상 과제: 3건
[OK] 잔디 전송 완료: 📋 동구밭 과제 마감 알림 (3건)
[DONE] 에이전트 실행 완료
```

---

## 에이전트 추가하는 법

새 에이전트는 `agents/` 폴더에 추가하고 `core/sheets_client.py`와 `core/notifier.py`를 그대로 import해서 사용합니다.

```python
from core.sheets_client import read_all_tasks, append_task, update_task_status
from core.notifier import send_jandi
```
