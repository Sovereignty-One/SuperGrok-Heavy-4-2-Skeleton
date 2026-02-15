# fullscan_cli.py
# Command-line utility for multi-source syllabic scan and batch verification with logging, rotation, checksums, extra metrics, and cluster grouping

import re
import argparse
import json
import gzip
from typing import List, Dict
from threading import RLock
from pathlib import Path
from datetime import datetime, timezone
import os
import shutil


class FullScanEngine:
    def __init__(self):
        self.lock = RLock()
        self.sources: Dict[str, List[str]] = {}
        self.context_maps: Dict[str, Dict[str, int]] = {}
        self.miss_counts: Dict[str, int] = {}
        self.clusters: Dict[str, List[List[str]]] = {}

    def ingest(self, source: str, raw: str):
        if source not in self.sources:
            self.sources[source] = []
            self.context_maps[source] = {}
            self.miss_counts[source] = 0
            self.clusters[source] = []

        lines = raw.strip().split('\n')
        for line in lines:
            tokens = self.tokenize_syllabic(line)
            start = len(self.sources[source])
            self.sources[source].extend(tokens)

            cluster = []
            for i, tk in enumerate(tokens):
                cluster.append(tk)
                if tk not in self.context_maps[source]:
                    self.context_maps[source][tk] = start + i
            if cluster:
                self.clusters[source].append(cluster)

    def tokenize_syllabic(self, text: str) -> List[str]:
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
        vowels = 'aeiouyAEIOUY'
        if not word:
            return []

        out = []
        syl = ''
        for char in word:
            syl += char
            if char in vowels and syl:
                out.append(syl)
                syl = ''
        if syl:
            out.append(syl)
        return out

    def scan_complete(self, source: str) -> bool:
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

    def verify_all(self) -> Dict[str, bool]:
        return {source: self.scan_complete(source) for source in self.sources.keys()}

    def dump(self, source: str) -> str:
        if source not in self.sources or not self.sources[source]:
            return ""
        full_text = self.sources[source]
        first = full_text[0]
        mid = full_text[len(full_text) // 2]
        last = full_text[-1]
        return " ".join([first, mid, last])

    def token_count(self, source: str) -> int:
        return len(self.sources.get(source, []))

    def avg_syllable_length(self, source: str) -> float:
        tokens = self.sources.get(source, [])
        if not tokens:
            return 0.0
        total_len = sum(len(t) for t in tokens)
        return total_len / len(tokens)

    def cluster_count(self, source: str) -> int:
        return len(self.clusters.get(source, []))

    def cluster_summary(self, source: str) -> List[str]:
        clusters = self.clusters.get(source, [])
        return [" ".join(c[:3]) for c in clusters[:5]]


def rotate_log_file(log_path: str, max_size: int = 1024 * 1024, compress: bool = True) -> str:
    if os.path.isfile(log_path) and os.path.getsize(log_path) > max_size:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        rotated_path = f"{log_path}.{timestamp}.bak"
        os.rename(log_path, rotated_path)
        if compress:
            with open(rotated_path, 'rb') as f_in, gzip.open(rotated_path + '.gz', 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
            os.remove(rotated_path)
    return log_path


def main():
    parser = argparse.ArgumentParser(description="Multi-source syllabic scanner and verifier with clusters.")
    parser.add_argument("files", nargs="+", help="Text files to scan and verify.")
    parser.add_argument("--dump", action="store_true", help="Show first/mid/last tokens for each file.")
    parser.add_argument("--json", action="store_true", help="Output results in JSON format.")
    parser.add_argument("--fail-log", type=str, help="Path to a log file for verification results.")
    parser.add_argument("--append", action="store_true", help="Append to the log instead of overwriting.")
    parser.add_argument("--max-log-size", type=int, default=1024*1024, help="Max size in bytes before log rotation.")
    parser.add_argument("--no-compress", action="store_true", help="Do not compress rotated logs.")
    parser.add_argument("--metrics", action="store_true", help="Include token counts and average syllable length in the log.")
    parser.add_argument("--clusters", action="store_true", help="Include cluster summaries in JSON/log output.")

    args = parser.parse_args()

    engine = FullScanEngine()

    for file_path in args.files:
        path = Path(file_path)
        if not path.is_file():
            print(f"Skipping '{file_path}' — not a file.")
            continue

        with path.open("r", encoding="utf-8") as f:
            content = f.read()
            engine.ingest(path.name, content)

    results = engine.verify_all()

    # Group sources by cluster count first
    cluster_groups: Dict[int, List[str]] = {}
    if args.clusters:
        for src in engine.sources:
            cnt = engine.cluster_count(src)
            cluster_groups.setdefault(cnt, []).append(src)

    # Logging
    if args.fail_log:
        active_log = rotate_log_file(args.fail_log, args.max_log_size, compress=not args.no_compress)
        mode = "a" if args.append else "w"
        total_missing = sum(engine.miss_counts.values())
        total_failures = sum(1 for complete in results.values() if not complete)

        with open(active_log, mode, encoding="utf-8") as log_file:
            log_file.write("=== Cluster Groups by Count ===\n")
            for cnt in sorted(cluster_groups):
                log_file.write(f"{cnt} clusters: {', '.join(cluster_groups[cnt])}\n")

            log_file.write("=== Verification Results (Clusters First) ===\n")
            for src, complete in results.items():
                timestamp = datetime.now(timezone.utc).isoformat()
                clusters_cnt = engine.cluster_count(src)
                cluster_str = f"Clusters: {clusters_cnt} | Preview: {engine.cluster_summary(src)}" if args.clusters else ""
                first_tok = engine.sources[src][0]
                last_tok = engine.sources[src][-1]
                checksum = engine.dump(src)
                tokens = engine.token_count(src)
                avg_len = engine.avg_syllable_length(src)
                metrics_str = f" | Tokens: {tokens} | AvgLen: {avg_len:.2f}" if args.metrics else ""
                status_str = "OK" if complete else f"FAIL ({engine.miss_counts[src]} missing)"

                log_file.write(f"[{timestamp}] {src} | {cluster_str} | Status: {status_str} | First: {first_tok} | Last: {last_tok} | Checksum: {checksum}{metrics_str}\n")

            log_file.write(f"Summary: {total_failures} failures, {total_missing} total missing syllables\n")

    if args.json:
        output = {
            "clusters": {src: engine.clusters[src] for src in engine.sources} if args.clusters else None,
            "results": {
                src: {
                    "complete": complete,
                    "missing": engine.miss_counts[src],
                    "checksum": engine.dump(src) if args.dump else None,
                    "tokens": engine.token_count(src) if args.metrics else None,
                    "avg_syllable_length": engine.avg_syllable_length(src) if args.metrics else None
                } for src, complete in results.items()
            }
        }
        print(json.dumps(output, indent=2))
    else:
        for src, complete in results.items():
            if args.clusters:
                print(f"{src} | Clusters: {engine.cluster_count(src)} | Preview: {engine.cluster_summary(src)}")
            status = "FULL READ CONFIRMED" if complete else f"Integrity fail ({engine.miss_counts[src]} missing)"
            print(f"  Status: {status}")
            if args.dump:
                print("  Checksum:", engine.dump(src))
            if args.metrics:
                print(f"  Tokens: {engine.token_count(src)} | Avg syllable length: {engine.avg_syllable_length(src):.2f}")


if __name__ == "__main__":
    main()



import argparse
import json
import re
import gzip
import os
import shutil
from typing import List, Dict
from threading import RLock
from pathlib import Path
from datetime import datetime, timezone


class FullScanEngine:
    def __init__(self, syllable_mode: bool = False):
        self.lock = RLock()
        self.syllable_mode = syllable_mode
        self.sources: Dict[str, List[str]] = {}
        self.context_maps: Dict[str, Dict[str, int]] = {}
        self.miss_counts: Dict[str, int] = {}
        self.clusters: Dict[str, List[List[str]]] = {}

    def ingest(self, source: str, raw: str):
        if source not in self.sources:
            self.sources[source] = []
            self.context_maps[source] = {}
            self.miss_counts[source] = 0
            self.clusters[source] = []

        lines = raw.strip().split('\n')
        for line in lines:
            tokens = self.tokenize_syllabic(line)
            start = len(self.sources[source])
            self.sources[source].extend(tokens)
            cluster = []
            for i, tk in enumerate(tokens):
                cluster.append(tk)
                if tk not in self.context_maps[source]:
                    self.context_maps[source][tk] = start + i
            if cluster:
                self.clusters[source].append(cluster)

    def syllabify(self, word: str) -> List[str]:
        return re.findall(r"[^aeiou]*[aeiou]+[^aeiou]*", word, re.I)

    def tokenize_syllabic(self, text: str) -> List[str]:
        if self.syllable_mode:
            words = re.findall(r"[\w']+", text)
            out = []
            for w in words:
                syls = self.syllabify(w)
                out.extend(syls)
            return out
        else:
            words = re.findall(r"[\w']+[.,!?;:]*", text)
            out = []
            for w in words:
                m = re.match(r"([\w']+)([.,!?;:]*)", w)
                if not m:
                    continue
                base, punc = m.groups()
                out.append(base + (punc or ''))
            return out

    def scan_complete(self, source: str) -> bool:
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

    def verify_all(self) -> Dict[str, bool]:
        return {source: self.scan_complete(source) for source in self.sources.keys()}

    def dump(self, source: str) -> str:
        if source not in self.sources or not self.sources[source]:
            return ""
        full_text = self.sources[source]
        first = full_text[0]
        mid = full_text[len(full_text) // 2]
        last = full_text[-1]
        return " ".join([first, mid, last])

    def token_count(self, source: str) -> int:
        return len(self.sources.get(source, []))

    def avg_syllable_length(self, source: str) -> float:
        tokens = self.sources.get(source, [])
        if not tokens:
            return 0.0
        total_len = sum(len(t) for t in tokens)
        return total_len / len(tokens)

    def cluster_count(self, source: str) -> int:
        return len(self.clusters.get(source, []))

    def cluster_summary(self, source: str) -> List[str]:
        clusters = self.clusters.get(source, [])
        return [" ".join(c[:3]) for c in clusters[:5]]


def rotate_log_file(log_path: str, max_size: int = 1024*1024, compress: bool = True) -> str:
    if os.path.isfile(log_path) and os.path.getsize(log_path) > max_size:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        rotated_path = f"{log_path}.{timestamp}.bak"
        os.rename(log_path, rotated_path)
        if compress:
            with open(rotated_path, 'rb') as f_in, gzip.open(rotated_path + '.gz', 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
            os.remove(rotated_path)
    return log_path


def parse_cli():
    parser = argparse.ArgumentParser(description="Multi-source syllabic scanner and verifier with clusters.")
    parser.add_argument("files", nargs="+", help="Text files to scan and verify.")
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument("--syllable-level", action="store_true")
    mode_group.add_argument("--word-level", action="store_true")
    parser.add_argument("--dump", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--fail-log", type=str)
    parser.add_argument("--append", action="store_true")
    parser.add_argument("--max-log-size", type=int, default=1024*1024)
    parser.add_argument("--no-compress", action="store_true")
    parser.add_argument("--metrics", action="store_true")
    parser.add_argument("--clusters", action="store_true")
    return parser.parse_args()


def init_engine(args) -> FullScanEngine:
    syllable_mode = args.syllable_level
    if args.word_level:
        syllable_mode = False
    return FullScanEngine(syllable_mode=syllable_mode)


def generate_json_output(engine: FullScanEngine, results: Dict[str, bool], args) -> str:
    return json.dumps({
        "tokenization_mode": "syllable" if engine.syllable_mode else "word",
        "clusters": {src: engine.clusters[src] for src in engine.sources} if args.clusters else None,
        "results": {
            src: {
                "complete": complete,
                "missing": engine.miss_counts[src],
                "checksum": engine.dump(src) if args.dump else None,
                "tokens": engine.token_count(src) if args.metrics else None,
                "avg_syllable_length": engine.avg_syllable_length(src) if args.metrics else None
            } for src, complete in results.items()
        }
    }, indent=2)


def write_log(engine: FullScanEngine, results: Dict[str, bool], cluster_groups: Dict[int, List[str]], args):
    if not args.fail_log:
        return
    active_log = rotate_log_file(args.fail_log, args.max_log_size, compress=not args.no_compress)
    mode = "a" if args.append else "w"
    token_mode = "Syllable-Level" if engine.syllable_mode else "Word-Level"
    total_missing = sum(engine.miss_counts.values())
    total_failures = sum(1 for complete in results.values() if not complete)

    with open(active_log, mode, encoding="utf-8") as log_file:
        log_file.write(f"=== Tokenization Mode: {token_mode} ===\n")
        log_file.write(f"Summary: {total_failures} failures, {total_missing} total missing syllables\n")
        log_file.write("=== Cluster Groups by Count ===\n")
        for cnt in sorted(cluster_groups):
            log_file.write(f"{cnt} clusters: {', '.join(cluster_groups[cnt])}\n")
        log_file.write("=== Verification Results (Clusters First) ===\n")
        for src, complete in results.items():
            timestamp = datetime.now(timezone.utc).isoformat()
            clusters_cnt = engine.cluster_count(src)
            cluster_str = f"Clusters: {clusters_cnt} | Preview: {engine.cluster_summary(src)}" if args.clusters else ""
            first_tok = engine.sources[src][0]
            last_tok = engine.sources[src][-1]
            checksum = engine.dump(src)
            tokens = engine.token_count(src)
            avg_len = engine.avg_syllable_length(src)
            metrics_str = f" | Tokens: {tokens} | AvgLen: {avg_len:.2f}" if args.metrics else ""
            status_str = "OK" if complete else f"FAIL ({engine.miss_counts[src]} missing)"
            log_file.write(f"[{timestamp}] {src} | {cluster_str} | Status: {status_str} | First: {first_tok} | Last: {last_tok} | Checksum: {checksum}{metrics_str}\n")


def main():
    args = parse_cli()
    engine = init_engine(args)

    for file_path in args.files:
        path = Path(file_path)
        if not path.is_file():
            print(f"Skipping '{file_path}' — not a file.")
            continue
        with path.open("r", encoding="utf-8") as f:
            engine.ingest(path.name, f.read())

    results = engine.verify_all()
    cluster_groups: Dict[int, List[str]] = {}
    if args.clusters:
        for src in engine.sources:
            cnt = engine.cluster_count(src)
            cluster_groups.setdefault(cnt, []).append(src)

    write_log(engine, results, cluster_groups, args)

    if args.json:
        print(generate_json_output(engine, results, args))
    else:
        for src, complete in results.items():
            if args.clusters:
                print(f"{src} | Clusters: {engine.cluster_count(src)} | Preview: {engine.cluster_summary(src)}")
            status = "FULL READ CONFIRMED" if complete else f"Integrity fail ({engine.miss_counts[src]} missing)"
            print(f"  Status: {status}")
            if args.dump:
                print("  Checksum:", engine.dump(src))
            if args.metrics:
                print(f"  Tokens: {engine.token_count(src)} | Avg syllable length: {engine.avg_syllable_length(src):.2f}")


if __name__ == "__main__":
    main()

This version:
	1.	Separates CLI parsing (parse_cli), engine instantiation (init_engine), and reporting (write_log and generate_json_output).
	2.	Collects JSON output generation in generate_json_output.
	3.	Logging writes the summary first, then cluster groups, followed by detailed per-source results.
