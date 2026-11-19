#!/bin/bash
# qml-steps.sh STEPS.json : run the SpeakerSetup harness with a steps file (the real type from the plugin, no screen)
cp "$1" /tmp/steps.json && qml6 /src/harness.qml 2>&1 | grep -E "^qml: (DUMP|RESULT)|rror|Warning|warn" | sed 's/^qml: //'
