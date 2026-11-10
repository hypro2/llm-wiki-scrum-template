import os
import sys
import json
import shutil
import re
from datetime import datetime

def get_scrum_dir():
    # Detect relative scrum directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    scrum_cand = os.path.abspath(os.path.join(script_dir, "..", "..", "..", "..", "..", "my_scrum-template"))
    if not os.path.exists(scrum_cand):
        scrum_cand = os.path.abspath(os.path.join(script_dir, "..", "..", "..", "..", "..", "my_scrum"))
    candidate_dirs = [scrum_cand] if os.path.exists(scrum_cand) else [os.getcwd()]
    for d in candidate_dirs:
        if os.path.exists(d):
            return d
    return os.getcwd()

def clean_user_content(content):
    if not content:
        return ""
    # Extract <USER_REQUEST> content if present
    match = re.search(r"<USER_REQUEST>\s*(.*?)\s*</USER_REQUEST>", content, re.DOTALL)
    if match:
        return match.group(1).strip()
    return content.strip()

def sanitize_filename(text):
    if not text:
        return "empty_request"
    text = clean_user_content(text)
    sanitized = re.sub(r'[^\w\s\-가-힣a-zA-Z0-9]', '', text)
    sanitized = re.sub(r'\s+', '_', sanitized.strip())
    return sanitized[:20]

def extract_project_name(dir_name):
    if "GitHub-" in dir_name:
        return dir_name.split("GitHub-")[-1]
    elif "antigravity-" in dir_name:
        return dir_name.split("antigravity-")[-1]
    return dir_name.split("-")[-1]

def safe_get_str(obj, key):
    if not isinstance(obj, dict):
        return ""
    res = obj.get(key)
    if isinstance(res, list):
        return "\n".join([str(x) for x in res])
    return str(res) if res is not None else ""

def format_tool_calls(tool_calls):
    if not tool_calls:
        return ""
    formatted = []
    for tc in tool_calls:
        if not isinstance(tc, dict):
            continue
        name = tc.get("name", "unknown_tool")
        args = tc.get("arguments", {})
        args_str = json.dumps(args, ensure_ascii=False, indent=2)
        formatted.append(f"> 🔧 **Tool Call**: `{name}`\n> ```json\n> {args_str}\n> ```")
    return "\n\n".join(formatted)

def parse_gemini_jsonl(jsonl_path, conv_id):
    md_lines = []
    md_lines.append(f"# 💬 AI 대화 로그 (Gemini)")
    md_lines.append(f"- **Conversation ID**: `{conv_id}`")
    md_lines.append("\n---\n")

    with open(jsonl_path, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            if not line.strip():
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

            time_str = ""
            if created_at:
                try:
                    dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                    time_str = dt.astimezone().strftime("%H:%M:%S")
                except Exception:
                    time_str = created_at

            time_badge = f" `[{time_str}]`" if time_str else ""

            if msg_type == "USER_INPUT" or source == "USER_EXPLICIT":
                clean_text = clean_user_content(content)
                md_lines.append(f"## 👤 User{time_badge}\n")
                md_lines.append(clean_text)
                md_lines.append("\n")
            elif msg_type == "PLANNER_RESPONSE":
                md_lines.append(f"## 🤖 Assistant{time_badge}\n")
                if thinking:
                    md_lines.append(f"<details>\n<summary>💭 생각 과정 보기</summary>\n\n{thinking.strip()}\n\n</details>\n")
                if content:
                    md_lines.append(content.strip())
                    md_lines.append("\n")
                if tool_calls:
                    md_lines.append(format_tool_calls(tool_calls))
                    md_lines.append("\n")
            elif source == "MODEL" and msg_type != "PLANNER_RESPONSE":
                md_lines.append(f"> 📥 **Tool Response ({msg_type})**\n")
                if content:
                    truncated = content[:1000] + "\n... [Truncated]" if len(content) > 1000 else content
                    indented = "\n".join([f"> {l}" for l in truncated.strip().split("\n")])
                    md_lines.append(indented)
                md_lines.append("\n")
            elif msg_type == "TOOL_RESPONSE":
                status = data.get("status", "")
                md_lines.append(f"> 📥 **Tool Response** (Status: {status})\n")
                if content:
                    truncated = content[:1000] + "\n... [Truncated]" if len(content) > 1000 else content
                    indented = "\n".join([f"> {l}" for l in truncated.strip().split("\n")])
                    md_lines.append(indented)
                md_lines.append("\n")
            elif source == "SYSTEM" and msg_type != "CONVERSATION_HISTORY":
                if content and "{{ CHECKPOINT" not in content:
                    md_lines.append(f"> ⚙️ **System**{time_badge}: {content.strip()}\n")

    return "\n".join(md_lines)

def parse_claude_jsonl(jsonl_path, conv_id, project_name):
    md_lines = []
    md_lines.append(f"# 💬 AI 대화 로그 (Claude Code)")
    md_lines.append(f"- **Project**: `{project_name}`")
    md_lines.append(f"- **Session ID**: `{conv_id}`")
    md_lines.append("\n---\n")

    with open(jsonl_path, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                data = json.loads(line)
            except Exception:
                continue

            if not isinstance(data, dict):
                continue

            msg_type = data.get("type")
            timestamp = data.get("timestamp", "")
            
            time_str = ""
            if timestamp:
                try:
                    dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                    time_str = dt.astimezone().strftime("%H:%M:%S")
                except Exception:
                    time_str = timestamp
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
                    clean_text = clean_user_content("\n".join(user_texts))
                    if clean_text:
                        md_lines.append(f"## 👤 User{time_badge}\n")
                        md_lines.append(clean_text)
                        md_lines.append("\n")
                
                for tr in tool_results:
                    tool_id = safe_get_str(tr, "tool_use_id")
                    content = safe_get_str(tr, "content")
                    is_error = tr.get("is_error", False) if isinstance(tr, dict) else False
                    error_badge = " (Error)" if is_error else ""
                    md_lines.append(f"> 📥 **Tool Response{error_badge}** (ID: `{tool_id[:8]}`)\n")
                    if content:
                        truncated = content[:1000] + "\n... [Truncated]" if len(content) > 1000 else content
                        indented = "\n".join([f"> {l}" for l in truncated.strip().split("\n")])
                        md_lines.append(indented)
                    md_lines.append("\n")

            elif msg_type == "assistant":
                md_lines.append(f"## 🤖 Assistant{time_badge}\n")
                message = data.get("message", {})
                content_list = message.get("content", []) if isinstance(message, dict) else []
                
                for item in content_list:
                    if not isinstance(item, dict):
                        continue
                    itype = item.get("type")
                    if itype == "thinking":
                        thinking = safe_get_str(item, "thinking")
                        if thinking:
                            md_lines.append(f"<details>\n<summary>💭 생각 과정 보기</summary>\n\n{thinking.strip()}\n\n</details>\n")
                    elif itype == "text":
                        text = safe_get_str(item, "text")
                        if text:
                            md_lines.append(text.strip())
                            md_lines.append("\n")
                    elif itype == "tool_use":
                        name = safe_get_str(item, "name")
                        tool_input = item.get("input", {}) if isinstance(item, dict) else {}
                        tool_id = safe_get_str(item, "id")
                        input_str = json.dumps(tool_input, ensure_ascii=False, indent=2)
                        md_lines.append(f"> 🔧 **Tool Call**: `{name}` (ID: `{tool_id[:8]}`)\n> ```json\n> {input_str}\n> ```\n")

            elif msg_type == "ai-title":
                ai_title = data.get("aiTitle", "")
                if ai_title:
                    md_lines.append(f"> 🏷️ **AI Title**: {ai_title}\n")
            elif msg_type == "attachment":
                attachment = data.get("attachment", {})
                if isinstance(attachment, dict):
                    atype = attachment.get("type")
                    if atype == "command_permissions":
                        allowed = attachment.get("allowedTools", [])
                        md_lines.append(f"> 🛡️ **Permissions**: Allowed {allowed}\n")

    return "\n".join(md_lines)

def detect_format(jsonl_path):
    if not os.path.exists(jsonl_path):
        return "unknown"
    try:
        with open(jsonl_path, "r", encoding="utf-8", errors="replace") as f:
            for i, line in enumerate(f):
                if i > 5:
                    break
                if not line.strip():
                    continue
                data = json.loads(line)
                if not isinstance(data, dict):
                    continue
                mtype = data.get("type")
                source = data.get("source")
                if mtype in ["queue-operation", "attachment", "user", "assistant", "ai-title"]:
                    return "claude"
                if mtype in ["USER_INPUT", "PLANNER_RESPONSE", "TOOL_RESPONSE"] or source in ["USER_EXPLICIT", "MODEL", "SYSTEM"]:
                    return "gemini"
    except Exception:
        pass
    return "gemini"

def get_claude_session_info(jsonl_path, default_date):
    first_input = ""
    date_str = default_date

    if not os.path.exists(jsonl_path):
        return date_str, "empty"

    try:
        with open(jsonl_path, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    data = json.loads(line)
                except Exception:
                    continue
                
                if not isinstance(data, dict):
                    continue

                if data.get("type") == "user":
                    message = data.get("message", {})
                    content_list = message.get("content", []) if isinstance(message, dict) else []
                    for item in content_list:
                        if isinstance(item, dict) and item.get("type") == "text":
                            first_input = safe_get_str(item, "text")
                            break
                    
                    timestamp = data.get("timestamp", "")
                    if timestamp:
                        try:
                            dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                            date_str = dt.astimezone().strftime("%Y-%m-%d")
                        except Exception:
                            pass
                    break
    except Exception as e:
        print(f"Error reading Claude log {jsonl_path}: {e}")

    title = sanitize_filename(first_input)
    return date_str, title

def get_gemini_session_info(jsonl_path, default_date):
    first_input = ""
    date_str = default_date

    if not os.path.exists(jsonl_path):
        return date_str, "empty"

    try:
        with open(jsonl_path, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    data = json.loads(line)
                except Exception:
                    continue
                
                if not isinstance(data, dict):
                    continue

                if data.get("type") == "USER_INPUT" or data.get("source") == "USER_EXPLICIT":
                    first_input = safe_get_str(data, "content")
                    created_at = data.get("created_at", "")
                    if created_at:
                        try:
                            dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                            date_str = dt.astimezone().strftime("%Y-%m-%d")
                        except Exception:
                            pass
                    break
    except Exception as e:
        print(f"Error reading Gemini log {jsonl_path}: {e}")

    title = sanitize_filename(first_input)
    return date_str, title

def find_session_file(conv_id):
    user_home = os.path.expanduser("~")
    
    # 1. Search in Gemini Antigravity
    brain_dir = os.path.join(user_home, ".gemini", "antigravity", "brain", conv_id)
    logs_dir = os.path.join(brain_dir, ".system_generated", "logs")
    jsonl_src = os.path.join(logs_dir, "transcript_full.jsonl")
    if not os.path.exists(jsonl_src):
        jsonl_src = os.path.join(logs_dir, "transcript.jsonl")
    
    if os.path.exists(jsonl_src):
        return jsonl_src, "gemini", "gemini"

    # 2. Search in Claude Code Projects
    claude_projects_dir = os.path.join(user_home, ".claude", "projects")
    if os.path.exists(claude_projects_dir):
        for proj in os.listdir(claude_projects_dir):
            proj_path = os.path.join(claude_projects_dir, proj)
            if not os.path.isdir(proj_path):
                continue
            target_file = os.path.join(proj_path, f"{conv_id}.jsonl")
            if os.path.exists(target_file):
                proj_name = extract_project_name(proj)
                return target_file, "claude", proj_name

    return None, None, None

def main():
    conv_id = None
    for i, arg in enumerate(sys.argv):
        if arg == "--conv-id" and i + 1 < len(sys.argv):
            conv_id = sys.argv[i + 1]
            break

    if not conv_id:
        print("Error: --conv-id is required.")
        sys.exit(1)

    jsonl_src, log_type, project_tag = find_session_file(conv_id)
    if not jsonl_src:
        print(f"Error: Chat log for conversation ID {conv_id} not found.")
        sys.exit(1)

    scrum_dir = get_scrum_dir()
    chats_dir = os.path.join(scrum_dir, "chats")
    os.makedirs(chats_dir, exist_ok=True)

    mtime = os.path.getmtime(jsonl_src)
    fallback_date = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d")

    if log_type == "claude":
        date_str, title = get_claude_session_info(jsonl_src, fallback_date)
        tag = f"[{project_tag}]"
    else:
        date_str, title = get_gemini_session_info(jsonl_src, fallback_date)
        tag = "[gemini]"

    if not title or title.strip() == "_" or title == "empty_request":
        title = "no_title"

    base_name = f"{date_str}-{tag}-{title}"
    dest_jsonl = os.path.join(chats_dir, f"{base_name}.jsonl")
    dest_md = os.path.join(chats_dir, f"{base_name}.md")

    if os.path.exists(dest_jsonl) or os.path.exists(dest_md):
        short_id = conv_id[:8]
        base_name = f"{date_str}-{tag}-{title}_{short_id}"
        dest_jsonl = os.path.join(chats_dir, f"{base_name}.jsonl")
        dest_md = os.path.join(chats_dir, f"{base_name}.md")

    # Copy raw JSONL
    try:
        shutil.copy2(jsonl_src, dest_jsonl)
        print(f"Successfully backed up raw JSONL to {dest_jsonl}")
    except Exception as e:
        print(f"Failed to copy JSONL: {e}")

    # Parse and write MD
    try:
        if log_type == "claude":
            md_content = parse_claude_jsonl(jsonl_src, conv_id, project_tag)
        else:
            md_content = parse_gemini_jsonl(jsonl_src, conv_id)

        with open(dest_md, "w", encoding="utf-8") as f:
            f.write(md_content)
        print(f"Successfully generated Markdown chat log at {dest_md}")
    except Exception as e:
        print(f"Failed to generate Markdown chat log: {e}")

if __name__ == "__main__":
    main()
