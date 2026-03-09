#pragma once
#include <juce_dsp/juce_dsp.h>
#include <cmath>
#include <random>
#include <array>

/**
 * VinylProcessor -- iZotope Vinyl-style decade emulation + detune.
 *
 * v4 rewrite: Stripped to Year + Detune only (Austin's directive).
 * Removed warp, dust, wear, noise parameters.
 *
 * Year (Decade) emulation based on historical vinyl frequency response:
 *   0.0 (2000s): LP ~18kHz, HP ~20Hz, no saturation — nearly transparent
 *   0.33 (1970s): LP ~12kHz, HP ~30Hz, light warmth, mild saturation
 *   0.66 (1950s): LP ~6kHz, HP ~60Hz, moderate saturation, narrower bandwidth
 *   1.0 (1930s): LP ~3.5kHz, HP ~100Hz, heavy saturation, narrow bandwidth, lo-fi
 *
 * Uses 2nd-order Butterworth LP + 1st-order HP + soft saturation.
 * Resonant bump near the LP cutoff for "phonograph" character at older decades.
 *
 * Detune: subtle vinyl-like pitch wobble via delay line modulation.
 * Two slow LFOs (0.12Hz + 0.31Hz) with max ~50 samples excursion at 44.1kHz
 * for realistic 2-5 cent pitch variation (real vinyl = 0.1-0.5% wow).
 *
 * Parameters:
 *   year: 0.0 (modern/2000s) to 1.0 (1930s lo-fi)
 *   detune: 0.0 (off) to 1.0 (heavy pitch wobble)
 */
class VinylProcessor
{
public:
    static constexpr int DELAY_BUF_SIZE = 4096;
    static constexpr int DELAY_MASK = DELAY_BUF_SIZE - 1;

    VinylProcessor() { delayBuf.fill(0.0f); }

    void prepare(double sampleRate, int /*blockSize*/)
    {
        sr = sampleRate;
        delayBuf.fill(0.0f);
        writePos = 0;

        // Nominal center delay for pitch modulation: 3ms
        nominalDelay = sr * 0.003;

        // LFO phases
        lfoPhase1 = 0.0;
        lfoPhase2 = 0.37;

        // Filter states (2nd-order LP: biquad, 1st-order HP)
        lp_z1 = lp_z2 = 0.0;
        hp_z1 = 0.0;

        // Saturation
        satDrive = 1.0;
    }

    void setParameters(float year, float detune)
    {
        // ======== Year -> filter cutoffs ========
        // Interpolate: year 0.0=2000s, 0.33=1970s, 0.66=1950s, 1.0=1930s
        float yearClamped = juce::jlimit(0.0f, 1.0f, year);

        // Low-pass cutoff (Hz)
        // 2000s: 18000, 1970s: 12000, 1950s: 6000, 1930s: 3500
        float lpFreq = juce::jmap(yearClamped, 0.0f, 1.0f, 18000.0f, 3500.0f);
        // Use logarithmic interpolation for more natural feel
        float logLpMin = std::log(3500.0f);
        float logLpMax = std::log(18000.0f);
        lpFreq = std::exp(logLpMax - yearClamped * (logLpMax - logLpMin));

        // High-pass cutoff (Hz)
        float hpFreq = juce::jmap(yearClamped, 0.0f, 1.0f, 20.0f, 100.0f);

        // Resonance: older decades get a slight bump near LP cutoff (phonograph character)
        float Q = juce::jmap(yearClamped, 0.0f, 1.0f, 0.707f, 1.2f);

        // ======== Compute 2nd-order LP biquad coefficients ========
        double w0 = 2.0 * juce::MathConstants<double>::pi * lpFreq / sr;
        double alpha = std::sin(w0) / (2.0 * Q);
        double cosw0 = std::cos(w0);

        double b0 = (1.0 - cosw0) / 2.0;
        double b1 = 1.0 - cosw0;
        double b2 = (1.0 - cosw0) / 2.0;
        double a0 = 1.0 + alpha;
        double a1 = -2.0 * cosw0;
        double a2 = 1.0 - alpha;

        lp_b0 = b0 / a0;
        lp_b1 = b1 / a0;
        lp_b2 = b2 / a0;
        lp_a1 = a1 / a0;
        lp_a2 = a2 / a0;

        // ======== 1st-order HP coefficient ========
        double hpW = 2.0 * juce::MathConstants<double>::pi * hpFreq / sr;
        hpCoeff = 1.0 - std::exp(-hpW);

        // ======== Saturation drive (older = more) ========
        satDrive = juce::jmap(yearClamped, 0.0f, 1.0f, 1.0f, 3.5f);
        satMix = juce::jmap(yearClamped, 0.0f, 1.0f, 0.0f, 0.6f);

        // ======== Detune depth (samples of delay excursion) ========
        // 0-50 samples at 44.1kHz ≈ 0-5 cents of pitch variation
        float detuneClamped = juce::jlimit(0.0f, 1.0f, detune);
        detuneDepth = static_cast<double>(juce::jmap(detuneClamped, 0.0f, 1.0f, 0.0f, 50.0f));
    }

    float processSample(float input)
    {
        float processed = input;

        // === Detune: delay-line pitch modulation ===
        if (detuneDepth > 0.05)
        {
            delayBuf[writePos] = processed;

            // Two desynced LFOs for non-periodic wobble
            lfoPhase1 += 0.12 / sr;
            if (lfoPhase1 > 1.0) lfoPhase1 -= 1.0;
            lfoPhase2 += 0.31 / sr;
            if (lfoPhase2 > 1.0) lfoPhase2 -= 1.0;

            double mod1 = std::sin(lfoPhase1 * 2.0 * juce::MathConstants<double>::pi);
            double mod2 = std::sin(lfoPhase2 * 2.0 * juce::MathConstants<double>::pi) * 0.4;
            double totalMod = (mod1 + mod2) / 1.4 * detuneDepth;

            double readDelay = nominalDelay + totalMod;
            readDelay = juce::jlimit(1.0, static_cast<double>(DELAY_BUF_SIZE - 4), readDelay);

            double readPos = static_cast<double>(writePos) - readDelay;
            if (readPos < 0.0) readPos += DELAY_BUF_SIZE;

            int idx = static_cast<int>(readPos);
            float frac = static_cast<float>(readPos - idx);

            // Cubic Hermite interpolation
            float ym1 = delayBuf[(idx - 1) & DELAY_MASK];
            float y0  = delayBuf[idx & DELAY_MASK];
            float y1  = delayBuf[(idx + 1) & DELAY_MASK];
            float y2  = delayBuf[(idx + 2) & DELAY_MASK];

            float c0 = y0;
            float c1 = 0.5f * (y1 - ym1);
            float c2 = ym1 - 2.5f * y0 + 2.0f * y1 - 0.5f * y2;
            float c3 = 0.5f * (y2 - ym1) + 1.5f * (y0 - y1);
            processed = ((c3 * frac + c2) * frac + c1) * frac + c0;

            writePos = (writePos + 1) & DELAY_MASK;
        }

        // === Saturation (warm asymmetric soft-clip, older decades = more) ===
        if (satMix > 0.001f)
        {
            float driven = processed * static_cast<float>(satDrive);
            float saturated = std::tanh(driven);
            // Normalize: divide by tanh(drive) to keep unity gain
            float norm = std::tanh(static_cast<float>(satDrive));
            if (norm > 0.01f) saturated /= norm;
            processed = processed * (1.0f - satMix) + saturated * satMix;
        }

        // === 2nd-order Low-pass filter (biquad, Transposed Direct Form II) ===
        double x = static_cast<double>(processed);
        double y = lp_b0 * x + lp_z1;
        lp_z1 = lp_b1 * x - lp_a1 * y + lp_z2;
        lp_z2 = lp_b2 * x - lp_a2 * y;
        processed = static_cast<float>(y);

        // === 1st-order High-pass filter ===
        hp_z1 += hpCoeff * (processed - hp_z1);
        processed = processed - static_cast<float>(hp_z1);

        return processed;
    }

    void processBlock(float* buffer, int numSamples)
    {
        for (int i = 0; i < numSamples; ++i)
            buffer[i] = processSample(buffer[i]);
    }

private:
    double sr = 44100.0;

    // Delay line for detune
    std::array<float, DELAY_BUF_SIZE> delayBuf;
    int writePos = 0;
    double nominalDelay = 132.0;
    double detuneDepth = 0.0;

    // Detune LFOs
    double lfoPhase1 = 0.0;
    double lfoPhase2 = 0.37;

    // 2nd-order LP biquad coefficients
    double lp_b0 = 1.0, lp_b1 = 0.0, lp_b2 = 0.0;
    double lp_a1 = 0.0, lp_a2 = 0.0;
    double lp_z1 = 0.0, lp_z2 = 0.0;

    // 1st-order HP
    double hpCoeff = 0.0;
    double hp_z1 = 0.0;

    // Saturation
    double satDrive = 1.0;
    float satMix = 0.0f;
};
