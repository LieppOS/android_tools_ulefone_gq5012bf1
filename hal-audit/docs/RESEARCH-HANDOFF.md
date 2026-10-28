# C51D — vibrator Android integration research handoff

**NOT YET MERGED.** Destination: `research/ulefone-gq5012bf1`
(`LieppOS/LieppOS-ulefone-gq5012bf1-research`), owned by DeepSeek during C55.
That checkout, device/vendor/manifest repositories, kernel repositories and the
shared Android platform/output were read only. No push, phone, ADB/fastboot,
flash, reboot or activation. Complete C51C kernel-timeout handoff (toolchain,
module hashes, CRC/KCFI receipts, ELF-tool correction) is unchanged at tools
commit `b2e292aa4416198a3d4885f559ab244c83c6e560`.

## Source revisions

| Owner | Start (C51C) | C51D |
|---|---|---|
| MediaTek HAL `android/hardware/mediatek/mt6878` | `efae973a60b67bf0df31380eea83b25f3e8f5f0a` | `d560ff4a4183be6094d9ed3dee8142c5684d4586` |
| Ulefone HAL `android/hardware/ulefone/gq5012bf1` | `72617cde4e647ac908539952fcd7c4f821d94d04` | `2acad919a48a5696739e77c3bc5af961342d2b0e` |
| Tools `hal-audit/` | `b2e292aa4416198a3d4885f559ab244c83c6e560` | commit containing this file |
| Kernel (read-only) | `af3ecd85d28614c2ad25c6448cd68634d62c6a33` | unchanged |
| Ulefone module mirror (read-only) | `b23e82b4deda06d96e84ca3bb84de5e1e1fc11b8` | unchanged |

Branch `integration/c51c-vibrator-timeout` in each owned repository; all were
clean at start and are clean after commit.

## 1. Stock vibrator evidence (read-only)

- Stock fragment `vendor/etc/vintf/manifest/vibrator-mtk-default.xml` declares
  `android.hardware.vibrator` V2 `IVibrator/default` AND `IVibratorManager/default`.
- Stock rc `vendor/etc/init/vibrator-mtk-default.rc`: service
  `vendor.vibrator-default /vendor/bin/hw/android.hardware.vibrator-service.mediatek`,
  class hal, user/group system, no `interface` lines.
- Stock binary SHA256 `ab4fc6285875b3f6ce70d1a7f15b10465d149fbb34a6c3bd8caa8d2d95b6573a`.
  NEEDED: libbase, libutils, liblog, libbinder_ndk, android.hardware.vibrator-V2-ndk,
  libhardware, libhardware_legacy, libc++, libc, libm, libdl. Strings (no
  disassembly): MediaTek `vendor/mediatek/proprietary/hardware/libvibrator/aidl/default/`
  `main.cpp`, `Vibrator.cpp`, `VibratorManager.cpp`; BnVibrator + BnVibratorManager;
  `/sys/class/leds/vibrator` with `activate`/`duration`/`state`, or
  `/sys/class/timed_output/vibrator/enable`. Manager sync log strings present.
- Live stock capture (`qwen_hardware/evidence/local/fingerprint-lights-vibrator-live.txt`):
  framework "Native HAL VibratorManager", `capabilitiesFlags = 11111111` (all
  eight Manager capability bits), `vibratorIds = [1]`, vibrator 1 capabilities 0,
  supportedEffects CLICK, DOUBLE_CLICK, TICK, HEAVY_CLICK, TEXTURE_TICK, no
  primitives. Live service list registers both instances.
- The `activate/duration/state` files come from the LED transient trigger:
  AOSP `system/core/rootdir/init.rc` writes `/sys/class/leds/vibrator/trigger
  "transient"` and later chowns trigger/activate/brightness/duration/state to
  system. Kernel config: `CONFIG_LEDS_TRIGGER_TRANSIENT=y`. The C50 and C51C
  regulator-vibrator drivers create no activate/duration/state files themselves.
- Stock vendor policy `vendor_sepolicy.cil:523`:
  `genfscon sysfs "/devices/platform/regulator-vibrator/leds/vibrator"` ->
  `sysfs_vibrator` (plus soc:/odm/timed_output alternatives). Stock ueventd has
  no vibrator entries. Stock `vibrator.default.so`, `libvibratorutils.so`,
  stock V2 NDK library are already `EXTRACT_ONLY` in `proprietary-files.txt`.
- Node: live DT `/regulator-vibrator`, `label = "vibrator"`, `vib-supply` MT6369
  VIBR LDO (`qwen_hardware/verification/findings/haptics.md`); live sysfs
  `/sys/devices/platform/regulator-vibrator/{driver,leds/vibrator}`
  (`slot-b-investigation/02-android-topology.txt`); kernel `mt6878.dts:3993`
  same label.

## 2. IVibratorManager decision

- Stock IVibrator and IVibratorManager are one process; the Manager returns its
  own in-process vibrator. Both rc files use `vendor.vibrator-default`.
  **Coexistence with this service is impossible; replacement is all-or-nothing.**
- Android 17 framework, actual source: Java
  `VintfHalVibratorManager.createHalVibratorManager` checks
  `isDeclared(IVibratorManager/default)`, else `isDeclared(IVibrator/default)` ->
  `LegacyHalVibratorManager` with one `DEFAULT_VIBRATOR_ID = 0`; native
  `connectManagerHal` -> `LegacyManagerHalWrapper` (capabilities NONE,
  SINGLE_VIBRATOR_ID). Matrices 202604/202704 list both interfaces `1-4`.
- **A Manager is not required.** A truthful one would advertise capabilities 0
  and one ID with every sync call unsupported, the same as the fallback. None is
  implemented. Stock's eight sync bits for one DC-driven ERM are not reproduced.
- **Retain the complete stock service for C55.**

Behavior differences after a future replacement: vibrator id 1 -> 0; prebaked
effects play via framework fallback waveforms through `on()`; framework `on()`
above the kernel maximum (5000ms) gets EX_ILLEGAL_ARGUMENT and
`SetAmplitudeVibratorStep` cancels that vibration (single one-shots >5s and
all-on repeating loops longer than 5s; loops <=5s request exactly
`REPEATING_EFFECT_ON_DURATION = 5000`). The ceiling is kept until hardware
validation; extending requests is a later owner/hardware decision.

## 3. Source defect fixed

C51C production `discoverDriverTimedRegulatorLed("/sys/class/leds")` opened every
LED class entry and returned the first EACCES. Platform policy gives
`hal_vibrator` only `sysfs_vibrator` file rw + dir search; `/sys/class/leds` is
`sysfs_leds` and sibling LEDs have other types, so under enforcing narrow policy
the service would never start, or would need broad LED access.

C51D `openDriverTimedRegulatorLed(device, label)` (MediaTek `LedSwitch.cpp`):
O_PATH|O_DIRECTORY open of `/sys/devices/platform/regulator-vibrator`;
`readlinkat(driver)` basename must be `regulator_vibrator` (unbound -> ENODEV);
`leds` and `<label>` opened O_PATH|O_DIRECTORY|O_NOFOLLOW (symlink -> ENOTDIR);
label rejects empty, `.`, `..` and `/`; then unchanged ABI1 checks. Board
`main.cpp` uses it with `"vibrator"`. Enumerators remain diagnostics/tests only.

## 4. Binder and kernel ABI review

- 24 frozen V2 methods; overrides compile against genuine SDK37 aidl-generated
  headers (frozen API SHA256 `51161792eba95aee28a92723a1430b235e57e75751c24db04d84f7d83cca318e`,
  hash `ea8742d6993e1a82917da38b9938e537aa7fcb54`).
- Registration `AServiceManager_addService(IVibrator/default)` after accepted
  initial OFF; thread pool max 0, main thread joins. Platform service_contexts
  already map the instance to `hal_vibrator_service`.
- Without CAP_ON_CALLBACK, the framework calls `on(ms, null)` and posts completion
  itself; non-null callbacks are refused (VTS `OnCallbackNotSupported`). After a
  failed `on()`, `cancelStep()` -> `CompleteEffectVibratorStep` -> `off()` clears
  the HAL fault latch. Static review of VtsHalVibratorTargetTest capability-0
  expectations: consistent; V3/V4 methods return UNKNOWN_TRANSACTION (accepted).
- Kernel agreement (source, not runtime): `timeout_abi` "1\n";
  `max_duration_ms` "%u\n" = `REG_VIBR_MAX_MS 5000U`; `duration_ms` store
  `kstrtouint(buf, 10)`, 1..max arms, 0 cancels, >max -EINVAL; read = remaining
  ms rounded up. HAL writes only "N\n"/"0\n" to duration_ms and validates
  1..max first. Store detaches the AOSP-selected transient trigger and drains its
  final OFF before arming. **No kernel defect found; kernel not modified.**

## 5. Tests and receipts (actual)

| Test | Result |
|---|---|
| HAL native (ControllerTest 12 + LifecycleTest 24) | 36/36 normal, 36/36 ASan/UBSan |
| HAL TSan (LifecycleTest) | 24/24 |
| New C51D native cases | 2: canonical binding/label/symlink/ABI; unreadable sibling LED breaks enumerator (EACCES) but not canonical open |
| Kernel shared policy (C51C harness) | 12/12 per mode + 4 static order guards |
| Python hal-audit | 100/100 opt-in, no skips (96 + 4 C51D contract checks); portable 81 pass / 19 skip |
| Genuine ARM64 object probe | 6/6 ELF64 AArch64 (Controller, LedSwitch, OneShot, DriverTimed, Vibrator, main) |
| Soong link | DEFERRED, not attempted |
| Binder IPC / VTS executed | 0 |
| Hardware | NOT PERFORMED |

C51D contract checks (`tests/test_c51d_integration.py`) pin: single-IVibrator
fragment; stock binary hash/both Bn classes/both fragment entries; identical init
service names; framework fallback source; canonical node in stock genfscon;
platform hal_vibrator/domain rules; no stock ueventd duration_ms entry; kernel
format strings and HAL parser.

## 6. Soong link — DEFERRED

C55 was running `m -j32 systemimage systemextimage productimage` in the shared
`out/` (load average 51-99) throughout. The platform tree contains neither
`hardware/mediatek/mt6878` nor `hardware/ulefone/gq5012bf1`; linking requires
adding them, which triggers Soong re-analysis of the shared output. Not done.
Exact procedure for an owner-approved exclusive window (relative OUT_DIR; no
product change; namespace not exported to Make, so the intermediate path is the
target; remove both directories afterwards):

```sh
cd /mnt/SamsungSSD/android/lineage-24.0
mkdir hardware/mediatek/mt6878 hardware/ulefone/gq5012bf1
git -C ~/LieppOS/android/hardware/mediatek/mt6878 archive d560ff4a4183be6094d9ed3dee8142c5684d4586 | tar -x -C hardware/mediatek/mt6878
git -C ~/LieppOS/android/hardware/ulefone/gq5012bf1 archive 2acad919a48a5696739e77c3bc5af961342d2b0e | tar -x -C hardware/ulefone/gq5012bf1
export OUT_DIR=out; source build/envsetup.sh; lunch lineage_gq5012bf1-cp2a-userdebug
m -j8 out/soong/.intermediates/hardware/ulefone/gq5012bf1/android.hardware.vibrator-service.gq5012bf1/android_vendor_arm64_armv8-a/android.hardware.vibrator-service.gq5012bf1
rm -r hardware/mediatek/mt6878 hardware/ulefone/gq5012bf1; rmdir hardware/mediatek hardware/ulefone
```

Record: linker exit status, undefined symbols, `llvm-readelf -d` NEEDED
(expect libbinder_ndk, libbase, android.hardware.vibrator-V2-ndk, libc++, libc,
libm, libdl), and the binary hash.

## 7. Exact C55/device-owner handoff (do not apply in C55)

1. Keep the stock vibrator selected; do not add this package; do not request activation.
2. Future replacement removes exactly these three stock entries (EXTRACT_ONLY + regenerate):
   `vendor/bin/hw/android.hardware.vibrator-service.mediatek`,
   `vendor/etc/init/vibrator-mtk-default.rc`,
   `vendor/etc/vintf/manifest/vibrator-mtk-default.xml`.
3. Product: `PRODUCT_SOONG_NAMESPACES += hardware/ulefone/gq5012bf1 hardware/mediatek/mt6878`;
   `PRODUCT_PACKAGES += android.hardware.vibrator-service.gq5012bf1` (installs module rc + fragment).
4. ueventd: `/sys/devices/platform/regulator-vibrator/leds/vibrator duration_ms 0664 system system`.
5. SELinux: no new allow. `BOARD_VENDOR_SEPOLICY_DIRS += hardware/ulefone/gq5012bf1/vibrator/sepolicy`
   (executable -> `hal_vibrator_default_exec`); keep stock genfscon line; rebuild
   vendor policy; enforcing only.
6. Kernel: C51C `regulator-vibrator.ko` (timeout ABI1) is a hard dependency; the
   stock HAL does not use it. Installation is separately authorized.
7. Verify: assembled `checkvintf` (IVibratorManager/default no longer declared),
   registration, IPC, VtsHalVibratorTargetTest, zero vibrator denials.
8. Hardware (separately authorized): duration rating, regulator fault/suspend/
   remove/process-death, physical OFF. Only then review `deploymentAllowed()`,
   `disabled`, `oneshot`.

Service linking: **not passed (deferred)**. Product integration: **not safe yet**.
Hardware activation: **not authorized**.

## 8. Remaining blockers

- Build: real Soong link and assembled VINTF/policy build not performed.
- Security: rebuilt vendor policy with executable label; ueventd DAC; enforcing check.
- ABI: installed kernel must provide timeout ABI1 (C51C module not installed).
- Runtime: Binder registration/IPC/VTS never executed; framework long-duration behavior is a policy decision.
- Physical: ERM continuous-on rating, MT6369 VIBR fault behavior, process-death OFF on device.
