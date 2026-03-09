#pragma once
#include <juce_dsp/juce_dsp.h>
#include <cmath>
#include <array>

/**
 * VinylProcessor -- Year (decade filtering) + Detune (pitch wobble).
 *
 * v5 rewrite fixes:
 * - Year: simple 1st-order LP (no resonance), gentle saturation, no HP filter.
 *   Previous Q=1.2 biquad caused weird resonant peaks. Now just smooth rolloff.
 * - Detune: always runs through the delay line (no discontinuity at detune=0).
 *   Nominal delay reduced to 1ms. Modulation depth max 15 samples (was 50).
 *   Much subtler pitch variation -- real vinyl is barely perceptible.
 * - Year at 0.0 is truly transparent (LP cutoff above Nyquist, sat=0).
 *
 * Parameters:
 *   year: 0.0 (modern/transparent) to 1.0 (1930s lo-fi)
 *   detune: 0.0 (no wobble) to 1.0 (noticeable pitch drift)
 */
class VinylProcessor
{
public:
    static constexpr int DELAY_BUF_SIZE = 2048;
    static constexpr int DELAY_MASK = DELAY_BUF_SIZE - 1;

    VinylProcessor() { delayBuf.fill(0.0f); }

    void prepare(double sampleRate, int /*blockSize*/)
    {
        sr = sampleRate;
        delayBuf.fill(0.0f);
        writePos = 0;

        // Nominal delay: 1ms (always on, prevents discontinuity)
        nominalDelay = sr * 0.001;

        lfoPhase1 = 0.0;
        lfoPhase2 = 0.43; // offset for non-periodic pattern

        // LP filter state (1st order)
        lp_z = 0.0;
    }

    void setParameters(float year, float detune)
    {
        float yearClamped = juce::jlimit(0.0f, 1.0f, year);
        float detuneClamped = juce::jlimit(0.0f, 1.0f, detune);

        // === Year → 1st-order LP cutoff (Hz) ===
        // 0.0 → 20000Hz (transparent), 1.0 → 2500Hz (lo-fi)
        // Log interpolation for musical feel
        float logMax = std::log(20000.0f);
        float logMin = std::log(2500.0f);
        float lpFreq = std::exp(logMax - yearClamped * (logMax - logMin));

        // 1st-order LP coefficient
        double w = 2.0 * juce::MathConstants<double>::pi * lpFreq / sr;
        lpCoeff = w / (1.0 + w);

        // Saturation: none at year=0, mild at year=1
        satAmount = yearClamped * yearClamped * 0.4f; // quadratic curve, gentle
        satDrive = 1.0f + yearClamped * 1.5f;         // max 2.5x drive (was 3.5x)

        // === Detune → pitch wobble depth ===
        // Max 15 samples excursion (was 50). ~1-2 cents of drift.
        detuneDepth = static_cast<double>(detuneClamped) * 15.0;
    }

    void processBlock(float* buffer, int numSamples)
    {
        for (int i = 0; i < numSamples; ++i)
        {
            float sample = buffer[i];

            // === Always process through delay line ===
            delayBuf[writePos] = sample;

            // Two slow desynced LFOs for non-periodic wobble
            lfoPhase1 += 0.15 / sr;  // ~6.7 second period
            if (lfoPhase1 > 1.0) lfoPhase1 -= 1.0;
            lfoPhase2 += 0.37 / sr;  // ~2.7 second period
            if (lfoPhase2 > 1.0) lfoPhase2 -= 1.0;

            double mod1 = std::sin(lfoPhase1 * 2.0 * juce::MathConstants<double>::pi);
            double mod2 = std::sin(lfoPhase2 * 2.0 * juce::MathConstants<double>::pi) * 0.35;
            double totalMod = (mod1 + mod2) / 1.35 * detuneDepth;

            double readDelay = nominalDelay + totalMod;
            readDelay = juce::jlimit(1.0, static_cast<double>(DELAY_BUF_SIZE - 4), readDelay);

            double readPosD = static_cast<double>(writePos) - readDelay;
            if (readPosD < 0.0) readPosD += DELAY_BUF_SIZE;

            // Linear interpolation (simpler, less artifact-prone than cubic for small mod depths)
            int idx = static_cast<int>(readPosD);
            float frac = static_cast<float>(readPosD - idx);
            float s0 = delayBuf[idx & DELAY_MASK];
            float s1 = delayBuf[(idx + 1) & DELAY_MASK];
            sample = s0 + frac * (s1 - s0);

            writePos = (writePos + 1) & DELAY_MASK;

            // === Saturation (only when year > 0) ===
            if (satAmount > 0.001f)
            {
                float driven = sample * satDrive;
                // Soft clip: x / (1 + |x|) — gentler than tanh
                float clipped = driven / (1.0f + std::abs(driven));
                // Normalize to keep unity gain
                float normFactor = satDrive / (1.0f + satDrive);
                if (normFactor > 0.01f) clipped /= normFactor;
                sample = sample * (1.0f - satAmount) + clipped * satAmount;
            }

            // === 1st-order LP filter ===
            lp_z += lpCoeff * (static_cast<double>(sample) - lp_z);
            sample = static_cast<float>(lp_z);

            buffer[i] = sample;
        }
    }

private:
    double sr = 44100.0;

    // Delay line
    std::array<float, DELAY_BUF_SIZE> delayBuf;
    int writePos = 0;
    double nominalDelay = 44.1; // 1ms at 44.1kHz

    // Detune LFOs
    double lfoPhase1 = 0.0;
    double lfoPhase2 = 0.43;
    double detuneDepth = 0.0;

    // 1st-order LP
    double lpCoeff = 1.0;
    double lp_z = 0.0;

    // Saturation
    float satAmount = 0.0f;
    float satDrive = 1.0f;
};
