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
    backgroundImg = juce::ImageFileFormat::loadFrom(
        BinaryData::background_png, BinaryData::background_pngSize);

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

    startTimerHz(30); // 30fps for smooth neon animation
}

AetherEditor::~AetherEditor()
{
    for (auto* s : { &swellSens, &swellAttack, &swellDepth,
                     &vinylYear, &vinylDetune,
                     &psycheShimmer, &psycheSpace, &psycheMod, &psycheWarp,
                     &psycheMix, &psycheNotches, &psycheSweep,
                     &lfoShape, &lfoRate, &lfoDepth, &lfoSyncRate, &lfoPhaseOffset,
                     &masterMix, &masterGain })
        s->setLookAndFeel(nullptr);
}

// ================================================================
// Timer — drives neon flicker animation
// ================================================================
void AetherEditor::timerCallback()
{
    neonTime += 1.0f / 30.0f;

    // Slow breathing: 0.7 - 1.0 over ~3 second cycle
    neonBreath = 0.85f + 0.15f * std::sin(neonTime * 2.1f);

    // Random flicker events (like a real neon tube)
    flickerCountdown--;
    if (flickerCountdown <= 0)
    {
        std::uniform_int_distribution<int> nextFlicker(15, 90); // 0.5 - 3 seconds between events
        flickerCountdown = nextFlicker(rng);

        std::uniform_real_distribution<float> flickerType(0.0f, 1.0f);
        float r = flickerType(rng);
        if (r < 0.15f)
            neonFlicker = 0.3f;  // hard stutter (rare)
        else if (r < 0.35f)
            neonFlicker = 0.6f;  // soft dip
        else
            neonFlicker = 1.0f;  // normal
    }
    else if (neonFlicker < 1.0f)
    {
        // Recover from flicker over a few frames
        neonFlicker = juce::jmin(1.0f, neonFlicker + 0.15f);
    }

    // Only repaint the neon areas (title top + portrait bottom-right)
    repaint(0, 0, getWidth(), 65);                  // title region
    repaint(getWidth() - 230, getHeight() - 220, 230, 220); // portrait region
}

// ================================================================
// Neon glow overlay — draws animated glow rectangles
// ================================================================
void AetherEditor::drawNeonGlow(juce::Graphics& g, juce::Rectangle<float> bounds,
                                 juce::Colour color, float intensity)
{
    float alpha = intensity * neonBreath * neonFlicker;
    alpha = juce::jlimit(0.0f, 1.0f, alpha);

    // Outer soft glow (large, faint)
    for (int i = 3; i >= 1; i--)
    {
        float expand = (float)i * 6.0f;
        float a = alpha * 0.12f * (float)(4 - i);
        g.setColour(color.withAlpha(a));
        g.drawRoundedRectangle(bounds.expanded(expand), 4.0f, 3.0f);
    }

    // Inner bright glow
    g.setColour(color.withAlpha(alpha * 0.5f));
    g.drawRoundedRectangle(bounds.expanded(2.0f), 3.0f, 2.5f);

    // Core neon line
    g.setColour(color.withAlpha(alpha * 0.8f));
    g.drawRoundedRectangle(bounds, 2.0f, 2.0f);

    // Hot white center (the brightest part of a neon tube)
    juce::Colour hotCenter = color.interpolatedWith(juce::Colours::white, 0.5f);
    g.setColour(hotCenter.withAlpha(alpha * 0.3f));
    g.drawRoundedRectangle(bounds.reduced(1.0f), 2.0f, 1.0f);
}

// ================================================================
// Layout
// ================================================================
void AetherEditor::resized()
{
    int K = 56;

    // LEFT COLUMN
    swellSens.setBounds  (80  - K/2, 240 - K/2, K, K);
    swellAttack.setBounds(160 - K/2, 240 - K/2, K, K);
    swellDepth.setBounds (240 - K/2, 240 - K/2, K, K);
    swellBypass.setBounds(40, 188, 36, 22);

    vinylYear.setBounds  (80  - K/2, 355 - K/2, K, K);
    vinylDetune.setBounds(160 - K/2, 355 - K/2, K, K);
    vinylBypass.setBounds(40, 303, 36, 22);

    masterMix.setBounds (80  - K/2, 465 - K/2, K, K);
    masterGain.setBounds(160 - K/2, 465 - K/2, K, K);

    // RIGHT COLUMN
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

    lfoShape.setBounds(455 - K/2, 410 - K/2, K, K);
    lfoRate.setBounds (535 - K/2, 410 - K/2, K, K);
    lfoDepth.setBounds(615 - K/2, 410 - K/2, K, K);
    lfoSyncRate.setBounds    (455 - K/2, 485 - K/2, K, K);
    lfoPhaseOffset.setBounds (535 - K/2, 485 - K/2, K, K);
    lfoSync.setBounds(700, 445, 55, 24);
    lfoBypass.setBounds(415, 361, 36, 22);
}

// ================================================================
// Paint
// ================================================================
void AetherEditor::paint(juce::Graphics& g)
{
    // Static background (wood desk + pedal with baked labels)
    if (backgroundImg.isValid())
        g.drawImage(backgroundImg, getLocalBounds().toFloat());
    else
        g.fillAll(juce::Colour(0xFF3B2F2F));

    // ---- Animated neon glow overlays ----
    juce::Colour neonRed(0xFFFF2828);

    // Title box "Austin's Secret Sauce" — approximate baked position
    // (centered, near top of pedal face)
    {
        float titleW = 350.0f;
        float titleH = 50.0f;
        float titleX = (float)getWidth() * 0.5f - titleW * 0.5f;
        float titleY = 8.0f;
        drawNeonGlow(g, { titleX, titleY, titleW, titleH }, neonRed, 0.9f);
    }

    // Portrait frame — bottom right of pedal face
    {
        float pw = 175.0f, ph = 175.0f;
        float px = (float)getWidth() - pw - 35.0f;
        float py = (float)getHeight() - ph - 40.0f;
        drawNeonGlow(g, { px, py, pw, ph }, neonRed, 0.75f);
    }

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
