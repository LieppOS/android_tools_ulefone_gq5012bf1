#!/usr/bin/env bash
# Build encbench.dex with the Lineage tree's prebuilt JDK, android.jar and d8.
# Output goes outside Git (default /tmp/lieppos-builds/encoder-bench).
# Host work is bound to NUMA nodes 0 and 1 (owner rule; nodes 2 and 3 forbidden).
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TREE="${TREE:-$HOME/LieppOS-workspace/lineage-24.0}"
OUT="${OUT:-/tmp/lieppos-builds/encoder-bench}"
CPUS="$(cat /sys/devices/system/node/node0/cpulist),$(cat /sys/devices/system/node/node1/cpulist)"
run() { numactl --physcpubind="$CPUS" --membind=0 -- "$@"; }

JDK="$TREE/prebuilts/jdk/jdk21/linux-x86"
ANDROID_JAR="$TREE/prebuilts/sdk/current/public/android.jar"
R8_JAR="$TREE/prebuilts/r8/r8.jar"
rm -rf "$OUT/classes"; mkdir -p "$OUT/classes"
run "$JDK/bin/javac" --release 11 -nowarn -classpath "$ANDROID_JAR" -d "$OUT/classes" \
    $(find "$HERE/src" -name '*.java')
run "$JDK/bin/java" -cp "$R8_JAR" com.android.tools.r8.D8 --min-api 34 --lib "$ANDROID_JAR" --output "$OUT" \
    $(find "$OUT/classes" -name '*.class')
mv "$OUT/classes.dex" "$OUT/encbench.dex"
echo "$OUT/encbench.dex"
