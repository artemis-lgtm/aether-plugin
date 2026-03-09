#pragma once
#include <juce_dsp/juce_dsp.h>
#include <cmath>
#include <array>

/**
 * TransientShaper -- Auto-swell / attack remover.
 *
 * v5 rewrite: "make it sound literally like a sine wave swelling into the note"
 *
 * Architecture: Reverse noise gate. Audio is SILENCED by default. When a note
 * is detected, gain fades from 0.0 to 1.0 over the attack time using a
 * raised-cosine curve. The look-ahead (15ms) ensures the gain envelope starts
 * ramping well before the pick transient reaches the output -- so the transient
 * is completely muted.
 *
 * Key fix from v4: depth=1.0 default, and at depth=1.0 the formula gives
 * exactly 0.0 gain in IDLE (no bleed). Previous bug: depth=0.8 allowed 20%
 * attack bleed even when gain was "zero."
 *
 * Parameters:
 *   sensitivity: 0=needs loud attack to trigger, 1=triggers on quiet playing
 *   attack: swell rise time in ms (10-800ms)
 *   depth: 0=no effect, 1=full swell (complete attack removal)
 */
class TransientShaper
{
public:
    // Look-ahead: 15ms at 48kHz = 720 samples. Buffer 1024 for safety.
    static constexpr int LA_SIZE = 1024;

    TransientShaper() { lookahead.fill(0.0f); }

    void prepare(double sampleRate, int /*blockSize*/)
    {
        sr = sampleRate;
        lookahead.fill(0.0f);
        laWritePos = 0;

        // 15ms look-ahead — plenty of time for gain to be near-zero when transient arrives
        lookaheadSamples = static_cast<int>(sr * 0.015);
        if (lookaheadSamples >= LA_SIZE) lookaheadSamples = LA_SIZE - 1;

        envelope = 0.0;
        currentGain = 0.0f;
        targetGain = 0.0f;
        gateOpen = false;

        // Envelope follower: very fast attack (0.1ms), moderate release (50ms)
        envAttackCoeff  = std::exp(-1.0 / (sr * 0.0001));
        envReleaseCoeff = std::exp(-1.0 / (sr * 0.050));
    }

    void setParameters(float sensitivity, float attackMs, float depth)
    {
        // Higher sensitivity = lower threshold
        threshold = juce::jmap(sensitivity, 0.0f, 1.0f, 0.05f, 0.001f);
        closeThreshold = threshold * 0.08; // gate closes well below open threshold

        // Attack time: how long the swell takes
        float attackClamped = juce::jlimit(10.0f, 800.0f, attackMs);
        attackSamples = static_cast<int>(attackClamped * 0.001 * sr);
        if (attackSamples < 1) attackSamples = 1;

        depthAmount = juce::jlimit(0.0f, 1.0f, depth);

        // Gain smoothing coefficient (prevents clicks) — ~2ms
        gainSmooth = static_cast<float>(std::exp(-1.0 / (sr * 0.002)));
    }

    void processBlock(float* buffer, int numSamples)
    {
        for (int i = 0; i < numSamples; ++i)
        {
            // Write to look-ahead buffer
            lookahead[laWritePos] = buffer[i];

            // Read delayed signal (15ms behind)
            int readPos = (laWritePos - lookaheadSamples + LA_SIZE) % LA_SIZE;
            float delayed = lookahead[readPos];
            laWritePos = (laWritePos + 1) % LA_SIZE;

            // Envelope follower on CURRENT (non-delayed) input
            double absIn = static_cast<double>(std::abs(buffer[i]));
            if (absIn > envelope)
                envelope = envAttackCoeff * envelope + (1.0 - envAttackCoeff) * absIn;
            else
                envelope = envReleaseCoeff * envelope + (1.0 - envReleaseCoeff) * absIn;

            // Gate logic: open when signal detected, close when signal dies
            if (!gateOpen && envelope > threshold)
            {
                gateOpen = true;
                swellCounter = 0;
                swellStartGain = currentGain; // start from wherever we are (could be mid-release)
            }
            else if (gateOpen && envelope < closeThreshold)
            {
                gateOpen = false;
            }

            // Compute target gain
            if (gateOpen)
            {
                swellCounter++;
                float phase = static_cast<float>(swellCounter) / static_cast<float>(attackSamples);
                if (phase >= 1.0f)
                {
                    targetGain = 1.0f;
                }
                else
                {
                    // Raised cosine: very flat at the start (almost zero), accelerates, then settles
                    float curve = 0.5f - 0.5f * std::cos(phase * juce::MathConstants<float>::pi);
                    // Blend from starting gain to 1.0
                    targetGain = swellStartGain + (1.0f - swellStartGain) * curve;
                }
            }
            else
            {
                // Gate closed: fade to zero (slow release, ~200ms)
                targetGain *= 0.9997f;
                if (targetGain < 0.0001f) targetGain = 0.0f;
            }

            // Smooth gain changes to prevent clicks
            currentGain = gainSmooth * currentGain + (1.0f - gainSmooth) * targetGain;

            // Apply: at depth=1.0 and currentGain=0, effectGain=0 (complete silence)
            float effectGain = 1.0f - depthAmount * (1.0f - currentGain);
            buffer[i] = delayed * effectGain;
        }
    }

private:
    double sr = 44100.0;

    // Look-ahead ring buffer
    std::array<float, LA_SIZE> lookahead;
    int laWritePos = 0;
    int lookaheadSamples = 660; // 15ms at 44.1kHz

    // Envelope follower
    double envelope = 0.0;
    double envAttackCoeff = 0.0;
    double envReleaseCoeff = 0.0;

    // Gate state
    bool gateOpen = false;
    float currentGain = 0.0f;
    float targetGain = 0.0f;
    float swellStartGain = 0.0f;
    int swellCounter = 0;
    float gainSmooth = 0.998f;

    // Parameters
    double threshold = 0.01;
    double closeThreshold = 0.001;
    int attackSamples = 6615;
    float depthAmount = 1.0f;
};
