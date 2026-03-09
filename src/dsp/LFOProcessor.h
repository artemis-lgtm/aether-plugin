#pragma once
#include <cmath>
#include <random>

/**
 * LFOProcessor -- Rhythmic volume modulation.
 *
 * Modeled after Xfer LFO Tool / Cableguys VolumeShaper.
 * Provides tempo-relevant volume shaping: tremolo, sidechain pump,
 * trance gate, and more.
 *
 * Shapes:
 *   0 = Sine        (classic smooth tremolo)
 *   1 = Triangle     (linear ramp tremolo)
 *   2 = Saw Down     (volume fades out, snaps back)
 *   3 = Saw Up       (volume rises, drops)
 *   4 = Square       (hard chop on/off)
 *   5 = Sidechain    (four-on-the-floor pump, exponential recovery)
 *   6 = Trance Gate  (16th-note rhythmic gate, 75% duty cycle)
 *   7 = Sample&Hold  (random stepped levels per cycle)
 *
 * Parameters:
 *   shape: waveform index (0-7)
 *   rate:  LFO speed in Hz (0.1 - 20.0)
 *   depth: modulation amount (0.0 = bypass, 1.0 = full modulation)
 */
class LFOProcessor
{
public:
    static constexpr int NUM_SHAPES = 8;
    static constexpr double PI2 = 2.0 * 3.14159265358979323846;

    LFOProcessor() = default;

    void prepare(double sampleRate, int /*blockSize*/)
    {
        sr = sampleRate;
        phase = 0.0;
        holdValue = 1.0f;
        prevGain = 1.0f;
        rng.seed(42);
    }

    void setParameters(int shapeIdx, float rateHz, float depthAmt)
    {
        shape = (shapeIdx >= 0 && shapeIdx < NUM_SHAPES) ? shapeIdx : 0;
        rate = (rateHz >= 0.1 && rateHz <= 20.0) ? static_cast<double>(rateHz) : 2.0;
        depth = (depthAmt >= 0.0f && depthAmt <= 1.0f) ? depthAmt : 0.0f;
    }

    /** Advance LFO by one sample and return the gain multiplier (0..1). */
    float nextGain()
    {
        // Advance phase
        phase += rate / sr;
        bool newCycle = false;
        if (phase >= 1.0)
        {
            phase -= 1.0;
            newCycle = true;
        }

        // Get shape value (0 = silence, 1 = full volume)
        float shapeVal = computeShape(phase, newCycle);

        // Apply depth: gain = 1 - depth*(1-shapeVal)
        // depth=0: gain=1 always (no effect)
        // depth=1: gain=shapeVal (full LFO)
        float gain = 1.0f - depth * (1.0f - shapeVal);

        // Tiny smoothing to avoid clicks on shape transitions
        gain = prevGain + 0.002f * (gain - prevGain);
        prevGain = gain;

        return gain;
    }

    static const char* shapeName(int idx)
    {
        static const char* names[] = {
            "Sine", "Triangle", "Saw Down", "Saw Up",
            "Square", "Sidechain", "Trance Gate", "S&&H"
        };
        if (idx >= 0 && idx < NUM_SHAPES) return names[idx];
        return "?";
    }

private:
    float computeShape(double p, bool newCycle)
    {
        switch (shape)
        {
            case 0: // Sine: smooth tremolo (1 at phase 0, 0 at phase 0.5)
                return 0.5f + 0.5f * static_cast<float>(std::cos(p * PI2));

            case 1: // Triangle: peak at 0, trough at 0.5
                return static_cast<float>(p < 0.5 ? 1.0 - 2.0 * p : 2.0 * p - 1.0);

            case 2: // Saw Down: starts high, ramps to silence
                return static_cast<float>(1.0 - p);

            case 3: // Saw Up: starts silent, ramps up
                return static_cast<float>(p);

            case 4: // Square: on first half, off second half
                return p < 0.5 ? 1.0f : 0.0f;

            case 5: // Sidechain pump: duck at start, exponential recovery
            {
                // (1-p)^4 inverted: fast initial recovery, natural pump feel
                float inv = 1.0f - static_cast<float>(p);
                float inv2 = inv * inv;
                return 1.0f - inv2 * inv2;  // 1 - (1-p)^4
            }

            case 6: // Trance gate: 4 subdivisions per cycle, 75% duty
            {
                double sub = p * 4.0;
                sub -= std::floor(sub);
                return sub < 0.75 ? 1.0f : 0.0f;
            }

            case 7: // Sample & Hold: random level per cycle
            {
                if (newCycle)
                {
                    std::uniform_real_distribution<float> dist(0.0f, 1.0f);
                    holdValue = dist(rng);
                }
                return holdValue;
            }

            default:
                return 1.0f;
        }
    }

    double sr = 44100.0;
    double phase = 0.0;
    double rate = 2.0;
    float depth = 0.0f;
    int shape = 0;
    float holdValue = 1.0f;
    float prevGain = 1.0f;
    std::mt19937 rng;
};
