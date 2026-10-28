# LieppOS HAL/VINTF audit

Read-only Python 3.10+ / Linux integration auditor. Standard-library runtime; no Android build, phone connection, root, extraction, source execution or external Python dependencies.

**Ownership:** only `tools/ulefone/gq5012bf1/hal-audit/` in the existing tools checkout. This is a specialized derived audit, not a replacement for `inventory/subsystems.csv` or the authoritative research repository. Nothing here changes Android configuration.

## C51B continuation — deployment CLOSED

Uncommitted C51B work was recovered on `integration/c51b-vibrator` without reset
or reimplementation. The timed-only backend now uses the verified Linux LED
`oneshot` protocol, never brightness-on fallback. Fault/retry/lifecycle handling
and the request policy were hardened. Code refuses discovery/I/O/registration
while `deploymentAllowed()` is false; init is also disabled+oneshot. Keep the
module and fragment unselected: source disable alone is not product integration.

Recorded C51B gate: **94/94 Python checks**, original native **12/12** and new
lifecycle/protocol **17/17**, both normally and ASan/UBSan; new **17/17 TSan**.
The real SDK37 aidl compiler generated frozen V2 headers from the authentic
platform source/hash; real Android Clang22/Bionic compiled **5/5 arm64 objects**.
No fake Binder header/class was used. **Not linked, Soong-built or IPC-tested.**

Reproduce the independent real-interface/object probe (read-only existing C52
platform, outputs created/removed only under this project's ignored `.tmp/`):

```sh
PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 python3 -B \
  tests/android_adapter_probe.py /mnt/SamsungSSD/android/lineage-24.0
```

A real isolated targeted Soong request exited 1 at missing
`build/soong/config/main.star`. DeepSeek C53 owns repair and source wiring; its
source, outputs and active research were not modified. Kernel ONESHOT availability,
driver lifetime, safe duration policy, real sysfs permissions, stock Manager
compatibility and hardware behavior still block deployment. See source-owner
READMEs, `reports/INTEGRATION-READINESS.md` and the updated **unmerged C51B**
`docs/RESEARCH-HANDOFF.md` for exact evidence/next actions.

## C51 baseline (historical)

The existing validator is reused. One real timed vibrator source implementation now lives in `android/hardware/ulefone/gq5012bf1/vibrator/`, using the native backend in `android/hardware/mediatek/mt6878/vibrator/`. These are existing source owners, not new checkouts. The source owner READMEs contain exact activation requirements and the process-death timeout safety blocker. Device/vendor activation is not applied.

Frozen C51 scan: 80 contracts (79 historical + one new source fragment), one source-mapped service, 77 historical init relationships still `MISSING_METADATA`, and all 48 explicit override overlaps reviewed as intentional at source level. `init_relationships` and `vintf_review` provide individual classifications without a fake libvintf PASS. Helper rc processes are not automatically assumed to be HAL servers. Static `validation_properties` do not infer executed unit/Soong/VTS/hardware results; actual receipts are in the research handoff.

C51 native backend tests pass 12/12 normally and under ASan/UBSan; the full Python suite passes 90/90 (original 78 + 12 new). The genuine Android Binder adapter is not compiled: target Soong/generated NDK headers are absent. No counterfeit generated header is used.

`tests/fixtures/IVibrator-V2.aidl` is an **UPSTREAM_ORIGINAL** immutable API test snapshot, Apache-2.0 with AOSP notices retained, from LineageOS `android_hardware_interfaces` commit `13fc23dae0dcd24fc2411d74f54a407999eaf555`; SHA-256 `51161792eba95aee28a92723a1430b235e57e75751c24db04d84f7d83cca318e`. The full required license text is preserved alongside it in `tests/fixtures/LICENSE.apache-2.0`. It is not a local AIDL module or a duplicate HAL implementation.

## Run without installing

From this directory:

```sh
export PYTHONPATH="$PWD/src"
export PYTHONDONTWRITEBYTECODE=1
python3 -B -m lieppos_hal_audit.cli --root /path/to/approved/source
```

Omitting `--output` is a summary-only dry run. With `--output`, only that **disjoint** report directory is written. Inputs are always read-only. Repeat `--root`; symlinks are never followed. Do not give a filesystem-wide root.

### Historical C51 report invocation

```sh
PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 python3 -B -m lieppos_hal_audit.cli \
  --root /home/armol/LieppOS/android/device/ulefone/gq5012bf1 \
  --root /home/armol/LieppOS/android/vendor/ulefone/gq5012bf1 \
  --root /home/armol/LieppOS/android/vendor/mediatek/mt6878 \
  --root /home/armol/LieppOS/android/vendor/lieppos \
  --root /home/armol/LieppOS/android/hardware/mediatek/mt6878 \
  --root /home/armol/LieppOS/android/hardware/ulefone/gq5012bf1 \
  --gq5012bf1 \
  --runtime-properties /mnt/SamsungSSD/lieppos-c46/hardware-approved/live-slotb-getprop-1.txt \
  --output "$PWD/reports"
```

**The committed machine reports remain the C51 snapshot** (tools baseline
`80545f8775e0695840a7640bb16faddc8be0f845`). Do not run the historical export above
to refresh C52/C53-owned inputs during this focused continuation. Only the
vibrator readiness interpretation is updated by C51B; the original 77 unresolved
relationships, 48 override reviews and other inventory rows are preserved.
A future explicitly requested fresh CLI scan sees current sources and will differ.

The optional historical getprop file is an existing, explicitly supplied evidence file, **not a live phone query**. Omit that option when unavailable; runtime evidence/counts will then differ. `--gq5012bf1` enables a filename/evidence-gated device coverage lens, including undeclared hardware artifact references. It does not manufacture interface names or versions from filenames.

Outputs:

- `reports/HAL-INVENTORY.json`: versioned envelope, inventory rows, raw declarations, diagnostics, literal module links, extraction metadata, source hashes, policy/permissions/kernel references and sanitized historical service states.
- `reports/HAL-INVENTORY.csv`: the required sixteen-column inventory projection.
- `reports/SCAN-SUMMARY.md`: generated human-readable scan summary.
- `reports/INTEGRATION-READINESS.md` and `reports/OPEN-SOURCE-HAL-ROADMAP.md`: reviewed interpretation; the CLI does **not** overwrite these.
- `docs/RESEARCH-HANDOFF.md`: the single research handoff; no duplicate research checkout.

Exit codes: `0` scan finished (**not compatibility PASS**); `1` diagnostics with `--fail-on-diagnostics`; `2` invalid/unsafe arguments or output/runtime I/O failure. Unavailable source roots are reported as `ROOT_UNAVAILABLE`, not silently treated as working hardware.

## Interpretation

A record is either a concrete declared interface/version/instance/format, or an explicitly unknown contract backed by a hardware executable/app reference. These populations must not be added together and called distinct HALs. Duplicate raw declarations are retained with provenance; inventory contracts are grouped by full interface, instance, format and version. All roots are discovery scope, **not** an evaluated product selection.

`properties` in JSON separates independent evidence:

| Property/status | Meaning |
|---|---|
| `DECLARED` | Found in a VINTF manifest, not a compatibility matrix. Does not prove it is installed. |
| `IMPLEMENTED_IN_SOURCE` | Exact fragment/module relationship with resolved in-scope literal source references. Source semantics, compilation and functionality remain unverified. |
| `PROPRIETARY_IMPLEMENTATION` | In the device lens, a retained hardware artifact in `proprietary-files.txt`; **extraction provenance only**, not confirmation the binary is present. |
| `SERVICE_PRESENT` | No static filename inference. Unknown without registration/runtime presence evidence. |
| `SERVICE_STARTED` | Historical `init.svc` evidence for an exact documented process reference; not interface registration or hardware operation. |
| `HARDWARE_VERIFIED` | Unknown unless explicit operation-test evidence is supplied; this audit supplies none. |
| `MISSING` | Not asserted globally from partial source roots. |
| `UNKNOWN` / `NEEDS_PLATFORM_VALIDATION` | Insufficient evidence; never a fabricated PASS. |

JSON `null` means unknown, not false. `EXTRACT_ONLY` is **not an install rule** and is not automatically proprietary-only: intended source replacements may exist elsewhere. Blueprint `PREBUILT_REFERENCE` also does not establish a proprietary license; `prebuilt_etc` is configuration, not proprietary implementation code. `source_repository` denotes the supplied source ownership root when linked, not a verified remote/commit. Byte SHA-256 provenance is the stable source identifier; shared Git metadata is not inspected.

`init_service` on an unknown-contract artifact can be a stock-init comment reference (see notes and `init_reference`); only `init_definitions` contains parsed `.rc` definitions. Library HALs and passthrough HALs are not automatically standalone services. Filename matches remain binary **candidates**, never exact interface-to-service bindings. Firmware and DT_NEEDED names are metadata references, not inspected binaries.

## What is implemented / deliberately not implemented

- Safe recursive bounded UTF-8 text discovery; VINTF HIDL fqnames and structured interfaces, AIDL fqnames/instances, omitted AIDL version default 1; explicit invalid/ranged versions remain unknown.
- Init services, executable paths, interface options, labels/users/groups and disabled state; imports/actions are never executed.
- Conservative Blueprint top-level literal properties with brace/string/comment handling; C/C++/Java and shell module source references, stems, init and VINTF links. Dynamic values, generated/filegroup/out-of-scope sources are unresolved.
- Extraction list source/destination/module/hash/options/symlink references, EXTRACT_ONLY and annotated DT_NEEDED consumers; no extraction or blob inspection.
- Literal SELinux file-context matching plus separate policy references; permission and kernel-ABI reference recording. Arbitrary file-context regexes are not executed.
- Duplicate, override-overlap, potential AIDL/HIDL coexistence, multiple-version, unresolved implementation/init, missing explicit init-registration VINTF, and executable-reference diagnostics.
- Deterministic JSON/CSV/Markdown, with internal **shape validation**, not a general JSON Schema implementation.

Not implemented: Soong/Make evaluation, defaults/arch/product selection, full Blueprint grammar, generated modules, VINTF partition/SKU/APEX merge and override semantics, matrix range satisfaction, HIDL inheritance, VTS, SELinux compilation/neverallow checks, ELF ABI verification or hardware tests. Missing diagnostics always mean **unresolved in this scan**, not proven absent on the device. `OVERRIDE_OVERLAP` is not a duplicate failure. `POTENTIAL_AIDL_HIDL_CONFLICT` may represent intentional coexistence.

No safely available `checkvintf` or `assemble_vintf` was found in non-symlink PATH directories during this task. No platform tools were downloaded or built. Use the actual Android 17 platform tools against owner-provided assembled partition metadata later.

## Safety

Inputs are opened through directory file descriptors with `O_NOFOLLOW`; output paths/files also reject symlinks and hardlinks. Protected paths are rejected lexically without inspecting them. Text is capped at 2 MiB/file, recursion at 64 directories. Binaries, private-key extensions, sensitive filenames, firmware/calibration/NVRAM/key directories, `.git`, `.repo`, kernel trees and common build/cache directories are skipped. Only whitelisted source/config/text extensions and selected filenames are opened. No input writes or source subprocess execution occur. Arbitrary source text should still be treated as untrusted metadata, not a compatibility certificate.

## Tests

```sh
# Portable synthetic/classifier suite: 81 passed; thirteen local checks skipped.
PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover -s tests -v

# Explicitly opt into the six authorized roots and documented C46 evidence:
LIEPPOS_REAL_SOURCE_TESTS=1 LIEPPOS_C51_SOURCE_TESTS=1 \
  PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 \
  python3 -B -m unittest discover -s tests -v
# C51B recorded result: 94/94 passed, no skips (12-case suite twice,
# 17-case suite normal + ASan/UBSan + TSan).
```

Tests use temporary files only under ignored `.tmp/` in this project and remove them. No caches/build outputs belong in Git. See readiness for the observed results and unresolved device integration questions.
