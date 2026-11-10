# My Scrum Template (`my_scrum`)

본 저장소는 **일일/월간 스크럼 개발 작업 내역** 및 AI 세션(Claude Code, Antigravity) 대화 이력을 체계적으로 기록하고 관리하는 일지/보고서 관리 인프라 템플릿입니다.

---

## 📁 디렉터리 구조

- `daily/`: 일일 개발 스크럼 리포트 (`YYYY-MM-DD.md`)
- `monthly/`: 월별 개발 종합 스크럼 보고서 (`YYYY-MM.md`)
- `total/`: 프로젝트 전체 종합 이력 및 로드맵
- `plans/`: 작업 계획서 및 기술 아키텍처 초안
- `chats/`: 개발 대화 로그 및 컨텍스트 기록
  - `raw/`: 원본 JSONL 대화 로그 파일 보관
  - `md/`: 프리미엄 마크다운 파싱 대화 로그 파일 보관
- `scripts/`: 스크럼 및 대화 로그 파싱/링크 변환 유틸리티 스크립트
  - `parse_chat.py`: Claude Code 및 Antigravity(Gemini) 대화 로그(JSONL) 프리미엄 마크다운 파서 CLI
  - `convert_links.py`: 스크럼 보고서 내의 plans 및 chats 링크를 상대 경로(`../plans/`, `../chats/md/`)로 일괄 자동 변환하는 유틸리티
  - `sync_sessions.py`: 세션 자동 탐색, 더미 필터링, 파싱, Obsidian 1:1 미러링 및 위키 자동 컴파일 통합 파이프라인
- `compile_wiki.bat`: 연동된 **Obsidian Vault LLM Wiki 대시보드**를 최신화하는 자동 컴파일 배치 파일
- `sync_and_compile.bat`: 세션 동기화 및 위키 컴파일을 원클릭으로 수행하는 배치 파일

---

## 🔄 Obsidian Vault LLM Wiki & Chats 연동 파이프라인

본 저장소에서 생성된 스크럼 보고서, 계획서(`plans`), 및 대화 로그(`chats/`)는 `sync_sessions.py` 또는 `scrum_report` 스킬을 통해 **Obsidian Vault**(`raw/sources/2-Areas/Work-Logs/`, `raw/sources/1-Projects/plans/`, `raw/sources/2-Areas/Work-Logs/chats/`)로 자동 복사·동기화되며, `python "wiki/build.py"` 가동을 통해 위키 지식 대시보드(`README.md`), 색인(`wiki/index.md`), 변경 로그(`wiki/log.md`)로 자동 환류 및 축적(Compounding)됩니다.
