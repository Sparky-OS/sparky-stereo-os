head -c 400000000 /dev/zero | pw-cat -p --raw -P "{ node.name=player application.name=Player }" --target alsa_output.rig_pcm16 --rate 44100 --format s16 --channels 2 - &
sleep 2
bash /src/ui.sh ${UI_DIR:-ui-green} snap:main "press:Sound Quality…" sleep:3 resize sleep:4 snap:page \
  click:585,1060 sleep:2 snap:popup key:Down key:Down key:Return sleep:12 snap:after-format \
  click:585,1135 sleep:2 key:Down key:Down key:Down key:Down key:Return sleep:12 snap:after-rate
echo "--- dac node after the page's choices"
pw-dump | python3 -c "
import json,sys
for o in json.load(sys.stdin):
    p=o.get('info',{}).get('props',{})
    if p.get('node.name')=='alsa_output.rig_dac': print({k:v for k,v in p.items() if k.startswith(('audio.','dither'))})"
cat /home/rig/.config/wireplumber/wireplumber.conf.d/50-sound-page.conf
