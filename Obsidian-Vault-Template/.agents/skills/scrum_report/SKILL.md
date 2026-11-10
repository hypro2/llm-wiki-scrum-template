---
name: scrum_report
description: 일일 개발 작업 내역(Git log, git diff, Claude/Antigravity 대화 로그 등)을 종합하여 일일/월별/전체 스크럼 보고서를 자동으로 생성 및 누적 업데이트하고 관련 계획서 및 대화 로그(chats) 링크를 상대 경로로 일괄 변환/동기화하는 스킬
---

# 📅 일일 스크럼 보고서 생성 및 관리 스킬 (scrum_report)

이 스킬은 사용자가 오늘 진행한 개발 작업(코드 변경, 세션 작업 등)에 대한 스크럼 정리를 요청할 때 트리거되어, 관련 데이터를 분석하고 규격화된 보고서로 저장 및 누적 업데이트를 수행합니다.

## 🛠️ 작업 순서 및 엄격 지침 (SOP)

### 1. [CRITICAL] 당일 전체 작업 프로젝트 및 세션 전수 스캔 (Pre-Flight Scan)
특정 저장소나 현재 세션에만 매몰되어 다른 저장소(예: `backend-api`, `frontend-app`, `rag-pipeline` 등)의 작업이 누락되는 사고를 원천 방지하기 위해 **반드시 아래 사전 데이터 수집 및 전수 검사를 실행**합니다:

- **저장소 코드 변경 내역**:
  - `git status` (수정/추가된 파일 목록 파악)
  - `git log --author="<author-name>" --no-merges -n 10 --stat` (본인 계정 작성 커밋만 필터링하여 파악)
  - `git diff` (실제 코드의 구체적인 변경 사항 파악)
  - `Documents/GitHub/` (또는 작업 워크스페이스 루트) 하위의 모든 저장소에서 오늘(`YYYY-MM-DD`) 변경/커밋된 파일 목록을 스캔하여 **오늘 작업한 모든 대상 프로젝트 목록(Project Scope)을 확정**합니다.
  - **[CRITICAL] 협업 저장소 본인 작성 커밋 엄격 필터링:
    - 반드시 **`git log --author="<author-name>" --no-merges`** 기준으로 본인이 직접 작성한 커밋과 워킹 트리 변경분만 스크럼 및 위키에 수록합니다.
    - `origin/main` 병합(Merge)을 통해 유입된 타 작업자의 커밋 및 기능(예: 공용 인증/권한 모듈, 타 담당자 신규 라우터 등 타인 작성분)은 **본인 작업이 아니므로 완료사항/진행사항/작업파일/위키 엔티티에서 전면 배제**합니다. (병합 커밋의 경우 본인이 직접 수행한 충돌 해소 사실만 간략히 언급 가능)

- **AI 대화 로그 및 플랜 파일 자동 수집 & 동기화**:
  - **3대 소스 경로**:
    1. Claude Code: `~/.claude/projects/` (프로젝트별 `.jsonl`)
    2. Antigravity: `~/.gemini/antigravity/brain/` (`transcript.jsonl` 및 `implementation_plan.md`)
    3. Antigravity IDE: `~/.gemini/antigravity-ide/brain/` (`transcript.jsonl` 및 `implementation_plan.md`)
  - **일괄 동기화 실행**: `python "my_scrum/scripts/sync_sessions.py"` (또는 `sync_and_compile.bat`)를 실행하여 3대 소스의 최신 세션/플랜을 `my_scrum` 및 `Obsidian Vault`로 증분 수집, 마크다운 파싱 및 위키 컴파일을 원클릭으로 수행합니다.
  - **계획서(Plans) 확인**: `plans/` 디렉토리 내에 오늘 새로 추가되었거나 수정된 계획서를 전수 확인합니다.
  - **대화 로그(Chats) 분석**: `my_scrum/chats/md/` 내의 파싱된 마크다운 대화 로그를 기반으로 작업 맥락을 분석합니다.

### 2. 프로젝트별 스크럼 작성 및 링크 규칙 (Core Value Focus & Code Path Ban)
확정된 프로젝트 범위 전체에 대해 `my_scrum/scrum_command.md` 템플릿 양식을 준수하여 다음 3대 항목을 작성합니다:
- **[CRITICAL] 코드 세부 내용 걷어내기 및 비즈니스/기능 핵심 위주 서술 (No Code Dumps)**:
  - 지엽적인 내부 코드 구현(함수명, 장황한 코드 파일 경로 나열, 단순 구문 수정 등)을 과감히 걷어냅니다.
  - **어떤 문제나 장애가 해결되었는지, 시스템과 비즈니스 관점에서 어떤 기능적 가치와 성능 개선이 달성되었는지 임팩트 위주로 압축 서술**합니다.
- **[CRITICAL] 코드 파일 경로 링크(`file:///...`) 첨부 전면 금지**:
  - 보고서 본문 및 주요 작업 파일 섹션에 `file:///...` 형태의 로컬 코드 절대 경로 링크를 절대 삽입하지 마십시오.
  - 소스 코드 및 실행 파일은 순수 백틱 텍스트(`data_processor.py`, `helper_cli.exe` 등)로만 깔끔하게 명시합니다.
- **허용되는 링크 (Only Plans & Chats)**:
  - **계획서 링크**: `[plan-name.md](../plans/plan-name.md)` 상대 경로만 사용
  - **대화 로그 링크**: `- 관련 대화: [chat-name.md](../chats/md/chat-name.md)` 상대 경로만 사용
- **✅ 완료사항 (Done)**:
  - 다중 프로젝트 작업 시 프로젝트별(예: `repo1`, `repo2`, `my_scrum` 등)로 명확히 구분하여 핵심 성과 위주로 명료하게 서술
  - **[CRITICAL] 세션 자동 동기화/위키 미러링 자체는 완료사항에서 제외**: `sync_sessions.py` 및 Obsidian 미러링/컴파일은 스크럼 작성 시 수반되는 정례 자동 인프라 작업이므로, 보고서 본문(`✅ 완료사항`)에 별도 항목으로 기재하지 마십시오.
- **🔄 진행사항 및 향후 계획 (In Progress & To Do)**: 미완료 과제 및 다음 착수 작업 나열
- **📂 주요 작업 파일 (Modified & Added Files)**: 무차별 파일 덤프를 지양하고 핵심 아키텍처/기능 파일 위주로 압축 명시 (경로 링크 없이 파일명 텍스트로만 기술)

### 3. 폴더 체계에 따른 저장 및 1:1 양방향 미러링 동기화
- **일별/월별/전체 저장**: `daily/YYYY-MM-DD.md`, `monthly/YYYY-MM.md`, `total/scrum_roadmap_template.md` 동시 누적 갱신
- **상대 경로 검증**: `python "my_scrum/scripts/convert_links.py"` 실행하여 절대 경로 링크가 없는지 확인
- **Obsidian Vault 지식 베이스 1:1 구조 일치 동기화**:
  - `my_scrum/chats/raw/` -> `Obsidian Vault/raw/sources/2-Areas/Work-Logs/chats/raw/` (1:1 복사)
  - `my_scrum/chats/md/` -> `Obsidian Vault/raw/sources/2-Areas/Work-Logs/chats/md/` (1:1 복사)
  - `my_scrum/daily/`, `monthly/`, `total/`, `plans/` -> `Obsidian Vault/raw/sources/2-Areas/Work-Logs/` 상응 디렉터리로 1:1 동기화
  - 위키 요약본(`wiki/sources/2-Areas/Work-Logs/daily/src-YYYY-MM-DD.md`, `monthly/src-YYYY-MM.md`, `total/src-scrum_roadmap_template.md`) 및 주간 지식 복리 원장(`[[wiki/Weekly-Knowledge-Compounding-Ledger.md]]`) 연계 갱신
- **LLM Wiki 컴파일**: `python "wiki/build.py"` 실행하여 메인 대시보드(`README.md`), 색인(`wiki/index.md`), 타임라인 로그(`wiki/log.md`) 최신화
- **[CRITICAL] 저장소별 Git 커밋/푸시 정책 준수**:
  - `my_scrum`, `Obsidian-Vault`: GitHub 원격(`origin/main`) 푸시 수행
  - 비공개 내부 저장소: **외부/원격 저장소로의 `git push` 절대 금지** (원격 푸시 대상은 오직 `my_scrum`과 `Obsidian-Vault`로 엄격히 한정)
