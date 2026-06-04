#!/usr/bin/env python3
"""
mcp-session-adapter.py — Stateful MCP stdio server for an interactive ngspice session.

Implements MCP protocol 2024-11-05 over stdio (JSON-RPC 2.0). Keeps a single ngspice
process alive between calls so a netlist is loaded once and queried many times — ideal for
corner sweeps, parameter alters, and ECO loops without per-query reload overhead.

Usage:
    python3 mcp-session-adapter.py --tool ngspice [--version 1.0.0]

Exposed tools:
    load_netlist   {"path": "<netlist>"}        — source a netlist into the live session
    run_analysis   {"command": "ac dec 10 1 1e9"} — run an analysis command
    measure        {"expr": "..."}              — run a `meas`/`print` and capture the value
    alter_param    {"device": "...", "value": "..."} — alter a device/param, then re-run
    run_command    {"command": "..."}           — raw ngspice command (escape hatch)
    close          {}                           — quit the session

All debug output goes to stderr. Each result is returned as compact text. This is a
pragmatic Phase-1 session server; richer typed queries are added in later phases.
"""

import sys
import json
import argparse
import os
import subprocess
import threading
import queue

_MARKER = "__MCP_DONE__"


class NgspiceSession:
    def __init__(self):
        self.proc = None
        self.out_q = queue.Queue()
        self._reader = None

    def start(self):
        if self.proc is not None:
            return
        self.proc = subprocess.Popen(
            ["ngspice", "-p"],  # interactive pipe mode
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, bufsize=1,
        )
        self._reader = threading.Thread(target=self._read_loop, daemon=True)
        self._reader.start()
        print("[session] ngspice started", file=sys.stderr)

    def _read_loop(self):
        for line in self.proc.stdout:
            self.out_q.put(line.rstrip("\n"))
        self.out_q.put(None)  # EOF sentinel

    def send(self, command, timeout=120):
        if self.proc is None:
            self.start()
        self.proc.stdin.write(command + "\n")
        self.proc.stdin.write(f'echo {_MARKER}\n')
        self.proc.stdin.flush()
        lines = []
        import time
        deadline = time.time() + timeout
        while time.time() < deadline:
            try:
                line = self.out_q.get(timeout=max(0.1, deadline - time.time()))
            except queue.Empty:
                break
            if line is None:
                lines.append("[session] ngspice exited")
                break
            if _MARKER in line:
                break
            lines.append(line)
        return "\n".join(lines)

    def close(self):
        if self.proc is None:
            return
        try:
            self.proc.stdin.write("quit\n")
            self.proc.stdin.flush()
        except (BrokenPipeError, ValueError):
            pass
        try:
            self.proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            self.proc.kill()
        self.proc = None
        print("[session] ngspice closed", file=sys.stderr)


SESSION = NgspiceSession()

_TOOLS = {
    "load_netlist": {"path": {"type": "string"}},
    "run_analysis": {"command": {"type": "string"}},
    "measure": {"expr": {"type": "string"}},
    "alter_param": {"device": {"type": "string"}, "value": {"type": "string"}},
    "run_command": {"command": {"type": "string"}},
    "close": {},
}


def _send(msg):
    sys.stdout.write(json.dumps(msg, separators=(',', ':')) + '\n')
    sys.stdout.flush()


def _ok(rid, result):
    return {"jsonrpc": "2.0", "id": rid, "result": result}


def _err(rid, code, msg):
    return {"jsonrpc": "2.0", "id": rid, "error": {"code": code, "message": msg}}


def _dispatch(name, a):
    if name == "load_netlist":
        return SESSION.send(f'source {a["path"]}')
    if name == "run_analysis":
        return SESSION.send(a["command"])
    if name == "measure":
        return SESSION.send(a["expr"])
    if name == "alter_param":
        return SESSION.send(f'alter {a["device"]}={a["value"]}')
    if name == "run_command":
        return SESSION.send(a["command"])
    if name == "close":
        SESSION.close()
        return "session closed"
    raise KeyError(name)


def main():
    parser = argparse.ArgumentParser(description="Stateful MCP adapter for an interactive ngspice session")
    parser.add_argument("--tool", default="ngspice")
    parser.add_argument("--version", default="1.0.0")
    args = parser.parse_args()
    print(f"[session] starting {args.tool} session MCP server", file=sys.stderr)

    for raw in sys.stdin:
        raw = raw.strip()
        if not raw:
            continue
        try:
            req = json.loads(raw)
        except json.JSONDecodeError:
            print(f"[session] malformed JSON ignored: {raw[:100]}", file=sys.stderr)
            continue
        method = req.get("method", "")
        rid = req.get("id")
        params = req.get("params") if isinstance(req.get("params"), dict) else {}
        if rid is None:
            continue

        if method == "initialize":
            _send(_ok(rid, {"protocolVersion": "2024-11-05", "capabilities": {"tools": {}},
                            "serverInfo": {"name": f"{args.tool}-session-mcp", "version": args.version}}))
        elif method == "ping":
            _send(_ok(rid, {}))
        elif method == "tools/list":
            tools = [{"name": n, "description": f"ngspice session: {n}",
                      "inputSchema": {"type": "object", "properties": p}} for n, p in _TOOLS.items()]
            _send(_ok(rid, {"tools": tools}))
        elif method == "tools/call":
            name = params.get("name", "")
            a = params.get("arguments") if isinstance(params.get("arguments"), dict) else {}
            if name not in _TOOLS:
                _send(_err(rid, -32602, f"Unknown tool '{name}'"))
                continue
            try:
                out = _dispatch(name, a)
                _send(_ok(rid, {"content": [{"type": "text", "text": out}], "isError": False}))
            except Exception as e:  # noqa: BLE001 — surface any session error to the client
                _send(_ok(rid, {"content": [{"type": "text", "text": f"error: {e}"}], "isError": True}))
        else:
            _send(_err(rid, -32601, f"Method not found: {method}"))

    SESSION.close()


if __name__ == "__main__":
    main()
