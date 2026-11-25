#!/bin/sh
# Runs inside the throwaway container as root: installs Debian's pychromecast,
# makes a self-signed certificate, starts receiver.py, runs sender.py, checks
# the expected sequence in the receiver log, and leaves the evidence owned by
# the calling user.  Nothing here reaches the LAN: the receiver listens on
# 127.0.0.1 only and the sender connects by address.
set -eu
HERE="$(cd "$(dirname "$0")" && pwd)"
OUT="$1"
UIDGID="$2"
mkdir -p "$OUT"

export DEBIAN_FRONTEND=noninteractive
apt-get -qq update
apt-get -qq -y install --no-install-recommends python3-pychromecast python3-protobuf openssl ca-certificates >"$OUT/apt.log" 2>&1
dpkg-query -W -f='${Package} ${Version}\n' python3-pychromecast python3-protobuf python3-zeroconf openssl 2>/dev/null > "$OUT/versions.txt" || true
. /etc/os-release; echo "$PRETTY_NAME" >> "$OUT/versions.txt"
python3 -c "import pychromecast, inspect; print('pychromecast', pychromecast.__version__ if hasattr(pychromecast,'__version__') else '?')" >> "$OUT/versions.txt" 2>&1 || true

cd "$OUT"
openssl req -x509 -newkey rsa:2048 -nodes -keyout key.pem -out cert.pem -days 1 \
  -subj "/CN=software-cast-receiver" >/dev/null 2>&1
openssl x509 -in cert.pem -noout -subject -issuer > cert-info.txt

rm -f receiver.log
python3 "$HERE/receiver.py" receiver.log cert.pem key.pem &
RECV=$!
sleep 1
set +e
python3 "$HERE/sender.py" sender.json > sender.out 2>&1
SENDER_RC=$?
set -e
echo "sender exit $SENDER_RC" >> sender.out
# give the receiver a moment to log the CLOSE, then stop it
for i in 1 2 3 4 5 6 7 8 9 10; do kill -0 $RECV 2>/dev/null || break; sleep 0.5; done
kill $RECV 2>/dev/null || true
wait $RECV 2>/dev/null || true

# The check: the sequence the public senders use, in order.
python3 - receiver.log check.txt <<'EOF'
import json, sys
lines = [json.loads(l) for l in open(sys.argv[1])]
def find(pred):
    for i, e in enumerate(lines):
        if pred(e):
            return i
    return -1
steps = [
  ("tls accepted with a self-signed certificate", lambda e: e.get("event") == "tls-accepted"),
  ("CONNECT on the connection namespace to receiver-0", lambda e: e.get("dir") == "recv" and e.get("ns","").endswith("tp.connection") and e.get("payload",{}).get("type") == "CONNECT" and e.get("dst") == "receiver-0"),
  ("GET_STATUS on the receiver namespace", lambda e: e.get("dir") == "recv" and e.get("ns","").endswith("cast.receiver") and e.get("payload",{}).get("type") == "GET_STATUS"),
  ("LAUNCH CC1AD845 (Default Media Receiver)", lambda e: e.get("event") == "launch" and e.get("appId") == "CC1AD845"),
  ("CONNECT to the app transport web-1", lambda e: e.get("dir") == "recv" and e.get("ns","").endswith("tp.connection") and e.get("payload",{}).get("type") == "CONNECT" and e.get("dst") == "web-1"),
  ("LOAD on the media namespace, video/mp4, LIVE", lambda e: e.get("event") == "load" and e.get("contentType") == "video/mp4" and e.get("streamType") == "LIVE"),
  ("MEDIA_STATUS PLAYING sent back", lambda e: e.get("dir") == "send" and e.get("ns","").endswith("cast.media") and e.get("payload",{}).get("status") and e["payload"]["status"][0].get("playerState") == "PLAYING"),
  ("STOP the app (quit) on the receiver namespace", lambda e: e.get("dir") == "recv" and e.get("ns","").endswith("cast.receiver") and e.get("payload",{}).get("type") == "STOP"),
  ("CLOSE from the sender", lambda e: e.get("event") == "sender-closed-channel"),
]
ok = True
last = -1
out = []
for name, pred in steps:
    idx = find(lambda e, p=pred: p(e))
    status = "PASS" if idx > last else ("FAIL (out of order)" if idx >= 0 else "FAIL (missing)")
    if not status.startswith("PASS"):
        ok = False
    out.append(f"{status:20s} {name} (line {idx+1})")
    if idx > last:
        last = idx
auth = find(lambda e: e.get("event") == "device-auth-challenge")
out.append(f"{'INFO':20s} device authentication challenge from this sender: {'yes' if auth >= 0 else 'none (pychromecast does not verify the receiver certificate)'}")
pings = sum(1 for e in lines if e.get("dir") == "recv" and e.get("payload",{}).get("type") == "PING")
out.append(f"{'INFO':20s} heartbeat PINGs answered: {pings}")
out.append(f"RESULT: {'PASS' if ok else 'FAIL'} ({len(lines)} log lines)")
open(sys.argv[2], "w").write("\n".join(out) + "\n")
print("\n".join(out))
EOF

rm -f key.pem
chown -R "$UIDGID" "$OUT"
