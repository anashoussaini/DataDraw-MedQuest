import json
import re
import shutil
from collections import defaultdict
from pathlib import Path


class MedicalDataCleaner:
    """
    Cleans JSON exam folders from any source directory into a chosen output directory.
    Never modifies the source files.
    """

    def __init__(self):
        self.smart_map = {
            "\u2019": "'",
            "\u2018": "'",
            "\u201c": '"',
            "\u201d": '"',
            "\u2026": "...",
            "\u2013": "-",
            "\u2014": "-",
        }

        self.p = {
            "split_file": re.compile(r"^(.*?)(?:_\d+)?(?:\s.*)?\.json$"),
            "q_prefix": re.compile(r"^\s*(?:Question\s*\d+|Q\.?\s*\d+|\d+[\.:)])\s*", re.I),
            "o_prefix": re.compile(r"^\s*[A-E][\.:)]\s*", re.I),
            "trailing": re.compile(r"[\.:;?…]+\s*$"),
            "multi_sp": re.compile(r"\s{2,}"),
            "invalid": re.compile(
                r"""[^\wÀ-ÖØ-öø-ÿ\s,;:'"\.\!\?\-\(\)\[\]°²³±≤≥→×€£%&@#/\\«»]""",
                re.UNICODE,
            ),
        }

        self.reset_logs()

    def reset_logs(self):
        self.invalid_years = []
        self.duplicate_answers = []
        self.merged_counts = {}
        self.stripped_chars = defaultdict(int)

    def clean_text(self, txt: str, is_q: bool) -> str:
        s = txt.strip()
        for old, new in self.smart_map.items():
            s = s.replace(old, new)
        s = self.p["q_prefix"].sub("", s) if is_q else self.p["o_prefix"].sub("", s)
        for ch in self.p["invalid"].findall(s):
            self.stripped_chars[ch] += 1
        s = self.p["invalid"].sub("", s)
        s = self.p["trailing"].sub("", s)
        s = self.p["multi_sp"].sub(" ", s).strip()
        if s and s[0].isalpha() and s[0].islower():
            s = s[0].upper() + s[1:]
        return s

    def read_json_file(self, file_path: Path):
        raw = file_path.read_bytes()
        attempted_encodings = []

        for encoding in ("utf-8", "utf-8-sig", "cp1252", "latin-1"):
            attempted_encodings.append(encoding)
            try:
                return json.loads(raw.decode(encoding))
            except UnicodeDecodeError:
                continue
            except json.JSONDecodeError:
                continue

        tried = ", ".join(attempted_encodings)
        raise ValueError(
            f"Could not decode JSON file {file_path.name} using encodings: {tried}"
        )

    def process_directory(
        self,
        root_dir: str | Path,
        output_dir: str | Path | None = None,
        reports_dir: str | Path | None = None,
        clear_output: bool = True,
    ):
        self.reset_logs()

        src = Path(root_dir)
        if not src.exists():
            raise FileNotFoundError(f"Source directory does not exist: {src}")

        dst = Path(output_dir) if output_dir is not None else Path.cwd() / "Medquestions_fixed"
        reports_root = Path(reports_dir) if reports_dir is not None else Path.cwd()

        if clear_output and dst.exists():
            shutil.rmtree(dst)
        dst.mkdir(parents=True, exist_ok=True)
        reports_root.mkdir(parents=True, exist_ok=True)

        groups = defaultdict(list)
        for file_path in src.rglob("*.json"):
            rel = file_path.relative_to(src)
            match = self.p["split_file"].match(rel.name)
            base = (match.group(1) if match else rel.stem) + ".json"
            groups[rel.parent / base].append(file_path)

        cleaned_file_count = 0
        cleaned_question_count = 0

        for dest_rel, files in groups.items():
            files = sorted(files, key=lambda path: (path.name != dest_rel.name, path.name))
            merged = None

            for file_path in files:
                data = self.read_json_file(file_path)
                if merged is None:
                    metadata = data.get("metadata", {}) or {}
                    year = str(metadata.get("exam_year", "")).strip()
                    if year.upper() not in ("UNK", "UNKNOWN") and (
                        not year.isdigit() or not 1900 < int(year) < 2100
                    ):
                        self.invalid_years.append(
                            {"file": str(file_path.relative_to(src)), "year": year}
                        )
                    merged = {"metadata": metadata, "content": {"questions": []}}
                merged["content"]["questions"].extend(data["content"]["questions"])

            if merged is None:
                continue

            if len(files) > 1:
                self.merged_counts[str(dest_rel)] = len(files)

            exam_var = dest_rel.stem.split("_")[-1]
            if exam_var.isdigit():
                merged["metadata"]["exam_variable"] = int(exam_var)

            for idx, question in enumerate(merged["content"]["questions"]):
                question["question"] = self.clean_text(question.get("question", ""), True)
                options = question.get("options", {})
                for key, value in options.items():
                    options[key] = self.clean_text(value, False)

                original_answers = question.get("correct_answers", [])
                seen, unique_answers, duplicates = set(), [], []
                for answer in original_answers:
                    if answer in seen:
                        duplicates.append(answer)
                    else:
                        seen.add(answer)
                        unique_answers.append(answer)
                if duplicates:
                    self.duplicate_answers.append(
                        {
                            "file": str(dest_rel),
                            "question_index": idx,
                            "original": original_answers,
                            "duplicates": duplicates,
                            "final": unique_answers,
                        }
                    )
                question["correct_answers"] = unique_answers

            output_path = dst / dest_rel
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(
                json.dumps(merged, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            cleaned_file_count += 1
            cleaned_question_count += len(merged["content"]["questions"])

        invalid_years_text = "\n".join(
            f"{entry['file']} | year: {entry['year']}" for entry in self.invalid_years
        )
        duplicate_answers_text = "\n".join(
            f"{entry['file']} q#{entry['question_index']} "
            f"orig={entry['original']} dups={entry['duplicates']} "
            f"final={entry['final']}"
            for entry in self.duplicate_answers
        )
        stripped_chars_text = "\n".join(
            f"{char!r}: {count}"
            for char, count in sorted(self.stripped_chars.items(), key=lambda item: -item[1])
        )

        (reports_root / "invalid_years.txt").write_text(invalid_years_text, encoding="utf-8")
        (reports_root / "duplicate_answers.txt").write_text(
            duplicate_answers_text, encoding="utf-8"
        )
        (reports_root / "stripped_chars.txt").write_text(
            stripped_chars_text, encoding="utf-8"
        )

        report_lines = ["Merge/Clean Summary", "=" * 30]
        for filename, count in self.merged_counts.items():
            report_lines.append(f"{filename} → merged {count} files")
        report_lines.extend(
            [
                f"Invalid years: {len(self.invalid_years)}",
                f"Duplicate-answer fixes: {len(self.duplicate_answers)}",
                f"Stripped weird chars: {len(self.stripped_chars)}",
            ]
        )
        processing_report_text = "\n".join(report_lines)
        (reports_root / "processing_report.txt").write_text(
            processing_report_text,
            encoding="utf-8",
        )

        return {
            "source_dir": str(src),
            "output_dir": str(dst),
            "reports_dir": str(reports_root),
            "input_json_files": sum(len(files) for files in groups.values()),
            "cleaned_json_files": cleaned_file_count,
            "cleaned_questions": cleaned_question_count,
            "merged_counts": dict(self.merged_counts),
            "invalid_years": list(self.invalid_years),
            "duplicate_answers": list(self.duplicate_answers),
            "stripped_chars": dict(self.stripped_chars),
            "reports": {
                "processing_report.txt": processing_report_text,
                "invalid_years.txt": invalid_years_text,
                "duplicate_answers.txt": duplicate_answers_text,
                "stripped_chars.txt": stripped_chars_text,
            },
        }
