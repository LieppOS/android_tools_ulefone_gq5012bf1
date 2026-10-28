# Research handoff — C51B vibrator continuation

**C51B NOT YET MERGED into the C53-owned canonical research worktree by Codex.**
DeepSeek owns C53 platform/device/vendor/research recovery. Destination remains
`LieppOS/LieppOS-ulefone-gq5012bf1-research` (`research/ulefone-gq5012bf1`).
C52 reports that its earlier C51 summary was integrated at research commit
`dadede0f74edaa884f2cce6b77cbc885cddc3675`; that does not merge these C51B results.
No research checkout, other agent branch/output, platform or kernel source was
modified. No push or phone operation occurred.

## C51B recovery and exact source revisions

The three assigned worktrees were recovered on `integration/c51b-vibrator`, with
unstaged/untracked C51B source and no staged work/index locks. HEADs were exactly
the C51 baselines d8a26a8 / 92f95b0 / 80545f8. Nothing was reset, discarded or blindly
reapplied. The interrupted correction to deterministic caller fault injection was
preserved. Recovery tests were already **94/94 PASS**, beyond the C51 90 baseline.

| Source owner | C51B commit | Tree |
|---|---|---|
| `android_hardware_mediatek_mt6878` | `1957904697f7eec67b42c3a46b9b86a5761da779` | `a04942aee7a1410a56ffdf97d590d187c58b545f` |
| `android_hardware_ulefone_gq5012bf1` | `88aac5431cdb2e2599411658d6e71dc233ab2bb6` | `cec737485c17a23de683fba10e807ce58737c026` |

Both preserve their respective C51 parents. Tools C51B changes are the commit
containing this handoff, parent `80545f8775e0695840a7640bb16faddc8be0f845`;
its full SHA is in the final completion receipt. Native source remains INDEPENDENT,
LieppOS Contributors, Apache-2.0; no generated headers, binaries, firmware,
calibration, keys or proprietary implementation bodies were imported.

## Verified timeout/lifecycle findings

Full source references/hashes, 14-scenario failure model and kernel-owner request
are in `android/hardware/mediatek/mt6878/vibrator/SAFETY.md` at the commit above.

- Existing regulator-vibrator brightness has no kernel-owned timeout. An hrtimer
  include is not timer initialization. The new host SIGTERM/SIGKILL/SIGABRT tests
  show a fake brightness node remains ON after process death; restarted mandatory
  OFF repairs it. **Not a real device watchdog test.**
- Existing `ledtrig-oneshot.c` / `led-core.c` implement a kernel-owned finite shot
  independent of the userspace process. With invert=0 and positive delay_on/off,
  the timer ends OFF. **delay_off=0 instead means indefinite ON**. A shot while a
  previous shot is pending is ignored; cancel before rearm is necessary.
- New `OneShot.cpp` uses exact-driver discovery, requires advertised oneshot and
  verifies active `[oneshot]`. Serialized writes: brightness=0, trigger=oneshot,
  invert=0, delay_on=requested milliseconds, delay_off=1, shot=1 **last**. It never
  emits brightness=1 or falls back to the unsafe diagnostic switch. Configuration
  and partial-write errors propagate. A failed shot write might already have
  armed a finite pulse; controller immediately attempts OFF, never reports success.
- Successful kernel shots no longer arm a competing normal userspace deadline:
  kernel turn-on begins on a later tick, and the earlier user deadline could
  shorten the requested pulse. User timers remain only for legacy diagnostic
  behavior and failed-I/O cleanup. Faults latch re-enable until explicit successful
  OFF, failed standalone OFF now arms retry, failed replacement stops immediately
  rather than preserving a distant deadline, null partial init returns ENODEV.
- The inspected gki_defconfig does not select ONESHOT. The **unapplied** review-only
  `oneshot-config-proposal.patch` adds CONFIG_LEDS_TRIGGER_ONESHOT=y to existing
  GPL kernel code. Fixture-only dry-run passes; no kernel worktree is modified.
- Guarantee is CONDITIONAL: correct loaded kernel/trigger, stable binding,
  exclusive authorized writer, running scheduler/workqueues and working regulator
  OFF. Physical/current feedback is not available through this driver. Kernel
  remove/probe-unwind/workqueue/notifier/suspend lifetime defects require owner
  review/fix. The finite signed-32-bit API bound is not a validated safe physical
  continuous-vibration limit; owner must establish a duration policy before release.
- **Process-death safety remains BLOCKED for deployment.** No custom PMIC timer,
  register, DT label, physical limit or independent watchdog process is invented.

## Actual interface/build receipt

The existing full platform is identified by read-only C52 coordination evidence
`docs/integration/C52-DEVICE-VENDOR-INTEGRATION.md` (SHA-256
`6380a7c76bc7d57b4228c43a2bb56cd1db374e32d81ebf32e9c955b7f7f08527`), not by a
filesystem-wide search. Canonical `android/` is presently integration-only.

From `/mnt/SamsungSSD/android/lineage-24.0`, the real targeted request was:

```sh
TARGET_PRODUCT=lineage_gq5012bf1 TARGET_RELEASE=cp2a TARGET_BUILD_VARIANT=userdebug \
  OUT_DIR=<owned-temporary>/soong TMPDIR=<owned-temporary> \
  GOCACHE=<owned-temporary>/gocache GOMAXPROCS=2 \
  bash build/soong/soong_ui.bash --make-mode -j2 android.hardware.vibrator-service.gq5012bf1
```

Network Go fetching was disabled; all build/cache output was isolated under the
existing ignored tooling `.tmp/` and removed. No C53 output/locks were reused.
Product evaluation ran; bootstrap exited **1**, with the actual error:
`failed to load @config//main.star: open main.star: no such file or directory`.
C53 owns repair. The two hardware source module paths are also absent in that
platform; C53 must wire canonical source revisions, not stale copies.

Independently, `tests/android_adapter_probe.py` used the **real platform SDK37 aidl**
to generate NDK headers from the authentic frozen V2 sources and hash, then real
source-selected Android Clang22/Bionic/libc++ with vendor/VNDK macros to compile
Controller.cpp, LedSwitch.cpp, OneShot.cpp, Vibrator.cpp and main.cpp:
**5/5 arm64 relocatable objects PASS** (ELF64 little-endian, e_machine=183,
e_type=REL checked). No fake BnVibrator or platform classes were created.

| Input/result | Exact value |
|---|---|
| Target interfaces commit | `13fc23dae0dcd24fc2411d74f54a407999eaf555` |
| Frozen IVibrator V2 SHA-256 | `51161792eba95aee28a92723a1430b235e57e75751c24db04d84f7d83cca318e` |
| Frozen interface hash | `ea8742d6993e1a82917da38b9938e537aa7fcb54` |
| SDK37 aidl executable SHA-256 | `e1e14741bd59f5b5eff3a01e50bc226d465b576f4ad4e9b77623933362e8d591` |
| Generated genuine BnVibrator.h SHA-256 | `be9855519afb8f1bf1076c2f64d1e4d7167184e8eec8634060db9e8b42bd73cc` |
| Source-selected compiler | `prebuilts/clang/host/linux-x86/clang-r584948/bin/clang++`, resource version22 |
| Target flags | aarch64-linux-android10000, C++17, PIC, no exceptions/RTTI, vendor/VNDK macros, Wall/Wextra/Werror, actual Bionic/libc++/NDK includes |

This fixes the old missing-header dependency **for an independent source-object
probe**. It verifies actual V2 override signatures, not service linking, the
Soong vendor graph, registration/IPC, VTS or physical operation. The service is
**NOT Soong-built or linked**. Generated files/objects are removed, not committed.
Pinned target IVibrator documentation and VTS source were consulted for truthful
capability/callback/optional-method behavior; VTS was not executed.

## Tests, integration gate and owner next actions

- **94/94 Python checks PASS**, original90 preserved plus4 focused C51B checks.
- **12/12 original native cases** normal and ASan/UBSan; **17/17 lifecycle/policy/
  protocol cases** normal, ASan/UBSan AND TSan. GCC16.2.1, C++17/pthread,
  Wall/Wextra/Werror/O1/g; leak/halt-on-error sanitizers. Tests use actual controller
  and production request policy with explicitly fake sysfs, not Binder mocks.
- Tests cover validation/cap0/callback rejection, every timed transaction failure,
  activation/cancellation/replacement, fault latch/recovery, read errors, missing/
  wrong/ambiguous nodes, fd ownership, concurrency, restart/shutdown, null init and
  legacy process-kill limitations. An initial new source-check expectation was
  corrected from20 unsupported wrappers to19 (24 frozen methods minus5 handled
  methods); no functional failure was suppressed or original test removed.
- Exact integration contract is the board owner's README at the commit above:
  module `android.hardware.vibrator-service.gq5012bf1`, V2 IVibrator/default,
  executable `/vendor/bin/hw/android.hardware.vibrator-service.gq5012bf1`, init
  `vendor.vibrator-default`, static libmtk_regulator_vibrator and shared V2-ndk/
  libbinder_ndk/libbase. System UID/group; default vibrator domain/executable type.
- Code gate is unconditionally FALSE **before discovery/I/O/registration**, plus
  disabled+oneshot init. There is no property/command-line bypass. Keep package
  AND fragment unselected; disabled alone cannot prevent interface-start requests.
- C52 reports stock binary/rc are PRODUCT_COPY_FILES and fragment is a package.
  Future exclusion must mark the exact three extraction entries EXTRACT_ONLY and
  regenerate vendor config, not mutate readonly product variables in BoardConfig.
- **Newly available C52 compatibility evidence:** stock V2 fragment also declares
  IVibratorManager/default; our source implements ONLY IVibrator. Do not drop
  Manager silently or fabricate its actuator IDs. Owner must resolve the Manager
  implementation/compatible selection before replacing the whole stock service.
- Node labels/real path/ueventd ownership remain unknown. Required narrow rights
  are directory/link reads, max_brightness read, trigger read/write, brightness
  OFF and invert/delay_on/delay_off/shot writes; no broad sysfs/root/permissive rule.
  **Creation-lifetime gate:** led_trigger_set removes/adds attribute groups;
  brightness=0 removes the trigger, so each new shot recreates its attributes.
  oneshot defines invert/delays as0644 and shot as0200. Do not assume a one-time
  chown/boot rule survives recreation, or that asynchronous change-event ueventd
  handling finishes before HAL writes. Owner must demonstrate deterministic
  narrow ownership/access across every cancel/rearm, or provide an appropriate
  stable kernel-timed ABI. Do not solve this with root/DAC_OVERRIDE shortcuts.
  Current source returns access errors/fault-latches; it does not pretend this
  unavailable ownership contract is solved.
- Next: C53 restores real bootstrap and wires sources; kernel owner validates
  ONESHOT/config/lifetime/duration policy; device/vendor owner resolves Manager,
  exact single-service selection, node policy, true linking/metadata/IPC. Only
  then separately approved hardware/process-death validation and gate review.
  No activation or hardware test was performed by C51B.

Reproduce from `tools/ulefone/gq5012bf1/hal-audit`:

```sh
LIEPPOS_REAL_SOURCE_TESTS=1 LIEPPOS_C51_SOURCE_TESTS=1 \
  PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover -s tests -v
PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 python3 -B tests/android_adapter_probe.py \
  /mnt/SamsungSSD/android/lineage-24.0
```

Only affected vibrator source/readiness interpretations were updated. Existing
JSON/CSV/SCAN-SUMMARY are explicitly retained frozen C51 snapshots; no new full
inventory exercise of C53-owned inputs or reopening of77 relationships occurred.
The live source lens now records the conditional oneshot dependency when present,
without certifying tests/build/hardware. All acceptance gates remain independent.
No extra checkout, repository, permanent build artifact or AI-policy automation.

---

# Retained C51 historical handoff (superseded above for vibrator)

The following is the C51 record at tools baseline80545f8. C52 reports that its
summary was merged; these old counts/build blockers/publication proposals are
historical and must not be applied as current C51B status.

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

## Archived C51 publication packets — SUPERSEDED, no current approval request

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
