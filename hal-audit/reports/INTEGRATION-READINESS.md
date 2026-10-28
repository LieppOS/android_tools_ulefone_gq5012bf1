# C51 — Android 17 HAL source integration readiness

**Result: SOURCE INTEGRATION PARTIAL. One real timed vibrator implementation is present; Android service compilation, platform activation and hardware verification are not complete.**

This continues audit baseline `cf8a4e653c000e7331d59d1e5cfb02f6550e1b56`; it does not repeat the kernel/Wi-Fi campaign. Only the assigned MediaTek/Ulefone hardware repositories and `hal-audit/` were changed. Device/vendor activation, shared inventory/docs, manifest and concurrent C50 research/kernel/module work remain untouched.

## Actual implementation result

| Item | Result |
|---|---|
| Existing upstream implementations located | LineageOS 24 charging-control default and Android vibrator example; Apache-2.0, reference implementations, not imported |
| Existing implementations integrated | 0 — no unnecessary duplicate of the existing Lineage health service |
| New HAL implementations | 1 — AIDL `android.hardware.vibrator.IVibrator`, frozen V2/default |
| Board service owner | `android/hardware/ulefone/gq5012bf1/vibrator/` |
| Native backend owner | `android/hardware/mediatek/mt6878/vibrator/` |
| Native backend builds | PASS, GCC 16.2.1 normal and ASan/UBSan builds |
| Native behavior tests | 12/12 in each build |
| Android Binder adapter build | BLOCKED, authentic generated BnVibrator header unavailable |
| Soong service builds / platform integration / hardware verification | 0 / 0 / 0 |

The code performs real kernel attribute I/O and timed off; it does not sleep and pretend a motor ran. It rejects unsupported callbacks/amplitude/effects/frequency/composition rather than advertising example capabilities. All 24 genuine V2 methods are declared/defined. The kernel LED callback itself queues asynchronous work, so successful writes mean accepted commands, not measured motor motion.

### Verified selection, no guessed DT label

Kernel source `drivers/leds/regulator-vibrator.c` identifies the actual `regulator_vibrator` platform driver, LED registration and zero/nonzero brightness behavior. Its byte SHA-256 is `d6cec1e2d6a04d1fd31f8a128ec365999ac1382539395b53d9873a4c85a5ff44`. The C46 dmesg captures that driver enabling/disabling (SHA-256 `8994a8516f527dd90215452f4354ddbe54d1faee18e4963f13e93f64a9732c81`). No driver source was modified/copied and no new hardware test occurred.

The label is provided by DT and was not independently recovered. The backend therefore discovers exactly one `/sys/class/leds` entry through its `device/driver` identity. It verifies max_brightness, rejects ambiguous/missing devices and final-attribute symlinks, and only writes 1/0. No guessed `vibrator` label, voltage, timed_output path, ioctl or calibration is introduced.

The target public `LineageOS/android_hardware_interfaces` commit `13fc23dae0dcd24fc2411d74f54a407999eaf555` retains frozen V2 and the NDK backend. The authentic V2 API fixture has SHA-256 `51161792eba95aee28a92723a1430b235e57e75751c24db04d84f7d83cca318e`. This is a **selected source contract**, not a claim that the missing stock vibrator fragment was recovered or that the target framework matrix accepts it.

## Priorities not guessed into implementations

| Candidate | Evidence-driven decision |
|---|---|
| Lights | Camp-light patches are known, but mapping custom lights to Android-standard light IDs and the actual standard lights contract are unverified. No fake light types or labels created. |
| Vibrator | Real kernel ABI + historical driver evidence + target frozen API support permit the bounded on/off source implementation. Activation remains gated below. |
| USB | No actual port/gadget fragment/rc/board-role/configfs contract supplied; do not copy a generic service and claim it works. |
| Health/battery | Existing Lineage/AOSP implementation families already exist. The configured MTK input_current_limit maps to a **shared thermal current-limit field** in `mtk_charger.c` (hash `d72a20d65e2a0e376716770e4a4701c3939b8dcd0e48c5b7bf562dadffef808a`, get/set at 3538–3540 / 3701–3703). Do not blindly clear a live thermal constraint with -1 or duplicate the existing service. |
| Power | Real hint/backend ownership and service-library loading contract are missing; no no-op service pretending successful power control. |

The existing source identified upstream is not a verified GQ5012BF1 implementation. No camera, radio, KeyMint/TEE or biometric replacement was attempted.

## Current derived inventory

| Population | C51 result |
|---|---:|
| Eligible source/config/license text files | 148 |
| VINTF declaration occurrences | 128 |
| Unique interface-instance-format-version contracts | 80 |
| Total inventory rows | 123 |
| Mapped HAL source implementations | 1 |
| Existing helper/client modules (not HAL servers) | 5 |
| Retained extraction-reference-only artifact rows | 35 |
| `implementation_status=UNKNOWN` rows | 87 |
| Hardware-verified services | 0 |

The extra declaration is the **new, unactivated source vibrator fragment**. This does not recover an additional stock device capability. The new implementation consumes no proprietary userspace libraries: it links open platform Binder/base/interface libraries and the native source backend. Its kernel/PMIC/DT/hardware boundary is not thereby declared fully open or verified. Unbound old binary candidates are explicitly separated from selected implementation dependencies in JSON.

## All 77 historical init relationships reclassified

`HAL-INVENTORY.json:init_relationships` contains an individual evidence-backed entry for each non-passthrough contract, with classifications/categories and source locations.

- **77 historical relationships remain MISSING_METADATA**, with SOURCE_UNAVAILABLE/UNRESOLVED categories scoped to supplied inputs. Filename/stock-init-comment candidates are retained as **unverified** process candidates, not resolutions.
- **1 new relationship is RESOLVED_SERVICE at source level**: V2 IVibrator/default → documented init name `vendor.vibrator-default` → new source executable/module/fragment.
- Therefore resolved **among the original 77: 0**; current total resolved source relationships: 1; current remaining: 77. There is no claimed reduction obtained by guessing shared processes.
- Two legacy passthrough contracts do not require standalone init relationships.
- Classifier supports genuine SHARED_SERVICE, LAZY_SERVICE, FRAMEWORK_OWNED and PROPRIETARY_SERVICE when exact source evidence exists. Disabled alone is not enough to call a service lazy. An unrelated helper in a module's rc is no longer automatically bound as its HAL process.

The 50 stock vendor fragment references and 122 vendor init references are still names without supplied bodies in the empty vendor roots. No generated vendor makefile appeared. Full stock relationships cannot be recovered from these references alone.

## VINTF review, not a custom compatibility PASS

- **48/48 exact overlaps have explicit override intent**: `vintf_review.overlaps` records each identity, both file/line references and `override=true`. Classified INTENTIONAL_OVERRIDE at source level, not duplicate failures. Actual SKU/partition/APEX selection remains unchecked.
- AEE `vendor.mediatek.hardware.aee.IAee/AEE` at main manifest lines 121/127 has HIDL 1.1 and AIDL 1 wire identities. Recorded as DISTINCT_PROTOCOL_IDENTITIES_REVIEWED. Text similarity alone establishes no conflict. The old potential-conflict diagnostic name is preserved for compatibility, not treated as a proven platform failure.
- AOSP libvintf source was consulted at commit `9a095008eaf2b4ac7cb6e9d2da6aeca596f04062` (`HalManifest.cpp` SHA-256 `6e9466040c3fa9bd09423fc762f0138408603647223b1d2b02e8b758279dc4be`): add/override removal and FqInstance checks are real merge logic, not reproduced by this parser.
- **Confirmed platform conflict count: UNKNOWN / NOT_RUN. No actual conflict is proven.** No checkvintf/assemble_vintf executable or complete target matrices were safely available. No device/vendor manifest entry was changed or removed.

## Exact blockers before activation

1. **Android build dependencies:** canonical `android/build/` is empty; `build/soong`, `hardware/interfaces`, generated `android.hardware.vibrator-V2-ndk` headers/library, `libbinder_ndk`/`libbase` build graph and target platform artifacts are absent. An actual native syntax-only adapter probe exits 1 at missing `aidl/android/hardware/vibrator/BnVibrator.h`. No fake header or successful Soong claim was substituted.
2. **Owner-only product/vendor selection:** add the new source namespace/package and remove only the old vibrator executable/rc/fragment from installation. Both use the same documented init name; do not install both. Exact paths and proposed makefile lines are in the board hardware README. Device/vendor files were not edited.
3. **Target contract/platform policy:** obtain the real stock fragment/matrices, verify V2/default compatibility and include the narrow source executable file_contexts mapping. Existing target `hal_vibrator_default` transition is referenced, not permissively replaced. Compile real policy and check assembled metadata later.
4. **Actual sysfs ownership/labels:** DT LED name and real device path/labels/ueventd ownership are missing. Supply sanitized metadata and grant only required directory/link reads, max_brightness read and exact brightness write. No broad sysfs permissions, root service or SELinux disabling is added.
5. **Process-death physical timeout:** this verified brightness interface has no kernel timed-off guarantee. Worker/startup/destructor safety cannot stop a motor while the process is dead. Owner-approved crash/restart/suspend validation or an existing verified fail-safe is required before activation. No kernel change is attempted.

Only `m android.hardware.vibrator-service.gq5012bf1` is proposed when the true Android 17 build exists; no full ROM build, unrestricted sync or second Android tree was created.

## Tests and evidence

- Original baseline verified **78/78 before edits**.
- Current suite **90/90 PASS**, no skips with both real-source and C51 flags: original 78 plus 12 new Python checks. The prior zero-source real-input assertion is now explicitly scoped to the original unmapped contracts, preserving that gate while allowing the new source candidate; no test was deleted or disabled.
- Native C++ suite **12/12 PASS twice**: normal build and ASan/UBSan (leak detection / halt-on-error enabled), including timing/cancellation/replacement, error propagation/retry, concurrency, descriptor lifetime, exact-driver discovery, malformed/missing/ambiguous/sysfs-link cases.
- Frozen method-set, exact init/module/VINTF linkage, dependencies and narrow executable policy references are checked. **Binder methods are not claimed execution-tested or compiled**; the API check does not substitute for authentic generated headers/VTS.
- Repeated actual source scans and generated JSON/CSV/Markdown exports are compared for deterministic content. All temporary binaries/fixtures are under the tooling runner's ignored `.tmp/` and removed; none is committed.
- The existing 2 MiB patch cap and its one skipped vendor patch remain explicit coverage limits.

Historical C46 getprop evidence and userdata/TEE upgrade safety constraints remain scoped to that exact image set. No current implementation is HARDWARE_VERIFIED. Research is **not yet integrated**: see the single `../docs/RESEARCH-HANDOFF.md` for source revisions, hashes, test receipt and publication review packets.
