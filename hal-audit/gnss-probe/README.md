# Aggregate-only foreground GNSS comparison

Independent public-API diagnostic, not a replacement HAL or a GNSS improvement
claim. Requires separate owner approval for installation, precise-location
permission, temporary receiver/screen activity and removal afterward.

Runs120 seconds requesting ordinary raw measurements, then120 seconds requesting
full tracking. GPS position interval remains1000ms in both phases; this is NOT a
5/10Hz benchmark or an independent cold-start TTFF comparison. Existing assistance
and other applications' requests can affect results. Sequential phases are not a
controlled accuracy proof, and reported accuracy is not measured true error.

The private `files/result.json` contains aggregate epoch counts, reported-accuracy
statistics, L5-family status/used-in-fix observations, measurement counts, ADR
valid/reset/cycle-slip counts and changes in hardware-clock discontinuity count.
Observation totals are repeated samples, not numbers of unique satellites.

The app never calls coordinate, raw range, ADR-distance, raw receiver-clock-time,
NMEA or satellite-ID getters. It has no network/storage permission, no service,
shared system UID, root helper, global setting changes or reboot functionality.
It does receive the normal framework callback objects in volatile process memory;
it only reads the listed quality metadata and writes aggregate JSON privately.
Leaving the foreground or pressing Stop releases its requests and records an
incomplete result. Completion also releases requests and the keep-screen-on flag.
It never auto-resumes an interrupted comparison.

Build outside source Git using the workspace's CPU/NUMA limit, for example:

```sh
numactl --physcpubind=0-7,16-23,32-39,48-55 --membind=0 -- \
  env JAVA_HOME=/opt/openjdk-bin-21.0.13_p9 \
  PATH=/opt/openjdk-bin-21.0.13_p9/bin:$PATH \
  bash hal-audit/gnss-probe/build.sh "$BUILD_DIR"
```

The build creates a disposable locally signed, debuggable APK and private key in
`BUILD_DIR`; never commit either. It does not need the platform signing key.
Install only if the package name `org.lieppos.gnssprobe` is not already owned by
another installation. Grant coarse/fine location with owner approval, keep GPS
already enabled, keep the phone stationary with clear sky, then launch
`org.lieppos.gnssprobe/.ProbeActivity`. Do not alter global location settings to
make a run succeed. Collect only its own result using `run-as`, release/stop the
app and uninstall after collecting the approved result.

Global developer full-tracking or another application's full request can invalidate
an ordinary/full distinction. Record that context without changing others'
settings. A successful registration is not proof that firmware honored a request.
Zero L5 observations alone is not proof of absent RF hardware. Raw/PVT mismatch
counts from the vendor's available log buffer are a separate, limited observation;
never export complete location-service dumps or raw vendor logs.
