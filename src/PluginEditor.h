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
                              float sliderPos, float rotaryStartAngle,
                              float rotaryEndAngle, juce::Slider&) override;
        void drawToggleButton(juce::Graphics&, juce::ToggleButton&,
                              bool highlighted, bool down) override;
    };
    CrayonLookAndFeel crayonLnf;

    // ---- Drawing helpers ----
    void drawSkyBackground(juce::Graphics&);
    void drawCloud(juce::Graphics&, float x, float y, float w);
    void drawSun(juce::Graphics&, float x, float y, float r);
    void drawTitle(juce::Graphics&);
    void drawSectionLabel(juce::Graphics&, int x, int y, int w, const juce::String& title, juce::Colour col);
    void drawDoodles(juce::Graphics&);
    void drawSwimmingCharacters(juce::Graphics&);

    // Doodle characters (drawn procedurally like kid's crayon drawings)
    void drawBoombox(juce::Graphics&, float x, float y, float size, float phase);
    void drawCassette(juce::Graphics&, float x, float y, float size, float phase);
    void drawMushroom(juce::Graphics&, float x, float y, float size, float phase, juce::Colour cap);
    void drawAlien(juce::Graphics&, float x, float y, float size, float phase, juce::Colour body);
    void drawFlower(juce::Graphics&, float x, float y, float size, float phase, juce::Colour petals);
    void drawGhost(juce::Graphics&, float x, float y, float size, float phase);
    void drawStar4(juce::Graphics&, float cx, float cy, float size);

    // ---- Animation ----
    float animTime = 0.0f;
    struct Swimmer {
        int type;       // 0=mushroom 1=alien 2=flower 3=ghost 4=boombox 5=cassette
        float y;
        float speed;
        float size;
        float phaseOffset;
        juce::Colour colour;
        bool goingRight;
    };
    std::vector<Swimmer> swimmers;
    void initSwimmers();

    // ---- Controls ----
    juce::Slider swellSens, swellAttack, swellDepth;
    juce::Slider vinylYear, vinylDetune;
    juce::Slider psycheShimmer, psycheSpace, psycheMod, psycheWarp, psycheMix, psycheNotches, psycheSweep;
    juce::Slider lfoShape, lfoRate, lfoDepth, lfoSyncRate, lfoPhaseOffset;
    juce::Slider masterMix, masterGain;
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
