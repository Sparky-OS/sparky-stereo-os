#!/usr/bin/env python3
"""An emulated UPnP AV renderer for container proofs.

It announces itself on SSDP (NOTIFY alive, and answers M-SEARCH), serves a
device description whose strings a UMS renderer profile can match, and keeps
the state of a real renderer: AVTransport (SetAVTransportURI, Play, Pause,
Stop, Seek, GetTransportInfo, GetPositionInfo) and RenderingControl
(SetVolume, GetVolume, SetMute, GetMute). Every request is recorded.

Two identities: "flat" is the description Flat Headset's player gives, and
"bravia" is a Sony KDL-46EX725 (the strings of Sony-BraviaEX725.conf).
"""
import argparse
import hashlib
import json
import os
import socket
import threading
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse
from xml.etree import ElementTree as ET
from xml.sax.saxutils import escape

SSDP_ADDRESS = "239.255.255.250"
SSDP_PORT = 1900
DEVICE_TYPE = "urn:schemas-upnp-org:device:MediaRenderer:3"
AV_TRANSPORT = "urn:schemas-upnp-org:service:AVTransport:3"
RENDERING_CONTROL = "urn:schemas-upnp-org:service:RenderingControl:3"

IDENTITIES = {
    "flat": {
        "udn": "6f1a5c6e-9d6a-4a9e-8a49-7b6e5c94d402",
        "friendlyName": "Flat Headset 94",
        "manufacturer": "KDE contributors",
        "manufacturerURL": "https://www.kde.org/",
        "modelDescription": "Flat Headset DLNA movie mode",
        "modelName": "Flat Headset",
        "modelNumber": "FlatHeadset/1.0 Panel/3840x2160",
        "server": "Linux/6.0 UPnP/1.0 FlatHeadset/1.0",
        "userAgent": "FlatHeadset/1.0",
    },
    "plain": {
        "udn": "6f1a5c6e-9d6a-4a9e-8a49-7b6e5c94d404",
        "friendlyName": "Proof Renderer",
        "manufacturer": "Proof Devices",
        "manufacturerURL": "https://example.invalid/",
        "modelDescription": "Proof renderer without a profile",
        "modelName": "Proof Renderer",
        "modelNumber": "1",
        "server": "Linux/6.0 UPnP/1.0 ProofRenderer/1.0",
        "userAgent": "ProofRenderer/1.0",
    },
    "bravia": {
        "udn": "6f1a5c6e-9d6a-4a9e-8a49-7b6e5c94d403",
        "friendlyName": "BRAVIA KDL-46EX725",
        "manufacturer": "Sony Corporation",
        "manufacturerURL": "https://www.sony.net/",
        "modelDescription": "BRAVIA KDL-46EX725",
        "modelName": "KDL-46EX725",
        "modelNumber": "KDL-46EX725",
        "server": "Linux/2.6 UPnP/1.0 Sony-BDP/2.0 DLNADOC/1.50",
        "userAgent": "UPnP/1.0 DLNADOC/1.50 BRAVIA",
    },
}


def xml_bytes(root):
    return b'<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(root, encoding="unicode").encode()


def clock(seconds):
    seconds = int(seconds)
    return "%d:%02d:%02d" % (seconds // 3600, (seconds // 60) % 60, seconds % 60)


def seconds_of(text):
    parts = [float(part) for part in text.split(":")]
    while len(parts) < 3:
        parts.insert(0, 0.0)
    return parts[0] * 3600 + parts[1] * 60 + parts[2]


class Renderer:
    def __init__(self, address, port, identity, identity_user_agent, record_dir):
        self.address = address
        self.port = port
        self.identity = IDENTITIES[identity]
        self.uuid = "uuid:" + self.identity["udn"]
        self.path = "/device.xml"
        self.location = f"http://{address}:{port}{self.path}"
        self.lock = threading.Lock()
        self.state = "NO_MEDIA_PRESENT"
        self.uri = ""
        self.metadata = ""
        self.position = 0.0
        self.started = None
        self.volume = 30
        self.mute = False
        self.calls = []
        self.fetches = []
        self.user_agent = identity_user_agent or self.identity["userAgent"]
        self.record_dir = record_dir
        self.description = self.build_description()

    def fetch(self, uri, label, headers=None):
        """Pulls the stream like a player: its own User-Agent, saved for the proof to look at."""
        entry = {"id": len(self.fetches) + 1, "uri": uri, "label": label, "headers": headers or {}, "done": False}
        self.fetches.append(entry)

        def run():
            import urllib.request
            request = urllib.request.Request(uri, headers=dict({"User-Agent": self.user_agent}, **(headers or {})))
            path = os.path.join(self.record_dir, "received", f"{entry['id']}-{label}.bin")
            os.makedirs(os.path.dirname(path), exist_ok=True)
            try:
                with urllib.request.urlopen(request, timeout=60) as response, open(path, "wb") as output:
                    entry["status"] = response.status
                    entry["content_type"] = response.headers.get("Content-Type")
                    entry["content_range"] = response.headers.get("Content-Range")
                    entry["time_seek"] = response.headers.get("TimeSeekRange.dlna.org")
                    entry["bytes"] = 0
                    while True:
                        block = response.read(65536)
                        if not block:
                            break
                        output.write(block)
                        entry["bytes"] += len(block)
                entry["path"] = path
            except Exception as error:  # the proof reads the reason
                entry["error"] = f"{type(error).__name__}: {error}"
            entry["done"] = True

        threading.Thread(target=run, daemon=True).start()

    def current_position(self):
        if self.state == "PLAYING" and self.started is not None:
            return self.position + (time.monotonic() - self.started)
        return self.position

    def freeze(self):
        self.position = self.current_position()
        self.started = None

    def build_description(self):
        ns = "urn:schemas-upnp-org:device-1-0"
        ET.register_namespace("", ns)
        root = ET.Element(f"{{{ns}}}root")
        spec = ET.SubElement(root, f"{{{ns}}}specVersion")
        ET.SubElement(spec, f"{{{ns}}}major").text = "1"
        ET.SubElement(spec, f"{{{ns}}}minor").text = "0"
        device = ET.SubElement(root, f"{{{ns}}}device")
        values = {
            "deviceType": DEVICE_TYPE,
            "friendlyName": self.identity["friendlyName"],
            "manufacturer": self.identity["manufacturer"],
            "manufacturerURL": self.identity["manufacturerURL"],
            "modelDescription": self.identity["modelDescription"],
            "modelName": self.identity["modelName"],
            "modelNumber": self.identity["modelNumber"],
            "modelURL": self.identity["manufacturerURL"],
            "serialNumber": "94",
            "UDN": self.uuid,
        }
        for name, value in values.items():
            ET.SubElement(device, f"{{{ns}}}{name}").text = value
        services = ET.SubElement(device, f"{{{ns}}}serviceList")
        for kind, service_type in (("AVTransport", AV_TRANSPORT), ("RenderingControl", RENDERING_CONTROL)):
            service = ET.SubElement(services, f"{{{ns}}}service")
            ET.SubElement(service, f"{{{ns}}}serviceType").text = service_type
            ET.SubElement(service, f"{{{ns}}}serviceId").text = f"urn:upnp-org:serviceId:{kind}"
            ET.SubElement(service, f"{{{ns}}}SCPDURL").text = f"/{kind}.xml"
            ET.SubElement(service, f"{{{ns}}}controlURL").text = f"/control/{kind}"
            ET.SubElement(service, f"{{{ns}}}eventSubURL").text = f"/event/{kind}"
        return xml_bytes(root)

    def respond(self, service, action, values):
        body = "".join(f"<{name}>{escape(str(value))}</{name}>" for name, value in values)
        return (
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/" '
            's:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/"><s:Body>'
            f'<u:{action}Response xmlns:u="{service}">{body}</u:{action}Response>'
            "</s:Body></s:Envelope>"
        ).encode()

    def fault(self, code, text):
        return (
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/" '
            's:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/"><s:Body><s:Fault>'
            "<faultcode>s:Client</faultcode><faultstring>UPnPError</faultstring><detail>"
            '<UPnPError xmlns="urn:schemas-upnp-org:control-1-0">'
            f"<errorCode>{code}</errorCode><errorDescription>{text}</errorDescription>"
            "</UPnPError></detail></s:Fault></s:Body></s:Envelope>"
        ).encode()

    def act(self, kind, action, arguments):
        """Returns (status, body)."""
        with self.lock:
            self.calls.append({"service": kind, "action": action, "arguments": arguments, "time": time.time()})
            if kind == "AVTransport":
                return self.av_transport(action, arguments)
            if kind == "RenderingControl":
                return self.rendering_control(action, arguments)
        return 404, self.fault(401, "Invalid Action")

    def av_transport(self, action, arguments):
        s = AV_TRANSPORT
        if action == "SetAVTransportURI":
            self.uri = arguments.get("CurrentURI", "")
            self.metadata = arguments.get("CurrentURIMetaData", "")
            self.position = 0.0
            self.started = None
            self.state = "STOPPED"
            return 200, self.respond(s, action, [])
        if action == "Play":
            if not self.uri:
                return 500, self.fault(701, "Transition not available")
            self.freeze()
            if self.state != "PAUSED_PLAYBACK":
                self.fetch(self.uri, "play")
            self.state = "PLAYING"
            self.started = time.monotonic()
            return 200, self.respond(s, action, [])
        if action == "Pause":
            if self.state != "PLAYING":
                return 500, self.fault(701, "Transition not available")
            self.freeze()
            self.state = "PAUSED_PLAYBACK"
            return 200, self.respond(s, action, [])
        if action == "Stop":
            self.freeze()
            self.position = 0.0
            self.state = "STOPPED" if self.uri else "NO_MEDIA_PRESENT"
            return 200, self.respond(s, action, [])
        if action == "Seek":
            if arguments.get("Unit") not in ("REL_TIME", "ABS_TIME"):
                return 500, self.fault(710, "Seek mode not supported")
            was_playing = self.state == "PLAYING"
            self.position = seconds_of(arguments.get("Target", "0"))
            if self.uri:
                self.fetch(self.uri, "seek", {"TimeSeekRange.dlna.org": "npt=%.3f-" % self.position})
            self.started = time.monotonic() if was_playing else None
            return 200, self.respond(s, action, [])
        if action == "GetTransportInfo":
            return 200, self.respond(s, action, [("CurrentTransportState", self.state), ("CurrentTransportStatus", "OK"), ("CurrentSpeed", "1")])
        if action == "GetPositionInfo":
            return 200, self.respond(s, action, [
                ("Track", 1), ("TrackDuration", "0:00:00"), ("TrackMetaData", self.metadata), ("TrackURI", self.uri),
                ("RelTime", clock(self.current_position())), ("AbsTime", clock(self.current_position())),
                ("RelCount", 0), ("AbsCount", 0),
            ])
        return 500, self.fault(401, "Invalid Action")

    def rendering_control(self, action, arguments):
        s = RENDERING_CONTROL
        if action == "SetVolume":
            value = int(arguments.get("DesiredVolume", "-1"))
            if not 0 <= value <= 100:
                return 500, self.fault(601, "Argument Value Out of Range")
            self.volume = value
            return 200, self.respond(s, action, [])
        if action == "GetVolume":
            return 200, self.respond(s, action, [("CurrentVolume", self.volume)])
        if action == "SetMute":
            self.mute = arguments.get("DesiredMute", "0") in ("1", "true")
            return 200, self.respond(s, action, [])
        if action == "GetMute":
            return 200, self.respond(s, action, [("CurrentMute", 1 if self.mute else 0)])
        return 500, self.fault(401, "Invalid Action")


class Handler(BaseHTTPRequestHandler):
    server_version = "Renderer/1.0"
    sys_version = ""

    def log_message(self, fmt, *args):
        import sys
        sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))

    def record(self, method):
        record = {"timestamp": time.time(), "method": method, "path": self.path, "headers": dict(self.headers.items())}
        with open(os.path.join(self.server.record_dir, "incoming-requests.jsonl"), "a", encoding="utf-8") as output:
            output.write(json.dumps(record, sort_keys=True) + "\n")

    def send_payload(self, content, media_type, status=200):
        self.send_response(status)
        self.send_header("Content-Type", media_type)
        self.send_header("Content-Length", str(len(content)))
        self.send_header("SERVER", self.server.renderer.identity["server"])
        self.end_headers()
        self.wfile.write(content)

    def do_GET(self):
        self.record("GET")
        path = urlparse(self.path).path
        renderer = self.server.renderer
        if path == renderer.path:
            self.send_payload(renderer.description, 'text/xml; charset="utf-8"')
        elif path in ("/AVTransport.xml", "/RenderingControl.xml"):
            self.send_payload(b'<?xml version="1.0"?><scpd xmlns="urn:schemas-upnp-org:service-1-0"></scpd>', 'text/xml; charset="utf-8"')
        elif path == "/status":
            with renderer.lock:
                status = {
                    "state": renderer.state, "uri": renderer.uri, "position": renderer.current_position(),
                    "volume": renderer.volume, "mute": renderer.mute, "calls": renderer.calls,
                    "fetches": renderer.fetches, "user_agent": renderer.user_agent,
                }
            self.send_payload(json.dumps(status).encode(), "application/json")
        else:
            self.send_error(404)

    def do_SUBSCRIBE(self):
        self.record("SUBSCRIBE")
        self.send_response(200)
        self.send_header("SERVER", self.server.renderer.identity["server"])
        self.send_header("SID", f"uuid:{uuid.uuid4()}")
        self.send_header("TIMEOUT", "Second-1800")
        self.send_header("Content-Length", "0")
        self.end_headers()

    do_UNSUBSCRIBE = do_SUBSCRIBE

    def do_POST(self):
        self.record("POST")
        path = urlparse(self.path).path
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length)
        kind = path.rsplit("/", 1)[-1]
        soap_action = self.headers.get("SOAPACTION", "").strip('"')
        action = soap_action.rsplit("#", 1)[-1]
        arguments = {}
        try:
            body = ET.fromstring(raw).find("{http://schemas.xmlsoap.org/soap/envelope/}Body")
            for child in list(body)[0]:
                arguments[child.tag.split("}")[-1]] = child.text or ""
        except (ET.ParseError, IndexError, AttributeError, TypeError):
            self.send_payload(self.server.renderer.fault(402, "Invalid Args"), 'text/xml; charset="utf-8"', 500)
            return
        status, payload = self.server.renderer.act(kind, action, arguments)
        if "CurrentURI" in arguments:
            digest = hashlib.sha256(arguments["CurrentURI"].encode()).hexdigest()
            with open(os.path.join(self.server.record_dir, digest + ".txt"), "w") as stream:
                stream.write(arguments["CurrentURI"] + "\n")
        self.send_payload(payload, 'text/xml; charset="utf-8"', status)


class Server(ThreadingHTTPServer):
    daemon_threads = True


def ssdp_messages(renderer, kind, search_target=None):
    targets = ["upnp:rootdevice", renderer.uuid, DEVICE_TYPE, AV_TRANSPORT, RENDERING_CONTROL]
    for target in targets if search_target is None else [search_target]:
        usn = renderer.uuid if target == renderer.uuid else f"{renderer.uuid}::{target}"
        headers = [
            "NOTIFY * HTTP/1.1" if kind == "notify" else "HTTP/1.1 200 OK",
            f"HOST: {SSDP_ADDRESS}:{SSDP_PORT}" if kind == "notify" else "EXT:",
            "CACHE-CONTROL: max-age=1800",
            f"LOCATION: {renderer.location}",
            "NTS: ssdp:alive" if kind == "notify" else "ST: " + target,
            f"NT: {target}" if kind == "notify" else "DATE: " + time.strftime("%a, %d %b %Y %H:%M:%S GMT", time.gmtime()),
            f"USN: {usn}",
            f"SERVER: {renderer.identity['server']}",
            "", "",
        ]
        yield "\r\n".join(headers).encode()


def ssdp(renderer):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("", SSDP_PORT))
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_IF, socket.inet_aton(renderer.address))
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 4)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, socket.inet_aton(SSDP_ADDRESS) + socket.inet_aton(renderer.address))
    sock.settimeout(1)
    last_notify = 0.0
    while True:
        if time.monotonic() - last_notify > 5:
            for message in ssdp_messages(renderer, "notify"):
                sock.sendto(message, (SSDP_ADDRESS, SSDP_PORT))
            last_notify = time.monotonic()
        try:
            data, source = sock.recvfrom(4096)
        except socket.timeout:
            continue
        text = data.decode("latin-1", "replace")
        if not text.startswith("M-SEARCH"):
            continue
        target = next((line.split(":", 1)[1].strip() for line in text.split("\r\n") if line.upper().startswith("ST:")), "")
        wanted = {"ssdp:all": None, "upnp:rootdevice": "upnp:rootdevice", DEVICE_TYPE: DEVICE_TYPE}
        if target in wanted or target.startswith("urn:schemas-upnp-org:device:MediaRenderer:"):
            time.sleep(0.1)
            for message in ssdp_messages(renderer, "response", wanted.get(target, DEVICE_TYPE) if target in wanted else target):
                sock.sendto(message, source)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", required=True)
    parser.add_argument("--port", type=int, required=True)
    parser.add_argument("--record-dir", required=True)
    parser.add_argument("--identity", choices=sorted(IDENTITIES), default="flat")
    parser.add_argument("--user-agent", default="")
    parser.add_argument("--no-ssdp", action="store_true", help="stay off SSDP, so UMS knows the renderer by its User-Agent only")
    args = parser.parse_args()
    os.makedirs(args.record_dir, exist_ok=True)
    renderer = Renderer(args.host, args.port, args.identity, args.user_agent, args.record_dir)
    server = Server((args.host, args.port), Handler)
    server.renderer = renderer
    server.record_dir = args.record_dir
    if not args.no_ssdp:
        threading.Thread(target=ssdp, args=(renderer,), daemon=True).start()
    server.serve_forever()


if __name__ == "__main__":
    main()
