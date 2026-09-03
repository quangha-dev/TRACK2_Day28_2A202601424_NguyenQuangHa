"""Package explicit lab deliverables, excluding runtime state and stale reports.

File presence is reported separately from live verification. Missing GPU files
stay UNVERIFIED when --without-gpu is used; no evidence is fabricated.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
from datetime import UTC, datetime
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

import yaml

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--without-gpu", action="store_true")
    parser.add_argument("--without-langsmith", action="store_true")
    parser.add_argument("--zip", type=Path, dest="zip_path")
    args = parser.parse_args()
    source = ROOT / "evidence"
    submission = ROOT / "submission"
    target = submission / "evidence"
    target.mkdir(parents=True, exist_ok=True)
    matrix = yaml.safe_load((ROOT / "contracts/integration-matrix.yaml").read_text("utf-8"))
    records = []
    for point in matrix["points"]:
        for relative in re.findall(r"evidence/[\w-]+\.json", point["demo_evidence"]):
            path = source / Path(relative).name
            if path.is_file():
                payload = json.loads(path.read_text("utf-8"))
                present = bool(payload)
            else:
                present = False
            gated = args.without_gpu and point["id"] in {"IP07", "IP10"}
            record = {
                "point": point["id"], "path": relative,
                "file_present": present,
                "status": "PRESENT" if present else "MISSING",
            }
            if gated:
                record["status"] = "UNVERIFIED"
                record["reason"] = (
                    "No GPU endpoint; full serving trace unavailable. "
                    "Local trace evidence, if present, is partial."
                )
            if present:
                shutil.copyfile(path, target / path.name)
                record["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
            records.append(record)
    extra_evidence = [path for path in source.glob("j*.json") if path.is_file()]
    for path in extra_evidence:
        json.loads(path.read_text("utf-8"))
        shutil.copyfile(path, target / path.name)

    supporting = [
        "ANSWERS.md", "docs/architecture-ownership.md", "submission/README.md",
        "submission/integration-report.json", "submission/failure-recovery-record.md",
        "submission/load-profile-analysis.md", "submission/gitops-validation-and-rollback.md",
        "submission/logs/fast-suite.txt", "submission/logs/integration-non-gpu.txt",
        "submission/logs/matrix.txt", "submission/logs/gitops-validation.txt",
    ]
    if not args.without_gpu:
        supporting.append("submission/vllm-local.md")
    missing = [r["path"] for r in records if r["status"] == "MISSING"]
    missing += [name for name in supporting if not (ROOT / name).is_file()]
    manifest = {
        "created_at_utc": datetime.now(UTC).isoformat(),
        "repository": "https://github.com/quangha-dev/TRACK2_Day28_2A202601424_NguyenQuangHa",
        "files_complete_excluding_declared_gates": not missing,
        "live_verification": "See original test logs and reports; file presence is not a pass.",
        "declared_gates": {
            **({"gpu": "UNVERIFIED"} if args.without_gpu else {}),
            **({"langsmith": "UNVERIFIED"}
               if args.without_gpu or args.without_langsmith else {}),
        },
        "required_ip_files": records, "missing": missing,
    }
    manifest_path = submission / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", "utf-8")
    if args.zip_path:
        archive_path = args.zip_path.resolve()
        archive_path.parent.mkdir(parents=True, exist_ok=True)
        paths = [ROOT / name for name in supporting]
        paths += [target / Path(r["path"]).name for r in records if r["file_present"]]
        paths += [target / path.name for path in extra_evidence]
        paths += list((submission / "logs").glob("*.txt"))
        paths += list(submission.glob("load-*.json"))
        paths += list((submission / "screenshots").glob("*.png"))
        paths += [manifest_path]
        with ZipFile(archive_path, "w", ZIP_DEFLATED) as archive:
            for path in sorted(set(paths)):
                if path.is_file():
                    archive.write(path, path.relative_to(ROOT).as_posix())
        print(f"Archive: {archive_path.name}")
    print(json.dumps({
        "missing": missing,
        "present_ip_files": sum(r["file_present"] for r in records),
    }, indent=2))
    if missing:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
