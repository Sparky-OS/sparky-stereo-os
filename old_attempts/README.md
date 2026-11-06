# The Python find and context tool, moved aside

`skills-context.py` (and its two tests) was the engine behind `sparky-stereo-skills find` and `context`.
The engine is now `sparky-stereo-skills-engine`, a small static program written in cgm-zig, which gives the same ranking, scores and context text (checked on 33 recorded rankings, 157 real symptoms and byte for byte on context output) and also serves the skills to AI assistants over the Model Context Protocol.
This copy stays because those checks were recorded from it and it is how they are regenerated.
Nothing was deleted: run `python3 -I old_attempts/skills-context.py --find "<symptom>"` on a checkout, as before.
