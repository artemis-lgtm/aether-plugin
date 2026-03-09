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
        // Bypass: red when off (bypassed), green when on (active)
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
        // Sync toggle
        g.setColour(on ? juce::Colour(0xBB00CEC9) : juce::Colour(0xBB888888));
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
    backgroundImg = juce::ImageFileFormat::loadFrom(
        BinaryData::background_png, BinaryData::background_pngSize);

    juce::Image knobImg = juce::ImageFileFormat::loadFrom(
        BinaryData::knobstrip_png, BinaryData::knobstrip_pngSize);

    filmstripLnf.setKnobStrip(knobImg, 128);
    setLookAndFeel(&filmstripLnf);
    setSize(1020, 620);

    auto setupKnob = [&](juce::Slider& s) {
        s.setSliderStyle(juce::Slider::RotaryHorizontalVerticalDrag);
        s.setTextBoxStyle(juce::Slider::NoTextBox, false, 0, 0);
        addAndMakeVisible(s);
    };

    setupKnob(swellSens); setupKnob(swellAttack); setupKnob(swellDepth);
    setupKnob(vinylYear); setupKnob(vinylDetune);
    setupKnob(psycheShimmer); setupKnob(psycheSpace); setupKnob(psycheMod);
    setupKnob(psycheWarp); setupKnob(psycheMix); setupKnob(psycheNotches); setupKnob(psycheSweep);
    setupKnob(lfoShape); setupKnob(lfoRate); setupKnob(lfoDepth);
    setupKnob(lfoSyncRate); setupKnob(lfoPhaseOffset);
    setupKnob(masterMix); setupKnob(masterGain);

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

    startTimerHz(24);
}

AetherEditor::~AetherEditor()
{
    setLookAndFeel(nullptr);
}

void AetherEditor::timerCallback()
{
    animTime += 1.0f / 24.0f;
    repaint(0, 0, getWidth(), 90); // Only repaint title area
}

// ================================================================
// Layout — knobs positioned directly on the pedal surface
// ================================================================
void AetherEditor::resized()
{
    int K = 62; // knob size
    int gap = 68; // horizontal gap

    int row1_y = 140;
    int row2_y = 250;
    int master_y = 380;

    int swell_x = 30;
    int vinyl_x = 240;
    int psyche_x = 420;
    int lfo_x = 730;

    // Swell
    swellSens.setBounds(swell_x, row1_y, K, K);
    swellAttack.setBounds(swell_x + gap, row1_y, K, K);
    swellDepth.setBounds(swell_x + gap * 2, row1_y, K, K);
    swellBypass.setBounds(swell_x - 5, row1_y - 30, 36, 22);

    // Vinyl
    vinylYear.setBounds(vinyl_x, row1_y, K, K);
    vinylDetune.setBounds(vinyl_x + gap, row1_y, K, K);
    vinylBypass.setBounds(vinyl_x - 5, row1_y - 30, 36, 22);

    // Psyche row 1
    psycheShimmer.setBounds(psyche_x, row1_y, K, K);
    psycheSpace.setBounds(psyche_x + gap, row1_y, K, K);
    psycheMod.setBounds(psyche_x + gap * 2, row1_y, K, K);
    psycheWarp.setBounds(psyche_x + gap * 3, row1_y, K, K);
    // Psyche row 2
    psycheMix.setBounds(psyche_x, row2_y, K, K);
    psycheNotches.setBounds(psyche_x + gap, row2_y, K, K);
    psycheSweep.setBounds(psyche_x + gap * 2, row2_y, K, K);
    psycheBypass.setBounds(psyche_x - 5, row1_y - 30, 36, 22);

    // LFO row 1
    lfoShape.setBounds(lfo_x, row1_y, K, K);
    lfoRate.setBounds(lfo_x + gap, row1_y, K, K);
    lfoDepth.setBounds(lfo_x + gap * 2, row1_y, K, K);
    // LFO row 2
    lfoSyncRate.setBounds(lfo_x, row2_y, K, K);
    lfoPhaseOffset.setBounds(lfo_x + gap, row2_y, K, K);
    lfoSync.setBounds(lfo_x + gap * 2, row2_y + 14, 52, 26);
    lfoBypass.setBounds(lfo_x - 5, row1_y - 30, 36, 22);

    // Master
    int W = getWidth();
    masterMix.setBounds(W / 2 - gap / 2 - K / 2, master_y, K, K);
    masterGain.setBounds(W / 2 + gap / 2 - K / 2, master_y, K, K);
}

// ================================================================
// Paint
// ================================================================
void AetherEditor::paint(juce::Graphics& g)
{
    // Full background image (doodle art + labels + mounting holes baked in)
    if (backgroundImg.isValid())
        g.drawImage(backgroundImg, getLocalBounds().toFloat());
    else
        g.fillAll(juce::Colour(0xFF5DADE2));

    // Animated title
    drawTitle(g);

    // LFO info readout
    int lShape = static_cast<int>(lfoShape.getValue());
    int lSyncR = static_cast<int>(lfoSyncRate.getValue());
    bool synced = lfoSync.getToggleState();
    juce::String info = LFOProcessor::shapeName(lShape);
    if (synced)
        info += juce::String(" | ") + LFOProcessor::syncRateName(lSyncR);
    g.setColour(juce::Colour(0xBBFFFFFF));
    g.setFont(juce::Font(10.0f));
    g.drawText(info, 730, 330, 204, 16, juce::Justification::centred);
}

// ================================================================
// Title — rainbow bouncing AETHER
// ================================================================
void AetherEditor::drawTitle(juce::Graphics& g)
{
    juce::String title = "AETHER";
    auto font = juce::Font(46.0f).boldened();
    g.setFont(font);

    float titleW = font.getStringWidthFloat(title);
    float startX = ((float)getWidth() - titleW) * 0.5f;
    float baseY = 30.0f;

    juce::Colour rainbow[] = {
        juce::Colour(0xFFFF6B6B), juce::Colour(0xFFFF8C42), juce::Colour(0xFFFFE066),
        juce::Colour(0xFF6BCB77), juce::Colour(0xFF00CEC9), juce::Colour(0xFFBB6BD9)
    };

    for (int i = 0; i < title.length(); ++i)
    {
        juce::String ch = title.substring(i, i + 1);
        float cw = font.getStringWidthFloat(ch);
        float bounce = std::sin(animTime * 2.5f + i * 0.8f) * 5.0f;
        float y = baseY + bounce;

        // Black outline for readability on busy background
        g.setColour(juce::Colour(0xCC000000));
        for (int dx = -2; dx <= 2; dx++)
            for (int dy = -2; dy <= 2; dy++)
                if (dx != 0 || dy != 0)
                    g.drawText(ch, (int)(startX + dx), (int)(y + dy), (int)cw + 2, 55,
                               juce::Justification::left);

        // Rainbow fill
        g.setColour(rainbow[i % 6]);
        g.drawText(ch, (int)startX, (int)y, (int)cw + 2, 55,
                   juce::Justification::left);

        startX += cw;
    }
}
