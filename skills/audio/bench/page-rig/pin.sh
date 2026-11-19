head -c 40000000 /dev/zero | pw-cat -p --raw -P "{ node.force-rate=44100 node.name=pinner application.name=Pinner }" --target alsa_output.rig_dac --rate 44100 --format s16 --channels 2 - &
sleep 2
bash /src/qml-steps.sh /src/steps-pin.json
