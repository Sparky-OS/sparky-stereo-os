# A software Cast receiver, for proofs on loopback

From the cast study of 2026-10-14, copied unchanged.
`receiver.py` speaks the CASTv2 channel on 127.0.0.1:8009 (TLS with a self-signed certificate; the connection, heartbeat, receiver and media namespaces), logs every message as one JSON line, answers a `LAUNCH` of the Default Media Receiver (`CC1AD845`) and a `LAUNCH_ERROR` for any other app id.
`sender.py` is Debian's pychromecast connecting to it by address; nothing browses DNS-SD.
`inside.sh` installs `python3-pychromecast`, `python3-protobuf` and `openssl`, makes the certificate, runs both and checks the nine steps of the public senders' sequence in order into `check.txt`.

## Run

In a throwaway Debian testing container, as root, with this folder mounted read-only and an output folder mounted read-write:

```sh
docker run --rm --ulimit core=1 --platform linux/amd64 \
  -v "$PWD:/proof:ro" -v "$OUT:/out" debian:testing@sha256:DIGEST \
  sh /proof/inside.sh /out "$(id -u):$(id -g)"
```

`inside.sh` fetches the three packages with apt, so as written it needs the container's network for apt; the receiver listens on 127.0.0.1 only and the sender connects by address.
A proof of anything that discovers or announces (a DNS-SD responder beside the receiver, the daemon's browse) runs with `--network none` and both ends in that one container: install the packages into an image first, then run the same steps offline.
Never run it on a network that has a real Cast device.

## Expected

`check.txt`: nine `PASS` lines in order (TLS accepted, `CONNECT` to `receiver-0`, `GET_STATUS`, `LAUNCH CC1AD845`, `CONNECT` to `web-1`, `LOAD` of `video/mp4` `LIVE`, `MEDIA_STATUS PLAYING`, `STOP`, `CLOSE`), "device authentication challenge from this sender: none", and `RESULT: PASS`.
The study measured `LOAD` to `MEDIA_STATUS` at 0.126 s on loopback with pychromecast 14.0.10.
Not rerun since the study.
