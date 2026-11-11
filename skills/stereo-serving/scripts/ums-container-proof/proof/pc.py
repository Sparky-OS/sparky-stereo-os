#!/usr/bin/env python3
"""A 3D film pushed from UMS to the PC as a renderer.

Run inside the PC container's network namespace. It finds UMS by SSDP, browses
its library as the PC (the address UMS knows from Rygel's announcement), finds
Rygel's MediaRenderer by SSDP, sets the film's URL on its AVTransport with the
item's DIDL-Lite and plays it, then reads Rygel's own answers: the transport
state, the track URI and the position, which Rygel takes from the MPRIS2
player. The player's side (PlaybackStatus, xesam:url) is read by the runner
with pc-probe.sh on the bus Rygel talks to.

One line per check, "PASS" or "FAIL" first; the pushed URL goes to
/records/pushed-url.txt.
"""
import argparse
import os
import socket
import sys
import time
import urllib.parse
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import proof  # noqa: E402


def find_renderer(address, timeout):
    message = "\r\n".join([
        "M-SEARCH * HTTP/1.1", f"HOST: {proof.SSDP[0]}:{proof.SSDP[1]}", 'MAN: "ssdp:discover"', "MX: 1",
        "ST: urn:schemas-upnp-org:device:MediaRenderer:1", "", "",
    ]).encode()
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.bind((address, 0))
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_IF, socket.inet_aton(address))
        sock.settimeout(1)
        deadline = time.monotonic() + timeout
        next_search = 0.0
        while time.monotonic() < deadline:
            if time.monotonic() >= next_search:
                sock.sendto(message, proof.SSDP)
                next_search = time.monotonic() + 2
            try:
                data, _ = sock.recvfrom(65536)
            except socket.timeout:
                continue
            for line in data.decode("utf-8", "replace").splitlines():
                if line.upper().startswith("LOCATION:"):
                    location = line.split(":", 1)[1].strip()
                    if urllib.parse.urlparse(location).hostname == address:
                        return location
    raise proof.Failure(f"no MediaRenderer announced by {address}")


def av_control(location):
    status, body, _ = proof.http(location)
    root = ET.fromstring(body)
    ns = "{urn:schemas-upnp-org:device-1-0}"
    friendly = root.findtext(f".//{ns}friendlyName")
    for service in root.iter(f"{ns}service"):
        if ":AVTransport:" in (service.findtext(f"{ns}serviceType") or ""):
            return friendly, urllib.parse.urljoin(location, service.findtext(f"{ns}controlURL")), service.findtext(f"{ns}serviceType")
    raise proof.Failure("the renderer has no AVTransport")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--address", required=True, help="this container's address")
    parser.add_argument("--server-ip", required=True)
    parser.add_argument("--user-agent", required=True)
    parser.add_argument("--title", required=True)
    parser.add_argument("--mime", default="video/x-matroska")
    args = parser.parse_args()
    failed = False
    state = {}
    ua = "ProofController/1.0"

    def check(name, test):
        nonlocal failed
        try:
            print(f"PASS pc {name}: {test()}")
        except (proof.Failure, OSError, KeyError, ValueError, ET.ParseError) as error:
            failed = True
            print(f"FAIL pc {name}: {type(error).__name__}: {error}")

    def call(action, arguments):
        code, body, _ = proof.soap(state["control"], state["service"], action, [("InstanceID", 0)] + arguments, ua)
        values = proof.soap_values(body) if body else {}
        if code != 200:
            raise proof.Failure(f"{action} returned HTTP {code}: {values}")
        return values

    def library():
        location = proof.discover_server(args.server_ip, args.user_agent, 20)
        control, service = proof.content_directory(location, args.user_agent)
        resources = proof.library(control, service, args.user_agent, {args.title}, location)
        urls = [url for name, url in resources.items() if name.startswith(args.title + ".mkv")]
        if len(urls) != 1:
            raise proof.Failure(f"{len(urls)} resources for {args.title}: {sorted(resources)}")
        state["url"] = urls[0]
        return urls[0]

    def renderer():
        location = find_renderer(args.address, 30)
        friendly, control, service = av_control(location)
        state["control"], state["service"] = control, service
        return f"{friendly} at {location}"

    def push():
        url = state["url"]
        # what a controller sends: the item as DIDL-Lite with the resource's protocolInfo, escaped into the argument
        didl = (
            '<DIDL-Lite xmlns="urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/" xmlns:dc="http://purl.org/dc/elements/1.1/" '
            'xmlns:upnp="urn:schemas-upnp-org:metadata-1-0/"><item id="1" parentID="0" restricted="1">'
            f"<dc:title>{args.title}</dc:title><upnp:class>object.item.videoItem</upnp:class>"
            f'<res protocolInfo="http-get:*:{args.mime}:*">{url}</res></item></DIDL-Lite>'
        )
        escaped = didl.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        call("SetAVTransportURI", [("CurrentURI", url.replace("&", "&amp;")), ("CurrentURIMetaData", escaped)])
        call("Play", [("Speed", 1)])
        with open("/records/pushed-url.txt", "w") as output:
            output.write(url + "\n")
        return "SetAVTransportURI and Play accepted"

    def plays():
        deadline = time.monotonic() + 40
        last = {}
        while time.monotonic() < deadline:
            last = call("GetTransportInfo", [])
            if last.get("CurrentTransportState") == "PLAYING":
                return f"Rygel reports {last['CurrentTransportState']}"
            time.sleep(0.5)
        raise proof.Failure(f"Rygel never reported PLAYING: {last}")

    def position():
        def seconds():
            h, m, s = call("GetPositionInfo", [])["RelTime"].split(":")
            return int(h) * 3600 + int(m) * 60 + float(s)
        first = seconds()
        time.sleep(1.6)
        second = seconds()
        if not second > first:
            raise proof.Failure(f"position {first} then {second}")
        return f"position {first:.1f} s then {second:.1f} s"

    def track():
        values = call("GetPositionInfo", [])
        if state["url"] not in values.get("TrackURI", ""):
            raise proof.Failure(f"TrackURI {values.get('TrackURI')!r}")
        return values["TrackURI"]

    check("UMS lists the film for the PC", library)
    check("Rygel announces the player as a MediaRenderer", renderer)
    check("the film is pushed to the player", push)
    check("Rygel reports the player playing", plays)
    check("the position moves", position)
    check("Rygel's track is the URL UMS gave", track)
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
