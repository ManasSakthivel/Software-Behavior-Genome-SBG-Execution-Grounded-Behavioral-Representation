#!/usr/bin/env bash
# WP-D / D2: re-hash exactly the files listed in PKG/logs/sbg_tree_sha256_BEFORE.txt (read-only) and diff.
PKG=/Users/manassakthivel/Desktop/SBG-FINALREVIEW/IEEE_ACCESS_PRE_SUBMISSION
OUT=$PKG/WP_D_EXTERNAL_VALIDATION/raw/WPD-D2_repro/integrity
mkdir -p "$OUT"; cd /Users/manassakthivel/Desktop/SBG-FINALREVIEW/SBG
awk '{ $1=""; sub(/^ +/,""); print }' "$PKG/logs/sbg_tree_sha256_BEFORE.txt" | tr '\n' '\0' | xargs -0 shasum -a 256 2>"$OUT/sbg_AFTER_D2.stderr" | sed 's#  \./#  ./#' > "$OUT/sbg_tree_sha256_AFTER_D2.txt"
sort -k2 "$PKG/logs/sbg_tree_sha256_BEFORE.txt" > "$OUT/before.sorted"; sort -k2 "$OUT/sbg_tree_sha256_AFTER_D2.txt" > "$OUT/after.sorted"
diff "$OUT/before.sorted" "$OUT/after.sorted" > "$OUT/diff.txt"; echo "diff rc=$? lines=$(wc -l < $OUT/diff.txt) before=$(wc -l < $OUT/before.sorted) after=$(wc -l < $OUT/after.sorted)" | tee "$OUT/summary.txt"
