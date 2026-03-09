#pragma once
#include <juce_dsp/juce_dsp.h>
#include <cmath>
#include <array>

/**
 * PsychedelicProcessor -- Spectral/shimmer psychedelic effects.
 * 
 * Combines Enigma-style swept notch filter bank with shimmer reverb,
 * modulated delays, and chorus for evolving psychedelic textures.
 *
 * Signal chain: Notch Sweep → Chorus → Modulated Delay → Shimmer Reverb
 *
 * The notch sweep is the core Enigma feature: multiple notch (band-reject)
 * filters whose center frequencies are swept by an LFO across the spectrum.
 * This creates the distinctive phaser-like but more complex spectral movement.
 *
 * Parameters:
 *   shimmer:    pitch-shifted reverb tail intensity (0.0 - 1.0)
 *   space:      reverb size/decay (0.0 - 1.0)
 *   modulation: sweep & chorus speed (0.0 - 1.0)
 *   warp:       delay feedback with pitch drift (0.0 - 1.0)
 *   mix:        wet/dry blend (0.0 - 1.0)
 *   notches:    number of notch filter pairs, 0=off (0.0 - 1.0 → 0-6 pairs)
 *   sweep:      notch sweep frequency range width (0.0 - 1.0)
 */
class PsychedelicProcessor
{
public:
    static constexpr int MAX_DELAY = 96000;  // ~2s at 48kHz
    static constexpr int REVERB_TAPS = 8;
    static constexpr int MAX_NOTCHES = 6;
    static constexpr double PI2 = 2.0 * 3.14159265358979323846;

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
        sweepLfoPhase = 0.0;
        shimmerAccum = 0.0f;
        
        // Clear notch filter states (2 states per biquad, Direct Form II Transposed)
        for (int i = 0; i < MAX_NOTCHES; ++i)
        {
            notchState[i][0] = notchState[i][1] = 0.0;
        }
        
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

    void setParameters(float shimmer, float space, float modulation,
                       float warp, float mix, float notchAmount, float sweepRange)
    {
        shimmerAmount = juce::jlimit(0.0f, 1.0f, shimmer);
        
        // Reverb decay
        reverbDecay = juce::jmap(space, 0.0f, 1.0f, 0.3f, 0.92f);
        
        // Modulation rate drives both chorus and notch sweep
        chorusRate = juce::jmap(modulation, 0.0f, 1.0f, 0.2f, 3.0f);
        chorusDepth = juce::jmap(modulation, 0.0f, 1.0f, 0.0f, 0.005f) * static_cast<float>(sr);
        // Notch sweep rate: slower than chorus for that slow Enigma feel
        sweepRate = juce::jmap(modulation, 0.0f, 1.0f, 0.05f, 1.5f);
        
        // Modulated delay
        delayTime = static_cast<int>(juce::jmap(warp, 0.0f, 1.0f, 0.05f, 0.4f) * sr);
        delayFeedback = juce::jmap(warp, 0.0f, 1.0f, 0.0f, 0.75f);
        delayModDepth = juce::jmap(warp, 0.0f, 1.0f, 0.0f, 0.002f) * static_cast<float>(sr);
        
        // Wet/dry
        wetDry = juce::jlimit(0.0f, 1.0f, mix);
        
        // Notch filter sweep (Enigma core)
        // notchAmount: 0 = off, maps to 1-6 active notch pairs
        activeNotches = static_cast<int>(juce::jmap(
            juce::jlimit(0.0f, 1.0f, notchAmount), 0.0f, 1.0f, 0.0f, 6.0f));
        
        // Sweep range: controls how wide the frequency sweep is
        // At 0: narrow sweep (200-800 Hz), At 1: full sweep (80-12000 Hz)
        float sweepClamped = juce::jlimit(0.0f, 1.0f, sweepRange);
        sweepMinFreq = juce::jmap(sweepClamped, 0.0f, 1.0f, 200.0f, 80.0f);
        sweepMaxFreq = juce::jmap(sweepClamped, 0.0f, 1.0f, 800.0f, 12000.0f);
    }

    float processSample(float input)
    {
        float dry = input;
        float processed = input;
        
        // === Stage 0: Notch Filter Sweep (Enigma core) ===
        if (activeNotches > 0)
        {
            // Advance sweep LFO (sine wave)
            sweepLfoPhase += sweepRate / sr;
            if (sweepLfoPhase > 1.0) sweepLfoPhase -= 1.0;
            
            // LFO value 0..1 maps to sweep position between min and max freq
            double lfoVal = 0.5 + 0.5 * std::sin(sweepLfoPhase * PI2);
            
            // Center frequency sweeps logarithmically
            double logMin = std::log(sweepMinFreq);
            double logMax = std::log(sweepMaxFreq);
            double centerLogFreq = logMin + lfoVal * (logMax - logMin);
            
            // Apply each notch filter in series
            for (int n = 0; n < activeNotches; ++n)
            {
                // Space notches logarithmically around center
                // Ratio between adjacent notches: ~1.5 octaves apart
                double offset = (n - (activeNotches - 1) * 0.5) * 0.585; // log(1.5)/log(e) ≈ 0.405, wider = 0.585
                double notchFreq = std::exp(centerLogFreq + offset);
                
                // Clamp to valid range
                notchFreq = std::max(20.0, std::min(notchFreq, sr * 0.45));
                
                // Calculate biquad notch filter coefficients
                double w0 = PI2 * notchFreq / sr;
                double Q = 2.5;  // Moderate notch width (Enigma-like)
                double alpha = std::sin(w0) / (2.0 * Q);
                
                double b0 = 1.0;
                double b1 = -2.0 * std::cos(w0);
                double b2 = 1.0;
                double a0 = 1.0 + alpha;
                double a1 = -2.0 * std::cos(w0);
                double a2 = 1.0 - alpha;
                
                // Normalize
                double nb0 = b0 / a0, nb1 = b1 / a0, nb2 = b2 / a0;
                double na1 = a1 / a0, na2 = a2 / a0;
                
                // Process through biquad (Transposed Direct Form II)
                double x = static_cast<double>(processed);
                double y = nb0 * x + notchState[n][0];
                notchState[n][0] = nb1 * x - na1 * y + notchState[n][1];
                notchState[n][1] = nb2 * x - na2 * y;
                
                processed = static_cast<float>(y);
            }
        }
        
        // === Stage 1: Chorus ===
        chorusLfoPhase += chorusRate / sr;
        if (chorusLfoPhase > 1.0) chorusLfoPhase -= 1.0;
        
        float chorusLfo = static_cast<float>(std::sin(chorusLfoPhase * PI2));
        float chorusDelaySamples = 15.0f + chorusLfo * chorusDepth;
        
        chorusBuffer[chorusWritePos] = processed;
        
        float chorusReadPos = static_cast<float>(chorusWritePos) - chorusDelaySamples;
        if (chorusReadPos < 0.0f) chorusReadPos += MAX_DELAY;
        int readIdx = static_cast<int>(chorusReadPos);
        float frac = chorusReadPos - readIdx;
        float chorusOut = chorusBuffer[readIdx % MAX_DELAY] * (1.0f - frac) 
                        + chorusBuffer[(readIdx + 1) % MAX_DELAY] * frac;
        
        chorusWritePos = (chorusWritePos + 1) % MAX_DELAY;
        float chorusMixed = processed * 0.7f + chorusOut * 0.3f;
        
        // === Stage 2: Modulated Delay ===
        delayLfoPhase += 0.13 / sr;
        if (delayLfoPhase > 1.0) delayLfoPhase -= 1.0;
        float delayMod = static_cast<float>(std::sin(delayLfoPhase * PI2)) * delayModDepth;
        
        int modDelayTime = juce::jlimit(1, MAX_DELAY - 1, delayTime + static_cast<int>(delayMod));
        
        int delayReadPos = (delayWritePos - modDelayTime + MAX_DELAY) % MAX_DELAY;
        float delayOut = delayLine[delayReadPos];
        
        delayLine[delayWritePos] = chorusMixed + delayOut * delayFeedback;
        delayWritePos = (delayWritePos + 1) % MAX_DELAY;
        
        float delayMixed = chorusMixed + delayOut * delayFeedback * 0.5f;
        
        // === Stage 3: Shimmer Reverb (FDN) ===
        float reverbIn = delayMixed;
        float reverbOut = 0.0f;
        
        for (int t = 0; t < REVERB_TAPS; ++t)
        {
            int tapDelay = reverbDelayTimes[t];
            int rp = (reverbWritePos[t] - tapDelay + MAX_DELAY) % MAX_DELAY;
            float tapOut = reverbBuffer[t][rp];
            reverbOut += tapOut;
            
            // Cross-mix between taps for density
            float crossMix = reverbBuffer[(t + 1) % REVERB_TAPS]
                            [(reverbWritePos[(t + 1) % REVERB_TAPS] - tapDelay / 2 + MAX_DELAY) % MAX_DELAY];
            
            float fbSignal = (tapOut * 0.7f + crossMix * 0.3f) * reverbDecay;
            
            // Shimmer: blend in octave-up signal from the buffer
            if (shimmerAmount > 0.0f)
            {
                int shimmerReadPos = (reverbWritePos[t] - tapDelay * 2 + MAX_DELAY * 2) % MAX_DELAY;
                float shimmerSample = reverbBuffer[t][shimmerReadPos];
                fbSignal += shimmerSample * shimmerAmount * 0.3f;
            }
            
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
    
    // Notch filter sweep (Enigma core)
    int activeNotches = 0;
    double sweepLfoPhase = 0.0;
    double sweepRate = 0.3;
    float sweepMinFreq = 200.0f;
    float sweepMaxFreq = 4000.0f;
    // Biquad states: [notch_index][state_index]
    // Transposed Direct Form II: 2 states per biquad
    double notchState[MAX_NOTCHES][2] = {};
    
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
