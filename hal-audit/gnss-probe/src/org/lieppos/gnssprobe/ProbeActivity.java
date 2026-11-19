// SPDX-License-Identifier: Apache-2.0
package org.lieppos.gnssprobe;

import android.Manifest;
import android.app.Activity;
import android.content.pm.PackageManager;
import android.location.GnssClock;
import android.location.GnssMeasurement;
import android.location.GnssMeasurementRequest;
import android.location.GnssMeasurementsEvent;
import android.location.GnssStatus;
import android.location.Location;
import android.location.LocationListener;
import android.location.LocationManager;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.os.SystemClock;
import android.view.WindowManager;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.TextView;
import java.io.FileOutputStream;
import java.nio.charset.StandardCharsets;
import org.json.JSONArray;
import org.json.JSONObject;

/** Foreground-only, fixed-duration probe. Never reads coordinates or range values. */
public final class ProbeActivity extends Activity {
    private static final long PHASE_MS = 120000;
    private final Handler handler = new Handler(Looper.getMainLooper());
    private final JSONArray completed = new JSONArray();
    private LocationManager manager;
    private TextView display;
    private Stats current;
    private boolean running;
    private long phaseStart;
    private String outcome = "not_started";

    private static boolean isL5(double hz) { return hz >= 1164e6 && hz <= 1189e6; }
    private static final class Stats {
        final boolean full;
        long fixes, duplicateFixes, mockFixes, accuracyCount, svCallbacks, svObservations;
        long usedObservations, l5Observations, l5UsedObservations, measurementEvents;
        long measurementObservations, l5MeasurementObservations, adrValid, adrReset, adrSlip;
        long discontinuityChanges, firstFixMs = -1, lastEpoch = -1;
        Integer lastDiscontinuity;
        double accuracySum, accuracySquareSum, l5Cn0Sum;
        long l5Cn0Count;
        boolean registrationAccepted;
        int measurementStatus = -1;
        Stats(boolean value) { full = value; }
        JSONObject json(long elapsed) throws Exception {
            JSONObject j = new JSONObject();
            j.put("requested_full_tracking", full).put("elapsed_ms", elapsed);
            j.put("measurement_registration_accepted", registrationAccepted);
            j.put("measurement_status", measurementStatus);
            j.put("unique_fix_epochs", fixes).put("duplicate_fix_epochs", duplicateFixes);
            j.put("mock_fixes", mockFixes).put("first_fix_reported_ms", firstFixMs);
            j.put("reported_accuracy_count", accuracyCount);
            if (accuracyCount > 0) {
                double mean = accuracySum / accuracyCount;
                j.put("mean_reported_accuracy_m", mean);
                j.put("std_reported_accuracy_m", Math.sqrt(Math.max(0,
                    accuracySquareSum / accuracyCount - mean * mean)));
            }
            j.put("sv_callbacks", svCallbacks).put("sv_observations", svObservations);
            j.put("used_in_fix_observations", usedObservations);
            j.put("l5_family_observations", l5Observations);
            j.put("l5_family_used_in_fix_observations", l5UsedObservations);
            if (l5Cn0Count > 0) j.put("l5_family_mean_cn0_dbhz", l5Cn0Sum / l5Cn0Count);
            j.put("measurement_events", measurementEvents);
            j.put("measurement_observations", measurementObservations);
            j.put("l5_family_measurement_observations", l5MeasurementObservations);
            j.put("adr_valid_observations", adrValid).put("adr_reset_observations", adrReset);
            j.put("adr_cycle_slip_observations", adrSlip);
            j.put("hardware_clock_discontinuity_changes", discontinuityChanges);
            return j;
        }
    }
    private final LocationListener locations = new LocationListener() {
        @Override public void onLocationChanged(Location location) {
            if (!running || current == null) return;
            // Deliberately never call getLatitude/getLongitude, toString, range or time APIs.
            long epoch = location.getElapsedRealtimeNanos();
            if (epoch == current.lastEpoch) { current.duplicateFixes++; return; }
            current.lastEpoch = epoch;
            current.fixes++;
            if (location.isMock()) current.mockFixes++;
            if (location.hasAccuracy()) {
                double a = location.getAccuracy();
                if (Double.isFinite(a) && a >= 0) {
                    current.accuracyCount++; current.accuracySum += a;
                    current.accuracySquareSum += a * a;
                }
            }
        }
    };
    private final GnssStatus.Callback satellites = new GnssStatus.Callback() {
        @Override public void onFirstFix(int ms) {
            if (running && current != null) current.firstFixMs = ms;
        }
        @Override public void onSatelliteStatusChanged(GnssStatus status) {
            if (!running || current == null) return;
            current.svCallbacks++;
            for (int i = 0; i < status.getSatelliteCount(); i++) {
                current.svObservations++;
                if (status.usedInFix(i)) current.usedObservations++;
                if (status.hasCarrierFrequencyHz(i) && isL5(status.getCarrierFrequencyHz(i))) {
                    current.l5Observations++;
                    if (status.usedInFix(i)) current.l5UsedObservations++;
                    current.l5Cn0Sum += status.getCn0DbHz(i); current.l5Cn0Count++;
                }
            }
        }
    };
    private final GnssMeasurementsEvent.Callback measurements = new GnssMeasurementsEvent.Callback() {
        @Override public void onStatusChanged(int status) {
            if (running && current != null) current.measurementStatus = status;
        }
        @Override public void onGnssMeasurementsReceived(GnssMeasurementsEvent event) {
            if (!running || current == null) return;
            current.measurementEvents++;
            GnssClock clock = event.getClock();
            int discontinuity = clock.getHardwareClockDiscontinuityCount();
            if (current.lastDiscontinuity != null && current.lastDiscontinuity != discontinuity)
                current.discontinuityChanges++;
            current.lastDiscontinuity = discontinuity;
            for (GnssMeasurement m : event.getMeasurements()) {
                current.measurementObservations++;
                if (m.hasCarrierFrequencyHz() && isL5(m.getCarrierFrequencyHz()))
                    current.l5MeasurementObservations++;
                int state = m.getAccumulatedDeltaRangeState();
                if ((state & GnssMeasurement.ADR_STATE_VALID) != 0) current.adrValid++;
                if ((state & GnssMeasurement.ADR_STATE_RESET) != 0) current.adrReset++;
                if ((state & GnssMeasurement.ADR_STATE_CYCLE_SLIP) != 0) current.adrSlip++;
            }
        }
    };
    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        LinearLayout layout = new LinearLayout(this); layout.setOrientation(LinearLayout.VERTICAL);
        layout.setPadding(36, 48, 36, 24);
        display = new TextView(this); display.setTextSize(20); layout.addView(display);
        Button stop = new Button(this); stop.setText("Stop and release GNSS");
        stop.setOnClickListener(v -> finishRun("stopped_by_user", false)); layout.addView(stop);
        setContentView(layout);
        manager = getSystemService(LocationManager.class);
        if (state != null) { finishRun("activity_recreated_no_auto_restart", false); return; }
        if (checkSelfPermission(Manifest.permission.ACCESS_FINE_LOCATION) != PackageManager.PERMISSION_GRANTED) {
            finishRun("fine_location_permission_missing", false); return;
        }
        if (!manager.isProviderEnabled(LocationManager.GPS_PROVIDER)) {
            finishRun("gps_provider_disabled_no_setting_changed", false); return;
        }
        try {
            getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);
            running = true;
            current = new Stats(false); phaseStart = SystemClock.elapsedRealtime();
            manager.registerGnssStatusCallback(getMainExecutor(), satellites);
            registerMeasurements(false);
            manager.requestLocationUpdates(LocationManager.GPS_PROVIDER, 1000, 0, locations,
                Looper.getMainLooper());
            outcome = "running"; save(false); tick();
        } catch (Exception e) { finishRun("start_failed_" + e.getClass().getSimpleName(), false); }
    }
    private void registerMeasurements(boolean full) {
        current.registrationAccepted = manager.registerGnssMeasurementsCallback(
            new GnssMeasurementRequest.Builder().setFullTracking(full)
                .setIntervalMillis(1000).build(),
            getMainExecutor(), measurements);
    }
    private void tick() {
        if (!running) return;
        long elapsed = SystemClock.elapsedRealtime() - phaseStart;
        if (elapsed >= PHASE_MS) {
            try {
                completed.put(current.json(elapsed));
                if (current.full) { current = null; finishRun("completed", true); return; }
                manager.unregisterGnssMeasurementsCallback(measurements);
                current = new Stats(true); phaseStart = SystemClock.elapsedRealtime();
                registerMeasurements(true); save(false);
            } catch (Exception e) { finishRun("phase_failed_" + e.getClass().getSimpleName(), false); return; }
        }
        display.setText("GNSS aggregate-only comparison\n\n" + (current.full ? "Full tracking" : "Ordinary")
            + " — " + Math.max(0, (PHASE_MS - (SystemClock.elapsedRealtime() - phaseStart)) / 1000)
            + " seconds left\n\nKeep still under open sky.\nNo coordinates or raw ranges saved."
            + "\n\nFix epochs: " + current.fixes + "\nRaw events: " + current.measurementEvents
            + "\nL5-family observations: " + current.l5Observations);
        handler.postDelayed(this::tick, 1000);
    }
    private void save(boolean complete) {
        try {
            JSONObject root = new JSONObject().put("schema", 1).put("outcome", outcome);
            root.put("complete", complete).put("phases", completed);
            root.put("no_coordinates_nmea_or_ranges_stored", true);
            root.put("independent_cold_start_comparison", false);
            if (current != null) root.put("current_phase",
                current.json(SystemClock.elapsedRealtime() - phaseStart));
            try (FileOutputStream out = openFileOutput("result.json", MODE_PRIVATE)) {
                out.write(root.toString(2).getBytes(StandardCharsets.UTF_8)); out.getFD().sync();
            }
        } catch (Exception e) { display.setText("Could not write aggregate result: " + e.getClass().getSimpleName()); }
    }
    private void finishRun(String result, boolean complete) {
        running = false; handler.removeCallbacksAndMessages(null); outcome = result;
        if (manager != null) {
            manager.removeUpdates(locations);
            manager.unregisterGnssStatusCallback(satellites);
            manager.unregisterGnssMeasurementsCallback(measurements);
        }
        getWindow().clearFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);
        save(complete); display.setText("GNSS probe: " + result + "\nGNSS requests released.\nAggregate result only.");
    }
    @Override public void onStop() {
        if (running) finishRun("left_foreground", false);
        super.onStop();
    }
}
