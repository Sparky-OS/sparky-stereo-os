#!/bin/bash
# vault-test.sh OWNER: the engine's own isolated_accounts_vault_roundtrip (the secret-service crate as DriveSync uses it:
# DH session, default collection, create, search, read, delete) on a private session bus answered by OWNER
# (kwallet: ksecretd unlocked as pam_kwallet does; gnome: gnome-keyring-daemon with an unlocked login keyring).
set -u
OWNER=$1; ROOT=$(mktemp -d /tmp/vault.XXXXXX); export HOME=$ROOT/home; mkdir -p "$HOME"
for d in data config cache runtime; do mkdir -m 700 "$ROOT/$d"; done
export XDG_DATA_HOME=$ROOT/data XDG_CONFIG_HOME=$ROOT/config XDG_CACHE_HOME=$ROOT/cache XDG_RUNTIME_DIR=$ROOT/runtime
export DRIVESYNC_TEST_VAULT_ROOT=$ROOT DBUS_SESSION_BUS_ADDRESS=unix:path=$ROOT/bus
dbus-daemon --session --fork --print-pid --address="$DBUS_SESSION_BUS_ADDRESS" > "$ROOT/bus.pid"
case "$OWNER" in
	kwallet) QT_QPA_PLATFORM=offscreen QT_LOGGING_RULES='kf.wallet*=true;ksecretd*=true' python3 -I /lane/kwallet-login.py "$ROOT/ksecretd.log" > /dev/null ;;
	gnome) printf 'rig' | gnome-keyring-daemon --unlock --components=secrets > /dev/null 2>&1 ;;
esac
for i in $(seq 50); do gdbus call --session --dest org.freedesktop.DBus --object-path /org/freedesktop/DBus --method org.freedesktop.DBus.NameHasOwner org.freedesktop.secrets 2>/dev/null | grep -q true && break; sleep 0.2; done
echo "owner: $(gdbus call --session --dest org.freedesktop.DBus --object-path /org/freedesktop/DBus --method org.freedesktop.DBus.GetNameOwner org.freedesktop.secrets 2>&1)"
echo "default alias: $(gdbus call --session --dest org.freedesktop.secrets --object-path /org/freedesktop/secrets --method org.freedesktop.Secret.Service.ReadAlias default 2>&1)"
echo "collections: $(gdbus call --session --dest org.freedesktop.secrets --object-path /org/freedesktop/secrets --method org.freedesktop.DBus.Properties.Get org.freedesktop.Secret.Service Collections 2>&1)"
echo "dh session: $(gdbus call --session --dest org.freedesktop.secrets --object-path /org/freedesktop/secrets --method org.freedesktop.Secret.Service.OpenSession dh-ietf1024-sha256-aes128-cbc-pkcs7 "<@ay [0x02]>" 2>&1 | cut -c1-160)"
/bin/test-binary --ignored --exact accounts::tests::isolated_accounts_vault_roundtrip --nocapture 2>&1 | tail -25
echo "test exit ${PIPESTATUS[0]}"
[ -f "$ROOT/ksecretd.log" ] && { echo "--- ksecretd log"; grep -v "^$" "$ROOT/ksecretd.log" | tail -25; }
kill $(cat "$ROOT/bus.pid") 2>/dev/null
