# encoder-bench: hardware video encoder throughput from adb

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
