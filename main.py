from html.parser import HTMLParser
import os
from pathlib import Path
import re
import subprocess
from dotenv import load_dotenv
import anthropic
import urllib
import yaml
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


from api.routes import creat_router

load_dotenv()

api_key = os.environ["ANTHROPIC_API_KEY"]
base_url = os.environ["ANTHROPIC_BASE_URL"]

ROOT = Path(__file__).resolve().parents[0]
SKILLS_DIR = ROOT / "skills"
print(SKILLS_DIR)


class SkillLoader:

    def __init__(self, skills_dir: Path):
        self.skills_dir = skills_dir
        self.skills = {}
        self._load_all()

    def _load_all(self):
        if not self.skills_dir.exists():
            return
        for f in sorted(self.skills_dir.rglob("SKILL.md")):
            text = f.read_text(encoding='utf-8')
            meta, body = self._parse_frontmatter(text)
            name = meta.get("name", f.parent.name)
            self.skills[name] = {"meta": meta, "body": body, "path": str(f)}

    def _parse_frontmatter(self, text: str) -> tuple:
        match = re.match(r"^---\n(.*?)\n---\n(.*)", text, re.DOTALL)
        if not match:
            return {}, text
        try:
            meta = yaml.safe_load(match.group(1)) or {}
        except yaml.YAMLError:
            meta = {}
        return meta, match.group(2).strip()

    def get_descriptions(self) -> str:
        if not self.skills:
            print("没有")
            return "(no skills available)"
        lines = []
        for name, skill in self.skills.items():
            desc = skill["meta"].get("description", "No description")
            tags = skill["meta"].get("tags", "")
            line = f"  - {name}: {desc}"
            if tags:
                line += f" [{tags}]"
            lines.append(line)
        return "\n".join(lines)

    def get_content(self, name: str) -> str:
        skill = self.skills.get(name)
        if not skill:
            return f"Error: Unknown skill '{name}'. Available: {', '.join(self.skills.keys())}"
        return f'<skill name="{name}">\n{skill["body"]}\n</skill>'


SKILL_LOADER = SkillLoader(SKILLS_DIR)
SYSTEM_PROMPT = f"""
                你是一个伺候我多年的佣人,
                对我的称呼是皇上,
                用中文回答我的问题,
                遇到不熟悉的专题时，请先调用 load_skill 工具加载对应的知识，再给出回答。
                当前可用技能：
                {SKILL_LOADER.get_descriptions()}
                """

TOOLS = [{
    "name": "run_command",
    "description": "在 Windows 终端执行一条 shell 命令并返回结果",
    "input_schema": {
        "type": "object",
        "properties": {
            "command": {
                "type": "string",
                "description": "要执行的shell命令"
            }
        },
        "required": ["command"]
    }
}, {
    "name": "web_fetch",
    "description": "获取指定 URL 的网页内容，支持文本提取模式",
    "input_schema": {
        "type": "object",
        "properties": {
            "url": {
                "type": "string",
                "description": "要访问的完整 URL"
            },
            "extract_mode": {
                "type": "string",
                "description": "提取模式：text（纯文本，默认）或 raw（原始 HTML）"
            },
            "max_chars": {
                "type": "integer",
                "description": "最大返回字符数，默认 8000"
            }
        },
        "required": ["url"]
    }
}, {
    "name": "load_skill",
    "description": "加载指定技能的详细知识内容，在回答相关问题前调用",
    "input_schema": {
        "type": "object",
        "properties": {
            "skill_name": {
                "type": "string",
                "description": "技能名称，必须是系统提示中列出的可用技能之一"
            }
        },
        "required": ["skill_name"]
    }
}]


class _TextExtractor(HTMLParser):

    def __init__(self):
        super().__init__()
        self._parts = []
        self._skip = False

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"):
            self._skip = True

    def handle_endtag(self, tag):
        if tag in ("script", "style"):
            self._skip = False
        if tag in ("p", "br", "div", "li", "tr", "h1", "h2", "h3", "h4"):
            self._parts.append("\n")

    def handle_data(self, data):
        if not self._skip:
            self._parts.append(data)

    def get_text(self):
        return re.sub(r"\n{3,}", "\n\n", "".join(self._parts)).strip()


def run_command(command: str):
    result = subprocess.run(command,
                            shell=True,
                            capture_output=True,
                            text=True)
    return result.stdout or result.stderr


def web_fetch(url: str,
              extract_mode: str = "text",
              max_chars: int = 8000) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
    except Exception as e:
        return f"Error fetching {url}: {e}"

    if extract_mode == "text":
        parser = _TextExtractor()
        parser.feed(raw)
        text = parser.get_text()
    else:
        text = raw

    return text[:max_chars]


client = anthropic.Anthropic(api_key=api_key, base_url=base_url)



def creat_app()-> FastAPI:

    app = FastAPI(title="小杰Agent", description="一个基于Anthropic API的智能助手", version="1.0.0")
    app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=False, allow_methods=["*"], allow_headers=["*"])
    app.include_router(creat_router(agent_provider=client), prefix="")


# history = []
# while True:
#     msg = input("给公公下一道圣旨:")
#     if msg in ("exit", "quit"):
#         break
#     history.append({"role": "user", "content": msg})
#     while True:
#         response = client.messages.create(model="deepseek-v4-flash",
#                                           max_tokens=1024,
#                                           system=SYSTEM_PROMPT,
#                                           tools=TOOLS,
#                                           messages=history)
#         history.append({"role": "assistant", "content": response.content})

#         if response.stop_reason != "tool_use":
#             reply = next(content.text for content in response.content
#                          if content.type == 'text')
#             print(f"公公给的答复是:{reply}")
#             break

#         tool_results = []  # 存储工具执行结果

#         for block in response.content:
#             if block.type != "tool_use":
#                 continue
#             if block.type == "tool_use":
#                 tool_name = block.name
#                 tool_input = block.input
#                 if tool_name == 'run_command':
#                     command = tool_input['command']
#                     print(f"[执行命令]:{command}")
#                     output = run_command(command=command)
#                     print(f"📤 命令输出:\n{output}")
#                     content = output

#                 elif tool_name == "web_fetch":
#                     url = tool_input["url"]
#                     mode = tool_input.get("extract_mode", "text")
#                     max_chars = tool_input.get("max_chars", 8000)
#                     print(f"[网页获取]: {url}")
#                     content = web_fetch(url, mode, max_chars)
#                 elif tool_name == "load_skill":
#                     skill_name = tool_input["skill_name"]
#                     print(f"[加载技能]: {skill_name}")
#                     content = SKILL_LOADER.get_content(skill_name)
#                 else:
#                     raise ValueError(f"未知工具:{tool_name}")
#                 tool_results.append({
#                     "type": "tool_result",
#                     "tool_use_id": block.id,
#                     "content": content
#                 })
#         history.append({"role": "user", "content": tool_results})
