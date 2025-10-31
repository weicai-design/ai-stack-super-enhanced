from __future__ import annotations

import json
import re
from collections import deque
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

EMAIL_RE = re.compile(r"([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,})")
URL_RE = re.compile(r"(https?://[^\s)>\]}\"']+)")


class SimpleKGWriter:
    """
    轻量级 KG 写入器：只用正则抽取 email 与 url，内存态管理，支持快照/保存/清理/加载。
    设计目标是满足测试用例，不依赖外部 NLP 库。
    """

    def __init__(self) -> None:
        self.entities: Dict[str, Dict[str, Any]] = {}  # key -> {id,type,count}
        self.edges: List[Dict[str, str]] = []  # {src,dst,type}
        self.docs: Dict[str, Dict[str, Any]] = {}  # doc_id -> meta/path

    def _add_edge_once(self, src: str, dst: str, etype: str) -> None:
        for e in self.edges:
            if e["src"] == src and e["dst"] == dst and e["type"] == etype:
                return
        self.edges.append({"src": src, "dst": dst, "type": etype})

    def _add_entity(self, ent_id: str, ent_type: str) -> Dict[str, Any]:
        ent = self.entities.setdefault(
            ent_id, {"id": ent_id, "type": ent_type, "count": 0}
        )
        ent["count"] += 1
        return ent

    def _domain_from_email(self, email: str) -> Optional[str]:
        parts = email.split("@", 1)
        return parts[1].lower() if len(parts) == 2 else None

    def _domain_from_url(self, url: str) -> Optional[str]:
        try:
            host = urlparse(url).hostname or ""
            return host.lower() or None
        except Exception:
            return None

    def add_text(
        self,
        text: str,
        doc_id: Optional[str] = None,
        meta: Optional[Dict[str, Any]] = None,
    ) -> None:
        if not text:
            return
        doc_id = doc_id or f"doc-{len(self.docs)+1}"
        if doc_id not in self.docs:
            self.docs[doc_id] = {"id": doc_id}
        if meta:
            self.docs[doc_id].update(meta)

        # emails
        for em in set(EMAIL_RE.findall(text)):
            self._add_entity(em, "email")
            self._add_edge_once(doc_id, em, "mentions")
            dom = self._domain_from_email(em)
            if dom:
                self._add_entity(dom, "domain")
                self._add_edge_once(em, dom, "belongs_to")
                self._add_edge_once(doc_id, dom, "mentions_domain")

        # urls
        for url in set(URL_RE.findall(text)):
            self._add_entity(url, "url")
            self._add_edge_once(doc_id, url, "mentions")
            dom = self._domain_from_url(url)
            if dom:
                self._add_entity(dom, "domain")
                self._add_edge_once(url, dom, "belongs_to")
                self._add_edge_once(doc_id, dom, "mentions_domain")

    # 兼容可能的 API 命名
    def add_document(
        self,
        text: str,
        doc_id: Optional[str] = None,
        meta: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.add_text(text, doc_id, meta)

    def clear(self) -> None:
        self.entities.clear()
        self.edges.clear()
        self.docs.clear()

    def snapshot(self) -> Dict[str, Any]:
        return {
            "entities": list(self.entities.values()),
            "edges": list(self.edges),
            "docs": self.docs.copy(),
        }

    def save(self, path: str | Path) -> None:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(
            json.dumps(self.snapshot(), ensure_ascii=False, indent=2), encoding="utf-8"
        )

    def load(self, path: str | Path) -> None:
        p = Path(path)
        if not p.exists():
            return
        data = json.loads(p.read_text(encoding="utf-8"))
        self.entities = {e["id"]: e for e in data.get("entities", [])}
        self.edges = data.get("edges", [])
        self.docs = data.get("docs", {})

    def query_entities(
        self, q: str = "", etype: Optional[str] = None, top_k: int = 20
    ) -> List[Dict[str, Any]]:
        ql = q.lower().strip()
        out = []
        for ent in self.entities.values():
            if etype and ent.get("type") != etype:
                continue
            if ql and ql not in ent["id"].lower():
                continue
            out.append(ent)
        out.sort(key=lambda e: (-e.get("count", 0), e["id"]))
        return out[: max(1, top_k)]

    def stats(self) -> Dict[str, Any]:
        by_type: Dict[str, int] = {}
        for e in self.entities.values():
            by_type[e["type"]] = by_type.get(e["type"], 0) + 1
        return {
            "num_entities": len(self.entities),
            "num_docs": len(self.docs),
            "num_edges": len(self.edges),
            "entities_by_type": by_type,
        }

    def neighbors(
        self, node_id: str, depth: int = 1, direction: str = "both"
    ) -> Dict[str, Any]:
        """
        返回以 node_id 为中心、指定深度的子图。
        direction: out|in|both
        """
        if depth < 0:
            depth = 0
        dir_opt = direction.lower()
        if dir_opt not in {"out", "in", "both"}:
            dir_opt = "both"

        # 构建邻接索引
        out_adj = {}
        in_adj = {}
        for e in self.edges:
            out_adj.setdefault(e["src"], []).append(e)
            in_adj.setdefault(e["dst"], []).append(e)

        # BFS 收集节点与边
        seen = {node_id}
        q = deque([(node_id, 0)])
        sub_edges = []
        while q:
            cur, d = q.popleft()
            if d == depth:
                continue
            if dir_opt in {"out", "both"}:
                for ed in out_adj.get(cur, []):
                    sub_edges.append(ed)
                    if ed["dst"] not in seen:
                        seen.add(ed["dst"])
                        q.append((ed["dst"], d + 1))
            if dir_opt in {"in", "both"}:
                for ed in in_adj.get(cur, []):
                    sub_edges.append(ed)
                    if ed["src"] not in seen:
                        seen.add(ed["src"])
                        q.append((ed["src"], d + 1))

        # 聚合节点属性（实体 + 文档）
        nodes = {}
        for nid in seen:
            if nid in self.entities:
                nodes[nid] = self.entities[nid]
            elif nid in self.docs:
                nodes[nid] = {"id": nid, "type": "doc", **self.docs[nid]}
            else:
                nodes[nid] = {"id": nid, "type": "unknown"}
        return {"center": node_id, "nodes": list(nodes.values()), "edges": sub_edges}
