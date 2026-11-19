#!/usr/bin/env bash
# SPDX-License-Identifier: Apache-2.0
set -euo pipefail
umask 077
SOURCE=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
BUILD=${1:?Pass a disposable build directory outside source Git}
SDK=${ANDROID_SDK_ROOT:-"$HOME/Android/Sdk"}
BT="$SDK/build-tools/36.0.0"
ANDROID_JAR="$SDK/platforms/android-36/android.jar"
mkdir -p "$BUILD/classes" "$BUILD/dex"
BUILD=$(cd -- "$BUILD" && pwd)
javac --release 8 -cp "$ANDROID_JAR" -d "$BUILD/classes" \
    "$SOURCE/src/org/lieppos/gnssprobe/ProbeActivity.java"
mapfile -d '' CLASSES < <(find "$BUILD/classes" -name '*.class' -print0)
"$BT/d8" --min-api 31 --lib "$ANDROID_JAR" --output "$BUILD/dex" "${CLASSES[@]}"
"$BT/aapt2" link -I "$ANDROID_JAR" --manifest "$SOURCE/AndroidManifest.xml" \
    -o "$BUILD/base.apk"
cp "$BUILD/base.apk" "$BUILD/unsigned.apk"
zip -q -j "$BUILD/unsigned.apk" "$BUILD/dex/classes.dex"
"$BT/zipalign" -f 4 "$BUILD/unsigned.apk" "$BUILD/aligned.apk"
if [[ ! -f "$BUILD/local-signing.jks" ]]; then
    keytool -genkeypair -keystore "$BUILD/local-signing.jks" \
        -storepass android -keypass android -alias probe -keyalg RSA -keysize 2048 \
        -validity 30 -dname 'CN=Local GNSS Diagnostic' >/dev/null 2>&1
fi
"$BT/apksigner" sign --ks "$BUILD/local-signing.jks" --ks-key-alias probe \
    --ks-pass pass:android --key-pass pass:android \
    --out "$BUILD/gnss-probe.apk" "$BUILD/aligned.apk"
"$BT/apksigner" verify "$BUILD/gnss-probe.apk"
printf 'Built and verified %s\n' "$BUILD/gnss-probe.apk"
