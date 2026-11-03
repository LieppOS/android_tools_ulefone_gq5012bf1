/*
 * Hardware video encoder throughput benchmark, run from adb without an app:
 *
 *   adb push encbench.dex /data/local/tmp/
 *   adb shell CLASSPATH=/data/local/tmp/encbench.dex app_process / \
 *       org.lieppos.encbench.EncBench <codec> <w> <h> <fps> <seconds> <mode> [content]
 *
 *   codec    c2.mtk.hevc.encoder | c2.mtk.avc.encoder | ...
 *   mode     max   - render as fast as the encoder accepts frames (throughput)
 *            paced - submit at exactly <fps> (realtime, like a camera) and
 *                    count frames that missed their deadline
 *   content  pan (default) - a random texture panned 7 px/frame (realistic motion)
 *            noise         - new per-pixel noise every frame (worst case)
 *   out      optional path: write the elementary stream (Annex-B) there, so the
 *            run also does the storage writes of a real recording and the
 *            result can be checked with a decoder/ffprobe
 *
 * Input is the encoder's own Surface, rendered with GLES, i.e. the same
 * zero-copy graphic-buffer path the camera uses; no CPU YUV copies.
 * Output: one machine-readable RESULT line plus per-second progress.
 */
package org.lieppos.encbench;

import android.media.MediaCodec;
import android.media.MediaCodecInfo;
import android.media.MediaFormat;
import android.opengl.EGL14;
import android.opengl.EGLConfig;
import android.opengl.EGLContext;
import android.opengl.EGLDisplay;
import android.opengl.EGLExt;
import android.opengl.EGLSurface;
import android.opengl.GLES20;
import android.os.Looper;
import android.view.Surface;

import java.io.BufferedReader;
import java.io.FileReader;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.FloatBuffer;
import java.util.Random;

public final class EncBench {
    private static final String VS =
            "attribute vec2 p; varying vec2 uv;\n"
            + "void main(){ uv = p*0.5+0.5; gl_Position = vec4(p,0.0,1.0); }\n";
    // pan: sample a fixed random texture with a per-frame offset.
    private static final String FS_PAN =
            "precision highp float; varying vec2 uv; uniform sampler2D t; uniform vec2 off;\n"
            + "void main(){ gl_FragColor = texture2D(t, uv*vec2(1.5,1.5) + off); }\n";
    // noise: integer hash of pixel + frame, fresh every frame.
    private static final String FS_NOISE =
            "precision highp float; uniform float f;\n"
            + "float h(vec2 q){ q = fract(q*vec2(0.1031,0.1030)); q += dot(q, q.yx+33.33);"
            + " return fract((q.x+q.y)*q.x); }\n"
            + "void main(){ vec2 c = gl_FragCoord.xy + f*vec2(17.0,29.0);"
            + " gl_FragColor = vec4(h(c), h(c+1.7), h(c+5.3), 1.0); }\n";

    public static void main(String[] a) throws Exception {
        if (a.length < 6) {
            System.err.println("usage: EncBench <codec> <w> <h> <fps> <seconds> <max|paced> [pan|noise] [out]");
            System.exit(2);
        }
        Looper.prepare();
        String codecName = a[0];
        int w = Integer.parseInt(a[1]), h = Integer.parseInt(a[2]);
        int fps = Integer.parseInt(a[3]);
        int seconds = Integer.parseInt(a[4]);
        boolean paced = a[5].equals("paced");
        boolean noise = a.length > 6 && a[6].equals("noise");
        java.io.FileOutputStream out = a.length > 7 ? new java.io.FileOutputStream(a[7]) : null;
        byte[] chunk = new byte[4 << 20];
        initThermal();
        String mime = codecName.contains("hevc") ? MediaFormat.MIMETYPE_VIDEO_HEVC
                : MediaFormat.MIMETYPE_VIDEO_AVC;

        MediaCodec codec = MediaCodec.createByCodecName(codecName);
        MediaCodecInfo.VideoCapabilities vc =
                codec.getCodecInfo().getCapabilitiesForType(mime).getVideoCapabilities();
        System.out.println("INFO codec=" + codecName + " declared: sizeSupported="
                + vc.isSizeSupported(w, h)
                + " areaSizeAndRateSupported=" + vc.areSizeAndRateSupported(w, h, fps)
                + " achievable=" + vc.getAchievableFrameRatesFor(w, h));

        // Bitrate like a phone camera: ~0.18 bit/pixel/frame (4K60 -> ~90 Mbit/s), capped by codec.
        int bitrate = (int) Math.min(100_000_000L, (long) (w * (long) h * fps * 0.18));
        MediaFormat f = MediaFormat.createVideoFormat(mime, w, h);
        f.setInteger(MediaFormat.KEY_COLOR_FORMAT,
                MediaCodecInfo.CodecCapabilities.COLOR_FormatSurface);
        f.setInteger(MediaFormat.KEY_BIT_RATE, bitrate);
        f.setInteger(MediaFormat.KEY_FRAME_RATE, fps);
        f.setInteger(MediaFormat.KEY_I_FRAME_INTERVAL, 1);
        f.setInteger(MediaFormat.KEY_PRIORITY, 0);              // realtime
        f.setInteger(MediaFormat.KEY_OPERATING_RATE, paced ? fps : Short.MAX_VALUE);
        f.setInteger(MediaFormat.KEY_BITRATE_MODE,
                MediaCodecInfo.EncoderCapabilities.BITRATE_MODE_VBR);
        codec.configure(f, null, null, MediaCodec.CONFIGURE_FLAG_ENCODE);
        Surface input = codec.createInputSurface();
        codec.start();
        System.out.println("INFO configured " + w + "x" + h + "@" + fps + " bitrate=" + bitrate
                + " mode=" + (paced ? "paced" : "max") + " content=" + (noise ? "noise" : "pan"));

        Gl gl = new Gl(input, w, h, noise);

        final int warmup = fps * 2;                 // frames ignored for the measurement
        final int total = warmup + fps * seconds;
        final long periodNs = 1_000_000_000L / fps;
        MediaCodec.BufferInfo info = new MediaCodec.BufferInfo();

        int submitted = 0, encoded = 0, late = 0;
        long bytes = 0, t0 = 0, tLast = 0, maxLatNs = 0, sumLatNs = 0;
        long[] submitTime = new long[total + 8];
        long next = System.nanoTime();
        long lastReport = 0;
        int encAtReport = 0;
        boolean eosSent = false;
        String thermalStart = thermal();

        while (true) {
            // Submit one frame when allowed.
            if (submitted < total) {
                long now = System.nanoTime();
                if (!paced || now >= next) {
                    if (paced && now - next > periodNs) late++;   // missed its slot by a full frame
                    gl.draw(submitted);
                    long pts = paced ? next : now;
                    EGLExt.eglPresentationTimeANDROID(gl.dpy, gl.surf, pts);
                    submitTime[submitted] = System.nanoTime();
                    EGL14.eglSwapBuffers(gl.dpy, gl.surf);  // blocks when the encoder is behind
                    submitted++;
                    next += periodNs;
                    if (paced && System.nanoTime() > next + periodNs * 4) {
                        next = System.nanoTime();          // do not burst to catch up
                    }
                }
            } else if (!eosSent) {
                codec.signalEndOfInputStream();
                eosSent = true;
            }

            // Drain everything that is ready.
            int idx;
            while ((idx = codec.dequeueOutputBuffer(info, 0)) != MediaCodec.INFO_TRY_AGAIN_LATER) {
                if (idx < 0) continue;                       // format/buffers changed
                boolean eos = (info.flags & MediaCodec.BUFFER_FLAG_END_OF_STREAM) != 0;
                boolean cfg = (info.flags & MediaCodec.BUFFER_FLAG_CODEC_CONFIG) != 0;
                if (out != null && info.size > 0) {
                    ByteBuffer ob = codec.getOutputBuffer(idx);
                    if (chunk.length < info.size) chunk = new byte[info.size];
                    ob.position(info.offset);
                    ob.get(chunk, 0, info.size);
                    out.write(chunk, 0, info.size);
                }
                if (!cfg && info.size > 0) {
                    long now = System.nanoTime();
                    if (encoded == warmup) t0 = now;
                    if (encoded >= warmup) {
                        bytes += info.size;
                        long lat = now - submitTime[Math.min(encoded, total - 1)];
                        sumLatNs += lat;
                        maxLatNs = Math.max(maxLatNs, lat);
                        tLast = now;
                    }
                    encoded++;
                    if (now - lastReport >= 1_000_000_000L) {
                        if (lastReport != 0) {
                            System.out.printf("PROGRESS frames=%d fps_last_s=%.1f %s%n", encoded,
                                    (encoded - encAtReport) * 1e9 / (now - lastReport), thermal());
                        }
                        lastReport = now;
                        encAtReport = encoded;
                    }
                }
                codec.releaseOutputBuffer(idx, false);
                if (eos) {
                    finish(codecName, w, h, fps, paced, noise, warmup, encoded, late, bytes,
                            t0, tLast, sumLatNs, maxLatNs, thermalStart);
                    if (out != null) out.close();
                    codec.stop();
                    codec.release();
                    gl.release();
                    return;
                }
            }
            if (submitted >= total && eosSent) Thread.sleep(1);
            else if (paced) {
                long sleepNs = next - System.nanoTime();
                if (sleepNs > 1_500_000) Thread.sleep(1);
            }
        }
    }

    private static void finish(String codec, int w, int h, int fps, boolean paced, boolean noise,
            int warmup, int encoded, int late, long bytes, long t0, long tLast,
            long sumLatNs, long maxLatNs, String thermalStart) {
        int measured = Math.max(0, encoded - warmup - 1);
        double secs = (tLast - t0) / 1e9;
        double outFps = secs > 0 ? measured / secs : 0;
        System.out.printf("RESULT codec=%s size=%dx%d target_fps=%d mode=%s content=%s"
                        + " frames=%d secs=%.2f encoded_fps=%.2f late_submits=%d"
                        + " avg_latency_ms=%.1f max_latency_ms=%.1f bitrate_mbps=%.1f"
                        + " thermal_start=[%s] thermal_end=[%s]%n",
                codec, w, h, fps, paced ? "paced" : "max", noise ? "noise" : "pan",
                measured, secs, outFps, late,
                measured > 0 ? sumLatNs / 1e6 / (measured + 1) : 0, maxLatNs / 1e6,
                secs > 0 ? bytes * 8 / secs / 1e6 : 0, thermalStart, thermal());
    }

    private static final java.util.List<String[]> ZONES = new java.util.ArrayList<>();

    /** Find the soc_max and ap_ntc zones once; reading is then two small files. */
    private static void initThermal() {
        for (int i = 0; i < 80; i++) {
            String type = read("/sys/class/thermal/thermal_zone" + i + "/type");
            if ("soc_max".equals(type) || "ap_ntc".equals(type)) {
                ZONES.add(new String[]{type, "/sys/class/thermal/thermal_zone" + i + "/temp"});
            }
        }
    }

    /** soc_max and ap_ntc in degrees C. */
    private static String thermal() {
        StringBuilder sb = new StringBuilder();
        for (String[] z : ZONES) {
            String t = read(z[1]);
            if (t != null) {
                if (sb.length() > 0) sb.append(' ');
                sb.append(z[0]).append('=').append(Integer.parseInt(t) / 1000.0);
            }
        }
        return sb.toString();
    }

    private static String read(String path) {
        try (BufferedReader r = new BufferedReader(new FileReader(path))) {
            String s = r.readLine();
            return s == null ? null : s.trim();
        } catch (Exception e) {
            return null;
        }
    }

    /** Minimal EGL/GLES renderer onto the encoder input surface. */
    private static final class Gl {
        final EGLDisplay dpy;
        final EGLSurface surf;
        final EGLContext ctx;
        final int prog, uOff, uF;
        final boolean noise;
        final FloatBuffer quad;

        Gl(Surface s, int w, int h, boolean noise) {
            this.noise = noise;
            dpy = EGL14.eglGetDisplay(EGL14.EGL_DEFAULT_DISPLAY);
            int[] v = new int[2];
            check(EGL14.eglInitialize(dpy, v, 0, v, 1), "eglInitialize");
            int[] attr = {EGL14.EGL_RED_SIZE, 8, EGL14.EGL_GREEN_SIZE, 8, EGL14.EGL_BLUE_SIZE, 8,
                    EGL14.EGL_RENDERABLE_TYPE, EGL14.EGL_OPENGL_ES2_BIT,
                    0x3142 /* EGL_RECORDABLE_ANDROID */, 1, EGL14.EGL_NONE};
            EGLConfig[] cfg = new EGLConfig[1];
            int[] n = new int[1];
            check(EGL14.eglChooseConfig(dpy, attr, 0, cfg, 0, 1, n, 0) && n[0] > 0, "eglChooseConfig");
            ctx = EGL14.eglCreateContext(dpy, cfg[0], EGL14.EGL_NO_CONTEXT,
                    new int[]{EGL14.EGL_CONTEXT_CLIENT_VERSION, 2, EGL14.EGL_NONE}, 0);
            surf = EGL14.eglCreateWindowSurface(dpy, cfg[0], s, new int[]{EGL14.EGL_NONE}, 0);
            check(EGL14.eglMakeCurrent(dpy, surf, surf, ctx), "eglMakeCurrent");
            GLES20.glViewport(0, 0, w, h);

            prog = link(VS, noise ? FS_NOISE : FS_PAN);
            GLES20.glUseProgram(prog);
            uOff = GLES20.glGetUniformLocation(prog, "off");
            uF = GLES20.glGetUniformLocation(prog, "f");
            quad = ByteBuffer.allocateDirect(8 * 4).order(ByteOrder.nativeOrder()).asFloatBuffer();
            quad.put(new float[]{-1, -1, 1, -1, -1, 1, 1, 1}).position(0);
            int p = GLES20.glGetAttribLocation(prog, "p");
            GLES20.glEnableVertexAttribArray(p);
            GLES20.glVertexAttribPointer(p, 2, GLES20.GL_FLOAT, false, 0, quad);

            if (!noise) {
                // 1024x1024 RGBA random texture with some low-frequency structure.
                int ts = 1024;
                ByteBuffer px = ByteBuffer.allocateDirect(ts * ts * 4);
                Random r = new Random(1234);
                for (int y = 0; y < ts; y++) {
                    for (int x = 0; x < ts; x++) {
                        int base = ((x / 64 + y / 64) & 1) * 80 + 60;
                        px.put((byte) (base + r.nextInt(90)));
                        px.put((byte) (base + r.nextInt(90)));
                        px.put((byte) (base + r.nextInt(90)));
                        px.put((byte) 255);
                    }
                }
                px.position(0);
                int[] tex = new int[1];
                GLES20.glGenTextures(1, tex, 0);
                GLES20.glBindTexture(GLES20.GL_TEXTURE_2D, tex[0]);
                GLES20.glTexParameteri(GLES20.GL_TEXTURE_2D, GLES20.GL_TEXTURE_MIN_FILTER, GLES20.GL_LINEAR);
                GLES20.glTexParameteri(GLES20.GL_TEXTURE_2D, GLES20.GL_TEXTURE_MAG_FILTER, GLES20.GL_LINEAR);
                GLES20.glTexParameteri(GLES20.GL_TEXTURE_2D, GLES20.GL_TEXTURE_WRAP_S, GLES20.GL_REPEAT);
                GLES20.glTexParameteri(GLES20.GL_TEXTURE_2D, GLES20.GL_TEXTURE_WRAP_T, GLES20.GL_REPEAT);
                GLES20.glTexImage2D(GLES20.GL_TEXTURE_2D, 0, GLES20.GL_RGBA, ts, ts, 0,
                        GLES20.GL_RGBA, GLES20.GL_UNSIGNED_BYTE, px);
            }
        }

        void draw(int frame) {
            if (noise) {
                GLES20.glUniform1f(uF, frame % 4096);
            } else {
                GLES20.glUniform2f(uOff, (frame * 7 % 1024) / 1024f, (frame * 3 % 1024) / 1024f);
            }
            GLES20.glDrawArrays(GLES20.GL_TRIANGLE_STRIP, 0, 4);
        }

        void release() {
            EGL14.eglMakeCurrent(dpy, EGL14.EGL_NO_SURFACE, EGL14.EGL_NO_SURFACE, EGL14.EGL_NO_CONTEXT);
            EGL14.eglDestroySurface(dpy, surf);
            EGL14.eglDestroyContext(dpy, ctx);
            EGL14.eglTerminate(dpy);
        }

        private static int link(String vs, String fs) {
            int p = GLES20.glCreateProgram();
            GLES20.glAttachShader(p, shader(GLES20.GL_VERTEX_SHADER, vs));
            GLES20.glAttachShader(p, shader(GLES20.GL_FRAGMENT_SHADER, fs));
            GLES20.glLinkProgram(p);
            int[] ok = new int[1];
            GLES20.glGetProgramiv(p, GLES20.GL_LINK_STATUS, ok, 0);
            check(ok[0] != 0, "link: " + GLES20.glGetProgramInfoLog(p));
            return p;
        }

        private static int shader(int type, String src) {
            int s = GLES20.glCreateShader(type);
            GLES20.glShaderSource(s, src);
            GLES20.glCompileShader(s);
            int[] ok = new int[1];
            GLES20.glGetShaderiv(s, GLES20.GL_COMPILE_STATUS, ok, 0);
            check(ok[0] != 0, "compile: " + GLES20.glGetShaderInfoLog(s));
            return s;
        }

        private static void check(boolean ok, String what) {
            if (!ok) throw new RuntimeException(what + " failed, egl error 0x"
                    + Integer.toHexString(EGL14.eglGetError()));
        }
    }
}
