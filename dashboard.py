#!/usr/bin/env python3
"""NetForge dashboard — a branded CLI that drives the real project features.

Modes (argparse):
  (no args)   interactive, EOF/pipe-safe menu loop
  --demo      scripted non-interactive showcase: runs a real loopback
              handshake + file transfer end-to-end and exits 0
  --json      machine-readable summary of the --demo run
  --help      argparse help

Everything here calls the ACTUAL NetForge classes (Server_Dashboard, the
General_User client, Report_Generator, the shared control-code tables). No
network or hardware is required: the loopback self-test binds an ephemeral
port on 127.0.0.1, serves from a daemon thread, and cleans up temp files.
"""

import argparse
import io
import json
import os
import socket
import sys
import tempfile
import threading
import time

# Make sibling project modules importable no matter the working directory.
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from Client import General_User
from ReportGenerator import Report_Generator
from ServerDashboard import Server_Dashboard
from ServerSettings import Server

# --------------------------------------------------------------------------- #
# Optional rich look & feel, with a clean plain-ANSI fallback.
# --------------------------------------------------------------------------- #
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.prompt import Prompt
    from rich import box

    _console = Console()
    _HAVE_RICH = True
except Exception:  # pragma: no cover - exercised only when rich is missing
    _console = None
    _HAVE_RICH = False


BRAND = "NetForge"
TAGLINE = "TCP file-transfer server framework with a 3-byte handshake protocol"

# Plain-ANSI colours for the fallback path.
_C = {
    "reset": "\033[0m", "bold": "\033[1m", "dim": "\033[2m",
    "cyan": "\033[36m", "green": "\033[32m", "red": "\033[31m",
    "yellow": "\033[33m", "magenta": "\033[35m", "blue": "\033[34m",
}


def _supports_color():
    return sys.stdout.isatty()


def _p(text=""):
    if _HAVE_RICH:
        _console.print(text)
    else:
        print(text)


def _ok(text):
    if _HAVE_RICH:
        _console.print(f"[bold green]{text}[/bold green]")
    elif _supports_color():
        print(f"{_C['green']}{_C['bold']}{text}{_C['reset']}")
    else:
        print(text)


def _err(text):
    if _HAVE_RICH:
        _console.print(f"[bold red]{text}[/bold red]")
    elif _supports_color():
        print(f"{_C['red']}{_C['bold']}{text}{_C['reset']}")
    else:
        print(text)


def banner():
    """Branded banner: project name + one-line tagline."""
    if _HAVE_RICH:
        _console.print(
            Panel.fit(
                f"[bold cyan]{BRAND}[/bold cyan]\n[dim]{TAGLINE}[/dim]",
                border_style="cyan", box=box.DOUBLE, padding=(1, 4),
            )
        )
    else:
        c = _C if _supports_color() else {k: "" for k in _C}
        line = "=" * 66
        print(f"{c['cyan']}{line}{c['reset']}")
        print(f"{c['cyan']}{c['bold']}   {BRAND}{c['reset']}")
        print(f"{c['dim']}   {TAGLINE}{c['reset']}")
        print(f"{c['cyan']}{line}{c['reset']}")


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def _free_port():
    """Grab an OS-assigned free TCP port on the loopback interface."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


def _sample_users():
    """A representative connected-users list, shaped like ConnClientInfo rows."""
    now = time.strftime("%Y-%m-%d %H:%M:%S")
    return [
        {
            "User No.": 1, "User ID": "alice", "Username": "user",
            "User IP": "127.0.0.1", "User Port": 51001,
            "User Type": "client", "User Application": "sender",
            "Connection Command": "connect", "Connected Time": now,
            "Connection Status": "Connection established",
        },
        {
            "User No.": 2, "User ID": "bob", "Username": "user",
            "User IP": "127.0.0.1", "User Port": 51002,
            "User Type": "client", "User Application": "receiver",
            "Connection Command": "connect", "Connected Time": now,
            "Connection Status": "Connection established",
        },
        {
            "User No.": 3, "User ID": "carol", "Username": "user",
            "User IP": "127.0.0.1", "User Port": 51003,
            "User Type": "admin", "User Application": "browser",
            "Connection Command": "connect", "Connected Time": now,
            "Connection Status": "Connection established",
        },
    ]


class _quiet_stdout:
    """Context manager that swallows the chatty print() output of helpers."""

    def __enter__(self):
        self._old = sys.stdout
        sys.stdout = io.StringIO()
        return self

    def __exit__(self, *exc):
        sys.stdout = self._old
        return False


# --------------------------------------------------------------------------- #
# Real feature: end-to-end loopback self-test
# --------------------------------------------------------------------------- #
def run_loopback_selftest(verbose=True):
    """Start a real Server_Dashboard on an ephemeral port in a daemon thread,
    then run the real client handshake for BOTH a sender upload and a receiver
    download. Returns a result dict; raises on failure."""
    result = {"port": None, "upload_ok": False, "download_ok": False,
              "uploaded_bytes": 0, "downloaded_bytes": 0, "roundtrip_ok": False}

    tmpdir = tempfile.mkdtemp(prefix="netforge_demo_")
    storage = os.path.join(tmpdir, "storage")
    downloads = os.path.join(tmpdir, "downloads")
    os.makedirs(storage, exist_ok=True)

    port = _free_port()
    result["port"] = port
    server = Server_Dashboard(ServerIP="127.0.0.1", ServerPort=port, verbose=False)
    server.storage_dir = storage

    thread = threading.Thread(target=server.StartServer, daemon=True)
    thread.start()

    # Wait until the listener actually accepts connections (bounded).
    deadline = time.time() + 5
    while time.time() < deadline:
        probe = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        probe.settimeout(0.3)
        try:
            probe.connect(("127.0.0.1", port))
            probe.close()
            break
        except OSError:
            probe.close()
            time.sleep(0.05)
    else:
        server.stop()
        raise RuntimeError("loopback server did not start in time")

    if verbose:
        _p(f"  [*] Server listening on 127.0.0.1:{port} (daemon thread)")

    try:
        # --- 1) sender handshake: client uploads a file to the server ------- #
        payload = b"NetForge loopback payload \x00\x01\x02\n" * 512
        src = os.path.join(tmpdir, "payload.bin")
        with open(src, "wb") as f:
            f.write(payload)

        up_client = General_User("127.0.0.1", port, user_id="demo_sender", verbose=False)
        up_client.client_socket.settimeout(5)
        result["upload_ok"] = bool(
            up_client.ConnToServer("demo_sender", 0x3B, filepath=src))  # 0x3B = sender

        saved = os.path.join(storage, "payload.bin")
        deadline = time.time() + 5
        while not os.path.exists(saved) and time.time() < deadline:
            time.sleep(0.05)
        result["uploaded_bytes"] = os.path.getsize(saved) if os.path.exists(saved) else 0
        if verbose:
            _p(f"  [+] sender handshake -> uploaded {result['uploaded_bytes']} bytes")

        # --- 2) receiver handshake: client downloads it back --------------- #
        down_client = General_User("127.0.0.1", port, user_id="demo_receiver", verbose=False)
        down_client.client_socket.settimeout(5)
        got = down_client.ConnToServer("demo_receiver", 0x2B,       # 0x2B = receiver
                                       filepath="payload.bin", dest_dir=downloads)
        result["download_ok"] = bool(got)
        got_path = os.path.join(downloads, "payload.bin")
        result["downloaded_bytes"] = (
            os.path.getsize(got_path) if os.path.exists(got_path) else 0)
        if verbose:
            _p(f"  [+] receiver handshake -> downloaded {result['downloaded_bytes']} bytes")

        # --- 3) byte-for-byte round-trip integrity ------------------------- #
        if os.path.exists(got_path):
            with open(got_path, "rb") as f:
                result["roundtrip_ok"] = f.read() == payload
    finally:
        server.stop()
        thread.join(5)
        # Clean up all temp files we created.
        try:
            import shutil
            shutil.rmtree(tmpdir, ignore_errors=True)
        except Exception:
            pass

    if not (result["upload_ok"] and result["download_ok"] and result["roundtrip_ok"]):
        raise RuntimeError(f"loopback self-test failed: {result}")
    return result


# --------------------------------------------------------------------------- #
# Real feature: protocol / status-code reference
# --------------------------------------------------------------------------- #
_PROTOCOL_ROWS = [
    ("Frame 1 (client -> server)", "3 bytes", "connect(0xAA) | client(0x2A) | request(0x3C)"),
    ("User ID (client -> server)", "N+1 bytes", "utf-8 id + null terminator 0x00"),
    ("Frame 2 (server -> client)", "3 bytes", "accepted(0x6C) | server(0x0A) | client(0x2A)"),
    ("Frame 3 (client -> server)", "3 bytes", "request(0x3C) | client(0x2A) | app(0x2B/0x3B)"),
    ("Frame 4 (server -> client)", "3 bytes", "accepted(0x6C) | server(0x0A) | app-echo"),
    ("File frame", "8+N+8+size", "!Q namelen | name | !Q size | raw bytes"),
    ("Transfer status", "1 byte", "0x09 success | 0x10 failed"),
]


def show_protocol_reference():
    """Show the handshake framing + a slice of the real control-code table."""
    srv = Server()  # the real shared table lives here
    codes = srv.user_status_code

    if _HAVE_RICH:
        t = Table(title="NetForge handshake framing", box=box.SIMPLE_HEAVY,
                  header_style="bold cyan")
        t.add_column("Step", style="bold")
        t.add_column("Size", style="yellow")
        t.add_column("Bytes / meaning")
        for step, size, meaning in _PROTOCOL_ROWS:
            t.add_row(step, size, meaning)
        _console.print(t)

        ct = Table(title="Control codes (from Server.user_status_code)",
                   box=box.SIMPLE_HEAVY, header_style="bold magenta")
        ct.add_column("Hex", style="green")
        ct.add_column("Meaning")
        for code in sorted(codes):
            ct.add_row(f"0x{code:02X}", codes[code])
        _console.print(ct)
    else:
        print("\nNetForge handshake framing")
        print("-" * 66)
        for step, size, meaning in _PROTOCOL_ROWS:
            print(f"  {step:<28} {size:<10} {meaning}")
        print("\nControl codes (from Server.user_status_code)")
        print("-" * 66)
        for code in sorted(codes):
            print(f"  0x{code:02X}  {codes[code]}")
    return codes


# --------------------------------------------------------------------------- #
# Real feature: reports of a sample connected-users list
# --------------------------------------------------------------------------- #
def generate_user_reports(out_dir=None, verbose=True):
    """Use the real Report_Generator to emit CSV + JSON of a users list."""
    out_dir = out_dir or os.path.join(PROJECT_ROOT, "reports")
    os.makedirs(out_dir, exist_ok=True)
    stamp = time.strftime("%Y%m%d_%H%M%S")
    csv_path = os.path.join(out_dir, f"connected_users_{stamp}.csv")
    json_path = os.path.join(out_dir, f"connected_users_{stamp}.json")

    users = _sample_users()
    reporter = Report_Generator()
    with _quiet_stdout():
        reporter.CSV_GenerateReport(users, filename=csv_path)
        reporter.JSON_GenerateReport(users, filename=json_path)

    if verbose:
        _ok(f"  [+] CSV report:  {csv_path}")
        _ok(f"  [+] JSON report: {json_path}")
        _p(f"  [+] {len(users)} connected-user records written")
    return {"csv": csv_path, "json": json_path, "records": len(users)}


# --------------------------------------------------------------------------- #
# Real feature: system stats
# --------------------------------------------------------------------------- #
def show_system_stats():
    """Live host stats via psutil if available, else stdlib fallbacks."""
    stats = {}
    try:
        import psutil
        stats["cpu_percent"] = psutil.cpu_percent(interval=0.2)
        stats["cpu_cores"] = psutil.cpu_count(logical=True)
        vm = psutil.virtual_memory()
        stats["mem_total_mb"] = round(vm.total / 1024 / 1024)
        stats["mem_used_pct"] = vm.percent
        stats["boot_epoch"] = int(psutil.boot_time())
    except Exception:
        stats["cpu_cores"] = os.cpu_count()
        try:
            la1, la5, la15 = os.getloadavg()
            stats["loadavg"] = f"{la1:.2f} {la5:.2f} {la15:.2f}"
        except Exception:
            pass
    stats["hostname"] = socket.gethostname()
    stats["pid"] = os.getpid()
    stats["python"] = sys.version.split()[0]

    if _HAVE_RICH:
        t = Table(title="Host / runtime stats", box=box.SIMPLE_HEAVY,
                  header_style="bold cyan")
        t.add_column("Metric", style="bold")
        t.add_column("Value", style="green")
        for k, v in stats.items():
            t.add_row(k, str(v))
        _console.print(t)
    else:
        print("\nHost / runtime stats")
        print("-" * 40)
        for k, v in stats.items():
            print(f"  {k:<16} {v}")
    return stats


def show_run_commands():
    """Print the commands to run the REAL server and client."""
    py = "python3"
    lines = [
        "Start the real server (auto IP + first free port 8000-8500):",
        f"    {py} ServerDashboard.py --verbose",
        f"    {py} ServerDashboard.py --host 127.0.0.1 --port 8000 --verbose",
        "",
        "Upload a file (sender role):",
        f"    {py} Client.py --host 127.0.0.1 --port 8000 --app sender --file ./myfile.txt",
        "",
        "Download a file (receiver role):",
        f"    {py} Client.py --host 127.0.0.1 --port 8000 --app receiver --file myfile.txt --dest-dir ./got",
    ]
    if _HAVE_RICH:
        _console.print(Panel("\n".join(lines), title="Run the real server / client",
                             border_style="blue", box=box.ROUNDED))
    else:
        print("\nRun the real server / client")
        print("-" * 66)
        for ln in lines:
            print(ln)


# --------------------------------------------------------------------------- #
# Demo mode
# --------------------------------------------------------------------------- #
def run_demo(as_json=False):
    """Scripted, non-interactive showcase of the real features. Exits fast."""
    summary = {}
    if not as_json:
        banner()
        _p("[bold]Running NetForge --demo showcase[/bold]" if _HAVE_RICH
           else "Running NetForge --demo showcase")
        _p()

    # 1) The headline feature: a real end-to-end loopback file transfer.
    if not as_json:
        _p("1) End-to-end loopback self-test (real handshake + file transfer)")
    res = run_loopback_selftest(verbose=not as_json)
    summary["loopback"] = res
    if not as_json:
        _ok("  [+] handshake OK, upload OK, download OK, byte-for-byte round-trip OK")
        _p()

    # 2) Reports of a sample connected-users list.
    if not as_json:
        _p("2) Report generation (real Report_Generator: CSV + JSON)")
    rep = generate_user_reports(verbose=not as_json)
    summary["reports"] = rep
    if not as_json:
        _p()

    # 3) Protocol / control-code reference.
    if not as_json:
        _p("3) Protocol reference (real Server.user_status_code table)")
        codes = show_protocol_reference()
        summary["control_codes"] = len(codes)
        _p()
    else:
        summary["control_codes"] = len(Server().user_status_code)

    if as_json:
        print(json.dumps(summary, indent=2))
    else:
        _ok("NetForge demo complete — all real features exercised successfully.")

    # Clean up the report files this demo just created (both modes).
    for key in ("csv", "json"):
        try:
            os.remove(rep[key])
        except OSError:
            pass
    return 0


# --------------------------------------------------------------------------- #
# Interactive menu (EOF / pipe safe)
# --------------------------------------------------------------------------- #
MENU = [
    ("Run end-to-end LOOPBACK self-test (handshake + file transfer)", "selftest"),
    ("Print commands to run the real server / client", "commands"),
    ("Show protocol + status-code reference table", "protocol"),
    ("Generate CSV/JSON report of a sample connected-users list", "reports"),
    ("Show host / runtime system stats", "stats"),
    ("Quit", "quit"),
]


def _render_menu():
    if _HAVE_RICH:
        t = Table(box=box.SIMPLE, show_header=False, padding=(0, 2))
        t.add_column(justify="right", style="bold cyan")
        t.add_column()
        for i, (label, _) in enumerate(MENU, 1):
            t.add_row(str(i), label)
        _console.print(Panel(t, title="Menu", border_style="cyan", box=box.ROUNDED))
    else:
        print("\nMenu")
        print("-" * 40)
        for i, (label, _) in enumerate(MENU, 1):
            print(f"  {i}. {label}")


def _read_choice():
    """Prompt for a menu choice. Returns None on EOF / non-TTY so we exit."""
    prompt = "Select an option [1-6]: "
    try:
        if _HAVE_RICH:
            return Prompt.ask(f"[bold cyan]{prompt.strip()}[/bold cyan]")
        return input(prompt)
    except (EOFError, KeyboardInterrupt):
        return None


def interactive():
    # If stdin is not a TTY (piped / redirected), don't start a blocking loop.
    if not sys.stdin.isatty():
        banner()
        _p("stdin is not a TTY — non-interactive. Try: python3 dashboard.py --demo")
        return 0

    banner()
    while True:
        _render_menu()
        choice = _read_choice()
        if choice is None:
            _p()
            _p("EOF / interrupt received — exiting.")
            return 0
        choice = choice.strip()
        action = None
        if choice.isdigit() and 1 <= int(choice) <= len(MENU):
            action = MENU[int(choice) - 1][1]
        elif choice.lower() in ("q", "quit", "exit"):
            action = "quit"

        if action is None:
            _err("Invalid choice — enter a number 1-6.")
            continue
        if action == "quit":
            _ok("Goodbye.")
            return 0

        _p()
        try:
            if action == "selftest":
                run_loopback_selftest(verbose=True)
                _ok("  [+] Loopback self-test passed.")
            elif action == "commands":
                show_run_commands()
            elif action == "protocol":
                show_protocol_reference()
            elif action == "reports":
                generate_user_reports(verbose=True)
            elif action == "stats":
                show_system_stats()
        except Exception as e:  # keep the menu alive on any action error
            _err(f"  [!] Action failed: {e}")
        _p()


def _parse_args(argv=None):
    parser = argparse.ArgumentParser(
        prog="dashboard.py",
        description=f"{BRAND} — {TAGLINE}",
    )
    parser.add_argument("--demo", action="store_true",
                        help="Run a scripted, non-interactive showcase and exit")
    parser.add_argument("--json", action="store_true",
                        help="With --demo: print a machine-readable JSON summary")
    return parser.parse_args(argv)


def main(argv=None):
    args = _parse_args(argv)
    try:
        if args.demo:
            return run_demo(as_json=args.json)
        return interactive()
    except KeyboardInterrupt:
        _p()
        _p("Interrupted — exiting.")
        return 0


if __name__ == "__main__":
    sys.exit(main())
