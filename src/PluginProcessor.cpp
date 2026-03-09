#include "PluginProcessor.h"
#include "PluginEditor.h"

AetherProcessor::AetherProcessor()
    : AudioProcessor(BusesProperties()
                     .withInput("Input", juce::AudioChannelSet::stereo(), true)
                     .withOutput("Output", juce::AudioChannelSet::stereo(), true)),
      apvts(*this, nullptr, "Parameters", createParameterLayout())
{
}

AetherProcessor::~AetherProcessor() {}

juce::AudioProcessorValueTreeState::ParameterLayout AetherProcessor::createParameterLayout()
{
    std::vector<std::unique_ptr<juce::RangedAudioParameter>> params;

    // === SWELL (Transient Shaper) ===
    params.push_back(std::make_unique<juce::AudioParameterFloat>(
        juce::ParameterID("swellSens", 1), "Swell Sensitivity",
        juce::NormalisableRange<float>(0.0f, 1.0f, 0.01f), 0.5f));
    
    params.push_back(std::make_unique<juce::AudioParameterFloat>(
        juce::ParameterID("swellAttack", 1), "Swell Attack",
        juce::NormalisableRange<float>(10.0f, 500.0f, 1.0f, 0.5f), 120.0f));
    
    params.push_back(std::make_unique<juce::AudioParameterFloat>(
        juce::ParameterID("swellDepth", 1), "Swell Depth",
        juce::NormalisableRange<float>(0.0f, 1.0f, 0.01f), 0.8f));

    // === VINYL ===
    params.push_back(std::make_unique<juce::AudioParameterFloat>(
        juce::ParameterID("vinylYear", 1), "Vinyl Year",
        juce::NormalisableRange<float>(0.0f, 1.0f, 0.01f), 0.3f));
    
    params.push_back(std::make_unique<juce::AudioParameterFloat>(
        juce::ParameterID("vinylWarp", 1), "Vinyl Warp",
        juce::NormalisableRange<float>(0.0f, 1.0f, 0.01f), 0.25f));
    
    params.push_back(std::make_unique<juce::AudioParameterFloat>(
        juce::ParameterID("vinylDust", 1), "Vinyl Dust",
        juce::NormalisableRange<float>(0.0f, 1.0f, 0.01f), 0.15f));
    
    params.push_back(std::make_unique<juce::AudioParameterFloat>(
        juce::ParameterID("vinylWear", 1), "Vinyl Wear",
        juce::NormalisableRange<float>(0.0f, 1.0f, 0.01f), 0.2f));
    
    params.push_back(std::make_unique<juce::AudioParameterFloat>(
        juce::ParameterID("vinylDetune", 1), "Vinyl Detune",
        juce::NormalisableRange<float>(0.0f, 1.0f, 0.01f), 0.0f));
    
    params.push_back(std::make_unique<juce::AudioParameterFloat>(
        juce::ParameterID("vinylNoise", 1), "Vinyl Noise",
        juce::NormalisableRange<float>(0.0f, 1.0f, 0.01f), 0.0f));

    // === PSYCHE (Enigma-inspired + Shimmer) ===
    params.push_back(std::make_unique<juce::AudioParameterFloat>(
        juce::ParameterID("psycheShimmer", 1), "Shimmer",
        juce::NormalisableRange<float>(0.0f, 1.0f, 0.01f), 0.4f));
    
    params.push_back(std::make_unique<juce::AudioParameterFloat>(
        juce::ParameterID("psycheSpace", 1), "Space",
        juce::NormalisableRange<float>(0.0f, 1.0f, 0.01f), 0.5f));
    
    params.push_back(std::make_unique<juce::AudioParameterFloat>(
        juce::ParameterID("psycheMod", 1), "Modulation",
        juce::NormalisableRange<float>(0.0f, 1.0f, 0.01f), 0.35f));
    
    params.push_back(std::make_unique<juce::AudioParameterFloat>(
        juce::ParameterID("psycheWarp", 1), "Warp",
        juce::NormalisableRange<float>(0.0f, 1.0f, 0.01f), 0.3f));
    
    params.push_back(std::make_unique<juce::AudioParameterFloat>(
        juce::ParameterID("psycheMix", 1), "Psyche Mix",
        juce::NormalisableRange<float>(0.0f, 1.0f, 0.01f), 0.5f));
    
    params.push_back(std::make_unique<juce::AudioParameterFloat>(
        juce::ParameterID("psycheNotches", 1), "Notches",
        juce::NormalisableRange<float>(0.0f, 1.0f, 0.01f), 0.5f));
    
    params.push_back(std::make_unique<juce::AudioParameterFloat>(
        juce::ParameterID("psycheSweep", 1), "Sweep",
        juce::NormalisableRange<float>(0.0f, 1.0f, 0.01f), 0.5f));

    // === LFO (Volume Shaper) ===
    params.push_back(std::make_unique<juce::AudioParameterFloat>(
        juce::ParameterID("lfoShape", 1), "LFO Shape",
        juce::NormalisableRange<float>(0.0f, 7.0f, 1.0f), 0.0f));
    
    params.push_back(std::make_unique<juce::AudioParameterFloat>(
        juce::ParameterID("lfoRate", 1), "LFO Rate",
        juce::NormalisableRange<float>(0.1f, 20.0f, 0.01f, 0.4f), 2.0f));
    
    params.push_back(std::make_unique<juce::AudioParameterFloat>(
        juce::ParameterID("lfoDepth", 1), "LFO Depth",
        juce::NormalisableRange<float>(0.0f, 1.0f, 0.01f), 0.0f));

    // === MASTER ===
    params.push_back(std::make_unique<juce::AudioParameterFloat>(
        juce::ParameterID("masterMix", 1), "Master Mix",
        juce::NormalisableRange<float>(0.0f, 1.0f, 0.01f), 0.7f));
    
    params.push_back(std::make_unique<juce::AudioParameterFloat>(
        juce::ParameterID("masterGain", 1), "Output Gain",
        juce::NormalisableRange<float>(-12.0f, 6.0f, 0.1f), 0.0f));

    // === Section Bypasses ===
    params.push_back(std::make_unique<juce::AudioParameterBool>(
        juce::ParameterID("swellBypass", 1), "Swell Bypass", false));
    
    params.push_back(std::make_unique<juce::AudioParameterBool>(
        juce::ParameterID("vinylBypass", 1), "Vinyl Bypass", false));
    
    params.push_back(std::make_unique<juce::AudioParameterBool>(
        juce::ParameterID("psycheBypass", 1), "Psyche Bypass", false));
    
    params.push_back(std::make_unique<juce::AudioParameterBool>(
        juce::ParameterID("lfoBypass", 1), "LFO Bypass", false));

    return { params.begin(), params.end() };
}

void AetherProcessor::prepareToPlay(double sampleRate, int samplesPerBlock)
{
    transientL.prepare(sampleRate, samplesPerBlock);
    transientR.prepare(sampleRate, samplesPerBlock);
    vinylL.prepare(sampleRate, samplesPerBlock);
    vinylR.prepare(sampleRate, samplesPerBlock);
    psychL.prepare(sampleRate, samplesPerBlock);
    psychR.prepare(sampleRate, samplesPerBlock);
    lfo.prepare(sampleRate, samplesPerBlock);
}

void AetherProcessor::releaseResources() {}

void AetherProcessor::processBlock(juce::AudioBuffer<float>& buffer, juce::MidiBuffer&)
{
    juce::ScopedNoDenormals noDenormals;
    auto totalNumInputChannels = getTotalNumInputChannels();
    auto totalNumOutputChannels = getTotalNumOutputChannels();
    int numSamples = buffer.getNumSamples();

    for (auto i = totalNumInputChannels; i < totalNumOutputChannels; ++i)
        buffer.clear(i, 0, numSamples);

    // Read parameters
    float swellSens = *apvts.getRawParameterValue("swellSens");
    float swellAttack = *apvts.getRawParameterValue("swellAttack");
    float swellDepth = *apvts.getRawParameterValue("swellDepth");
    bool swellBypass = *apvts.getRawParameterValue("swellBypass") > 0.5f;
    
    float vYear = *apvts.getRawParameterValue("vinylYear");
    float vWarp = *apvts.getRawParameterValue("vinylWarp");
    float vDust = *apvts.getRawParameterValue("vinylDust");
    float vWear = *apvts.getRawParameterValue("vinylWear");
    float vDetune = *apvts.getRawParameterValue("vinylDetune");
    float vNoise = *apvts.getRawParameterValue("vinylNoise");
    bool vinylBypass = *apvts.getRawParameterValue("vinylBypass") > 0.5f;
    
    float pShimmer = *apvts.getRawParameterValue("psycheShimmer");
    float pSpace = *apvts.getRawParameterValue("psycheSpace");
    float pMod = *apvts.getRawParameterValue("psycheMod");
    float pWarp = *apvts.getRawParameterValue("psycheWarp");
    float pMix = *apvts.getRawParameterValue("psycheMix");
    float pNotches = *apvts.getRawParameterValue("psycheNotches");
    float pSweep = *apvts.getRawParameterValue("psycheSweep");
    bool psycheBypass = *apvts.getRawParameterValue("psycheBypass") > 0.5f;
    
    int lShape = static_cast<int>(*apvts.getRawParameterValue("lfoShape"));
    float lRate = *apvts.getRawParameterValue("lfoRate");
    float lDepth = *apvts.getRawParameterValue("lfoDepth");
    bool lfoBypass = *apvts.getRawParameterValue("lfoBypass") > 0.5f;
    
    float masterMix = *apvts.getRawParameterValue("masterMix");
    float masterGain = *apvts.getRawParameterValue("masterGain");
    float gainLinear = juce::Decibels::decibelsToGain(masterGain);

    // Update DSP parameters
    transientL.setParameters(swellSens, swellAttack, swellDepth);
    transientR.setParameters(swellSens, swellAttack, swellDepth);
    vinylL.setParameters(vYear, vWarp, vDust, vWear, vDetune, vNoise);
    vinylR.setParameters(vYear, vWarp, vDust, vWear, vDetune, vNoise);
    psychL.setParameters(pShimmer, pSpace, pMod, pWarp, pMix, pNotches, pSweep);
    psychR.setParameters(pShimmer, pSpace, pMod, pWarp, pMix, pNotches, pSweep);
    lfo.setParameters(lShape, lRate, lDepth);

    // Store dry signal for master mix
    juce::AudioBuffer<float> dryBuffer;
    dryBuffer.makeCopyOf(buffer);

    // Process per-channel effects: Swell → Vinyl → Psyche
    for (int channel = 0; channel < juce::jmin(totalNumInputChannels, 2); ++channel)
    {
        float* channelData = buffer.getWritePointer(channel);
        
        auto& transient = (channel == 0) ? transientL : transientR;
        auto& vinyl = (channel == 0) ? vinylL : vinylR;
        auto& psych = (channel == 0) ? psychL : psychR;

        if (!swellBypass)
            transient.processBlock(channelData, numSamples);
        
        if (!vinylBypass)
            vinyl.processBlock(channelData, numSamples);
        
        if (!psycheBypass)
            psych.processBlock(channelData, numSamples);
    }

    // LFO: apply same gain to both channels (shared phase)
    if (!lfoBypass && lDepth > 0.001f)
    {
        int channels = juce::jmin(totalNumInputChannels, 2);
        for (int i = 0; i < numSamples; ++i)
        {
            float gain = lfo.nextGain();
            for (int ch = 0; ch < channels; ++ch)
                buffer.getWritePointer(ch)[i] *= gain;
        }
    }

    // Master mix (dry/wet) and gain
    for (int channel = 0; channel < juce::jmin(totalNumInputChannels, 2); ++channel)
    {
        float* wet = buffer.getWritePointer(channel);
        const float* dry = dryBuffer.getReadPointer(channel);
        
        for (int i = 0; i < numSamples; ++i)
        {
            wet[i] = (dry[i] * (1.0f - masterMix) + wet[i] * masterMix) * gainLinear;
        }
    }
}

void AetherProcessor::getStateInformation(juce::MemoryBlock& destData)
{
    auto state = apvts.copyState();
    std::unique_ptr<juce::XmlElement> xml(state.createXml());
    copyXmlToBinary(*xml, destData);
}

void AetherProcessor::setStateInformation(const void* data, int sizeInBytes)
{
    std::unique_ptr<juce::XmlElement> xml(getXmlFromBinary(data, sizeInBytes));
    if (xml != nullptr && xml->hasTagName(apvts.state.getType()))
        apvts.replaceState(juce::ValueTree::fromXml(*xml));
}

juce::AudioProcessorEditor* AetherProcessor::createEditor()
{
    return new AetherEditor(*this);
}

juce::AudioProcessor* JUCE_CALLTYPE createPluginFilter()
{
    return new AetherProcessor();
}
