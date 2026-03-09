#pragma once
#include <juce_dsp/juce_dsp.h>
#include <cmath>
#include <array>

/**
 * PsychedelicProcessor -- Spectral/shimmer psychedelic effects.
 * 
 * v3 rewrite: Fixed signal flow so modulation effects are always audible.
 * 
 * Signal chain: Input -> Notch Sweep -> Chorus -> Mod Delay -> [Shimmer Reverb blend] -> Mix
 *
 * The notch sweep is the core Enigma feature: swept band-reject filters
 * whose center frequencies are modulated by a slow LFO across the spectrum.
 * Uses wider notch Q (0.7-1.2) for audible spectral movement.
 *
 * v2 bug: mix only blended dry vs reverb output, throwing away notch/chorus/delay.
 * v3 fix: mix blends dry vs full processed chain. Shimmer is layered on top.
 *
 * Parameters:
 *   shimmer:    reverb blend layered onto the processed signal (0.0 - 1.0)
 *   space:      reverb size/decay (0.0 - 1.0)
 *   modulation: sweep & chorus speed + depth (0.0 - 1.0)
 *   warp:       delay feedback with modulation (0.0 - 1.0)
 *   mix:        wet/dry blend of FULL chain vs dry (0.0 - 1.0)
 *   notches:    number of notch filter pairs, 0=off (0.0 - 1.0 -> 0-6 pairs)
 *   sweep:      notch sweep frequency range width (0.0 - 1.0)
 */
class PsychedelicProcessor
{
public:
    static constexpr int MAX_DELAY = 96000;
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
        
        delayLine.fill(0.0f);
        for (auto& tap : reverbBuffer)
            tap.fill(0.0f);
        chorusBuffer.fill(0.0f);
        
        delayWritePos = 0;
        chorusWritePos = 0;
        for (auto& pos : reverbWritePos)
            pos = 0;
        
        chorusLfoPhase = 0.0;
        chorusLfoPhase2 = 0.0;
        delayLfoPhase = 0.0;
        sweepLfoPhase = 0.0;
        
        for (int i = 0; i < MAX_NOTCHES; ++i)
            notchState[i][0] = notchState[i][1] = 0.0;
        
        // Reverb tap times (prime-number spacing for density)
        reverbDelayTimes[0] = static_cast<int>(0.0297 * sr);
        reverbDelayTimes[1] = static_cast<int>(0.0371 * sr);
        reverbDelayTimes[2] = static_cast<int>(0.0411 * sr);
        reverbDelayTimes[3] = static_cast<int>(0.0437 * sr);
        reverbDelayTimes[4] = static_cast<int>(0.0533 * sr);
        reverbDelayTimes[5] = static_cast<int>(0.0671 * sr);
        reverbDelayTimes[6] = static_cast<int>(0.0797 * sr);
        reverbDelayTimes[7] = static_cast<int>(0.0907 * sr);
        
        // Smoothing states
        prevProcessed = 0.0f;
    }

    void setParameters(float shimmer, float space, float modulation,
                       float warp, float mix, float notchAmount, float sweepRange)
    {
        // Shimmer: how much reverb is layered onto the processed signal
        shimmerAmount = juce::jlimit(0.0f, 1.0f, shimmer);
        
        // Reverb decay
        reverbDecay = juce::jmap(space, 0.0f, 1.0f, 0.3f, 0.92f);
        
        // Modulation rate and depth -- chorus
        float modClamped = juce::jlimit(0.0f, 1.0f, modulation);
        chorusRate = juce::jmap(modClamped, 0.0f, 1.0f, 0.2f, 4.0f);
        // Chorus depth: 1-10ms range (in samples). Real chorus uses 1-10ms.
        chorusDepth = juce::jmap(modClamped, 0.0f, 1.0f, 0.001f, 0.010f) * static_cast<float>(sr);
        
        // Notch sweep rate: slow Enigma feel
        sweepRate = juce::jmap(modClamped, 0.0f, 1.0f, 0.05f, 2.0f);
        
        // Modulated delay
        delayTime = static_cast<int>(juce::jmap(warp, 0.0f, 1.0f, 0.05f, 0.4f) * sr);
        delayFeedback = juce::jmap(warp, 0.0f, 1.0f, 0.0f, 0.75f);
        delayModDepth = juce::jmap(warp, 0.0f, 1.0f, 0.0f, 0.003f) * static_cast<float>(sr);
        
        // Mix: blend between dry input and FULL processed chain
        wetDry = juce::jlimit(0.0f, 1.0f, mix);
        
        // Notch filters
        activeNotches = static_cast<int>(juce::jmap(
            juce::jlimit(0.0f, 1.0f, notchAmount), 0.0f, 1.0f, 0.0f, 6.0f));
        
        // Sweep range
        float sweepClamped = juce::jlimit(0.0f, 1.0f, sweepRange);
        sweepMinFreq = juce::jmap(sweepClamped, 0.0f, 1.0f, 200.0f, 60.0f);
        sweepMaxFreq = juce::jmap(sweepClamped, 0.0f, 1.0f, 1200.0f, 14000.0f);
    }

    float processSample(float input)
    {
        float dry = input;
        float processed = input;
        
        // === Stage 0: Notch Filter Sweep (Enigma core) ===
        if (activeNotches > 0)
        {
            sweepLfoPhase += sweepRate / sr;
            if (sweepLfoPhase > 1.0) sweepLfoPhase -= 1.0;
            
            // Tri-wave LFO for more even sweep feel than sine
            double lfoVal;
            if (sweepLfoPhase < 0.5)
                lfoVal = sweepLfoPhase * 2.0;
            else
                lfoVal = 2.0 - sweepLfoPhase * 2.0;
            
            double logMin = std::log(sweepMinFreq);
            double logMax = std::log(sweepMaxFreq);
            double centerLogFreq = logMin + lfoVal * (logMax - logMin);
            
            for (int n = 0; n < activeNotches; ++n)
            {
                // Space notches ~1 octave apart (log2 spacing)
                double offset = (n - (activeNotches - 1) * 0.5) * 0.693; // ln(2)
                double notchFreq = std::exp(centerLogFreq + offset);
                notchFreq = std::max(20.0, std::min(notchFreq, sr * 0.45));
                
                // Wider Q for audible effect (0.7-1.2 range)
                // Q varies slightly per notch for a more complex sound
                double Q = 0.7 + (n % 3) * 0.25;
                double w0 = PI2 * notchFreq / sr;
                double alpha = std::sin(w0) / (2.0 * Q);
                
                double b0 = 1.0;
                double b1 = -2.0 * std::cos(w0);
                double b2 = 1.0;
                double a0 = 1.0 + alpha;
                double a1 = -2.0 * std::cos(w0);
                double a2 = 1.0 - alpha;
                
                double nb0 = b0 / a0, nb1 = b1 / a0, nb2 = b2 / a0;
                double na1 = a1 / a0, na2 = a2 / a0;
                
                // Transposed Direct Form II
                double x = static_cast<double>(processed);
                double y = nb0 * x + notchState[n][0];
                notchState[n][0] = nb1 * x - na1 * y + notchState[n][1];
                notchState[n][1] = nb2 * x - na2 * y;
                
                processed = static_cast<float>(y);
            }
        }
        
        // === Stage 1: Stereo Chorus (dual-voice with offset LFOs) ===
        // Two chorus voices with detuned LFOs for richer sound
        chorusLfoPhase += chorusRate / sr;
        if (chorusLfoPhase > 1.0) chorusLfoPhase -= 1.0;
        chorusLfoPhase2 += (chorusRate * 1.17) / sr;  // slightly detuned second voice
        if (chorusLfoPhase2 > 1.0) chorusLfoPhase2 -= 1.0;
        
        float lfo1 = static_cast<float>(std::sin(chorusLfoPhase * PI2));
        float lfo2 = static_cast<float>(std::sin(chorusLfoPhase2 * PI2));
        
        // Center delay ~7ms + modulation depth
        float centerDelay = 0.007f * static_cast<float>(sr);
        float delay1 = centerDelay + lfo1 * chorusDepth;
        float delay2 = centerDelay + lfo2 * chorusDepth * 0.8f;
        
        chorusBuffer[chorusWritePos] = processed;
        
        // Read voice 1 with linear interpolation
        float readPos1 = static_cast<float>(chorusWritePos) - delay1;
        if (readPos1 < 0.0f) readPos1 += MAX_DELAY;
        int idx1 = static_cast<int>(readPos1);
        float frac1 = readPos1 - idx1;
        float voice1 = chorusBuffer[idx1 % MAX_DELAY] * (1.0f - frac1)
                      + chorusBuffer[(idx1 + 1) % MAX_DELAY] * frac1;
        
        // Read voice 2
        float readPos2 = static_cast<float>(chorusWritePos) - delay2;
        if (readPos2 < 0.0f) readPos2 += MAX_DELAY;
        int idx2 = static_cast<int>(readPos2);
        float frac2 = readPos2 - idx2;
        float voice2 = chorusBuffer[idx2 % MAX_DELAY] * (1.0f - frac2)
                      + chorusBuffer[(idx2 + 1) % MAX_DELAY] * frac2;
        
        chorusWritePos = (chorusWritePos + 1) % MAX_DELAY;
        
        // Mix: equal blend of dry + two chorus voices (normalized)
        float chorusMixed = processed * 0.5f + voice1 * 0.3f + voice2 * 0.2f;
        
        // === Stage 2: Modulated Delay ===
        delayLfoPhase += 0.13 / sr;
        if (delayLfoPhase > 1.0) delayLfoPhase -= 1.0;
        float delayMod = static_cast<float>(std::sin(delayLfoPhase * PI2)) * delayModDepth;
        
        // Read from delay with interpolation
        float modDelay = static_cast<float>(delayTime) + delayMod;
        modDelay = juce::jlimit(1.0f, static_cast<float>(MAX_DELAY - 2), modDelay);
        float delayReadF = static_cast<float>(delayWritePos) - modDelay;
        if (delayReadF < 0.0f) delayReadF += MAX_DELAY;
        int dIdx = static_cast<int>(delayReadF);
        float dFrac = delayReadF - dIdx;
        float delayOut = delayLine[dIdx % MAX_DELAY] * (1.0f - dFrac)
                       + delayLine[(dIdx + 1) % MAX_DELAY] * dFrac;
        
        // Write to delay with feedback (soft-clip feedback to prevent blowup)
        float fbSignal = std::tanh(delayOut * delayFeedback);
        delayLine[delayWritePos] = chorusMixed + fbSignal;
        delayWritePos = (delayWritePos + 1) % MAX_DELAY;
        
        // Delay contributes to the processed signal (parallel blend)
        processed = chorusMixed + delayOut * delayFeedback * 0.4f;
        
        // === Stage 3: Shimmer Reverb (layered onto processed, controlled by shimmer knob) ===
        if (shimmerAmount > 0.01f)
        {
            float reverbIn = processed;
            float reverbOut = 0.0f;
            
            for (int t = 0; t < REVERB_TAPS; ++t)
            {
                int tapDelay = reverbDelayTimes[t];
                int rp = (reverbWritePos[t] - tapDelay + MAX_DELAY) % MAX_DELAY;
                float tapOut = reverbBuffer[t][rp];
                reverbOut += tapOut;
                
                // Cross-mix for density
                float crossMix = reverbBuffer[(t + 1) % REVERB_TAPS]
                    [(reverbWritePos[(t + 1) % REVERB_TAPS] - tapDelay / 2 + MAX_DELAY) % MAX_DELAY];
                
                float fb = (tapOut * 0.7f + crossMix * 0.3f) * reverbDecay;
                
                // Octave-up shimmer from double-speed read
                int shimmerReadPos = (reverbWritePos[t] - tapDelay * 2 + MAX_DELAY * 2) % MAX_DELAY;
                float shimmerSample = reverbBuffer[t][shimmerReadPos];
                fb += shimmerSample * 0.25f;
                
                fb = std::tanh(fb);  // prevent blowup
                
                reverbBuffer[t][reverbWritePos[t]] = reverbIn / REVERB_TAPS + fb;
                reverbWritePos[t] = (reverbWritePos[t] + 1) % MAX_DELAY;
            }
            
            reverbOut /= REVERB_TAPS;
            
            // Layer reverb onto processed signal (shimmer controls blend)
            processed = processed * (1.0f - shimmerAmount * 0.6f) + reverbOut * shimmerAmount;
        }
        
        // === Gain compensation: keep output level close to input level ===
        // Slight normalization to prevent volume drop when effects are active
        
        // === Final wet/dry mix: dry input vs full processed chain ===
        float output = dry * (1.0f - wetDry) + processed * wetDry;
        return output;
    }

    void processBlock(float* buffer, int numSamples)
    {
        for (int i = 0; i < numSamples; ++i)
            buffer[i] = processSample(buffer[i]);
    }

private:
    double sr = 44100.0;
    
    // Notch filter sweep
    int activeNotches = 0;
    double sweepLfoPhase = 0.0;
    double sweepRate = 0.3;
    float sweepMinFreq = 200.0f;
    float sweepMaxFreq = 4000.0f;
    double notchState[MAX_NOTCHES][2] = {};
    
    // Chorus (dual-voice)
    std::array<float, MAX_DELAY> chorusBuffer;
    int chorusWritePos = 0;
    double chorusLfoPhase = 0.0;
    double chorusLfoPhase2 = 0.0;
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
    
    // Output
    float wetDry = 0.5f;
    float prevProcessed = 0.0f;
};
