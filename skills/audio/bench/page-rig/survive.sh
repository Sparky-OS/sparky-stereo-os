bash /src/qml-steps.sh /src/steps-g1.json >/dev/null 2>&1
echo "--- after the page's change"; pw-metadata -n settings | grep -E "clock.(rate|allowed-rates|quantum)'"
systemctl --user restart pipewire.service wireplumber.service; sleep 4
echo "--- after a restart of the session's audio (no engine apply)"; pw-metadata -n settings | grep -E "clock.(rate|allowed-rates|quantum)'"
echo "--- node quality after restart"; pw-dump | python3 -c "
import json,sys
for o in json.load(sys.stdin):
    p=o.get('info',{}).get('props',{})
    if str(p.get('node.name','')).startswith('alsa_output.'): print(p['node.name'],'resample.quality',p.get('resample.quality'))"
