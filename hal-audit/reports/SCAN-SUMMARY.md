# HAL/VINTF static scan

> Not a Soong build, libvintf check, SELinux compile, or hardware test.

## Totals

- records: 123
- declaration_records: 128
- unique_declared_contracts: 80
- source_implemented_records: 1
- proprietary_reference_records: 56
- proprietary_classified_artifact_records: 35
- unresolved_records: 87
- source_helper_modules: 5
- historical_started_process_records: 11
- hardware_verified_records: 0
- init_relationships_resolved: 1
- init_relationships_remaining: 77
- init_classification_counts: {'MISSING_METADATA': 77, 'RESOLVED_SERVICE': 1}

## Input scope

- `/home/armol/LieppOS/android/device/ulefone/gq5012bf1`: 19 eligible text files
- `/home/armol/LieppOS/android/hardware/mediatek/mt6878`: 7 eligible text files
- `/home/armol/LieppOS/android/hardware/ulefone/gq5012bf1`: 9 eligible text files
- `/home/armol/LieppOS/android/vendor/lieppos`: 113 eligible text files
- `/home/armol/LieppOS/android/vendor/mediatek/mt6878`: 0 eligible text files
- `/home/armol/LieppOS/android/vendor/ulefone/gq5012bf1`: 0 eligible text files

## Diagnostics

| Code | Count |
|---|---:|
| FILE_TOO_LARGE | 1 |
| MISSING_IMPLEMENTATION_IN_SCAN | 66 |
| MISSING_INIT_IN_SCAN | 77 |
| OVERRIDE_OVERLAP | 48 |
| POTENTIAL_AIDL_HIDL_CONFLICT | 1 |

All missing diagnostics mean **not resolved in supplied roots**, not proven absent from a running device.
OVERRIDE_OVERLAP is an ODM/vendor merge review, not a confirmed duplicate error.

## Contracts

| Subsystem | Interface | Version | Instance | Implementation |
|---|---|---|---|---|
| Audio | UNKNOWN | UNKNOWN | UNKNOWN | PROPRIETARY_IMPLEMENTATION |
| Audio | android.hardware.audio.IDevicesFactory | 7.1 | default | UNKNOWN |
| Audio | android.hardware.audio.effect.IEffectsFactory | 7.0 | default | UNKNOWN |
| Audio | android.hardware.soundtrigger3.ISoundTriggerHw | 1 | default | UNKNOWN |
| Audio | vendor.mediatek.hardware.audio.IMtkAudio | 1 | default | UNKNOWN |
| Auxiliary display | UNKNOWN | UNKNOWN | UNKNOWN | PROPRIETARY_IMPLEMENTATION |
| Battery and charging | UNKNOWN | UNKNOWN | UNKNOWN | PROPRIETARY_IMPLEMENTATION |
| Bluetooth | android.hardware.bluetooth.IBluetoothHci | 1.1 | default | UNKNOWN |
| Bluetooth | vendor.mediatek.hardware.bluetooth.audio.IBluetoothAudioProvidersFactory | 2.2 | default | UNKNOWN |
| Boot control | UNKNOWN | UNKNOWN | UNKNOWN | PROPRIETARY_IMPLEMENTATION |
| Camera | UNKNOWN | UNKNOWN | UNKNOWN | PROPRIETARY_IMPLEMENTATION |
| Camera | vendor.mediatek.hardware.camera.atms.IATMs | 1 | default | UNKNOWN |
| Camera | vendor.mediatek.hardware.camera.bgservice.IBGService | 1 | default | UNKNOWN |
| DRM | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |
| Face biometrics | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |
| Fingerprint | android.hardware.biometrics.fingerprint.IFingerprint | 3 | virtual | UNKNOWN |
| GNSS | UNKNOWN | UNKNOWN | UNKNOWN | PROPRIETARY_IMPLEMENTATION |
| GNSS | android.hardware.gnss.IGnss | 3 | default | UNKNOWN |
| Graphics allocator | UNKNOWN | UNKNOWN | UNKNOWN | PROPRIETARY_IMPLEMENTATION |
| Graphics composer | UNKNOWN | UNKNOWN | UNKNOWN | PROPRIETARY_IMPLEMENTATION |
| Graphics composer | vendor.mediatek.hardware.composer_ext.IComposerExt | 1 | default | UNKNOWN |
| Graphics mapper | android.hardware.graphics.mapper.IMapper | 4.0 | default | UNKNOWN |
| Health | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |
| Lights | UNKNOWN | UNKNOWN | UNKNOWN | PROPRIETARY_IMPLEMENTATION |
| NFC | UNKNOWN | UNKNOWN | UNKNOWN | PROPRIETARY_IMPLEMENTATION |
| Other vendor/platform interfaces | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |
| Other vendor/platform interfaces | UNKNOWN | UNKNOWN | UNKNOWN | PROPRIETARY_IMPLEMENTATION |
| Other vendor/platform interfaces | UNKNOWN | UNKNOWN | UNKNOWN | PROPRIETARY_IMPLEMENTATION |
| Other vendor/platform interfaces | UNKNOWN | UNKNOWN | UNKNOWN | PROPRIETARY_IMPLEMENTATION |
| Other vendor/platform interfaces | UNKNOWN | UNKNOWN | UNKNOWN | PROPRIETARY_IMPLEMENTATION |
| Other vendor/platform interfaces | UNKNOWN | UNKNOWN | UNKNOWN | PROPRIETARY_IMPLEMENTATION |
| Other vendor/platform interfaces | UNKNOWN | UNKNOWN | UNKNOWN | PROPRIETARY_IMPLEMENTATION |
| Other vendor/platform interfaces | UNKNOWN | UNKNOWN | UNKNOWN | PROPRIETARY_IMPLEMENTATION |
| Other vendor/platform interfaces | UNKNOWN | UNKNOWN | UNKNOWN | PROPRIETARY_IMPLEMENTATION |
| Other vendor/platform interfaces | UNKNOWN | UNKNOWN | UNKNOWN | PROPRIETARY_IMPLEMENTATION |
| Other vendor/platform interfaces | UNKNOWN | UNKNOWN | UNKNOWN | PROPRIETARY_IMPLEMENTATION |
| Other vendor/platform interfaces | android.hardware.cas.IMediaCasService | 1 | default | UNKNOWN |
| Other vendor/platform interfaces | android.hardware.renderscript.IDevice | 1.0 | default | UNKNOWN |
| Other vendor/platform interfaces | vendor.mediatek.hardware.aee.IAee | 1 | AEE | UNKNOWN |
| Other vendor/platform interfaces | vendor.mediatek.hardware.aee.IAee | 1.1 | AEE | UNKNOWN |
| Other vendor/platform interfaces | vendor.mediatek.hardware.aee.IAee | 1.1 | default | UNKNOWN |
| Other vendor/platform interfaces | vendor.mediatek.hardware.apmonitor.IApmService | 1 | default | UNKNOWN |
| Other vendor/platform interfaces | vendor.mediatek.hardware.atci.IAtcid | 1 | default | UNKNOWN |
| Other vendor/platform interfaces | vendor.mediatek.hardware.dmc.IDmcService | 1 | default | UNKNOWN |
| Other vendor/platform interfaces | vendor.mediatek.hardware.log.ILog | 1 | ATMWiFiHidlServer | UNKNOWN |
| Other vendor/platform interfaces | vendor.mediatek.hardware.log.ILog | 1 | ConnsysFWHidlServer | UNKNOWN |
| Other vendor/platform interfaces | vendor.mediatek.hardware.log.ILog | 1 | LoggerHidlServer | UNKNOWN |
| Other vendor/platform interfaces | vendor.mediatek.hardware.log.ILog | 1 | MobileLogHidlServer | UNKNOWN |
| Other vendor/platform interfaces | vendor.mediatek.hardware.log.ILog | 1 | ModemLogHidlServer | UNKNOWN |
| Other vendor/platform interfaces | vendor.mediatek.hardware.mdmonitor.IMDMonitorService | 1 | default | UNKNOWN |
| Other vendor/platform interfaces | vendor.mediatek.hardware.mmagent.IMMAgent | 1 | default | UNKNOWN |
| Other vendor/platform interfaces | vendor.mediatek.hardware.nvram.INvram | 1 | default | UNKNOWN |
| Other vendor/platform interfaces | vendor.mediatek.hardware.pq_aidl.IPictureQuality_AIDL | 7 | default | UNKNOWN |
| Other vendor/platform interfaces | vendor.mediatek.hardware.videotelephony.IVideoTelephony | 1 | default | UNKNOWN |
| Power | UNKNOWN | UNKNOWN | UNKNOWN | PROPRIETARY_IMPLEMENTATION |
| Power | UNKNOWN | UNKNOWN | UNKNOWN | PROPRIETARY_IMPLEMENTATION |
| Radio / telephony | UNKNOWN | UNKNOWN | UNKNOWN | PROPRIETARY_IMPLEMENTATION |
| Radio / telephony | android.hardware.radio.config.IRadioConfig | 2 | default | UNKNOWN |
| Radio / telephony | android.hardware.radio.data.IRadioData | 2 | slot1 | UNKNOWN |
| Radio / telephony | android.hardware.radio.data.IRadioData | 2 | slot2 | UNKNOWN |
| Radio / telephony | android.hardware.radio.ims.IRadioIms | 1 | slot1 | UNKNOWN |
| Radio / telephony | android.hardware.radio.ims.IRadioIms | 1 | slot2 | UNKNOWN |
| Radio / telephony | android.hardware.radio.messaging.IRadioMessaging | 2 | slot1 | UNKNOWN |
| Radio / telephony | android.hardware.radio.messaging.IRadioMessaging | 2 | slot2 | UNKNOWN |
| Radio / telephony | android.hardware.radio.modem.IRadioModem | 2 | imsSlot1 | UNKNOWN |
| Radio / telephony | android.hardware.radio.modem.IRadioModem | 2 | imsSlot2 | UNKNOWN |
| Radio / telephony | android.hardware.radio.modem.IRadioModem | 2 | se1 | UNKNOWN |
| Radio / telephony | android.hardware.radio.modem.IRadioModem | 2 | se2 | UNKNOWN |
| Radio / telephony | android.hardware.radio.modem.IRadioModem | 2 | slot1 | UNKNOWN |
| Radio / telephony | android.hardware.radio.modem.IRadioModem | 2 | slot2 | UNKNOWN |
| Radio / telephony | android.hardware.radio.network.IRadioNetwork | 2 | imsSlot1 | UNKNOWN |
| Radio / telephony | android.hardware.radio.network.IRadioNetwork | 2 | imsSlot2 | UNKNOWN |
| Radio / telephony | android.hardware.radio.network.IRadioNetwork | 2 | slot1 | UNKNOWN |
| Radio / telephony | android.hardware.radio.network.IRadioNetwork | 2 | slot2 | UNKNOWN |
| Radio / telephony | android.hardware.radio.sap.ISap | 1 | slot1 | UNKNOWN |
| Radio / telephony | android.hardware.radio.sap.ISap | 1 | slot2 | UNKNOWN |
| Radio / telephony | android.hardware.radio.sim.IRadioSim | 2 | imsSlot1 | UNKNOWN |
| Radio / telephony | android.hardware.radio.sim.IRadioSim | 2 | imsSlot2 | UNKNOWN |
| Radio / telephony | android.hardware.radio.sim.IRadioSim | 2 | se1 | UNKNOWN |
| Radio / telephony | android.hardware.radio.sim.IRadioSim | 2 | se2 | UNKNOWN |
| Radio / telephony | android.hardware.radio.sim.IRadioSim | 2 | slot1 | UNKNOWN |
| Radio / telephony | android.hardware.radio.sim.IRadioSim | 2 | slot2 | UNKNOWN |
| Radio / telephony | android.hardware.radio.voice.IRadioVoice | 2 | imsSlot1 | UNKNOWN |
| Radio / telephony | android.hardware.radio.voice.IRadioVoice | 2 | imsSlot2 | UNKNOWN |
| Radio / telephony | android.hardware.radio.voice.IRadioVoice | 2 | slot1 | UNKNOWN |
| Radio / telephony | android.hardware.radio.voice.IRadioVoice | 2 | slot2 | UNKNOWN |
| Radio / telephony | vendor.mediatek.hardware.mtkradioex.data.IMtkRadioExData | 2 | slot1 | UNKNOWN |
| Radio / telephony | vendor.mediatek.hardware.mtkradioex.data.IMtkRadioExData | 2 | slot2 | UNKNOWN |
| Radio / telephony | vendor.mediatek.hardware.mtkradioex.dch.IMtkRadioExDc | 1 | slot1 | UNKNOWN |
| Radio / telephony | vendor.mediatek.hardware.mtkradioex.dch.IMtkRadioExDc | 1 | slot2 | UNKNOWN |
| Radio / telephony | vendor.mediatek.hardware.mtkradioex.ims.IMtkRadioExIms | 1 | slot1 | UNKNOWN |
| Radio / telephony | vendor.mediatek.hardware.mtkradioex.ims.IMtkRadioExIms | 1 | slot2 | UNKNOWN |
| Radio / telephony | vendor.mediatek.hardware.mtkradioex.messaging.IMtkRadioExMessaging | 1 | slot1 | UNKNOWN |
| Radio / telephony | vendor.mediatek.hardware.mtkradioex.messaging.IMtkRadioExMessaging | 1 | slot2 | UNKNOWN |
| Radio / telephony | vendor.mediatek.hardware.mtkradioex.modem.IMtkRadioExModem | 2 | slot1 | UNKNOWN |
| Radio / telephony | vendor.mediatek.hardware.mtkradioex.modem.IMtkRadioExModem | 2 | slot2 | UNKNOWN |
| Radio / telephony | vendor.mediatek.hardware.mtkradioex.network.IMtkRadioExNetwork | 1 | slot1 | UNKNOWN |
| Radio / telephony | vendor.mediatek.hardware.mtkradioex.network.IMtkRadioExNetwork | 1 | slot2 | UNKNOWN |
| Radio / telephony | vendor.mediatek.hardware.mtkradioex.rcs.IMtkRadioExRcs | 1 | slot1 | UNKNOWN |
| Radio / telephony | vendor.mediatek.hardware.mtkradioex.rcs.IMtkRadioExRcs | 1 | slot2 | UNKNOWN |
| Radio / telephony | vendor.mediatek.hardware.mtkradioex.sim.IMtkRadioExSim | 1 | slot1 | UNKNOWN |
| Radio / telephony | vendor.mediatek.hardware.mtkradioex.sim.IMtkRadioExSim | 1 | slot2 | UNKNOWN |
| Radio / telephony | vendor.mediatek.hardware.mtkradioex.voice.IMtkRadioExVoice | 1 | slot1 | UNKNOWN |
| Radio / telephony | vendor.mediatek.hardware.mtkradioex.voice.IMtkRadioExVoice | 1 | slot2 | UNKNOWN |
| Security | UNKNOWN | UNKNOWN | UNKNOWN | PROPRIETARY_IMPLEMENTATION |
| Security | UNKNOWN | UNKNOWN | UNKNOWN | PROPRIETARY_IMPLEMENTATION |
| Security | android.hardware.secure_element.ISecureElement | 1 | SIM1 | UNKNOWN |
| Security | android.hardware.secure_element.ISecureElement | 1 | SIM2 | UNKNOWN |
| Sensors | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |
| Sensors | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |
| Sensors | UNKNOWN | UNKNOWN | UNKNOWN | PROPRIETARY_IMPLEMENTATION |
| Thermal camera | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |
| Thermal management | UNKNOWN | UNKNOWN | UNKNOWN | PROPRIETARY_IMPLEMENTATION |
| Thermal management | UNKNOWN | UNKNOWN | UNKNOWN | PROPRIETARY_IMPLEMENTATION |
| USB | UNKNOWN | UNKNOWN | UNKNOWN | PROPRIETARY_IMPLEMENTATION |
| USB | UNKNOWN | UNKNOWN | UNKNOWN | PROPRIETARY_IMPLEMENTATION |
| Ulefone-specific hardware | UNKNOWN | UNKNOWN | UNKNOWN | PROPRIETARY_IMPLEMENTATION |
| Ulefone-specific hardware | UNKNOWN | UNKNOWN | UNKNOWN | PROPRIETARY_IMPLEMENTATION |
| Ulefone-specific hardware | UNKNOWN | UNKNOWN | UNKNOWN | PROPRIETARY_IMPLEMENTATION |
| Vibrator/haptics | android.hardware.vibrator.IVibrator | 2 | default | IMPLEMENTED_IN_SOURCE |
| Wi-Fi | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |
| Wi-Fi | UNKNOWN | UNKNOWN | UNKNOWN | PROPRIETARY_IMPLEMENTATION |
| Wi-Fi | UNKNOWN | UNKNOWN | UNKNOWN | PROPRIETARY_IMPLEMENTATION |

See HAL-INVENTORY.json for file hashes, line diagnostics, init/module/extraction relationships and uncertainty.
