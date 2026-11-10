---
name: linkedin_ingestion
description: >
  LinkedIn 프로필 최근 활동 피드를 Playwright로 전체 수집(무한 스크롤 + see-more 클릭 + 댓글 펼치기)하고,
  댓글 URL 자동 추출 → lnkd.in 웹 검색 보강 → Obsidian LLM Wiki 정성 심층 집필 → build.py 컴파일까지
  전체 파이프라인을 재수행 가능하도록 정의한 SOP 스킬.
  트리거: "링크드인 수집", "LinkedIn 스크래핑", "링크드인 위키 저장", "SOP 재실행" 등
---

# LinkedIn Activity Ingestion & Web-Enriched Wiki Compilation SOP (재수행 가이드)

## 1. 개요 (Overview)
본 스킬은 **LinkedIn 프로필 최근 활동 피드의 전체 본문 자동 수집**부터,
수집된 포스트 항목을 **인터넷 검색(`search_web`)으로 원본 GitHub 링크 및 기술 아키텍처를 탐색·보강하여
Obsidian LLM Wiki (`wiki/`)에 고품질 정성 집필 및 자동 컴파일**하기까지의 전체 워크플로우를 정의합니다.

### 전체 파이프라인 (5단계)
```
[1] linkedin_final_scrape.py 실행
      → 무한 스크롤 + see-more 클릭 + 댓글 펼치기
      → raw/sources/0-Inbox/linkedin_posts/*.md 생성
      ↓
[2] 댓글 URL 자동 추출 (스크립트 내장)
      → "in the comments" 패턴 감지 → 댓글 섹션 클릭 → URL 파싱
      ↓
[3] lnkd.in 링크 웹 검색 보강 (AI 수동 수행)
      → lnkd.in 잔존 파일 탐지 → search_web으로 실제 GitHub/arXiv 탐색 → 파일 직접 업데이트
      ↓
[4] LLM Wiki 지식 심층 정성 집필 및 병합 (AI 직접 작성, 빈약 요약 금지)
      → wiki/sources/0-Inbox/linkedin_posts/src-*.md 1:1 매칭 생성 (시니어 엔지니어링 수준)
      → wiki/concepts/, wiki/entities/ 보강
      ↓
[5] wiki/build.py 실행 → 인덱스/로그/대시보드 컴파일
```

---

## 2. 1단계: Playwright 기반 전체 피드 & 본문 전체(Full Content) 수집

LinkedIn 피드의 `...자세히 보기` (see-more) 접힌 본문을 자동으로 펴서 100% 원본 텍스트를 수집하는 Python 스크립트 워크플로우입니다.

### 실행 커맨드
```powershell
# 1. 의존성 패키지 설치
python -m pip install playwright

# 2. 브라우저 세션 기반 스크립트 실행
python "<Obsidian-Vault-Path>\raw\sources\3-Resources\Technical-Notes\linkedin_final_scrape.py"
```

### 스크립트 위치 (사용자 별도 준비)
`<Obsidian-Vault-Path>\raw\sources\3-Resources\Technical-Notes\linkedin_final_scrape.py` *(템플릿 기본 저장소에는 미포함; Playwright 스크래퍼를 해당 경로에 배치하여 사용)*

### 핵심 수집 로직 요약
```python
# 1. Persistent Session Profile 로드 (로그인 유지)
user_data_dir = os.path.join(os.path.expanduser("~"), ".linkedin_stealth_profile")

# 2. 피드 종단 감지형 무한 스크롤
# 3. '...자세히 보기 / see more' 버튼 일괄 자동 클릭 [3.5단계]
# 4. 댓글 섹션 자동 펼치기 [3.6단계]
# 5. 항목별 개별 마크다운 파일 분리 저장 (.feed-shared-update-v2)
```

### 결과물
- `raw/sources/0-Inbox/linkedin_posts/*.md` (포스트별 초기 수집 파일 — 분류 후 `raw/sources/3-Resources/Technical-Notes/linkedin_posts/`로 이동 관리)
- `~/.gemini/antigravity/scratch/linkedin_activities.txt` (전체 통합본)

---

## 3. 2.5단계: 댓글 섹션 자동 펼치기 및 URL 추출 (스크립트 내장)

**배경**: 많은 포스트가 "GitHub repo in the comments!", "Link in the replies!" 형태로 실제 원본 링크를 본문이 아닌 **댓글**에만 올립니다. 댓글 영역 자동 펼침 및 URL 파싱 로직을 스크립트에 내장하여 처리합니다.

### 동작 원리 (`linkedin_final_scrape.py` 내 [3.6]단계)
```python
# 1. 본문에 댓글 안내 키워드가 있는 포스트만 선별
needs_comments = any(kw in post_text for kw in [
    "in the comments", "in the replies", "link in the comments",
    "shared the link", "repo in the comments", "댓글에"
])

# 2. 해당 포스트의 댓글 버튼 클릭하여 댓글 로드
if needs_comments:
    comment_btns = post_el.locator(
        "button.comment-button, button[aria-label*='댓글'], .social-counts-reactions__count-value"
    ).all()
    for cb in comment_btns:
        if cb.is_visible():
            cb.click(timeout=1500)
            time.sleep(1.5)
            break

# 3. 댓글 HTML에서 외부 URL 파싱 (LinkedIn 내부/가입 링크 제외)
comment_section = post.locator(".comments-comments-list, .feed-shared-update-v2__comments-container")
if comment_section.count() > 0:
    comment_html = comment_section.inner_html()
    comment_urls = re.findall(r'href=["\'"]([^"\']+)["\'"]', comment_html)
    comment_urls = [
        u for u in comment_urls
        if u.startswith("http") and "linkedin.com" not in u and "lnkd.in/" not in u
    ]
```

### 찐 원본 출처 우선순위
```
1순위: 댓글에서 파싱된 외부 URL
2순위: 본문 내 외부 URL
없으면: 찐 원본 출처 필드 생략 (수집 출처만 기재)
```

---

## 4. 2.6단계: `lnkd.in` 잔존 링크 웹 검색 보강 (AI 수동 수행)

스크립트 실행 후에도 **`lnkd.in/` 단축 링크**가 찐 원본 출처로 남아있는 경우, 이는 AI Engineering 뉴스레터 가입 유도 링크 등 **진짜 원본이 아닌** 경우입니다. 이 단계에서 AI가 직접 웹 검색으로 실제 URL을 찾아 교체합니다.

### 탐지: lnkd.in 잔존 파일 확인
```powershell
Get-ChildItem "<Obsidian-Vault-Path>\raw\sources\0-Inbox\linkedin_posts" |
ForEach-Object {
    $content = Get-Content $_.FullName -Encoding UTF8 -TotalCount 5
    $line = $content | Where-Object { $_ -match "찐 원본" -and $_ -match "lnkd\.in" }
    if ($line) { Write-Host "[lnkd.in 잔존] $($_.Name)" }
}
```

### 보강 절차
1. 잔존 파일 본문 내용 읽기 (`view_file`)
2. 포스트 핵심 키워드 추출 (프로젝트명, 저자, 기술명)
3. 웹 검색: `search_web(query="<프로젝트명> GitHub site:github.com OR site:arxiv.org")`
4. 찾은 실제 URL로 해당 파일의 `찐 원본 출처` 줄 교체

---

## 5. 3단계: Obsidian LLM Wiki 지식 집필 & 병합 (Compounding) 규칙

### 🚨 [CRITICAL] 고품질 정성 집필 지침 (빈약한 요약 절대 금지)
1. **디렉터리 및 파일명 1:1 엄격 매칭**:
   - `raw/sources/0-Inbox/linkedin_posts/<원본파일명>.md` ➔ `wiki/sources/0-Inbox/linkedin_posts/src-<원본파일명>.md`
   - 임의로 줄인 파일명을 사용하지 말고 원본 파일명 기반 1:1 매칭을 유지합니다.
2. **시니어 엔지니어링 수준의 심층 작성 (Deep Rewrite)**:
   - 1~2문단의 단순 요약이나 껍데기 템플릿 작성을 **엄격히 금지**합니다.
   - AI 에이전트(LLM)는 반드시 원본 파일과 댓글을 `view_file`로 정독하고, 다음 4가지 핵심 요소를 문서에 명시해야 합니다:
     - ① **기술 아키텍처 및 작동 원리** (다이어그램, 프로세스 구조 포함)
     - ② **실증 벤치마크 수치 및 성능 비교 데이터** (표, 메트릭 명시)
     - ③ **실제 파이프라인/CLI 커맨드/코드 스니펫 예시**
     - ④ **댓글 토론 및 커뮤니티 전문가 통찰·기술적 한계점**
3. **지식 보존 및 복리 결합 (Compounding) & 실무 사례 이원화**:
   - 기존 개념/실체 파일이 이미 존재할 경우 기존 내용을 유실하지 않고 새로운 깃허브 링크, 성능 지표, 적용 사례를 유기적으로 확장 결합합니다.
   - 개념/실체 문서의 `실무 적용 사례` 섹션은 반드시 **`1. 사용자 자체 실무 적용 사례 (Internal Practice)`**와 **`2. 오픈소스/GitHub 실무 유즈케이스 (External OSS Use-Cases)`**로 분리하며, LinkedIn에서 수집된 외부 기술을 사내 시스템에 직접 적용했다고 지어내는 할루시네이션을 엄금합니다.
   - 주간 지식 복리 수행 시 도출된 5대 카테고리 지식을 `[[wiki/Weekly-Knowledge-Compounding-Ledger.md|주간 지식 복리 기록]]`에 누적 등재합니다.
4. **한 줄 요약 주석 주입**:
   - 문서 하단에 `<!-- ONE_LINE_SUMMARY: <핵심 설명 1문장> -->` 주석을 반드시 포함합니다.

---

## 6. 4단계: 위키 빌드 및 자동 컴파일 (Compile)

모든 문서 집필 및 보강이 끝나면 다음 명령어를 터미널에서 실행하여 인덱스와 대시보드를 일괄 자동 컴파일합니다.

```powershell
# Windows PowerShell 기준 실행
python "<Obsidian-Vault-Path>\wiki\build.py"
```

### 컴파일 결과 대상
- `README.md`: 볼트 루트 메인 대시보드 및 디렉터리 통계 갱신 (`wiki/overview.md`는 폐기됨)
- `wiki/index.md`: 전체 문서 색인 및 한 줄 요약 갱신
- `wiki/log.md`: 타임라인 순 위키 변경 이력 로그 갱신
- `wiki/Weekly-Knowledge-Compounding-Ledger.md`: 누적 문서 통계 자동 동기화

---

## 관련 파일
- 스크립트: `raw/sources/3-Resources/Technical-Notes/linkedin_final_scrape.py`
- 초기 수집 경로: `raw/sources/0-Inbox/linkedin_posts/` (정식 분류 경로: `raw/sources/3-Resources/Technical-Notes/linkedin_posts/`)
- 위키 소스: `wiki/sources/0-Inbox/linkedin_posts/` 및 `wiki/sources/3-Resources/Technical-Notes/linkedin_posts/`
- 위키 빌더: `wiki/build.py`
