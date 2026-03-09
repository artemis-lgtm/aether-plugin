#include "PluginEditor.h"
#include "dsp/LFOProcessor.h"
#include <cmath>

// ================================================================
// Colour palette (bright, crayon-like)
// ================================================================
namespace Crayon
{
    const auto Cream       = juce::Colour(0xFFFFF8E7);
    const auto PinkBg      = juce::Colour(0xFFFFD6E0);
    const auto BlueBg      = juce::Colour(0xFFD0E8FF);
    const auto PurpleBg    = juce::Colour(0xFFE8D0FF);
    const auto GreenBg     = juce::Colour(0xFFD0FFDA);
    const auto YellowBg    = juce::Colour(0xFFFFF3B0);
    const auto Outline      = juce::Colour(0xFF2D1B4E);
    const auto Pink         = juce::Colour(0xFFFF69B4);
    const auto Purple       = juce::Colour(0xFF9B59B6);
    const auto Blue         = juce::Colour(0xFF3498DB);
    const auto Green        = juce::Colour(0xFF2ECC71);
    const auto Orange       = juce::Colour(0xFFFF8C42);
    const auto Yellow       = juce::Colour(0xFFFFD700);
    const auto Red          = juce::Colour(0xFFFF6B6B);
    const auto Teal         = juce::Colour(0xFF00CEC9);
    const auto White        = juce::Colour(0xFFFFFFFF);
    const auto DarkText     = juce::Colour(0xFF2D1B4E);
    const auto MushroomCap  = juce::Colour(0xFFFF4444);
    const auto MushroomDots = juce::Colour(0xFFFFFFCC);
    const auto GhostBody    = juce::Colour(0xCCE8E0FF);
    const auto CrystalBody  = juce::Colour(0xAA88DDFF);
    const auto FlowerCenter = juce::Colour(0xFFFFDD44);
}

// ================================================================
// Look and Feel
// ================================================================
AetherEditor::CrayonLookAndFeel::CrayonLookAndFeel()
{
    setColour(juce::Slider::rotarySliderFillColourId, Crayon::Purple);
    setColour(juce::Slider::rotarySliderOutlineColourId, Crayon::Cream);
    setColour(juce::Slider::thumbColourId, Crayon::Pink);
    setColour(juce::Label::textColourId, Crayon::DarkText);
}

void AetherEditor::CrayonLookAndFeel::drawRotarySlider(
    juce::Graphics& g, int x, int y, int w, int h,
    float sliderPos, float rotaryStartAngle, float rotaryEndAngle, juce::Slider& slider)
{
    auto bounds = juce::Rectangle<float>((float)x, (float)y, (float)w, (float)h);
    auto radius = juce::jmin(bounds.getWidth(), bounds.getHeight()) / 2.0f - 4.0f;
    auto centre = bounds.getCentre();
    auto angle = rotaryStartAngle + sliderPos * (rotaryEndAngle - rotaryStartAngle);

    // Outer circle (thick crayon outline)
    g.setColour(Crayon::Cream);
    g.fillEllipse(centre.x - radius, centre.y - radius, radius * 2.0f, radius * 2.0f);

    // Colourful ring
    juce::Path arcBg;
    arcBg.addCentredArc(centre.x, centre.y, radius - 2.0f, radius - 2.0f,
                         0.0f, rotaryStartAngle, rotaryEndAngle, true);
    g.setColour(Crayon::Outline.withAlpha(0.2f));
    g.strokePath(arcBg, juce::PathStrokeType(5.0f));

    // Value arc
    juce::Path arcVal;
    arcVal.addCentredArc(centre.x, centre.y, radius - 2.0f, radius - 2.0f,
                          0.0f, rotaryStartAngle, angle, true);
    g.setColour(Crayon::Pink);
    g.strokePath(arcVal, juce::PathStrokeType(5.0f, juce::PathStrokeType::curved,
                                               juce::PathStrokeType::rounded));

    // Inner filled circle
    float innerR = radius * 0.55f;
    g.setColour(Crayon::PurpleBg);
    g.fillEllipse(centre.x - innerR, centre.y - innerR, innerR * 2.0f, innerR * 2.0f);

    // Thick outline
    g.setColour(Crayon::Outline);
    g.drawEllipse(centre.x - radius, centre.y - radius, radius * 2.0f, radius * 2.0f, 2.5f);
    g.drawEllipse(centre.x - innerR, centre.y - innerR, innerR * 2.0f, innerR * 2.0f, 2.0f);

    // Pointer line (thick, crayon-like)
    juce::Path pointer;
    auto pointerLen = radius * 0.75f;
    auto pointerThick = 3.0f;
    pointer.addRectangle(-pointerThick * 0.5f, -pointerLen, pointerThick, pointerLen * 0.45f);
    pointer.applyTransform(juce::AffineTransform::rotation(angle).translated(centre.x, centre.y));
    g.setColour(Crayon::Outline);
    g.fillPath(pointer);
}

void AetherEditor::CrayonLookAndFeel::drawToggleButton(
    juce::Graphics& g, juce::ToggleButton& button,
    bool /*highlighted*/, bool /*down*/)
{
    auto bounds = button.getLocalBounds().toFloat().reduced(2.0f);
    bool on = button.getToggleState();

    // Determine if this is a bypass button (text is single letter) or sync button
    bool isBypass = button.getButtonText().length() == 1;

    if (isBypass)
    {
        g.setColour(on ? Crayon::Red.withAlpha(0.4f) : Crayon::Green.withAlpha(0.6f));
        g.fillRoundedRectangle(bounds, 6.0f);
        g.setColour(Crayon::Outline);
        g.drawRoundedRectangle(bounds, 6.0f, 2.0f);
        g.setColour(Crayon::DarkText);
        g.setFont(juce::Font(12.0f).boldened());
        g.drawText(on ? "OFF" : button.getButtonText(), bounds, juce::Justification::centred);
    }
    else
    {
        g.setColour(on ? Crayon::Teal.withAlpha(0.7f) : Crayon::Outline.withAlpha(0.3f));
        g.fillRoundedRectangle(bounds, 6.0f);
        g.setColour(Crayon::Outline);
        g.drawRoundedRectangle(bounds, 6.0f, 2.0f);
        g.setColour(on ? Crayon::White : Crayon::DarkText);
        g.setFont(juce::Font(11.0f).boldened());
        g.drawText(button.getButtonText(), bounds, juce::Justification::centred);
    }
}

// ================================================================
// Constructor / Destructor
// ================================================================
AetherEditor::AetherEditor(AetherProcessor& p)
    : AudioProcessorEditor(&p), processor(p)
{
    setLookAndFeel(&crayonLnf);
    setSize(1020, 620);

    auto setupKnob = [&](juce::Slider& s, bool isInt = false) {
        s.setSliderStyle(juce::Slider::RotaryHorizontalVerticalDrag);
        s.setTextBoxStyle(juce::Slider::NoTextBox, false, 0, 0);
        if (isInt) s.setRange(s.getMinimum(), s.getMaximum(), 1.0);
        addAndMakeVisible(s);
    };

    // Swell
    setupKnob(swellSens); setupKnob(swellAttack); setupKnob(swellDepth);
    // Vinyl
    setupKnob(vinylYear); setupKnob(vinylWarp); setupKnob(vinylDust);
    setupKnob(vinylWear); setupKnob(vinylDetune); setupKnob(vinylNoise);
    // Psyche
    setupKnob(psycheShimmer); setupKnob(psycheSpace); setupKnob(psycheMod);
    setupKnob(psycheWarp); setupKnob(psycheMix); setupKnob(psycheNotches); setupKnob(psycheSweep);
    // LFO
    setupKnob(lfoShape, true); setupKnob(lfoRate); setupKnob(lfoDepth);
    setupKnob(lfoSyncRate, true); setupKnob(lfoPhaseOffset);
    // Master
    setupKnob(masterMix); setupKnob(masterGain);

    // Toggles
    for (auto* b : { &swellBypass, &vinylBypass, &psycheBypass, &lfoBypass, &lfoSync })
        addAndMakeVisible(*b);

    // Labels
    addLabel(swellSens, "SENS"); addLabel(swellAttack, "ATK"); addLabel(swellDepth, "DEPTH");
    addLabel(vinylYear, "YEAR"); addLabel(vinylWarp, "WARP"); addLabel(vinylDust, "DUST");
    addLabel(vinylWear, "WEAR"); addLabel(vinylDetune, "DETUNE"); addLabel(vinylNoise, "NOISE");
    addLabel(psycheShimmer, "SHIMMER"); addLabel(psycheSpace, "SPACE"); addLabel(psycheMod, "MOD");
    addLabel(psycheWarp, "WARP"); addLabel(psycheMix, "MIX"); addLabel(psycheNotches, "NOTCH"); addLabel(psycheSweep, "SWEEP");
    addLabel(lfoShape, "SHAPE"); addLabel(lfoRate, "RATE"); addLabel(lfoDepth, "DEPTH");
    addLabel(lfoSyncRate, "DIV"); addLabel(lfoPhaseOffset, "PHASE");
    addLabel(masterMix, "MIX"); addLabel(masterGain, "GAIN");

    // Attachments
    auto& apvts = processor.apvts;
    aSwellSens    = std::make_unique<SliderAttachment>(apvts, "swellSens",    swellSens);
    aSwellAttack  = std::make_unique<SliderAttachment>(apvts, "swellAttack",  swellAttack);
    aSwellDepth   = std::make_unique<SliderAttachment>(apvts, "swellDepth",   swellDepth);
    aVinylYear    = std::make_unique<SliderAttachment>(apvts, "vinylYear",    vinylYear);
    aVinylWarp    = std::make_unique<SliderAttachment>(apvts, "vinylWarp",    vinylWarp);
    aVinylDust    = std::make_unique<SliderAttachment>(apvts, "vinylDust",    vinylDust);
    aVinylWear    = std::make_unique<SliderAttachment>(apvts, "vinylWear",    vinylWear);
    aVinylDetune  = std::make_unique<SliderAttachment>(apvts, "vinylDetune",  vinylDetune);
    aVinylNoise   = std::make_unique<SliderAttachment>(apvts, "vinylNoise",   vinylNoise);
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
    aMasterMix     = std::make_unique<SliderAttachment>(apvts, "masterMix",    masterMix);
    aMasterGain    = std::make_unique<SliderAttachment>(apvts, "masterGain",   masterGain);
    aSwellBypass   = std::make_unique<ButtonAttachment>(apvts, "swellBypass",  swellBypass);
    aVinylBypass   = std::make_unique<ButtonAttachment>(apvts, "vinylBypass",  vinylBypass);
    aPsycheBypass  = std::make_unique<ButtonAttachment>(apvts, "psycheBypass", psycheBypass);
    aLfoBypass     = std::make_unique<ButtonAttachment>(apvts, "lfoBypass",    lfoBypass);
    aLfoSync       = std::make_unique<ButtonAttachment>(apvts, "lfoSync",      lfoSync);

    initCreatures();
    startTimerHz(30); // 30fps animation
}

AetherEditor::~AetherEditor()
{
    setLookAndFeel(nullptr);
}

// ================================================================
// Creature & sparkle initialization
// ================================================================
void AetherEditor::initCreatures()
{
    std::mt19937 rng(12345);
    std::uniform_real_distribution<float> xDist(30.0f, 990.0f);
    std::uniform_real_distribution<float> yDist(50.0f, 590.0f);
    std::uniform_real_distribution<float> sizeDist(18.0f, 38.0f);
    std::uniform_real_distribution<float> speedDist(0.3f, 1.2f);
    std::uniform_real_distribution<float> driftDist(8.0f, 30.0f);
    std::uniform_real_distribution<float> phaseDist(0.0f, 6.28f);
    std::uniform_int_distribution<int> typeDist(0, 4);

    for (int i = 0; i < 12; ++i)
    {
        Creature c;
        c.type = typeDist(rng);
        c.baseX = xDist(rng);
        c.baseY = yDist(rng);
        c.driftX = driftDist(rng);
        c.driftY = driftDist(rng) * 0.7f;
        c.speedX = speedDist(rng);
        c.speedY = speedDist(rng) * 0.8f;
        c.size = sizeDist(rng);
        c.phaseX = phaseDist(rng);
        c.phaseY = phaseDist(rng);
        creatures.push_back(c);
    }

    // Sparkles (little stars in the background)
    std::uniform_real_distribution<float> spSizeDist(2.0f, 6.0f);
    std::uniform_real_distribution<float> spSpeedDist(1.0f, 4.0f);
    for (int i = 0; i < 40; ++i)
    {
        Sparkle s;
        s.x = xDist(rng);
        s.y = yDist(rng);
        s.phase = phaseDist(rng);
        s.speed = spSpeedDist(rng);
        s.size = spSizeDist(rng);
        sparkles.push_back(s);
    }
}

// ================================================================
// Timer
// ================================================================
void AetherEditor::timerCallback()
{
    animTime += 1.0f / 30.0f;
    repaint();
}

// ================================================================
// Layout
// ================================================================
void AetherEditor::resized()
{
    int W = getWidth();
    int knobW = 58, knobH = 58;
    int labelH = 14;
    int pad = 6;
    int sectionY = 80;  // below title
    int sectionH = 240;
    int sectionW = (W - 50) / 4;

    // Section bounds
    int sx0 = 15;
    auto swell  = juce::Rectangle<int>(sx0, sectionY, sectionW, sectionH);
    auto vinyl  = juce::Rectangle<int>(sx0 + sectionW + 5, sectionY, sectionW, sectionH);
    auto psyche = juce::Rectangle<int>(sx0 + (sectionW + 5) * 2, sectionY, sectionW, sectionH);
    auto lfoSec = juce::Rectangle<int>(sx0 + (sectionW + 5) * 3, sectionY, sectionW, sectionH);

    auto placeKnob = [&](juce::Slider& s, int bx, int by) {
        s.setBounds(bx, by, knobW, knobH);
    };

    int knobY1 = sectionY + 38;
    int knobY2 = sectionY + 38 + knobH + labelH + pad;
    int knobGap = knobW + 4;

    // Swell (3 knobs)
    int sc = swell.getCentreX() - knobW * 3 / 2 - 2;
    placeKnob(swellSens, sc, knobY1);
    placeKnob(swellAttack, sc + knobGap, knobY1);
    placeKnob(swellDepth, sc + knobGap * 2, knobY1);
    swellBypass.setBounds(swell.getX() + 4, swell.getY() + 4, 30, 22);

    // Vinyl (6 knobs, 2 rows)
    int vc = vinyl.getX() + 8;
    placeKnob(vinylYear, vc, knobY1);
    placeKnob(vinylWarp, vc + knobGap, knobY1);
    placeKnob(vinylDust, vc + knobGap * 2, knobY1);
    placeKnob(vinylWear, vc, knobY2);
    placeKnob(vinylDetune, vc + knobGap, knobY2);
    placeKnob(vinylNoise, vc + knobGap * 2, knobY2);
    vinylBypass.setBounds(vinyl.getX() + 4, vinyl.getY() + 4, 30, 22);

    // Psyche (7 knobs, 2 rows: 4+3)
    int pc = psyche.getX() + 2;
    int pGap = knobW + 1;
    placeKnob(psycheShimmer, pc, knobY1);
    placeKnob(psycheSpace, pc + pGap, knobY1);
    placeKnob(psycheMod, pc + pGap * 2, knobY1);
    placeKnob(psycheWarp, pc + pGap * 3, knobY1);
    placeKnob(psycheMix, pc, knobY2);
    placeKnob(psycheNotches, pc + pGap, knobY2);
    placeKnob(psycheSweep, pc + pGap * 2, knobY2);
    psycheBypass.setBounds(psyche.getX() + 4, psyche.getY() + 4, 30, 22);

    // LFO (5 knobs + sync, 2 rows: 3+2+sync)
    int lc = lfoSec.getX() + 8;
    placeKnob(lfoShape, lc, knobY1);
    placeKnob(lfoRate, lc + knobGap, knobY1);
    placeKnob(lfoDepth, lc + knobGap * 2, knobY1);
    placeKnob(lfoSyncRate, lc, knobY2);
    placeKnob(lfoPhaseOffset, lc + knobGap, knobY2);
    lfoSync.setBounds(lc + knobGap * 2, knobY2 + 10, 50, 28);
    lfoBypass.setBounds(lfoSec.getX() + 4, lfoSec.getY() + 4, 30, 22);

    // Master (bottom center)
    int my = sectionY + sectionH + 25;
    int mx = W / 2 - knobGap;
    placeKnob(masterMix, mx, my);
    placeKnob(masterGain, mx + knobGap, my);

    // Update label positions (below each knob)
    for (auto& lbl : labels)
    {
        if (auto* slider = dynamic_cast<juce::Slider*>(lbl->getAttachedComponent()))
        {
            auto sb = slider->getBounds();
            lbl->setBounds(sb.getX() - 4, sb.getBottom() - 2, sb.getWidth() + 8, labelH);
        }
    }
}

// ================================================================
// Label helper
// ================================================================
juce::Label& AetherEditor::addLabel(juce::Slider& s, const juce::String& text)
{
    auto lbl = std::make_unique<juce::Label>("", text);
    lbl->setFont(juce::Font(10.0f).boldened());
    lbl->setColour(juce::Label::textColourId, Crayon::DarkText);
    lbl->setJustificationType(juce::Justification::centred);
    lbl->attachToComponent(&s, false);
    addAndMakeVisible(*lbl);
    auto& ref = *lbl;
    labels.push_back(std::move(lbl));
    return ref;
}

// ================================================================
// Paint
// ================================================================
void AetherEditor::paint(juce::Graphics& g)
{
    drawBackground(g);
    drawSparkles(g);

    int W = getWidth();
    int sectionY = 80;
    int sectionH = 240;
    int sectionW = (W - 50) / 4;
    int sx0 = 15;

    // Draw section boxes
    drawSectionBox(g, {sx0, sectionY, sectionW, sectionH}, Crayon::PinkBg, "SWELL");
    drawSectionBox(g, {sx0 + sectionW + 5, sectionY, sectionW, sectionH}, Crayon::BlueBg, "VINYL");
    drawSectionBox(g, {sx0 + (sectionW + 5) * 2, sectionY, sectionW, sectionH}, Crayon::PurpleBg, "PSYCHE");
    drawSectionBox(g, {sx0 + (sectionW + 5) * 3, sectionY, sectionW, sectionH}, Crayon::GreenBg, "LFO");

    // Master section label
    int my = sectionY + sectionH + 10;
    g.setColour(Crayon::DarkText);
    g.setFont(juce::Font(14.0f).boldened());
    g.drawText("MASTER", 0, my, W, 18, juce::Justification::centred);

    // Draw creatures (on top of sections, behind knobs -- they float around)
    for (auto& c : creatures)
    {
        float cx = c.baseX + std::sin(animTime * c.speedX + c.phaseX) * c.driftX;
        float cy = c.baseY + std::sin(animTime * c.speedY + c.phaseY) * c.driftY;
        float phase = animTime * c.speedX;

        switch (c.type)
        {
            case 0: drawMushroom(g, cx, cy, c.size, phase); break;
            case 1: drawGhost(g, cx, cy, c.size, phase); break;
            case 2: drawCrystal(g, cx, cy, c.size, phase); break;
            case 3: drawFlower(g, cx, cy, c.size, phase); break;
            case 4: drawAlienEye(g, cx, cy, c.size, phase); break;
        }
    }

    drawTitle(g);

    // LFO shape/rate display text
    {
        int lShape = static_cast<int>(lfoShape.getValue());
        int lSync = static_cast<int>(lfoSyncRate.getValue());
        bool synced = lfoSync.getToggleState();
        juce::String info = LFOProcessor::shapeName(lShape);
        if (synced)
            info += juce::String(" | ") + LFOProcessor::syncRateName(lSync);

        int lfoX = sx0 + (sectionW + 5) * 3;
        g.setColour(Crayon::DarkText.withAlpha(0.8f));
        g.setFont(juce::Font(11.0f));
        g.drawText(info, lfoX, sectionY + sectionH - 18, sectionW, 16, juce::Justification::centred);
    }

    // Version
    g.setColour(Crayon::DarkText.withAlpha(0.4f));
    g.setFont(juce::Font(9.0f));
    g.drawText("v3.0 // artemis", 0, getHeight() - 14, getWidth(), 12, juce::Justification::centredRight);
}

// ================================================================
// Background
// ================================================================
void AetherEditor::drawBackground(juce::Graphics& g)
{
    // Cream paper background
    g.fillAll(Crayon::Cream);

    // Subtle notebook lines
    g.setColour(Crayon::Blue.withAlpha(0.06f));
    for (int y = 30; y < getHeight(); y += 24)
        g.drawHorizontalLine(y, 0.0f, (float)getWidth());

    // Margin line (notebook left margin)
    g.setColour(Crayon::Red.withAlpha(0.12f));
    g.drawVerticalLine(10, 0.0f, (float)getHeight());

    // Colorful crayon scribbles in corners (decorative)
    float t = animTime * 0.3f;
    g.setColour(Crayon::Pink.withAlpha(0.08f));
    g.fillEllipse(std::sin(t) * 20.0f - 30.0f, std::cos(t * 0.7f) * 15.0f - 20.0f, 140.0f, 100.0f);
    g.setColour(Crayon::Blue.withAlpha(0.06f));
    g.fillEllipse((float)getWidth() - 100.0f + std::sin(t * 0.5f) * 15.0f,
                  (float)getHeight() - 80.0f + std::cos(t * 0.9f) * 10.0f, 120.0f, 90.0f);
    g.setColour(Crayon::Green.withAlpha(0.06f));
    g.fillEllipse((float)getWidth() - 90.0f + std::cos(t * 0.3f) * 10.0f, -20.0f, 100.0f, 80.0f);
    g.setColour(Crayon::Yellow.withAlpha(0.08f));
    g.fillEllipse(-20.0f, (float)getHeight() - 60.0f + std::sin(t * 0.6f) * 12.0f, 110.0f, 80.0f);
}

// ================================================================
// Title
// ================================================================
void AetherEditor::drawTitle(juce::Graphics& g)
{
    // Big rainbow "AETHER" title
    juce::String title = "AETHER";
    auto font = juce::Font(42.0f).boldened();
    g.setFont(font);

    float titleW = font.getStringWidthFloat(title);
    float startX = ((float)getWidth() - titleW) * 0.5f;
    float y = 20.0f;

    juce::Colour rainbow[] = { Crayon::Red, Crayon::Orange, Crayon::Yellow,
                                Crayon::Green, Crayon::Blue, Crayon::Purple };

    for (int i = 0; i < title.length(); ++i)
    {
        juce::String ch = title.substring(i, i + 1);
        float cw = font.getStringWidthFloat(ch);
        float bounce = std::sin(animTime * 2.5f + i * 0.8f) * 4.0f;

        // Shadow
        g.setColour(Crayon::Outline.withAlpha(0.3f));
        g.drawText(ch, (int)(startX + 2), (int)(y + bounce + 2), (int)cw + 2, 50,
                   juce::Justification::left);

        // Letter
        g.setColour(rainbow[i % 6]);
        g.drawText(ch, (int)startX, (int)(y + bounce), (int)cw + 2, 50,
                   juce::Justification::left);

        startX += cw;
    }

    // Subtitle
    g.setColour(Crayon::DarkText.withAlpha(0.5f));
    g.setFont(juce::Font(11.0f).italicised());
    g.drawText("psychedelic guitar processor", 0, 58, getWidth(), 16, juce::Justification::centred);
}

// ================================================================
// Section box (wobbly crayon rectangle)
// ================================================================
void AetherEditor::drawSectionBox(juce::Graphics& g, juce::Rectangle<int> bounds,
                                   juce::Colour colour, const juce::String& title)
{
    auto r = bounds.toFloat().reduced(2.0f);

    // Fill
    g.setColour(colour.withAlpha(0.5f));
    auto wobbled = makeWobblyRect(r, 3.0f, static_cast<unsigned int>(bounds.getX() * 7 + bounds.getY()));
    g.fillPath(wobbled);

    // Thick crayon outline
    g.setColour(Crayon::Outline.withAlpha(0.6f));
    g.strokePath(wobbled, juce::PathStrokeType(2.5f));

    // Section title
    g.setColour(Crayon::DarkText);
    g.setFont(juce::Font(13.0f).boldened());
    g.drawText(title, bounds.getX() + 36, bounds.getY() + 4, bounds.getWidth() - 40, 20,
               juce::Justification::left);
}

// ================================================================
// Wobbly rectangle (crayon style)
// ================================================================
juce::Path AetherEditor::makeWobblyRect(juce::Rectangle<float> r, float wobble, unsigned int seed)
{
    std::mt19937 rng(seed);
    std::uniform_real_distribution<float> dist(-wobble, wobble);
    juce::Path p;

    int steps = 12;
    // Top edge
    p.startNewSubPath(r.getX() + dist(rng), r.getY() + dist(rng));
    for (int i = 1; i <= steps; ++i)
    {
        float t = (float)i / (float)steps;
        p.lineTo(r.getX() + r.getWidth() * t + dist(rng), r.getY() + dist(rng));
    }
    // Right edge
    for (int i = 1; i <= steps; ++i)
    {
        float t = (float)i / (float)steps;
        p.lineTo(r.getRight() + dist(rng), r.getY() + r.getHeight() * t + dist(rng));
    }
    // Bottom edge (reversed)
    for (int i = 1; i <= steps; ++i)
    {
        float t = (float)i / (float)steps;
        p.lineTo(r.getRight() - r.getWidth() * t + dist(rng), r.getBottom() + dist(rng));
    }
    // Left edge (reversed)
    for (int i = 1; i <= steps; ++i)
    {
        float t = (float)i / (float)steps;
        p.lineTo(r.getX() + dist(rng), r.getBottom() - r.getHeight() * t + dist(rng));
    }
    p.closeSubPath();
    return p;
}

// ================================================================
// Sparkles
// ================================================================
void AetherEditor::drawSparkles(juce::Graphics& g)
{
    for (auto& s : sparkles)
    {
        float alpha = 0.3f + 0.7f * (0.5f + 0.5f * std::sin(animTime * s.speed + s.phase));
        g.setColour(Crayon::Yellow.withAlpha(alpha * 0.6f));
        drawStar(g, s.x, s.y, s.size, alpha);
    }
}

// ================================================================
// Creature drawing functions
// ================================================================

void AetherEditor::drawMushroom(juce::Graphics& g, float x, float y, float size, float phase)
{
    float wobble = std::sin(phase * 2.0f) * 2.0f;
    float s = size;

    // Stem
    g.setColour(Crayon::Cream);
    g.fillRoundedRectangle(x - s * 0.15f, y, s * 0.3f, s * 0.5f, 3.0f);
    g.setColour(Crayon::Outline);
    g.drawRoundedRectangle(x - s * 0.15f, y, s * 0.3f, s * 0.5f, 3.0f, 2.0f);

    // Cap
    juce::Path cap;
    cap.addCentredArc(x, y + wobble * 0.5f, s * 0.45f, s * 0.35f, 0.0f,
                       juce::MathConstants<float>::pi, juce::MathConstants<float>::twoPi, true);
    cap.closeSubPath();
    g.setColour(Crayon::MushroomCap);
    g.fillPath(cap);
    g.setColour(Crayon::Outline);
    g.strokePath(cap, juce::PathStrokeType(2.0f));

    // Dots on cap
    g.setColour(Crayon::MushroomDots);
    g.fillEllipse(x - s * 0.15f, y - s * 0.2f + wobble * 0.5f, s * 0.1f, s * 0.1f);
    g.fillEllipse(x + s * 0.08f, y - s * 0.25f + wobble * 0.5f, s * 0.08f, s * 0.08f);
    g.fillEllipse(x - s * 0.3f, y - s * 0.1f + wobble * 0.5f, s * 0.07f, s * 0.07f);

    // Eyes
    g.setColour(Crayon::Outline);
    g.fillEllipse(x - s * 0.1f, y + s * 0.12f, s * 0.08f, s * 0.1f);
    g.fillEllipse(x + s * 0.04f, y + s * 0.12f, s * 0.08f, s * 0.1f);

    // Smile
    juce::Path smile;
    smile.addCentredArc(x, y + s * 0.2f, s * 0.08f, s * 0.04f, 0.0f,
                         0.0f, juce::MathConstants<float>::pi, true);
    g.strokePath(smile, juce::PathStrokeType(1.5f));
}

void AetherEditor::drawStar(juce::Graphics& g, float cx, float cy, float size, float twinkle)
{
    int points = 4;
    float outerR = size * twinkle;
    float innerR = outerR * 0.35f;
    juce::Path star;

    for (int i = 0; i < points * 2; ++i)
    {
        float r = (i % 2 == 0) ? outerR : innerR;
        float angle = (float)i / (float)(points * 2) * juce::MathConstants<float>::twoPi
                      - juce::MathConstants<float>::halfPi;
        float px = cx + std::cos(angle) * r;
        float py = cy + std::sin(angle) * r;
        if (i == 0) star.startNewSubPath(px, py);
        else star.lineTo(px, py);
    }
    star.closeSubPath();
    g.fillPath(star);
}

void AetherEditor::drawGhost(juce::Graphics& g, float x, float y, float size, float phase)
{
    float s = size;
    float wobble = std::sin(phase * 1.5f) * 3.0f;

    // Body
    juce::Path body;
    body.startNewSubPath(x - s * 0.35f, y + s * 0.4f);
    body.lineTo(x - s * 0.35f, y);
    body.addCentredArc(x, y, s * 0.35f, s * 0.35f, 0.0f,
                        juce::MathConstants<float>::pi, juce::MathConstants<float>::twoPi, false);
    body.lineTo(x + s * 0.35f, y + s * 0.4f);
    // Wavy bottom
    float waveStep = s * 0.175f;
    for (float wx = x + s * 0.35f; wx >= x - s * 0.35f; wx -= waveStep)
    {
        float wy = y + s * 0.4f + std::sin((wx + wobble) * 0.5f) * s * 0.08f;
        body.lineTo(wx, wy);
    }
    body.closeSubPath();

    g.setColour(Crayon::GhostBody);
    g.fillPath(body);
    g.setColour(Crayon::Outline.withAlpha(0.5f));
    g.strokePath(body, juce::PathStrokeType(1.8f));

    // Eyes (big round cute eyes)
    g.setColour(Crayon::Outline);
    g.fillEllipse(x - s * 0.18f, y - s * 0.05f, s * 0.13f, s * 0.16f);
    g.fillEllipse(x + s * 0.06f, y - s * 0.05f, s * 0.13f, s * 0.16f);
    // Eye highlights
    g.setColour(Crayon::White);
    g.fillEllipse(x - s * 0.15f, y - s * 0.02f, s * 0.05f, s * 0.05f);
    g.fillEllipse(x + s * 0.09f, y - s * 0.02f, s * 0.05f, s * 0.05f);

    // Blush
    g.setColour(Crayon::Pink.withAlpha(0.3f));
    g.fillEllipse(x - s * 0.25f, y + s * 0.08f, s * 0.12f, s * 0.08f);
    g.fillEllipse(x + s * 0.14f, y + s * 0.08f, s * 0.12f, s * 0.08f);
}

void AetherEditor::drawCrystal(juce::Graphics& g, float x, float y, float size, float rotation)
{
    float s = size;
    float angle = rotation * 0.3f;

    juce::Path crystal;
    // Diamond shape
    crystal.startNewSubPath(x, y - s * 0.5f);  // top
    crystal.lineTo(x + s * 0.3f, y);            // right
    crystal.lineTo(x, y + s * 0.5f);            // bottom
    crystal.lineTo(x - s * 0.3f, y);            // left
    crystal.closeSubPath();

    auto transform = juce::AffineTransform::rotation(angle, x, y);
    crystal.applyTransform(transform);

    // Glow
    g.setColour(Crayon::Teal.withAlpha(0.15f));
    g.fillEllipse(x - s * 0.5f, y - s * 0.5f, s, s);

    g.setColour(Crayon::CrystalBody);
    g.fillPath(crystal);
    g.setColour(Crayon::Outline.withAlpha(0.6f));
    g.strokePath(crystal, juce::PathStrokeType(2.0f));

    // Inner facet lines
    g.setColour(Crayon::White.withAlpha(0.4f));
    juce::Path facet;
    facet.startNewSubPath(x - s * 0.1f, y - s * 0.3f);
    facet.lineTo(x - s * 0.15f, y + s * 0.1f);
    facet.applyTransform(transform);
    g.strokePath(facet, juce::PathStrokeType(1.0f));
}

void AetherEditor::drawFlower(juce::Graphics& g, float x, float y, float size, float rotation)
{
    float s = size;
    int petals = 6;
    float petalR = s * 0.3f;
    float centerR = s * 0.15f;

    juce::Colour petalColors[] = { Crayon::Pink, Crayon::Purple, Crayon::Orange,
                                    Crayon::Blue, Crayon::Red, Crayon::Teal };

    for (int i = 0; i < petals; ++i)
    {
        float angle = rotation * 0.5f + (float)i / (float)petals * juce::MathConstants<float>::twoPi;
        float px = x + std::cos(angle) * petalR;
        float py = y + std::sin(angle) * petalR;

        g.setColour(petalColors[i % 6].withAlpha(0.65f));
        g.fillEllipse(px - petalR * 0.6f, py - petalR * 0.6f, petalR * 1.2f, petalR * 1.2f);
        g.setColour(Crayon::Outline.withAlpha(0.35f));
        g.drawEllipse(px - petalR * 0.6f, py - petalR * 0.6f, petalR * 1.2f, petalR * 1.2f, 1.5f);
    }

    // Center
    g.setColour(Crayon::FlowerCenter);
    g.fillEllipse(x - centerR, y - centerR, centerR * 2.0f, centerR * 2.0f);
    g.setColour(Crayon::Outline);
    g.drawEllipse(x - centerR, y - centerR, centerR * 2.0f, centerR * 2.0f, 2.0f);

    // Smiley face in center
    float fc = centerR * 0.4f;
    g.fillEllipse(x - fc * 0.6f, y - fc * 0.4f, fc * 0.3f, fc * 0.35f);
    g.fillEllipse(x + fc * 0.3f, y - fc * 0.4f, fc * 0.3f, fc * 0.35f);
}

void AetherEditor::drawAlienEye(juce::Graphics& g, float x, float y, float size, float lookPhase)
{
    float s = size;
    // Outer eye
    g.setColour(Crayon::White);
    g.fillEllipse(x - s * 0.4f, y - s * 0.3f, s * 0.8f, s * 0.6f);
    g.setColour(Crayon::Outline);
    g.drawEllipse(x - s * 0.4f, y - s * 0.3f, s * 0.8f, s * 0.6f, 2.5f);

    // Iris (follows a circular path)
    float lookX = std::sin(lookPhase * 0.7f) * s * 0.12f;
    float lookY = std::cos(lookPhase * 0.5f) * s * 0.06f;
    float irisR = s * 0.18f;

    // Rainbow iris
    g.setColour(Crayon::Purple);
    g.fillEllipse(x + lookX - irisR, y + lookY - irisR, irisR * 2.0f, irisR * 2.0f);
    g.setColour(Crayon::Teal.withAlpha(0.5f));
    g.fillEllipse(x + lookX - irisR * 0.7f, y + lookY - irisR * 0.7f,
                  irisR * 1.4f, irisR * 1.4f);

    // Pupil
    float pupilR = irisR * 0.5f;
    g.setColour(Crayon::Outline);
    g.fillEllipse(x + lookX - pupilR, y + lookY - pupilR, pupilR * 2.0f, pupilR * 2.0f);

    // Highlight
    g.setColour(Crayon::White);
    g.fillEllipse(x + lookX - pupilR * 0.3f + irisR * 0.3f,
                  y + lookY - pupilR * 0.3f - irisR * 0.3f,
                  pupilR * 0.5f, pupilR * 0.5f);

    // Eyelashes (top)
    for (int i = 0; i < 3; ++i)
    {
        float la = -0.8f + (float)i * 0.4f + juce::MathConstants<float>::halfPi;
        float lx1 = x + std::cos(la) * s * 0.35f;
        float ly1 = y + std::sin(la) * s * 0.25f - s * 0.05f;
        float lx2 = x + std::cos(la) * s * 0.5f;
        float ly2 = y + std::sin(la) * s * 0.38f - s * 0.05f;
        g.setColour(Crayon::Outline);
        g.drawLine(lx1, ly1, lx2, ly2, 2.0f);
    }
}

// ================================================================
// Slider setup
// ================================================================
void AetherEditor::setupSlider(juce::Slider& s, bool isInt)
{
    s.setSliderStyle(juce::Slider::RotaryHorizontalVerticalDrag);
    s.setTextBoxStyle(juce::Slider::NoTextBox, false, 0, 0);
    if (isInt) s.setRange(s.getMinimum(), s.getMaximum(), 1.0);
    addAndMakeVisible(s);
}
