"""Minimal client for the BlenderMCP addon socket (default 127.0.0.1:9876).

   python3 bl_client.py script.py        run a Python file inside the open Blender (prints its stdout)
   python3 bl_client.py info             scene summary
   python3 bl_client.py cmd TYPE [JSON]  any addon command, e.g. cmd get_polyhaven_status

`__file__` is injected into executed scripts, so they can locate their own folder (scripts/ -> project root)."""
import socket, json, sys, os

HOST, PORT = os.environ.get('BLENDER_MCP_HOST', '127.0.0.1'), int(os.environ.get('BLENDER_MCP_PORT', 9876))


def send(cmd, timeout=600):
    s = socket.create_connection((HOST, PORT), timeout=timeout)
    s.sendall(json.dumps(cmd).encode())
    buf = b""
    while True:
        chunk = s.recv(65536)
        if not chunk:
            break
        buf += chunk
        try:
            r = json.loads(buf.decode())
            break
        except Exception:
            continue
    s.close()
    return r


def run_file(path):
    path = os.path.abspath(path)
    code = f"__file__ = {path!r}\n" + open(path).read()
    return send({"type": "execute_code", "params": {"code": code}})


if __name__ == "__main__":
    if sys.argv[1] == "info":
        print(json.dumps(send({"type": "get_scene_info", "params": {}}), indent=1))
    elif sys.argv[1] == "cmd":
        params = json.loads(sys.argv[3]) if len(sys.argv) > 3 else {}
        print(json.dumps(send({"type": sys.argv[2], "params": params}), indent=1))
    else:
        r = run_file(sys.argv[1])
        if r.get("status") == "success":
            print(r["result"].get("result", r["result"]))
        else:
            print(json.dumps(r, indent=1))
            sys.exit(1)
