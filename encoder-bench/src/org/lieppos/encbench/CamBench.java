/*
 * Camera pipeline (sensor -> ISP -> output) frame-rate benchmark, run from adb:
 *
 *   adb shell su shell env CLASSPATH=/data/local/tmp/encbench.dex app_process / \
 *       org.lieppos.encbench.CamBench <cameraId> <w> <h> <fpsMin> <fpsMax> <seconds> \
 *       <normal|highspeed> [hfps=0|1] [encode]
 *
 *   normal     regular session, TEMPLATE_RECORD, CONTROL_AE_TARGET_FPS_RANGE=[min,max]
 *   highspeed  constrained high-speed session (setRepeatingBurst of the HS request list)
 *   hfps=1     also set the MediaTek vendor tag com.mediatek.streamingfeature.hfpsMode=1
 *              as a session parameter and in every request (what the stock app does
 *              for its 60 fps video mode)
 *   encode     add a HEVC encoder input surface (normal: second output; the consumer
 *              is then camera -> ISP -> encoder like a real recording)
 *   preview=WxH  size of the GL preview output (default: same as w x h)
 *   nopreview    no GL preview output (encoder only; needs encode)
 *
 * The first output is always a SurfaceTexture drained on a GL thread, so the
 * camera is never back-pressured by the measurement. Reported:
 *   result_fps    capture results per second (pipeline completions)
 *   sensor_fps    from SENSOR_TIMESTAMP deltas (what the sensor really ran at)
 *   consumer_fps  frames that reached the SurfaceTexture
 *   encoded_fps   encoder output frames per second (with encode)
 * Runs as the shell uid (com.android.shell holds CAMERA), like scrcpy's camera source.
 */
package org.lieppos.encbench;

import android.annotation.SuppressLint;
import android.content.AttributionSource;
import android.content.Context;
import android.content.ContextWrapper;
import android.graphics.SurfaceTexture;
import android.hardware.camera2.CameraCaptureSession;
import android.hardware.camera2.CameraCharacteristics;
import android.hardware.camera2.CameraConstrainedHighSpeedCaptureSession;
import android.hardware.camera2.CameraDevice;
import android.hardware.camera2.CameraManager;
import android.hardware.camera2.CaptureFailure;
import android.hardware.camera2.CaptureRequest;
import android.hardware.camera2.CaptureResult;
import android.hardware.camera2.TotalCaptureResult;
import android.hardware.camera2.params.OutputConfiguration;
import android.hardware.camera2.params.SessionConfiguration;
import android.media.MediaCodec;
import android.media.MediaCodecInfo;
import android.media.MediaFormat;
import android.opengl.EGL14;
import android.opengl.EGLConfig;
import android.opengl.EGLContext;
import android.opengl.EGLDisplay;
import android.opengl.EGLSurface;
import android.opengl.GLES11Ext;
import android.opengl.GLES20;
import android.os.Handler;
import android.os.HandlerThread;
import android.os.Looper;
import android.os.Process;
import android.util.Range;
import android.view.Surface;

import java.lang.reflect.Constructor;
import java.lang.reflect.Field;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.Executor;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicLong;

public final class CamBench {
    private static final CaptureRequest.Key<int[]> HFPS_MODE =
            new CaptureRequest.Key<>("com.mediatek.streamingfeature.hfpsMode", int[].class);

    // results
    static final AtomicInteger results = new AtomicInteger();
    static final AtomicInteger failures = new AtomicInteger();
    static final AtomicInteger consumed = new AtomicInteger();
    static final AtomicInteger encoded = new AtomicInteger();
    static volatile boolean measuring;
    static long firstSensorTs = -1, lastSensorTs = -1, maxGapNs, sumFrameDur, nFrameDur;
    static int sensorFrames;
    static volatile String lastResultRange = "?";

    public static void main(String[] a) throws Exception {
        if (a.length < 7) {
            System.err.println("usage: CamBench <id> <w> <h> <fpsMin> <fpsMax> <seconds> "
                    + "<normal|highspeed> [hfps=0|1] [encode]");
            System.exit(2);
        }
        final String id = a[0];
        final int w = Integer.parseInt(a[1]), h = Integer.parseInt(a[2]);
        final int fMin = Integer.parseInt(a[3]), fMax = Integer.parseInt(a[4]);
        final int seconds = Integer.parseInt(a[5]);
        final boolean hs = a[6].equals("highspeed");
        boolean hfps = false, encode = false, noPreview = false;
        int pw = w, ph = h;
        for (int i = 7; i < a.length; i++) {
            if (a[i].equals("hfps=1")) hfps = true;
            if (a[i].equals("encode")) encode = true;
            if (a[i].equals("nopreview")) noPreview = true;
            if (a[i].startsWith("preview=")) {
                String[] wh = a[i].substring(8).split("x");
                pw = Integer.parseInt(wh[0]);
                ph = Integer.parseInt(wh[1]);
            }
        }
        final int previewW = pw, previewH = ph;

        Looper.prepareMainLooper();
        Context ctx = shellContext();
        CameraManager cm = (CameraManager) CameraManager.class
                .getDeclaredConstructor(Context.class).newInstance(ctx);
        CameraCharacteristics ch = cm.getCameraCharacteristics(id);
        System.out.println("INFO camera=" + id + " uid=" + Process.myUid()
                + " " + w + "x" + h + " fps=[" + fMin + "," + fMax + "] session="
                + (hs ? "highspeed" : "normal") + " hfps=" + hfps + " encode=" + encode
                + " preview=" + (noPreview ? "none" : previewW + "x" + previewH)
                + " aeRanges=" + Arrays.toString(ch.get(
                        CameraCharacteristics.CONTROL_AE_AVAILABLE_TARGET_FPS_RANGES)));

        HandlerThread camThread = new HandlerThread("cam");
        camThread.start();
        Handler camH = new Handler(camThread.getLooper());
        Executor camExec = camH::post;

        // GL consumer
        HandlerThread glThread = new HandlerThread("gl");
        glThread.start();
        Handler glH = new Handler(glThread.getLooper());
        final SurfaceTexture[] stHolder = new SurfaceTexture[1];
        CountDownLatch glReady = new CountDownLatch(1);
        glH.post(() -> {
            GlSink sink = new GlSink();
            int[] tex = new int[1];
            GLES20.glGenTextures(1, tex, 0);
            GLES20.glBindTexture(GLES11Ext.GL_TEXTURE_EXTERNAL_OES, tex[0]);
            SurfaceTexture st = new SurfaceTexture(tex[0]);
            st.setDefaultBufferSize(previewW, previewH);
            st.setOnFrameAvailableListener(t -> {
                t.updateTexImage();
                if (measuring) consumed.incrementAndGet();
            }, glH);
            stHolder[0] = st;
            glReady.countDown();
        });
        glReady.await();
        Surface preview = new Surface(stHolder[0]);

        // Optional encoder
        MediaCodec enc = null;
        Surface encSurface = null;
        Thread drain = null;
        if (encode) {
            enc = MediaCodec.createByCodecName("c2.mtk.hevc.encoder");
            MediaFormat f = MediaFormat.createVideoFormat(MediaFormat.MIMETYPE_VIDEO_HEVC, w, h);
            f.setInteger(MediaFormat.KEY_COLOR_FORMAT,
                    MediaCodecInfo.CodecCapabilities.COLOR_FormatSurface);
            f.setInteger(MediaFormat.KEY_BIT_RATE,
                    (int) Math.min(100_000_000L, (long) (w * (long) h * fMax * 0.18)));
            f.setInteger(MediaFormat.KEY_FRAME_RATE, fMax);
            f.setInteger(MediaFormat.KEY_I_FRAME_INTERVAL, 1);
            f.setInteger(MediaFormat.KEY_PRIORITY, 0);
            f.setInteger(MediaFormat.KEY_OPERATING_RATE, fMax);
            enc.configure(f, null, null, MediaCodec.CONFIGURE_FLAG_ENCODE);
            encSurface = enc.createInputSurface();
            enc.start();
            final MediaCodec e = enc;
            drain = new Thread(() -> {
                MediaCodec.BufferInfo bi = new MediaCodec.BufferInfo();
                while (!Thread.currentThread().isInterrupted()) {
                    int idx;
                    try {
                        idx = e.dequeueOutputBuffer(bi, 10_000);
                    } catch (IllegalStateException ex) {
                        return;
                    }
                    if (idx >= 0) {
                        if (measuring && (bi.flags & MediaCodec.BUFFER_FLAG_CODEC_CONFIG) == 0
                                && bi.size > 0) {
                            encoded.incrementAndGet();
                        }
                        e.releaseOutputBuffer(idx, false);
                    }
                }
            });
            drain.start();
        }

        // Open camera
        final CameraDevice[] dev = new CameraDevice[1];
        CountDownLatch opened = new CountDownLatch(1);
        cm.openCamera(id, camExec, new CameraDevice.StateCallback() {
            @Override public void onOpened(CameraDevice d) { dev[0] = d; opened.countDown(); }
            @Override public void onDisconnected(CameraDevice d) {
                System.out.println("ERROR camera disconnected"); d.close(); opened.countDown(); }
            @Override public void onError(CameraDevice d, int err) {
                System.out.println("ERROR camera open error " + err); d.close(); opened.countDown(); }
        });
        if (!opened.await(10, TimeUnit.SECONDS) || dev[0] == null) {
            System.out.println("ERROR camera did not open");
            System.exit(1);
        }
        CameraDevice d = dev[0];

        List<Surface> targets = new ArrayList<>();
        if (!noPreview) targets.add(preview);
        if (encSurface != null) targets.add(encSurface);

        CaptureRequest.Builder rb = d.createCaptureRequest(CameraDevice.TEMPLATE_RECORD);
        for (Surface s : targets) rb.addTarget(s);
        rb.set(CaptureRequest.CONTROL_AE_TARGET_FPS_RANGE, new Range<>(fMin, fMax));
        if (hfps) rb.set(HFPS_MODE, new int[]{1});

        List<OutputConfiguration> outs = new ArrayList<>();
        for (Surface s : targets) outs.add(new OutputConfiguration(s));
        final CameraCaptureSession[] sess = new CameraCaptureSession[1];
        CountDownLatch configured = new CountDownLatch(1);
        SessionConfiguration sc = new SessionConfiguration(
                hs ? SessionConfiguration.SESSION_HIGH_SPEED : SessionConfiguration.SESSION_REGULAR,
                outs, camExec, new CameraCaptureSession.StateCallback() {
                    @Override public void onConfigured(CameraCaptureSession s) {
                        sess[0] = s; configured.countDown(); }
                    @Override public void onConfigureFailed(CameraCaptureSession s) {
                        System.out.println("ERROR session configure failed"); configured.countDown(); }
                });
        sc.setSessionParameters(rb.build());
        d.createCaptureSession(sc);
        if (!configured.await(15, TimeUnit.SECONDS) || sess[0] == null) {
            System.out.println("ERROR no session");
            d.close();
            System.exit(1);
        }

        CameraCaptureSession.CaptureCallback cb = new CameraCaptureSession.CaptureCallback() {
            @Override public void onCaptureCompleted(CameraCaptureSession s, CaptureRequest r,
                    TotalCaptureResult res) {
                if (!measuring) return;
                results.incrementAndGet();
                Long ts = res.get(CaptureResult.SENSOR_TIMESTAMP);
                Long fd = res.get(CaptureResult.SENSOR_FRAME_DURATION);
                Range<Integer> rr = res.get(CaptureResult.CONTROL_AE_TARGET_FPS_RANGE);
                if (rr != null) lastResultRange = rr.toString();
                synchronized (CamBench.class) {
                    if (ts != null) {
                        if (firstSensorTs < 0) firstSensorTs = ts;
                        else maxGapNs = Math.max(maxGapNs, ts - lastSensorTs);
                        lastSensorTs = ts;
                        sensorFrames++;
                    }
                    if (fd != null && fd > 0) { sumFrameDur += fd; nFrameDur++; }
                }
            }
            @Override public void onCaptureFailed(CameraCaptureSession s, CaptureRequest r,
                    CaptureFailure f) {
                if (measuring) failures.incrementAndGet();
            }
        };

        if (hs) {
            CameraConstrainedHighSpeedCaptureSession hss =
                    (CameraConstrainedHighSpeedCaptureSession) sess[0];
            hss.setRepeatingBurst(hss.createHighSpeedRequestList(rb.build()), cb, camH);
        } else {
            sess[0].setRepeatingRequest(rb.build(), cb, camH);
        }

        Thread.sleep(3000);                     // AE/pipeline warm-up
        long t0 = System.nanoTime();
        measuring = true;
        String th0 = thermal();
        for (int s = 1; s <= seconds; s++) {
            Thread.sleep(1000);
            if (s % 5 == 0 || s == seconds) {
                System.out.printf("PROGRESS t=%ds results=%d consumed=%d encoded=%d range=%s %s%n",
                        s, results.get(), consumed.get(), encoded.get(), lastResultRange, thermal());
            }
        }
        measuring = false;
        double secs = (System.nanoTime() - t0) / 1e9;

        sess[0].stopRepeating();
        sess[0].close();
        d.close();
        if (drain != null) drain.interrupt();
        if (enc != null) { try { enc.stop(); } catch (Exception ignored) { } enc.release(); }

        double sensorFps;
        double avgFrameDurMs;
        long gap;
        synchronized (CamBench.class) {
            sensorFps = sensorFrames > 1
                    ? (sensorFrames - 1) * 1e9 / (lastSensorTs - firstSensorTs) : 0;
            avgFrameDurMs = nFrameDur > 0 ? sumFrameDur / 1e6 / nFrameDur : 0;
            gap = maxGapNs;
        }
        System.out.printf("RESULT camera=%s size=%dx%d fps=[%d,%d] session=%s hfps=%b encode=%b"
                        + " secs=%.2f result_fps=%.2f sensor_fps=%.2f consumer_fps=%.2f"
                        + " encoded_fps=%.2f failures=%d max_sensor_gap_ms=%.1f"
                        + " avg_frame_duration_ms=%.2f result_range=%s"
                        + " thermal_start=[%s] thermal_end=[%s]%n",
                id, w, h, fMin, fMax, hs ? "highspeed" : "normal", hfps, encode, secs,
                results.get() / secs, sensorFps, consumed.get() / secs, encoded.get() / secs,
                failures.get(), gap / 1e6, avgFrameDurMs, lastResultRange, th0, thermal());
        System.exit(0);
    }

    /** System context presented as com.android.shell (uid 2000), as scrcpy does. */
    @SuppressLint("PrivateApi")
    private static Context shellContext() throws Exception {
        Class<?> atc = Class.forName("android.app.ActivityThread");
        Constructor<?> c = atc.getDeclaredConstructor();
        c.setAccessible(true);
        Object at = c.newInstance();
        Field cur = atc.getDeclaredField("sCurrentActivityThread");
        cur.setAccessible(true);
        cur.set(null, at);
        Field sys = atc.getDeclaredField("mSystemThread");
        sys.setAccessible(true);
        sys.setBoolean(at, true);
        Context base = (Context) atc.getMethod("getSystemContext").invoke(at);
        return new ContextWrapper(base) {
            @Override public String getPackageName() { return "com.android.shell"; }
            @Override public String getOpPackageName() { return "com.android.shell"; }
            @Override public AttributionSource getAttributionSource() {
                return new AttributionSource.Builder(Process.myUid())
                        .setPackageName("com.android.shell").build();
            }
            @Override public Context getApplicationContext() { return this; }
        };
    }

    private static String thermal() {
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < 80; i++) {
            String type = read("/sys/class/thermal/thermal_zone" + i + "/type");
            if ("soc_max".equals(type) || "ap_ntc".equals(type)) {
                String t = read("/sys/class/thermal/thermal_zone" + i + "/temp");
                if (t != null) sb.append(sb.length() > 0 ? " " : "").append(type).append('=')
                        .append(Integer.parseInt(t) / 1000.0);
            }
        }
        return sb.toString();
    }

    private static String read(String p) {
        try (java.io.BufferedReader r = new java.io.BufferedReader(new java.io.FileReader(p))) {
            String s = r.readLine();
            return s == null ? null : s.trim();
        } catch (Exception e) {
            return null;
        }
    }

    /** Pbuffer EGL context so SurfaceTexture.updateTexImage() can drain frames. */
    private static final class GlSink {
        GlSink() {
            EGLDisplay dpy = EGL14.eglGetDisplay(EGL14.EGL_DEFAULT_DISPLAY);
            int[] v = new int[2];
            EGL14.eglInitialize(dpy, v, 0, v, 1);
            int[] attr = {EGL14.EGL_RENDERABLE_TYPE, EGL14.EGL_OPENGL_ES2_BIT,
                    EGL14.EGL_SURFACE_TYPE, EGL14.EGL_PBUFFER_BIT, EGL14.EGL_NONE};
            EGLConfig[] cfg = new EGLConfig[1];
            int[] n = new int[1];
            EGL14.eglChooseConfig(dpy, attr, 0, cfg, 0, 1, n, 0);
            EGLContext ctx = EGL14.eglCreateContext(dpy, cfg[0], EGL14.EGL_NO_CONTEXT,
                    new int[]{EGL14.EGL_CONTEXT_CLIENT_VERSION, 2, EGL14.EGL_NONE}, 0);
            EGLSurface pb = EGL14.eglCreatePbufferSurface(dpy, cfg[0],
                    new int[]{EGL14.EGL_WIDTH, 16, EGL14.EGL_HEIGHT, 16, EGL14.EGL_NONE}, 0);
            if (!EGL14.eglMakeCurrent(dpy, pb, pb, ctx)) {
                throw new RuntimeException("eglMakeCurrent failed 0x"
                        + Integer.toHexString(EGL14.eglGetError()));
            }
        }
    }
}
