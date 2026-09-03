from __future__ import annotations

import json
import os
import re
import socket
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from json_repair import repair_json

from .config import RUNTIME_ROOT


SILICONFLOW_ENDPOINT = "https://api.siliconflow.cn/v1/chat/completions"
SILICONFLOW_EMBEDDING_ENDPOINT = "https://api.siliconflow.cn/v1/embeddings"
SILICONFLOW_MODEL = "Qwen/Qwen3.5-35B-A3B"
SILICONFLOW_EMBEDDING_MODEL = "BAAI/bge-m3"


class AgentService:
    def __init__(self, config_file: Path | None = None) -> None:
        self.config_file = config_file or (RUNTIME_ROOT / "siliconflow_config.json")
        self.lock = threading.RLock()

    @staticmethod
    def _open_with_retry(
        request: urllib.request.Request,
        *,
        timeout: int,
        attempts: int = 3,
    ):
        """Retry transient provider failures without retrying permanent errors."""
        last_error: Exception | None = None
        for attempt in range(attempts):
            try:
                return urllib.request.urlopen(request, timeout=timeout)
            except urllib.error.HTTPError as exc:
                if exc.code not in {408, 409, 429, 500, 502, 503, 504}:
                    raise
                last_error = exc
            except (TimeoutError, socket.timeout) as exc:
                last_error = exc
            except urllib.error.URLError as exc:
                if not isinstance(exc.reason, (TimeoutError, socket.timeout)):
                    raise
                last_error = exc
            if attempt + 1 >= attempts:
                break
            time.sleep(2 ** attempt)
        if last_error:
            raise last_error
        raise RuntimeError("SiliconFlow request failed without an error.")

    def _load(self) -> dict[str, str]:
        stored: dict[str, str] = {}
        if self.config_file.exists():
            try:
                value = json.loads(self.config_file.read_text(encoding="utf-8"))
                if isinstance(value, dict):
                    stored = {str(key): str(item) for key, item in value.items() if item is not None}
            except (OSError, json.JSONDecodeError):
                stored = {}
        return {
            "api_key": os.getenv("SILICONFLOW_API_KEY") or stored.get("api_key", ""),
            "model": SILICONFLOW_MODEL,
        }

    def status(self) -> dict[str, Any]:
        value = self._load()
        key = value["api_key"]
        return {
            "configured": bool(key),
            "provider": "siliconflow",
            "provider_label": "硅基流动 Qwen3.5 快速模型",
            "model": SILICONFLOW_MODEL,
            "endpoint": SILICONFLOW_ENDPOINT,
            "api_key_hint": f"{key[:3]}***{key[-4:]}" if len(key) >= 8 else ("已配置" if key else "未配置"),
        }

    def configure(self, api_key: str | None) -> dict[str, Any]:
        with self.lock:
            current = self._load()
            key = (api_key or "").strip() or current["api_key"]
            if not key:
                raise ValueError("请填写硅基流动 API Key。")
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            temporary = self.config_file.with_suffix(".tmp")
            temporary.write_text(
                json.dumps({"api_key": key, "model": SILICONFLOW_MODEL}, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            temporary.replace(self.config_file)
        return self.status()

    def _messages(
        self,
        question: str,
        history: list[dict[str, str]],
        sources: list[dict[str, Any]],
        use_knowledge: bool,
    ) -> list[dict[str, str]]:
        system = (
            "你是轨道交通结构安全保护智能助手。你可以回答通用问题，也可以协助分析工程案例。"
            "回答应准确、清晰、完整，篇幅应与问题复杂度相匹配，避免无必要的重复和过度展开；"
            "涉及工程安全、规范阈值或合规结论时，不得编造依据，应明确提示人工复核。"
        )
        if use_knowledge:
            context = "\n\n".join(
                f"[{index}] 案例《{item['case_name']}》"
                f"{'，文件名：' + item.get('original_file_name') if item.get('original_file_name') else ''}\n"
                f"{item['excerpt']}"
                for index, item in enumerate(sources, start=1)
            )
            system += (
                "本轮启用了知识库。优先依据下面的检索材料回答，并在使用材料时标注[序号]。"
                "材料不足时可以使用通用知识补充，但必须明确区分。\n\n知识库材料：\n"
                + (context or "未检索到相关材料")
            )
        messages: list[dict[str, str]] = [{"role": "system", "content": system}]
        for item in history[-12:]:
            if item.get("role") in {"user", "assistant"} and item.get("content"):
                messages.append({"role": item["role"], "content": item["content"][:8000]})
        messages.append({"role": "user", "content": question})
        return messages

    def chat(
        self,
        question: str,
        history: list[dict[str, str]],
        sources: list[dict[str, Any]],
        use_knowledge: bool,
    ) -> dict[str, Any]:
        config = self._load()
        if not config["api_key"]:
            raise RuntimeError("硅基流动 API 尚未配置，请先在左下角“设置 > 大模型”中填写 API Key。")
        payload = json.dumps(
            {
                "model": SILICONFLOW_MODEL,
                "messages": self._messages(question, history, sources, use_knowledge),
                "stream": False,
                "max_tokens": 2800,
                "temperature": 0.5,
                "enable_thinking": False,
            },
            ensure_ascii=False,
        ).encode("utf-8")
        request = urllib.request.Request(
            SILICONFLOW_ENDPOINT,
            data=payload,
            method="POST",
            headers={
                "Authorization": f"Bearer {config['api_key']}",
                "Content-Type": "application/json; charset=utf-8",
                "Accept": "application/json",
            },
        )
        try:
            with self._open_with_retry(request, timeout=120) as response:
                result = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"硅基流动 API 返回错误（{exc.code}）：{detail[:500]}") from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(f"无法连接硅基流动 API：{exc.reason}") from exc
        try:
            answer = result["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise RuntimeError("硅基流动 API 返回了无法识别的结果。") from exc
        if not answer:
            raise RuntimeError("硅基流动 API 未返回回答内容。")
        return {
            "answer": answer,
            "provider": "siliconflow",
            "model": result.get("model") or SILICONFLOW_MODEL,
            "usage": result.get("usage") or {},
        }

    def complete_json(self, system: str, prompt: str, *, max_tokens: int = 2400) -> dict[str, Any] | list[Any]:
        """Request one strict JSON response for machine-reviewed rule drafts."""
        config = self._load()
        if not config["api_key"]:
            raise RuntimeError("硅基流动 API 尚未配置，请先在左下角“设置 > 大模型”中填写 API Key。")
        payload = json.dumps(
            {
                "model": SILICONFLOW_MODEL,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": prompt},
                ],
                "stream": False,
                "max_tokens": max_tokens,
                "temperature": 0.1,
                "enable_thinking": False,
                "response_format": {"type": "json_object"},
            },
            ensure_ascii=False,
        ).encode("utf-8")
        request = urllib.request.Request(
            SILICONFLOW_ENDPOINT,
            data=payload,
            method="POST",
            headers={
                "Authorization": f"Bearer {config['api_key']}",
                "Content-Type": "application/json; charset=utf-8",
                "Accept": "application/json",
            },
        )
        try:
            with self._open_with_retry(request, timeout=180) as response:
                result = json.loads(response.read().decode("utf-8"))
            content = result["choices"][0]["message"]["content"].strip()
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"硅基流动 API 返回错误（{exc.code}）：{detail[:500]}") from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(f"无法连接硅基流动 API：{exc.reason}") from exc
        except (KeyError, IndexError, TypeError, json.JSONDecodeError) as exc:
            raise RuntimeError("硅基流动 API 返回了无法识别的结果。") from exc

        if content.startswith("```"):
            content = content.split("\n", 1)[-1]
            content = content.rsplit("```", 1)[0].strip()
        try:
            value = json.loads(content)
        except json.JSONDecodeError as exc:
            try:
                repaired = repair_json(content, return_objects=True)
            except (ValueError, TypeError, KeyError) as repair_exc:
                raise RuntimeError(f"AI未返回合法JSON，本地修复也未成功：{exc.msg}") from repair_exc
            if not isinstance(repaired, (dict, list)):
                raise RuntimeError(f"AI未返回合法JSON，本地修复也未成功：{exc.msg}")
            value = repaired
        if not isinstance(value, (dict, list)):
            raise RuntimeError("AI规则结果必须是JSON对象或数组。")
        return value

    def summarize_conversation_title(self, question: str, answer: str, mode: str = "general") -> str:
        """Create a concise subject title after the first question has an answer."""
        fallback = "知识库工程咨询" if mode == "knowledge" else "工程技术咨询"
        try:
            value = self.complete_json(
                "你负责为轨道工程智能助手的对话生成历史标题。"
                "只输出JSON对象，格式为{\"title\":\"...\"}。"
                "标题必须概括本轮咨询主题，使用6至18个汉字；不得照抄提问句，不要使用问号、引号、书名号或‘用户’‘助手’等词。",
                f"提问：{question[:800]}\n\n回答摘要：{answer[:1200]}",
                max_tokens=80,
            )
            title = str(value.get("title") or "") if isinstance(value, dict) else ""
            title = re.sub(r"[\r\n\t\"'“”‘’《》?？!！:：]+", "", title).strip()
            if 3 <= len(title) <= 24:
                return title
        except Exception:
            pass
        return fallback

    def embed(self, texts: list[str]) -> list[list[float]]:
        """Create semantic vectors for RAG chunks using the configured provider."""
        if not texts:
            return []
        config = self._load()
        if not config["api_key"]:
            raise RuntimeError("硅基流动 API 尚未配置，无法建立向量索引。")
        vectors: list[list[float]] = []
        for start in range(0, len(texts), 24):
            batch = [str(text)[:12000] for text in texts[start:start + 24]]
            payload = json.dumps(
                {"model": SILICONFLOW_EMBEDDING_MODEL, "input": batch, "encoding_format": "float"},
                ensure_ascii=False,
            ).encode("utf-8")
            request = urllib.request.Request(
                SILICONFLOW_EMBEDDING_ENDPOINT,
                data=payload,
                method="POST",
                headers={
                    "Authorization": f"Bearer {config['api_key']}",
                    "Content-Type": "application/json; charset=utf-8",
                    "Accept": "application/json",
                },
            )
            try:
                with self._open_with_retry(request, timeout=150) as response:
                    result = json.loads(response.read().decode("utf-8"))
                ordered = sorted(result["data"], key=lambda item: item["index"])
                vectors.extend([[float(value) for value in item["embedding"]] for item in ordered])
            except urllib.error.HTTPError as exc:
                detail = exc.read().decode("utf-8", errors="replace")
                raise RuntimeError(f"硅基流动向量 API 返回错误（{exc.code}）：{detail[:500]}") from exc
            except urllib.error.URLError as exc:
                raise RuntimeError(f"无法连接硅基流动向量 API：{exc.reason}") from exc
            except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
                raise RuntimeError("硅基流动向量 API 返回了无法识别的结果。") from exc
        if len(vectors) != len(texts):
            raise RuntimeError("向量 API 返回数量与文本数量不一致。")
        return vectors
