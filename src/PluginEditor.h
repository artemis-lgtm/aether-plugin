#pragma once
#include "PluginProcessor.h"
#include <juce_audio_processors/juce_audio_processors.h>
#include <juce_gui_basics/juce_gui_basics.h>
#include <random>

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

    // ---- Image-based knob Look & Feel ----
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
        int frameW = 64;
    };
    FilmstripLookAndFeel filmstripLnf;

    // Background image
    juce::Image backgroundImg;

    // Title animation
    float animTime = 0.0f;
    void drawTitle(juce::Graphics&);
    void drawSwimmingCharacters(juce::Graphics&);

    // Animated characters
    struct Swimmer {
        int type;
        float y, speed, size, phaseOffset;
        juce::Colour colour;
        bool goingRight;
    };
    std::vector<Swimmer> swimmers;
    void initSwimmers();

    // Character drawing
    void drawMushroom(juce::Graphics&, float x, float y, float size, float phase, juce::Colour cap);
    void drawGhost(juce::Graphics&, float x, float y, float size, float phase);
    void drawAlien(juce::Graphics&, float x, float y, float size, float phase, juce::Colour body);

    // ---- Controls ----
    juce::Slider swellSens, swellAttack, swellDepth;
    juce::Slider vinylYear, vinylDetune;
    juce::Slider psycheShimmer, psycheSpace, psycheMod, psycheWarp, psycheMix, psycheNotches, psycheSweep;
    juce::Slider lfoShape, lfoRate, lfoDepth, lfoSyncRate, lfoPhaseOffset;
    juce::Slider masterMix, masterGain;
    juce::ToggleButton swellBypass{"S"}, vinylBypass{"V"}, psycheBypass{"P"}, lfoBypass{"L"};
    juce::ToggleButton lfoSync{"SYNC"};

    std::vector<std::unique_ptr<juce::Label>> labels;
    juce::Label& addLabel(juce::Slider& s, const juce::String& text);

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
