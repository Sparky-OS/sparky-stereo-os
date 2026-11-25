#!/usr/bin/env python3
"""The sender side of the handshake proof: pychromecast (Debian's package) against receiver.py.

It connects by address (no mDNS, so nothing on the LAN is touched), reads the
receiver status, launches the Default Media Receiver, sends a LOAD for a LIVE
video/mp4 stream, waits for the media status, and records what it saw.
"""
import json
import sys
import time
import uuid

import pychromecast
from pychromecast.controllers.media import STREAM_TYPE_LIVE

out_path = sys.argv[1] if len(sys.argv) > 1 else "sender.json"
result = {"pychromecast": pychromecast.__version__ if hasattr(pychromecast, "__version__") else "unknown"}

host = ("127.0.0.1", 8009, uuid.UUID("7e2f0e77-0000-0000-0000-00000000c0de"), "Software receiver", "Cast proof")
cast = pychromecast.get_chromecast_from_host(host, tries=1, timeout=10)
cast.wait(timeout=15)
result["connected"] = cast.socket_client.is_connected
result["receiver_status_before"] = {
    "app_id": cast.app_id,
    "display_name": cast.app_display_name,
    "is_idle": cast.is_idle,
    "volume": cast.status.volume_level if cast.status else None,
}
result["device"] = {
    "friendly_name": cast.cast_info.friendly_name,
    "model_name": cast.cast_info.model_name,
    "cast_type": cast.cast_info.cast_type,
    "manufacturer": cast.cast_info.manufacturer,
}

mc = cast.media_controller
t0 = time.monotonic()
mc.play_media("http://127.0.0.1:8000/kwin-output-1.mp4", "video/mp4",
              title="Cast: proof output", stream_type=STREAM_TYPE_LIVE)
mc.block_until_active(timeout=15)
t1 = time.monotonic()
result["load_to_media_status_s"] = round(t1 - t0, 3)
result["receiver_status_after"] = {
    "app_id": cast.app_id,
    "display_name": cast.app_display_name,
    "transport_id": cast.status.transport_id if cast.status else None,
    "session_id": cast.status.session_id if cast.status else None,
}
result["media_status"] = {
    "player_state": mc.status.player_state,
    "content_id": mc.status.content_id,
    "content_type": mc.status.content_type,
    "stream_type": mc.status.stream_type,
    "media_session_id": mc.status.media_session_id,
}
cast.quit_app()
time.sleep(0.5)
cast.disconnect(timeout=5)
result["disconnected"] = not cast.socket_client.is_connected

with open(out_path, "w") as f:
    json.dump(result, f, indent=2)
print(json.dumps(result, indent=2))
