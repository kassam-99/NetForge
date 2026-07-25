"""Test suite for NetForge: smoke imports, pure logic, report generation,
logging, and loopback handshake + file-transfer integration tests.

All socket operations use short timeouts so no test can hang.
"""
import importlib
import json
import socket
import struct
import threading
import time

import pytest

MODULES = [
    "ServerSettings",
    "server_logs",
    "ReportGenerator",
    "ServerFunctions",
    "ServerHandler",
    "ServerDashboard",
    "Client",
]


# --------------------------------------------------------------------------- #
# Smoke import tests
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("module_name", MODULES)
def test_import_module(module_name):
    assert importlib.import_module(module_name) is not None


# --------------------------------------------------------------------------- #
# Pure logic
# --------------------------------------------------------------------------- #
def test_find_key_by_value():
    from ServerFunctions import Server_Functions
    sf = Server_Functions(ServerIP="127.0.0.1", ServerPort=9)
    assert sf.find_key_by_value(sf.user_status_code, "connect") == 0xAA
    assert sf.find_key_by_value(sf.user_status_code, "sender") == 0x3B
    assert sf.find_key_by_value(sf.user_status_code, "receiver") == 0x2B
    assert sf.find_key_by_value(sf.user_status_code, "nope") is None


def test_control_code_tables_consistent():
    from ServerSettings import Server
    from Client import General_User
    srv = Server()
    cli = General_User("127.0.0.1", 8000)
    # Codes the client knows must agree with the server's table.
    for code, name in cli.client_control_codes.items():
        if code in srv.user_status_code:
            assert srv.user_status_code[code] == name


# --------------------------------------------------------------------------- #
# ReportGenerator
# --------------------------------------------------------------------------- #
def test_json_report_is_valid_json(tmp_path):
    from ReportGenerator import Report_Generator
    path = tmp_path / "report.json"
    data = [{"Name": "John", "Age": 30}, {"Name": "Jane", "Age": 25}]
    Report_Generator().JSON_GenerateReport(data, filename=str(path))
    loaded = json.loads(path.read_text())
    assert "metadata" in loaded
    assert loaded["records"] == data


def test_csv_report(tmp_path):
    from ReportGenerator import Report_Generator
    path = tmp_path / "report.csv"
    Report_Generator().CSV_GenerateReport([{"a": 1, "b": 2}], filename=str(path))
    text = path.read_text()
    assert "a,b" in text.splitlines()[0]


def test_txt_report_metadata(tmp_path):
    from ReportGenerator import Report_Generator
    path = tmp_path / "report.txt"
    # Must not raise even without a controlling terminal (getpass, not getlogin).
    Report_Generator().TXT_GenerateReport([{"x": 1}], filename=str(path))
    assert "Record 1" in path.read_text()


# --------------------------------------------------------------------------- #
# Logging
# --------------------------------------------------------------------------- #
def test_logger_no_duplicate_handlers(tmp_path, monkeypatch):
    import server_logs
    monkeypatch.setattr(server_logs.Logs, "script_dir", str(tmp_path), raising=False)
    log1 = server_logs.Logs(verbose=False)
    log1.script_dir = str(tmp_path)
    log1.LogEngine("logs", "dup_test")
    log2 = server_logs.Logs(verbose=False)
    log2.script_dir = str(tmp_path)
    log2.LogEngine("logs", "dup_test")
    # Same named logger -> exactly one FileHandler despite two instances.
    assert len(log2.logger.handlers) == 1


# --------------------------------------------------------------------------- #
# Framing helpers via socketpair
# --------------------------------------------------------------------------- #
def test_send_recv_file_roundtrip(tmp_path):
    from ServerFunctions import Server_Functions
    sf = Server_Functions(ServerIP="127.0.0.1", ServerPort=9)
    src = tmp_path / "src.bin"
    payload = b"NetForge payload \x00\x01\x02" * 5000
    src.write_bytes(payload)

    a, b = socket.socketpair()
    a.settimeout(5)
    b.settimeout(5)
    try:
        result = {}

        def receiver():
            path, size = sf.recv_file(b, str(tmp_path / "out"))
            result["path"] = path
            result["size"] = size

        t = threading.Thread(target=receiver)
        t.start()
        sf.send_file(a, str(src))
        t.join(5)
        assert not t.is_alive()
    finally:
        a.close()
        b.close()

    assert result["size"] == len(payload)
    with open(result["path"], "rb") as f:
        assert f.read() == payload


# --------------------------------------------------------------------------- #
# Loopback integration: handshake + file transfer
# --------------------------------------------------------------------------- #
def _free_port():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


@pytest.fixture()
def running_server(tmp_path):
    from ServerDashboard import Server_Dashboard
    port = _free_port()
    server = Server_Dashboard(ServerIP="127.0.0.1", ServerPort=port, verbose=False)
    server.storage_dir = str(tmp_path / "storage")
    thread = threading.Thread(target=server.StartServer, daemon=True)
    thread.start()

    # Wait until the listener is accepting connections.
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
        pytest.fail("server did not start")

    yield server, port
    server.stop()
    thread.join(5)


def test_handshake_sender_upload(running_server, tmp_path):
    from Client import General_User
    server, port = running_server

    src = tmp_path / "upload.txt"
    content = b"hello netforge upload\n" * 100
    src.write_bytes(content)

    client = General_User("127.0.0.1", port, user_id="tester", verbose=False)
    client.client_socket.settimeout(5)
    ok = client.ConnToServer("tester", 0x3B, filepath=str(src))  # sender
    assert ok is True

    # Server should have stored the uploaded file with identical content.
    saved = tmp_path / "storage" / "upload.txt"
    deadline = time.time() + 5
    while not saved.exists() and time.time() < deadline:
        time.sleep(0.05)
    assert saved.exists()
    assert saved.read_bytes() == content


def test_handshake_receiver_download(running_server, tmp_path):
    from Client import General_User
    server, port = running_server

    # Place a file in the server storage for the client to fetch.
    storage = tmp_path / "storage"
    storage.mkdir(parents=True, exist_ok=True)
    content = b"downloadable content 12345" * 50
    (storage / "download.txt").write_bytes(content)

    dest = tmp_path / "downloads"
    client = General_User("127.0.0.1", port, user_id="grabber", verbose=False)
    client.client_socket.settimeout(5)
    ok = client.ConnToServer("grabber", 0x2B, filepath="download.txt", dest_dir=str(dest))  # receiver
    assert ok is True
    assert (dest / "download.txt").read_bytes() == content


def test_handshake_wrong_first_byte_rejected(running_server):
    server, port = running_server
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(5)
    s.connect(("127.0.0.1", port))
    # Send an invalid command byte (0x00) -> server should disconnect us.
    s.send(struct.pack("BBB", 0x00, 0x2A, 0x3C))
    s.send(b"baduser\x00")
    resp = s.recv(3)
    # Server responds with a disconnect frame (or closes) rather than "accepted".
    if resp:
        status = resp[0]
        assert status != 0x6C  # not "accepted"
    s.close()
