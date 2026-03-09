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

    // ---- Custom Look & Feel ----
    class PedalLookAndFeel : public juce::LookAndFeel_V4
    {
    public:
        PedalLookAndFeel();
        void drawRotarySlider(juce::Graphics&, int x, int y, int w, int h,
                              float sliderPos, float rotaryStartAngle,
                              float rotaryEndAngle, juce::Slider&) override;
        void drawToggleButton(juce::Graphics&, juce::ToggleButton&,
                              bool highlighted, bool down) override;
    };
    PedalLookAndFeel pedalLnf;

    // ---- Drawing helpers ----
    void drawPedalBackground(juce::Graphics&);
    void drawTitle(juce::Graphics&);
    void drawSectionBox(juce::Graphics&, juce::Rectangle<int> bounds,
                        juce::Colour colour, const juce::String& title);
    void drawSwimmingCharacters(juce::Graphics&);

    // Character drawing
    void drawPrincess(juce::Graphics&, float x, float y, float size, float phase, juce::Colour dress);
    void drawFairy(juce::Graphics&, float x, float y, float size, float phase, juce::Colour glow);
    void drawUnicorn(juce::Graphics&, float x, float y, float size, float phase);
    void drawStar(juce::Graphics&, float cx, float cy, float size, float alpha);
    void drawCrayonScribble(juce::Graphics&, float x, float y, float w, float h,
                            juce::Colour colour, unsigned int seed);
    juce::Path makeWobblyRect(juce::Rectangle<float> r, float wobble, unsigned int seed);

    // ---- Animation ----
    float animTime = 0.0f;
    struct Swimmer {
        int type;          // 0=princess, 1=fairy, 2=unicorn
        float startX;      // starting X (offscreen left or right)
        float y;
        float speed;       // pixels per frame
        float size;
        float phaseOffset;
        juce::Colour colour;
        bool goingRight;
    };
    std::vector<Swimmer> swimmers;
    struct BgStar { float x, y, phase, speed, size; };
    std::vector<BgStar> bgStars;
    void initSwimmers();

    // ---- Controls ----
    // Swell
    juce::Slider swellSens, swellAttack, swellDepth;
    // Vinyl (year + detune only)
    juce::Slider vinylYear, vinylDetune;
    // Psyche
    juce::Slider psycheShimmer, psycheSpace, psycheMod, psycheWarp, psycheMix, psycheNotches, psycheSweep;
    // LFO
    juce::Slider lfoShape, lfoRate, lfoDepth, lfoSyncRate, lfoPhaseOffset;
    // Master
    juce::Slider masterMix, masterGain;
    // Toggles
    juce::ToggleButton swellBypass{"S"}, vinylBypass{"V"}, psycheBypass{"P"}, lfoBypass{"L"};
    juce::ToggleButton lfoSync{"SYNC"};

    // Labels
    std::vector<std::unique_ptr<juce::Label>> labels;
    juce::Label& addLabel(juce::Slider& s, const juce::String& text);

    // Attachments
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
