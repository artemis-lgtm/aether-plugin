#pragma once
#include <juce_gui_extra/juce_gui_extra.h>
#include "PluginProcessor.h"

class AetherEditor : public juce::AudioProcessorEditor, private juce::Timer
{
public:
    explicit AetherEditor(AetherProcessor&);
    ~AetherEditor() override;

    void paint(juce::Graphics&) override;
    void resized() override;

private:
    void timerCallback() override;
    
    // Custom knob look
    class AetherLookAndFeel : public juce::LookAndFeel_V4
    {
    public:
        AetherLookAndFeel();
        void drawRotarySlider(juce::Graphics&, int x, int y, int width, int height,
                             float sliderPos, float rotaryStartAngle, float rotaryEndAngle,
                             juce::Slider&) override;
        void drawToggleButton(juce::Graphics&, juce::ToggleButton&,
                             bool shouldDrawButtonAsHighlighted, bool shouldDrawButtonAsDown) override;
    };

    AetherLookAndFeel aetherLnf;
    AetherProcessor& processorRef;

    // Helper to create attached sliders
    struct KnobAttachment {
        juce::Slider slider;
        std::unique_ptr<juce::AudioProcessorValueTreeState::SliderAttachment> attachment;
        juce::Label label;
    };

    struct BypassAttachment {
        juce::ToggleButton button;
        std::unique_ptr<juce::AudioProcessorValueTreeState::ButtonAttachment> attachment;
    };

    // Swell section
    KnobAttachment swellSens, swellAttack, swellDepth;
    BypassAttachment swellBypass;
    
    // Vinyl section
    KnobAttachment vinylYear, vinylWarp, vinylDust, vinylWear, vinylDetune, vinylNoise;
    BypassAttachment vinylBypassBtn;
    
    // Psyche section
    KnobAttachment psycheShimmer, psycheSpace, psycheMod, psycheWarp, psycheMix;
    KnobAttachment psycheNotches, psycheSweep;
    BypassAttachment psycheBypassBtn;
    
    // LFO section
    KnobAttachment lfoShape, lfoRate, lfoDepth;
    BypassAttachment lfoBypassBtn;
    
    // Master
    KnobAttachment masterMix, masterGain;

    // Animation
    float animPhase = 0.0f;

    void setupKnob(KnobAttachment& knob, const juce::String& paramId, const juce::String& name);
    void setupBypass(BypassAttachment& bp, const juce::String& paramId, const juce::String& name);

    JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR(AetherEditor)
};
