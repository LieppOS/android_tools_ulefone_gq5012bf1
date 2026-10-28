# Research handoff — C51 Android 17 HAL source

**NOT YET INTEGRATED into the canonical research repository.** Claude owns concurrent C50 research changes. This is the existing single handoff, prepared for later import into `LieppOS/LieppOS-ulefone-gq5012bf1-research`; no research checkout/branch was modified or copied.

## Starting state and ownership

- Policies read: workspace AGENTS.md and canonical AI-POLICY.md / REPO-OWNERSHIP.md.
- Tools baseline: branch `integration/codex-hal-vintf`, clean commit `cf8a4e653c000e7331d59d1e5cfb02f6550e1b56`; **78/78 tests passed before edits**.
- Both existing hardware checkouts were empty, clean, unborn `main`, with expected existing origins and no other refs/implementations or index locks observed. No previous work was overwritten.
- All C51 development uses local `integration/c51-hal-source` branches in the three assigned repositories. Tools changes are restricted to `hal-audit/`.
- No kernel/module, device/vendor, manifest, shared inventory/docs, research or C50 output/branch was modified. No phone, flashing, reboot, full Android/kernel build, unrestricted sync, new repository, second Android tree or push occurred.

## Source revisions

| Owner repository | Commit | Tree | Content |
|---|---|---|---|
| `LieppOS/android_hardware_mediatek_mt6878` | `d8a26a85b00a5db382185150b2be148d8bade307` | `6373a0001855ce19bdb58b1300e6ba86e11390c6` | Native regulator LED discovery/timed controller, Soong library, 12-case C++ tests, provenance/license |
| `LieppOS/android_hardware_ulefone_gq5012bf1` | `92f95b00c3d8a019b23f91279df1cbb39d242164` | `ddb7f1e412d23f19034a12f02c4c972148be81dc` | Real frozen V2 AIDL vibrator adapter, registration, rc/fragment, narrow executable mapping, exact owner requirements |

The tools revision is the C51 commit containing this handoff (parent baseline above; full final SHA is supplied in the campaign completion receipt). The original audit remains reproducible from its baseline commit; no numbered copy of its reports is created.

## Verified findings and source classification

1. **One new implementation**, not two duplicate services: Ulefone owns `android.hardware.vibrator.IVibrator` V2/default; MediaTek owns its reusable native backend. Origin **INDEPENDENT**, LieppOS Contributors, Apache-2.0. No GPL kernel bodies or proprietary executable contents were imported.
2. Kernel `drivers/leds/regulator-vibrator.c` registers a platform driver named `regulator_vibrator` (line 19/313), uses zero/nonzero LED brightness (163–173), takes LED name from DT label and registers its parent through LED class (231–240). SHA-256: `d6cec1e2d6a04d1fd31f8a128ec365999ac1382539395b53d9873a4c85a5ff44`. The backend therefore discovers exactly one matching `/sys/class/leds` device; it does **not** invent a `vibrator` label or timed_output path.
3. The LED callback queues work and reports accepted writes, not regulator motion/error acknowledgment. The new source propagates available I/O errors and does not fabricate physical feedback. It rejects partial transactions and ambiguous/missing/invalid devices. Final attribute symlinks are refused; expected class/device sysfs links are handled deliberately under the fixed production root.
4. Timed on/off, monotonic cancellation/replacement, serialized access, error propagation/retry and shutdown off are implemented. Capability bits are zero. Unsupported callbacks/amplitude/compositions/effects/frequency/always-on operations explicitly return unsupported errors. No unverified feature is advertised.
5. **Safety blocker:** the verified LED ABI has no kernel timeout. Process death can leave the actuator on until a successful restarted service initial off or a kernel suspend/shutdown attempt. Worker/destructor safety is not a process-death fail-safe. Activation requires owner-approved crash/restart/power validation or an existing verified fail-safe. No kernel change is proposed/applied by C51.
6. DT LED label, actual real-device sysfs path, labels and ueventd ownership are not recovered. The source does not run as root or grant broad sysfs permissions. `vibrator/sepolicy/file_contexts` maps only the new executable to target `hal_vibrator_default_exec`; real node policy remains an owner prerequisite.
7. The target `LineageOS/android_hardware_interfaces` commit **13fc23dae0dcd24fc2411d74f54a407999eaf555** retains genuine frozen vibrator V2 and the NDK backend (`vibrator/aidl/Android.bp` SHA-256 `ce71a302b6d4f65e5b68b31162c0858a5149c92f8ed8aa34fa635f3cf984085a`). V2 API SHA-256: **51161792eba95aee28a92723a1430b235e57e75751c24db04d84f7d83cca318e**. The authentic API test fixture preserves AOSP notices and full Apache license; it is not a substitute generated header/interface module.
8. V2/default is the **selected new source contract**, not a recovered stock fragment or Android 17 matrix PASS. Existing extraction metadata references the stock V2 NDK library, MTK executable, `vibrator-mtk-default.rc/xml` and init name `vendor.vibrator-default`; those bodies remain unavailable. Do not install the new and old definitions together.
9. Existing upstream Lineage charging control was located at `LineageOS/android_hardware_lineage_interfaces` commit **68dca0c523594fb7c34e94782d0f21660530a2dc**, Apache-2.0, `health/aidl/default/ChargingControl.cpp`. It was **not duplicated/imported**. The configured MTK input_current_limit reads/writes `thermal_input_current_limit` in `mtk_charger.c:3538–3540,3701–3703` (SHA-256 `d72a20d65e2a0e376716770e4a4701c3939b8dcd0e48c5b7bf562dadffef808a`). Blindly clearing a shared thermal constraint is not a safe new health implementation.
10. The existing Android vibrator example source was located and inspected at the pinned target interfaces commit, `vibrator/aidl/default/Vibrator.cpp` (Apache-2.0). It is not a verified MTK hardware backend and was not imported with its example capabilities. Lights/USB/power contracts were insufficient for safe board implementations; no dummy services were written. No camera/radio/TEE/biometric work or reverse-engineering campaign was undertaken.

Kernel paths above are relative to `android/kernel/ulefone/gq5012bf1/` and were inspected read-only only for the immediate userspace ABI. Source/provenance of the kernel itself remains with its existing owner.

## Historical evidence, narrow scope

The existing documented external C46 files were read without phone access:

- `hardware-approved/slotb-dmesg.txt`: SHA-256 `8994a8516f527dd90215452f4354ddbe54d1faee18e4963f13e93f64a9732c81`; driver `vibr_enable` / `vibr_disable` at lines 170/191. **Not a test of the C51 source.**
- `hardware-approved/live-slotb-getprop-1.txt`: SHA-256 `442b75bded935b46dd3fa473bc1d706339d0bc27f84a516bc3b919bee82a5a45`; Android 17/SDK37 at 862/865, Lineage version at 898, boot_completed=1 at 1250. Only allowlisted properties are retained, no raw log/device identifiers.
- Authorized provenance document `docs/integration/ACTIVE-BUILD-PROVENANCE.md` (baseline SHA-256 `ffb173ce0ee4c7f38d60ff5e99125c4b8c93883f0dc49f8bbc70ac8174c695a5`) quotes C46 `vendor_boot_b` hash `fee66502411e57c958cff58021e7379f6a2f0cd05b061738ac0469974360bfb6` and `vbmeta_b` hash `29c29463bf8bed9cbe3efdf7d0d985c852d30acf4f22a098c190c1043e3ae9ea`. No ROM image was opened/rehashed.

C46 completion applies only to that image set, not individual HAL functionality or the current source. Existing cross-version userdata/TEE key-upgrade risk remains relevant to future owner-approved hardware plans. No C51 source service is HARDWARE_VERIFIED.

## Init and VINTF disposition

- All **77 original non-passthrough relationships** have individual `init_relationships` records with declaration provenance, actual parsed service links if any, categories and explicitly unverified stock-comment candidates. All 77 remain **MISSING_METADATA** / source unavailable in the supplied roots; **zero** historical relationships were falsely resolved from filenames or guessed shared processes.
- The new vibrator contributes **one RESOLVED_SERVICE source relationship**; 77 remain. Shared/lazy/framework/proprietary classifications are implemented and tested only when supporting evidence exists. Disabled alone is not lazy; unrelated module rc helpers are no longer automatically treated as HAL processes. Passthrough libraries are not counted as missing standalone services.
- All **48 overlaps** are reviewed as explicit **INTENTIONAL_OVERRIDE** at source-intent level, with both file/line references and identical contract identities. No shared manifest was changed. Actual selected partition/SKU/APEX merge remains unvalidated.
- AEE HIDL 1.1 versus AIDL 1 `IAee/AEE` (`manifest.xml:121,127`) is recorded **DISTINCT_PROTOCOL_IDENTITIES_REVIEWED**, not a proven duplicate. Legacy diagnostic naming is retained; text similarity alone proves no failure.
- Reference libvintf source: AOSP commit **9a095008eaf2b4ac7cb6e9d2da6aeca596f04062**, `HalManifest.cpp` SHA-256 `6e9466040c3fa9bd09423fc762f0138408603647223b1d2b02e8b758279dc4be`; override/FqInstance logic was consulted, **not reimplemented as platform validation**. Actual platform conflict count is UNKNOWN (`NOT_RUN`), not a fabricated zero-conflict certification.

Current scan: **148** eligible files, **128** declaration occurrences / **80** unique contracts (79 historical + one new unactivated source fragment), **123** inventory rows, **1** mapped source HAL and **0** hardware-verified services. One original metadata-only vibrator row is represented by the new source-contract row; there is no recovered new physical capability. Selected implementation dependencies are separated from unbound old blob candidate metadata.

## Test/build receipt and reproduction

```sh
cd /home/armol/LieppOS/tools/ulefone/gq5012bf1/hal-audit
LIEPPOS_REAL_SOURCE_TESTS=1 LIEPPOS_C51_SOURCE_TESTS=1 \
  PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 \
  python3 -B -m unittest discover -s tests -v
```

- **90/90 Python checks PASS**, no skips: original 78 plus 12 C51 checks. The prior zero-source real-input assertion is explicitly scoped to the original unmapped contracts while allowing the genuine new candidate; no test was deleted or disabled to mask a failure.
- **12/12 native C++ cases PASS in each of two builds**, native and ASan/UBSan. Compiler: GCC 16.2.1 Linux x86_64; `-std=c++17 -pthread -Wall -Wextra -Werror -O1 -g`, sanitizer flags `-fsanitize=address,undefined -fno-omit-frame-pointer`, leak detection/halt-on-error enabled. Tests exercise timing, cancellation/replacement, error propagation/retry, concurrency, discovery/malformed/ambiguous/missing nodes, leaf-link safety and fd lifetime.
- All 24 frozen AIDL method names, source definitions, module/fragment/init linkage, dependencies and narrow executable context are checked. **Binder methods themselves are not execution-tested/compiled**, and source matching is not VTS/SELinux compilation.
- An actual syntax-only adapter dependency probe exited **1**: missing authentic `aidl/android/hardware/vibrator/BnVibrator.h`. Canonical build/soong, generated V2 NDK library/headers, libbinder_ndk/libbase graph, target matrices/policy are absent. **SOONG_BUILD_PASSED / VINTF_VALIDATED / PLATFORM_INTEGRATED / HARDWARE_VERIFIED are NOT claimed.** No fake header or full platform download was used.
- Compiler outputs/fixtures use and clean the tooling runner's ignored `.tmp/`; nothing is left in source or C50 build outputs. No expected hashes were edited to hide test failures.

Use the existing six-root CLI invocation in `../README.md` to regenerate reports. Two complete C51 exports were byte-identical; hashes:

| Report | SHA-256 |
|---|---|
| `HAL-INVENTORY.json` | `b693ab1af7ed7e97b6bedc6733ef73e4248e8035cdc0a247e3d4676d20b75151` |
| `HAL-INVENTORY.csv` | `353c7d4b66aba8699f15f149c3a9af6b5a1011f0d8f4250636e6a52dc7fa34fd` |
| `SCAN-SUMMARY.md` | `bf2fa75a368b19aebce6f3461caf013024b9c4bdf3c546e29df3d4a4285b5df0` |

All 148 raw-byte source/config/license hashes are embedded in JSON. Canonical `inventory/subsystems.csv` is neither modified nor copied; its previous audit snapshot is available in baseline Git history, not reissued as a competing inventory.

## Exact owner next actions

See `android/hardware/ulefone/gq5012bf1/README.md` for proposed namespace/package lines and exact old binary/rc/fragment exclusions. No activation edits were applied. Required gates:

1. Supply true target Android 17 build dependencies; build **only** `android.hardware.vibrator-service.gq5012bf1` and selected policy.
2. Supply real stock vibrator fragment/matrices and sanitized actual sysfs path/labels/ownership; validate selection, no duplicate service, and narrow system-UID/domain access.
3. Establish/validate process-death timeout safety before activation; no blind kernel change by this campaign.
4. Run real assembled metadata checks and later separately authorized hardware tests on an identified safe image set. Do not infer any operation from C46 boot completion.
5. When research ownership is free, import the verified narrative/provenance and reference the canonical source/tool commits. **Research remains unmerged and publication-held** under the existing policy.

## Publication approval packets — preparation only, NO push

Both proposals are **source-only experimental review candidates, NOT deployment-ready**. Each reachable proposed source history is one new root commit containing only the scoped source/license/tests/docs; no inherited vendor history or binary payload is introduced. Source inspection found no secrets, firmware, calibration or device identifiers in these new hardware trees. This is not a hardware/security certification.

| Field | MediaTek backend | Ulefone adapter |
|---|---|---|
| Repository | `LieppOS/android_hardware_mediatek_mt6878` | `LieppOS/android_hardware_ulefone_gq5012bf1` |
| Existing remote | `origin` (`git@github.com:LieppOS/android_hardware_mediatek_mt6878.git`) | `origin` (`git@github.com:LieppOS/android_hardware_ulefone_gq5012bf1.git`) |
| Destination ref proposed | `refs/heads/integration/c51-hal-source` | `refs/heads/integration/c51-hal-source` |
| Full commit | `d8a26a85b00a5db382185150b2be148d8bade307` | `92f95b00c3d8a019b23f91279df1cbb39d242164` |
| Tree | `6373a0001855ce19bdb58b1300e6ba86e11390c6` | `ddb7f1e412d23f19034a12f02c4c972148be81dc` |
| License/origin | INDEPENDENT, Apache-2.0; full LICENSE present | INDEPENDENT, Apache-2.0; full LICENSE present; uses platform interface, no copied generated headers |
| Build validation | Native + ASan/UBSan backend 12/12 each; Soong NOT RUN | AIDL API/config source checks PASS; actual adapter probe BLOCKED by missing BnVibrator.h; Soong NOT RUN |
| Security/integration status | No broad privileges/data payloads; physical timeout fail-safe unverified | System UID, literal executable context; exact sysfs policy/ownership, target compatibility and crash safety required |
| Dependencies | Linux LED ABI, actual regulator driver/DT/PMIC; whole hardware stack not certified open | Exact backend commit above, target V2 NDK/libbinder_ndk/libbase, owner product/vendor/policy selection |
| Expected prior remote state | UNKNOWN; must be rechecked under any future exact approval | UNKNOWN; must be rechecked under any future exact approval |
| Force permitted | **NO** | **NO** |

A packet is not authorization. No remote branch, main branch, repository setting, research history or phone state was changed. Final campaign verdict is partial source integration with explicit build/runtime blockers, not a claim that Android 17 userspace is fully open or functional.
