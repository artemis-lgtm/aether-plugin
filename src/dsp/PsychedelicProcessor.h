#pragma once
#include <juce_dsp/juce_dsp.h>
#include <cmath>
#include <array>

/**
 * PsychedelicProcessor -- Waves Enigma-style architecture.
 *
 * v4 rewrite based on Waves Enigma user guide signal flow:
 *
 *   Input → [Sum] → [Notch Filter Network (LFO swept)] → Output → Mix(dry/wet)
 *              ↑                                             |
 *              |___ [Feedback Filter] ← [Delay] ← [Decay] ←_|
 *
 * The notch filter network (2-12 notches in pairs) sweeps across the spectrum,
 * creating the signature evolving spectral animation.
 *
 * The feedback loop sends the output back through a filter and delay, creating
 * resonant, reverb-like sustain. The feedback filter shapes what frequencies
 * build up over successive iterations.
 *
 * This is fundamentally different from v1-v3 which had separate chorus/delay/reverb
 * stages. Enigma's character comes from the INTERACTION between the notch sweep
 * and the filtered feedback — each pass through the loop further sculpts the spectrum.
 *
 * Parameters:
 *   shimmer  → feedback filter brightness (LP cutoff in feedback path)
 *   space    → feedback delay time (short=metallic/spring, long=echo)
 *   mod      → LFO rate for notch sweep
 *   warp     → feedback decay/amount (how much signal recirculates)
 *   mix      → wet/dry balance
 *   notches  → number of notch pairs (1-6, i.e. 2-12 individual notches)
 *   sweep    → frequency range of the notch sweep
 */
class PsychedelicProcessor
{
public:
    static constexpr int MAX_DELAY = 96000;
    static constexpr int MAX_NOTCHES = 6;
    static constexpr double PI2 = 2.0 * 3.14159265358979323846;

    PsychedelicProcessor()
    {
        delayLine.fill(0.0f);
    }

    void prepare(double sampleRate, int /*blockSize*/)
    {
        sr = sampleRate;
        delayLine.fill(0.0f);
        delayWritePos = 0;
        sweepLfoPhase = 0.0;

        for (int i = 0; i < MAX_NOTCHES; ++i)
            notchState[i][0] = notchState[i][1] = 0.0;

        // Feedback filter state
        fbFilterState = 0.0;

        // Feedback accumulator
        feedbackSample = 0.0f;
    }

    void setParameters(float shimmer, float space, float modulation,
                       float warp, float mix, float notchAmount, float sweepRange)
    {
        // === Notch network ===
        activeNotches = static_cast<int>(juce::jmap(
            juce::jlimit(0.0f, 1.0f, notchAmount), 0.0f, 1.0f, 0.0f, 6.0f));

        // Notch depth: how deep the notches cut (in gain terms)
        // Full depth = deep spectral carving
        notchDepth = 1.0f; // fixed deep for now, Enigma uses Depth 0-200

        // === Sweep LFO rate ===
        float modClamped = juce::jlimit(0.0f, 1.0f, modulation);
        sweepRate = juce::jmap(modClamped, 0.0f, 1.0f, 0.03f, 8.0f);

        // === Sweep frequency range ===
        float sweepClamped = juce::jlimit(0.0f, 1.0f, sweepRange);
        // Log-spaced sweep range
        sweepMinFreq = juce::jmap(sweepClamped, 0.0f, 1.0f, 200.0f, 40.0f);
        sweepMaxFreq = juce::jmap(sweepClamped, 0.0f, 1.0f, 3000.0f, 18000.0f);

        // === Feedback loop ===
        // Space -> delay time (5ms to 300ms)
        float spaceClamped = juce::jlimit(0.0f, 1.0f, space);
        feedbackDelay = static_cast<int>(juce::jmap(spaceClamped, 0.0f, 1.0f, 0.005f, 0.300f) * static_cast<float>(sr));
        feedbackDelay = juce::jlimit(1, MAX_DELAY - 1, feedbackDelay);

        // Warp -> feedback decay/gain (how much recirculates)
        // Pushed to 0.93 for more aggressive resonant buildup
        float warpClamped = juce::jlimit(0.0f, 1.0f, warp);
        feedbackGain = juce::jmap(warpClamped, 0.0f, 1.0f, 0.0f, 0.93f);

        // Shimmer -> feedback filter brightness (LP cutoff in feedback path)
        float shimmerClamped = juce::jlimit(0.0f, 1.0f, shimmer);
        // 0 = dark feedback (800Hz LP), 1 = bright feedback (12kHz LP)
        float fbFilterFreq = juce::jmap(shimmerClamped, 0.0f, 1.0f, 800.0f, 12000.0f);
        fbFilterCoeff = 1.0 - std::exp(-PI2 * fbFilterFreq / sr);

        // === Output mix ===
        wetDry = juce::jlimit(0.0f, 1.0f, mix);
    }

    float processSample(float input)
    {
        float dry = input;

        // === Sum input with feedback return ===
        float summed = input + feedbackSample;

        // Warm tanh saturation -- lets the signal get hotter before taming it
        summed = std::tanh(summed * 0.7f) * (1.0f / 0.7f);

        float processed = summed;

        // === Notch Filter Network (the core Enigma processor) ===
        if (activeNotches > 0)
        {
            // Advance sweep LFO
            sweepLfoPhase += sweepRate / sr;
            if (sweepLfoPhase > 1.0) sweepLfoPhase -= 1.0;

            // Triangle LFO for even sweep (Enigma uses configurable waveforms)
            double lfoVal;
            if (sweepLfoPhase < 0.5)
                lfoVal = sweepLfoPhase * 2.0;
            else
                lfoVal = 2.0 - sweepLfoPhase * 2.0;

            // Log-spaced center frequency
            double logMin = std::log(static_cast<double>(sweepMinFreq));
            double logMax = std::log(static_cast<double>(sweepMaxFreq));
            double centerLogFreq = logMin + lfoVal * (logMax - logMin);

            for (int n = 0; n < activeNotches; ++n)
            {
                // Space notches ~1 octave apart (log2 spacing)
                double offset = (n - (activeNotches - 1) * 0.5) * 0.693; // ln(2)
                double notchFreq = std::exp(centerLogFreq + offset);
                notchFreq = juce::jlimit(20.0, sr * 0.45, notchFreq);

                // Sharper Q for more dramatic spectral carving
                // Higher Q = narrower notch = more pronounced sweep effect
                double Q = 1.5 + (n % 3) * 0.8; // 1.5, 2.3, 3.1, 1.5, 2.3, 3.1

                double w0 = PI2 * notchFreq / sr;
                double sinW0 = std::sin(w0);
                double cosW0 = std::cos(w0);
                double alpha = sinW0 / (2.0 * Q);

                // Notch (band-reject) biquad coefficients
                double b0 = 1.0;
                double b1 = -2.0 * cosW0;
                double b2 = 1.0;
                double a0 = 1.0 + alpha;
                double a1 = -2.0 * cosW0;
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

        // === Write processed signal to delay line (for feedback) ===
        delayLine[delayWritePos] = processed;

        // === Read from delay line for feedback ===
        int readPos = (delayWritePos - feedbackDelay + MAX_DELAY) % MAX_DELAY;
        float delayOut = delayLine[readPos];

        delayWritePos = (delayWritePos + 1) % MAX_DELAY;

        // === Feedback path: delay output -> LP filter -> gain -> back to input ===
        // Low-pass filter in feedback path (shimmer controls brightness)
        fbFilterState += fbFilterCoeff * (static_cast<double>(delayOut) - fbFilterState);
        float filtered = static_cast<float>(fbFilterState);

        // Apply feedback gain (warp controls how much recirculates)
        feedbackSample = filtered * feedbackGain;

        // Soft-clip feedback to prevent runaway
        feedbackSample = std::tanh(feedbackSample);

        // === Wet/dry mix ===
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
    int activeNotches = 3;
    double sweepLfoPhase = 0.0;
    double sweepRate = 0.3;
    float sweepMinFreq = 200.0f;
    float sweepMaxFreq = 4000.0f;
    float notchDepth = 1.0f;
    double notchState[MAX_NOTCHES][2] = {};

    // Feedback delay line
    std::array<float, MAX_DELAY> delayLine;
    int delayWritePos = 0;
    int feedbackDelay = 4410;
    float feedbackGain = 0.5f;

    // Feedback filter (1-pole LP)
    double fbFilterCoeff = 0.5;
    double fbFilterState = 0.0;

    // Feedback return sample
    float feedbackSample = 0.0f;

    // Output
    float wetDry = 0.5f;
};
