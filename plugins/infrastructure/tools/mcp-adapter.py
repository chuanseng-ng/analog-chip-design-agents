#!/usr/bin/env python3
"""
mcp-adapter.py — Generic MCP stdio server wrapping an analog/RF EDA tool wrapper script.

Implements MCP protocol 2024-11-05 over stdio (JSON-RPC 2.0, newline-delimited).

Usage:
    python3 mcp-adapter.py --wrapper /path/to/wrap-TOOL.sh --tool TOOL \\
        [--description "Short description"] [--version 1.0.0]

Environment:
    TOOL_TIMEOUT_S   Kill timeout in seconds for the wrapper process (default: 300)

Each tools/call invocation runs the wrapper with the provided arguments and returns its
compact JSON output as the MCP tool result. All debug output goes to stderr so it does not
corrupt the protocol stream on stdout.
"""

import sys
import json
import subprocess
import argparse
import os
import tempfile
import atexit

_temp_files = []


def _cleanup_temp_files():
    for path in _temp_files:
        try:
            os.unlink(path)
        except OSError:
            pass


atexit.register(_cleanup_temp_files)


def _send(msg):
    sys.stdout.write(json.dumps(msg, separators=(',', ':')) + '\n')
    sys.stdout.flush()


def _ok(req_id, result):
    return {"jsonrpc": "2.0", "id": req_id, "result": result}


def _err(req_id, code, message):
    return {"jsonrpc": "2.0", "id": req_id, "error": {"code": code, "message": message}}


# Per-tool extra input properties (beyond raw args[]).
_EXTRA_PROPERTIES = {
    "ngspice": {
        "netlist": {"type": "string", "description": "Path to the SPICE netlist/deck to run in batch (-b) mode"},
        "control": {"type": "string", "description": "Inline ngspice control block, written to a temp .sp and run with -b"},
    },
    "xyce": {
        "netlist": {"type": "string", "description": "Path to the SPICE netlist for Xyce"},
    },
    "magic": {
        "tcl_script": {"type": "string", "description": "Inline Magic Tcl script (DRC/extract), written to a temp file"},
        "gds": {"type": "string", "description": "GDS file to load"},
    },
    "klayout": {
        "drc_script": {"type": "string", "description": "Path to a KLayout DRC/LVS .lydrc/.lylvs script"},
        "layout": {"type": "string", "description": "Layout (GDS/OASIS) file to check"},
    },
    "netgen": {
        "layout_netlist": {"type": "string", "description": "Extracted layout netlist for LVS"},
        "source_netlist": {"type": "string", "description": "Schematic/source netlist for LVS"},
    },
    "openvaf": {
        "va_file": {"type": "string", "description": "Path to the Verilog-A source to compile to OSDI"},
    },
    "openems": {
        "sim_script": {"type": "string", "description": "Path to the openEMS Octave/Python simulation script"},
    },
}


def _input_schema(tool):
    props = {
        "args": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Raw CLI arguments passed directly to the wrapper script",
            "default": [],
        }
    }
    props.update(_EXTRA_PROPERTIES.get(tool, {}))
    return {"type": "object", "properties": props}


def _write_temp(content, suffix):
    tf = tempfile.NamedTemporaryFile(mode="w", suffix=suffix, delete=False, prefix="mcp_")
    tf.write(content)
    tf.flush()
    tf.close()
    _temp_files.append(tf.name)
    print(f"[mcp-adapter] wrote temp file {tf.name}", file=sys.stderr)
    return tf.name


def _build_cli_args(tool, inputs):
    raw = inputs.get("args", [])

    if tool == "ngspice":
        if "control" in inputs:
            return ["-b", _write_temp(inputs["control"], ".sp")] + raw
        if "netlist" in inputs:
            return ["-b", inputs["netlist"]] + raw

    elif tool == "xyce":
        if "netlist" in inputs:
            return [inputs["netlist"]] + raw

    elif tool == "magic":
        cli = list(raw)
        if "tcl_script" in inputs:
            cli = ["-dnull", "-noconsole", _write_temp(inputs["tcl_script"], ".tcl")] + cli
        if "gds" in inputs:
            cli.append(inputs["gds"])
        return cli

    elif tool == "klayout":
        cli = []
        if "drc_script" in inputs:
            cli += ["-b", "-r", inputs["drc_script"]]
        if "layout" in inputs:
            cli += ["-rd", "input=" + inputs["layout"]]
        return cli + raw

    elif tool == "netgen":
        if "layout_netlist" in inputs and "source_netlist" in inputs:
            return ["-batch", "lvs", inputs["layout_netlist"], inputs["source_netlist"]] + raw

    elif tool == "openvaf":
        if "va_file" in inputs:
            return [inputs["va_file"]] + raw

    elif tool == "openems":
        if "sim_script" in inputs:
            return [inputs["sim_script"]] + raw

    return raw


def _run_wrapper(wrapper_path, tool, inputs, timeout):
    cli_args = _build_cli_args(tool, inputs)
    cmd = [wrapper_path] + cli_args
    print(f"[mcp-adapter] running: {' '.join(cmd)}", file=sys.stderr)
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        stdout = proc.stdout.strip()
        if stdout:
            try:
                return json.loads(stdout)
            except json.JSONDecodeError:
                return {"tool": tool, "exit_code": proc.returncode,
                        "status": "FAIL" if proc.returncode != 0 else "WARN",
                        "summary": {}, "errors": ["wrapper output was not valid JSON"],
                        "warnings": [], "raw_output_excerpt": stdout[:500]}
        stderr_snippet = proc.stderr.strip()[:500] if proc.stderr else ""
        return {"tool": tool, "exit_code": proc.returncode,
                "status": "FAIL" if proc.returncode != 0 else "PASS",
                "summary": {}, "errors": [stderr_snippet] if stderr_snippet else [],
                "warnings": [], "raw_log": ""}
    except subprocess.TimeoutExpired:
        return {"tool": tool, "exit_code": -1, "status": "FAIL", "summary": {},
                "errors": [f"process timed out after {timeout}s — raise TOOL_TIMEOUT_S"],
                "warnings": [], "raw_log": ""}
    except FileNotFoundError:
        return {"tool": tool, "exit_code": 1, "status": "FAIL", "summary": {},
                "errors": [f"wrapper script not found: {wrapper_path}"], "warnings": [], "raw_log": ""}


def main():
    parser = argparse.ArgumentParser(description="Generic MCP stdio adapter for analog EDA wrapper scripts")
    parser.add_argument("--wrapper", required=True, help="Absolute path to the wrapper script")
    parser.add_argument("--tool", required=True, help="Tool name (ngspice, xyce, magic, ...)")
    parser.add_argument("--description", default="", help="One-line description shown in tools/list")
    parser.add_argument("--version", default="1.0.0")
    args = parser.parse_args()

    try:
        timeout = int(os.environ.get("TOOL_TIMEOUT_S", "300"))
    except ValueError:
        print("[mcp-adapter] WARNING: invalid TOOL_TIMEOUT_S, using 300s", file=sys.stderr)
        timeout = 300

    tool_name = args.tool
    wrapper_path = args.wrapper
    description = args.description or f"Run {tool_name} via output-filtering wrapper; returns compact JSON"

    print(f"[mcp-adapter] starting {tool_name} MCP server (wrapper={wrapper_path}, timeout={timeout}s)", file=sys.stderr)

    for raw_line in sys.stdin:
        raw_line = raw_line.strip()
        if not raw_line:
            continue
        try:
            req = json.loads(raw_line)
        except json.JSONDecodeError:
            print(f"[mcp-adapter] malformed JSON ignored: {raw_line[:100]}", file=sys.stderr)
            continue

        method = req.get("method", "")
        req_id = req.get("id")
        _raw_params = req.get("params")
        params = _raw_params if isinstance(_raw_params, dict) else {}

        if req_id is None:
            print(f"[mcp-adapter] notification: {method}", file=sys.stderr)
            continue

        if method == "initialize":
            _send(_ok(req_id, {"protocolVersion": "2024-11-05", "capabilities": {"tools": {}},
                               "serverInfo": {"name": f"{tool_name}-mcp", "version": args.version}}))
        elif method == "ping":
            _send(_ok(req_id, {}))
        elif method == "tools/list":
            _send(_ok(req_id, {"tools": [{"name": tool_name, "description": description,
                                          "inputSchema": _input_schema(tool_name)}]}))
        elif method == "tools/call":
            call_name = params.get("name", "")
            _raw_args = params.get("arguments")
            call_inputs = _raw_args if isinstance(_raw_args, dict) else {}
            if call_name != tool_name:
                _send(_err(req_id, -32602, f"Unknown tool '{call_name}'; this server exposes '{tool_name}'"))
                continue
            result = _run_wrapper(wrapper_path, tool_name, call_inputs, timeout)
            _send(_ok(req_id, {"content": [{"type": "text", "text": json.dumps(result, indent=2)}],
                               "isError": result.get("status") == "FAIL"}))
        else:
            _send(_err(req_id, -32601, f"Method not found: {method}"))


if __name__ == "__main__":
    main()
