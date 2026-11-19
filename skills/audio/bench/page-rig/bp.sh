nodedither(){ pw-dump | python3 -c "
import json,sys
for o in json.load(sys.stdin):
    p=o.get('info',{}).get('props',{})
    if p.get('node.name')=='alsa_output.rig_pcm16': print('rig_pcm16 dither.method =',p.get('dither.method'))"; }
echo before; nodedither
cp /src/steps-bp.json /tmp/steps.json
cat > /tmp/bp1.json <<'J'
[{"op":"apply","state":{"devices":{"alsa_output.rig_pcm16":{"bitPerfect":true}}},"what":"device:alsa_output.rig_pcm16"}]
J
cp /tmp/bp1.json /tmp/steps.json; qml6 /src/harness.qml 2>&1 | grep -o '"message":{[^}]*}'
echo after bit-perfect; nodedither
echo '[{"op":"apply","state":{},"what":"device:alsa_output.rig_pcm16"}]' >/tmp/steps.json; qml6 /src/harness.qml 2>&1 | grep -o '"message":{[^}]*}'
echo after back to automatic; nodedither
