#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import socket
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_MD = ROOT / "AUDIT_REPORT.md"
OUT_JSON = ROOT / "audit_report.json"

expected_top = [
    "🚀 Core System & Entry Points",
    "⚙️ Configuration Center",
    "🔧 Core Engine",
    "📚 Enhanced RAG & Knowledge Graph",
    "💼 Intelligent ERP & Business Management",
    "📈 Intelligent Stock Trading",
    "🎨 Intelligent Content Creation",
    "🔍 Intelligent Trend Analysis",
    "🤖 Intelligent Task Agent",
    "💬 Intelligent OpenWebUI Interaction Center",
    "🛠️ Intelligent System Resource Management",
    "🐳 Intelligent Docker Containerization",
    "📖 Intelligent Documentation & Testing",
    "extensions",
    "plugins",
    "scripts",
    "models",
    ".vscode",
]

key_checks = {
    "📚 Enhanced RAG & Knowledge Graph": [
        "api/app.py",
        "core",
        "pipelines",
        "knowledge_graph",
    ],
    ".vscode": [
        "settings.json",
    ],
    "models": [
        "all-MiniLM-L6-v2",
        "all-MiniLM-L6-v2/modules.json",
        "all-MiniLM-L6-v2/1_Pooling",
        "all-MiniLM-L6-v2/0_Transformer",
    ],
    "scripts": [
        "dev.sh",
        "smoke.sh",
        "scaffold_minimal.py",
        "audit_repo.py",
    ],
}


def path_exists(rel: str) -> bool:
    return (ROOT / rel).exists()


def service_alive(host="127.0.0.1", port=8011, timeout=0.3) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def http_json(url: str, timeout=1.0):
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8", errors="ignore"))
    except urllib.error.HTTPError as e:
        return {"status": e.code, "error": str(e)}
    except Exception as e:
        return {"error": str(e)}


def main():
    report = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "root": str(ROOT),
        "top_dirs": {},
        "key_checks": {},
        "service": {},
        "notes": [],
    }

    # 顶层目录覆盖率
    for name in expected_top:
        report["top_dirs"][name] = path_exists(name)

    # 关键路径检查
    for base, items in key_checks.items():
        base_ok = path_exists(base)
        details = {}
        for item in items:
            rel = f"{base}/{item}"
            details[rel] = path_exists(rel)
        report["key_checks"][base] = {"exists": base_ok, "items": details}

    # 服务探测
    alive = service_alive()
    report["service"]["port_8011_alive"] = alive
    if alive:
        report["service"]["api_probe"] = try_api()
    else:
        report["service"]["api_probe"] = {"error": "server not listening on :8011"}

    # 结论摘要（优先级）
    gaps = []
    # 顶层模块
    for name, ok in report["top_dirs"].items():
        if not ok:
            gaps.append(f"缺少顶层模块目录: {name}")
    # RAG&KG关键文件
    rag_key = report["key_checks"].get("📚 Enhanced RAG & Knowledge Graph", {})
    for rel, ok in rag_key.get("items", {}).items():
        if not ok:
            gaps.append(f"RAG&KG 缺少关键路径: {rel}")
    # scripts
    scripts_key = report["key_checks"].get("scripts", {})
    for rel, ok in scripts_key.get("items", {}).items():
        if not ok:
            gaps.append(f"缺少脚本: {rel}")
    # models
    if (
        not report["key_checks"]
        .get("models", {})
        .get("items", {})
        .get("models/all-MiniLM-L6-v2", False)
    ):
        gaps.append("缺少本地 ST 模型目录: models/all-MiniLM-L6-v2（已配置可忽略）")

    # 服务状态
    if report["service"]["port_8011_alive"]:
        api = report["service"]["api_probe"]
        if isinstance(api, dict):
            ready = api.get("readyz", {}).get("ready", False)
            st_ok = api.get("readyz", {}).get("st_model", False)
            if not ready:
                gaps.append("服务 /readyz 未就绪")
            if not st_ok:
                gaps.append("服务未加载 SentenceTransformers 模型")
    else:
        gaps.append("uvicorn 未监听 8011 端口")

    report["summary_gaps"] = gaps
    report["ok"] = len(gaps) == 0

    # 写 JSON
    OUT_JSON.write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    # 写 Markdown
    lines = []
    lines.append(f"# 仓库审计报告（自动生成）")
    lines.append(f"- 时间: {report['timestamp']}")
    lines.append(f"- 根目录: {report['root']}")
    lines.append("")
    lines.append("## 顶层模块覆盖")
    for name, ok in report["top_dirs"].items():
        lines.append(f"- {name}: {'✓' if ok else '✗'}")
    lines.append("")
    lines.append("## 关键路径检查")
    for base, data in report["key_checks"].items():
        lines.append(f"- {base}: {'✓' if data.get('exists') else '✗'}")
        for rel, ok in data.get("items", {}).items():
            lines.append(f"  - {rel}: {'✓' if ok else '✗'}")
    lines.append("")
    lines.append("## 服务探测")
    lines.append(
        f"- 8011 端口: {'在线' if report['service']['port_8011_alive'] else '离线'}"
    )
    if isinstance(report["service"]["api_probe"], dict):
        rp = report["service"]["api_probe"]
        lines.append(
            f"  - /readyz: {json.dumps(rp.get('readyz', {}), ensure_ascii=False)}"
        )
        lines.append(
            f"  - /index/info: {json.dumps(rp.get('index_info', {}), ensure_ascii=False)}"
        )
        lines.append(
            f"  - /kg/stats: {json.dumps(rp.get('kg_stats', {}), ensure_ascii=False)}"
        )
    lines.append("")
    lines.append("## 差距与优先级")
    if gaps:
        for g in gaps:
            lines.append(f"- [ ] {g}")
    else:
        lines.append("- [x] 当前关键项均满足")
    lines.append("")
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")

    print(f"OK: 生成 {OUT_JSON} 与 {OUT_MD}")
    if gaps:
        print("发现差距项：")
        for g in gaps:
            print(" -", g)


if __name__ == "__main__":
    if not ROOT.exists():
        print(f"路径不存在: {ROOT}", file=sys.stderr)
        sys.exit(1)
    main()
