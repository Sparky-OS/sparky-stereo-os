#!/usr/bin/env python3
"""A minimal software Cast receiver, for the handshake proof only.

It speaks the CASTv2 channel the way the public senders (pychromecast,
GNOME Network Displays) expect: TLS on port 8009, each message a 4-byte
big-endian length followed by a CastMessage protobuf.  It answers the
connection, heartbeat, receiver and media namespaces with the smallest
valid replies, logs every message as one JSON line, and exits on request.

It does NOT implement device authentication (urn:x-cast:com.google.cast.tp.deviceauth):
a challenge that arrives is logged so the proof shows which senders ask for it.
"""
import json
import socket
import ssl
import struct
import sys
import threading
import time

from pychromecast.generated import cast_channel_pb2 as pb

NS_CONNECTION = "urn:x-cast:com.google.cast.tp.connection"
NS_HEARTBEAT = "urn:x-cast:com.google.cast.tp.heartbeat"
NS_RECEIVER = "urn:x-cast:com.google.cast.receiver"
NS_MEDIA = "urn:x-cast:com.google.cast.media"
NS_DEVICEAUTH = "urn:x-cast:com.google.cast.tp.deviceauth"

APP_DMR = "CC1AD845"
TRANSPORT_ID = "web-1"

log_path = sys.argv[1] if len(sys.argv) > 1 else "receiver.log"
cert = sys.argv[2] if len(sys.argv) > 2 else "cert.pem"
key = sys.argv[3] if len(sys.argv) > 3 else "key.pem"
log_lock = threading.Lock()


def log(entry):
    entry["t"] = round(time.monotonic(), 3)
    with log_lock:
        with open(log_path, "a") as f:
            f.write(json.dumps(entry) + "\n")


class Session:
    def __init__(self):
        self.app_running = False
        self.session_id = "7E2F0E77-0000-0000-0000-000000000001"
        self.media = None
        self.media_session_id = 1
        self.volume = {"level": 1.0, "muted": False}

    def receiver_status(self, request_id):
        apps = []
        if self.app_running:
            apps.append({
                "appId": APP_DMR,
                "appType": "WEB",
                "displayName": "Default Media Receiver",
                "iconUrl": "",
                "isIdleScreen": False,
                "launchedFromCloud": False,
                "namespaces": [
                    {"name": NS_MEDIA},
                    {"name": "urn:x-cast:com.google.cast.cac"},
                    {"name": "urn:x-cast:com.google.cast.debugoverlay"},
                    {"name": "urn:x-cast:com.google.cast.broadcast"},
                ],
                "sessionId": self.session_id,
                "statusText": "Default Media Receiver",
                "transportId": TRANSPORT_ID,
                "universalAppId": APP_DMR,
            })
        return {
            "requestId": request_id,
            "type": "RECEIVER_STATUS",
            "status": {
                "applications": apps,
                "userEq": {},
                "volume": {
                    "controlType": "attenuation",
                    "level": self.volume["level"],
                    "muted": self.volume["muted"],
                    "stepInterval": 0.05,
                },
            },
        }

    def media_status(self, request_id):
        status = []
        if self.media is not None:
            status.append({
                "mediaSessionId": self.media_session_id,
                "playbackRate": 1,
                "playerState": "PLAYING",
                "currentTime": 0.0,
                "supportedMediaCommands": 274447,
                "volume": {"level": 1, "muted": False},
                "media": self.media,
                "currentItemId": 1,
                "repeatMode": "REPEAT_OFF",
            })
        return {"type": "MEDIA_STATUS", "requestId": request_id, "status": status}


def send(conn, src, dst, ns, payload):
    msg = pb.CastMessage()
    msg.protocol_version = msg.CASTV2_1_0
    msg.source_id = src
    msg.destination_id = dst
    msg.namespace = ns
    msg.payload_type = msg.STRING
    msg.payload_utf8 = json.dumps(payload)
    data = msg.SerializeToString()
    conn.sendall(struct.pack(">I", len(data)) + data)
    log({"dir": "send", "src": src, "dst": dst, "ns": ns, "payload": payload})


def read_exact(conn, n):
    buf = b""
    while len(buf) < n:
        chunk = conn.recv(n - len(buf))
        if not chunk:
            raise ConnectionError("peer closed")
        buf += chunk
    return buf


def handle(conn, peer, session, stop_event):
    log({"event": "tls-accepted", "peer": peer[0], "cipher": conn.cipher()[0], "tls": conn.version()})
    try:
        while not stop_event.is_set():
            (length,) = struct.unpack(">I", read_exact(conn, 4))
            msg = pb.CastMessage()
            msg.ParseFromString(read_exact(conn, length))
            if msg.payload_type == msg.BINARY:
                log({"dir": "recv", "src": msg.source_id, "dst": msg.destination_id,
                     "ns": msg.namespace, "binary_bytes": len(msg.payload_binary)})
                if msg.namespace == NS_DEVICEAUTH:
                    log({"event": "device-auth-challenge", "note": "this software receiver has no Google-signed device certificate; a sender that requires one stops here"})
                continue
            try:
                payload = json.loads(msg.payload_utf8)
            except json.JSONDecodeError:
                payload = {"raw": msg.payload_utf8}
            log({"dir": "recv", "src": msg.source_id, "dst": msg.destination_id,
                 "ns": msg.namespace, "payload": payload})
            mtype = payload.get("type")
            rid = payload.get("requestId", 0)
            if msg.namespace == NS_HEARTBEAT and mtype == "PING":
                send(conn, msg.destination_id, msg.source_id, NS_HEARTBEAT, {"type": "PONG"})
            elif msg.namespace == NS_CONNECTION and mtype == "CONNECT":
                pass
            elif msg.namespace == NS_CONNECTION and mtype == "CLOSE":
                if msg.destination_id == "receiver-0":
                    log({"event": "sender-closed-channel"})
                    stop_event.set()
                    return
            elif msg.namespace == NS_RECEIVER and mtype == "GET_STATUS":
                send(conn, "receiver-0", msg.source_id, NS_RECEIVER, session.receiver_status(rid))
            elif msg.namespace == NS_RECEIVER and mtype == "LAUNCH":
                log({"event": "launch", "appId": payload.get("appId")})
                if payload.get("appId") == APP_DMR:
                    session.app_running = True
                    send(conn, "receiver-0", msg.source_id, NS_RECEIVER, session.receiver_status(rid))
                else:
                    send(conn, "receiver-0", msg.source_id, NS_RECEIVER,
                         {"requestId": rid, "type": "LAUNCH_ERROR", "reason": "NOT_FOUND"})
            elif msg.namespace == NS_RECEIVER and mtype == "STOP":
                session.app_running = False
                session.media = None
                send(conn, "receiver-0", msg.source_id, NS_RECEIVER, session.receiver_status(rid))
            elif msg.namespace == NS_RECEIVER and mtype == "SET_VOLUME":
                session.volume.update(payload.get("volume", {}))
                send(conn, "receiver-0", msg.source_id, NS_RECEIVER, session.receiver_status(rid))
            elif msg.namespace == NS_MEDIA and mtype == "LOAD":
                session.media = payload.get("media")
                log({"event": "load", "contentId": session.media.get("contentId"),
                     "contentType": session.media.get("contentType"),
                     "streamType": session.media.get("streamType")})
                send(conn, TRANSPORT_ID, msg.source_id, NS_MEDIA, session.media_status(rid))
            elif msg.namespace == NS_MEDIA and mtype == "GET_STATUS":
                send(conn, TRANSPORT_ID, msg.source_id, NS_MEDIA, session.media_status(rid))
            elif msg.namespace == NS_MEDIA and mtype in ("PLAY", "PAUSE", "STOP", "SEEK"):
                send(conn, TRANSPORT_ID, msg.source_id, NS_MEDIA, session.media_status(rid))
            else:
                log({"event": "unhandled", "ns": msg.namespace, "type": mtype})
    except (ConnectionError, ssl.SSLError, OSError) as exc:
        log({"event": "connection-ended", "error": str(exc)})
    finally:
        try:
            conn.close()
        except OSError:
            pass


def main():
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ctx.load_cert_chain(cert, key)
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(("127.0.0.1", 8009))
    srv.listen(2)
    srv.settimeout(1.0)
    log({"event": "listening", "addr": "127.0.0.1:8009", "cert": "self-signed"})
    session = Session()
    stop_event = threading.Event()
    deadline = time.monotonic() + 120
    while not stop_event.is_set() and time.monotonic() < deadline:
        try:
            raw, peer = srv.accept()
        except socket.timeout:
            continue
        try:
            conn = ctx.wrap_socket(raw, server_side=True)
        except ssl.SSLError as exc:
            log({"event": "tls-failed", "error": str(exc)})
            continue
        threading.Thread(target=handle, args=(conn, peer, session, stop_event), daemon=True).start()
    log({"event": "receiver-exit", "stopped_by_sender": stop_event.is_set()})


if __name__ == "__main__":
    main()
