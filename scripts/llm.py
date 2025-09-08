#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json, os, subprocess, sys, textwrap, urllib.request

# ==== ここに自分のキーを直書き（PoC用）====
OPENAI_API_KEY = "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"
OPENAI_MODEL = "gpt-4o-mini"  # 速くて安い系。好みで変更OK
# ==========================================

def run(cmd):
    return subprocess.check_output(cmd, text=True).strip()

def gh_issue_body(num: str) -> tuple[str, str]:
    # gh CLI から Issue の title/body を取得
    out = run(["gh", "issue", "view", num, "--json", "title,body"])
    j = json.loads(out)
    return j.get("title",""), j.get("body","")

def repo_snapshot(max_bytes_per_file=4000) -> str:
    files = run(["git", "ls-files"]).splitlines()
    parts = ["# REPO TREE", *files, "", "# FILE SNIPPETS"]
    for f in files:
        try:
            with open(f, "r", encoding="utf-8", errors="ignore") as fp:
                data = fp.read(max_bytes_per_file)
            parts.append(f"\n[[FILE:{f}]]\n{data}\n[[/FILE]]")
        except Exception:
            continue
    return "\n".join(parts)

def call_openai(messages: list[dict]) -> str:
    req = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json",
        },
        data=json.dumps({
            "model": OPENAI_MODEL,
            "messages": messages,
            "temperature": 0.2,
            "response_format": { "type": "text" },
        }).encode("utf-8"),
        method="POST",
    )
    with urllib.request.urlopen(req) as resp:
        j = json.loads(resp.read())
    content = j["choices"][0]["message"]["content"]
    return content

def strip_markdown_fence(text: str) -> str:
    t = text.strip()
    if t.startswith("```"):
        # ```diff や ```patch にも対応
        lines = t.splitlines()
        # 1行目の ```xxx を落とし、末尾 ``` を落とす
        if len(lines) >= 2 and lines[-1].strip().startswith("```"):
            return "\n".join(lines[1:-1]).strip() + "\n"
    return t if t.endswith("\n") else t + "\n"

def main():
    if len(sys.argv) < 2:
        print("Usage: llm.py <issue_number>", file=sys.stderr)
        sys.exit(2)
    issue_no = sys.argv[1]

    title, body = gh_issue_body(issue_no)
    snapshot = repo_snapshot()

    system = textwrap.dedent("""
        You are a code patch generator bot.
        Output MUST be a unified diff (git patch) that applies cleanly with `git apply --index`.
        - Base is current repository state provided.
        - If file does not exist, create it in the patch.
        - Keep patch minimal and focused on the issue.
        - Use LF line endings. No trailing binary blobs.
        - Do not include explanations. Output patch only.
    """).strip()

    user = f"""Issue #{issue_no}: {title}

SPEC (from GitHub issue body):
{body}

REPOSITORY SNAPSHOT:
{snapshot}
"""

    patch = call_openai([
        {"role":"system","content":system},
        {"role":"user","content":user},
    ])

    # Markdownフェンスを外して標準出力へ
    print(strip_markdown_fence(patch), end="")

if __name__ == "__main__":
    main()
