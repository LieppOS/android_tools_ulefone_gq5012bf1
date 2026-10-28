# Research handoff: Android 17 HAL/VINTF audit

## Import boundary

Prepared only in `tools/ulefone/gq5012bf1/hal-audit/` on the existing tools repository's local `integration/codex-hal-vintf` branch. This is the **single** handoff for later integration into `LieppOS/LieppOS-ulefone-gq5012bf1-research` / `research/ulefone-gq5012bf1/` after DeepSeek finishes. Do not copy a research checkout or replace `inventory/subsystems.csv` with this derived HAL inventory. No active research, kernel/module, device/vendor, manifest, shared-doc or canonical-inventory file was modified.

No phone operations, Android/kernel builds, flashing, source execution, proprietary executable copying, private-key/calibration access or GitHub push occurred. The initially authorized temporary Codex directory was moved into the corrected ownership location and removed as an external directory; no duplicate checkout was created.

## Verified findings to integrate

1. Six explicit Android roots yielded 132 hashed text files. Both designated vendor implementation roots and both designated hardware implementation roots contain no implementation files. Actual device configuration and LieppOS helper sources are present; a complete Android HAL source tree is not.
2. Five available VINTF XML files contain **127 occurrences / 79 unique interface-instance-format-version contracts**, across 43 package families. Another **44** artifact/app records have unknown native contracts, giving **123 derived inventory rows**. The extra rows must not be called 44 discovered interface implementations.
3. `device/ulefone/gq5012bf1/BoardConfig.mk:240-245` selects the five manifest inputs. `device.mk:118` requires a generated vendor product file absent from the empty vendor root; BoardConfig's generated vendor include is at line 248. Full-ROM source integration remains incomplete.
4. `vintf/manifest.xml:24` declares HIDL audio 7.1/default; line 34 declares Bluetooth HCI 1.1/default; line 39 declares passthrough mapper 4.0/default. `vintf/gnss-default.xml:2` declares AIDL GNSS v3/default. `vintf/fingerprint-example.xml:2` declares AIDL fingerprint v3/**virtual**, not verified physical authentication.
5. **48 overlaps are explicit ODM overrides**, not confirmed duplicate failures. One potential mixed-transport coexistence review concerns `vendor.mediatek.hardware.aee.IAee/AEE` at `vintf/manifest.xml:121,127`. Real libvintf/SKU/partition assembly is required before changing either.
6. The extraction list contains 50 vendor VINTF fragment references, 122 vendor init rc references and 52 hardware executable references. Their names/comments are not parsed fragment/init bodies. BoardConfig's 49-fragment comment differs from the current list count. All counts include EXTRACT_ONLY entries where applicable.
7. **Zero** declared contracts are mapped to local HAL server source. Five source-built helpers/clients exist, including the Java tinylcd client and native rear-input/touchscreen helpers; none is an open tinylcd server. No proprietary-only global source-unavailability conclusion was reached. The 36 retained artifact rows classified proprietary are extraction-provenance references, not license or runtime findings.
8. Thermal-camera evidence is an `M170infisens` APK import (`vendor/lieppos/energy_tc2c/Android.bp`) plus permission defaults. The native interface is UNKNOWN. It must not be conflated with the Android thermal-management HAL.
9. `vendor/lieppos/apps/TinyScreenService/src/com/lieppos/tinyscreen/TinyLcdHal.java:24-25` contains the client token `vendor.yft.hardware.tinylcd@1.0::ITinylcd/default`. Transaction comments are not independent runtime ABI verification. `apps/TinyDisplay/daemon/tinydisplay_touch_daemon.cpp` references `/dev/input`, rear touch and YFT key inputs. Camp-light sysfs references are carried **patch** evidence, not proof those patches are applied.
10. `vendor/lieppos/lieppos.mk:38-43` configures a Lineage charging-control path/package. `sepolicy/service_contexts:1-2` labels Lineage `IChargingControl/default` and `IFastCharge/default`; these labels do not establish service registration. Device battery/TrustKernel policy is source evidence only; no policy compile or HAL operation test occurred.

Paths above are relative to `/home/armol/LieppOS/android/` unless otherwise stated. All exact contract instances, candidate binary/DT_NEEDED metadata, source lines, policy/permission/kernel references and raw-byte source hashes are in `../reports/HAL-INVENTORY.json`. CSV is the required sixteen-column projection, not a new canonical subsystem inventory.

## C46 evidence, exact scope

Existing documented evidence was read from:

`/mnt/SamsungSSD/lieppos-c46/hardware-approved/live-slotb-getprop-1.txt`

Byte SHA-256: `442b75bded935b46dd3fa473bc1d706339d0bc27f84a516bc3b919bee82a5a45`.

- Lines 862 / 865: Android 17 / SDK 37.
- Line 898: `24.0-20261002-UNOFFICIAL-gq5012bf1`.
- Line 1250: `sys.boot_completed=1`.
- Lines 223 / 228 / 299: bootanim / camerahalserver / tinylcd_hal recorded running.

JSON retains only allowlisted version/boot/init-state properties, original line numbers and the raw file hash. It does not copy the raw getprop log or device identifiers. Eleven unknown-contract process-reference rows have historical running-state associations; no HAL is HARDWARE_VERIFIED and no binder/HIDL registration dump was available in the inspected authorized inputs.

`/home/armol/LieppOS/docs/integration/ACTIVE-BUILD-PROVENANCE.md:74-85` binds this result to C46 and records the userdata key-upgrade incident:

- C46 `vendor_boot_b`: `fee66502411e57c958cff58021e7379f6a2f0cd05b061738ac0469974360bfb6`.
- C46 `vbmeta_b`: `29c29463bf8bed9cbe3efdf7d0d985c852d30acf4f22a098c190c1043e3ae9ea`.

These image hashes are **quoted from the authorized provenance document**, not newly computed image hashes; no ROM image was opened. Boot completion applies only to that recorded image set. It does not validate the current device product or any individual HAL. Existing unresolved display behavior is not investigated here. Future hardware planning must account for the documented cross-version shared-userdata/TEE key safety issue.

## Source provenance anchors

Shared Git metadata was not inspected; byte hashes, not assumed clean-tree commits, identify the reviewed files. Full hashes for all 132 source inputs are embedded in the JSON. Stable repeated scans were used instead of duplicating source trees.

| File (relative to `/home/armol/LieppOS/`) | Raw-byte SHA-256 |
|---|---|
| `android/device/ulefone/gq5012bf1/BoardConfig.mk` | `14aee8d1649ab042b4539a543ab2ecafdb185d781bdffb3f346e6eb71e6e4f56` |
| `android/device/ulefone/gq5012bf1/device.mk` | `7c05ccb30797a74f8b2a15827ac6cab0a0fb79fe6201b38f514f028939d75093` |
| `android/device/ulefone/gq5012bf1/proprietary-files.txt` | `cc9c2f359a9e6395915e2fd0356ec0acb8c14ded6d9dba270ec110f0961169b8` |
| `android/device/ulefone/gq5012bf1/vintf/manifest.xml` | `b0acd338fbc5aeccc220f50724daaa95d5a812486181336ce0e9aecc134cb1d3` |
| `android/device/ulefone/gq5012bf1/vintf/manifest_dsds.xml` | `97e655265d566cb582f0414b00431b69ddb7d57cb798cfef2a1af6ca1122f2ed` |
| `android/device/ulefone/gq5012bf1/vintf/fingerprint-example.xml` | `39393ef729b0511b025d05bf5e9fb6428675dd813475a950b68d129b1a6517c9` |
| `android/device/ulefone/gq5012bf1/vintf/gnss-default.xml` | `34c9966b5dc344760c5206f9a5a884b1e9293a287db2bbea2651700622e1d8d3` |
| `android/vendor/lieppos/lieppos.mk` | `a2efc2f87b9beaa46ca22e9c033d99fc79652141c31a865908a76a3512ca7322` |
| `android/vendor/lieppos/apps/TinyScreenService/src/com/lieppos/tinyscreen/TinyLcdHal.java` | `559b1ec3bfe469c0aa0aa9ee59f7de3e1b56b3db0c62887a93de3f6681b65bb3` |
| `docs/integration/ACTIVE-BUILD-PROVENANCE.md` | `ffb173ce0ee4c7f38d60ff5e99125c4b8c93883f0dc49f8bbc70ac8174c695a5` |
| `inventory/subsystems.csv` | `cbf319db9a9b990983732c3c911bdede5e8272a1486514b3547285d8fb8d2ff0` |

The canonical CSV uses CRLF. Its normalized-text hash differs; the table deliberately uses raw-byte SHA-256. No copy of that CSV is included.

## Reproduction and test receipt

Use the exact six-root CLI invocation in `../README.md`. `--output` writes only the owned reports; omit it for a read-only summary. The C46 properties argument is optional; omitting it changes historical evidence fields/counts. No phone connection is attempted.

```sh
cd /home/armol/LieppOS/tools/ulefone/gq5012bf1/hal-audit
LIEPPOS_REAL_SOURCE_TESTS=1 PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 \
  python3 -B -m unittest discover -s tests -v
```

Actual result: **78/78 passed**, no skips (73 synthetic/unit/CLI tests + five real-source tests). Tests cover XML, duplicates/overrides/coexistence, partial source/proprietary distinctions, JSON shape/CSV, CLI, no source execution, filtering, no-follow/hardlink output safety and source hash/mtime/mode preservation. No generic JSON Schema, Soong, libvintf or policy compilation PASS is claimed.

Two complete report exports with unchanged source inputs produced byte-identical JSON, CSV and Markdown:

| Generated report | SHA-256 |
|---|---|
| `HAL-INVENTORY.json` | `ab5dfbe1a040857ebfb89c9210cd2928aadaf5d70192e51f3b2390bb49378409` |
| `HAL-INVENTORY.csv` | `2e9d85efe08d651e05e5b931c4b26d46183ba72001720b5854a0e3e171081765` |
| `SCAN-SUMMARY.md` | `f1c82e9cff44d6ef1dcfbf53ff9b49d3e42c20165502f3c997117111b38a6a84` |

## Unknowns and next owner decisions

- Missing real fragment/rc bodies, generated vendor integration, actual product/SKU selection and exact Android 17 matrices prevent platform compatibility certification. Main target-level 8 / sepolicy 34.0 versus shipping API 35 needs reconciliation, not arbitrary rewriting.
- 77 non-passthrough init relationships and 66 implementation relationships are unresolved **within the supplied roots**, not proven missing on the historical phone image.
- No safely available checkvintf/assemble_vintf was found in non-symlink PATH directories; no platform was downloaded/built.
- A carried patch over 2 MiB was deliberately skipped and identified in the scan diagnostics.
- Globally verified replacement source availability, firmware/TEE matching and per-subsystem operation remain unknown. Consult the roadmap before implementation work; no reverse-engineering recommendation is made until existing implementations are ruled out.

After the active research owner is ready: import this concise finding narrative and reference the specialized tool/reports at their tools repository location, preserving hashes and uncertainty. Do not import raw proprietary artifacts, duplicate source/checkouts, or silently promote declaration/process evidence to verified hardware support.
