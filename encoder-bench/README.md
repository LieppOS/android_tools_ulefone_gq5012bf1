# encoder-bench: hardware encoder and camera pipeline throughput from adb

Measures what the GQ5012BF1 (MT6878) hardware encoders really sustain, without
an app or a ROM build. It renders frames with GLES straight into the encoder's
input Surface. That is the same zero-copy graphic-buffer path the camera uses,
with no CPU YUV copies, so the result is the encoder's capability rather than
the harness's.

## Build (host)

```sh
./build.sh            # -> /tmp/lieppos-builds/encoder-bench/encbench.dex
```

Uses the Lineage tree's prebuilt JDK 21, `android.jar` and `r8.jar` (D8)
(`TREE=` overrides the tree path). Host work is bound to NUMA nodes 0 and 1.

## Run (phone, adb root not required)

```sh
adb push /tmp/lieppos-builds/encoder-bench/encbench.dex /data/local/tmp/
adb shell CLASSPATH=/data/local/tmp/encbench.dex app_process / \
    org.lieppos.encbench.EncBench <codec> <w> <h> <fps> <seconds> <max|paced> [pan|noise] [out]
```

| Argument | Meaning |
|---|---|
| `codec` | e.g. `c2.mtk.hevc.encoder`, `c2.mtk.avc.encoder` |
| `max` | submit as fast as the encoder accepts frames (throughput) |
| `paced` | submit at exactly `fps` like a camera; `late_submits` counts missed slots |
| `pan` | random texture panned 7 px/frame (realistic motion, default) |
| `noise` | fresh per-pixel noise every frame (worst case; rate control cannot hold the bitrate) |
| `out` | write the Annex-B stream to a file, for storage load and decoder checks |

The bitrate is about 0.18 bit/pixel/frame (4K60 ≈ 90 Mbit/s), capped at the codec's
100 Mbit/s. The first 2 s are warm-up and are excluded. Output is per-second
`PROGRESS` lines and one `RESULT` line with fps, latency, bitrate, and the
`soc_max`/`ap_ntc` temperatures.

Remove `/data/local/tmp/encbench.dex` and any `out` files afterwards.

## CamBench: camera pipeline (sensor -> ISP -> outputs)

```sh
adb shell CLASSPATH=/data/local/tmp/encbench.dex app_process / \
    org.lieppos.encbench.CamBench <cameraId> <w> <h> <fpsMin> <fpsMax> <seconds> \
    <normal|highspeed> [hfps=1] [encode] [preview=WxH] [nopreview]
```

It runs as root through adb (uid 0 passes the CAMERA permission check). It reports the
capture-result rate, the real sensor rate (from `SENSOR_TIMESTAMP` and
`SENSOR_FRAME_DURATION`), the frames delivered to a GL consumer and the HEVC encoder
output rate. `hfps=1` sets MediaTek's `com.mediatek.streamingfeature.hfpsMode`, the stock
app's 60 fps switch. The HAL only enables HFPS when a real video-encoder stream
(`encode`) is part of the session.

Warnings:

- The stock HAL **aborts** (`evaluateSensorSetting: Unknown sensorMode`) on the 4K
  constrained high-speed configurations it advertises. `camerahalserver` then restarts.
- Do not read the vendor `/proc/mmdvfs` debug files while testing. Doing so caused a
  kernel panic and a reboot.
