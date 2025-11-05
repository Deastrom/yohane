from collections.abc import Sequence
from dataclasses import dataclass
from functools import cached_property
from typing import Literal

import pyphen
import regex as re


@dataclass
class _Text:
    raw: str

    @cached_property
    def normalized(self):
        return normalize_uroman(self.raw)

    @cached_property
    def transcript(self):
        return self.normalized.split()

    @cached_property
    def transcript_for_alignment(self):
        """Transcript with parentheses stripped for forced alignment tokenizer."""
        return strip_parens(self.normalized).split()


@dataclass
class Lyrics(_Text):
    language: Literal["ja", "en"] = "ja"

    @cached_property
    def lines(self):
        return [Line(line, language=self.language) for line in filter(None, self.raw.splitlines())]


@dataclass
class Line(_Text):
    language: Literal["ja", "en"] = "ja"

    @cached_property
    def words(self):
        return [Word(word, language=self.language) for word in filter(None, self.transcript)]


@dataclass
class Word(_Text):
    language: Literal["ja", "en"] = "ja"

    @cached_property
    def syllables(self):
        return auto_split(self.normalized, self.language)


def strip_parens(text: str) -> str:
    """Strip parentheses from text for forced alignment."""
    return text.replace("(", "").replace(")", "")


def normalize_uroman(text: str):
    text = text.lower()
    text = text.replace("'", "'")
    # Preserve parentheses for backing vocals detection
    text = re.sub("([^a-z'\n ()])", " ", text)
    text = re.sub("\n[\n ]+", "\n", text)
    text = re.sub(" +", " ", text)
    return text.strip()


# https://docs.karaokes.moe/aegisub/auto-split.lua
AUTO_SPLIT_RE = re.compile(
    r"(?i)(?:(?<=[^sc])(?=h))|(?:(?<=[^kstnhfmrwpbdgzcj])(?=y))|(?:(?<=[^t])(?=s))|(?:(?=[ktnfmrwpbdgzcj]))|(?:(?<=[aeiou]|[^[:alnum:]])(?=[aeiou]))"
)

# Custom English syllable dictionary for common words pyphen misses
# Especially useful for singing/karaoke vocabulary
_CUSTOM_ENGLISH_SYLLABLES: dict[str, list[str]] = {
    # Common singing/music words
    "singing": ["sing", "ing"],
    "melody": ["mel", "o", "dy"],
    "karaoke": ["kar", "a", "o", "ke"],
    "rhythm": ["rhythm"],  # Actually single syllable
    "tonight": ["to", "night"],
    # Time-related words
    "everyday": ["ev", "ry", "day"],
    "someday": ["some", "day"],
    "sunday": ["sun", "day"],
    "monday": ["mon", "day"],
    "tuesday": ["tues", "day"],
    "wednesday": ["wednes", "day"],
    "thursday": ["thurs", "day"],
    "friday": ["fri", "day"],
    "saturday": ["sat", "ur", "day"],
    # Common contractions and informal words
    "gonna": ["gon", "na"],
    "wanna": ["wan", "na"],
    "gotta": ["got", "ta"],
    "kinda": ["kin", "da"],
    "sorta": ["sor", "ta"],
    "outta": ["out", "ta"],
    "coulda": ["could", "a"],
    "shoulda": ["should", "a"],
    "woulda": ["would", "a"],
    # Emotion/feeling words
    "loving": ["lov", "ing"],
    "feeling": ["feel", "ing"],
    "dreaming": ["dream", "ing"],
    "hoping": ["hop", "ing"],
    # Other common words
    "baby": ["ba", "by"],
    "maybe": ["may", "be"],
    "crazy": ["cra", "zy"],
    "lady": ["la", "dy"],
    "lately": ["late", "ly"],
    "lonely": ["lone", "ly"],
    "only": ["on", "ly"],
    "really": ["re", "al", "ly"],
    "yeah": ["yeah"],  # Single syllable
    "whoa": ["whoa"],  # Single syllable
    "woah": ["woah"],  # Single syllable
}

# English syllable splitter using pyphen with custom dictionary fallback
_ENGLISH_DICT = pyphen.Pyphen(lang="en_US")


def split_english(word: str) -> Sequence[str]:
    """Split English word into syllables using custom dictionary + pyphen.

    First checks custom dictionary for common words pyphen misses,
    then falls back to pyphen's dictionary-based splitting.
    """
    # Check custom dictionary first (for words pyphen commonly misses)
    if word in _CUSTOM_ENGLISH_SYLLABLES:
        return _CUSTOM_ENGLISH_SYLLABLES[word]

    # Fall back to pyphen
    result = _ENGLISH_DICT.inserted(word, hyphen="|")
    syllables: Sequence[str] = result.split("|") if result else [word]
    return syllables


def auto_split(word: str, language: Literal["ja", "en"] = "ja") -> Sequence[str]:
    """Split word into syllables based on language."""
    if language == "en":
        return split_english(word)
    else:  # Japanese (default)
        splitter_str, _ = AUTO_SPLIT_RE.subn("#@", word)
        syllables = re.split("#@", splitter_str, flags=re.MULTILINE)
        syllables = list(filter(None, syllables))
        return syllables
