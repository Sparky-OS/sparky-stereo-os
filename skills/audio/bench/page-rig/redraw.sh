cp /src/steps-dump.json /tmp/steps.json; qml6 /src/harness.qml 2>&1 | grep -v "^Detected\|^Qt depends\|^If this\|^for more" | head -5
