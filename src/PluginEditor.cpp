#include "PluginEditor.h"
#include "dsp/LFOProcessor.h"

// === Custom Look & Feel ===
AetherEditor::AetherLookAndFeel::AetherLookAndFeel()
{
    setColour(juce::Slider::rotarySliderFillColourId, juce::Colour(0xFF8B5CF6));
    setColour(juce::Slider::rotarySliderOutlineColourId, juce::Colour(0xFF1E1B2E));
    setColour(juce::Slider::thumbColourId, juce::Colour(0xFFC084FC));
    setColour(juce::Label::textColourId, juce::Colour(0xFFE2D9F3));
}

void AetherEditor::AetherLookAndFeel::drawRotarySlider(
    juce::Graphics& g, int x, int y, int width, int height,
    float sliderPos, float rotaryStartAngle, float rotaryEndAngle, juce::Slider& slider)
{
    auto radius = (float)juce::jmin(width / 2, height / 2) - 6.0f;
    auto centreX = (float)x + (float)width * 0.5f;
    auto centreY = (float)y + (float)height * 0.5f;
    auto angle = rotaryStartAngle + sliderPos * (rotaryEndAngle - rotaryStartAngle);

    // Outer ring glow
    juce::ColourGradient glow(juce::Colour(0x308B5CF6), centreX, centreY,
                               juce::Colour(0x00000000), centreX + radius + 8, centreY, true);
    g.setGradientFill(glow);
    g.fillEllipse(centreX - radius - 4, centreY - radius - 4,
                  (radius + 4) * 2, (radius + 4) * 2);

    // Background circle
    g.setColour(juce::Colour(0xFF0D0B14));
    g.fillEllipse(centreX - radius, centreY - radius, radius * 2, radius * 2);

    // Track (dark)
    juce::Path bgArc;
    bgArc.addCentredArc(centreX, centreY, radius - 2, radius - 2,
                         0.0f, rotaryStartAngle, rotaryEndAngle, true);
    g.setColour(juce::Colour(0xFF2D2640));
    g.strokePath(bgArc, juce::PathStrokeType(3.0f, juce::PathStrokeType::curved,
                                               juce::PathStrokeType::rounded));

    // Active arc (gradient purple > cyan)
    juce::Path valueArc;
    valueArc.addCentredArc(centreX, centreY, radius - 2, radius - 2,
                            0.0f, rotaryStartAngle, angle, true);
    juce::ColourGradient arcGrad(juce::Colour(0xFF8B5CF6), centreX - radius, centreY,
                                  juce::Colour(0xFF06B6D4), centreX + radius, centreY, false);
    g.setGradientFill(arcGrad);
    g.strokePath(valueArc, juce::PathStrokeType(3.0f, juce::PathStrokeType::curved,
                                                  juce::PathStrokeType::rounded));

    // Pointer dot
    auto pointerLength = radius - 8.0f;
    auto pointerX = centreX + pointerLength * std::cos(angle - juce::MathConstants<float>::halfPi);
    auto pointerY = centreY + pointerLength * std::sin(angle - juce::MathConstants<float>::halfPi);
    g.setColour(juce::Colour(0xFFC084FC));
    g.fillEllipse(pointerX - 4, pointerY - 4, 8, 8);
    g.setColour(juce::Colour(0x40FFFFFF));
    g.fillEllipse(pointerX - 2, pointerY - 2, 4, 4);
}

void AetherEditor::AetherLookAndFeel::drawToggleButton(
    juce::Graphics& g, juce::ToggleButton& button,
    bool, bool)
{
    auto bounds = button.getLocalBounds().toFloat().reduced(4);
    auto isOn = button.getToggleState();

    // Sync toggle gets a distinct look (cyan/gray) vs bypass (red/green)
    bool isSyncButton = (button.getButtonText() == "SYNC");

    if (isSyncButton)
    {
        g.setColour(isOn ? juce::Colour(0xFF06B6D4) : juce::Colour(0xFF2D2640));
        g.fillRoundedRectangle(bounds, 4.0f);
        g.setColour(juce::Colours::white);
        g.setFont(10.0f);
        g.drawText(isOn ? "SYNC" : "FREE", bounds, juce::Justification::centred);
    }
    else
    {
        g.setColour(isOn ? juce::Colour(0xFFEF4444) : juce::Colour(0xFF22C55E));
        g.fillRoundedRectangle(bounds, 4.0f);
        g.setColour(juce::Colours::white);
        g.setFont(11.0f);
        g.drawText(isOn ? "OFF" : "ON", bounds, juce::Justification::centred);
    }
}

// === Editor ===
AetherEditor::AetherEditor(AetherProcessor& p)
    : AudioProcessorEditor(&p), processorRef(p)
{
    setLookAndFeel(&aetherLnf);
    
    // Swell
    setupKnob(swellSens, "swellSens", "SENSE");
    setupKnob(swellAttack, "swellAttack", "ATTACK");
    setupKnob(swellDepth, "swellDepth", "DEPTH");
    setupBypass(swellBypass, "swellBypass", "SWELL");
    
    // Vinyl (6 knobs)
    setupKnob(vinylYear, "vinylYear", "YEAR");
    setupKnob(vinylWarp, "vinylWarp", "WARP");
    setupKnob(vinylDust, "vinylDust", "DUST");
    setupKnob(vinylWear, "vinylWear", "WEAR");
    setupKnob(vinylDetune, "vinylDetune", "DETUNE");
    setupKnob(vinylNoise, "vinylNoise", "NOISE");
    setupBypass(vinylBypassBtn, "vinylBypass", "VINYL");
    
    // Psyche (7 knobs)
    setupKnob(psycheShimmer, "psycheShimmer", "SHIMMER");
    setupKnob(psycheSpace, "psycheSpace", "SPACE");
    setupKnob(psycheMod, "psycheMod", "MOD");
    setupKnob(psycheWarp, "psycheWarp", "WARP");
    setupKnob(psycheMix, "psycheMix", "MIX");
    setupKnob(psycheNotches, "psycheNotches", "NOTCHES");
    setupKnob(psycheSweep, "psycheSweep", "SWEEP");
    setupBypass(psycheBypassBtn, "psycheBypass", "PSYCHE");
    
    // LFO (5 knobs + sync toggle)
    setupKnob(lfoShape, "lfoShape", "SHAPE");
    setupKnob(lfoRate, "lfoRate", "RATE");
    setupKnob(lfoDepth, "lfoDepth", "DEPTH");
    setupKnob(lfoSyncRate, "lfoSyncRate", "DIV");
    setupKnob(lfoPhaseOffset, "lfoPhaseOffset", "PHASE");
    setupBypass(lfoBypassBtn, "lfoBypass", "LFO");
    setupBypass(lfoSyncBtn, "lfoSync", "SYNC");
    
    // Master
    setupKnob(masterMix, "masterMix", "DRY/WET");
    setupKnob(masterGain, "masterGain", "GAIN");

    setSize(960, 500);
    startTimerHz(30);
}

AetherEditor::~AetherEditor()
{
    setLookAndFeel(nullptr);
}

void AetherEditor::setupKnob(KnobAttachment& knob, const juce::String& paramId, const juce::String& name)
{
    knob.slider.setSliderStyle(juce::Slider::RotaryHorizontalVerticalDrag);
    knob.slider.setTextBoxStyle(juce::Slider::NoTextBox, false, 0, 0);
    addAndMakeVisible(knob.slider);
    knob.attachment = std::make_unique<juce::AudioProcessorValueTreeState::SliderAttachment>(
        processorRef.apvts, paramId, knob.slider);
    
    knob.label.setText(name, juce::dontSendNotification);
    knob.label.setJustificationType(juce::Justification::centred);
    knob.label.setFont(juce::Font(10.0f));
    addAndMakeVisible(knob.label);
}

void AetherEditor::setupBypass(BypassAttachment& bp, const juce::String& paramId, const juce::String& name)
{
    bp.button.setButtonText(name);
    addAndMakeVisible(bp.button);
    bp.attachment = std::make_unique<juce::AudioProcessorValueTreeState::ButtonAttachment>(
        processorRef.apvts, paramId, bp.button);
}

void AetherEditor::timerCallback()
{
    animPhase += 0.015f;
    if (animPhase > juce::MathConstants<float>::twoPi)
        animPhase -= juce::MathConstants<float>::twoPi;
    repaint();
}

void AetherEditor::paint(juce::Graphics& g)
{
    // === Background: deep space gradient with animated nebula ===
    juce::ColourGradient bg(juce::Colour(0xFF0A0612), 0, 0,
                             juce::Colour(0xFF1A0B2E), getWidth(), getHeight(), false);
    bg.addColour(0.5, juce::Colour(0xFF0F0720));
    g.setGradientFill(bg);
    g.fillAll();

    // Animated nebula glow
    float glowX = getWidth() * 0.4f + std::sin(animPhase) * 60.0f;
    float glowY = getHeight() * 0.3f + std::cos(animPhase * 0.7f) * 30.0f;
    juce::ColourGradient nebula(juce::Colour(0x158B5CF6), glowX, glowY,
                                 juce::Colour(0x00000000), glowX + 200, glowY + 200, true);
    g.setGradientFill(nebula);
    g.fillEllipse(glowX - 150, glowY - 150, 300, 300);

    float glow2X = getWidth() * 0.7f + std::cos(animPhase * 1.3f) * 40.0f;
    float glow2Y = getHeight() * 0.5f + std::sin(animPhase * 0.5f) * 50.0f;
    juce::ColourGradient nebula2(juce::Colour(0x1006B6D4), glow2X, glow2Y,
                                  juce::Colour(0x00000000), glow2X + 180, glow2Y + 180, true);
    g.setGradientFill(nebula2);
    g.fillEllipse(glow2X - 130, glow2Y - 130, 260, 260);

    // === Title ===
    g.setColour(juce::Colour(0xFFE2D9F3));
    g.setFont(juce::Font(28.0f).boldened());
    g.drawText("AETHER", getLocalBounds().removeFromTop(45), juce::Justification::centred);
    g.setFont(juce::Font(9.0f));
    g.setColour(juce::Colour(0xFF8B7FAA));
    g.drawText("PSYCHEDELIC GUITAR PROCESSOR", 0, 33, getWidth(), 14, juce::Justification::centred);

    // === Section backgrounds ===
    auto drawSection = [&](juce::Rectangle<float> bounds, const juce::String& title, juce::Colour accent)
    {
        g.setColour(juce::Colour(0x15FFFFFF));
        g.fillRoundedRectangle(bounds, 8.0f);
        g.setColour(accent.withAlpha(0.3f));
        g.drawRoundedRectangle(bounds, 8.0f, 1.0f);
        g.setColour(accent);
        g.setFont(juce::Font(12.0f).boldened());
        g.drawText(title, bounds.removeFromTop(22), juce::Justification::centred);
    };

    float sectTop = 52.0f;
    float sectH = 310.0f;
    drawSection(juce::Rectangle<float>(8, sectTop, 118, sectH), "SWELL", juce::Colour(0xFF22C55E));
    drawSection(juce::Rectangle<float>(134, sectTop, 222, sectH), "VINYL", juce::Colour(0xFFF59E0B));
    drawSection(juce::Rectangle<float>(364, sectTop, 270, sectH), "PSYCHE", juce::Colour(0xFF8B5CF6));
    drawSection(juce::Rectangle<float>(642, sectTop, 310, sectH), "LFO", juce::Colour(0xFFEC4899));

    // LFO shape name display
    if (auto* param = processorRef.apvts.getRawParameterValue("lfoShape"))
    {
        int shapeIdx = static_cast<int>(param->load());
        g.setColour(juce::Colour(0xFFEC4899));
        g.setFont(juce::Font(14.0f).boldened());
        g.drawText(LFOProcessor::shapeName(shapeIdx),
                   juce::Rectangle<float>(642, sectTop + 240, 310, 22),
                   juce::Justification::centred);
    }

    // LFO sync rate name (when sync is enabled)
    if (auto* syncParam = processorRef.apvts.getRawParameterValue("lfoSync"))
    {
        bool syncOn = syncParam->load() > 0.5f;
        if (syncOn)
        {
            if (auto* rateParam = processorRef.apvts.getRawParameterValue("lfoSyncRate"))
            {
                int rateIdx = static_cast<int>(rateParam->load());
                g.setColour(juce::Colour(0xFF06B6D4));
                g.setFont(juce::Font(13.0f).boldened());
                g.drawText(LFOProcessor::syncRateName(rateIdx),
                           juce::Rectangle<float>(642, sectTop + 262, 310, 20),
                           juce::Justification::centred);
            }
        }
        else
        {
            // Show Hz rate when in free mode
            if (auto* hzParam = processorRef.apvts.getRawParameterValue("lfoRate"))
            {
                float hz = hzParam->load();
                g.setColour(juce::Colour(0xFF8B7FAA));
                g.setFont(juce::Font(11.0f));
                juce::String rateStr = juce::String(hz, 1) + " Hz";
                g.drawText(rateStr,
                           juce::Rectangle<float>(642, sectTop + 262, 310, 20),
                           juce::Justification::centred);
            }
        }
    }

    // Master strip
    drawSection(juce::Rectangle<float>(8, 370, 944, 65), "MASTER", juce::Colour(0xFF06B6D4));

    // Credits
    g.setColour(juce::Colour(0xFF4A3F6B));
    g.setFont(juce::Font(8.0f));
    g.drawText("v3.0 // artemis", 0, getHeight() - 14, getWidth(), 12, juce::Justification::centredRight);
}

void AetherEditor::resized()
{
    int knob = 55;
    int lblH = 14;
    int gap = 8;
    int row1Y = 78;     // first row of knobs in each section
    int rowH = knob + lblH + gap;  // height per knob row
    int row2Y = row1Y + rowH;
    int row3Y = row2Y + rowH;

    auto placeKnob = [&](KnobAttachment& k, int x, int y)
    {
        k.slider.setBounds(x, y, knob, knob);
        k.label.setBounds(x - 4, y + knob, knob + 8, lblH);
    };

    auto placeBypass = [&](BypassAttachment& bp, int x, int y, int w = 38)
    {
        bp.button.setBounds(x, y, w, 18);
    };

    // ---- SWELL (3 knobs vertical, x=8..126) ----
    int sx = 35;
    placeKnob(swellSens, sx, row1Y);
    placeKnob(swellAttack, sx, row2Y);
    placeKnob(swellDepth, sx, row3Y);
    placeBypass(swellBypass, sx + knob + 4, row1Y);

    // ---- VINYL (6 knobs: 3 top + 3 bottom, x=134..356) ----
    int vx = 145;
    int vGap = knob + gap;
    placeKnob(vinylYear, vx, row1Y);
    placeKnob(vinylWarp, vx + vGap, row1Y);
    placeKnob(vinylDetune, vx + vGap * 2, row1Y);
    placeKnob(vinylDust, vx, row2Y);
    placeKnob(vinylWear, vx + vGap, row2Y);
    placeKnob(vinylNoise, vx + vGap * 2, row2Y);
    placeBypass(vinylBypassBtn, vx + vGap * 2 + knob - 30, row1Y - 20);

    // ---- PSYCHE (7 knobs: 4 top + 3 bottom, x=364..634) ----
    int px = 375;
    int pGap = knob + gap;
    placeKnob(psycheNotches, px, row1Y);
    placeKnob(psycheShimmer, px + pGap, row1Y);
    placeKnob(psycheSpace, px + pGap * 2, row1Y);
    placeKnob(psycheMod, px + pGap * 3, row1Y);
    placeKnob(psycheSweep, px, row2Y);
    placeKnob(psycheWarp, px + pGap, row2Y);
    placeKnob(psycheMix, px + pGap * 2, row2Y);
    placeBypass(psycheBypassBtn, px + pGap * 3 + knob - 30, row1Y - 20);

    // ---- LFO (5 knobs: 3 top + 2 bottom, x=642..952) ----
    int lx = 700;
    int lGap = knob + gap + 10;

    // Row 1: Shape, Rate, Depth
    placeKnob(lfoShape, lx, row1Y);
    placeKnob(lfoRate, lx + lGap, row1Y);
    placeKnob(lfoDepth, lx + lGap * 2, row1Y);

    // Row 2: Sync Division, Phase Offset
    placeKnob(lfoSyncRate, lx, row2Y);
    placeKnob(lfoPhaseOffset, lx + lGap, row2Y);

    // Toggles: Sync (left), Bypass (right)
    placeBypass(lfoSyncBtn, lx + lGap * 2 - 8, row1Y - 20, 48);
    placeBypass(lfoBypassBtn, lx + lGap * 2 + 44, row1Y - 20);

    // ---- MASTER (horizontal, bottom strip) ----
    int my = 381;
    placeKnob(masterMix, 420, my);
    placeKnob(masterGain, 500, my);
}
