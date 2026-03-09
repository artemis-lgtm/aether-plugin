#pragma once
#include "PluginProcessor.h"
#include <juce_audio_processors/juce_audio_processors.h>
#include <juce_gui_basics/juce_gui_basics.h>

class AetherEditor : public juce::AudioProcessorEditor,
                     private juce::Timer
{
public:
    AetherEditor(AetherProcessor&);
    ~AetherEditor() override;

    void paint(juce::Graphics&) override;
    void resized() override;
    void timerCallback() override;

private:
    AetherProcessor& processor;

    // ---- Filmstrip knob Look & Feel ----
    class FilmstripLookAndFeel : public juce::LookAndFeel_V4
    {
    public:
        FilmstripLookAndFeel();
        void setKnobStrip(juce::Image strip, int numFrames);
        void drawRotarySlider(juce::Graphics&, int x, int y, int w, int h,
                              float sliderPos, float rotaryStartAngle,
                              float rotaryEndAngle, juce::Slider&) override;
        void drawToggleButton(juce::Graphics&, juce::ToggleButton&,
                              bool highlighted, bool down) override;
    private:
        juce::Image knobStrip;
        int frames = 128;
        int frameW = 128;
    };
    FilmstripLookAndFeel filmstripLnf;

    juce::Image backgroundImg;

    // Title animation
    float animTime = 0.0f;
    void drawTitle(juce::Graphics&);
    void drawSectionLabel(juce::Graphics&, const juce::String& text, int x, int y, int width);
    void drawKnobLabel(juce::Graphics&, const juce::String& text, int knobX, int y);

    // ---- Controls ----
    juce::Slider swellSens, swellAttack, swellDepth;
    juce::Slider vinylYear, vinylDetune;
    juce::Slider psycheShimmer, psycheSpace, psycheMod, psycheWarp, psycheMix, psycheNotches, psycheSweep;
    juce::Slider lfoShape, lfoRate, lfoDepth, lfoSyncRate, lfoPhaseOffset;
    juce::Slider masterMix, masterGain;
    juce::ToggleButton swellBypass{"S"}, vinylBypass{"V"}, psycheBypass{"P"}, lfoBypass{"L"};
    juce::ToggleButton lfoSync{"SYNC"};

    using SliderAttachment = juce::AudioProcessorValueTreeState::SliderAttachment;
    using ButtonAttachment = juce::AudioProcessorValueTreeState::ButtonAttachment;
    std::unique_ptr<SliderAttachment> aSwellSens, aSwellAttack, aSwellDepth;
    std::unique_ptr<SliderAttachment> aVinylYear, aVinylDetune;
    std::unique_ptr<SliderAttachment> aPsycheShimmer, aPsycheSpace, aPsycheMod, aPsycheWarp, aPsycheMix, aPsycheNotches, aPsycheSweep;
    std::unique_ptr<SliderAttachment> aLfoShape, aLfoRate, aLfoDepth, aLfoSyncRate, aLfoPhaseOffset;
    std::unique_ptr<SliderAttachment> aMasterMix, aMasterGain;
    std::unique_ptr<ButtonAttachment> aSwellBypass, aVinylBypass, aPsycheBypass, aLfoBypass, aLfoSync;

    JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR(AetherEditor)
};
