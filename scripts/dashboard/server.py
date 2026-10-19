#!/usr/bin/env python3
"""Servidor HTTP local e somente leitura para o estado do Ralph."""

from __future__ import annotations

import argparse
import json
import os
import re
import signal
import subprocess
import time
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

RUN_ID_RE = re.compile(r"^run-[A-Za-z0-9_-]+$")
MAX_LOG_BYTES = 256 * 1024


class RalphStore:
    def __init__(self, repo: Path) -> None:
        self.repo = repo.resolve()
        self.phases = self.repo / ".phases"

    def current_id(self) -> str | None:
        pointer = self.phases / "current"
        try:
            value = pointer.read_text(encoding="utf-8").strip()
        except OSError:
            return None
        return value if RUN_ID_RE.fullmatch(value) else None

    def run_dir(self, run_id: str) -> Path | None:
        if not RUN_ID_RE.fullmatch(run_id):
            return None
        candidate = (self.phases / "runs" / run_id).resolve()
        runs_root = (self.phases / "runs").resolve()
        if candidate.parent != runs_root or not candidate.is_dir():
            return None
        return candidate

    def state_dir(self, run_id: str | None) -> Path | None:
        if run_id:
            run = self.run_dir(run_id)
            return run / "state" if run else None
        legacy = self.phases / "state"
        return legacy if legacy.is_dir() else None

    @staticmethod
    def _read_tsv(path: Path) -> tuple[dict[str, str], list[dict], list[dict]]:
        meta: dict[str, str] = {}
        phases: list[dict] = []
        tasks: list[dict] = []
        try:
            lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            return meta, phases, tasks
        for line in lines:
            parts = line.split("\t")
            if not parts:
                continue
            if parts[0] == "META" and len(parts) >= 3:
                meta[parts[1]] = "\t".join(parts[2:])
            elif parts[0] == "PHASE" and len(parts) == 2:
                meta["phase"] = parts[1]
            elif parts[0] == "ACTIVITY" and len(parts) >= 2:
                meta["activity"] = "\t".join(parts[1:])
            elif parts[0] == "PHASE" and len(parts) >= 6:
                phases.append({
                    "number": parts[1], "status": parts[2], "attempt": parts[3],
                    "gates": parts[4].split(), "title": "\t".join(parts[5:]), "tasks": [],
                })
            elif parts[0] == "TASK" and len(parts) >= 5:
                tasks.append({
                    "phase": parts[1], "number": parts[2], "status": parts[3],
                    "title": "\t".join(parts[4:]),
                })
        phase_index = {phase["number"]: phase for phase in phases}
        for task in tasks:
            phase = phase_index.get(task["phase"])
            if phase:
                phase["tasks"].append(task)
        return meta, phases, tasks

    @staticmethod
    def _read_live(path: Path) -> tuple[dict[str, str], list[dict]]:
        meta: dict[str, str] = {}
        tasks: list[dict] = []
        try:
            lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            return meta, tasks
        for line in lines:
            parts = line.split("\t")
            if parts[0] == "PHASE" and len(parts) >= 2:
                meta["phase"] = parts[1]
            elif parts[0] == "ACTIVITY" and len(parts) >= 2:
                meta["activity"] = "\t".join(parts[1:])
            elif parts[0] == "LIVE" and len(parts) >= 3:
                tasks.append({"number": parts[1], "status": parts[2]})
        return meta, tasks

    def run_state(self, run_id: str | None = None) -> dict:
        resolved_id = run_id or self.current_id()
        state_dir = self.state_dir(resolved_id)
        if state_dir is None:
            return {"version": 1, "run": None, "phases": [], "updated_at": int(time.time())}
        meta, phases, _ = self._read_tsv(state_dir / "run.tsv")
        live_meta, live_tasks = self._read_live(state_dir / "live.tsv")
        for key in ("activity",):
            if key in live_meta and live_meta[key]:
                meta[key] = live_meta[key]
        phase_number = live_meta.get("phase")
        if phase_number:
            by_phase = {phase["number"]: phase for phase in phases}
            for live_task in live_tasks:
                phase = by_phase.get(phase_number)
                if not phase:
                    continue
                for task in phase["tasks"]:
                    if task["number"] == live_task["number"] and task["status"] not in {"done", "incomplete"}:
                        task["status"] = live_task["status"]
        return {
            "version": 1,
            "run": {"id": resolved_id or meta.get("run"), "meta": meta},
            "phases": phases,
            "updated_at": int(time.time()),
        }

    def runs(self) -> list[dict]:
        runs_root = self.phases / "runs"
        result: list[dict] = []
        if runs_root.is_dir():
            for directory in sorted(runs_root.iterdir(), reverse=True):
                if not directory.is_dir() or not RUN_ID_RE.fullmatch(directory.name):
                    continue
                state = self.run_state(directory.name)
                meta = state["run"]["meta"] if state["run"] else {}
                result.append({"id": directory.name, "project": meta.get("project"), "engine": meta.get("engine"), "status": meta.get("status"), "started": meta.get("started"), "ended": meta.get("ended")})
        current = self.current_id()
        if not result and (self.phases / "state").is_dir():
            legacy = self.run_state(None)
            meta = legacy["run"]["meta"] if legacy["run"] else {}
            result.append({"id": None, "project": meta.get("project"), "engine": meta.get("engine"), "status": meta.get("status"), "started": meta.get("started"), "ended": meta.get("ended")})
        for item in result:
            item["current"] = item["id"] == current
        return result

    def logs(self, run_id: str | None, offset: int) -> dict:
        resolved_id = run_id or self.current_id()
        run = self.run_dir(resolved_id) if resolved_id else None
        log_dir = (run / "logs") if run else (self.phases / "logs")
        try:
            files = sorted(path for path in log_dir.iterdir() if path.is_file())
            data = b"".join(
                b"\n== " + path.name.encode("utf-8", errors="replace") + b" ==\n" + path.read_bytes()
                for path in files
            )
            size = len(data)
            start = max(0, min(offset, size))
            if size - start > MAX_LOG_BYTES:
                start = size - MAX_LOG_BYTES
        except OSError:
            return {"offset": 0, "next_offset": 0, "text": "", "truncated": False}
        chunk = data[start : start + MAX_LOG_BYTES]
        return {"offset": start, "next_offset": start + len(chunk), "text": chunk.decode("utf-8", errors="replace"), "truncated": start > offset}

    @staticmethod
    def _is_pid_alive(pid: int) -> bool:
        if pid <= 1:
            return False
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return False
        except PermissionError:
            return True
        except OSError:
            return False
        try:
            state = subprocess.check_output(
                ["ps", "-p", str(pid), "-o", "state="],
                text=True, errors="replace",
            ).strip()
            if not state or state.startswith("Z"):
                return False
        except Exception:
            return False
        return True

    @staticmethod
    def _get_process_tree(root_pid: int) -> list[int]:
        ppid_map: dict[int, list[int]] = {}
        try:
            out = subprocess.check_output(["ps", "-A", "-o", "pid,ppid"], text=True, errors="replace")
            for line in out.strip().splitlines()[1:]:
                parts = line.strip().split()
                if len(parts) >= 2 and parts[0].isdigit() and parts[1].isdigit():
                    child_pid, parent_pid = int(parts[0]), int(parts[1])
                    ppid_map.setdefault(parent_pid, []).append(child_pid)
        except Exception:
            return []

        descendants: list[int] = []

        def collect(p: int) -> None:
            for child in ppid_map.get(p, []):
                collect(child)
                descendants.append(child)

        collect(root_pid)
        return descendants

    def _verify_process_is_ralph(self, pid: int) -> bool:
        if pid <= 1 or pid == os.getpid():
            return False
        lock_file = self.phases / ".lock" / "pid"
        if lock_file.is_file():
            try:
                if lock_file.read_text(encoding="utf-8").strip() == str(pid):
                    return True
            except OSError:
                pass
        try:
            cmd = subprocess.check_output(
                ["ps", "-p", str(pid), "-o", "command="],
                text=True, errors="replace",
            ).strip()
        except Exception:
            return False
        cmd_lower = cmd.lower()
        return "ralph" in cmd_lower or str(self.repo) in cmd

    def _cleanup_stale_lock(self, pid: int | None = None) -> None:
        lock_dir = self.phases / ".lock"
        lock_pid_file = lock_dir / "pid"
        if lock_dir.is_dir():
            if lock_pid_file.is_file():
                try:
                    content = lock_pid_file.read_text(encoding="utf-8").strip()
                    if pid is None or content == str(pid):
                        lock_pid_file.unlink(missing_ok=True)
                except OSError:
                    pass
            try:
                lock_dir.rmdir()
            except OSError:
                pass

    def _mark_run_stopped(self, run_id: str | None) -> None:
        state_dir = self.state_dir(run_id)
        if not state_dir or not state_dir.is_dir():
            return
        tsv_file = state_dir / "run.tsv"
        now = str(int(time.time()))
        if tsv_file.is_file():
            try:
                lines = tsv_file.read_text(encoding="utf-8", errors="replace").splitlines()
                updated_lines: list[str] = []
                has_ended = False
                status_updated = False
                for line in lines:
                    parts = line.split("\t")
                    if parts and parts[0] == "META":
                        if len(parts) >= 3 and parts[1] == "status":
                            if parts[2] in {"running", "waiting"}:
                                updated_lines.append("META\tstatus\tstopped")
                                status_updated = True
                            else:
                                updated_lines.append(line)
                        elif len(parts) >= 2 and parts[1] == "ended":
                            has_ended = True
                            if len(parts) == 2 or not parts[2] or parts[2] == "—":
                                updated_lines.append(f"META\tended\t{now}")
                            else:
                                updated_lines.append(line)
                        else:
                            updated_lines.append(line)
                    else:
                        updated_lines.append(line)
                if status_updated and not has_ended:
                    updated_lines.append(f"META\tended\t{now}")
                tsv_file.write_text("\n".join(updated_lines) + "\n", encoding="utf-8")
            except OSError:
                pass
        live_file = state_dir / "live.tsv"
        try:
            live_file.write_text("ACTIVITY\tExecução encerrada pelo usuário\n", encoding="utf-8")
        except OSError:
            pass

    def stop_run(self, run_id: str | None = None) -> tuple[bool, str, int | None]:
        resolved_id = run_id or self.current_id()
        state = self.run_state(resolved_id)
        meta = (state.get("run") or {}).get("meta", {})

        lock_file = self.phases / ".lock" / "pid"
        lock_pid: int | None = None
        if lock_file.is_file():
            try:
                raw = lock_file.read_text(encoding="utf-8").strip()
                if raw.isdigit():
                    lock_pid = int(raw)
            except OSError:
                pass

        meta_pid: int | None = None
        raw_meta_pid = meta.get("pid")
        if raw_meta_pid and str(raw_meta_pid).isdigit():
            meta_pid = int(raw_meta_pid)

        target_pid = lock_pid or meta_pid
        is_active_status = meta.get("status") in {"running", "waiting"}

        if target_pid is None:
            if not is_active_status and not lock_file.is_file():
                return False, "Nenhuma execução ativa encontrada para encerrar", None
            return False, "PID da execução não foi encontrado", None

        if not self._is_pid_alive(target_pid):
            self._cleanup_stale_lock(target_pid)
            self._mark_run_stopped(resolved_id)
            return True, f"Execução já havia finalizado (PID {target_pid}). Lock e estado foram limpos.", target_pid

        if not self._verify_process_is_ralph(target_pid):
            return False, f"Processo PID {target_pid} não confere com execução do Ralph", target_pid

        # 1. Envia SIGTERM aos descendentes e ao processo alvo
        descendants = self._get_process_tree(target_pid)
        for child in descendants:
            try:
                os.kill(child, signal.SIGTERM)
            except OSError:
                pass
        try:
            os.kill(target_pid, signal.SIGTERM)
        except OSError:
            pass

        # 2. Aguarda até 3 segundos pela saída graciosa
        deadline = time.time() + 3.0
        while time.time() < deadline:
            if not self._is_pid_alive(target_pid):
                break
            time.sleep(0.1)

        # 3. Força com SIGKILL se ainda estiver ativo
        if self._is_pid_alive(target_pid):
            for child in self._get_process_tree(target_pid):
                try:
                    os.kill(child, signal.SIGKILL)
                except OSError:
                    pass
            try:
                os.kill(target_pid, signal.SIGKILL)
            except OSError:
                pass
            deadline = time.time() + 1.0
            while time.time() < deadline:
                if not self._is_pid_alive(target_pid):
                    break
                time.sleep(0.05)

        self._cleanup_stale_lock(target_pid)
        self._mark_run_stopped(resolved_id)

        if self._is_pid_alive(target_pid):
            return False, f"Não foi possível encerrar o processo PID {target_pid}", target_pid

        return True, f"Execução (PID {target_pid}) encerrada com sucesso", target_pid


class Handler(SimpleHTTPRequestHandler):
    store: RalphStore
    assets: Path

    def log_message(self, *_: object) -> None:
        return

    def json(self, payload: object, status: HTTPStatus = HTTPStatus.OK) -> None:
        raw = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        parts = [unquote(part) for part in parsed.path.split("/") if part]
        if parts[:3] != ["api", "v1", "runs"]:
            return super().do_GET()
        query = parse_qs(parsed.query)
        if len(parts) == 3:
            return self.json({"runs": self.store.runs()})
        run_id = parts[3] if len(parts) >= 4 else None
        if run_id == "current":
            return self.json(self.store.run_state())
        if not RUN_ID_RE.fullmatch(run_id or ""):
            return self.json({"error": "run not found"}, HTTPStatus.NOT_FOUND)
        if len(parts) == 4:
            if not self.store.run_dir(run_id):
                return self.json({"error": "run not found"}, HTTPStatus.NOT_FOUND)
            return self.json(self.store.run_state(run_id))
        if len(parts) == 5 and parts[4] == "logs":
            try:
                offset = max(0, int(query.get("after", ["0"])[0]))
            except ValueError:
                offset = 0
            return self.json(self.store.logs(run_id, offset))
        return self.json({"error": "not found"}, HTTPStatus.NOT_FOUND)

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        parts = [unquote(part) for part in parsed.path.split("/") if part]
        if len(parts) == 4 and parts[:4] == ["api", "v1", "runs", "stop"]:
            success, message, pid = self.store.stop_run()
            status = HTTPStatus.OK if success else HTTPStatus.BAD_REQUEST
            return self.json({"ok": success, "message": message, "pid": pid}, status)
        if len(parts) == 5 and parts[:3] == ["api", "v1", "runs"] and parts[4] == "stop":
            run_id = parts[3]
            if run_id == "current":
                success, message, pid = self.store.stop_run()
            elif RUN_ID_RE.fullmatch(run_id):
                success, message, pid = self.store.stop_run(run_id)
            else:
                return self.json({"ok": False, "error": "ID de execução inválido"}, HTTPStatus.BAD_REQUEST)
            status = HTTPStatus.OK if success else HTTPStatus.BAD_REQUEST
            return self.json({"ok": success, "message": message, "pid": pid}, status)
        return self.json({"error": "endpoint not found"}, HTTPStatus.NOT_FOUND)

    def translate_path(self, path: str) -> str:
        parsed = urlparse(path).path
        if parsed in {"", "/"}:
            return str(self.assets / "index.html")
        target = (self.assets / parsed.lstrip("/")).resolve()
        if target.parent != self.assets.resolve() or not target.is_file():
            return str(self.assets / "missing")
        return str(target)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True)
    parser.add_argument("--port", type=int, required=True)
    args = parser.parse_args()
    Handler.store = RalphStore(Path(args.repo))
    Handler.assets = Path(__file__).with_name("web")
    server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
