head -c 400000000 /dev/zero | pw-cat -p --raw -P "{ node.name=player application.name=Player }" --target alsa_output.rig_dac --rate 96000 --format s32 --channels 2 - &
sleep 2
bash /src/ui.sh "$@"
