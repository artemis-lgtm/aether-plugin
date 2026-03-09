#include "PluginEditor.h"
#include "dsp/LFOProcessor.h"
#include <cmath>

// ================================================================
// Colour palette — bright sky / crayon childlike
// ================================================================
namespace Sky
{
    const auto Blue        = juce::Colour(0xFF5DADE2);   // sky blue
    const auto BlueDark    = juce::Colour(0xFF3498DB);
    const auto BlueLight   = juce::Colour(0xFF85C1E9);
    const auto White       = juce::Colour(0xFFFFFFFF);
    const auto CloudWhite  = juce::Colour(0xFFF0F4F8);
    const auto SunYellow   = juce::Colour(0xFFFFD700);
    const auto SunOrange   = juce::Colour(0xFFFFAA00);
    const auto Black       = juce::Colour(0xFF222222);
    const auto CrayonRed   = juce::Colour(0xFFFF6B6B);
    const auto CrayonPink  = juce::Colour(0xFFFF69B4);
    const auto CrayonOrange= juce::Colour(0xFFFF8C42);
    const auto CrayonYellow= juce::Colour(0xFFFFE066);
    const auto CrayonGreen = juce::Colour(0xFF6BCB77);
    const auto CrayonPurple= juce::Colour(0xFFBB6BD9);
    const auto CrayonTeal  = juce::Colour(0xFF00CEC9);
    const auto Brown       = juce::Colour(0xFF8B5E3C);
    const auto LabelBg     = juce::Colour(0x50FFFFFF);   // semi-transparent white
    const auto KnobWhite   = juce::Colour(0xFFF5F5F5);
    const auto KnobShadow  = juce::Colour(0x40000000);
    const auto KnobSlot    = juce::Colour(0xFFCCCCCC);
}

// ================================================================
// Look and Feel — big chunky white knobs like hardware pedal
// ================================================================
AetherEditor::CrayonLookAndFeel::CrayonLookAndFeel()
{
    setColour(juce::Label::textColourId, Sky::Black);
}

void AetherEditor::CrayonLookAndFeel::drawRotarySlider(
    juce::Graphics& g, int x, int y, int w, int h,
    float sliderPos, float rotaryStartAngle, float rotaryEndAngle, juce::Slider&)
{
    auto bounds = juce::Rectangle<float>((float)x, (float)y, (float)w, (float)h);
    auto radius = juce::jmin(bounds.getWidth(), bounds.getHeight()) / 2.0f - 2.0f;
    auto centre = bounds.getCentre();
    auto angle = rotaryStartAngle + sliderPos * (rotaryEndAngle - rotaryStartAngle);

    // Drop shadow
    g.setColour(Sky::KnobShadow);
    g.fillEllipse(centre.x - radius + 2, centre.y - radius + 2, radius * 2.0f, radius * 2.0f);

    // White knob body (like real hardware pedal knob)
    juce::ColourGradient knobGrad(Sky::White, centre.x - radius * 0.3f, centre.y - radius * 0.3f,
                                   Sky::KnobSlot, centre.x + radius * 0.5f, centre.y + radius * 0.5f, true);
    g.setGradientFill(knobGrad);
    g.fillEllipse(centre.x - radius, centre.y - radius, radius * 2.0f, radius * 2.0f);

    // Subtle rim
    g.setColour(juce::Colour(0x20000000));
    g.drawEllipse(centre.x - radius, centre.y - radius, radius * 2.0f, radius * 2.0f, 1.5f);

    // Indicator notch/slot (like real knob)
    float notchLen = radius * 0.35f;
    float notchStartR = radius * 0.15f;
    float nx1 = centre.x + std::sin(angle) * notchStartR;
    float ny1 = centre.y - std::cos(angle) * notchStartR;
    float nx2 = centre.x + std::sin(angle) * (notchStartR + notchLen);
    float ny2 = centre.y - std::cos(angle) * (notchStartR + notchLen);
    g.setColour(juce::Colour(0xFF888888));
    g.drawLine(nx1, ny1, nx2, ny2, 2.5f);
}

void AetherEditor::CrayonLookAndFeel::drawToggleButton(
    juce::Graphics& g, juce::ToggleButton& button, bool, bool)
{
    auto bounds = button.getLocalBounds().toFloat().reduced(2.0f);
    bool on = button.getToggleState();
    bool isBypass = button.getButtonText().length() == 1;

    if (isBypass)
    {
        g.setColour(on ? Sky::CrayonRed.withAlpha(0.8f) : Sky::CrayonGreen.withAlpha(0.8f));
        g.fillRoundedRectangle(bounds, 6.0f);
        g.setColour(Sky::Black.withAlpha(0.3f));
        g.drawRoundedRectangle(bounds, 6.0f, 1.5f);
        g.setColour(Sky::White);
        g.setFont(juce::Font(11.0f).boldened());
        g.drawText(on ? "OFF" : "ON", bounds, juce::Justification::centred);
    }
    else
    {
        g.setColour(on ? Sky::CrayonTeal.withAlpha(0.8f) : juce::Colour(0xFFBBBBBB));
        g.fillRoundedRectangle(bounds, 6.0f);
        g.setColour(Sky::Black.withAlpha(0.3f));
        g.drawRoundedRectangle(bounds, 6.0f, 1.5f);
        g.setColour(on ? Sky::White : Sky::Black);
        g.setFont(juce::Font(10.0f).boldened());
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

    addLabel(swellSens, "SENS"); addLabel(swellAttack, "ATK"); addLabel(swellDepth, "DEPTH");
    addLabel(vinylYear, "YEAR"); addLabel(vinylDetune, "DETUNE");
    addLabel(psycheShimmer, "SHIMMER"); addLabel(psycheSpace, "SPACE"); addLabel(psycheMod, "MOD");
    addLabel(psycheWarp, "WARP"); addLabel(psycheMix, "MIX"); addLabel(psycheNotches, "NOTCH"); addLabel(psycheSweep, "SWEEP");
    addLabel(lfoShape, "SHAPE"); addLabel(lfoRate, "RATE"); addLabel(lfoDepth, "DEPTH");
    addLabel(lfoSyncRate, "DIV"); addLabel(lfoPhaseOffset, "PHASE");
    addLabel(masterMix, "MIX"); addLabel(masterGain, "GAIN");

    auto& apvts = processor.apvts;
    aSwellSens    = std::make_unique<SliderAttachment>(apvts, "swellSens",    swellSens);
    aSwellAttack  = std::make_unique<SliderAttachment>(apvts, "swellAttack",  swellAttack);
    aSwellDepth   = std::make_unique<SliderAttachment>(apvts, "swellDepth",   swellDepth);
    aVinylYear    = std::make_unique<SliderAttachment>(apvts, "vinylYear",    vinylYear);
    aVinylDetune  = std::make_unique<SliderAttachment>(apvts, "vinylDetune",  vinylDetune);
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

    initSwimmers();
    startTimerHz(30);
}

AetherEditor::~AetherEditor()
{
    setLookAndFeel(nullptr);
}

// ================================================================
// Swimmers
// ================================================================
void AetherEditor::initSwimmers()
{
    std::mt19937 rng(12345);
    std::uniform_real_distribution<float> yDist(80.0f, 560.0f);
    std::uniform_real_distribution<float> sizeDist(25.0f, 42.0f);
    std::uniform_real_distribution<float> speedDist(0.3f, 1.2f);
    std::uniform_real_distribution<float> phaseDist(0.0f, 6.28f);
    std::uniform_int_distribution<int> typeDist(0, 5);
    std::uniform_int_distribution<int> dirDist(0, 1);

    juce::Colour colors[] = {
        Sky::CrayonRed, Sky::CrayonPink, Sky::CrayonOrange,
        Sky::CrayonGreen, Sky::CrayonPurple, Sky::CrayonTeal
    };

    for (int i = 0; i < 10; ++i)
    {
        Swimmer s;
        s.type = typeDist(rng);
        s.goingRight = dirDist(rng) == 1;
        s.y = yDist(rng);
        s.speed = speedDist(rng);
        s.size = sizeDist(rng);
        s.phaseOffset = phaseDist(rng);
        s.colour = colors[i % 6];
        swimmers.push_back(s);
    }
}

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
    int knobW = 62, knobH = 62;
    int labelH = 14;
    int pad = 6;
    int sectionY = 100;
    int sectionH = 240;
    int sectionW = (W - 50) / 4;

    int sx0 = 15;

    auto placeKnob = [&](juce::Slider& s, int bx, int by) {
        s.setBounds(bx, by, knobW, knobH);
    };

    int knobY1 = sectionY + 45;
    int knobY2 = sectionY + 45 + knobH + labelH + pad;
    int knobGap = knobW + 6;

    // Swell (3 knobs centered)
    int sc = sx0 + sectionW / 2 - knobW * 3 / 2 - 4;
    placeKnob(swellSens, sc, knobY1);
    placeKnob(swellAttack, sc + knobGap, knobY1);
    placeKnob(swellDepth, sc + knobGap * 2, knobY1);
    swellBypass.setBounds(sx0 + 6, sectionY + 8, 34, 24);

    // Vinyl (2 knobs centered)
    int vx = sx0 + sectionW + 5;
    int vc = vx + sectionW / 2 - knobW - 4;
    placeKnob(vinylYear, vc, knobY1);
    placeKnob(vinylDetune, vc + knobGap, knobY1);
    vinylBypass.setBounds(vx + 6, sectionY + 8, 34, 24);

    // Psyche (7 knobs, 2 rows: 4+3)
    int px = sx0 + (sectionW + 5) * 2;
    int pc = px + 4;
    int pGap = knobW + 1;
    placeKnob(psycheShimmer, pc, knobY1);
    placeKnob(psycheSpace, pc + pGap, knobY1);
    placeKnob(psycheMod, pc + pGap * 2, knobY1);
    placeKnob(psycheWarp, pc + pGap * 3, knobY1);
    placeKnob(psycheMix, pc, knobY2);
    placeKnob(psycheNotches, pc + pGap, knobY2);
    placeKnob(psycheSweep, pc + pGap * 2, knobY2);
    psycheBypass.setBounds(px + 6, sectionY + 8, 34, 24);

    // LFO (5 knobs + sync, 2 rows)
    int lx = sx0 + (sectionW + 5) * 3;
    int lc = lx + 8;
    placeKnob(lfoShape, lc, knobY1);
    placeKnob(lfoRate, lc + knobGap, knobY1);
    placeKnob(lfoDepth, lc + knobGap * 2, knobY1);
    placeKnob(lfoSyncRate, lc, knobY2);
    placeKnob(lfoPhaseOffset, lc + knobGap, knobY2);
    lfoSync.setBounds(lc + knobGap * 2, knobY2 + 12, 52, 28);
    lfoBypass.setBounds(lx + 6, sectionY + 8, 34, 24);

    // Master (bottom center)
    int my = sectionY + sectionH + 40;
    int mx = W / 2 - knobGap;
    placeKnob(masterMix, mx, my);
    placeKnob(masterGain, mx + knobGap, my);

    for (auto& lbl : labels)
    {
        if (auto* slider = dynamic_cast<juce::Slider*>(lbl->getAttachedComponent()))
        {
            auto sb = slider->getBounds();
            lbl->setBounds(sb.getX() - 4, sb.getBottom() - 2, sb.getWidth() + 8, labelH);
        }
    }
}

juce::Label& AetherEditor::addLabel(juce::Slider& s, const juce::String& text)
{
    auto lbl = std::make_unique<juce::Label>("", text);
    lbl->setFont(juce::Font(10.0f).boldened());
    lbl->setColour(juce::Label::textColourId, Sky::Black.withAlpha(0.8f));
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
    drawSkyBackground(g);
    drawDoodles(g);
    drawSwimmingCharacters(g);

    int W = getWidth();
    int sectionY = 100;
    int sectionH = 240;
    int sectionW = (W - 50) / 4;
    int sx0 = 15;

    // Section backgrounds (semi-transparent white boxes with crayon borders)
    auto drawSection = [&](int x, int y, int w, int h, juce::Colour borderCol, const juce::String& title)
    {
        auto r = juce::Rectangle<float>((float)x, (float)y, (float)w, (float)h);
        // White translucent fill
        g.setColour(juce::Colour(0x60FFFFFF));
        g.fillRoundedRectangle(r, 10.0f);
        // Thick crayon border
        g.setColour(borderCol);
        g.drawRoundedRectangle(r, 10.0f, 3.0f);
        // Title
        g.setColour(borderCol.darker(0.2f));
        g.setFont(juce::Font(14.0f).boldened());
        g.drawText(title, x + 42, y + 6, w - 48, 20, juce::Justification::left);
    };

    drawSection(sx0, sectionY, sectionW, sectionH, Sky::CrayonPink, "SWELL");
    drawSection(sx0 + sectionW + 5, sectionY, sectionW, sectionH, Sky::CrayonOrange, "VINYL");
    drawSection(sx0 + (sectionW + 5) * 2, sectionY, sectionW, sectionH, Sky::CrayonPurple, "PSYCHE");
    drawSection(sx0 + (sectionW + 5) * 3, sectionY, sectionW, sectionH, Sky::CrayonGreen, "LFO");

    drawTitle(g);

    // Master label
    int my = sectionY + sectionH + 24;
    g.setColour(Sky::Black.withAlpha(0.7f));
    g.setFont(juce::Font(14.0f).boldened());
    g.drawText("MASTER", 0, my, W, 16, juce::Justification::centred);

    // LFO info display
    {
        int lShape = static_cast<int>(lfoShape.getValue());
        int lSyncR = static_cast<int>(lfoSyncRate.getValue());
        bool synced = lfoSync.getToggleState();
        juce::String info = LFOProcessor::shapeName(lShape);
        if (synced)
            info += juce::String(" | ") + LFOProcessor::syncRateName(lSyncR);
        int lfoX = sx0 + (sectionW + 5) * 3;
        g.setColour(Sky::Black.withAlpha(0.5f));
        g.setFont(juce::Font(10.0f));
        g.drawText(info, lfoX, sectionY + sectionH - 18, sectionW, 16, juce::Justification::centred);
    }

    // Version
    g.setColour(Sky::Black.withAlpha(0.2f));
    g.setFont(juce::Font(9.0f));
    g.drawText("v3.0 // aether audio", 0, getHeight() - 14, getWidth() - 8, 12, juce::Justification::centredRight);
}

// ================================================================
// Sky background — bright blue gradient with clouds and sun
// ================================================================
void AetherEditor::drawSkyBackground(juce::Graphics& g)
{
    // Blue sky gradient (lighter at top, slightly darker at bottom)
    juce::ColourGradient skyGrad(Sky::BlueLight, 0.0f, 0.0f,
                                  Sky::Blue, 0.0f, (float)getHeight(), false);
    skyGrad.addColour(0.4, Sky::Blue);
    g.setGradientFill(skyGrad);
    g.fillRect(getLocalBounds());

    // Green grass strip at very bottom
    g.setColour(Sky::CrayonGreen.withAlpha(0.3f));
    g.fillRect(0, getHeight() - 30, getWidth(), 30);
    // Wavy grass line
    juce::Path grassLine;
    grassLine.startNewSubPath(0, (float)(getHeight() - 30));
    for (float x = 0; x <= (float)getWidth(); x += 15.0f)
    {
        float gy = (float)(getHeight() - 30) + std::sin(x * 0.05f + animTime * 0.5f) * 4.0f;
        grassLine.lineTo(x, gy);
    }
    g.setColour(Sky::CrayonGreen.withAlpha(0.5f));
    g.strokePath(grassLine, juce::PathStrokeType(2.5f));

    // Sun (top right, with rays)
    drawSun(g, (float)(getWidth() - 70), 55.0f, 35.0f);

    // Clouds
    drawCloud(g, 60.0f, 25.0f, 70.0f);
    drawCloud(g, 280.0f, 15.0f, 55.0f);
    drawCloud(g, 520.0f, 30.0f, 65.0f);
    drawCloud(g, 750.0f, 20.0f, 50.0f);
}

void AetherEditor::drawCloud(juce::Graphics& g, float x, float y, float w)
{
    float h = w * 0.45f;
    g.setColour(Sky::White.withAlpha(0.85f));
    // 3 overlapping circles = puffy cloud
    g.fillEllipse(x, y + h * 0.2f, w * 0.5f, h * 0.7f);
    g.fillEllipse(x + w * 0.2f, y, w * 0.55f, h * 0.85f);
    g.fillEllipse(x + w * 0.45f, y + h * 0.15f, w * 0.5f, h * 0.7f);
    // Crayon outline
    g.setColour(Sky::BlueDark.withAlpha(0.15f));
    g.drawEllipse(x, y + h * 0.2f, w * 0.5f, h * 0.7f, 1.5f);
    g.drawEllipse(x + w * 0.2f, y, w * 0.55f, h * 0.85f, 1.5f);
    g.drawEllipse(x + w * 0.45f, y + h * 0.15f, w * 0.5f, h * 0.7f, 1.5f);
}

void AetherEditor::drawSun(juce::Graphics& g, float x, float y, float r)
{
    // Rays
    int numRays = 12;
    for (int i = 0; i < numRays; ++i)
    {
        float a = (float)i / (float)numRays * juce::MathConstants<float>::twoPi
                  + animTime * 0.3f;
        float innerR = r * 1.2f;
        float outerR = r * 1.8f + std::sin(animTime * 2.0f + (float)i) * 4.0f;
        g.setColour(Sky::SunYellow.withAlpha(0.4f));
        g.drawLine(x + std::cos(a) * innerR, y + std::sin(a) * innerR,
                   x + std::cos(a) * outerR, y + std::sin(a) * outerR, 2.5f);
    }
    // Sun body
    g.setColour(Sky::SunYellow);
    g.fillEllipse(x - r, y - r, r * 2, r * 2);
    g.setColour(Sky::SunOrange.withAlpha(0.3f));
    g.drawEllipse(x - r, y - r, r * 2, r * 2, 2.0f);
    // Smiley face
    g.setColour(Sky::Black.withAlpha(0.6f));
    g.fillEllipse(x - r * 0.3f, y - r * 0.2f, 4, 4);
    g.fillEllipse(x + r * 0.15f, y - r * 0.2f, 4, 4);
    juce::Path smile;
    smile.addCentredArc(x, y + r * 0.1f, r * 0.3f, r * 0.15f,
                         0.0f, 0.2f, juce::MathConstants<float>::pi - 0.2f, true);
    g.strokePath(smile, juce::PathStrokeType(1.5f));
}

// ================================================================
// Title — rainbow bouncing AETHER
// ================================================================
void AetherEditor::drawTitle(juce::Graphics& g)
{
    juce::String title = "AETHER";
    auto font = juce::Font(48.0f).boldened();
    g.setFont(font);

    float titleW = font.getStringWidthFloat(title);
    float startX = ((float)getWidth() - titleW) * 0.5f;
    float y = 42.0f;

    juce::Colour rainbow[] = {
        Sky::CrayonRed, Sky::CrayonOrange, Sky::CrayonYellow,
        Sky::CrayonGreen, Sky::CrayonTeal, Sky::CrayonPurple
    };

    for (int i = 0; i < title.length(); ++i)
    {
        juce::String ch = title.substring(i, i + 1);
        float cw = font.getStringWidthFloat(ch);
        float bounce = std::sin(animTime * 2.5f + i * 0.8f) * 6.0f;

        // Dark outline/shadow for readability on blue sky
        g.setColour(Sky::Black.withAlpha(0.3f));
        g.drawText(ch, (int)(startX + 2), (int)(y + bounce + 2), (int)cw + 2, 55,
                   juce::Justification::left);
        // White outline
        for (int dx = -1; dx <= 1; dx++)
            for (int dy = -1; dy <= 1; dy++)
            {
                g.setColour(Sky::White.withAlpha(0.6f));
                g.drawText(ch, (int)(startX + dx), (int)(y + bounce + dy), (int)cw + 2, 55,
                           juce::Justification::left);
            }

        g.setColour(rainbow[i % 6]);
        g.drawText(ch, (int)startX, (int)(y + bounce), (int)cw + 2, 55,
                   juce::Justification::left);

        startX += cw;
    }

    g.setColour(Sky::White.withAlpha(0.7f));
    g.setFont(juce::Font(11.0f).italicised());
    g.drawText("psychedelic guitar processor", 0, 82, getWidth(), 14, juce::Justification::centred);
}

// ================================================================
// Static doodles (crayon drawings scattered on the sky)
// ================================================================
void AetherEditor::drawDoodles(juce::Graphics& g)
{
    // Small static crayon doodles in the margins/corners -- like a kid decorated the panel
    // Little stars
    g.setColour(Sky::CrayonYellow.withAlpha(0.5f));
    drawStar4(g, 30, 570, 8);
    drawStar4(g, 990, 580, 6);
    drawStar4(g, 500, 560, 7);
    drawStar4(g, 120, 590, 5);
    drawStar4(g, 870, 560, 9);

    // Music notes (simple crayon style)
    auto drawNote = [&](float nx, float ny, juce::Colour c) {
        g.setColour(c.withAlpha(0.35f));
        g.fillEllipse(nx, ny, 8, 6);
        g.drawLine(nx + 7, ny + 3, nx + 7, ny - 14, 2.0f);
        g.drawLine(nx + 7, ny - 14, nx + 14, ny - 11, 2.0f);
    };
    drawNote(45, 400, Sky::CrayonPurple);
    drawNote(970, 420, Sky::CrayonPink);
    drawNote(200, 550, Sky::CrayonOrange);
    drawNote(820, 540, Sky::CrayonGreen);

    // Tiny hearts
    auto drawHeart = [&](float hx, float hy, float hs, juce::Colour c) {
        g.setColour(c.withAlpha(0.3f));
        g.fillEllipse(hx - hs * 0.5f, hy - hs * 0.3f, hs * 0.55f, hs * 0.5f);
        g.fillEllipse(hx, hy - hs * 0.3f, hs * 0.55f, hs * 0.5f);
        juce::Path tri;
        tri.startNewSubPath(hx - hs * 0.5f, hy);
        tri.lineTo(hx + hs * 0.55f, hy);
        tri.lineTo(hx + hs * 0.025f, hy + hs * 0.5f);
        tri.closeSubPath();
        g.fillPath(tri);
    };
    drawHeart(80, 480, 14, Sky::CrayonRed);
    drawHeart(940, 380, 12, Sky::CrayonPink);
}

// ================================================================
// Swimming characters
// ================================================================
void AetherEditor::drawSwimmingCharacters(juce::Graphics& g)
{
    float totalWidth = 1220.0f;

    for (auto& s : swimmers)
    {
        float speed = s.goingRight ? s.speed : -s.speed;
        float rawX;
        if (s.goingRight)
        {
            rawX = std::fmod(animTime * speed * 30.0f + s.phaseOffset * 100.0f, totalWidth) - 100.0f;
        }
        else
        {
            rawX = 1120.0f - std::fmod(animTime * std::abs(speed) * 30.0f + s.phaseOffset * 100.0f, totalWidth);
        }

        float bobY = s.y + std::sin(animTime * 1.5f + s.phaseOffset) * 10.0f;
        float phase = animTime * 2.0f + s.phaseOffset;

        switch (s.type)
        {
            case 0: drawMushroom(g, rawX, bobY, s.size, phase, s.colour); break;
            case 1: drawAlien(g, rawX, bobY, s.size, phase, s.colour); break;
            case 2: drawFlower(g, rawX, bobY, s.size, phase, s.colour); break;
            case 3: drawGhost(g, rawX, bobY, s.size, phase); break;
            case 4: drawBoombox(g, rawX, bobY, s.size, phase); break;
            case 5: drawCassette(g, rawX, bobY, s.size, phase); break;
        }
    }
}

// ================================================================
// Character: Mushroom (psychedelic, crayon style)
// ================================================================
void AetherEditor::drawMushroom(juce::Graphics& g, float x, float y, float size,
                                 float phase, juce::Colour cap)
{
    float s = size;
    float wobble = std::sin(phase * 2.0f) * 2.0f;

    // Stem
    g.setColour(Sky::CloudWhite);
    g.fillRect(x - s * 0.12f + wobble, y, s * 0.24f, s * 0.35f);
    g.setColour(Sky::Black.withAlpha(0.4f));
    g.drawRect(x - s * 0.12f + wobble, y, s * 0.24f, s * 0.35f, 1.5f);

    // Cap (half circle)
    juce::Path capPath;
    capPath.addCentredArc(x + wobble, y, s * 0.4f, s * 0.28f, 0.0f,
                           juce::MathConstants<float>::pi, juce::MathConstants<float>::twoPi, true);
    capPath.closeSubPath();
    g.setColour(cap);
    g.fillPath(capPath);
    g.setColour(Sky::Black.withAlpha(0.4f));
    g.strokePath(capPath, juce::PathStrokeType(2.0f));

    // Polka dots on cap
    g.setColour(Sky::White.withAlpha(0.7f));
    g.fillEllipse(x - s * 0.15f + wobble, y - s * 0.18f, s * 0.1f, s * 0.08f);
    g.fillEllipse(x + s * 0.08f + wobble, y - s * 0.22f, s * 0.08f, s * 0.07f);
    g.fillEllipse(x + wobble - s * 0.02f, y - s * 0.12f, s * 0.06f, s * 0.05f);

    // Face (cute!)
    g.setColour(Sky::Black.withAlpha(0.6f));
    g.fillEllipse(x - s * 0.06f + wobble, y + s * 0.08f, 3, 3);
    g.fillEllipse(x + s * 0.04f + wobble, y + s * 0.08f, 3, 3);
    // Smile
    juce::Path smile;
    smile.addCentredArc(x + wobble, y + s * 0.16f, s * 0.06f, s * 0.03f,
                         0.0f, 0.2f, juce::MathConstants<float>::pi - 0.2f, true);
    g.strokePath(smile, juce::PathStrokeType(1.2f));
}

// ================================================================
// Character: Alien (3-eyed, crayon style)
// ================================================================
void AetherEditor::drawAlien(juce::Graphics& g, float x, float y, float size,
                              float phase, juce::Colour body)
{
    float s = size;
    float bob = std::sin(phase * 1.5f) * 3.0f;

    // Body (oval)
    g.setColour(body.withAlpha(0.7f));
    g.fillEllipse(x - s * 0.22f, y - s * 0.15f + bob, s * 0.44f, s * 0.5f);
    g.setColour(Sky::Black.withAlpha(0.4f));
    g.drawEllipse(x - s * 0.22f, y - s * 0.15f + bob, s * 0.44f, s * 0.5f, 1.8f);

    // Head (bigger oval on top)
    g.setColour(body.withAlpha(0.8f));
    g.fillEllipse(x - s * 0.25f, y - s * 0.42f + bob, s * 0.5f, s * 0.35f);
    g.setColour(Sky::Black.withAlpha(0.4f));
    g.drawEllipse(x - s * 0.25f, y - s * 0.42f + bob, s * 0.5f, s * 0.35f, 1.8f);

    // 3 eyes
    float eyeY = y - s * 0.3f + bob;
    g.setColour(Sky::White);
    g.fillEllipse(x - s * 0.18f, eyeY, s * 0.1f, s * 0.08f);
    g.fillEllipse(x - s * 0.04f, eyeY - s * 0.02f, s * 0.1f, s * 0.08f);
    g.fillEllipse(x + s * 0.1f, eyeY, s * 0.1f, s * 0.08f);
    g.setColour(Sky::Black);
    g.fillEllipse(x - s * 0.15f, eyeY + s * 0.01f, 3, 3);
    g.fillEllipse(x, eyeY - s * 0.01f, 3, 3);
    g.fillEllipse(x + s * 0.13f, eyeY + s * 0.01f, 3, 3);

    // Antenna
    g.setColour(body.darker(0.2f));
    g.drawLine(x, y - s * 0.42f + bob, x - s * 0.1f, y - s * 0.58f + bob, 1.5f);
    g.drawLine(x, y - s * 0.42f + bob, x + s * 0.1f, y - s * 0.58f + bob, 1.5f);
    g.setColour(Sky::CrayonYellow);
    g.fillEllipse(x - s * 0.1f - 3, y - s * 0.58f + bob - 3, 6, 6);
    g.fillEllipse(x + s * 0.1f - 3, y - s * 0.58f + bob - 3, 6, 6);

    // Little legs
    g.setColour(body.darker(0.1f));
    float legY = y + s * 0.32f + bob;
    g.drawLine(x - s * 0.08f, legY - s * 0.05f, x - s * 0.15f, legY + s * 0.1f, 1.8f);
    g.drawLine(x + s * 0.08f, legY - s * 0.05f, x + s * 0.15f, legY + s * 0.1f, 1.8f);
}

// ================================================================
// Character: Flower (dancing)
// ================================================================
void AetherEditor::drawFlower(juce::Graphics& g, float x, float y, float size,
                               float phase, juce::Colour petals)
{
    float s = size;
    float sway = std::sin(phase * 1.8f) * 4.0f;

    // Stem
    g.setColour(Sky::CrayonGreen.withAlpha(0.7f));
    g.drawLine(x + sway * 0.3f, y + s * 0.15f, x, y + s * 0.55f, 2.5f);
    // Leaves
    g.setColour(Sky::CrayonGreen.withAlpha(0.5f));
    g.fillEllipse(x - s * 0.15f, y + s * 0.3f, s * 0.18f, s * 0.08f);
    g.fillEllipse(x + s * 0.02f, y + s * 0.38f, s * 0.16f, s * 0.07f);

    // Petals (circle of ellipses)
    int numPetals = 6;
    float petalR = s * 0.18f;
    for (int i = 0; i < numPetals; ++i)
    {
        float a = (float)i / (float)numPetals * juce::MathConstants<float>::twoPi + phase * 0.3f;
        float px = x + sway * 0.3f + std::cos(a) * petalR;
        float py = y + std::sin(a) * petalR;
        g.setColour(petals.withAlpha(0.6f));
        g.fillEllipse(px - s * 0.09f, py - s * 0.07f, s * 0.18f, s * 0.14f);
    }

    // Center
    g.setColour(Sky::CrayonYellow);
    g.fillEllipse(x + sway * 0.3f - s * 0.08f, y - s * 0.08f, s * 0.16f, s * 0.16f);
    g.setColour(Sky::Black.withAlpha(0.4f));
    g.drawEllipse(x + sway * 0.3f - s * 0.08f, y - s * 0.08f, s * 0.16f, s * 0.16f, 1.2f);

    // Face in center
    g.setColour(Sky::Black.withAlpha(0.5f));
    g.fillEllipse(x + sway * 0.3f - 3, y - 2, 2.5f, 2.5f);
    g.fillEllipse(x + sway * 0.3f + 2, y - 2, 2.5f, 2.5f);
}

// ================================================================
// Character: Ghost (cute, blushing)
// ================================================================
void AetherEditor::drawGhost(juce::Graphics& g, float x, float y, float size, float phase)
{
    float s = size;
    float float_ = std::sin(phase * 2.0f) * 4.0f;

    // Ghost body
    juce::Path body;
    body.startNewSubPath(x - s * 0.25f, y + s * 0.3f + float_);
    body.lineTo(x - s * 0.25f, y - s * 0.1f + float_);
    body.addCentredArc(x, y - s * 0.1f + float_, s * 0.25f, s * 0.2f,
                        0.0f, juce::MathConstants<float>::pi, juce::MathConstants<float>::twoPi, false);
    body.lineTo(x + s * 0.25f, y + s * 0.3f + float_);
    // Wavy bottom
    body.lineTo(x + s * 0.15f, y + s * 0.22f + float_);
    body.lineTo(x + s * 0.05f, y + s * 0.3f + float_);
    body.lineTo(x - s * 0.05f, y + s * 0.22f + float_);
    body.lineTo(x - s * 0.15f, y + s * 0.3f + float_);
    body.closeSubPath();

    g.setColour(Sky::White.withAlpha(0.85f));
    g.fillPath(body);
    g.setColour(Sky::Black.withAlpha(0.3f));
    g.strokePath(body, juce::PathStrokeType(1.8f));

    // Eyes (big and cute)
    g.setColour(Sky::Black);
    g.fillEllipse(x - s * 0.1f, y - s * 0.05f + float_, 5, 6);
    g.fillEllipse(x + s * 0.06f, y - s * 0.05f + float_, 5, 6);

    // Blush spots
    g.setColour(Sky::CrayonPink.withAlpha(0.4f));
    g.fillEllipse(x - s * 0.18f, y + s * 0.04f + float_, s * 0.1f, s * 0.06f);
    g.fillEllipse(x + s * 0.1f, y + s * 0.04f + float_, s * 0.1f, s * 0.06f);

    // Tiny mouth
    g.setColour(Sky::Black.withAlpha(0.4f));
    g.fillEllipse(x - 2, y + s * 0.1f + float_, 4, 3);
}

// ================================================================
// Character: Boombox (crayon style, like Turnt's doodles)
// ================================================================
void AetherEditor::drawBoombox(juce::Graphics& g, float x, float y, float size, float phase)
{
    float s = size;
    float bounce = std::sin(phase * 3.0f) * 2.0f;

    // Body rectangle
    g.setColour(Sky::CrayonYellow.withAlpha(0.7f));
    g.fillRoundedRectangle(x - s * 0.35f, y - s * 0.15f + bounce, s * 0.7f, s * 0.35f, 4.0f);
    g.setColour(Sky::Black.withAlpha(0.5f));
    g.drawRoundedRectangle(x - s * 0.35f, y - s * 0.15f + bounce, s * 0.7f, s * 0.35f, 4.0f, 2.0f);

    // Speaker circles
    g.setColour(Sky::Black.withAlpha(0.4f));
    float spkR = s * 0.08f;
    g.drawEllipse(x - s * 0.2f - spkR, y - spkR * 0.5f + bounce, spkR * 2, spkR * 2, 1.8f);
    g.drawEllipse(x + s * 0.12f, y - spkR * 0.5f + bounce, spkR * 2, spkR * 2, 1.8f);
    // Inner speaker
    g.fillEllipse(x - s * 0.2f - spkR * 0.3f, y + spkR * 0.2f + bounce, spkR * 0.6f, spkR * 0.6f);
    g.fillEllipse(x + s * 0.12f + spkR * 0.7f, y + spkR * 0.2f + bounce, spkR * 0.6f, spkR * 0.6f);

    // Tape window in center
    g.setColour(Sky::CrayonOrange.withAlpha(0.5f));
    g.fillRect(x - s * 0.06f, y - s * 0.08f + bounce, s * 0.12f, s * 0.08f);
    g.setColour(Sky::Black.withAlpha(0.3f));
    g.drawRect(x - s * 0.06f, y - s * 0.08f + bounce, s * 0.12f, s * 0.08f, 1.0f);

    // Handle on top
    g.setColour(Sky::Black.withAlpha(0.4f));
    juce::Path handle;
    handle.addCentredArc(x, y - s * 0.15f + bounce, s * 0.15f, s * 0.08f,
                          0.0f, juce::MathConstants<float>::pi, juce::MathConstants<float>::twoPi, true);
    g.strokePath(handle, juce::PathStrokeType(2.0f));

    // Music notes coming out
    float noteX = x + s * 0.35f + std::sin(phase) * 5;
    float noteY = y - s * 0.1f + bounce - std::fmod(animTime * 15.0f, 30.0f);
    g.setColour(Sky::CrayonPurple.withAlpha(0.4f));
    g.fillEllipse(noteX, noteY, 5, 4);
    g.drawLine(noteX + 4, noteY + 2, noteX + 4, noteY - 8, 1.5f);
}

// ================================================================
// Character: Cassette (retro, crayon style)
// ================================================================
void AetherEditor::drawCassette(juce::Graphics& g, float x, float y, float size, float phase)
{
    float s = size;
    float tilt = std::sin(phase * 1.5f) * 0.05f;
    auto xf = juce::AffineTransform::rotation(tilt, x, y);

    // Body
    g.setColour(Sky::CrayonTeal.withAlpha(0.6f));
    juce::Path body;
    body.addRoundedRectangle(x - s * 0.35f, y - s * 0.18f, s * 0.7f, s * 0.36f, 5.0f);
    body.applyTransform(xf);
    g.fillPath(body);

    juce::Path outline;
    outline.addRoundedRectangle(x - s * 0.35f, y - s * 0.18f, s * 0.7f, s * 0.36f, 5.0f);
    outline.applyTransform(xf);
    g.setColour(Sky::Black.withAlpha(0.5f));
    g.strokePath(outline, juce::PathStrokeType(2.0f));

    // Tape reels (two circles)
    float reelR = s * 0.07f;
    float spinAngle = animTime * 3.0f;
    for (int side = -1; side <= 1; side += 2)
    {
        float rx = x + side * s * 0.13f;
        float ry = y - s * 0.02f;
        g.setColour(Sky::White.withAlpha(0.8f));
        g.fillEllipse(rx - reelR, ry - reelR, reelR * 2, reelR * 2);
        g.setColour(Sky::Black.withAlpha(0.4f));
        g.drawEllipse(rx - reelR, ry - reelR, reelR * 2, reelR * 2, 1.2f);
        // Spokes
        for (int sp = 0; sp < 3; ++sp)
        {
            float a = spinAngle + (float)sp * juce::MathConstants<float>::twoPi / 3.0f;
            g.drawLine(rx, ry, rx + std::cos(a) * reelR * 0.7f, ry + std::sin(a) * reelR * 0.7f, 1.0f);
        }
    }

    // Label strip
    g.setColour(Sky::CrayonYellow.withAlpha(0.5f));
    g.fillRect(x - s * 0.25f, y - s * 0.16f, s * 0.5f, s * 0.08f);
    g.setColour(Sky::Black.withAlpha(0.3f));
    g.setFont(juce::Font(7.0f));
    g.drawText("AETHER", (int)(x - s * 0.2f), (int)(y - s * 0.16f), (int)(s * 0.4f), (int)(s * 0.08f),
               juce::Justification::centred);
}

// ================================================================
// Star helper (4-point)
// ================================================================
void AetherEditor::drawStar4(juce::Graphics& g, float cx, float cy, float size)
{
    int points = 4;
    float outerR = size;
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
