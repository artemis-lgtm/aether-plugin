#include "PluginEditor.h"
#include "dsp/LFOProcessor.h"
#include "BinaryData.h"
#include <cmath>

// ================================================================
// Filmstrip Look & Feel
// ================================================================
AetherEditor::FilmstripLookAndFeel::FilmstripLookAndFeel() {}

void AetherEditor::FilmstripLookAndFeel::setKnobStrip(juce::Image strip, int numFrames)
{
    knobStrip = strip;
    frames = numFrames;
    if (knobStrip.isValid())
        frameW = knobStrip.getWidth() / frames;
}

void AetherEditor::FilmstripLookAndFeel::drawRotarySlider(
    juce::Graphics& g, int x, int y, int w, int h,
    float sliderPos, float, float, juce::Slider&)
{
    if (!knobStrip.isValid())
        return;

    int frameIndex = static_cast<int>(sliderPos * (float)(frames - 1) + 0.5f);
    frameIndex = juce::jlimit(0, frames - 1, frameIndex);

    int srcX = frameIndex * frameW;
    float scale = juce::jmin((float)w / (float)frameW, (float)h / (float)frameW);
    float drawW = (float)frameW * scale;
    float drawH = (float)frameW * scale;
    float drawX = (float)x + ((float)w - drawW) * 0.5f;
    float drawY = (float)y + ((float)h - drawH) * 0.5f;

    g.drawImage(knobStrip,
                (int)drawX, (int)drawY, (int)drawW, (int)drawH,
                srcX, 0, frameW, frameW);
}

void AetherEditor::FilmstripLookAndFeel::drawToggleButton(
    juce::Graphics& g, juce::ToggleButton& button, bool, bool)
{
    auto bounds = button.getLocalBounds().toFloat().reduced(1.0f);
    bool on = button.getToggleState();
    bool isBypass = button.getButtonText().length() == 1;

    if (isBypass)
    {
        g.setColour(on ? juce::Colour(0xBBFF4444) : juce::Colour(0xBB44DD44));
        g.fillRoundedRectangle(bounds, 8.0f);
        g.setColour(juce::Colour(0x60000000));
        g.drawRoundedRectangle(bounds, 8.0f, 1.5f);
        g.setColour(juce::Colours::white);
        g.setFont(juce::Font(10.0f).boldened());
        g.drawText(on ? "OFF" : "ON", bounds, juce::Justification::centred);
    }
    else
    {
        g.setColour(on ? juce::Colour(0xBBFF2828) : juce::Colour(0xBB888888));
        g.fillRoundedRectangle(bounds, 8.0f);
        g.setColour(juce::Colour(0x60000000));
        g.drawRoundedRectangle(bounds, 8.0f, 1.5f);
        g.setColour(juce::Colours::white);
        g.setFont(juce::Font(9.0f).boldened());
        g.drawText(button.getButtonText(), bounds, juce::Justification::centred);
    }
}

// ================================================================
// Constructor
// ================================================================
AetherEditor::AetherEditor(AetherProcessor& p)
    : AudioProcessorEditor(&p), processor(p)
{
    // Background (baked: wood texture + duct tape labels + neon title + portrait)
    backgroundImg = juce::ImageFileFormat::loadFrom(
        BinaryData::background_png, BinaryData::background_pngSize);

    // Per-section colored knob filmstrips
    auto loadStrip = [](FilmstripLookAndFeel& lnf, const char* data, int size) {
        juce::Image img = juce::ImageFileFormat::loadFrom(data, size);
        lnf.setKnobStrip(img, 128);
    };

    loadStrip(swellLnf,  BinaryData::knobswell_png,  BinaryData::knobswell_pngSize);
    loadStrip(vinylLnf,  BinaryData::knobvinyl_png,   BinaryData::knobvinyl_pngSize);
    loadStrip(masterLnf, BinaryData::knobmaster_png,  BinaryData::knobmaster_pngSize);
    loadStrip(psycheLnf, BinaryData::knobpsyche_png,  BinaryData::knobpsyche_pngSize);
    loadStrip(lfoLnf,    BinaryData::knoblfo_png,     BinaryData::knoblfo_pngSize);

    setSize(1020, 620);

    // Setup knobs with section-specific look and feel
    auto setupKnob = [&](juce::Slider& s, FilmstripLookAndFeel& lnf) {
        s.setSliderStyle(juce::Slider::RotaryHorizontalVerticalDrag);
        s.setTextBoxStyle(juce::Slider::NoTextBox, false, 0, 0);
        s.setLookAndFeel(&lnf);
        addAndMakeVisible(s);
    };

    setupKnob(swellSens, swellLnf);
    setupKnob(swellAttack, swellLnf);
    setupKnob(swellDepth, swellLnf);
    setupKnob(vinylYear, vinylLnf);
    setupKnob(vinylDetune, vinylLnf);
    setupKnob(psycheShimmer, psycheLnf);
    setupKnob(psycheSpace, psycheLnf);
    setupKnob(psycheMod, psycheLnf);
    setupKnob(psycheWarp, psycheLnf);
    setupKnob(psycheMix, psycheLnf);
    setupKnob(psycheNotches, psycheLnf);
    setupKnob(psycheSweep, psycheLnf);
    setupKnob(lfoShape, lfoLnf);
    setupKnob(lfoRate, lfoLnf);
    setupKnob(lfoDepth, lfoLnf);
    setupKnob(lfoSyncRate, lfoLnf);
    setupKnob(lfoPhaseOffset, lfoLnf);
    setupKnob(masterMix, masterLnf);
    setupKnob(masterGain, masterLnf);

    for (auto* b : { &swellBypass, &vinylBypass, &psycheBypass, &lfoBypass, &lfoSync })
        addAndMakeVisible(*b);

    auto& apvts = processor.apvts;
    aSwellSens     = std::make_unique<SliderAttachment>(apvts, "swellSens",     swellSens);
    aSwellAttack   = std::make_unique<SliderAttachment>(apvts, "swellAttack",   swellAttack);
    aSwellDepth    = std::make_unique<SliderAttachment>(apvts, "swellDepth",    swellDepth);
    aVinylYear     = std::make_unique<SliderAttachment>(apvts, "vinylYear",     vinylYear);
    aVinylDetune   = std::make_unique<SliderAttachment>(apvts, "vinylDetune",   vinylDetune);
    aPsycheShimmer = std::make_unique<SliderAttachment>(apvts, "psycheShimmer", psycheShimmer);
    aPsycheSpace   = std::make_unique<SliderAttachment>(apvts, "psycheSpace",   psycheSpace);
    aPsycheMod     = std::make_unique<SliderAttachment>(apvts, "psycheMod",     psycheMod);
    aPsycheWarp    = std::make_unique<SliderAttachment>(apvts, "psycheWarp",    psycheWarp);
    aPsycheMix     = std::make_unique<SliderAttachment>(apvts, "psycheMix",     psycheMix);
    aPsycheNotches = std::make_unique<SliderAttachment>(apvts, "psycheNotches", psycheNotches);
    aPsycheSweep   = std::make_unique<SliderAttachment>(apvts, "psycheSweep",   psycheSweep);
    aLfoShape      = std::make_unique<SliderAttachment>(apvts, "lfoShape",      lfoShape);
    aLfoRate       = std::make_unique<SliderAttachment>(apvts, "lfoRate",       lfoRate);
    aLfoDepth      = std::make_unique<SliderAttachment>(apvts, "lfoDepth",      lfoDepth);
    aLfoSyncRate   = std::make_unique<SliderAttachment>(apvts, "lfoSyncRate",   lfoSyncRate);
    aLfoPhaseOffset = std::make_unique<SliderAttachment>(apvts, "lfoPhaseOffset", lfoPhaseOffset);
    aMasterMix     = std::make_unique<SliderAttachment>(apvts, "masterMix",     masterMix);
    aMasterGain    = std::make_unique<SliderAttachment>(apvts, "masterGain",    masterGain);
    aSwellBypass   = std::make_unique<ButtonAttachment>(apvts, "swellBypass",   swellBypass);
    aVinylBypass   = std::make_unique<ButtonAttachment>(apvts, "vinylBypass",   vinylBypass);
    aPsycheBypass  = std::make_unique<ButtonAttachment>(apvts, "psycheBypass",  psycheBypass);
    aLfoBypass     = std::make_unique<ButtonAttachment>(apvts, "lfoBypass",     lfoBypass);
    aLfoSync       = std::make_unique<ButtonAttachment>(apvts, "lfoSync",       lfoSync);
}

AetherEditor::~AetherEditor()
{
    // Clear per-slider LAF before destruction
    for (auto* s : { &swellSens, &swellAttack, &swellDepth,
                     &vinylYear, &vinylDetune,
                     &psycheShimmer, &psycheSpace, &psycheMod, &psycheWarp,
                     &psycheMix, &psycheNotches, &psycheSweep,
                     &lfoShape, &lfoRate, &lfoDepth, &lfoSyncRate, &lfoPhaseOffset,
                     &masterMix, &masterGain })
        s->setLookAndFeel(nullptr);
}

// ================================================================
// Layout — two-column design matching baked background
// ================================================================
// UV coordinates from render: x/1020, y/620
// Knob size reduced to avoid covering duct tape labels
void AetherEditor::resized()
{
    int K = 56; // knob size (smaller to not cover labels)

    // LEFT COLUMN: Swell / Vinyl / Master stacked
    // Swell row (3 knobs)
    swellSens.setBounds  (80  - K/2, 240 - K/2, K, K);
    swellAttack.setBounds(160 - K/2, 240 - K/2, K, K);
    swellDepth.setBounds (240 - K/2, 240 - K/2, K, K);
    swellBypass.setBounds(40, 188, 36, 22);

    // Vinyl row (2 knobs)
    vinylYear.setBounds  (80  - K/2, 355 - K/2, K, K);
    vinylDetune.setBounds(160 - K/2, 355 - K/2, K, K);
    vinylBypass.setBounds(40, 303, 36, 22);

    // Master row (2 knobs)
    masterMix.setBounds (80  - K/2, 465 - K/2, K, K);
    masterGain.setBounds(160 - K/2, 465 - K/2, K, K);

    // RIGHT COLUMN: Psyche / LFO stacked
    // Psyche — 7 knobs in one row
    int psycheGap = 70;
    int psycheStart = 420;
    psycheShimmer.setBounds(psycheStart               - K/2, 240 - K/2, K, K);
    psycheSpace.setBounds  (psycheStart + psycheGap    - K/2, 240 - K/2, K, K);
    psycheMod.setBounds    (psycheStart + psycheGap*2  - K/2, 240 - K/2, K, K);
    psycheWarp.setBounds   (psycheStart + psycheGap*3  - K/2, 240 - K/2, K, K);
    psycheMix.setBounds    (psycheStart + psycheGap*4  - K/2, 240 - K/2, K, K);
    psycheNotches.setBounds(psycheStart + psycheGap*5  - K/2, 240 - K/2, K, K);
    psycheSweep.setBounds  (psycheStart + psycheGap*6  - K/2, 240 - K/2, K, K);
    psycheBypass.setBounds(385, 188, 36, 22);

    // LFO — row 1 (3 knobs), row 2 (2 knobs + sync)
    lfoShape.setBounds(455 - K/2, 410 - K/2, K, K);
    lfoRate.setBounds (535 - K/2, 410 - K/2, K, K);
    lfoDepth.setBounds(615 - K/2, 410 - K/2, K, K);
    lfoSyncRate.setBounds    (455 - K/2, 485 - K/2, K, K);
    lfoPhaseOffset.setBounds (535 - K/2, 485 - K/2, K, K);
    lfoSync.setBounds(700, 445, 55, 24);
    lfoBypass.setBounds(415, 361, 36, 22);
}

// ================================================================
// Paint — background only (all labels baked into texture)
// ================================================================
void AetherEditor::paint(juce::Graphics& g)
{
    if (backgroundImg.isValid())
        g.drawImage(backgroundImg, getLocalBounds().toFloat());
    else
        g.fillAll(juce::Colour(0xFF3B2F2F));

    // LFO info readout
    int lShape = static_cast<int>(lfoShape.getValue());
    int lSyncR = static_cast<int>(lfoSyncRate.getValue());
    bool synced = lfoSync.getToggleState();
    juce::String info = LFOProcessor::shapeName(lShape);
    if (synced)
        info += juce::String(" | ") + LFOProcessor::syncRateName(lSyncR);

    auto infoBounds = juce::Rectangle<float>(415.0f, 520.0f, 240.0f, 18.0f);
    g.setColour(juce::Colour(0x80000000));
    g.fillRoundedRectangle(infoBounds, 6.0f);
    g.setColour(juce::Colour(0xEEFFFFFF));
    g.setFont(juce::Font(10.0f).boldened());
    g.drawText(info, infoBounds.toNearestInt(), juce::Justification::centred);
}
