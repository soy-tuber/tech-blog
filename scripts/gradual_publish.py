"""Gradually publish Zenn & Qiita articles — 5 per day to avoid rate limiting.

Zenn:  articles/*.md  → published: true/false
Qiita: public/*.md    → ignorePublish: false/true  (inverted logic)

Usage:
  python3 scripts/gradual_publish.py          # Publish next 5 pairs
  python3 scripts/gradual_publish.py --dry-run # Preview without changes
  python3 scripts/gradual_publish.py --reset   # Set ALL to unpublished
  python3 scripts/gradual_publish.py --status  # Show current counts
"""

import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
ZENN_DIR = REPO / "articles"
QIITA_DIR = REPO / "public"
BATCH_SIZE = 5


# ── Zenn helpers (published: true/false) ──

def zenn_is_published(path: Path) -> bool:
    m = re.search(r"^published:\s*(true|false)", path.read_text("utf-8"), re.MULTILINE)
    return m is not None and m.group(1) == "true"


def zenn_set_published(path: Path, value: bool):
    text = path.read_text("utf-8")
    path.write_text(
        re.sub(r"^published:\s*(true|false)",
               f"published: {'true' if value else 'false'}",
               text, count=1, flags=re.MULTILINE),
        "utf-8",
    )


def zenn_unpublished() -> list[Path]:
    return sorted(f for f in ZENN_DIR.glob("*.md") if not zenn_is_published(f))


def zenn_published() -> list[Path]:
    return sorted(f for f in ZENN_DIR.glob("*.md") if zenn_is_published(f))


# ── Qiita helpers (ignorePublish: true = skip, false = publish) ──

def qiita_is_published(path: Path) -> bool:
    """Published = ignorePublish: false (or already has an id)."""
    text = path.read_text("utf-8")
    m = re.search(r"^ignorePublish:\s*(true|false)", text, re.MULTILINE)
    return m is not None and m.group(1) == "false"


def qiita_set_published(path: Path, value: bool):
    text = path.read_text("utf-8")
    # ignorePublish logic is inverted: publish=true means ignorePublish=false
    ignore_val = "false" if value else "true"
    path.write_text(
        re.sub(r"^ignorePublish:\s*(true|false)",
               f"ignorePublish: {ignore_val}",
               text, count=1, flags=re.MULTILINE),
        "utf-8",
    )


def qiita_unpublished() -> list[Path]:
    """Articles with ignorePublish: true AND id: null (never published)."""
    result = []
    for f in sorted(QIITA_DIR.glob("*.md")):
        text = f.read_text("utf-8")
        ignore_m = re.search(r"^ignorePublish:\s*true", text, re.MULTILINE)
        id_m = re.search(r"^id:\s*null", text, re.MULTILINE)
        if ignore_m and id_m:
            result.append(f)
    return result


def qiita_published() -> list[Path]:
    return sorted(f for f in QIITA_DIR.glob("*.md") if qiita_is_published(f))


# ── Git ──

def git_push(files: list[Path], message: str):
    for f in files:
        subprocess.run(["git", "add", str(f)], check=True, cwd=REPO)
    subprocess.run(["git", "commit", "-m", message], check=True, cwd=REPO)
    subprocess.run(["git", "push", "origin", "main"], check=True, cwd=REPO)


# ── Main ──

def main():
    dry_run = "--dry-run" in sys.argv
    reset_mode = "--reset" in sys.argv
    status_mode = "--status" in sys.argv

    if status_mode:
        zp, zu = len(zenn_published()), len(zenn_unpublished())
        qp, qu = len(qiita_published()), len(qiita_unpublished())
        print(f"Zenn:  {zp} published, {zu} pending")
        print(f"Qiita: {qp} published, {qu} pending")
        total = max(zu, qu)
        if total > 0:
            days = (total + BATCH_SIZE - 1) // BATCH_SIZE
            print(f"Estimated: {days} more days to finish")
        return

    if reset_mode:
        changed = []
        for f in zenn_published():
            zenn_set_published(f, False)
            changed.append(f)
        for f in QIITA_DIR.glob("*.md"):
            text = f.read_text("utf-8")
            if re.search(r"^id:\s*null", text, re.MULTILINE):
                qiita_set_published(f, False)
                changed.append(f)
        print(f"Reset {len(changed)} files to unpublished")
        if changed and not dry_run:
            git_push(changed, f"reset {len(changed)} articles to draft")
        return

    # Normal batch publish
    z_batch = zenn_unpublished()[:BATCH_SIZE]
    q_batch = qiita_unpublished()[:BATCH_SIZE]

    if not z_batch and not q_batch:
        print("All articles are already published!")
        return

    changed = []

    if z_batch:
        print(f"\n[Zenn] Publishing {len(z_batch)} articles:")
        for f in z_batch:
            print(f"  {f.name}")
            if not dry_run:
                zenn_set_published(f, True)
            changed.append(f)

    if q_batch:
        print(f"\n[Qiita] Publishing {len(q_batch)} articles:")
        for f in q_batch:
            print(f"  {f.name}")
            if not dry_run:
                qiita_set_published(f, True)
            changed.append(f)

    if changed and not dry_run:
        git_push(changed, f"publish batch: {len(z_batch)} zenn + {len(q_batch)} qiita")
        print(f"\nDone! Pushed {len(changed)} files.")
        z_rem = len(zenn_unpublished())
        q_rem = len(qiita_unpublished())
        remaining = max(z_rem, q_rem)
        if remaining > 0:
            days = (remaining + BATCH_SIZE - 1) // BATCH_SIZE
            print(f"Remaining: Zenn={z_rem} Qiita={q_rem} ({days} more days)")
    elif dry_run:
        print("\n[dry-run] No changes made.")


if __name__ == "__main__":
    main()
