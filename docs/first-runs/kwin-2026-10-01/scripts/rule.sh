#!/bin/sh
# Stereo content window rule for a test: rule.sh <name> <wmclass regex> <content>|off
# content: sbs-half, sbs-half-right-first, sbs-full, tab-half, tab-full, ... (rulesettings.kcfg)
set -eu
. "$(dirname "$0")/session.env"
name=$1 class=$2 content=$3
rules=$(kreadconfig6 --file kwinrulesrc --group General --key rules)
if [ "$content" = off ]; then
    kwriteconfig6 --file kwinrulesrc --group "$name" --key stereo3drule --delete
    kwriteconfig6 --file kwinrulesrc --group "$name" --key stereo3d --delete
else
    case ",$rules," in
    *",$name,"*) ;;
    *)
        rules=${rules:+$rules,}$name
        kwriteconfig6 --file kwinrulesrc --group General --key rules "$rules"
        kwriteconfig6 --file kwinrulesrc --group General --key count "$(echo "$rules" | tr ',' '\n' | wc -l)"
        kwriteconfig6 --file kwinrulesrc --group "$name" --key Description "Stereo content test: $class"
        kwriteconfig6 --file kwinrulesrc --group "$name" --key wmclass "$class"
        kwriteconfig6 --file kwinrulesrc --group "$name" --key wmclassmatch 3
        ;;
    esac
    kwriteconfig6 --file kwinrulesrc --group "$name" --key stereo3d "$content"
    kwriteconfig6 --file kwinrulesrc --group "$name" --key stereo3drule 2
fi
qdbus6 org.kde.KWin /KWin reconfigure
echo "rule $name ($class): stereo content $content"
