# LLM Wiki & Scrum Engineering Infrastructure Templates

이 폴더는 **Karpathy 스타일 LLM Wiki**와 **AI 기반 개발 스크럼(My Scrum) 인프라**를 새로운 프로젝트나 저장소에 즉시 복제하여 사용할 수 있도록 민감 정보 및 사내 데이터를 정제한 공식 템플릿 패키지입니다.

---

## 📦 템플릿 구성

### 1. `Obsidian-Vault-Template/` (Karpathy 스타일 마크다운 지식 복리 위키)
- **핵심 아키텍처**:
  - `raw/`: 원본 자료 보관소 (불변 상태 유지)
  - `wiki/`: 에이전트 가공 5대 지식망 (`concepts/`, `entities/`, `comparisons/`, `synthesis/`, `queries/`, `sources/`)
  - `wiki/build.py`: 대시보드(`README.md`), 색인(`index.md`), 변경 이력(`log.md`) 및 주간 복리 원장 자동 컴파일러
- **운영 규칙 및 에이전트 스킬**:
  - `AGENTS.md`, `purpose.md`, `schema.md`
  - `.agents/rules/`: `wiki_ingestion_rule.md`, `owner_rule.md`, `core_system_rule.md`, `user_dev_memory.md`
  - `.agents/skills/`: `llm_wiki_compiler`, `wiki_qa`, `scrum_report`, `sources_classifier`, `linkedin_ingestion`

### 2. `my_scrum-template/` (일일/월간 스크럼 및 AI 세션 관리 인프라)
- **디렉터리 구조**:
  - `daily/`, `monthly/`, `total/`, `plans/`, `chats/` (`raw/`, `md/`)
- **유틸리티 & 배치**:
  - `scripts/sync_sessions.py`: Claude Code 및 Antigravity 세션 자동 동기화, 더미 필터링, 마크다운 파싱 및 1:1 미러링
  - `scripts/parse_chat.py`: JSONL 대화 로그 프리미엄 마크다운 변환기
  - `scripts/convert_links.py`: plans 및 chats 링크 상대 경로 자동 변환기
  - `compile_wiki.bat`, `sync_and_compile.bat`: 원클릭 실행 스크립트
  - `scrum_command.md`: 일일 스크럼 프롬프트 템플릿

---

## 🚀 빠른 시작 가이드 (Quick Start)

### 1단계: 원하는 경로로 폴더 복제
```powershell
# 새 프로젝트 경로로 복사 예시
Copy-Item -Recurse "./Obsidian-Vault-Template" "경로/내-볼트"
Copy-Item -Recurse "./my_scrum-template" "경로/내-스크럼"
```

### 2단계: 소유자 및 프로젝트 정보 설정
1. `Obsidian-Vault-Template/wiki/entities/소유자.md` 파일명을 본인 이름으로 변경
2. `purpose.md`의 연구 범위 및 목적 작성
3. `scrum_command.md`의 Git Author명 설정

### 3단계: 컴파일 테스트
```powershell
# 옵시디언 볼트 대시보드 컴파일
py "Obsidian-Vault-Template/wiki/build.py"

# 또는 my_scrum 배치 실행
cd "my_scrum-template"
.\compile_wiki.bat
```
