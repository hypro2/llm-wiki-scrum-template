#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
parse_chat.py - Claude Code & Antigravity (Gemini) JSONL Premium Markdown Parser (CLI)

이 스크립트는 Claude Code 및 Antigravity(Gemini)의 대화 기록(JSONL)을 분석하여
도구별 맞춤 시각화(Git Diff 생성, 터미널 쉘 블록, 언어별 구문 강조, 로컬 파일 링크)와
Obsidian/GitHub 표준 콜아웃(Callout) 디자인을 적용하여 고품질 마크다운(.md)으로 변환하는 CLI 도구입니다.

사용법:
  # 단일 파일 파싱 (자동 파일명으로 저장)
  python parse_chat.py path/to/session.jsonl

  # 단일 파일 파싱 후 특정 폴더에 저장
  python parse_chat.py path/to/session.jsonl -o chats/

  # 폴더 내 모든 JSONL 파일 일괄 파싱
  python parse_chat.py path/to/chats_dir/ -o parsed_md/
"""

import os
import sys
import json
import re
import difflib
import argparse
from datetime import datetime

# Windows 콘솔 유니코드 출력 호환성 보장
if sys.platform.startswith("win"):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")


LANG_MAP = {
    ".py": "python",
    ".js": "javascript",
    ".jsx": "jsx",
    ".ts": "typescript",
    ".tsx": "tsx",
    ".json": "json",
    ".jsonl": "json",
    ".md": "markdown",
    ".html": "html",
    ".htm": "html",
    ".css": "css",
    ".scss": "scss",
    ".bat": "bat",
    ".cmd": "bat",
    ".ps1": "powershell",
    ".sh": "bash",
    ".bash": "bash",
    ".sql": "sql",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".toml": "toml",
    ".txt": "text",
    ".diff": "diff",
    ".patch": "diff",
}


def get_lang_from_path(file_path):
    """
    파일 경로에서 확장자를 추출하여 마크다운 코드 블록 언어 태그를 반환합니다.
    """
    if not file_path:
        return "text"
    _, ext = os.path.splitext(file_path.strip().lower())
    return LANG_MAP.get(ext, "text")


def format_file_link(file_path):
    """
    파일 경로를 클릭 가능한 로컬 마크다운 링크로 변환합니다.
    """
    if not file_path:
        return ""
    clean_path = str(file_path).strip().strip('"').strip("'")
    normalized = clean_path.replace("\\", "/")
    basename = os.path.basename(normalized) or clean_path
    if not normalized.startswith("file:///"):
        if ":" in normalized:
            uri = f"file:///{normalized}"
        else:
            uri = f"file://{normalized}"
    else:
        uri = normalized
    return f"[`{basename}`]({uri})"


def generate_git_diff(target_content, replacement_content, filename="file"):
    """
    TargetContent와 ReplacementContent 간의 unified Git diff 문자열을 생성합니다.
    """
    target_lines = (target_content or "").splitlines()
    replacement_lines = (replacement_content or "").splitlines()
    
    diff_lines = list(difflib.unified_diff(
        target_lines,
        replacement_lines,
        fromfile=f"a/{os.path.basename(filename) or 'original'}",
        tofile=f"b/{os.path.basename(filename) or 'modified'}",
        lineterm=""
    ))
    
    if not diff_lines:
        res = []
        for l in target_lines:
            res.append(f"- {l}")
        for l in replacement_lines:
            res.append(f"+ {l}")
        return "\n".join(res)
    
    return "\n".join(diff_lines)


def clean_user_content(content):
    """
    사용자 입력 메시지에서 <USER_REQUEST> 본문을 최우선 추출하고,
    부가 메타데이터가 있는 경우 이를 분리하여 반환합니다.
    """
    if not content:
        return "", ""

    if not isinstance(content, str):
        content = str(content)

    match = re.search(r"<USER_REQUEST>\s*(.*?)\s*</USER_REQUEST>", content, re.DOTALL)
    if match:
        main_request = match.group(1).strip()
        rest_meta = content.replace(match.group(0), "").strip()
        return main_request, rest_meta
    
    return content.strip(), ""


def sanitize_filename(text, max_len=25):
    """
    제목 텍스트를 파일명에 적합하도록 정제합니다.
    """
    if not text:
        return "no_title"
    
    main_req, _ = clean_user_content(text)
    if not main_req:
        main_req = text

    sanitized = re.sub(r'[^\w\s\-가-힣a-zA-Z0-9]', '', main_req)
    sanitized = re.sub(r'\s+', '_', sanitized.strip())
    sanitized = sanitized.strip('_')
    
    if not sanitized:
        return "no_title"
    
    return sanitized[:max_len]


def safe_get_str(obj, key=None, default=""):
    """
    안전하게 문자열로 변환합니다.
    """
    if key is not None:
        if not isinstance(obj, dict):
            return default
        val = obj.get(key, default)
    else:
        val = obj

    if val is None:
        return default
    if isinstance(val, list):
        return "\n".join([str(x) for x in val])
    if isinstance(val, (dict, bool, int, float)):
        return str(val)
    return str(val)


def format_iso_time(timestamp_str, time_only=True):
    """
    ISO 8601 타임스탬프 문자열을 보기 좋은 로컬 시간 포맷으로 변환합니다.
    """
    if not timestamp_str:
        return ""
    try:
        dt = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
        local_dt = dt.astimezone()
        if time_only:
            return local_dt.strftime("%H:%M:%S")
        else:
            return local_dt.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return str(timestamp_str)


def detect_format(jsonl_path):
    """
    JSONL 파일의 내용을 분석하여 'claude' 또는 'gemini' 포맷인지 판별합니다.
    """
    if not os.path.exists(jsonl_path):
        return "unknown"
    
    try:
        with open(jsonl_path, "r", encoding="utf-8", errors="replace") as f:
            for i, line in enumerate(f):
                if i > 20:
                    break
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                except Exception:
                    continue

                if not isinstance(data, dict):
                    continue

                mtype = data.get("type")
                source = data.get("source")

                if mtype in ["queue-operation", "attachment", "user", "assistant", "ai-title"]:
                    return "claude"
                if mtype in ["USER_INPUT", "PLANNER_RESPONSE", "TOOL_RESPONSE", "CONVERSATION_HISTORY"] or \
                   source in ["USER_EXPLICIT", "MODEL", "SYSTEM"]:
                    return "gemini"
    except Exception:
        pass
    
    return "gemini"


def extract_session_meta(jsonl_path, log_type):
    """
    JSONL 파일에서 세션 ID, 날짜(YYYY-MM-DD), 플랫폼 태그, 첫 질문 요약 제목을 추출합니다.
    """
    filename = os.path.basename(jsonl_path)
    file_id = os.path.splitext(filename)[0]

    abs_path = os.path.abspath(jsonl_path)
    uuid_match = re.search(r'([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})', abs_path, re.I)
    session_id = uuid_match.group(1) if uuid_match else file_id

    mtime = os.path.getmtime(jsonl_path)
    default_date = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d")
    first_time_full = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")
    
    first_query = ""
    ai_title = ""
    extracted_date = default_date
    project_tag = "claude" if log_type == "claude" else "gemini"

    if "c--Users-" in abs_path:
        proj_part = abs_path.split("c--Users-")[-1].split(os.sep)[0]
        if "GitHub-" in proj_part:
            project_tag = proj_part.split("GitHub-")[-1]
        elif "-" in proj_part:
            project_tag = proj_part.split("-")[-1]

    try:
        with open(jsonl_path, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                except Exception:
                    continue
                if not isinstance(data, dict):
                    continue

                if log_type == "claude":
                    mtype = data.get("type")
                    if mtype == "ai-title":
                        ai_title = data.get("aiTitle", "")
                    elif mtype == "user" and not first_query:
                        msg = data.get("message", {})
                        content_list = msg.get("content", []) if isinstance(msg, dict) else []
                        for item in content_list:
                            if isinstance(item, dict) and item.get("type") == "text":
                                first_query = safe_get_str(item, "text")
                                break
                        ts = data.get("timestamp")
                        if ts:
                            try:
                                dt = datetime.fromisoformat(ts.replace("Z", "+00:00")).astimezone()
                                extracted_date = dt.strftime("%Y-%m-%d")
                                first_time_full = dt.strftime("%Y-%m-%d %H:%M:%S")
                            except Exception:
                                pass
                else:
                    mtype = data.get("type")
                    source = data.get("source")
                    if (mtype == "USER_INPUT" or source == "USER_EXPLICIT") and not first_query:
                        first_query = safe_get_str(data, "content")
                        ca = data.get("created_at")
                        if ca:
                            try:
                                dt = datetime.fromisoformat(ca.replace("Z", "+00:00")).astimezone()
                                extracted_date = dt.strftime("%Y-%m-%d")
                                first_time_full = dt.strftime("%Y-%m-%d %H:%M:%S")
                            except Exception:
                                pass

                if first_query and (log_type != "claude" or ai_title):
                    break
    except Exception as e:
        print(f"[Warning] Error reading session meta from {jsonl_path}: {e}", file=sys.stderr)

    title_source = ai_title if ai_title else first_query
    clean_title = sanitize_filename(title_source)
    if not clean_title or clean_title == "empty_request":
        clean_title = "no_title"

    return {
        "session_id": session_id,
        "date_str": extracted_date,
        "first_time_full": first_time_full,
        "project_tag": project_tag,
        "title": clean_title,
        "log_type": log_type
    }


def format_tool_call_custom(name, args, tool_id=""):
    """
    도구 종류(파일수정, 명령어, 파일조회 등)에 맞추어 Obsidian/GitHub 표준 콜아웃 포맷으로 시각화합니다.
    """
    id_badge = f" `[{tool_id[:8]}]`" if tool_id else ""
    lines = []
    lines.append(f"> [!EXAMPLE] 🔧 Tool Call: `{name}`{id_badge}")
    
    if isinstance(args, str):
        try:
            args = json.loads(args)
        except Exception:
            pass

    if not isinstance(args, dict):
        lines.append(f">\n> ```text\n> {str(args)}\n> ```")
        return "\n".join(lines)

    # 1. 파일 수정 도구 (replace_file_content, Edit, multi_replace_file_content)
    if name in ["replace_file_content", "Edit"]:
        target_file = safe_get_str(args, "TargetFile") or safe_get_str(args, "file_path") or safe_get_str(args, "path")
        instruction = safe_get_str(args, "Instruction")
        desc = safe_get_str(args, "Description")
        target_content = safe_get_str(args, "TargetContent") or safe_get_str(args, "old_string")
        replacement_content = safe_get_str(args, "ReplacementContent") or safe_get_str(args, "new_string")
        
        if target_file:
            lines.append(f"> - **Target File**: {format_file_link(target_file)}")
        if instruction:
            lines.append(f"> - **Instruction**: {instruction}")
        if desc:
            lines.append(f"> - **Description**: {desc}")
            
        if target_content or replacement_content:
            diff_text = generate_git_diff(target_content, replacement_content, target_file)
            lines.append(f">\n> ```diff")
            for l in diff_text.split("\n"):
                lines.append(f"> {l}")
            lines.append(f"> ```")
        return "\n".join(lines)

    elif name == "multi_replace_file_content":
        target_file = safe_get_str(args, "TargetFile")
        instruction = safe_get_str(args, "Instruction")
        chunks = args.get("ReplacementChunks", [])
        if target_file:
            lines.append(f"> - **Target File**: {format_file_link(target_file)}")
        if instruction:
            lines.append(f"> - **Instruction**: {instruction}")
        
        for idx, chunk in enumerate(chunks, 1):
            tc = safe_get_str(chunk, "TargetContent")
            rc = safe_get_str(chunk, "ReplacementContent")
            diff_text = generate_git_diff(tc, rc, target_file)
            lines.append(f">\n> **Chunk {idx} Diff**:")
            lines.append(f"> ```diff")
            for l in diff_text.split("\n"):
                lines.append(f"> {l}")
            lines.append(f"> ```")
        return "\n".join(lines)

    # 2. 파일 생성 도구 (write_to_file, Write)
    elif name in ["write_to_file", "Write"]:
        target_file = safe_get_str(args, "TargetFile") or safe_get_str(args, "file_path") or safe_get_str(args, "path")
        code_content = safe_get_str(args, "CodeContent") or safe_get_str(args, "content")
        desc = safe_get_str(args, "Description")
        lang = get_lang_from_path(target_file)
        
        if target_file:
            lines.append(f"> - **Create File**: {format_file_link(target_file)}")
        if desc:
            lines.append(f"> - **Description**: {desc}")
        if code_content:
            lines.append(f">\n> ```{lang}")
            for l in code_content.split("\n"):
                lines.append(f"> {l}")
            lines.append(f"> ```")
        return "\n".join(lines)

    # 3. 터미널 명령어 실행 (run_command, Bash, PowerShell)
    elif name in ["run_command", "Bash", "PowerShell", "Execute"]:
        cmd = safe_get_str(args, "CommandLine") or safe_get_str(args, "command")
        cwd = safe_get_str(args, "Cwd") or safe_get_str(args, "working_directory")
        desc = safe_get_str(args, "Description") or safe_get_str(args, "toolAction")
        
        if cwd:
            lines.append(f"> - **Working Directory**: `{cwd}`")
        if desc:
            lines.append(f"> - **Action**: {desc}")
        if cmd:
            lines.append(f">\n> ```powershell")
            lines.append(f"> $ {cmd}")
            lines.append(f"> ```")
        return "\n".join(lines)

    # 4. 파일 조회 (view_file, Read, Cat)
    elif name in ["view_file", "Read", "Cat"]:
        path = safe_get_str(args, "AbsolutePath") or safe_get_str(args, "file_path") or safe_get_str(args, "path")
        start = safe_get_str(args, "StartLine") or safe_get_str(args, "offset")
        end = safe_get_str(args, "EndLine") or safe_get_str(args, "limit")
        action = safe_get_str(args, "toolAction") or safe_get_str(args, "description")
        
        if path:
            range_info = f" `(Lines {start}-{end})`" if start and end else ""
            lines.append(f"> - **View Path**: {format_file_link(path)}{range_info}")
        if action:
            lines.append(f"> - **Action**: {action}")
        return "\n".join(lines)

    # 5. 질문 도구 (ask_question)
    elif name == "ask_question":
        questions = args.get("questions", [])
        if isinstance(questions, list):
            for q in questions:
                if isinstance(q, dict):
                    q_text = safe_get_str(q, "question")
                    options = q.get("options", [])
                    lines.append(f"> - ❓ **Question**: {q_text}")
                    if isinstance(options, list):
                        for opt in options:
                            lines.append(f">   - [ ] {str(opt)}")
                else:
                    lines.append(f"> - ❓ **Question**: {str(q)}")
        else:
            lines.append(f"> - ❓ **Question**: {str(questions)}")
        return "\n".join(lines)

    # 6. 일반 도구 (JSON 직렬화)
    else:
        args_str = json.dumps(args, ensure_ascii=False, indent=2)
        lines.append(f">\n> ```json")
        for l in args_str.split("\n"):
            lines.append(f"> {l}")
        lines.append(f"> ```")
        return "\n".join(lines)


def format_tool_response_custom(tool_name, content, status="", is_error=False, tool_id=""):
    """
    도구 응답(Tool Response)을 깔끔한 콜아웃 헤더와 독립 코드 블록으로 렌더링하여
    마크다운 뷰어에서의 깨짐을 100% 방지합니다.
    """
    id_badge = f" `[{tool_id[:8]}]`" if tool_id else ""
    callout_type = "WARNING" if is_error else "INFO"
    title_label = f"⚠️ Tool Error: `{tool_name}`{id_badge}" if is_error else f"📥 Tool Response: `{tool_name}`{id_badge}"
    
    if status:
        title_label += f" *(Status: {status})*"

    lines = []
    lines.append(f"> [!{callout_type}] {title_label}")

    if not content or not str(content).strip():
        lines.append(f"> *(Empty Response)*\n")
        return "\n".join(lines)

    content_str = str(content).strip()
    
    # JSON 문자열 여부 판별
    if (content_str.startswith("{") and content_str.endswith("}")) or \
       (content_str.startswith("[") and content_str.endswith("]")):
        try:
            parsed = json.loads(content_str)
            formatted_json = json.dumps(parsed, ensure_ascii=False, indent=2)
            lines.append(f"\n```json\n{formatted_json}\n```\n")
            return "\n".join(lines)
        except Exception:
            pass

    lang = get_lang_from_path(tool_name) if tool_name and "." in tool_name else "text"
    lines.append(f"\n```{lang}\n{content_str}\n```\n")
    return "\n".join(lines)


def parse_claude_jsonl(jsonl_path, meta):
    """
    Claude Code JSONL 파일을 프리미엄 마크다운으로 변환합니다.
    """
    md = []
    md.append(f"# 💬 AI 대화 로그 (Claude Code)")
    md.append(f"\n> [!INFO] 📋 Session Overview")
    md.append(f"> - **프로젝트**: `{meta['project_tag']}`")
    md.append(f"> - **세션 ID**: `{meta['session_id']}`")
    md.append(f"> - **시작 일시**: `{meta['first_time_full']}`")
    md.append("\n---\n")

    current_tool_names = {}

    with open(jsonl_path, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
            except Exception:
                continue
            if not isinstance(data, dict):
                continue

            msg_type = data.get("type")
            timestamp = data.get("timestamp", "")
            time_str = format_iso_time(timestamp)
            time_badge = f" `[{time_str}]`" if time_str else ""

            if msg_type == "user":
                message = data.get("message", {})
                content_list = message.get("content", []) if isinstance(message, dict) else []
                user_texts = []
                tool_results = []

                for item in content_list:
                    if not isinstance(item, dict):
                        continue
                    itype = item.get("type")
                    if itype == "text":
                        user_texts.append(safe_get_str(item, "text"))
                    elif itype == "tool_result":
                        tool_results.append(item)

                if user_texts:
                    full_text = "\n".join(user_texts)
                    main_req, meta_text = clean_user_content(full_text)
                    md.append(f"## 👤 User{time_badge}\n")
                    if main_req:
                        md.append(main_req)
                        md.append("\n")
                    if meta_text:
                        md.append(f"> [!ABSTRACT] ℹ️ User Metadata / Context")
                        for l in meta_text.strip().split("\n"):
                            md.append(f"> {l}")
                        md.append("\n")

                for tr in tool_results:
                    tool_id = safe_get_str(tr, "tool_use_id")
                    content = safe_get_str(tr, "content")
                    is_error = tr.get("is_error", False)
                    tool_name = current_tool_names.get(tool_id, "tool")
                    
                    md.append(format_tool_response_custom(tool_name, content, is_error=is_error, tool_id=tool_id))
                    md.append("\n")

            elif msg_type == "assistant":
                md.append(f"## 🤖 Assistant{time_badge}\n")
                message = data.get("message", {})
                content_list = message.get("content", []) if isinstance(message, dict) else []

                for item in content_list:
                    if not isinstance(item, dict):
                        continue
                    itype = item.get("type")

                    if itype == "thinking":
                        thinking = safe_get_str(item, "thinking")
                        if thinking:
                            md.append("> [!NOTE] 💭 Thinking")
                            for l in thinking.strip().split("\n"):
                                md.append(f"> {l}")
                            md.append("\n")

                    elif itype == "text":
                        text = safe_get_str(item, "text")
                        if text:
                            md.append(text.strip())
                            md.append("\n\n")

                    elif itype == "tool_use":
                        name = safe_get_str(item, "name", "tool")
                        tool_input = item.get("input", {})
                        tool_id = safe_get_str(item, "id")
                        if tool_id:
                            current_tool_names[tool_id] = name
                        
                        md.append(format_tool_call_custom(name, tool_input, tool_id))
                        md.append("\n")

            elif msg_type == "ai-title":
                ai_title = data.get("aiTitle", "")
                if ai_title:
                    md.append(f"> [!TIP] 🏷️ **AI Title**: {ai_title}\n\n")

            elif msg_type == "attachment":
                attachment = data.get("attachment", {})
                if isinstance(attachment, dict):
                    atype = attachment.get("type")
                    if atype == "command_permissions":
                        allowed = attachment.get("allowedTools", [])
                        md.append(f"> 🛡️ **Permissions**: Allowed `{allowed}`\n\n")

    return "\n".join(md)


def parse_gemini_jsonl(jsonl_path, meta):
    """
    Antigravity (Gemini) JSONL 파일을 프리미엄 마크다운으로 변환합니다.
    """
    md = []
    md.append(f"# 💬 AI 대화 로그 (Antigravity Gemini)")
    md.append(f"\n> [!INFO] 📋 Session Overview")
    md.append(f"> - **Conversation ID**: `{meta['session_id']}`")
    md.append(f"> - **시작 일시**: `{meta['first_time_full']}`")
    md.append("\n---\n")

    last_tool_name = "tool"

    with open(jsonl_path, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
            except Exception:
                continue
            if not isinstance(data, dict):
                continue

            source = data.get("source")
            msg_type = data.get("type")
            content = safe_get_str(data, "content")
            tool_calls = data.get("tool_calls", [])
            created_at = data.get("created_at", "")
            thinking = safe_get_str(data, "thinking")

            time_str = format_iso_time(created_at)
            time_badge = f" `[{time_str}]`" if time_str else ""

            if msg_type == "USER_INPUT" or source == "USER_EXPLICIT":
                main_req, meta_text = clean_user_content(content)
                md.append(f"## 👤 User{time_badge}\n")
                if main_req:
                    md.append(main_req)
                    md.append("\n")
                if meta_text:
                    md.append(f"> [!ABSTRACT] ℹ️ User Metadata / Context")
                    for l in meta_text.strip().split("\n"):
                        md.append(f"> {l}")
                    md.append("\n")

            elif msg_type == "PLANNER_RESPONSE":
                md.append(f"## 🤖 Assistant{time_badge}\n")
                if thinking:
                    md.append("> [!NOTE] 💭 Thinking")
                    for l in thinking.strip().split("\n"):
                        md.append(f"> {l}")
                    md.append("\n")

                if content:
                    md.append(content.strip())
                    md.append("\n\n")

                if tool_calls:
                    for tc in tool_calls:
                        if not isinstance(tc, dict):
                            continue
                        name = tc.get("name", "unknown_tool")
                        args = tc.get("arguments") or tc.get("args") or {}
                        tool_id = tc.get("id") or tc.get("call_id") or ""
                        last_tool_name = name
                        
                        md.append(format_tool_call_custom(name, args, tool_id))
                        md.append("\n")

            elif source == "MODEL" and msg_type != "PLANNER_RESPONSE":
                md.append(format_tool_response_custom(last_tool_name, content, status=msg_type))
                md.append("\n")

            elif msg_type == "TOOL_RESPONSE":
                status = data.get("status", "")
                md.append(format_tool_response_custom(last_tool_name, content, status=status))
                md.append("\n")

            elif source == "SYSTEM" and msg_type != "CONVERSATION_HISTORY":
                if content and "{{ CHECKPOINT" not in content and not content.startswith("{"):
                    md.append(f"> ⚙️ **System**{time_badge}: {content.strip()}\n\n")

    return "\n".join(md)


def process_file(jsonl_path, output_path=None, overwrite=True, verbose=True):
    """
    단일 JSONL 파일을 파싱하여 마크다운 파일로 저장합니다.
    """
    if not os.path.exists(jsonl_path):
        print(f"❌ [Error] Input file not found: {jsonl_path}", file=sys.stderr)
        return False, None

    log_type = detect_format(jsonl_path)
    meta = extract_session_meta(jsonl_path, log_type)

    if log_type == "claude":
        md_content = parse_claude_jsonl(jsonl_path, meta)
        tag = f"[{meta['project_tag']}]"
    else:
        md_content = parse_gemini_jsonl(jsonl_path, meta)
        tag = "[gemini]"

    short_id = meta['session_id'][:8]
    auto_filename = f"{meta['date_str']}-{tag}-{meta['title']}_{short_id}.md"

    if output_path:
        if os.path.isdir(output_path) or output_path.endswith(("\\", "/")):
            os.makedirs(output_path, exist_ok=True)
            target_md_path = os.path.join(output_path, auto_filename)
        else:
            parent_dir = os.path.dirname(output_path)
            if parent_dir:
                os.makedirs(parent_dir, exist_ok=True)
            target_md_path = output_path
    else:
        parent_dir = os.path.dirname(jsonl_path) or "."
        parent_basename = os.path.basename(os.path.abspath(parent_dir)).lower()
        if parent_basename == "raw":
            # chats/raw/ -> chats/md/ 자동 매핑
            md_sibling = os.path.join(os.path.dirname(os.path.abspath(parent_dir)), "md")
            os.makedirs(md_sibling, exist_ok=True)
            target_md_path = os.path.join(md_sibling, auto_filename)
        else:
            target_md_path = os.path.join(parent_dir, auto_filename)

    if os.path.exists(target_md_path) and not overwrite:
        if verbose:
            print(f"⏩ [Skip] Target already exists: {target_md_path}")
        return True, target_md_path

    try:
        with open(target_md_path, "w", encoding="utf-8") as f:
            f.write(md_content)
        if verbose:
            print(f"✅ [Parsed] {os.path.basename(jsonl_path)} -> {target_md_path}")
        return True, target_md_path
    except Exception as e:
        print(f"❌ [Error] Failed to write {target_md_path}: {e}", file=sys.stderr)
        return False, None


def process_directory(dir_path, output_dir=None, overwrite=True, max_workers=8):
    """
    지정된 디렉토리 내의 모든 .jsonl 파일을 스캔하여 병렬 일괄 파싱합니다.
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed

    if not os.path.isdir(dir_path):
        print(f"❌ [Error] Directory not found: {dir_path}", file=sys.stderr)
        return 0, 0

    jsonl_files = [
        os.path.join(dir_path, f)
        for f in os.listdir(dir_path)
        if f.lower().endswith(".jsonl") and not f.startswith(".")
    ]

    total_files = len(jsonl_files)
    if not total_files:
        print(f"ℹ️ No .jsonl files found in {dir_path}")
        return 0, 0

    print(f"🚀 Found {total_files} JSONL files in '{dir_path}'. Starting parallel batch parsing (workers={max_workers})...")
    success_count = 0
    fail_count = 0

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_file = {
            executor.submit(process_file, jf, output_dir, overwrite, False): jf
            for jf in jsonl_files
        }
        for idx, future in enumerate(as_completed(future_to_file), 1):
            jf = future_to_file[future]
            try:
                ok, _ = future.result()
                if ok:
                    success_count += 1
                else:
                    fail_count += 1
            except Exception as e:
                print(f"❌ [Error] Exception processing {os.path.basename(jf)}: {e}", file=sys.stderr)
                fail_count += 1

            if idx % 50 == 0 or idx == total_files:
                print(f"⏳ Progress: {idx}/{total_files} files processed ({success_count} succeeded, {fail_count} failed)...")

    print(f"\n✨ Premium batch parsing complete: {success_count} succeeded, {fail_count} failed.")
    return success_count, fail_count


def main():
    parser = argparse.ArgumentParser(
        description="Claude Code & Antigravity (Gemini) JSONL Premium Markdown Chat Parser"
    )
    parser.add_argument(
        "target",
        nargs="?",
        help="Path to a .jsonl file or a directory containing .jsonl files"
    )
    parser.add_argument(
        "-f", "--file",
        help="Explicit path to a single .jsonl file"
    )
    parser.add_argument(
        "-d", "--dir",
        help="Explicit path to a directory of .jsonl files"
    )
    parser.add_argument(
        "-o", "--output",
        help="Output file path (for single file) or output directory path"
    )
    parser.add_argument(
        "--no-overwrite",
        action="store_true",
        help="Do not overwrite existing output files"
    )

    args = parser.parse_args()
    overwrite = not args.no_overwrite

    target_path = args.file or args.dir or args.target

    if not target_path:
        parser.print_help()
        sys.exit(1)

    if os.path.isdir(target_path):
        process_directory(target_path, output_dir=args.output, overwrite=overwrite)
    elif os.path.isfile(target_path):
        process_file(target_path, output_path=args.output, overwrite=overwrite)
    else:
        print(f"❌ [Error] Invalid path: {target_path}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
