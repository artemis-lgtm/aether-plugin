#pragma once
#include <juce_dsp/juce_dsp.h>
#include <cmath>
#include <random>
#include <array>

/**
 * VinylProcessor -- Lo-fi vinyl warmth and character.
 * 
 * Inspired by iZotope Vinyl: adds the character of vinyl playback
 * to any signal. Warmth, wobble, dust, age, and detune.
 *
 * Parameters:
 *   year: simulated decade (0.0=modern crisp, 1.0=1950s lo-fi)
 *   warp: wow & flutter intensity (pitch wobble)
 *   dust: crackle/noise amount
 *   wear: frequency degradation
 *   detune: slow drunken pitch drift amount (0.0=off, 1.0=heavy wobble)
 *           Simulates turntable motor speed instability -- pitch wanders
 *           slowly and organically, like iZotope Vinyl's detune.
 */
class VinylProcessor
{
public:
    // Modulated delay buffer: needs to be large enough for max detune excursion
    // At 44.1kHz, 16384 samples = ~370ms of delay range
    static constexpr int DELAY_BUF_SIZE = 16384;
    // Nominal center delay in samples (~10ms at 44.1kHz)
    static constexpr double NOMINAL_DELAY = 441.0;

    VinylProcessor() { delayBuffer.fill(0.0f); }

    void prepare(double sampleRate, int /*blockSize*/)
    {
        sr = sampleRate;
        lfoPhase = 0.0;
        lfoPhase2 = 0.0;
        dustCounter = 0;
        lastSample = 0.0f;
        
        // Initialize filter states
        lpState = 0.0;
        hpState = 0.0;
        
        // Modulated delay line for detune
        delayBuffer.fill(0.0f);
        delayWritePos = 0;
        nominalDelay = sr * 0.01;  // 10ms center delay
        
        // Detune drift LFOs -- multiple slow, desynced oscillators
        // for organic, non-periodic wandering
        driftPhase1 = 0.0;
        driftPhase2 = 0.37;   // offset so they don't sync
        driftPhase3 = 0.71;
        brownianState = 0.0;
        
        rng.seed(42);
    }

    void setParameters(float year, float warp, float dust, float wear, float detuneAmount)
    {
        // Year maps to low-pass cutoff: modern = 18kHz, 1950s = 4kHz
        float cutoff = juce::jmap(year, 0.0f, 1.0f, 18000.0f, 3500.0f);
        lpCoeff = 1.0 - std::exp(-2.0 * juce::MathConstants<double>::pi * cutoff / sr);
        
        // Subtle high-pass as records age (rumble filter)
        float hpCutoff = juce::jmap(year, 0.0f, 1.0f, 5.0f, 80.0f);
        hpCoeff = 1.0 - std::exp(-2.0 * juce::MathConstants<double>::pi * hpCutoff / sr);
        
        // Warp: wow (slow ~0.5Hz) and flutter (faster ~6Hz)
        wowDepth = juce::jmap(warp, 0.0f, 1.0f, 0.0f, 0.003f);
        flutterDepth = juce::jmap(warp, 0.0f, 1.0f, 0.0f, 0.0008f);
        
        // Dust: probability of crackle per sample
        dustProb = juce::jmap(dust, 0.0f, 1.0f, 0.0f, 0.0003f);
        dustAmp = juce::jmap(dust, 0.0f, 1.0f, 0.0f, 0.08f);
        
        // Wear: subtle saturation + noise floor
        wearAmount = juce::jmap(wear, 0.0f, 1.0f, 0.0f, 0.4f);
        noiseFloor = juce::jmap(wear, 0.0f, 1.0f, 0.0f, 0.003f);
        
        // Detune: depth of slow pitch drift in samples
        // At full (1.0), the delay modulation swings +/- ~200 samples at 44.1kHz
        // which is roughly +/- 30 cents of pitch wobble -- slow and organic
        detuneDepth = juce::jmap(juce::jlimit(0.0f, 1.0f, detuneAmount),
                                  0.0f, 1.0f, 0.0f, 200.0f);
    }

    float processSample(float input)
    {
        // === Write to delay buffer ===
        delayBuffer[delayWritePos] = input;
        
        // === Detune: slow drunken pitch drift via modulated delay ===
        // Three desynced slow LFOs + brownian noise for organic drift
        //
        // LFO1: ~0.15 Hz (very slow primary drift, ~6.7 second cycle)
        // LFO2: ~0.07 Hz (ultra-slow secondary, ~14 second cycle)
        // LFO3: ~0.31 Hz (slightly faster color, ~3.2 second cycle)
        // Brownian: random walk, low-pass filtered for smooth wandering
        
        driftPhase1 += 0.15 / sr;
        if (driftPhase1 > 1.0) driftPhase1 -= 1.0;
        
        driftPhase2 += 0.07 / sr;
        if (driftPhase2 > 1.0) driftPhase2 -= 1.0;
        
        driftPhase3 += 0.31 / sr;
        if (driftPhase3 > 1.0) driftPhase3 -= 1.0;
        
        double drift1 = std::sin(driftPhase1 * 2.0 * juce::MathConstants<double>::pi);
        double drift2 = std::sin(driftPhase2 * 2.0 * juce::MathConstants<double>::pi) * 0.6;
        double drift3 = std::sin(driftPhase3 * 2.0 * juce::MathConstants<double>::pi) * 0.25;
        
        // Brownian random walk (very gentle, low-pass filtered)
        std::uniform_real_distribution<double> brownDist(-1.0, 1.0);
        brownianState += brownDist(rng) * 0.0001;
        brownianState *= 0.9999;  // decay toward zero to prevent runaway
        brownianState = juce::jlimit(-0.5, 0.5, brownianState);
        
        // Combined drift signal, weighted
        double driftSignal = (drift1 + drift2 + drift3 + brownianState * 0.4);
        // Normalize roughly to -1..+1 range
        driftSignal /= 2.25;
        
        // Modulate delay time around the nominal center
        double modulatedDelay = nominalDelay + driftSignal * detuneDepth;
        modulatedDelay = juce::jlimit(1.0, static_cast<double>(DELAY_BUF_SIZE - 2), modulatedDelay);
        
        // Read from delay line with cubic interpolation for smooth pitch
        double readPos = static_cast<double>(delayWritePos) - modulatedDelay;
        if (readPos < 0.0) readPos += DELAY_BUF_SIZE;
        
        int idx = static_cast<int>(readPos);
        float frac = static_cast<float>(readPos - idx);
        
        // Cubic Hermite interpolation (4-point)
        float ym1 = delayBuffer[(idx - 1 + DELAY_BUF_SIZE) % DELAY_BUF_SIZE];
        float y0  = delayBuffer[idx % DELAY_BUF_SIZE];
        float y1  = delayBuffer[(idx + 1) % DELAY_BUF_SIZE];
        float y2  = delayBuffer[(idx + 2) % DELAY_BUF_SIZE];
        
        float c0 = y0;
        float c1 = 0.5f * (y1 - ym1);
        float c2 = ym1 - 2.5f * y0 + 2.0f * y1 - 0.5f * y2;
        float c3 = 0.5f * (y2 - ym1) + 1.5f * (y0 - y1);
        float detuned = ((c3 * frac + c2) * frac + c1) * frac + c0;
        
        // If detune is off (depth ~0), pass through clean
        float processed = (detuneDepth > 0.01f) ? detuned : input;
        
        // Advance write position
        delayWritePos = (delayWritePos + 1) % DELAY_BUF_SIZE;
        
        // === Wow & Flutter (gain-modulated pitch feel) ===
        lfoPhase += 0.5 / sr;  // 0.5 Hz wow
        if (lfoPhase > 1.0) lfoPhase -= 1.0;
        double wow = std::sin(lfoPhase * 2.0 * juce::MathConstants<double>::pi) * wowDepth;
        
        lfoPhase2 += 6.3 / sr;  // ~6.3 Hz flutter
        if (lfoPhase2 > 1.0) lfoPhase2 -= 1.0;
        double flutter = std::sin(lfoPhase2 * 2.0 * juce::MathConstants<double>::pi) * flutterDepth;
        
        float pitchMod = 1.0f + static_cast<float>(wow + flutter);
        processed *= pitchMod;
        
        // === Saturation (warm tape-style) ===
        if (wearAmount > 0.0f)
        {
            float driven = processed * (1.0f + wearAmount * 2.0f);
            processed = std::tanh(driven) / std::tanh(1.0f + wearAmount * 2.0f);
        }
        
        // === Low-pass filter (year-dependent) ===
        lpState += lpCoeff * (processed - lpState);
        processed = static_cast<float>(lpState);
        
        // === High-pass filter (rumble) ===
        hpState += hpCoeff * (processed - hpState);
        processed = processed - static_cast<float>(hpState);
        
        // === Dust/Crackle ===
        std::uniform_real_distribution<float> dist(0.0f, 1.0f);
        if (dist(rng) < dustProb)
        {
            float crackle = (dist(rng) * 2.0f - 1.0f) * dustAmp;
            processed += crackle;
        }
        
        // === Noise floor (wear) ===
        if (noiseFloor > 0.0f)
        {
            float noise = (dist(rng) * 2.0f - 1.0f) * noiseFloor;
            processed += noise;
        }
        
        lastSample = processed;
        return processed;
    }

    void processBlock(float* buffer, int numSamples)
    {
        for (int i = 0; i < numSamples; ++i)
            buffer[i] = processSample(buffer[i]);
    }

private:
    double sr = 44100.0;
    double lfoPhase = 0.0;
    double lfoPhase2 = 0.0;
    double lpCoeff = 1.0;
    double hpCoeff = 0.0;
    double lpState = 0.0;
    double hpState = 0.0;
    double wowDepth = 0.0;
    double flutterDepth = 0.0;
    float dustProb = 0.0f;
    float dustAmp = 0.0f;
    float wearAmount = 0.0f;
    float noiseFloor = 0.0f;
    float lastSample = 0.0f;
    int dustCounter = 0;
    std::mt19937 rng;
    
    // Modulated delay line for detune
    std::array<float, DELAY_BUF_SIZE> delayBuffer;
    int delayWritePos = 0;
    double nominalDelay = 441.0;
    
    // Detune drift oscillators
    double driftPhase1 = 0.0;
    double driftPhase2 = 0.0;
    double driftPhase3 = 0.0;
    double brownianState = 0.0;
    double detuneDepth = 0.0;
};
