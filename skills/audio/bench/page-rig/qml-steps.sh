#!/bin/bash
# qml-steps.sh STEPS.json : run the SoundFormats harness with a steps file
cp "$1" /tmp/steps.json && qml6 /src/harness.qml 2>&1 | grep -E "^qml: (DUMP|RESULT)|rror|Warning" | sed 's/^qml: //'
