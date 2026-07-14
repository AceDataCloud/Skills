"""CDP WebSocket 客户端（Browser, Page, Element），对应 Go browser/browser.go + go-rod API。

通过原生 WebSocket 与 Chrome DevTools Protocol 通信，实现浏览器自动化控制。
"""

from __future__ import annotations

import json
import logging
import os
import random
import select
import time
from collections import deque
from typing import Any

from .errors import CDPError, ElementNotFoundError
from .stealth import STEALTH_JS, build_ua_override

logger = logging.getLogger(__name__)


class PipeTransport:
    """Null-delimited CDP transport used by Chrome remote-debugging-pipe."""

    def __init__(self, write_fd: int, read_fd: int) -> None:
        self.write_fd = write_fd
        self.read_fd = read_fd
        self.buffer = bytearray()

    def send(self, message: str) -> None:
        payload = message.encode("utf-8") + b"\0"
        while payload:
            written = os.write(self.write_fd, payload)
            payload = payload[written:]

    def recv(self, timeout: float) -> str:
        deadline = time.monotonic() + timeout
        while True:
            separator = self.buffer.find(b"\0")
            if separator >= 0:
                message = bytes(self.buffer[:separator])
                del self.buffer[: separator + 1]
                return message.decode("utf-8")
            remaining = deadline - time.monotonic()
            if remaining <= 0 or not select.select([self.read_fd], [], [], remaining)[0]:
                raise TimeoutError
            chunk = os.read(self.read_fd, 64 * 1024)
            if not chunk:
                raise CDPError("Chrome closed the CDP pipe")
            self.buffer.extend(chunk)

    def close(self) -> None:
        for fd in (self.write_fd, self.read_fd):
            try:
                os.close(fd)
            except OSError:
                pass


class CDPClient:
    """底层 CDP WebSocket 通信客户端。"""

    def __init__(self, transport: PipeTransport) -> None:
        self._transport = transport
        self._id = 0
        self._callbacks: dict[int, Any] = {}

    def send(self, method: str, params: dict | None = None) -> dict:
        """发送 CDP 命令并等待结果。"""
        self._id += 1
        msg: dict[str, Any] = {"id": self._id, "method": method}
        if params:
            msg["params"] = params
        self._transport.send(json.dumps(msg))
        return self._wait_for(self._id)

    def _wait_for(self, msg_id: int, timeout: float = 30.0) -> dict:
        """等待指定 id 的响应。"""
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            try:
                raw = self._transport.recv(max(0.1, deadline - time.monotonic()))
            except TimeoutError:
                break
            data = json.loads(raw)
            if data.get("id") == msg_id:
                if "error" in data:
                    raise CDPError(f"CDP 错误: {data['error']}")
                return data.get("result", {})
        raise CDPError(f"等待 CDP 响应超时 (id={msg_id})")

    def close(self) -> None:
        import contextlib

        with contextlib.suppress(Exception):
            self._transport.close()


class Page:
    """CDP 页面对象，封装常用操作。"""

    def __init__(self, cdp: CDPClient, target_id: str, session_id: str) -> None:
        self._cdp = cdp
        self.target_id = target_id
        self.session_id = session_id
        self._transport = cdp._transport
        self._id_counter = 1000
        self._events: deque[dict[str, Any]] = deque(maxlen=256)

    def _send_session(self, method: str, params: dict | None = None) -> dict:
        """向 session 发送命令。"""
        self._id_counter += 1
        msg: dict[str, Any] = {
            "id": self._id_counter,
            "method": method,
            "sessionId": self.session_id,
        }
        if params:
            msg["params"] = params
        self._transport.send(json.dumps(msg))
        return self._wait_session(self._id_counter)

    def _wait_session(self, msg_id: int, timeout: float = 60.0) -> dict:
        """等待 session 响应。"""
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            try:
                raw = self._transport.recv(max(0.1, deadline - time.monotonic()))
            except TimeoutError:
                break
            data = json.loads(raw)
            if data.get("id") == msg_id:
                if "error" in data:
                    raise CDPError(f"CDP 错误: {data['error']}")
                return data.get("result", {})
            if "method" in data and data.get("sessionId") == self.session_id:
                self._events.append(data)
        raise CDPError(f"等待 session 响应超时 (id={msg_id})")

    def clear_events(self) -> None:
        self._events.clear()

    def wait_for_event(self, timeout: float) -> dict[str, Any] | None:
        if self._events:
            return self._events.popleft()
        try:
            raw = self._transport.recv(timeout)
        except TimeoutError:
            return None
        data = json.loads(raw)
        if "method" in data and data.get("sessionId") == self.session_id:
            return data
        return None

    def navigate(self, url: str) -> None:
        """导航到指定 URL。"""
        logger.info("导航到: %s", url)
        self._send_session("Page.navigate", {"url": url})

    def set_cookies(self, cookies: list[dict[str, Any]]) -> None:
        """Install request-scoped cookies in this page's browser context."""
        self._send_session("Network.enable")
        self._send_session("Network.setCookies", {"cookies": cookies})

    def wait_for_load(self, timeout: float = 60.0) -> None:
        """等待页面加载完成（通过轮询 document.readyState）。"""
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            try:
                state = self.evaluate("document.readyState")
                if state == "complete":
                    return
            except CDPError:
                pass
            time.sleep(0.5)
        logger.warning("等待页面加载超时")

    def wait_dom_stable(self, timeout: float = 10.0, interval: float = 0.5) -> None:
        """等待 DOM 稳定（连续两次 DOM 快照一致）。"""
        last_html = ""
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            try:
                html = self.evaluate("document.body ? document.body.innerHTML.length : 0")
                if html == last_html and html != "":
                    return
                last_html = html
            except CDPError:
                pass
            time.sleep(interval)

    def evaluate(self, expression: str, timeout: float = 30.0) -> Any:
        """执行 JavaScript 表达式并返回结果。"""
        result = self._send_session(
            "Runtime.evaluate",
            {
                "expression": expression,
                "returnByValue": True,
                "awaitPromise": True,
            },
        )
        if "exceptionDetails" in result:
            raise CDPError(f"JS 执行异常: {result['exceptionDetails']}")
        remote_obj = result.get("result", {})
        return remote_obj.get("value")

    def evaluate_function(self, function_body: str, *args: Any) -> Any:
        """执行 JavaScript 函数并返回结果。

        function_body 是一个完整的函数体，如 `() => { return 1; }`
        """
        result = self._send_session(
            "Runtime.evaluate",
            {
                "expression": f"({function_body})()",
                "returnByValue": True,
                "awaitPromise": True,
            },
        )
        if "exceptionDetails" in result:
            raise CDPError(f"JS 函数执行异常: {result['exceptionDetails']}")
        remote_obj = result.get("result", {})
        return remote_obj.get("value")

    def query_selector(self, selector: str) -> str | None:
        """查找单个元素，返回 objectId 或 None。"""
        result = self._send_session(
            "Runtime.evaluate",
            {
                "expression": f"document.querySelector({json.dumps(selector)})",
                "returnByValue": False,
            },
        )
        remote_obj = result.get("result", {})
        if remote_obj.get("subtype") == "null" or remote_obj.get("type") == "undefined":
            return None
        return remote_obj.get("objectId")

    def query_selector_all(self, selector: str) -> list[str]:
        """查找多个元素，返回 objectId 列表。"""
        # 通过 JS 返回元素数量，然后逐个获取
        count = self.evaluate(f"document.querySelectorAll({json.dumps(selector)}).length")
        if not count:
            return []
        object_ids = []
        for i in range(count):
            result = self._send_session(
                "Runtime.evaluate",
                {
                    "expression": (f"document.querySelectorAll({json.dumps(selector)})[{i}]"),
                    "returnByValue": False,
                },
            )
            obj = result.get("result", {})
            oid = obj.get("objectId")
            if oid:
                object_ids.append(oid)
        return object_ids

    def has_element(self, selector: str) -> bool:
        """检查元素是否存在。"""
        return self.evaluate(f"document.querySelector({json.dumps(selector)}) !== null") is True

    def wait_for_element(self, selector: str, timeout: float = 30.0) -> str:
        """等待元素出现，返回 objectId。"""
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            oid = self.query_selector(selector)
            if oid:
                return oid
            time.sleep(0.5)
        raise ElementNotFoundError(selector)

    def click_element(self, selector: str) -> None:
        """点击指定选择器的元素（通过 CDP Input 事件，isTrusted=true）。"""
        box = self.evaluate(
            f"""
            (() => {{
                const el = document.querySelector({json.dumps(selector)});
                if (!el) return null;
                el.scrollIntoView({{block: 'center'}});
                const rect = el.getBoundingClientRect();
                return {{x: rect.left + rect.width / 2, y: rect.top + rect.height / 2}};
            }})()
            """
        )
        if not box:
            return
        x = box["x"] + random.uniform(-3, 3)
        y = box["y"] + random.uniform(-3, 3)
        self.mouse_move(x, y)
        time.sleep(random.uniform(0.03, 0.08))
        self.mouse_click(x, y)

    def click_creator_tab(self, text: str) -> bool:
        """Click the real creator tab while excluding XHS honeypot copies."""
        document = self._send_session("DOM.getDocument", {"depth": -1, "pierce": True})
        target: dict[str, Any] | None = None

        def attrs(node: dict[str, Any]) -> dict[str, str]:
            values = node.get("attributes") or []
            return dict(zip(values[0::2], values[1::2]))

        def content(node: dict[str, Any]) -> str:
            chunks = [node.get("nodeValue") or ""]
            for child in node.get("children") or []:
                chunks.append(content(child))
            for shadow_root in node.get("shadowRoots") or []:
                chunks.append(content(shadow_root))
            return "".join(chunks).strip()

        def find(node: dict[str, Any]) -> None:
            nonlocal target
            if target is not None:
                return
            properties = attrs(node)
            classes = properties.get("class", "").split()
            if (
                node.get("nodeName") == "DIV"
                and "creator-tab" in classes
                and properties.get("data-hp-bound") == "1"
                and "data-hp-kind" not in properties
                and "button-hp-installed" not in properties
                and content(node) == text
            ):
                target = node
                return
            for child in node.get("children") or []:
                find(child)
            for shadow_root in node.get("shadowRoots") or []:
                find(shadow_root)

        find(document["root"])
        return self._click_dom_node(target) if target else False

    def _click_dom_node(self, target: dict[str, Any]) -> bool:
        node_ref = (
            {"backendNodeId": target["backendNodeId"]}
            if target.get("backendNodeId")
            else {"nodeId": target["nodeId"]}
        )
        self._send_session("DOM.scrollIntoViewIfNeeded", node_ref)
        model = self._send_session("DOM.getBoxModel", node_ref).get("model")
        if not model:
            return False
        quad = model.get("border") or model.get("content")
        if not quad or len(quad) < 8:
            return False
        x = sum(quad[0::2]) / 4
        y = sum(quad[1::2]) / 4
        self.mouse_move(x, y)
        time.sleep(random.uniform(0.03, 0.08))
        self.mouse_click(x, y)
        return True

    def click_pierced_button(self, host_name: str, button_text: str) -> bool:
        document = self._send_session("DOM.getDocument", {"depth": -1, "pierce": True})
        targets: list[dict[str, Any]] = []

        def attrs(node: dict[str, Any]) -> dict[str, str]:
            values = node.get("attributes") or []
            return dict(zip(values[0::2], values[1::2]))

        def content(node: dict[str, Any]) -> str:
            chunks = [node.get("nodeValue") or ""]
            for child in node.get("children") or []:
                chunks.append(content(child))
            for shadow_root in node.get("shadowRoots") or []:
                chunks.append(content(shadow_root))
            return "".join(chunks).strip()

        def find_button(node: dict[str, Any]) -> None:
            properties = attrs(node)
            if (
                node.get("nodeName") == "BUTTON"
                and content(node) == button_text
                and "disabled" not in properties
                and properties.get("aria-disabled") != "true"
            ):
                targets.append(node)
                return
            for child in node.get("children") or []:
                find_button(child)
            for shadow_root in node.get("shadowRoots") or []:
                find_button(shadow_root)

        def find_host(node: dict[str, Any]) -> None:
            properties = attrs(node)
            if node.get("nodeName") == host_name.upper() and properties.get("is-publish") == "true":
                for shadow_root in node.get("shadowRoots") or []:
                    find_button(shadow_root)
                return
            for child in node.get("children") or []:
                find_host(child)

        find_host(document["root"])
        for target in targets:
            node_ref = {"backendNodeId": target["backendNodeId"]}
            try:
                self._send_session("DOM.scrollIntoViewIfNeeded", node_ref)
                model = self._send_session("DOM.getBoxModel", node_ref).get("model")
            except CDPError:
                continue
            if not model or not model.get("width") or not model.get("height"):
                continue
            quad = model.get("border") or model.get("content")
            if not quad or len(quad) < 8:
                continue
            x = sum(quad[0::2]) / 4
            y = sum(quad[1::2]) / 4
            hit = self._send_session(
                "DOM.getNodeForLocation",
                {"x": int(x), "y": int(y), "includeUserAgentShadowDOM": True},
            )
            hit_id = hit.get("backendNodeId")
            if hit_id != target.get("backendNodeId"):
                if not hit_id:
                    continue
                try:
                    hit_object_id = self._send_session(
                        "DOM.resolveNode", {"backendNodeId": hit_id}
                    ).get("object", {}).get("objectId")
                    button_object_id = self._send_session(
                        "DOM.resolveNode", node_ref
                    ).get("object", {}).get("objectId")
                    if not hit_object_id or not button_object_id:
                        continue
                    contains = self._send_session(
                        "Runtime.callFunctionOn",
                        {
                            "objectId": hit_object_id,
                            "functionDeclaration": "function(button) { return button.contains(this); }",
                            "arguments": [{"objectId": button_object_id}],
                            "returnByValue": True,
                        },
                    ).get("result", {}).get("value")
                except CDPError:
                    contains = False
                if contains is not True:
                    continue
            self.mouse_move(x, y)
            time.sleep(random.uniform(0.03, 0.08))
            self.mouse_click(x, y)
            return True
        return False

    def input_text(self, selector: str, text: str) -> None:
        """向指定选择器的元素输入文本。"""
        self.evaluate(
            f"""
            (() => {{
                const el = document.querySelector({json.dumps(selector)});
                if (!el) return;
                el.focus();
                el.value = {json.dumps(text)};
                el.dispatchEvent(new Event('input', {{bubbles: true}}));
                el.dispatchEvent(new Event('change', {{bubbles: true}}));
            }})()
            """
        )

    def input_content_editable(self, selector: str, text: str) -> None:
        """向 contentEditable 元素输入文本（CDP 逐字输入，模拟真实打字）。"""
        # 1. focus 元素
        self.evaluate(
            f"""
            (() => {{
                const el = document.querySelector({json.dumps(selector)});
                if (el) el.focus();
            }})()
            """
        )
        time.sleep(0.1)
        # 2. 全选清空（Ctrl+A + Backspace）
        self._send_session(
            "Input.dispatchKeyEvent",
            {"type": "keyDown", "key": "a", "code": "KeyA", "modifiers": 2},
        )
        self._send_session(
            "Input.dispatchKeyEvent",
            {"type": "keyUp", "key": "a", "code": "KeyA", "modifiers": 2},
        )
        self._send_session(
            "Input.dispatchKeyEvent",
            {
                "type": "keyDown",
                "key": "Backspace",
                "code": "Backspace",
                "windowsVirtualKeyCode": 8,
            },
        )
        self._send_session(
            "Input.dispatchKeyEvent",
            {
                "type": "keyUp",
                "key": "Backspace",
                "code": "Backspace",
                "windowsVirtualKeyCode": 8,
            },
        )
        time.sleep(0.1)
        # 3. 逐字输入（随机 30-80ms 间隔，换行符转为 Enter 键）
        for char in text:
            if char == "\n":
                self.press_key("Enter")
            else:
                self._send_session(
                    "Input.dispatchKeyEvent",
                    {"type": "keyDown", "text": char},
                )
                self._send_session(
                    "Input.dispatchKeyEvent",
                    {"type": "keyUp", "text": char},
                )
            time.sleep(random.uniform(0.03, 0.08))

    def get_element_text(self, selector: str) -> str | None:
        """获取元素文本内容。"""
        return self.evaluate(
            f"""
            (() => {{
                const el = document.querySelector({json.dumps(selector)});
                return el ? el.textContent : null;
            }})()
            """
        )

    def get_element_attribute(self, selector: str, attr: str) -> str | None:
        """获取元素属性值。"""
        return self.evaluate(
            f"""
            (() => {{
                const el = document.querySelector({json.dumps(selector)});
                return el ? el.getAttribute({json.dumps(attr)}) : null;
            }})()
            """
        )

    def get_elements_count(self, selector: str) -> int:
        """获取匹配元素数量。"""
        result = self.evaluate(f"document.querySelectorAll({json.dumps(selector)}).length")
        return result if isinstance(result, int) else 0

    def scroll_by(self, x: int, y: int) -> None:
        """滚动页面。"""
        self.evaluate(f"window.scrollBy({x}, {y})")

    def scroll_to(self, x: int, y: int) -> None:
        """滚动到指定位置。"""
        self.evaluate(f"window.scrollTo({x}, {y})")

    def scroll_to_bottom(self) -> None:
        """滚动到页面底部。"""
        self.evaluate("window.scrollTo(0, document.body.scrollHeight)")

    def scroll_element_into_view(self, selector: str) -> None:
        """将元素滚动到可视区域。"""
        self.evaluate(
            f"""
            (() => {{
                const el = document.querySelector({json.dumps(selector)});
                if (el) el.scrollIntoView({{behavior: 'smooth', block: 'center'}});
            }})()
            """
        )

    def scroll_nth_element_into_view(self, selector: str, index: int) -> None:
        """将第 N 个匹配元素滚动到可视区域。"""
        self.evaluate(
            f"""
            (() => {{
                const els = document.querySelectorAll({json.dumps(selector)});
                if (els[{index}]) els[{index}].scrollIntoView(
                    {{behavior: 'smooth', block: 'center'}}
                );
            }})()
            """
        )

    def get_scroll_top(self) -> int:
        """获取当前滚动位置。"""
        result = self.evaluate(
            "window.pageYOffset || document.documentElement.scrollTop"
            " || document.body.scrollTop || 0"
        )
        return int(result) if result else 0

    def get_viewport_height(self) -> int:
        """获取视口高度。"""
        result = self.evaluate("window.innerHeight")
        return int(result) if result else 768

    def set_file_input(self, selector: str, files: list[str]) -> None:
        """设置文件输入框的文件（通过 CDP DOM.setFileInputFiles）。"""
        # 先获取 nodeId
        doc = self._send_session("DOM.getDocument", {"depth": 0})
        root_node_id = doc["root"]["nodeId"]
        result = self._send_session(
            "DOM.querySelector",
            {"nodeId": root_node_id, "selector": selector},
        )
        node_id = result.get("nodeId", 0)
        if node_id == 0:
            raise ElementNotFoundError(selector)
        self._send_session(
            "DOM.setFileInputFiles",
            {"nodeId": node_id, "files": files},
        )

    def dispatch_wheel_event(self, delta_y: float) -> None:
        """触发滚轮事件以激活懒加载。"""
        self.evaluate(
            f"""
            (() => {{
                let target = document.querySelector('.note-scroller')
                    || document.querySelector('.interaction-container')
                    || document.documentElement;
                const event = new WheelEvent('wheel', {{
                    deltaY: {delta_y},
                    deltaMode: 0,
                    bubbles: true,
                    cancelable: true,
                    view: window,
                }});
                target.dispatchEvent(event);
            }})()
            """
        )

    def mouse_move(self, x: float, y: float) -> None:
        """移动鼠标。"""
        self._send_session(
            "Input.dispatchMouseEvent",
            {"type": "mouseMoved", "x": x, "y": y},
        )

    def mouse_click(self, x: float, y: float, button: str = "left") -> None:
        """在指定坐标点击。"""
        self._send_session(
            "Input.dispatchMouseEvent",
            {"type": "mousePressed", "x": x, "y": y, "button": button, "clickCount": 1},
        )
        self._send_session(
            "Input.dispatchMouseEvent",
            {"type": "mouseReleased", "x": x, "y": y, "button": button, "clickCount": 1},
        )

    def type_text(self, text: str, delay_ms: int = 50) -> None:
        """逐字符输入文本。"""
        for char in text:
            self._send_session(
                "Input.dispatchKeyEvent",
                {"type": "keyDown", "text": char},
            )
            self._send_session(
                "Input.dispatchKeyEvent",
                {"type": "keyUp", "text": char},
            )
            if delay_ms > 0:
                time.sleep(delay_ms / 1000.0)

    def press_key(self, key: str) -> None:
        """按下并释放指定键。"""
        key_map = {
            "Enter": {"key": "Enter", "code": "Enter", "windowsVirtualKeyCode": 13},
            "ArrowDown": {
                "key": "ArrowDown",
                "code": "ArrowDown",
                "windowsVirtualKeyCode": 40,
            },
            "Tab": {"key": "Tab", "code": "Tab", "windowsVirtualKeyCode": 9},
        }
        info = key_map.get(key, {"key": key, "code": key})
        self._send_session(
            "Input.dispatchKeyEvent",
            {"type": "keyDown", **info},
        )
        self._send_session(
            "Input.dispatchKeyEvent",
            {"type": "keyUp", **info},
        )

    def inject_stealth(self) -> None:
        """注入反检测脚本。"""
        self._send_session(
            "Page.addScriptToEvaluateOnNewDocument",
            {"source": STEALTH_JS},
        )

    def remove_element(self, selector: str) -> None:
        """移除 DOM 元素。"""
        self.evaluate(
            f"""
            (() => {{
                const el = document.querySelector({json.dumps(selector)});
                if (el) el.remove();
            }})()
            """
        )

    def hover_element(self, selector: str) -> None:
        """悬停到元素中心。"""
        box = self.evaluate(
            f"""
            (() => {{
                const el = document.querySelector({json.dumps(selector)});
                if (!el) return null;
                const rect = el.getBoundingClientRect();
                return {{x: rect.left + rect.width / 2, y: rect.top + rect.height / 2}};
            }})()
            """
        )
        if box:
            self.mouse_move(box["x"], box["y"])

    def select_all_text(self, selector: str) -> None:
        """选中输入框内所有文本。"""
        self.evaluate(
            f"""
            (() => {{
                const el = document.querySelector({json.dumps(selector)});
                if (!el) return;
                el.focus();
                el.select ? el.select() : document.execCommand('selectAll');
            }})()
            """
        )

    def screenshot_element(self, selector: str, padding: int = 0) -> bytes:
        """对指定 CSS 选择器的元素截图，返回 PNG 字节。

        通过 CDP Page.captureScreenshot 截取元素所在区域，比 Python 层 PNG
        解码/重编码快很多，且图片直接来自浏览器渲染结果。

        Args:
            selector: CSS 选择器。
            padding:  在元素四周额外保留的像素数（背景色填充，相当于白边）。

        Returns:
            PNG 字节；元素不存在时返回 b""。
        """
        import base64 as _b64

        # 用 DOM.getBoxModel 获取元素坐标，返回的是 page 坐标系（CSS px，相对于文档左上角）。
        # getBoundingClientRect 返回的是 viewport 坐标系，对 position:fixed 遮罩层内的元素
        # 加 pageXOffset 后依然会截到遮罩背后的内容。DOM.getBoxModel 则始终正确。
        try:
            doc = self._send_session("DOM.getDocument", {"depth": 0})
            root_id = doc["root"]["nodeId"]
            query = self._send_session("DOM.querySelector", {"nodeId": root_id, "selector": selector})
            node_id = query.get("nodeId", 0)
            if not node_id:
                return b""
            box_model = self._send_session("DOM.getBoxModel", {"nodeId": node_id})
            model = box_model["model"]
            content = model["content"]  # [x1,y1, x2,y2, x3,y3, x4,y4] 顺时针四角
            x, y = content[0], content[1]
            width, height = float(model["width"]), float(model["height"])
        except Exception:
            return b""

        result = self._send_session(
            "Page.captureScreenshot",
            {
                "format": "png",
                "clip": {
                    "x": max(0.0, x - padding),
                    "y": max(0.0, y - padding),
                    "width": width + padding * 2,
                    "height": height + padding * 2,
                    "scale": 1.0,
                },
            },
        )
        return _b64.b64decode(result.get("data", ""))


class Browser:
    """Chrome 浏览器 CDP 控制器。"""

    def __init__(self, transport: PipeTransport) -> None:
        self._cdp: CDPClient | None = CDPClient(transport)
        self._chrome_version: str | None = None

    def connect(self) -> None:
        """连接到 Chrome DevTools。"""
        if not self._cdp:
            raise CDPError("Chrome CDP pipe is closed")
        info = self._cdp.send("Browser.getVersion")

        # 从 "Chrome/134.0.6998.88" 提取真实版本号，用于动态构建 UA
        browser_str = info.get("Browser", "")
        if "/" in browser_str:
            self._chrome_version = browser_str.split("/", 1)[1]

        logger.info("连接到 Chrome CDP pipe (version=%s)", self._chrome_version)

    def _targets(self) -> list[dict[str, Any]]:
        if not self._cdp:
            raise CDPError("Chrome CDP pipe is closed")
        return self._cdp.send("Target.getTargets").get("targetInfos", [])

    def _setup_page(self, page: Page) -> Page:
        """为 Page 对象注入 stealth、UA、viewport，并启用必要的 CDP domain。"""
        import contextlib

        page.inject_stealth()
        page._send_session(
            "Emulation.setUserAgentOverride",
            build_ua_override(self._chrome_version),
        )
        page._send_session(
            "Emulation.setDeviceMetricsOverride",
            {
                "width": random.randint(1366, 1920),
                "height": random.randint(768, 1080),
                "deviceScaleFactor": 1,
                "mobile": False,
            },
        )
        for perm in ("geolocation", "notifications", "midi", "camera", "microphone"):
            with contextlib.suppress(CDPError):
                assert self._cdp is not None
                self._cdp.send(
                    "Browser.setPermission",
                    {"permission": {"name": perm}, "setting": "denied"},
                )
        page._send_session("Page.enable")
        page._send_session("DOM.enable")
        page._send_session("Runtime.enable")
        return page

    def new_page(self, url: str = "about:blank") -> Page:
        """创建新页面（强制开新 tab）。"""
        if not self._cdp:
            self.connect()
        assert self._cdp is not None

        result = self._cdp.send("Target.createTarget", {"url": url})
        target_id = result["targetId"]
        result = self._cdp.send(
            "Target.attachToTarget",
            {"targetId": target_id, "flatten": True},
        )
        session_id = result["sessionId"]
        return self._setup_page(Page(self._cdp, target_id, session_id))

    def get_or_create_page(self) -> Page:
        """复用现有空白 tab，找不到时才新建。

        避免每次命令都创建新 tab 导致 Chrome 中 tab 无限堆积。
        空白 tab 判定：url 为 about:blank 或 chrome://newtab/。
        """
        if not self._cdp:
            self.connect()
        assert self._cdp is not None

        import contextlib

        targets = self._targets()

        for target in targets:
            if target.get("type") == "page" and target.get("url") in (
                "about:blank",
                "chrome://newtab/",
            ):
                target_id = target["targetId"]
                with contextlib.suppress(Exception):
                    result = self._cdp.send(
                        "Target.attachToTarget",
                        {"targetId": target_id, "flatten": True},
                    )
                    session_id = result.get("sessionId")
                    if session_id:
                        logger.debug("复用空白 tab: %s", target_id)
                        return self._setup_page(Page(self._cdp, target_id, session_id))

        # 没有空白 tab，新建一个
        return self.new_page()

    def get_page_by_target_id(self, target_id: str) -> Page | None:
        """通过 target_id 精确连接到指定 tab。"""
        if not self._cdp:
            self.connect()
        assert self._cdp is not None
        try:
            result = self._cdp.send(
                "Target.attachToTarget",
                {"targetId": target_id, "flatten": True},
            )
        except Exception:
            return None
        session_id = result.get("sessionId")
        if not session_id:
            return None
        page = Page(self._cdp, target_id, session_id)
        page._send_session("Page.enable")
        page._send_session("DOM.enable")
        page._send_session("Runtime.enable")
        page.inject_stealth()
        return page

    def get_existing_page(self) -> Page | None:
        """获取已有页面（取第一个非 about:blank 的 page target）。"""
        if not self._cdp:
            self.connect()
        assert self._cdp is not None

        targets = self._targets()

        for target in targets:
            if target.get("type") == "page" and target.get("url") != "about:blank":
                target_id = target["targetId"]
                result = self._cdp.send(
                    "Target.attachToTarget",
                    {"targetId": target_id, "flatten": True},
                )
                session_id = result["sessionId"]
                page = Page(self._cdp, target_id, session_id)
                page._send_session("Page.enable")
                page._send_session("DOM.enable")
                page._send_session("Runtime.enable")
                page.inject_stealth()
                return page
        return None

    def close_page(self, page: Page) -> None:
        """关闭页面。"""
        import contextlib

        if self._cdp:
            with contextlib.suppress(CDPError):
                self._cdp.send("Target.closeTarget", {"targetId": page.target_id})

    def close(self) -> None:
        """关闭连接。"""
        if self._cdp:
            self._cdp.close()
            self._cdp = None
