# Android 17 / GQ5012BF1 integration readiness

**Result: PARTIAL integration evidence; working static validator. Not Android compatibility certification.**

Device context: Ulefone Armor 29 Pro Thermal / GQ5012BF1, MT6878T, Android 17 / LineageOS 24.0, custom 6.1.115-based GKI campaign. No kernel/module work, Android build, ROM modification, flashing or phone access was performed by this audit.

## Observed totals

| Population | Observed result |
|---|---:|
| Explicit Android source roots scanned | 6 |
| Eligible text files hashed | 132 |
| Actual VINTF declaration occurrences | 127 |
| Unique interface + instance + format + version contracts | 79 |
| Distinct declared package families | 43 |
| Additional artifact/app records with unknown native contracts | 44 |
| Total inventory records (not a count of distinct HALs) | 123 |
| Concrete declared contracts mapped to local HAL server source | 0 |
| Source-built helper/client modules, not HAL servers | 5 |
| Records with proprietary extraction references/candidates | 56 |
| Retained extraction artifact records without local source | 36 |
| Records with `implementation_status=UNKNOWN` | 87 |
| Confirmed globally proprietary-only implementations | UNKNOWN |
| Hardware-verified HALs | 0 |
| Historical started-process reference records | 11 |

The 36 retained artifacts are classified `PROPRIETARY_IMPLEMENTATION` **only at extraction-reference provenance scope**. This does not prove a proprietary license, binary presence, exclusive unavailability of upstream source, service registration, or operation. For example, vendor-retained hostapd/wpa_supplicant artifacts have upstream open-source families; their device-specific source correspondence is unverified. All 79 declared contracts still lack a verified runtime interface binding in this audit. The additional 44 records deliberately retain unknown interface/version/instance instead of deriving them from executable filenames.

## Actual input availability

Paths below are relative to `/home/armol/LieppOS/android/`.

| Root | Eligible text files | Finding |
|---|---:|---|
| `device/ulefone/gq5012bf1` | 19 | Five VINTF XML files, product/board configuration, extraction metadata and device policy. No HAL server source. |
| `vendor/ulefone/gq5012bf1` | 0 | No integration implementation files found. |
| `vendor/mediatek/mt6878` | 0 | No integration implementation files found. |
| `hardware/mediatek/mt6878` | 0 | No HAL implementations found. |
| `hardware/ulefone/gq5012bf1` | 0 | No HAL implementations found. |
| `vendor/lieppos` | 113 | Apps/helpers, policies, configuration and patches with unknown application status; not a complete platform checkout. |

One vendor patch exceeded the documented 2 MiB text cap and was not parsed: `patches/personal/device_phh_treble/0001-Revert-treble-add-pixel-charger-2-3.patch`. This is explicit scan coverage loss, not a HAL failure. Binaries/prebuilt kernel/images/APKs, firmware and calibration material were not read/copied.

`device.mk` requires `vendor/ulefone/gq5012bf1/gq5012bf1-vendor.mk`; `BoardConfig.mk` refers to generated `BoardConfigVendor.mk`. Those generated integration files are not available in the empty vendor root. The extraction list is **not** evidence they have been generated or that blobs are installed. No full-ROM build readiness is claimed.

## VINTF and service findings

| Diagnostic | Count | Correct interpretation |
|---|---:|---|
| `OVERRIDE_OVERLAP` | 48 | Exact vendor/ODM DSDS contract overlaps, with `override="true"` in `manifest_dsds.xml`. Not 48 confirmed duplicates. Requires real libvintf merge/partition/SKU selection. |
| `POTENTIAL_AIDL_HIDL_CONFLICT` | 1 | `vendor.mediatek.hardware.aee.IAee/AEE`: HIDL 1.1 and AIDL default-version 1 appear together in `manifest.xml` at HAL anchors 121 and 127. May be intentional coexistence. |
| `DUPLICATE_HAL` | 0 | No non-override duplicate identity groups in this scan. |
| `MISSING_IMPLEMENTATION_IN_SCAN` | 66 | No exact source link or filename binary candidate found for these contracts. Shared processes and omitted generated/vendor trees remain possible. |
| `MISSING_INIT_IN_SCAN` | 77 | All non-passthrough contracts lack exact parsed init/module relationships in supplied roots. Not proof the tested vendor image lacked those services. |
| `MISSING_EXECUTABLE_REFERENCE` | 0 | All three actually parsed helper init services have local module/source references. |
| `MISSING_VINTF_IN_SCAN` | 0 | No parsed helper init service explicitly advertises a HAL interface; this is not proof every installed HAL has a declaration. |
| Malformed XML / unknown explicit versions | 0 / 0 | Five available manifest files parsed; absent fragment bodies cannot be evaluated. |

The extraction list contains **50 vendor VINTF fragment filenames** (41 retained, nine EXTRACT_ONLY) and **122 vendor init `.rc` references**. Their bodies are absent in the available vendor source roots. The BoardConfig comment mentioning 49 fragments is not an authoritative count of the extracted list or installed image. The list contains **52 hardware executable references** (seven EXTRACT_ONLY). Filename and stock-init comment discovery must not be promoted into parsed XML or init service definitions.

### Verified concrete declarations

- Audio: HIDL `android.hardware.audio.IDevicesFactory`, 7.1/default; effects factory 7.0/default. DSP/ALSA/vendor backend source remains unknown.
- Bluetooth: HIDL `android.hardware.bluetooth.IBluetoothHci`, 1.1/default. Two differently named Bluetooth service artifacts are extraction candidates, not proof of a conflicting active installation.
- Graphics mapper: HIDL 4.0 `IMapper/default`, passthrough. RenderScript 1.0 is also passthrough: neither is automatically a standalone init service.
- Radio: AIDL interface families with real slot/IMS/SE instances retained exactly in JSON/CSV; DSDS override entries must be merged, not counted as new physical radios.
- GNSS: AIDL `android.hardware.gnss.IGnss`, version 3/default.
- Fingerprint: AIDL `android.hardware.biometrics.fingerprint.IFingerprint`, version 3/**virtual**. This is not a verified physical Microarray fingerprint implementation. The extraction list separately references `microarray.fingerprint.default.so`.
- Numerous MediaTek service contracts are present, including camera adjuncts and composer extension. They do not substitute for the unavailable camera-provider/composer fragment bodies.

The graphics composer executable name contains `@3.2`; this audit intentionally **does not turn that filename into an interface/version claim**. Likewise allocator, NFC, KeyMint, boot control, USB and thermal fragment contracts remain unknown until their actual XML is available.

## Source and device feature coverage

The complete minimum checklist is represented in JSON `coverage` (24 groups: the requested security/DRM group is split for clarity) and the roadmap. Integration configuration supports investigating all requested subsystems; it does **not** establish that every service is Android-mandatory or physically working.

Five source-built helper/client modules were found:

1. `TinyDisplayTouchDaemon`: C++ input reader, literal init service and `tinydisplay_touch_daemon` label.
2. `TinyScreenService`: Java client/power-off wrapper for `vendor.yft.hardware.tinylcd@1.0::ITinylcd/default`; **not the server**.
3. `lieppos-touchscreen-grabber`: C++ input helper with init reference.
4. `toggle_touchscreen.sh`: source shell helper, never executed by this audit.
5. `lieppos-microg-location-defaults.sh`: source shell helper with init reference, not a hardware HAL.

The thermal-camera integration contains an `android_app_import` for `M170infisens.apk` and app permission defaults. No thermal-camera native contract or source implementation was reconstructed. Android thermal **management** is a separate subsystem; the thermal camera is not assumed to use that HAL.

Programmable buttons/rear touch use source references to `/dev/input`, `hyn_ts` and `yft-gpio-keys` in the auxiliary-display helper. Camp-light ABI paths appear in vendor-carried patches (`yft_camplight/leds_ctl`, `power/control`, `camplight_mode`, `camplight_set_brightness`). Patch presence does not prove application or hardware operation. A dedicated Android-standard programmable-button HAL is not inferred.

## SELinux, permissions and kernel contracts

- Device policy defines TrustKernel device types and rules for `tee`, `hal_keymint_default` and `hal_gatekeeper_default`, plus RPMB/storage policy references. No private key or protected store contents were read. Exact live node availability, executable domains and Android 17 policy compatibility remain unverified.
- Device `genfs_contexts` includes power-supply/charger labels. LieppOS configuration references `/sys/class/power_supply/mtk-master-charger/input_current_limit`, and its separate `hal_lineage_health_default` policy permits battery-info access.
- `vendor.lineage.health.IChargingControl/default` and `IFastCharge/default` appear in **service_contexts**, not verified VINTF/service registration evidence. Do not conflate Lineage charging control with `android.hardware.health`.
- Auxiliary input code has an explicit init seclabel and policy rules. Installed executable labels, transitions and app Binder/input permissions need compiled-policy validation; no daemon executable path mapping was found in the supplied LieppOS file_contexts.
- Thermal app CAMERA/RECORD_AUDIO/media-storage permissions are configuration evidence only. NFC/fingerprint/sensor feature XML references do not establish hardware function.
- Many device-specific kernel ABI dependencies remain UNKNOWN. The report records known source/configuration/patch references and labels their scope; it does not copy kernel ownership claims or repeat C49 driver-source investigations.

## Historical C46 evidence: narrow interpretation

The existing documented external file `live-slotb-getprop-1.txt` has byte SHA-256:

`442b75bded935b46dd3fa473bc1d706339d0bc27f84a516bc3b919bee82a5a45`

Selected properties show Android release 17, SDK 37, Lineage `24.0-20261002-UNOFFICIAL-gq5012bf1`, and `sys.boot_completed=1`. It also records `bootanim=running` and individual process states. JSON preserves only allowlisted properties and their original line numbers, not serial numbers or the raw log.

Processes including `camerahalserver`, `tinylcd_hal`, `nfc_hal_service`, `thermal_core` and `fuelgauged` were recorded running. That does not establish provider registration, valid camera frames/thermograms, NFC transactions, charging correctness, or other operations. The current workspace source is not proved identical to that historical userspace image.

`docs/integration/ACTIVE-BUILD-PROVENANCE.md` ties the C46 result to its exact image set and records an unresolved display loop. It also documents shared-userdata key upgrades and stock Android 15 decryption failure after the Android 17 boot. Any later owner-approved hardware test must account for that safety constraint. No such test was attempted here; no display debugging was performed.

## Android 17 framework/vendor compatibility questions

1. Available main manifest declares `target-level="8"`, sepolicy 34.0; product configuration declares shipping API 35 on supported modern branches. Reconcile these historical/source values with the actual shipping FCM, vendor image and Android 17 framework matrices. Do not simply raise the level or mandate AIDL everywhere.
2. Assemble selected vendor/ODM/SKU/APEX manifests, including generated source-replacement fragments. Check true override/coexistence behavior and framework/device matrix compatibility using **the target platform tools**.
3. Resolve EXTRACT_ONLY replacements for health, Wi-Fi, sensors multihal, IR, face/ClearKey and associated fragments/init files. A product package reference is not imported implementation source or proof of correct device adaptation.
4. Verify stable-AIDL versions/hashes and HIDL passthrough support in the actual Android 17 build. Generic current AOSP documentation is not a frozen LineageOS 24 compatibility matrix.
5. Validate the virtual fingerprint declaration against intended physical service exposure and remove/replace only after verified implementation planning by the configuration owner.
6. Validate vendor-library ABI/runtime dependencies, Soong/product installation, service-manager contexts, policy compilation/neverallows and VTS against the intended image set. No such platform validation was available here.

No safely available `checkvintf`/`assemble_vintf` executable was found in non-symlink PATH directories. None was downloaded/built.

## Tests and reproduction evidence

- **78/78 tests passed**, no skips with `LIEPPOS_REAL_SOURCE_TESTS=1`: 73 synthetic/unit/CLI tests plus five real-source integration tests.
- Includes XML parser cases, duplicate/override/conflict tests, partial/malformed sources, proprietary and prebuilt distinctions, source/permission/kernel references, JSON shape and CSV validation, CLI smoke/dry-run/strict modes, no-execution tests, secret/binary filtering, symlink/hardlink/output isolation and read-only metadata checks.
- Repeated real scans compare byte-equivalent sorted JSON and CSV in memory, source hashes and source mtimes/modes. Exported JSON/CSV/Markdown were also regenerated and compared for deterministic content (see handoff for final hashes).
- No general JSON Schema engine is claimed; internal report-shape checks are implemented and tested.
- Real vendor and available source-helper inputs were scanned. No local open-source device HAL server project was available in the four designated vendor/hardware roots; source helpers are not counted as HAL servers.

## Next actions (configuration/platform owners; not performed here)

1. Provide sanitized existing vendor/ODM manifest fragments and init/configuration text, with hashes, without copying secrets, calibration data or proprietary executable payloads.
2. Reconstruct exact service/module/registration relationships; identify any already-existing matching open-source implementation before considering new implementation work.
3. Obtain the actual target Android 17 matrices/tools and evaluate the assembled image metadata, source replacement selection and policy integration offline.
4. Use the subsystem roadmap for staged source adoption; maintain vendor-specific firmware/TEE compatibility boundaries.
5. Plan separately approved per-subsystem operation tests on a precisely identified safe image set. Record negative and unknown results instead of extrapolating from boot completion.

Canonical inventory/research remain untouched. See `../docs/RESEARCH-HANDOFF.md` for import-ready references and source provenance.
