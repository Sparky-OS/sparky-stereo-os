#!/usr/bin/env python3
"""The controller of the container proof.

stream: finds the media server by SSDP, browses its library as the renderer
(same address, same User-Agent), pushes each case's resource to the emulated
renderer (SetAVTransportURI, Play), waits for the renderer to have pulled the
stream, and checks what it received: container, codec, size, frame rate, the
stereo mark in the stream, and the colour at the middle of each eye.

control: drives the renderer's AVTransport and RenderingControl (play, pause,
seek, volume, mute) and checks its answers, and that a call it must refuse is
refused with the UPnP error code.

One line per case on stdout, "PASS" or "FAIL" first; the exit status is 1
when a line says FAIL.
"""
import argparse
import hashlib
import json
import os
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from xml.etree import ElementTree as ET

SSDP = ("239.255.255.250", 1900)
DIDL = "{urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/}"
DC = "{http://purl.org/dc/elements/1.1/}"
UPNP = "{urn:schemas-upnp-org:device-1-0}"

COLOURS = {
    "red": lambda r, g, b: r > 200 and g < 64 and b < 64,
    "cyan": lambda r, g, b: r < 64 and g > 200 and b > 200,
    "green": lambda r, g, b: r < 64 and g > 200 and b < 64,
    "white": lambda r, g, b: r > 200 and g > 200 and b > 200,
}


class Failure(Exception):
    pass


def http(url, data=None, headers=None, method=None, timeout=30):
    request = urllib.request.Request(url, data=data, headers=dict(headers or {}, Connection="close"), method=method)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.status, response.read(), dict(response.headers)
    except urllib.error.HTTPError as error:
        return error.code, error.read(), dict(error.headers)


def discover_server(address, user_agent, timeout):
    message = "\r\n".join([
        "M-SEARCH * HTTP/1.1", f"HOST: {SSDP[0]}:{SSDP[1]}", 'MAN: "ssdp:discover"', "MX: 1",
        "ST: urn:schemas-upnp-org:device:MediaServer:1", f"USER-AGENT: {user_agent}", "", "",
    ]).encode("ascii")
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as probe_socket:
        probe_socket.connect((address, 9))
        local = probe_socket.getsockname()[0]
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((local, 0))
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_IF, socket.inet_aton(local))
        sock.settimeout(1)
        deadline = time.monotonic() + timeout
        next_search = 0.0
        while time.monotonic() < deadline:
            if time.monotonic() >= next_search:
                sock.sendto(message, SSDP)
                next_search = time.monotonic() + 1.5
            try:
                data, _ = sock.recvfrom(65536)
            except socket.timeout:
                continue
            for line in data.decode("utf-8", "replace").splitlines():
                if line.upper().startswith("LOCATION:"):
                    location = line.split(":", 1)[1].strip()
                    if urllib.parse.urlparse(location).hostname == address:
                        return location
    raise Failure(f"no MediaServer at {address} answered the SSDP search")


def content_directory(location, user_agent):
    status, body, _ = http(location, headers={"User-Agent": user_agent})
    if status != 200:
        raise Failure(f"the server description returned HTTP {status}")
    for service in ET.fromstring(body).iter(f"{UPNP}service"):
        if ":ContentDirectory:" in (service.findtext(f"{UPNP}serviceType") or ""):
            return urllib.parse.urljoin(location, service.findtext(f"{UPNP}controlURL")), service.findtext(f"{UPNP}serviceType")
    raise Failure("the server description has no ContentDirectory")


def soap(url, service, action, arguments, user_agent):
    parts = [f'<u:{action} xmlns:u="{service}">']
    parts += [f"<{name}>{value}</{name}>" for name, value in arguments]
    parts.append(f"</u:{action}>")
    body = (
        '<?xml version="1.0" encoding="utf-8"?><s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/" '
        's:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/"><s:Body>' + "".join(parts) + "</s:Body></s:Envelope>"
    ).encode()
    headers = {"Content-Type": 'text/xml; charset="utf-8"', "SOAPACTION": f'"{service}#{action}"', "User-Agent": user_agent}
    return http(url, data=body, headers=headers, method="POST")


def soap_values(body):
    values = {}
    for element in ET.fromstring(body).iter():
        if len(element) == 0 and element.tag.split("}")[-1] not in ("faultcode", "faultstring"):
            values[element.tag.split("}")[-1]] = element.text or ""
    return values


def browse(control, service, object_id, user_agent):
    status, body, _ = soap(control, service, "Browse", [
        ("ObjectID", object_id), ("BrowseFlag", "BrowseDirectChildren"), ("Filter", "*"),
        ("StartingIndex", "0"), ("RequestedCount", "0"), ("SortCriteria", "")], user_agent)
    if status != 200:
        raise Failure(f"Browse {object_id} returned HTTP {status}")
    return ET.fromstring(soap_values(body)["Result"].encode())


def library(control, service, user_agent, fixture_names, location):
    """The resources of the folder that holds the fixtures: {file name: url}."""
    root = browse(control, service, "0", user_agent)
    for container in root.findall(f"{DIDL}container"):
        listing = browse(control, service, container.get("id"), user_agent)
        resources = {}
        for item in listing.findall(f"{DIDL}item"):
            for res in item.findall(f"{DIDL}res"):
                url = urllib.parse.urljoin(location, res.text or "")
                name = os.path.basename(urllib.parse.urlparse(url).path)
                resources[name] = url
        if any(name.split(".mkv")[0] in fixture_names for name in resources):
            return resources
    raise Failure("no folder of the library holds the fixtures")


def tool(command):
    done = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    if done.returncode:
        raise Failure(f"{command[0]} failed: {done.stderr.decode(errors='replace')[:300]}")
    return done.stdout


def probe(path):
    data = json.loads(tool(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_streams", "-show_format", "-of", "json", path]))
    if not data.get("streams"):
        raise Failure("the received stream has no video")
    stream = data["streams"][0]
    # the first frame's Stereo 3D side data, read the way UMS reads it: FFmpeg's showinfo
    log = subprocess.run(["ffmpeg", "-hide_banner", "-nostdin", "-i", path, "-an", "-sn", "-frames:v", "1", "-vf", "showinfo", "-f", "null", "-"],
                         stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False).stdout.decode(errors="replace")
    marks = []
    for found in log.splitlines():
        if "Stereo 3D: type - " in found:
            text = found.split("Stereo 3D: type - ", 1)[1]
            marks.append(text.split(",")[0].strip())
    numerator, _, denominator = stream.get("avg_frame_rate", "0/1").partition("/")
    rate = float(numerator) / float(denominator or 1) if float(denominator or 1) else 0.0
    return {
        "container": data["format"].get("format_name"), "codec": stream.get("codec_name"),
        "width": stream.get("width"), "height": stream.get("height"), "fps": round(rate, 2),
        "mark": marks[0] if marks else None, "start": float(data["format"].get("start_time", 0) or 0),
    }


def pixel(path, x, y, width, height):
    raw = tool(["ffmpeg", "-hide_banner", "-loglevel", "error", "-i", path, "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "rgb24", "pipe:1"])
    if len(raw) != width * height * 3:
        raise Failure(f"expected {width * height * 3} bytes of the first frame, got {len(raw)}")
    offset = (y * width + x) * 3
    return raw[offset], raw[offset + 1], raw[offset + 2]


def check_received(path, expect):
    info = probe(path)
    width, height = info["width"], info["height"]
    problems = []
    for key in ("container", "codec"):
        if key in expect and info[key] != expect[key]:
            problems.append(f"{key} {info[key]!r}, wanted {expect[key]!r}")
    if "size" in expect and [width, height] != expect["size"]:
        problems.append(f"size {width}x{height}, wanted {expect['size'][0]}x{expect['size'][1]}")
    if "fps" in expect and abs(info["fps"] - expect["fps"]) > 1:
        problems.append(f"{info['fps']} frames a second, wanted {expect['fps']}")
    if "mark" in expect and info["mark"] != expect["mark"]:
        problems.append(f"stereo mark {info['mark']!r}, wanted {expect['mark']!r}")
    places = {
        "left": (width // 4, height // 2), "right": (3 * width // 4, height // 2),
        "top": (width // 2, height // 4), "bottom": (width // 2, 3 * height // 4), "centre": (width // 2, height // 2),
    }
    seen = {}
    for place, colour in expect.get("pixels", {}).items():
        rgb = pixel(path, *places[place], width, height)
        seen[place] = list(rgb)
        if not COLOURS[colour](*rgb):
            problems.append(f"{place} is {list(rgb)}, wanted {colour}")
    return info, seen, problems


def wait_for(renderer, predicate, what, timeout=60):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        status = json.loads(http(renderer + "/status")[1])
        found = predicate(status)
        if found:
            return found
        time.sleep(0.3)
    raise Failure(f"timed out waiting for {what}")


def stream(args):
    cases = [case for case in json.load(open(args.cases))["cases"] if case["instance"] == args.instance]
    names = {case["title"] for case in cases}
    location = discover_server(args.server_ip, args.user_agent, args.discovery_timeout)
    control, service = content_directory(location, args.user_agent)
    resources = library(control, service, args.user_agent, names, location)
    status = json.loads(http(args.renderer + "/status")[1])
    transport = args.renderer + "/control/AVTransport"
    failed = False
    for case in cases:
        label = case["id"]
        expect = case["expect"]
        matches = [url for name, url in resources.items() if name == case["title"] + ".mkv" or name.startswith(case["title"] + ".mkv_transcoded_to")]
        try:
            if not expect.get("offered", True):
                if matches:
                    raise Failure("offered to the renderer, but it must be refused")
                print(f"PASS {label}: not offered to the renderer, as it must be")
                continue
            if len(matches) != 1:
                raise Failure(f"{len(matches)} resources for {case['title']} in the library: {sorted(resources)}")
            url = matches[0]
            before = len(json.loads(http(args.renderer + "/status")[1])["fetches"])
            for action, arguments in (
                ("SetAVTransportURI", [("InstanceID", 0), ("CurrentURI", url.replace("&", "&amp;")), ("CurrentURIMetaData", "")]),
                ("Play", [("InstanceID", 0), ("Speed", 1)]),
            ):
                code, body, _ = soap(transport, "urn:schemas-upnp-org:service:AVTransport:1", action, arguments, args.user_agent)
                if code != 200:
                    raise Failure(f"{action} returned HTTP {code}")
            if "seek" in case:
                wait_for(args.renderer, lambda s: len(s["fetches"]) > before and s["fetches"][before]["done"], "the first pull")
                soap(transport, "urn:schemas-upnp-org:service:AVTransport:1", "Seek",
                     [("InstanceID", 0), ("Unit", "REL_TIME"), ("Target", case["seek"])], args.user_agent)
                before += 1
            fetch = wait_for(args.renderer, lambda s: s["fetches"][before] if len(s["fetches"]) > before and s["fetches"][before]["done"] else None, "the pull")
            if fetch.get("error") or fetch.get("status") != 200:
                raise Failure(f"the renderer's pull failed: {fetch.get('error') or fetch.get('status')}")
            info, seen, problems = check_received(fetch["path"], expect)
            summary = f"{info['container']} {info['codec']} {info['width']}x{info['height']} {info['fps']} fps mark={info['mark']} pixels={seen}"
            if problems:
                raise Failure("; ".join(problems) + f" [{summary}]")
            print(f"PASS {label}: {summary}")
        except Failure as failure:
            failed = True
            print(f"FAIL {label}: {failure}")
    return 1 if failed else 0


def control(args):
    av = args.renderer + "/control/AVTransport"
    rc = args.renderer + "/control/RenderingControl"
    avs, rcs = "urn:schemas-upnp-org:service:AVTransport:1", "urn:schemas-upnp-org:service:RenderingControl:1"
    ua = args.user_agent
    failed = False

    def call(url, service, action, arguments):
        code, body, _ = soap(url, service, action, [("InstanceID", 0)] + arguments, ua)
        return code, soap_values(body) if body else {}

    def step(name, test):
        nonlocal failed
        try:
            detail = test()
            print(f"PASS control {name}: {detail}")
        except (Failure, AssertionError, KeyError, ValueError) as error:
            failed = True
            print(f"FAIL control {name}: {error}")

    def expect(condition, text):
        if not condition:
            raise Failure(text)
        return text

    def state():
        return call(av, avs, "GetTransportInfo", [])[1]["CurrentTransportState"]

    def seconds():
        h, m, s = call(av, avs, "GetPositionInfo", [])[1]["RelTime"].split(":")
        return int(h) * 3600 + int(m) * 60 + int(s)

    def refused_without_media():
        code, values = call(av, avs, "Play", [("Speed", 1)])
        return expect(code == 500 and values.get("errorCode") == "701", f"HTTP {code} {values}")

    def set_uri():
        call(av, avs, "SetAVTransportURI", [("CurrentURI", args.uri), ("CurrentURIMetaData", "")])
        return expect(state() == "STOPPED", state())

    def play():
        call(av, avs, "Play", [("Speed", 1)])
        return expect(state() == "PLAYING", state())

    def advances():
        time.sleep(2.2)
        return expect(seconds() >= 2, f"{seconds()} s")

    def pause():
        call(av, avs, "Pause", [])
        expect(state() == "PAUSED_PLAYBACK", state())
        first = seconds()
        time.sleep(1.2)
        return expect(seconds() == first, f"moved from {first} to {seconds()} s while paused")

    def seek():
        call(av, avs, "Seek", [("Unit", "REL_TIME"), ("Target", "0:00:05")])
        return expect(seconds() == 5, f"{seconds()} s")

    def resume():
        call(av, avs, "Play", [("Speed", 1)])
        time.sleep(1.2)
        return expect(state() == "PLAYING" and seconds() >= 6, f"{state()} {seconds()} s")

    def volume():
        call(rc, rcs, "SetVolume", [("Channel", "Master"), ("DesiredVolume", 55)])
        return expect(call(rc, rcs, "GetVolume", [("Channel", "Master")])[1]["CurrentVolume"] == "55", "volume 55")

    def mute():
        call(rc, rcs, "SetMute", [("Channel", "Master"), ("DesiredMute", 1)])
        expect(call(rc, rcs, "GetMute", [("Channel", "Master")])[1]["CurrentMute"] == "1", "not muted")
        call(rc, rcs, "SetMute", [("Channel", "Master"), ("DesiredMute", 0)])
        return expect(call(rc, rcs, "GetMute", [("Channel", "Master")])[1]["CurrentMute"] == "0", "muted and unmuted")

    def stop():
        call(av, avs, "Stop", [])
        return expect(state() == "STOPPED" and seconds() == 0, f"{state()} {seconds()} s")

    def out_of_range():
        code, values = call(rc, rcs, "SetVolume", [("Channel", "Master"), ("DesiredVolume", 120)])
        expect(code == 500 and values.get("errorCode") == "601", f"HTTP {code} {values}")
        return "volume 120 refused with UPnP error 601"

    def stayed():
        return expect(call(rc, rcs, "GetVolume", [("Channel", "Master")])[1]["CurrentVolume"] == "55", "55 after the refusal")

    step("play without media is refused with 701", refused_without_media)
    step("a URI sets the transport to STOPPED", set_uri)
    step("play", play)
    step("the position advances while playing", advances)
    step("pause holds the position", pause)
    step("seek to 0:00:05 while paused", seek)
    step("play resumes from the seek", resume)
    step("set and get the volume", volume)
    step("mute and unmute", mute)
    step("stop ends at position 0", stop)
    step("a volume out of range is refused with 601", out_of_range)
    step("the volume stayed", stayed)
    return 1 if failed else 0


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="mode", required=True)
    s = sub.add_parser("stream")
    s.add_argument("--cases", required=True)
    s.add_argument("--instance", required=True)
    s.add_argument("--server-ip", required=True)
    s.add_argument("--renderer", required=True, help="http://ip:port of the emulated renderer")
    s.add_argument("--user-agent", required=True)
    s.add_argument("--discovery-timeout", type=float, default=20)
    c = sub.add_parser("control")
    c.add_argument("--renderer", required=True)
    c.add_argument("--user-agent", required=True)
    c.add_argument("--uri", required=True)
    args = parser.parse_args()
    try:
        status = stream(args) if args.mode == "stream" else control(args)
    except (Failure, OSError, ValueError, KeyError, ET.ParseError) as failure:
        print(f"FAIL {args.mode}: {type(failure).__name__}: {failure}")
        status = 1
    sys.exit(status)


if __name__ == "__main__":
    main()
