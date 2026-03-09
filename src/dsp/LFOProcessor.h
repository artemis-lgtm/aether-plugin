#pragma once
#include <cmath>
#include <random>

/**
 * LFOProcessor -- Rhythmic volume modulation with DAW transport sync.
 *
 * Modeled after Xfer LFO Tool / Cableguys VolumeShaper.
 * Provides tempo-synced (BPM-locked) and free-running volume shaping.
 *
 * Transport Sync (via AudioPlayHead):
 *   When enabled and host is playing, LFO phase locks directly to the
 *   beat position -- no drift, no accumulation errors. Jumping around
 *   the timeline always gives the correct phase.
 *   When host is stopped, LFO free-runs at the tempo-derived rate
 *   so preview still works.
 *
 * Shapes:
 *   0 = Sine          (classic smooth tremolo)
 *   1 = Triangle       (linear ramp tremolo)
 *   2 = Saw Down       (volume fades out, snaps back)
 *   3 = Saw Up         (volume rises, drops)
 *   4 = Square         (hard chop on/off)
 *   5 = Sidechain      (duck at beat, exponential recovery -- the Xfer classic)
 *   6 = Trance Gate    (4 sub-gates per cycle, 75% duty)
 *   7 = Sample & Hold  (random stepped level each cycle)
 *   8 = Half Sine      (positive bump first half, silence second half)
 *   9 = Noise          (smoothed random, organic movement)
 *
 * Sync Rates (19 musical divisions):
 *   8/1  4/1  2/1  1/1  1/2  1/2D  1/2T
 *   1/4  1/4D 1/4T 1/8  1/8D 1/8T
 *   1/16 1/16D 1/16T 1/32 1/32T 1/64
 */
class LFOProcessor
{
public:
    static constexpr int NUM_SHAPES     = 10;
    static constexpr int NUM_SYNC_RATES = 19;
    static constexpr double PI2 = 2.0 * 3.14159265358979323846;

    LFOProcessor() = default;

    void prepare(double sampleRate, int /*blockSize*/)
    {
        sr = sampleRate;
        phase = 0.0;
        holdValue = 1.0f;
        prevGain = 1.0f;
        noiseState = 0.0f;
        sampleInBlock = 0;
        rng.seed(42);
    }

    void setParameters(int shapeIdx, float rateHz, float depthAmt,
                       bool sync, int syncRate, float phaseOff)
    {
        shape       = (shapeIdx >= 0 && shapeIdx < NUM_SHAPES) ? shapeIdx : 0;
        rate        = (rateHz >= 0.1f && rateHz <= 20.0f) ? static_cast<double>(rateHz) : 2.0;
        depth       = (depthAmt >= 0.0f && depthAmt <= 1.0f) ? depthAmt : 0.0f;
        syncEnabled = sync;
        syncRateIdx = (syncRate >= 0 && syncRate < NUM_SYNC_RATES) ? syncRate : 7;
        phaseOffset = static_cast<double>(phaseOff);
    }

    /** Call at the start of each processBlock with transport info from AudioPlayHead. */
    void beginBlock(bool isPlaying, double bpm, double ppqPosition)
    {
        hostIsPlaying = isPlaying;
        hostBpm       = (bpm > 0.0) ? bpm : 120.0;
        blockStartPpq = ppqPosition;
        ppqPerSample  = (sr > 0.0) ? hostBpm / (60.0 * sr) : 0.0;
        sampleInBlock = 0;
    }

    /** Advance one sample. Returns gain multiplier in [0..1]. */
    float nextGain()
    {
        bool newCycle = false;

        if (syncEnabled)
        {
            double divBeats = getSyncBeats(syncRateIdx);

            if (hostIsPlaying)
            {
                // Phase computed directly from transport position (drift-free).
                double currentPpq = blockStartPpq + sampleInBlock * ppqPerSample;
                double pos = currentPpq / divBeats + phaseOffset;
                double newPhase = std::fmod(pos, 1.0);
                if (newPhase < 0.0) newPhase += 1.0;

                // Detect cycle wrap for S&H trigger
                newCycle = (newPhase < phase - 0.5);
                phase = newPhase;
            }
            else
            {
                // Transport stopped: free-run at synced rate so preview works
                double hz = hostBpm / (60.0 * divBeats);
                phase += hz / sr;
                if (phase >= 1.0) { phase -= 1.0; newCycle = true; }
            }
        }
        else
        {
            // Free-running Hz mode
            phase += rate / sr;
            if (phase >= 1.0) { phase -= 1.0; newCycle = true; }
        }

        ++sampleInBlock;

        float shapeVal = computeShape(phase, newCycle);
        float gain = 1.0f - depth * (1.0f - shapeVal);

        // Light smoothing (~0.5ms at 44.1kHz) to prevent clicks
        gain = prevGain + 0.05f * (gain - prevGain);
        prevGain = gain;
        return gain;
    }

    // ---- Static helpers for UI display ----

    static double getSyncBeats(int idx)
    {
        static const double b[NUM_SYNC_RATES] = {
            32.0,       // 0:  8/1  (8 bars)
            16.0,       // 1:  4/1  (4 bars)
            8.0,        // 2:  2/1  (2 bars)
            4.0,        // 3:  1/1  (1 bar)
            2.0,        // 4:  1/2
            3.0,        // 5:  1/2D (dotted)
            4.0 / 3.0,  // 6:  1/2T (triplet)
            1.0,        // 7:  1/4
            1.5,        // 8:  1/4D
            2.0 / 3.0,  // 9:  1/4T
            0.5,        // 10: 1/8
            0.75,       // 11: 1/8D
            1.0 / 3.0,  // 12: 1/8T
            0.25,       // 13: 1/16
            0.375,      // 14: 1/16D
            1.0 / 6.0,  // 15: 1/16T
            0.125,      // 16: 1/32
            1.0 / 12.0, // 17: 1/32T
            0.0625      // 18: 1/64
        };
        return (idx >= 0 && idx < NUM_SYNC_RATES) ? b[idx] : 1.0;
    }

    static const char* shapeName(int idx)
    {
        static const char* n[NUM_SHAPES] = {
            "Sine", "Triangle", "Saw Down", "Saw Up", "Square",
            "Sidechain", "Trance Gate", "S&H", "Half Sine", "Noise"
        };
        return (idx >= 0 && idx < NUM_SHAPES) ? n[idx] : "?";
    }

    static const char* syncRateName(int idx)
    {
        static const char* n[NUM_SYNC_RATES] = {
            "8/1", "4/1", "2/1", "1/1",
            "1/2", "1/2 D", "1/2 T",
            "1/4", "1/4 D", "1/4 T",
            "1/8", "1/8 D", "1/8 T",
            "1/16", "1/16 D", "1/16 T",
            "1/32", "1/32 T", "1/64"
        };
        return (idx >= 0 && idx < NUM_SYNC_RATES) ? n[idx] : "?";
    }

private:
    float computeShape(double p, bool newCycle)
    {
        switch (shape)
        {
            case 0: // Sine
                return 0.5f + 0.5f * static_cast<float>(std::cos(p * PI2));

            case 1: // Triangle
                return static_cast<float>(p < 0.5 ? 1.0 - 2.0 * p : 2.0 * p - 1.0);

            case 2: // Saw Down
                return static_cast<float>(1.0 - p);

            case 3: // Saw Up
                return static_cast<float>(p);

            case 4: // Square
                return p < 0.5 ? 1.0f : 0.0f;

            case 5: // Sidechain pump: 1-(1-p)^4
            {
                float inv = 1.0f - static_cast<float>(p);
                float i2 = inv * inv;
                return 1.0f - i2 * i2;
            }

            case 6: // Trance gate: 4 sub-divisions, 75% duty
            {
                double sub = p * 4.0;
                return (sub - std::floor(sub)) < 0.75 ? 1.0f : 0.0f;
            }

            case 7: // Sample & Hold
                if (newCycle)
                {
                    std::uniform_real_distribution<float> d(0.0f, 1.0f);
                    holdValue = d(rng);
                }
                return holdValue;

            case 8: // Half Sine: positive bump first half, silence second
                return static_cast<float>(p < 0.5 ? std::sin(p * PI2) : 0.0);

            case 9: // Smoothed Noise
            {
                std::uniform_real_distribution<float> d(-1.0f, 1.0f);
                noiseState = noiseState * 0.95f + d(rng) * 0.05f;
                return 0.5f + noiseState * 0.5f;
            }

            default: return 1.0f;
        }
    }

    double sr = 44100.0, phase = 0.0, rate = 2.0;
    float  depth = 0.0f, holdValue = 1.0f, prevGain = 1.0f, noiseState = 0.0f;
    int    shape = 0;
    std::mt19937 rng;

    // Transport sync
    bool   syncEnabled   = false;
    int    syncRateIdx   = 7;       // default 1/4 note
    double phaseOffset   = 0.0;
    bool   hostIsPlaying = false;
    double hostBpm       = 120.0;
    double blockStartPpq = 0.0;
    double ppqPerSample  = 0.0;
    int    sampleInBlock = 0;
};
