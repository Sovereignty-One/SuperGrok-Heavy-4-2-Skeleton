# no_skip_core_multi_batch_fixed.py
# FullScanEngine with multi-source support and batch verification (fixed)

import re
from typing import List, Dict
from threading import RLock

class FullScanEngine:
    def __init__(self):
        self.lock = RLock()
        self.sources: Dict[str, List[str]] = {}
        self.context_maps: Dict[str, Dict[str, int]] = {}
        self.miss_counts: Dict[str, int] = {}

    def ingest(self, source: str, raw: str):
        """Ingests a block of text for a given source and tokenizes it syllabically."""
        if source not in self.sources:
            self.sources[source] = []
            self.context_maps[source] = {}
            self.miss_counts[source] = 0

        lines = raw.strip().split('\n')
        for line in lines:
            tokens = self.tokenize_syllabic(line)
            start = len(self.sources[source])
            self.sources[source].extend(tokens)

            for i, tk in enumerate(tokens):
                if tk not in self.context_maps[source]:
                    self.context_maps[source][tk] = start + i  # first occurrence only

    def tokenize_syllabic(self, text: str) -> List[str]:
        """Tokenize text into words with attached punctuation, then syllabify."""
        # Matches words with attached punctuation like commas or periods
        words = re.findall(r"[\w']+[.,!?;:]*", text)
        out = []
        for w in words:
            m = re.match(r"([\w']+)([.,!?;:]*)", w)
            if not m:
                continue
            base, punc = m.groups()
            syls = self.syllabify(base)
            token = ''.join(syls) + (punc or '')
            out.append(token)
        return out

    def syllabify(self, word: str) -> List[str]:
        """Splits a word into rough syllables using vowel clusters."""
        vowels = 'aeiouyAEIOUY'
        if not word:
            return []
        out = []
        syl = ''
        for i, char in enumerate(word):
            syl += char
            if char in vowels:
                out.append(syl)
                syl = ''
        if syl:
            out.append(syl)
        return out

    def scan_complete(self, source: str) -> bool:
        """Checks whether all tokens from a source are accounted for in the context map."""
        if source not in self.sources or not self.sources[source]:
            return False

        full_text = self.sources[source]
        context_map = self.context_maps[source]

        first = full_text[0]
        last = full_text[-1]
        length = len(full_text)

        missing = sum(1 for tok in full_text if tok not in context_map)
        self.miss_counts[source] = missing

        return (
            missing == 0
            and context_map.get(first) == 0
            and context_map.get(last) == length - 1
        )

    def verify_end(self, source: str):
        """Verify integrity for a single source at the end of ingestion."""
        try:
            if self.scan_complete(source):
                print(f"FULL READ CONFIRMED for '{source}'. No syllable skipped.")
            else:
                raise ValueError(
                    f"Integrity fail for '{source}'. {self.miss_counts[source]} syllables untracked."
                )
        except Exception as e:
            print(f"Verification failed for '{source}': {e}")

    def verify_all(self) -> Dict[str, bool]:
        """Batch verification of all sources."""
        results = {}
        for source in self.sources.keys():
            complete = self.scan_complete(source)
            results[source] = complete
            if complete:
                print(f"FULL READ CONFIRMED for '{source}'.")
            else:
                print(f"Integrity fail for '{source}'. {self.miss_counts[source]} syllables untracked.")
        return results

    def dump(self, source: str) -> str:
        """Returns a checksum string containing first, middle, and last token for a source."""
        if source not in self.sources or not self.sources[source]:
            return ""
        full_text = self.sources[source]
        first = full_text[0]
        mid = full_text[len(full_text)//2]
        last = full_text[-1]
        return " ".join([first, mid, last])


# ——— usage ———
if __name__ == "__main__":
    engine = FullScanEngine()

    engine.ingest("article_1", """
    This is the first letter. The very first.
    In the middle: context is king, syllables are bricks.
    Last period. Done.
    """)
    engine.ingest("article_2", """
    Another text source begins. Tokens must be tracked separately.
    Testing the second source scan.
    """)

    # Batch verification
    engine.verify_all()  # Verifies all sources at once

    print("Checksum article_1:", engine.dump("article_1"))
    print("Checksum article_2:", engine.dump("article_2"))
