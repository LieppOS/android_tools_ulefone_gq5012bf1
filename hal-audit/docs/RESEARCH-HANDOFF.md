# C51C — vibrator kernel timeout research handoff

**NOT YET MERGED by Codex into the C54-owned canonical research worktree.**
Destination: `research/ulefone-gq5012bf1`
(`LieppOS/LieppOS-ulefone-gq5012bf1-research`). DeepSeek owns C54 vendor/policy/
research; none of those source/branch/output trees was modified by this campaign.
No new repository, checkout, Android tree, phone operation or push.

This replaces the current handoff with focused C51C evidence, not a new audit.
Complete historical C51/C51B handoffs remain in tools commits80545f8/df8ea6b;
C52/C53 report their previous summaries were integrated. Frozen C51 JSON/CSV/
SCAN-SUMMARY remain byte-identical; 77 relationships were not reopened.

## Ownership, source revisions and provenance

Kernel recovered clean at C50 `27a31fbc7a70b13efd74b50721147e44f8914e84`, branch
integration/c49-hardware-source-expansion; Ulefone mirror clean at
`0e00dda7f53fedd8b83092aca5c3b96542bf255f`, byte-identical old vibrator source.
The user explicitly confirmed **exclusive kernel + mirror write ownership**.
Dedicated local branches: `integration/c51c-vibrator-timeout`; no protected C48
publication branch or C50 history was rewritten. Other agents' trees stayed
read-only. Canonical combined-kernel-first / provenance-mirror rules were read.

| Owner | C51C commit |
|---|---|
| Kernel | `af3ecd85d28614c2ad25c6448cd68634d62c6a33` |
| Ulefone module provenance mirror | `b23e82b4deda06d96e84ca3bb84de5e1e1fc11b8` |
| MediaTek HAL | `efae973a60b67bf0df31380eea83b25f3e8f5f0a` |
| Ulefone HAL | `72617cde4e647ac908539952fcd7c4f821d94d04` |

Tools changes descend from C51B `df8ea6b640e97b1f131c6c4f747c505717936da8`;
the commit containing this handoff is identified in the final completion receipt.
Kernel driver keeps MediaTek's GPL-2.0 notice, with independent LieppOS additions;
private policy/test code is GPL-2.0. HAL additions remain independent Apache-2.0.
No firmware, calibration, secret, copied Binder stub or private key was introduced.
Mirror sync covers **only driver + private header**, with updated per-file hashes,
counts and scoped canonical commit in SOURCE-MANIFEST.json. Other paths remain
based on the original C48 snapshot; mirror is not an independent build root.

## Actual configuration and decision

The real C48/C50 build script copies **configs/c44-reference.config**, SHA256
`40de208ba474abfac862ada26301d5a8b26490141e8c944ed303a3ccce8fd2fc`.
It explicitly has REGULATOR_VIBRATOR=m, ONESHOT unset, CFI_CLANG=y,
MODVERSIONS=y, MODULE_SIG=y, MODULE_SIG_ALL unset. Output olddefconfig is
**byte-identical**, not merely feature-equivalent.

The C51B proposal patched gki_defconfig (SHA2566416f396...), not that recipe's
input. It is now marked SUPERSEDED/DO NOT APPLY, retained only as history/test
fixture. LED one-shot code exists, but config enable alone would not fix the old
driver's swallowed regulator errors, unbounded brightness path, workqueue leaks,
remove/suspend races or per-trigger attribute recreation/DAC race.

**Selected Option B only:** driver-owned timeout. No generic trigger/core/config
change, new core export, DT label, voltage, PMIC timer or hardware rating guessed.
Implementation and ABI are authoritative at the kernel commit above:

- `drivers/leds/regulator-vibrator.c`
- `drivers/leds/regulator-vibrator-state.h`
- `Documentation/ABI/testing/sysfs-class-led-regulator-vibrator`

## Kernel behavior and failure model

Static LED attributes exist for the class-device lifetime: `timeout_abi=1`,
`max_duration_ms=5000`, atomic `duration_ms`, `last_error`. Positive duration
1..maximum starts; 0 cancels/acknowledges recovered fault. Invalid/overflow input
leaves the previous bounded request unchanged. Read remaining time is a requested
state, NOT motor/current measurement. The ceiling is **provisional SOFTWARE
policy, NOT a validated physical continuous-on/thermal limit**.

- CLOCK_BOOTTIME hrtimer is armed before regulator enable. Callback only queues
  kernel work; sleeping regulator operations and all requests use one mutex.
  Regulator notifier only records an atomic fault and queues work (no recursive
  regulator calls/request-lock acquisition).
- Old queued expiry checks the **current** absolute deadline under that mutex;
  it cannot cancel a later rearm. A bound kernel timer/work item does not depend
  on a user fd/thread/process/Binder client surviving SIGKILL/crash.
- Timed sysfs requests detach periodic triggers and **flush the final old LED-core
  OFF callback before arming**, preventing a late old OFF from truncating a new
  request. Suspend likewise drains this work before provider suspension.
- Legacy positive brightness is also finite (maximum policy duration); legacy
  method signature/driver name stay intact, but indefinite-ON semantics are
  intentionally changed. Other privileged periodic writers must not compete.
- I/O errors propagate; logical activation cancels, re-enable latches, bound/live
  driver retries failed OFF at250ms. Background recovery does not clear the latch;
  explicit accepted OFF does. Owned enable refs are balanced; reported still-ON
  rail/other consumer is EBUSY, not forced disable/fake OFF. Probe does not pulse
  an OFF rail just to initialize its reference count.
- Suspend blocks positive requests, cancels timeout and requires checked OFF;
  failure aborts that callback, retains fault/retry. Resume never resurrects an
  old request. Teardown stops producers, synchronizes notifier and LED unregister,
  cancels timer/work outside any mutex the work needs, then tries checked OFF
  up to3 times with250ms gaps. Dedicated workqueue allocation/leak is removed.

**Source-supported guarantee:** expiry and OFF attempts independent of userspace
under a running kernel, normal binding lifetime and functioning regulator APIs.
**Not a physical hard-deadline guarantee.** Persistent PMIC/I2C failure, a rail held
by another consumer, kernel hangs/starvation and forced device removal cannot be
made physically OFF by software. Remove return errors do not veto Linux unbind;
failed final OFF is critical/logged, not claimed successful. Hardware fault,
process-death, suspend/remove and duration-rating tests remain unperformed.
Deployment stays CLOSED.

## Actual kernel build and scoped ABI receipt

No unprotected C50 toolchain path was supplied. The matching compiler was obtained
from the official Android prebuilt archive at commit
`425c8149f17c8d9914bf690b4d5abe45a13fb993`, path clang-r487747c:
`https://android.googlesource.com/platform/prebuilts/clang/host/linux-x86/+archive/425c8149f17c8d9914bf690b4d5abe45a13fb993/clang-r487747c.tar.gz`.
Archive SHA256 `10f007a1d5e946fc7c6cb903ec9cc3932d2cad4e3e896cfb1dc1a6b3e30dfdb2`.
Actual clang-17 SHA256
`25617ca38946d0e7476025e6fa4c15fb386894b75d9372e63a9f3cec47988ce0`, Android
10087095 / r487747c /17.0.2, LLD17.0.2: matches the documented C50 version/hash
prefix. Only needed build inputs were extracted in owned ignored output; no new
source checkout. No private signing key, disabled protection or stub was needed.

Isolated kernel OUT=out/c51c, source DEVICE_MODULES_PATH=canonical kernel,
ARCH=arm64 LLVM=1 LLVM_IAS=1 MTK_PLATFORM=mt6878 -j2. Copied unchanged reference
config; ran **olddefconfig modules_prepare**, then targeted
**drivers/leds/regulator-vibrator.ko**, with read-only C49 output as
KBUILD_MIXED_TREE and copied compatible Module.symvers. Genuine compilation,
modpost and final linkage: **PASS**. Pre-existing Kconfig warnings were retained,
not suppressed; driver/private-header checkpatch: **0 errors/0 warnings**.

| Result | Actual |
|---|---|
| New module SHA256 | `039526f98cc1dc560f372f2104cb5e4bcafe0885359595dad96990e80e489f45` |
| C50 baseline module SHA256 | `6dbeb0f71f9e1e9f199270f34ee9f366149fcb9b7ea59a23eedb00d2e402d794` |
| Identity/dependencies | Same regulator_vibrator/GPL/empty depends/vermagic |
| Vermagic | `6.1.115-mt6878-gq5012bf1-c29+ SMP preempt mod_unload modversions aarch64` |
| Import CRCs | 32/32 resolve/match C50 core;13 common unchanged;0 unversioned undefineds |
| Existing callback KCFI tags | 6/6 match (real arm64 preamble words, not a vacuous0 named-symbol count) |
| New kernel exports | 0 |
| Kernel Image | NOT rebuilt/modified; reference remains SHA256585080a838140a2c73c8caaae27c60ea6f360c926dc1b25ebc0e3a52c1f3a3d0 |

Scope is **ABI_VERIFIED_OFFLINE for identity/import CRC/six callback tags only**,
not whole-kernel ABI parity, module loading or hardware. New module intentionally
differs; original reference hashes/verifier were not edited to hide the delta.

**Validation correction disclosed:** the initial LLVM objcopy --dump-section
invocation (no output argument) rewrote the C49 baseline ELF container. Its exact
recorded bytes were restored from the verified identical C48 final-out copy;
SHA2566dbeb0f7... rechecked. The task's rewritten candidate was deleted/relinked.
The permanent verifier now parses ELF read-only and asserts all input hashes
unchanged before/after. Reference Module.symvers stays SHA2563331100038b4a2e528f29e8c2c49217cc2c4ddecdbd3f1f43bebe497684348e6.
No C54 source/shared Android output was affected by this correction.

Reproduction commands and test scope are in the kernel's existing
`tools/ulefone/gq5012bf1/README.md` and `tests/vibrator/` beneath it.

## HAL alignment and test receipt

Production now uses `discoverDriverTimedRegulatorLed`/DriverTimed.cpp only;
requires ABI1 + valid exported maximum + duration attribute, never falls back to
brightness or one-shot. Single duration transaction replaces six trigger writes.
Controller and Binder argument validation honor the kernel maximum. Fault/error
handling and unsupported capability/callback behavior stay truthful.

- **96/96 Python checks**, including all prior94 and two focused C51C checks.
- HAL native **34/34** normal and ASan/UBSan (original12 + expanded22);
  expanded **22/22 TSan**. Explicitly fake sysfs tests, not physical timer proof.
- Kernel's actual portable shared policy: **12/12** normal/ASan-UBSan/TSan plus
  **4/4 static** integration-order guards. Not execution of Linux timer/regulator
  APIs. KUnit is configured but no ARM64 runtime/emulator/load test was run.
- Genuine SDK37 aidl/frozen V2 and real Clang22/Bionic/vendor/VNDK probe:
  **6/6 ELF64 AArch64 source objects PASS**; NOT linked/Soong/IPC tested.
  The API SHA256 remains51161792eba95aee28a92723a1430b235e57e75751c24db04d84f7d83cca318e.
  Generated headers are temporary and embed command paths; no bit-identical raw
  header promise or checked-in substitute is used.

## Exact C54 owner next actions and closed gates

Current detailed integration contract: board README at the source commit above.
Keep source module/fragment UNSELECTED and existing code/init gates CLOSED.
Default system UID/domain, V2/default, module/executable/init names remain unchanged.

1. Validate/install the exact new kernel module under separate authorization;
   verify real timeout ABI1/effective config/dedicated supply and enforce a
   hardware-supported duration policy. No physical activation occurred here.
2. Establish actual DT-label/real-device labels and stable ueventd ownership.
   Permit metadata/last_error/duration reads plus **duration_ms write only** for
   system UID/hal_vibrator_default. No trigger/invert/delay/shot/brightness writes,
   root, DAC override, permissive domain or guessed path is required/supplied.
3. Resolve stock IVibratorManager/default V2 before replacing the complete stock
   binary/fragment; source implements IVibrator only, no invented actuator IDs.
4. Wire exact canonical source revisions once; mark the three stock extraction
   entries EXTRACT_ONLY and regenerate vendor config at product-definition time.
   Do not mutate readonly product lists in late BoardConfig or install duplicates.
5. C53 established **relative OUT_DIR=out works**; absolute OUT_DIR caused the
   earlier main.star error, not a missing source to fabricate. C54 owns active
   shared platform/vendor/policy outputs, so C51C did NOT start a concurrent Soong
   build or repair that checkout. Owner's available-slot target is:
   OUT_DIR=out; lunch lineage_gq5012bf1-cp2a-userdebug;
   m -j2 android.hardware.vibrator-service.gq5012bf1.
6. Complete real service link, assembled VINTF/SKU/APEX checks, enforcing policy
   and IPC, then separately authorized real hardware/fault/process-death tests.
   Only after all proofs review a deliberate code/init gate change. No automatic
   selection, new repository, push, flash, reboot or phone access is authorized.
