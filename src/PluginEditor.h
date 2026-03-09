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
    class CrayonLookAndFeel : public juce::LookAndFeel_V4
    {
    public:
        CrayonLookAndFeel();
        void drawRotarySlider(juce::Graphics&, int x, int y, int w, int h,
                              float sliderPosProportional, float rotaryStartAngle,
                              float rotaryEndAngle, juce::Slider&) override;
        void drawToggleButton(juce::Graphics&, juce::ToggleButton&,
                              bool shouldDrawButtonAsHighlighted,
                              bool shouldDrawButtonAsDown) override;
    };
    CrayonLookAndFeel crayonLnf;

    // ---- Drawing helpers ----
    void drawBackground(juce::Graphics&);
    void drawTitle(juce::Graphics&);
    void drawSectionBox(juce::Graphics&, juce::Rectangle<int> bounds,
                        juce::Colour colour, const juce::String& title);
    void drawMushroom(juce::Graphics&, float x, float y, float size, float phase);
    void drawStar(juce::Graphics&, float cx, float cy, float size, float twinkle);
    void drawGhost(juce::Graphics&, float x, float y, float size, float phase);
    void drawCrystal(juce::Graphics&, float x, float y, float size, float rotation);
    void drawFlower(juce::Graphics&, float x, float y, float size, float rotation);
    void drawAlienEye(juce::Graphics&, float x, float y, float size, float lookPhase);
    void drawSparkles(juce::Graphics&);
    juce::Path makeWobblyRect(juce::Rectangle<float> r, float wobble, unsigned int seed);

    // ---- Animation state ----
    float animTime = 0.0f;
    struct Creature {
        int type;       // 0=mushroom, 1=ghost, 2=crystal, 3=flower, 4=alien eye
        float baseX, baseY;
        float driftX, driftY;   // amplitude of movement
        float speedX, speedY;   // frequency
        float size;
        float phaseX, phaseY;   // initial phase offsets
    };
    std::vector<Creature> creatures;
    struct Sparkle {
        float x, y, phase, speed, size;
    };
    std::vector<Sparkle> sparkles;
    void initCreatures();

    // ---- Controls ----
    // Swell
    juce::Slider swellSens, swellAttack, swellDepth;
    // Vinyl
    juce::Slider vinylYear, vinylWarp, vinylDust, vinylWear, vinylDetune, vinylNoise;
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
    std::unique_ptr<SliderAttachment> aVinylYear, aVinylWarp, aVinylDust, aVinylWear, aVinylDetune, aVinylNoise;
    std::unique_ptr<SliderAttachment> aPsycheShimmer, aPsycheSpace, aPsycheMod, aPsycheWarp, aPsycheMix, aPsycheNotches, aPsycheSweep;
    std::unique_ptr<SliderAttachment> aLfoShape, aLfoRate, aLfoDepth, aLfoSyncRate, aLfoPhaseOffset;
    std::unique_ptr<SliderAttachment> aMasterMix, aMasterGain;
    std::unique_ptr<ButtonAttachment> aSwellBypass, aVinylBypass, aPsycheBypass, aLfoBypass, aLfoSync;

    void setupSlider(juce::Slider& s, bool isInt = false);

    JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR(AetherEditor)
};
