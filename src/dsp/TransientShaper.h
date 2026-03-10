#pragma once
#include <juce_dsp/juce_dsp.h>
#include <cmath>
#include <array>

/**
 * TransientShaper -- Auto-swell / attack remover.
 *
 * v6 AGGRESSIVE rewrite: retriggers on every new note onset.
 *
 * Architecture: Envelope follower detects note onsets (sharp rises in amplitude).
 * On each onset, gain resets to zero and ramps up over the attack time using
 * a raised-cosine curve. The look-ahead (15ms) ensures the transient is muted.
 *
 * Key fix from v5: RETRIGGER. When a new transient is detected (envelope rises
 * sharply), the swell resets even if the gate is already open. This means EVERY
 * note gets the swell treatment, not just the first one.
 *
 * Parameters:
 *   sensitivity: 0=needs loud attack to trigger, 1=triggers on quiet playing
 *   attack: swell rise time in ms (10-2000ms) -- EXTENDED range for more drama
 *   depth: 0=no effect, 1=full swell (complete attack removal)
 */
class TransientShaper
{
public:
    static constexpr int LA_SIZE = 2048;

    TransientShaper() { lookahead.fill(0.0f); }

    void prepare(double sampleRate, int /*blockSize*/)
    {
        sr = sampleRate;
        lookahead.fill(0.0f);
        laWritePos = 0;

        // 20ms look-ahead for better transient suppression
        lookaheadSamples = static_cast<int>(sr * 0.020);
        if (lookaheadSamples >= LA_SIZE) lookaheadSamples = LA_SIZE - 1;

        envelope = 0.0;
        slowEnvelope = 0.0;
        currentGain = 0.0f;
        targetGain = 0.0f;
        gateOpen = false;
        swellCounter = 0;
        peakHold = 0.0;
        holdCounter = 0;

        // Envelope follower: very fast attack (0.05ms), moderate release (30ms)
        envAttackCoeff  = std::exp(-1.0 / (sr * 0.00005));
        envReleaseCoeff = std::exp(-1.0 / (sr * 0.030));

        // Slow envelope for onset detection (attack ~5ms, release ~100ms)
        slowAttackCoeff  = std::exp(-1.0 / (sr * 0.005));
        slowReleaseCoeff = std::exp(-1.0 / (sr * 0.100));
    }

    void setParameters(float sensitivity, float attackMs, float depth)
    {
        // Higher sensitivity = lower threshold AND lower onset ratio
        float sensClamped = juce::jlimit(0.0f, 1.0f, sensitivity);
        threshold = juce::jmap(sensClamped, 0.0f, 1.0f, 0.08f, 0.0005f);
        closeThreshold = threshold * 0.05;

        // Onset detection: ratio of fast/slow envelope that triggers retrigger
        // At max sensitivity, even small increases retrigger
        onsetRatio = juce::jmap(sensClamped, 0.0f, 1.0f, 6.0f, 1.8f);

        // Attack time: how long the swell takes (EXTENDED range)
        float attackClamped = juce::jlimit(10.0f, 2000.0f, attackMs);
        attackSamples = static_cast<int>(attackClamped * 0.001 * sr);
        if (attackSamples < 1) attackSamples = 1;

        depthAmount = juce::jlimit(0.0f, 1.0f, depth);

        // Gain smoothing: ~1ms (fast enough to kill transients)
        gainSmooth = static_cast<float>(std::exp(-1.0 / (sr * 0.001)));
    }

    void processBlock(float* buffer, int numSamples)
    {
        for (int i = 0; i < numSamples; ++i)
        {
            // Write to look-ahead buffer
            lookahead[laWritePos] = buffer[i];

            // Read delayed signal
            int readPos = (laWritePos - lookaheadSamples + LA_SIZE) % LA_SIZE;
            float delayed = lookahead[readPos];
            laWritePos = (laWritePos + 1) % LA_SIZE;

            // === FAST envelope (for gate open/close) ===
            double absIn = static_cast<double>(std::abs(buffer[i]));
            if (absIn > envelope)
                envelope = envAttackCoeff * envelope + (1.0 - envAttackCoeff) * absIn;
            else
                envelope = envReleaseCoeff * envelope + (1.0 - envReleaseCoeff) * absIn;

            // === SLOW envelope (for onset detection) ===
            if (absIn > slowEnvelope)
                slowEnvelope = slowAttackCoeff * slowEnvelope + (1.0 - slowAttackCoeff) * absIn;
            else
                slowEnvelope = slowReleaseCoeff * slowEnvelope + (1.0 - slowReleaseCoeff) * absIn;

            // === ONSET DETECTION: fast envelope jumps well above slow envelope ===
            bool onsetDetected = false;
            if (slowEnvelope > 0.00001 && envelope > threshold)
            {
                double ratio = envelope / (slowEnvelope + 0.00001);
                if (ratio > onsetRatio)
                    onsetDetected = true;
            }
            else if (!gateOpen && envelope > threshold)
            {
                // First note from silence
                onsetDetected = true;
            }

            // Cooldown: don't retrigger within 30ms of last trigger
            if (holdCounter > 0)
            {
                holdCounter--;
                onsetDetected = false;
            }

            // === Gate + Retrigger logic ===
            if (onsetDetected)
            {
                gateOpen = true;
                swellCounter = 0;
                swellStartGain = 0.0f;  // Always reset to zero on new onset
                targetGain = 0.0f;
                holdCounter = static_cast<int>(sr * 0.030);  // 30ms cooldown
            }
            else if (gateOpen && envelope < closeThreshold)
            {
                gateOpen = false;
            }

            // === Compute target gain ===
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
                    // Raised cosine: very flat start, accelerates, settles
                    float curve = 0.5f - 0.5f * std::cos(phase * juce::MathConstants<float>::pi);
                    targetGain = swellStartGain + (1.0f - swellStartGain) * curve;
                }
            }
            else
            {
                // Gate closed: fast fade to zero (~50ms)
                targetGain *= 0.9990f;
                if (targetGain < 0.0001f) targetGain = 0.0f;
            }

            // Smooth gain changes
            currentGain = gainSmooth * currentGain + (1.0f - gainSmooth) * targetGain;

            // Apply depth
            float effectGain = 1.0f - depthAmount * (1.0f - currentGain);
            buffer[i] = delayed * effectGain;
        }
    }

private:
    double sr = 44100.0;

    // Look-ahead ring buffer
    std::array<float, LA_SIZE> lookahead;
    int laWritePos = 0;
    int lookaheadSamples = 882;

    // Fast envelope follower (gate trigger)
    double envelope = 0.0;
    double envAttackCoeff = 0.0;
    double envReleaseCoeff = 0.0;

    // Slow envelope follower (onset detection baseline)
    double slowEnvelope = 0.0;
    double slowAttackCoeff = 0.0;
    double slowReleaseCoeff = 0.0;

    // Gate state
    bool gateOpen = false;
    float currentGain = 0.0f;
    float targetGain = 0.0f;
    float swellStartGain = 0.0f;
    int swellCounter = 0;
    float gainSmooth = 0.999f;
    int holdCounter = 0;

    // Onset detection
    double onsetRatio = 3.0;
    double peakHold = 0.0;

    // Parameters
    double threshold = 0.01;
    double closeThreshold = 0.0005;
    int attackSamples = 6615;
    float depthAmount = 1.0f;
};
