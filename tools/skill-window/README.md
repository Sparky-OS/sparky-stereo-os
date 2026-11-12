# The description window, counted without a model

**For** anyone who writes or reviews a skill: how `tools/check-skills.py` knows whether the index will embed the whole description, and where the two data files here come from.

## What is counted

A local skills index embeds one text per skill: the name, a blank line, and the description on one line.
The edition's index uses sentence-transformers/all-MiniLM-L6-v2 through FastEmbed.
The model's card says: "By default, input text longer than 256 word pieces is truncated."
FastEmbed's copy of the tokenizer carries the same number (`"truncation": {"max_length": 256}`).
The 256 include the two tokens the model adds itself, `[CLS]` and `[SEP]`.
Words past the window are never embedded, so a symptom written at the end of a long description stops leading to the skill.

`wordpiece.py` counts those tokens with Python alone: no model, no network, no library beyond the standard one.

```sh
python3 tools/check-skills.py --count                 # every skill, largest first
python3 tools/check-skills.py --count stereo-video    # one skill
```

## The files

| File | What it is | Source | SHA-256 |
| --- | --- | --- | --- |
| `vocab.txt` | The model's vocabulary, 30,522 word pieces, unchanged | `vocab.txt` of [sentence-transformers/all-MiniLM-L6-v2](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2) at revision `1110a243fdf4706b3f48f1d95db1a4f5529b4d41`, byte for byte the `vocab.txt` of [google-bert/bert-base-uncased](https://huggingface.co/google-bert/bert-base-uncased) at `86b5e0934494bd15c9632b12f734a8a67f723594`; both under the Apache License 2.0 | `07eced375cec144d27c900241f3e339478dec958f92fddbc551f295c992038a3` |
| `char-classes.txt` | How the model's tokenizer treats every code point: it vanishes, it splits words like a space, or it is a token of its own | Made by `regenerate.py` from the `tokenizer.json` of [Qdrant/all-MiniLM-L6-v2-onnx](https://huggingface.co/Qdrant/all-MiniLM-L6-v2-onnx) at `d13954661f83248295ba75c1ed411eef3b7b936e` (SHA-256 `851ca67100d372ca3ae031a6abd168f53489eebfd7d89523f35c5c9b4d372c3c`), the copy FastEmbed downloads, with tokenizers 0.23.1 | `e916d0b176783b7b0bc3e30935bdef4d5dde333fb636c998440f2923f3458bb4` |
| `window-goldens.tsv` | The model tokenizer's own count for 287 texts, one per line: the count, a tab, the text as a JSON string | Made by `regenerate.py` in the same run | `0fb407774969560b8cac7a5bde12aa16e5a68dba760d463c57749a11d9600f4d` |

`wordpiece.py` checks the SHA-256 of `vocab.txt` and of `char-classes.txt` before it counts.
A changed or missing file stops `check-skills.py` with the reason; it never counts with other data.

The vocabulary is BERT's, by Jacob Devlin, Ming-Wei Chang, Kenton Lee and Kristina Toutanova (Google), as the model card of bert-base-uncased cites them.
all-MiniLM-L6-v2 is the sentence-transformers project's model, fine-tuned from `nreimers/MiniLM-L6-H384-uncased`, as its card says.

## How the counter was checked

All on 2026-11-12, against tokenizers 0.23.1 with the `tokenizer.json` above:

- Every Unicode code point (1,112,064 of them), each placed between two letters: the same tokens from both.
- 23,151 texts, being every line of every Markdown file in this repository (the README translations in Japanese, Korean, Chinese, Polish, Portuguese, French and German among them), every `SKILL.md` whole, 60 hard cases and 4,000 seeded random strings: the same tokens from both.
- The same counts under Python 3.12 (Unicode 15.0) and Python 3.14 (Unicode 16.0).
  The character table comes from the tokenizer itself, so the count does not follow the Unicode tables of the Python that runs it.
- `tools/tests/test_check_skills.py` keeps 287 of those texts as a test, and each of six planted mistakes in the counter or the check made it fail.

Theoretically, a character added to Unicode after the Python in use and carrying a decomposition or a case mapping could be counted differently, because decomposition and lowercasing come from Python.
No text in the checks above met that case.

## When the index changes its model

`regenerate.py` rebuilds `char-classes.txt` and `window-goldens.tsv` from the new model's `tokenizer.json`.
It is the one script here that needs the `tokenizers` library.
Replace `vocab.txt` with the new model's file, put the three new SHA-256 values into `wordpiece.py` and this page, set `WINDOW` to the new model's window, and run the tests.
The counter does BERT's WordPiece only; a model with another kind of tokenizer needs another counter, and until one exists `--window 0` switches the check off and says so in its output.
