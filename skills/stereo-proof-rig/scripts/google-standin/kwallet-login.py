#!/usr/bin/python3
"""kwallet-login.py: unlock (or create) the person's KDE Wallet the way pam_kwallet5 does at a display manager's login.

KWallet 6.32's ksecretd takes `--pam-login PIPE SOCKET`: it reads the 56-byte key pam_kwallet derives from the login
password from PIPE, then accepts one connection on the listening SOCKET and reads the session's environment as VAR=value
lines (pam_kwallet_init sends `env`), then opens or creates the local wallet with that key and answers
org.freedesktop.secrets (kwallet src/runtime/ksecretd/main.cpp, v6.32.0); it does so only when PAM_KWALLET5_LOGIN is in its environment. Here the key is random: no password exists.
"""
import os
import socket
import subprocess
import sys

run = os.environ['XDG_RUNTIME_DIR']
path = os.path.join(run, 'kwallet5.socket')
if os.path.exists(path):
	os.unlink(path)
r, w = os.pipe()
os.write(w, os.urandom(56))
os.close(w)
server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
server.bind(path)
server.listen(5)
env = {k: v for k, v in os.environ.items() if k != 'XDG_SESSION_ID'}
# ksecretd reads --pam-login only when PAM_KWALLET5_LOGIN names the socket, as pam_kwallet sets it (main.cpp, v6.32.0)
env['PAM_KWALLET5_LOGIN'] = path
env.setdefault('QT_QPA_PLATFORM', 'offscreen')
log = open(sys.argv[1] if len(sys.argv) > 1 else os.devnull, 'ab')
process = subprocess.Popen(['ksecretd', '--pam-login', str(r), str(server.fileno())], pass_fds=(r, server.fileno()),
	env=env, stdout=log, stderr=log, start_new_session=True)
os.close(r)
client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
client.connect(path)
client.sendall(''.join(f'{k}={v}\n' for k, v in env.items()).encode())
client.close()
server.close()
print(process.pid)
