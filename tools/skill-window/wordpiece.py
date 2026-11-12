# SPDX-License-Identifier: GPL-2.0-or-later
"""Count the word pieces a text becomes for the skills index, with no dependency.

The local skills index embeds each skill's name and description with
sentence-transformers/all-MiniLM-L6-v2, whose model card says: "By default, input text
longer than 256 word pieces is truncated." What is cut off is never embedded, so the last
trigger words of a long description stop routing to the skill.

This module does what that model's tokenizer does (BERT, uncased): drop control characters
and accents, lowercase, split on white space, give punctuation and CJK characters a token
of their own, then cut each word into the longest pieces the vocabulary holds.
Two files beside it carry the model's own data: vocab.txt (its vocabulary, unchanged) and
char-classes.txt (how its tokenizer treats every code point, read from the tokenizer
itself, so the answer does not depend on the Unicode tables of the Python that runs it).
count() includes the [CLS] and [SEP] tokens the model adds, as the index's window does.
README.md in this folder says where both files come from and how the answers were checked.
"""
import bisect
import hashlib
import unicodedata
from pathlib import Path

HERE = Path(__file__).resolve().parent
VOCAB = HERE / 'vocab.txt'
VOCAB_SHA256 = '07eced375cec144d27c900241f3e339478dec958f92fddbc551f295c992038a3'
CLASSES = HERE / 'char-classes.txt'
CLASSES_SHA256 = 'e916d0b176783b7b0bc3e30935bdef4d5dde333fb636c998440f2923f3458bb4'
WINDOW = 256
MAX_WORD_CHARS = 100
SPECIAL = ('[PAD]', '[UNK]', '[CLS]', '[SEP]', '[MASK]')
VANISH, SPACE, ALONE = 'vanish', 'space', 'alone'
_cache = {}


class DataError(Exception):
    """A data file is missing or is not the model's own."""


def _read(path, sha256, what):
    try:
        data = Path(path).read_bytes()
    except OSError as e:
        raise DataError(f'cannot read {what} {path}: {e}') from e
    if sha256 and hashlib.sha256(data).hexdigest() != sha256:
        raise DataError(f'{path} is not {what} of all-MiniLM-L6-v2 (its SHA-256 is not {sha256}); '
                        'restore the file from git')
    return data.decode('utf-8')


def load_vocab(path=VOCAB, sha256=VOCAB_SHA256):
    """The vocabulary as a set. Pass sha256=None for another model's vocabulary."""
    key = ('vocab', str(path))
    if key not in _cache:
        _cache[key] = frozenset(_read(path, sha256, 'the vocabulary').split('\n')) - {''}
    return _cache[key]


def _load_classes():
    if 'classes' not in _cache:
        spans = []
        for line in _read(CLASSES, CLASSES_SHA256, 'the character table').splitlines():
            name, *ranges = line.split()
            for r in ranges:
                first, _, last = r.partition('-')
                spans.append((int(first, 16), int(last or first, 16), name))
        spans.sort()
        _cache['classes'] = ([s[0] for s in spans], spans)
    return _cache['classes']


def char_class(ch):
    """'vanish', 'space', 'alone' or None for an ordinary character."""
    starts, spans = _load_classes()
    i = bisect.bisect_right(starts, ord(ch)) - 1
    if i >= 0 and spans[i][1] >= ord(ch):
        return spans[i][2]
    return None


def _normalize(text):
    out = []
    for ch in text:
        cls = char_class(ch)
        if cls == VANISH:
            continue
        out.append(' ' if cls == SPACE else f' {ch} ' if cls == ALONE else ch)
    text = unicodedata.normalize('NFD', ''.join(out))
    # the accents a letter decomposes into vanish too; lowercase one character at a time, as the tokenizer does
    return ''.join(ch.lower() for ch in text if char_class(ch) != VANISH)


def _words(text):
    for chunk in text.split():
        word = []
        for ch in chunk:
            if char_class(ch) == ALONE:
                if word:
                    yield ''.join(word)
                    word = []
                yield ch
            else:
                word.append(ch)
        if word:
            yield ''.join(word)


def _pieces(word, vocab):
    if len(word) > MAX_WORD_CHARS:
        return ['[UNK]']
    pieces, start = [], 0
    while start < len(word):
        end = len(word)
        piece = None
        while start < end:
            candidate = ('##' if start else '') + word[start:end]
            if candidate in vocab:
                piece = candidate
                break
            end -= 1
        if piece is None:
            return ['[UNK]']
        pieces.append(piece)
        start = end
    return pieces


def tokenize(text, vocab=None):
    """The word pieces of text, without [CLS] and [SEP]."""
    vocab = load_vocab() if vocab is None else vocab
    out = []
    rest = text
    while rest:
        # a special token written in the text is one token, as the model's tokenizer treats it
        hits = [(rest.find(s), s) for s in SPECIAL if s in rest]
        if not hits:
            segment, special, rest = rest, None, ''
        else:
            at, special = min(hits)
            segment, rest = rest[:at], rest[at + len(special):]
        for word in _words(_normalize(segment)):
            out.extend(_pieces(word, vocab))
        if special:
            out.append(special)
    return out


def count(text, vocab=None):
    """How many tokens the model sees for text, [CLS] and [SEP] included."""
    return len(tokenize(text, vocab)) + 2


def embedded_text(name, description):
    """What the index embeds for a skill: the name, a blank line, the description on one line."""
    return f"{' '.join(str(name).split())}\n\n{' '.join(str(description).split())}"


def split_at_window(text, window=WINDOW, vocab=None):
    """The words of text that fit the window and the words after them, as two strings."""
    vocab = load_vocab() if vocab is None else vocab
    budget = window - 2
    words = text.split()
    for i, word in enumerate(words):
        n = len(tokenize(word, vocab))
        if n > budget:
            return ' '.join(words[:i]), ' '.join(words[i:])
        budget -= n
    return ' '.join(words), ''
