#pragma once
#include <juce_dsp/juce_dsp.h>
#include <cmath>
#include <array>

/**
 * TransientShaper -- Auto-swell / attack remover (Boss SG-1 Slow Gear style).
 *
 * v4 rewrite: Added look-ahead buffer so the gain envelope leads the audio.
 * The transient is detected 5ms before it reaches the output, allowing the
 * gain to start at zero and ramp up AFTER the attack has already passed
 * in the lookahead window.
 *
 * State machine: IDLE -> SWELLING -> SUSTAIN -> RELEASING -> IDLE
 *   - IDLE: gain = 0, waiting for transient
 *   - SWELLING: S-curve ramp from 0 to 1 over attack time
 *   - SUSTAIN: gain = 1, note is ringing
 *   - RELEASING: slow fade to 0 after note decays
 *
 * Parameters:
 *   sensitivity: threshold for detecting new notes (0=insensitive, 1=very sensitive)
 *   attack: swell time in ms (10-800ms)
 *   depth: how much attack is removed (0=none, 1=full)
 */
class TransientShaper
{
public:
    // Look-ahead buffer: ~5ms at 48kHz = 240 samples, use 512 for headroom
    static constexpr int LA_SIZE = 512;

    TransientShaper() { lookahead.fill(0.0f); }

    void prepare(double sampleRate, int /*blockSize*/)
    {
        sr = sampleRate;
        lookahead.fill(0.0f);
        laWritePos = 0;

        // Look-ahead: 5ms
        lookaheadSamples = static_cast<int>(sr * 0.005);
        if (lookaheadSamples >= LA_SIZE) lookaheadSamples = LA_SIZE - 1;

        envelope = 0.0;
        currentGain = 0.0f;
        state = IDLE;
        swellCounter = 0;

        // Envelope follower: 0.5ms attack, 30ms release
        envAttackCoeff  = std::exp(-1.0 / (sr * 0.0005));
        envReleaseCoeff = std::exp(-1.0 / (sr * 0.030));
    }

    void setParameters(float sensitivity, float attackMs, float depth)
    {
        // Sensitivity: high sens = low threshold
        threshold = juce::jmap(sensitivity, 0.0f, 1.0f, 0.08f, 0.002f);
        
        // Release threshold: note is "done" when envelope drops to this fraction of trigger threshold
        releaseThreshold = threshold * 0.15;

        // Attack time in samples (10-800ms)
        float attackClamped = juce::jlimit(10.0f, 800.0f, attackMs);
        attackSamples = static_cast<int>(attackClamped * 0.001 * sr);
        if (attackSamples < 1) attackSamples = 1;

        // Depth: 0 = no effect (full attack), 1 = complete swell (no attack)
        depthAmount = juce::jlimit(0.0f, 1.0f, depth);
    }

    float processSample(float input)
    {
        // === Write to look-ahead buffer ===
        lookahead[laWritePos] = input;

        // === Read delayed signal (5ms behind) ===
        int readPos = (laWritePos - lookaheadSamples + LA_SIZE) % LA_SIZE;
        float delayed = lookahead[readPos];
        laWritePos = (laWritePos + 1) % LA_SIZE;

        // === Envelope follower on current (non-delayed) input ===
        double absIn = static_cast<double>(std::abs(input));
        if (absIn > envelope)
            envelope = envAttackCoeff * envelope + (1.0 - envAttackCoeff) * absIn;
        else
            envelope = envReleaseCoeff * envelope + (1.0 - envReleaseCoeff) * absIn;

        // === State machine ===
        switch (state)
        {
            case IDLE:
                currentGain = 0.0f;
                if (envelope > threshold)
                {
                    state = SWELLING;
                    swellCounter = 0;
                }
                break;

            case SWELLING:
            {
                swellCounter++;
                float phase = static_cast<float>(swellCounter) / static_cast<float>(attackSamples);
                if (phase >= 1.0f)
                {
                    currentGain = 1.0f;
                    state = SUSTAIN;
                }
                else
                {
                    // S-curve (raised cosine) for natural swell feel
                    currentGain = 0.5f - 0.5f * std::cos(phase * juce::MathConstants<float>::pi);
                }
                break;
            }

            case SUSTAIN:
                currentGain = 1.0f;
                if (envelope < releaseThreshold)
                    state = RELEASING;
                break;

            case RELEASING:
                // Exponential fade to zero
                currentGain *= 0.9985f;
                if (currentGain < 0.001f)
                {
                    currentGain = 0.0f;
                    state = IDLE;
                }
                // Re-trigger if new note arrives during release
                if (envelope > threshold)
                {
                    state = SWELLING;
                    swellCounter = 0;
                    // Don't reset currentGain to 0 — start ramp from current position
                }
                break;
        }

        // === Apply depth-weighted gain ===
        // At depth=0: effectGain=1.0 always (no swell). At depth=1: effectGain=currentGain (full swell).
        float effectGain = 1.0f - depthAmount * (1.0f - currentGain);
        return delayed * effectGain;
    }

    void processBlock(float* buffer, int numSamples)
    {
        for (int i = 0; i < numSamples; ++i)
            buffer[i] = processSample(buffer[i]);
    }

private:
    double sr = 44100.0;

    // Look-ahead ring buffer
    std::array<float, LA_SIZE> lookahead;
    int laWritePos = 0;
    int lookaheadSamples = 220;

    // Envelope follower
    double envelope = 0.0;
    double envAttackCoeff = 0.0;
    double envReleaseCoeff = 0.0;

    // State machine
    enum State { IDLE, SWELLING, SUSTAIN, RELEASING };
    State state = IDLE;
    int swellCounter = 0;
    float currentGain = 0.0f;

    // Parameters
    double threshold = 0.01;
    double releaseThreshold = 0.002;
    int attackSamples = 4410;
    float depthAmount = 0.8f;
};
