#pragma once
#include <juce_dsp/juce_dsp.h>
#include <cmath>
#include <array>

/**
 * PsychedelicProcessor -- Spectral/shimmer psychedelic effects.
 * 
 * Inspired by Enigma-style spectral processing: creates evolving,
 * otherworldly textures from any input. Shimmer reverb, modulated
 * delays, chorus, and spectral smearing.
 *
 * Signal chain: Chorus → Modulated Delay → Shimmer Reverb
 *
 * Parameters:
 *   shimmer: pitch-shifted reverb tail intensity (0.0 - 1.0)
 *   space: reverb size/decay (0.0 - 1.0)
 *   modulation: chorus/phaser movement speed and depth (0.0 - 1.0)
 *   warp: delay feedback with pitch drift (0.0 - 1.0)
 *   mix: wet/dry blend (0.0 - 1.0)
 */
class PsychedelicProcessor
{
public:
    static constexpr int MAX_DELAY = 96000;  // ~2s at 48kHz
    static constexpr int REVERB_TAPS = 8;

    PsychedelicProcessor()
    {
        delayLine.fill(0.0f);
        for (auto& tap : reverbBuffer)
            tap.fill(0.0f);
        chorusBuffer.fill(0.0f);
    }

    void prepare(double sampleRate, int /*blockSize*/)
    {
        sr = sampleRate;
        
        // Clear buffers
        delayLine.fill(0.0f);
        for (auto& tap : reverbBuffer)
            tap.fill(0.0f);
        chorusBuffer.fill(0.0f);
        
        delayWritePos = 0;
        chorusWritePos = 0;
        for (auto& pos : reverbWritePos)
            pos = 0;
        
        chorusLfoPhase = 0.0;
        delayLfoPhase = 0.0;
        shimmerAccum = 0.0f;
        
        // Reverb tap delay times (prime-number-based for density)
        reverbDelayTimes[0] = static_cast<int>(0.0297 * sr);
        reverbDelayTimes[1] = static_cast<int>(0.0371 * sr);
        reverbDelayTimes[2] = static_cast<int>(0.0411 * sr);
        reverbDelayTimes[3] = static_cast<int>(0.0437 * sr);
        reverbDelayTimes[4] = static_cast<int>(0.0533 * sr);
        reverbDelayTimes[5] = static_cast<int>(0.0671 * sr);
        reverbDelayTimes[6] = static_cast<int>(0.0797 * sr);
        reverbDelayTimes[7] = static_cast<int>(0.0907 * sr);
    }

    void setParameters(float shimmer, float space, float modulation, float warp, float mix)
    {
        shimmerAmount = juce::jlimit(0.0f, 1.0f, shimmer);
        
        // Reverb decay: maps to feedback coefficient
        reverbDecay = juce::jmap(space, 0.0f, 1.0f, 0.3f, 0.92f);
        
        // Chorus LFO rate and depth
        chorusRate = juce::jmap(modulation, 0.0f, 1.0f, 0.2f, 3.0f);
        chorusDepth = juce::jmap(modulation, 0.0f, 1.0f, 0.0f, 0.005f) * static_cast<float>(sr);
        
        // Modulated delay
        delayTime = static_cast<int>(juce::jmap(warp, 0.0f, 1.0f, 0.05f, 0.4f) * sr);
        delayFeedback = juce::jmap(warp, 0.0f, 1.0f, 0.0f, 0.75f);
        delayModDepth = juce::jmap(warp, 0.0f, 1.0f, 0.0f, 0.002f) * static_cast<float>(sr);
        
        wetDry = juce::jlimit(0.0f, 1.0f, mix);
    }

    float processSample(float input)
    {
        float dry = input;
        
        // === Stage 1: Chorus ===
        chorusLfoPhase += chorusRate / sr;
        if (chorusLfoPhase > 1.0) chorusLfoPhase -= 1.0;
        
        float chorusLfo = static_cast<float>(std::sin(chorusLfoPhase * 2.0 * juce::MathConstants<double>::pi));
        float chorusDelaySamples = 15.0f + chorusLfo * chorusDepth;
        
        // Write to chorus buffer
        chorusBuffer[chorusWritePos] = input;
        
        // Read with interpolation
        float chorusReadPos = static_cast<float>(chorusWritePos) - chorusDelaySamples;
        if (chorusReadPos < 0.0f) chorusReadPos += MAX_DELAY;
        int readIdx = static_cast<int>(chorusReadPos);
        float frac = chorusReadPos - readIdx;
        float chorusOut = chorusBuffer[readIdx % MAX_DELAY] * (1.0f - frac) 
                        + chorusBuffer[(readIdx + 1) % MAX_DELAY] * frac;
        
        chorusWritePos = (chorusWritePos + 1) % MAX_DELAY;
        float chorusMixed = input * 0.7f + chorusOut * 0.3f;
        
        // === Stage 2: Modulated Delay ===
        delayLfoPhase += 0.13 / sr;  // Very slow modulation
        if (delayLfoPhase > 1.0) delayLfoPhase -= 1.0;
        float delayMod = static_cast<float>(std::sin(delayLfoPhase * 2.0 * juce::MathConstants<double>::pi)) * delayModDepth;
        
        int modDelayTime = juce::jlimit(1, MAX_DELAY - 1, delayTime + static_cast<int>(delayMod));
        
        // Read from delay
        int delayReadPos = (delayWritePos - modDelayTime + MAX_DELAY) % MAX_DELAY;
        float delayOut = delayLine[delayReadPos];
        
        // Write with feedback
        delayLine[delayWritePos] = chorusMixed + delayOut * delayFeedback;
        delayWritePos = (delayWritePos + 1) % MAX_DELAY;
        
        float delayMixed = chorusMixed + delayOut * delayFeedback * 0.5f;
        
        // === Stage 3: Shimmer Reverb ===
        // Multi-tap FDN (Feedback Delay Network) reverb
        float reverbIn = delayMixed;
        float reverbOut = 0.0f;
        
        for (int t = 0; t < REVERB_TAPS; ++t)
        {
            int tapDelay = reverbDelayTimes[t];
            int readPos = (reverbWritePos[t] - tapDelay + MAX_DELAY) % MAX_DELAY;
            float tapOut = reverbBuffer[t][readPos];
            reverbOut += tapOut;
            
            // Feed back with cross-mixing between taps for density
            float crossMix = reverbBuffer[(t + 1) % REVERB_TAPS]
                            [(reverbWritePos[(t + 1) % REVERB_TAPS] - tapDelay / 2 + MAX_DELAY) % MAX_DELAY];
            
            float fbSignal = (tapOut * 0.7f + crossMix * 0.3f) * reverbDecay;
            
            // Shimmer: pitch-shift up an octave by reading at half speed
            // (simplified: we blend in an octave-up signal from earlier in the buffer)
            if (shimmerAmount > 0.0f)
            {
                int shimmerReadPos = (reverbWritePos[t] - tapDelay * 2 + MAX_DELAY * 2) % MAX_DELAY;
                float shimmerSample = reverbBuffer[t][shimmerReadPos];
                fbSignal += shimmerSample * shimmerAmount * 0.3f;
            }
            
            // Soft clip the feedback to prevent runaway
            fbSignal = std::tanh(fbSignal);
            
            reverbBuffer[t][reverbWritePos[t]] = reverbIn / REVERB_TAPS + fbSignal;
            reverbWritePos[t] = (reverbWritePos[t] + 1) % MAX_DELAY;
        }
        
        reverbOut /= REVERB_TAPS;
        
        // === Final mix ===
        float wet = reverbOut;
        return dry * (1.0f - wetDry) + wet * wetDry;
    }

    void processBlock(float* buffer, int numSamples)
    {
        for (int i = 0; i < numSamples; ++i)
            buffer[i] = processSample(buffer[i]);
    }

private:
    double sr = 44100.0;
    
    // Chorus
    std::array<float, MAX_DELAY> chorusBuffer;
    int chorusWritePos = 0;
    double chorusLfoPhase = 0.0;
    float chorusRate = 1.0f;
    float chorusDepth = 0.0f;
    
    // Modulated delay
    std::array<float, MAX_DELAY> delayLine;
    int delayWritePos = 0;
    double delayLfoPhase = 0.0;
    int delayTime = 22050;
    float delayFeedback = 0.3f;
    float delayModDepth = 0.0f;
    
    // Reverb (FDN)
    std::array<std::array<float, MAX_DELAY>, REVERB_TAPS> reverbBuffer;
    std::array<int, REVERB_TAPS> reverbWritePos = {};
    std::array<int, REVERB_TAPS> reverbDelayTimes = {};
    float reverbDecay = 0.7f;
    float shimmerAmount = 0.3f;
    float shimmerAccum = 0.0f;
    
    // Output
    float wetDry = 0.5f;
};
