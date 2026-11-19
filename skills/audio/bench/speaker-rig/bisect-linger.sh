#!/bin/bash
# bisect-linger.sh : the four forms of the setup's playback.props (both flags, dont-fallback alone, linger alone, neither) at a fresh start:
# does the setup's sink exist, is its output linked to the device, and where does it go when the device leaves?
# Run as the user rig in the session (rig-run.sh NAME IMAGE bash /src/bisect-linger.sh) of an image with the package.
cat > /tmp/s.json <<'J'
[{"op":"apply","node":"alsa_output.rig_51","makeDefault":false,"state":{"devices":{"alsa_output.rig_51":{"positions":["FL","FR","FC","LFE","RL","RR"],"distances":{"FL":2.0,"FR":3.0,"FC":3.0,"LFE":3.0,"RL":3.0,"RR":3.0}}}}}]
J
bash /src/qml-steps.sh /tmp/s.json | grep -c '"ok":true'
F=~/.config/pipewire/pipewire.conf.d/50-speaker-page.conf
cp $F /tmp/both.conf
has() { pw-cli ls Node | grep -q "node.name = \"$1\""; }
for form in "both:node.dont-fallback = true node.linger = true" "fallback-only:node.dont-fallback = true" "linger-only:node.linger = true" "neither:"; do
  name=${form%%:*}; flags=${form#*:}
  sed "s/node.dont-fallback = true node.linger = true/$flags/" /tmp/both.conf > $F
  systemctl --user restart wireplumber.service pipewire.service; sleep 5
  sink=no; has speaker_setup.alsa_output.rig_51 && sink=yes
  linked=$(pw-link -l | grep -A8 "^speaker_setup_out" | grep -c "|-> alsa_output.rig_51")
  id=$(pw-dump | python3 -c "
import json,sys
for o in json.load(sys.stdin):
    if o.get('info',{}).get('props',{}).get('node.name')=='alsa_output.rig_51': print(o['id'])")
  after=n/a
  if [ "$sink" = yes ]; then
    pw-cli destroy $id; sleep 4
    after=$(pw-link -l | grep -A8 "^speaker_setup_out" | grep "|->" | sed 's/.*|-> //; s/:.*//' | sort -u | tr '\n' ' ')
    [ -z "$after" ] && after="no link"
    has speaker_setup.alsa_output.rig_51 || after="$after (sink gone)"
  fi
  echo "FORM $name: sink-exists=$sink output-links-to-device=$linked after-device-leaves: $after"
done
