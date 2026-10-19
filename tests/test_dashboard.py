#!/usr/bin/env python3
"""Testes automatizados para scripts/dashboard/server.py e funcionalidade de encerrar o Ralph."""

from __future__ import annotations

import json
import os
import shutil
import signal
import subprocess
import tempfile
import time
import unittest
import urllib.request
import urllib.error
from pathlib import Path


class DashboardServerTest(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp(prefix="ralph-test-")
        self.repo = Path(self.tmp_dir)
        self.phases = self.repo / ".phases"
        self.runs_dir = self.phases / "runs"
        self.runs_dir.mkdir(parents=True, exist_ok=True)

        # Port for test server
        self.port = 17332
        self.server_proc = None

    def tearDown(self):
        if self.server_proc:
            try:
                self.server_proc.terminate()
                self.server_proc.wait(timeout=2)
            except Exception:
                try:
                    self.server_proc.kill()
                except Exception:
                    pass
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def start_server(self):
        harness_root = Path(__file__).resolve().parent.parent
        server_py = harness_root / "scripts" / "dashboard" / "server.py"

        # Try to find a free port
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(("127.0.0.1", 0))
        self.port = s.getsockname()[1]
        s.close()

        self.server_proc = subprocess.Popen(
            ["python3", str(server_py), "--repo", str(self.repo), "--port", str(self.port)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        time.sleep(0.5)

    def request(self, path: str, method: str = "GET", data: dict | None = None) -> tuple[int, dict]:
        url = f"http://127.0.0.1:{self.port}{path}"
        body = json.dumps(data).encode("utf-8") if data is not None else None
        req = urllib.request.Request(url, data=body, method=method)
        req.add_header("Content-Type", "application/json")
        try:
            with urllib.request.urlopen(req) as resp:
                status = resp.status
                payload = json.loads(resp.read().decode("utf-8"))
                return status, payload
        except urllib.error.HTTPError as e:
            status = e.code
            payload = json.loads(e.read().decode("utf-8"))
            return status, payload

    def test_no_active_run_stop(self):
        self.start_server()
        status, data = self.request("/api/v1/runs/stop", method="POST")
        self.assertEqual(status, 400)
        self.assertFalse(data.get("ok"))
        self.assertIn("Nenhuma execução", data.get("message", ""))

    def test_stop_active_mock_ralph(self):
        run_id = f"run-20261013-120000-{os.getpid()}"
        run_dir = self.runs_dir / run_id
        state_dir = run_dir / "state"
        state_dir.mkdir(parents=True, exist_ok=True)

        (self.phases / "current").write_text(run_id, encoding="utf-8")

        # Spawn a long running process simulating ralph.sh and a child
        mock_script = (
            "#!/usr/bin/env bash\n"
            "trap 'exit 0' TERM INT\n"
            "sleep 30 &\n"
            "wait $!\n"
        )
        script_file = self.repo / "ralph.sh"
        script_file.write_text(mock_script, encoding="utf-8")
        script_file.chmod(0o755)

        proc = subprocess.Popen([str(script_file)])
        pid = proc.pid

        # Setup lock and run.tsv
        lock_dir = self.phases / ".lock"
        lock_dir.mkdir(parents=True, exist_ok=True)
        (lock_dir / "pid").write_text(str(pid), encoding="utf-8")

        run_tsv = (
            f"META\tproject\ttest\n"
            f"META\tstatus\trunning\n"
            f"META\tstarted\t{int(time.time())}\n"
            f"META\tpid\t{pid}\n"
            f"META\trun\t{run_id}\n"
        )
        (state_dir / "run.tsv").write_text(run_tsv, encoding="utf-8")
        (state_dir / "live.tsv").write_text("ACTIVITY\ttrabalhando...\n", encoding="utf-8")

        self.start_server()

        # Call POST to stop
        status, data = self.request("/api/v1/runs/current/stop", method="POST")
        self.assertEqual(status, 200)
        self.assertTrue(data.get("ok"))
        self.assertEqual(data.get("pid"), pid)

        # Process should be terminated
        time.sleep(0.5)
        self.assertIsNotNone(proc.poll())

        # Lock should be cleaned up
        self.assertFalse((lock_dir / "pid").exists())
        self.assertFalse(lock_dir.exists())

        # run.tsv should reflect status stopped
        updated_tsv = (state_dir / "run.tsv").read_text(encoding="utf-8")
        self.assertIn("META\tstatus\tstopped", updated_tsv)
        self.assertIn("META\tended\t", updated_tsv)

        # live.tsv should reflect user termination
        updated_live = (state_dir / "live.tsv").read_text(encoding="utf-8")
        self.assertIn("Execução encerrada", updated_live)

    def test_stale_lock_cleanup_on_stop(self):
        run_id = f"run-20261013-120000-stale"
        run_dir = self.runs_dir / run_id
        state_dir = run_dir / "state"
        state_dir.mkdir(parents=True, exist_ok=True)

        (self.phases / "current").write_text(run_id, encoding="utf-8")

        # Fake dead PID
        dead_pid = 999999
        lock_dir = self.phases / ".lock"
        lock_dir.mkdir(parents=True, exist_ok=True)
        (lock_dir / "pid").write_text(str(dead_pid), encoding="utf-8")

        run_tsv = (
            f"META\tproject\ttest\n"
            f"META\tstatus\trunning\n"
            f"META\tstarted\t{int(time.time())}\n"
            f"META\tpid\t{dead_pid}\n"
            f"META\trun\t{run_id}\n"
        )
        (state_dir / "run.tsv").write_text(run_tsv, encoding="utf-8")

        self.start_server()

        status, data = self.request("/api/v1/runs/stop", method="POST")
        self.assertEqual(status, 200)
        self.assertTrue(data.get("ok"))
        self.assertIn("Lock e estado foram limpos", data.get("message", ""))

        # Lock cleaned
        self.assertFalse((lock_dir / "pid").exists())

        # Status updated
        updated_tsv = (state_dir / "run.tsv").read_text(encoding="utf-8")
        self.assertIn("META\tstatus\tstopped", updated_tsv)

    def test_stop_by_explicit_run_id(self):
        run_id = f"run-20261013-120000-explicit"
        run_dir = self.runs_dir / run_id
        state_dir = run_dir / "state"
        state_dir.mkdir(parents=True, exist_ok=True)

        (self.phases / "current").write_text("run-other", encoding="utf-8")

        mock_script = (
            "#!/usr/bin/env bash\n"
            "trap 'exit 0' TERM INT\n"
            "sleep 30 &\n"
            "wait $!\n"
        )
        script_file = self.repo / "ralph.sh"
        script_file.write_text(mock_script, encoding="utf-8")
        script_file.chmod(0o755)

        proc = subprocess.Popen([str(script_file)])
        pid = proc.pid

        lock_dir = self.phases / ".lock"
        lock_dir.mkdir(parents=True, exist_ok=True)
        (lock_dir / "pid").write_text(str(pid), encoding="utf-8")

        run_tsv = (
            f"META\tproject\ttest\n"
            f"META\tstatus\trunning\n"
            f"META\tstarted\t{int(time.time())}\n"
            f"META\tpid\t{pid}\n"
            f"META\trun\t{run_id}\n"
        )
        (state_dir / "run.tsv").write_text(run_tsv, encoding="utf-8")

        self.start_server()

        status, data = self.request(f"/api/v1/runs/{run_id}/stop", method="POST")
        self.assertEqual(status, 200)
        self.assertTrue(data.get("ok"))
        self.assertEqual(data.get("pid"), pid)

        time.sleep(0.5)
        self.assertIsNotNone(proc.poll())

    def test_invalid_run_id_stop(self):
        self.start_server()
        status, data = self.request("/api/v1/runs/invalid-id!/stop", method="POST")
        self.assertEqual(status, 400)
        self.assertFalse(data.get("ok"))
        self.assertIn("inválido", data.get("error", ""))

    def test_web_assets_content(self):
        harness_root = Path(__file__).resolve().parent.parent
        web_dir = harness_root / "scripts" / "dashboard" / "web"

        index_html = (web_dir / "index.html").read_text(encoding="utf-8")
        self.assertIn('id="stop-run"', index_html)
        self.assertIn("Encerrar Ralph", index_html)

        app_js = (web_dir / "app.js").read_text(encoding="utf-8")
        self.assertIn("stopped:'⏹ Encerrado'", app_js)
        self.assertIn("stop-run", app_js)
        self.assertIn("/stop", app_js)

        app_css = (web_dir / "app.css").read_text(encoding="utf-8")
        self.assertIn(".btn-danger", app_css)
        self.assertIn(".stopped", app_css)


if __name__ == "__main__":
    unittest.main()
