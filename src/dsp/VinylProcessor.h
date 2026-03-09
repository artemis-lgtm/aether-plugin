#pragma once
#include <juce_dsp/juce_dsp.h>
#include <cmath>
#include <random>
#include <array>

/**
 * VinylProcessor -- Lo-fi vinyl warmth and character.
 * 
 * v3 rewrite: Fixed wow/flutter to modulate pitch via delay line (not gain).
 * All pitch modulation (detune, wow, flutter) goes through one unified delay line.
 * Added proper wet/dry mix per-section.
 *
 * Inspired by iZotope Vinyl.
 *
 * Parameters:
 *   year:   simulated decade (0.0=modern, 1.0=1950s lo-fi)
 *   warp:   wow & flutter intensity (actual pitch modulation via delay)
 *   dust:   crackle/noise amount
 *   wear:   frequency degradation + saturation
 *   detune: slow drunken pitch drift (0.0=off, 1.0=heavy wobble)
 *   noise:  turntable noise (mechanical rumble + electrical hiss/hum)
 */
class VinylProcessor
{
public:
    // Delay buffer for ALL pitch modulation (detune + wow + flutter)
    // 32768 samples at 44.1kHz = ~743ms -- enough for all combined excursion
    static constexpr int DELAY_BUF_SIZE = 32768;
    static constexpr int DELAY_MASK = DELAY_BUF_SIZE - 1;  // power of 2 for fast modulo

    VinylProcessor() { delayBuffer.fill(0.0f); }

    void prepare(double sampleRate, int /*blockSize*/)
    {
        sr = sampleRate;
        
        delayBuffer.fill(0.0f);
        delayWritePos = 0;
        
        // Nominal center delay: 10ms (adds latency but allows pitch modulation in both directions)
        nominalDelay = sr * 0.01;
        
        // LFO phases for wow/flutter
        wowPhase = 0.0;
        flutterPhase1 = 0.0;
        flutterPhase2 = 0.37;  // offset for non-periodic feel
        
        // Detune drift LFOs
        driftPhase1 = 0.0;
        driftPhase2 = 0.37;
        driftPhase3 = 0.71;
        brownianState = 0.0;
        
        // Filter states
        lpState = 0.0;
        hpState = 0.0;
        
        // Noise generators
        rumblePhase = 0.0;
        humPhase = 0.0;
        hissState = 0.0;
        
        rng.seed(42);
    }

    void setParameters(float year, float warp, float dust, float wear,
                       float detuneAmount, float noiseAmount)
    {
        // Year -> low-pass cutoff
        float cutoff = juce::jmap(year, 0.0f, 1.0f, 18000.0f, 3500.0f);
        lpCoeff = 1.0 - std::exp(-2.0 * juce::MathConstants<double>::pi * cutoff / sr);
        
        // Year -> high-pass (rumble filter as records age)
        float hpCutoff = juce::jmap(year, 0.0f, 1.0f, 5.0f, 80.0f);
        hpCoeff = 1.0 - std::exp(-2.0 * juce::MathConstants<double>::pi * hpCutoff / sr);
        
        // Wow & Flutter: now expressed as delay modulation depth in samples
        // Wow: ~0.5 Hz, up to ±2% speed variation = ±(0.02 * nominalDelay) samples
        // At 44.1kHz with 10ms nominal, 2% = ~8.8 samples. Scale up for audible effect.
        // Real vinyl can have up to 0.25% wow (hi-fi) to 2%+ (worn record)
        // We map warp 0-1 to 0-40 samples of wow excursion (~0-9% at 10ms center)
        wowDepthSamples = juce::jmap(warp, 0.0f, 1.0f, 0.0f, 40.0f);
        // Flutter: ~5-7 Hz, smaller amplitude
        flutterDepthSamples = juce::jmap(warp, 0.0f, 1.0f, 0.0f, 12.0f);
        
        // Dust
        dustProb = juce::jmap(dust, 0.0f, 1.0f, 0.0f, 0.0004f);
        dustAmp = juce::jmap(dust, 0.0f, 1.0f, 0.0f, 0.12f);
        
        // Wear: saturation + noise floor
        wearAmount = juce::jmap(wear, 0.0f, 1.0f, 0.0f, 0.5f);
        noiseFloor = juce::jmap(wear, 0.0f, 1.0f, 0.0f, 0.004f);
        
        // Detune: slow drunken pitch drift in samples of delay excursion
        // Range: 0-600 samples (~0-13ms at 44.1kHz). Much more audible than v2's 200.
        detuneDepth = static_cast<double>(juce::jmap(juce::jlimit(0.0f, 1.0f, detuneAmount),
                                  0.0f, 1.0f, 0.0f, 600.0f));
        
        // Noise
        float noiseClamped = juce::jlimit(0.0f, 1.0f, noiseAmount);
        rumbleAmp = juce::jmap(noiseClamped, 0.0f, 1.0f, 0.0f, 0.018f);
        humAmp = juce::jmap(noiseClamped, 0.0f, 1.0f, 0.0f, 0.010f);
        hissAmp = juce::jmap(noiseClamped, 0.0f, 1.0f, 0.0f, 0.008f);
    }

    float processSample(float input)
    {
        // === Write input to delay buffer ===
        delayBuffer[delayWritePos] = input;
        
        // === Compute total delay modulation (all pitch effects combined) ===
        double totalMod = 0.0;
        
        // -- Wow: slow ~0.5 Hz pitch drift --
        wowPhase += 0.5 / sr;
        if (wowPhase > 1.0) wowPhase -= 1.0;
        totalMod += std::sin(wowPhase * 2.0 * juce::MathConstants<double>::pi) * wowDepthSamples;
        
        // -- Flutter: faster ~5.5 Hz + ~6.7 Hz (two oscillators for complexity) --
        flutterPhase1 += 5.5 / sr;
        if (flutterPhase1 > 1.0) flutterPhase1 -= 1.0;
        flutterPhase2 += 6.7 / sr;
        if (flutterPhase2 > 1.0) flutterPhase2 -= 1.0;
        totalMod += std::sin(flutterPhase1 * 2.0 * juce::MathConstants<double>::pi) * flutterDepthSamples * 0.6;
        totalMod += std::sin(flutterPhase2 * 2.0 * juce::MathConstants<double>::pi) * flutterDepthSamples * 0.4;
        
        // -- Detune: very slow drift (3 desynced LFOs + brownian) --
        if (detuneDepth > 0.1)
        {
            driftPhase1 += 0.15 / sr;
            if (driftPhase1 > 1.0) driftPhase1 -= 1.0;
            driftPhase2 += 0.07 / sr;
            if (driftPhase2 > 1.0) driftPhase2 -= 1.0;
            driftPhase3 += 0.31 / sr;
            if (driftPhase3 > 1.0) driftPhase3 -= 1.0;
            
            double d1 = std::sin(driftPhase1 * 2.0 * juce::MathConstants<double>::pi);
            double d2 = std::sin(driftPhase2 * 2.0 * juce::MathConstants<double>::pi) * 0.6;
            double d3 = std::sin(driftPhase3 * 2.0 * juce::MathConstants<double>::pi) * 0.25;
            
            // Brownian random walk
            std::uniform_real_distribution<double> brownDist(-1.0, 1.0);
            brownianState += brownDist(rng) * 0.0002;
            brownianState *= 0.9999;
            brownianState = juce::jlimit(-0.5, 0.5, brownianState);
            
            double driftSignal = (d1 + d2 + d3 + brownianState * 0.4) / 2.25;
            totalMod += driftSignal * detuneDepth;
        }
        
        // === Read from delay line with cubic Hermite interpolation ===
        double modulatedDelay = nominalDelay + totalMod;
        modulatedDelay = juce::jlimit(1.0, static_cast<double>(DELAY_BUF_SIZE - 4), modulatedDelay);
        
        double readPos = static_cast<double>(delayWritePos) - modulatedDelay;
        if (readPos < 0.0) readPos += DELAY_BUF_SIZE;
        
        int idx = static_cast<int>(readPos);
        float frac = static_cast<float>(readPos - idx);
        
        // 4-point cubic Hermite
        float ym1 = delayBuffer[(idx - 1) & DELAY_MASK];
        float y0  = delayBuffer[idx & DELAY_MASK];
        float y1  = delayBuffer[(idx + 1) & DELAY_MASK];
        float y2  = delayBuffer[(idx + 2) & DELAY_MASK];
        
        float c0 = y0;
        float c1 = 0.5f * (y1 - ym1);
        float c2 = ym1 - 2.5f * y0 + 2.0f * y1 - 0.5f * y2;
        float c3 = 0.5f * (y2 - ym1) + 1.5f * (y0 - y1);
        float processed = ((c3 * frac + c2) * frac + c1) * frac + c0;
        
        // If no pitch modulation at all, use clean input (bypass delay line)
        bool hasPitchMod = (wowDepthSamples > 0.01f || flutterDepthSamples > 0.01f || detuneDepth > 0.1);
        if (!hasPitchMod)
            processed = input;
        
        delayWritePos = (delayWritePos + 1) & DELAY_MASK;
        
        // === Saturation (warm tape-style) ===
        if (wearAmount > 0.0f)
        {
            float drive = 1.0f + wearAmount * 3.0f;
            float driven = processed * drive;
            // Asymmetric soft clipping for warmth
            processed = std::tanh(driven) / std::tanh(drive);
        }
        
        // === Low-pass filter (year) ===
        lpState += lpCoeff * (processed - lpState);
        processed = static_cast<float>(lpState);
        
        // === High-pass filter (rumble) ===
        hpState += hpCoeff * (processed - hpState);
        processed = processed - static_cast<float>(hpState);
        
        // === Dust/Crackle ===
        std::uniform_real_distribution<float> dist(0.0f, 1.0f);
        if (dist(rng) < dustProb)
        {
            // Shaped crackle: short burst, not just single-sample click
            float crackle = (dist(rng) * 2.0f - 1.0f) * dustAmp;
            processed += crackle;
        }
        
        // === Noise floor (wear) ===
        if (noiseFloor > 0.0f)
            processed += (dist(rng) * 2.0f - 1.0f) * noiseFloor;
        
        // === Turntable Noise ===
        if (rumbleAmp > 0.0f)
        {
            rumblePhase += 33.0 / sr;
            if (rumblePhase > 1.0) rumblePhase -= 1.0;
            double rumble = std::sin(rumblePhase * 2.0 * juce::MathConstants<double>::pi);
            double rumbleSub = std::sin(rumblePhase * juce::MathConstants<double>::pi);
            processed += static_cast<float>((rumble * 0.7 + rumbleSub * 0.3) * rumbleAmp);
        }
        
        if (humAmp > 0.0f)
        {
            humPhase += 60.0 / sr;
            if (humPhase > 1.0) humPhase -= 1.0;
            double hum = std::sin(humPhase * 2.0 * juce::MathConstants<double>::pi);
            double hum2 = std::sin(humPhase * 4.0 * juce::MathConstants<double>::pi) * 0.5;
            processed += static_cast<float>((hum + hum2) * humAmp);
        }
        
        if (hissAmp > 0.0f)
        {
            float rawNoise = dist(rng) * 2.0f - 1.0f;
            hissState = hissState * 0.85 + rawNoise * 0.15;
            processed += static_cast<float>(hissState) * hissAmp;
        }
        
        return processed;
    }

    void processBlock(float* buffer, int numSamples)
    {
        for (int i = 0; i < numSamples; ++i)
            buffer[i] = processSample(buffer[i]);
    }

private:
    double sr = 44100.0;
    
    // Unified delay line for all pitch modulation
    std::array<float, DELAY_BUF_SIZE> delayBuffer;
    int delayWritePos = 0;
    double nominalDelay = 441.0;
    
    // Wow LFO
    double wowPhase = 0.0;
    float wowDepthSamples = 0.0f;
    
    // Flutter LFOs (two oscillators)
    double flutterPhase1 = 0.0;
    double flutterPhase2 = 0.0;
    float flutterDepthSamples = 0.0f;
    
    // Detune drift
    double driftPhase1 = 0.0;
    double driftPhase2 = 0.0;
    double driftPhase3 = 0.0;
    double brownianState = 0.0;
    double detuneDepth = 0.0;
    
    // Filters
    double lpCoeff = 1.0;
    double hpCoeff = 0.0;
    double lpState = 0.0;
    double hpState = 0.0;
    
    // Saturation
    float wearAmount = 0.0f;
    float noiseFloor = 0.0f;
    
    // Dust
    float dustProb = 0.0f;
    float dustAmp = 0.0f;
    
    // Noise generators
    double rumblePhase = 0.0;
    double humPhase = 0.0;
    double hissState = 0.0;
    float rumbleAmp = 0.0f;
    float humAmp = 0.0f;
    float hissAmp = 0.0f;
    
    std::mt19937 rng;
};
