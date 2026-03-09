#include "PluginEditor.h"

// === Custom Look & Feel ===
AetherEditor::AetherLookAndFeel::AetherLookAndFeel()
{
    // Dark psychedelic theme
    setColour(juce::Slider::rotarySliderFillColourId, juce::Colour(0xFF8B5CF6));     // Purple
    setColour(juce::Slider::rotarySliderOutlineColourId, juce::Colour(0xFF1E1B2E));  // Dark
    setColour(juce::Slider::thumbColourId, juce::Colour(0xFFC084FC));                // Light purple
    setColour(juce::Label::textColourId, juce::Colour(0xFFE2D9F3));                  // Soft lavender
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

    // Active arc (gradient purple → cyan)
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
    
    // Inner glow on pointer
    g.setColour(juce::Colour(0x40FFFFFF));
    g.fillEllipse(pointerX - 2, pointerY - 2, 4, 4);
}

void AetherEditor::AetherLookAndFeel::drawToggleButton(
    juce::Graphics& g, juce::ToggleButton& button,
    bool /*shouldDrawButtonAsHighlighted*/, bool /*shouldDrawButtonAsDown*/)
{
    auto bounds = button.getLocalBounds().toFloat().reduced(4);
    auto isOn = button.getToggleState();
    
    // Bypass button: red when bypassed, subtle green when active
    g.setColour(isOn ? juce::Colour(0xFFEF4444) : juce::Colour(0xFF22C55E));
    g.fillRoundedRectangle(bounds, 4.0f);
    
    g.setColour(juce::Colours::white);
    g.setFont(11.0f);
    g.drawText(isOn ? "OFF" : "ON", bounds, juce::Justification::centred);
}

// === Editor ===
AetherEditor::AetherEditor(AetherProcessor& p)
    : AudioProcessorEditor(&p), processorRef(p)
{
    setLookAndFeel(&aetherLnf);
    
    // Setup all knobs
    setupKnob(swellSens, "swellSens", "SENSE");
    setupKnob(swellAttack, "swellAttack", "ATTACK");
    setupKnob(swellDepth, "swellDepth", "DEPTH");
    setupBypass(swellBypass, "swellBypass", "SWELL");
    
    setupKnob(vinylYear, "vinylYear", "YEAR");
    setupKnob(vinylWarp, "vinylWarp", "WARP");
    setupKnob(vinylDust, "vinylDust", "DUST");
    setupKnob(vinylWear, "vinylWear", "WEAR");
    setupKnob(vinylDetune, "vinylDetune", "DETUNE");
    setupBypass(vinylBypassBtn, "vinylBypass", "VINYL");
    
    setupKnob(psycheShimmer, "psycheShimmer", "SHIMMER");
    setupKnob(psycheSpace, "psycheSpace", "SPACE");
    setupKnob(psycheMod, "psycheMod", "MOD");
    setupKnob(psycheWarp, "psycheWarp", "WARP");
    setupKnob(psycheMix, "psycheMix", "MIX");
    setupBypass(psycheBypassBtn, "psycheBypass", "PSYCHE");
    
    setupKnob(masterMix, "masterMix", "DRY/WET");
    setupKnob(masterGain, "masterGain", "GAIN");

    setSize(840, 480);
    startTimerHz(30);  // Animation refresh
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
    knob.label.setFont(juce::Font(11.0f));
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

    // Animated nebula glow (subtle)
    float glowX = getWidth() * 0.5f + std::sin(animPhase) * 60.0f;
    float glowY = getHeight() * 0.3f + std::cos(animPhase * 0.7f) * 30.0f;
    juce::ColourGradient nebula(juce::Colour(0x158B5CF6), glowX, glowY,
                                 juce::Colour(0x00000000), glowX + 200, glowY + 200, true);
    g.setGradientFill(nebula);
    g.fillEllipse(glowX - 150, glowY - 150, 300, 300);

    float glow2X = getWidth() * 0.7f + std::cos(animPhase * 1.3f) * 40.0f;
    float glow2Y = getHeight() * 0.6f + std::sin(animPhase * 0.5f) * 50.0f;
    juce::ColourGradient nebula2(juce::Colour(0x1006B6D4), glow2X, glow2Y,
                                  juce::Colour(0x00000000), glow2X + 180, glow2Y + 180, true);
    g.setGradientFill(nebula2);
    g.fillEllipse(glow2X - 130, glow2Y - 130, 260, 260);

    // === Title ===
    g.setColour(juce::Colour(0xFFE2D9F3));
    g.setFont(juce::Font(32.0f).boldened());
    g.drawText("AETHER", getLocalBounds().removeFromTop(50), juce::Justification::centred);
    
    g.setFont(juce::Font(10.0f));
    g.setColour(juce::Colour(0xFF8B7FAA));
    g.drawText("PSYCHEDELIC GUITAR PROCESSOR", 0, 38, getWidth(), 16, juce::Justification::centred);

    // === Section dividers ===
    auto drawSectionBg = [&](juce::Rectangle<float> bounds, const juce::String& title, juce::Colour accent)
    {
        g.setColour(juce::Colour(0x15FFFFFF));
        g.fillRoundedRectangle(bounds, 8.0f);
        g.setColour(accent.withAlpha(0.3f));
        g.drawRoundedRectangle(bounds, 8.0f, 1.0f);
        
        g.setColour(accent);
        g.setFont(juce::Font(13.0f).boldened());
        g.drawText(title, bounds.removeFromTop(24), juce::Justification::centred);
    };

    // Section backgrounds
    drawSectionBg(juce::Rectangle<float>(10, 60, 190, 330), "SWELL", juce::Colour(0xFF22C55E));
    drawSectionBg(juce::Rectangle<float>(210, 60, 290, 330), "VINYL", juce::Colour(0xFFF59E0B));
    drawSectionBg(juce::Rectangle<float>(510, 60, 320, 330), "PSYCHE", juce::Colour(0xFF8B5CF6));

    // Master section
    drawSectionBg(juce::Rectangle<float>(10, 400, 820, 70), "MASTER", juce::Colour(0xFF06B6D4));
}

void AetherEditor::resized()
{
    int knobSize = 65;
    int labelH = 16;
    int sectionTop = 88;
    int knobSpacing = 70;

    auto placeKnob = [&](KnobAttachment& knob, int x, int y)
    {
        knob.slider.setBounds(x, y, knobSize, knobSize);
        knob.label.setBounds(x - 5, y + knobSize, knobSize + 10, labelH);
    };

    auto placeBypass = [&](BypassAttachment& bp, int x, int y)
    {
        bp.button.setBounds(x, y, 40, 20);
    };

    // Swell: 3 knobs + bypass
    int sx = 30;
    placeKnob(swellSens, sx, sectionTop);
    placeKnob(swellAttack, sx, sectionTop + knobSize + labelH + 10);
    placeKnob(swellDepth, sx, sectionTop + (knobSize + labelH + 10) * 2);
    placeBypass(swellBypass, sx + knobSize + 10, sectionTop);

    // Vinyl: 5 knobs (3 top, 2 bottom) + bypass
    int vx = 225;
    placeKnob(vinylYear, vx, sectionTop);
    placeKnob(vinylWarp, vx + knobSpacing + 10, sectionTop);
    placeKnob(vinylDetune, vx + (knobSpacing + 10) * 2, sectionTop);
    placeKnob(vinylDust, vx + 20, sectionTop + knobSize + labelH + 10);
    placeKnob(vinylWear, vx + 20 + knobSpacing + 10, sectionTop + knobSize + labelH + 10);
    placeBypass(vinylBypassBtn, vx + 210, sectionTop);

    // Psyche: 5 knobs (3+2 grid) + bypass
    int px = 525;
    placeKnob(psycheShimmer, px, sectionTop);
    placeKnob(psycheSpace, px + knobSpacing + 10, sectionTop);
    placeKnob(psycheMod, px + (knobSpacing + 10) * 2, sectionTop);
    placeKnob(psycheWarp, px + 20, sectionTop + knobSize + labelH + 10);
    placeKnob(psycheMix, px + 20 + knobSpacing + 10, sectionTop + knobSize + labelH + 10);
    placeBypass(psycheBypassBtn, px + 240, sectionTop);

    // Master: horizontal, centered
    int my = 418;
    placeKnob(masterMix, 350, my - 15);
    placeKnob(masterGain, 430, my - 15);
}
