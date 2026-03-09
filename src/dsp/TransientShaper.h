#pragma once
#include <juce_dsp/juce_dsp.h>
#include <cmath>

/**
 * TransientShaper -- Removes pick attack from guitar to create synth-pad feel.
 * 
 * Based on the Boss SG-1 Slow Gear concept: envelope follower detects transients
 * and applies a slow volume swell, killing the sharp pick attack.
 *
 * Parameters:
 *   sensitivity: how easily it detects a new note (0.0 - 1.0)
 *   attack: how long the fade-in takes (10ms - 500ms)
 *   depth: how much attack is removed (0.0 = none, 1.0 = full removal)
 */
class TransientShaper
{
public:
    TransientShaper() = default;

    void prepare(double sampleRate, int /*blockSize*/)
    {
        sr = sampleRate;
        envelope = 0.0;
        gainRamp = 0.0;
        gateOpen = false;
        holdCounter = 0;
    }

    void setParameters(float sensitivity, float attackMs, float depth)
    {
        // Sensitivity maps to threshold (lower sensitivity = higher threshold)
        threshold = juce::jmap(sensitivity, 0.0f, 1.0f, 0.1f, 0.005f);
        
        // Attack time in samples
        float attackClamped = juce::jlimit(10.0f, 500.0f, attackMs);
        attackSamples = static_cast<int>(attackClamped * 0.001 * sr);
        
        // Depth controls how much of the dry attack bleeds through
        dryBleed = 1.0f - juce::jlimit(0.0f, 1.0f, depth);
        
        // Envelope follower coefficients
        envAttack = std::exp(-1.0 / (sr * 0.001));   // 1ms attack
        envRelease = std::exp(-1.0 / (sr * 0.050));   // 50ms release
    }

    float processSample(float input)
    {
        // Envelope follower
        float absInput = std::abs(input);
        if (absInput > envelope)
            envelope = envAttack * envelope + (1.0 - envAttack) * absInput;
        else
            envelope = envRelease * envelope + (1.0 - envRelease) * absInput;

        // Transient detection: new note when envelope rises above threshold
        if (!gateOpen && envelope > threshold)
        {
            gateOpen = true;
            gainRamp = 0.0;
            holdCounter = 0;
        }

        // Ramp up gain over attack time
        if (gateOpen)
        {
            holdCounter++;
            if (holdCounter < attackSamples)
            {
                // Smooth S-curve ramp (sine-based for natural feel)
                float phase = static_cast<float>(holdCounter) / static_cast<float>(attackSamples);
                gainRamp = 0.5f - 0.5f * std::cos(phase * juce::MathConstants<float>::pi);
            }
            else
            {
                gainRamp = 1.0f;
            }

            // Close gate when signal drops
            if (envelope < threshold * 0.3)
            {
                gateOpen = false;
            }
        }

        // Mix: full ramp gain + dry bleed for partial attack preservation
        float gain = gainRamp + dryBleed * (1.0f - gainRamp);
        return input * gain;
    }

    void processBlock(float* buffer, int numSamples)
    {
        for (int i = 0; i < numSamples; ++i)
            buffer[i] = processSample(buffer[i]);
    }

private:
    double sr = 44100.0;
    double envelope = 0.0;
    double envAttack = 0.0;
    double envRelease = 0.0;
    float threshold = 0.01f;
    int attackSamples = 4410;  // 100ms default
    float dryBleed = 0.0f;
    float gainRamp = 0.0f;
    bool gateOpen = false;
    int holdCounter = 0;
};
