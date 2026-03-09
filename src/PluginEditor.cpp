#include "PluginEditor.h"
#include "dsp/LFOProcessor.h"
#include <cmath>

// ================================================================
// Colour palette — crayon on metal
// ================================================================
namespace Pedal
{
    const auto Metal       = juce::Colour(0xFF3A3A42);   // dark brushed metal
    const auto MetalLight  = juce::Colour(0xFF555560);
    const auto MetalEdge   = juce::Colour(0xFF222228);
    const auto Cream       = juce::Colour(0xFFFFF8E7);
    const auto Pink        = juce::Colour(0xFFFF69B4);
    const auto HotPink     = juce::Colour(0xFFFF1493);
    const auto Purple      = juce::Colour(0xFF9B59B6);
    const auto Blue        = juce::Colour(0xFF3498DB);
    const auto Green       = juce::Colour(0xFF2ECC71);
    const auto Orange      = juce::Colour(0xFFFF8C42);
    const auto Yellow      = juce::Colour(0xFFFFD700);
    const auto Red         = juce::Colour(0xFFFF6B6B);
    const auto Teal        = juce::Colour(0xFF00CEC9);
    const auto White       = juce::Colour(0xFFFFFFFF);
    const auto CrayonPink  = juce::Colour(0xFFFF85A2);
    const auto CrayonBlue  = juce::Colour(0xFF85C1FF);
    const auto CrayonGreen = juce::Colour(0xFF85FFB0);
    const auto CrayonPurple= juce::Colour(0xFFCC85FF);
    const auto CrayonYellow= juce::Colour(0xFFFFE066);
    const auto Outline     = juce::Colour(0xFFFFFFDD);   // crayon white-ish on dark bg
    const auto DarkText    = juce::Colour(0xFFFFFFFF);
    const auto SectionPink = juce::Colour(0x30FF69B4);
    const auto SectionBlue = juce::Colour(0x303498DB);
    const auto SectionPurple = juce::Colour(0x309B59B6);
    const auto SectionGreen  = juce::Colour(0x302ECC71);
}

// ================================================================
// Look and Feel — pedal style
// ================================================================
AetherEditor::PedalLookAndFeel::PedalLookAndFeel()
{
    setColour(juce::Label::textColourId, Pedal::White);
}

void AetherEditor::PedalLookAndFeel::drawRotarySlider(
    juce::Graphics& g, int x, int y, int w, int h,
    float sliderPos, float rotaryStartAngle, float rotaryEndAngle, juce::Slider&)
{
    auto bounds = juce::Rectangle<float>((float)x, (float)y, (float)w, (float)h);
    auto radius = juce::jmin(bounds.getWidth(), bounds.getHeight()) / 2.0f - 4.0f;
    auto centre = bounds.getCentre();
    auto angle = rotaryStartAngle + sliderPos * (rotaryEndAngle - rotaryStartAngle);

    // Knob body — dark circle with metallic look
    g.setColour(Pedal::MetalLight);
    g.fillEllipse(centre.x - radius, centre.y - radius, radius * 2.0f, radius * 2.0f);

    // Crayon-drawn ring (thick, slightly rough)
    juce::Path arcBg;
    arcBg.addCentredArc(centre.x, centre.y, radius - 2.0f, radius - 2.0f,
                         0.0f, rotaryStartAngle, rotaryEndAngle, true);
    g.setColour(Pedal::White.withAlpha(0.15f));
    g.strokePath(arcBg, juce::PathStrokeType(4.0f));

    // Value arc — hot pink crayon
    juce::Path arcVal;
    arcVal.addCentredArc(centre.x, centre.y, radius - 2.0f, radius - 2.0f,
                          0.0f, rotaryStartAngle, angle, true);
    g.setColour(Pedal::HotPink);
    g.strokePath(arcVal, juce::PathStrokeType(4.0f, juce::PathStrokeType::curved,
                                               juce::PathStrokeType::rounded));

    // Inner circle
    float innerR = radius * 0.52f;
    g.setColour(Pedal::Metal);
    g.fillEllipse(centre.x - innerR, centre.y - innerR, innerR * 2.0f, innerR * 2.0f);

    // Crayon outline
    g.setColour(Pedal::Outline.withAlpha(0.5f));
    g.drawEllipse(centre.x - radius, centre.y - radius, radius * 2.0f, radius * 2.0f, 2.5f);

    // Pointer line
    juce::Path pointer;
    auto pointerLen = radius * 0.72f;
    pointer.addRectangle(-1.5f, -pointerLen, 3.0f, pointerLen * 0.42f);
    pointer.applyTransform(juce::AffineTransform::rotation(angle).translated(centre.x, centre.y));
    g.setColour(Pedal::Yellow);
    g.fillPath(pointer);
}

void AetherEditor::PedalLookAndFeel::drawToggleButton(
    juce::Graphics& g, juce::ToggleButton& button, bool, bool)
{
    auto bounds = button.getLocalBounds().toFloat().reduced(2.0f);
    bool on = button.getToggleState();
    bool isBypass = button.getButtonText().length() == 1;

    if (isBypass)
    {
        // LED-style: green=active, red=bypassed
        g.setColour(on ? Pedal::Red.withAlpha(0.6f) : Pedal::Green.withAlpha(0.7f));
        g.fillRoundedRectangle(bounds, 5.0f);
        g.setColour(Pedal::Outline.withAlpha(0.4f));
        g.drawRoundedRectangle(bounds, 5.0f, 1.5f);
        g.setColour(Pedal::White);
        g.setFont(juce::Font(11.0f).boldened());
        g.drawText(on ? "OFF" : "ON", bounds, juce::Justification::centred);
    }
    else
    {
        g.setColour(on ? Pedal::Teal.withAlpha(0.7f) : Pedal::MetalLight);
        g.fillRoundedRectangle(bounds, 5.0f);
        g.setColour(Pedal::Outline.withAlpha(0.4f));
        g.drawRoundedRectangle(bounds, 5.0f, 1.5f);
        g.setColour(Pedal::White);
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
    setLookAndFeel(&pedalLnf);
    setSize(1020, 620);

    auto setupKnob = [&](juce::Slider& s) {
        s.setSliderStyle(juce::Slider::RotaryHorizontalVerticalDrag);
        s.setTextBoxStyle(juce::Slider::NoTextBox, false, 0, 0);
        addAndMakeVisible(s);
    };

    // Swell
    setupKnob(swellSens); setupKnob(swellAttack); setupKnob(swellDepth);
    // Vinyl (year + detune only)
    setupKnob(vinylYear); setupKnob(vinylDetune);
    // Psyche
    setupKnob(psycheShimmer); setupKnob(psycheSpace); setupKnob(psycheMod);
    setupKnob(psycheWarp); setupKnob(psycheMix); setupKnob(psycheNotches); setupKnob(psycheSweep);
    // LFO
    setupKnob(lfoShape); setupKnob(lfoRate); setupKnob(lfoDepth);
    setupKnob(lfoSyncRate); setupKnob(lfoPhaseOffset);
    // Master
    setupKnob(masterMix); setupKnob(masterGain);

    // Toggles
    for (auto* b : { &swellBypass, &vinylBypass, &psycheBypass, &lfoBypass, &lfoSync })
        addAndMakeVisible(*b);

    // Labels
    addLabel(swellSens, "SENS"); addLabel(swellAttack, "ATK"); addLabel(swellDepth, "DEPTH");
    addLabel(vinylYear, "YEAR"); addLabel(vinylDetune, "DETUNE");
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
// Swimmers + stars
// ================================================================
void AetherEditor::initSwimmers()
{
    std::mt19937 rng(54321);
    std::uniform_real_distribution<float> yDist(40.0f, 580.0f);
    std::uniform_real_distribution<float> sizeDist(28.0f, 50.0f);
    std::uniform_real_distribution<float> speedDist(0.4f, 1.8f);
    std::uniform_real_distribution<float> phaseDist(0.0f, 6.28f);
    std::uniform_int_distribution<int> typeDist(0, 2);
    std::uniform_int_distribution<int> dirDist(0, 1);

    juce::Colour dressColors[] = {
        Pedal::Pink, Pedal::CrayonPurple, Pedal::CrayonBlue,
        Pedal::CrayonGreen, Pedal::HotPink, Pedal::CrayonYellow
    };

    for (int i = 0; i < 8; ++i)
    {
        Swimmer s;
        s.type = typeDist(rng);
        s.goingRight = dirDist(rng) == 1;
        s.startX = s.goingRight ? -80.0f : 1100.0f;
        s.y = yDist(rng);
        s.speed = speedDist(rng);
        s.size = sizeDist(rng);
        s.phaseOffset = phaseDist(rng);
        s.colour = dressColors[i % 6];
        swimmers.push_back(s);
    }

    // Background sparkle stars
    std::uniform_real_distribution<float> xDist(10.0f, 1010.0f);
    std::uniform_real_distribution<float> starSizeDist(2.0f, 5.0f);
    std::uniform_real_distribution<float> starSpeedDist(1.5f, 4.0f);
    for (int i = 0; i < 30; ++i)
    {
        BgStar st;
        st.x = xDist(rng);
        st.y = yDist(rng);
        st.phase = phaseDist(rng);
        st.speed = starSpeedDist(rng);
        st.size = starSizeDist(rng);
        bgStars.push_back(st);
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
    int sectionY = 85;
    int sectionH = 240;
    int sectionW = (W - 50) / 4;

    int sx0 = 15;
    auto swell  = juce::Rectangle<int>(sx0, sectionY, sectionW, sectionH);
    auto vinyl  = juce::Rectangle<int>(sx0 + sectionW + 5, sectionY, sectionW, sectionH);
    auto psyche = juce::Rectangle<int>(sx0 + (sectionW + 5) * 2, sectionY, sectionW, sectionH);
    auto lfoSec = juce::Rectangle<int>(sx0 + (sectionW + 5) * 3, sectionY, sectionW, sectionH);

    auto placeKnob = [&](juce::Slider& s, int bx, int by) {
        s.setBounds(bx, by, knobW, knobH);
    };

    int knobY1 = sectionY + 42;
    int knobY2 = sectionY + 42 + knobH + labelH + pad;
    int knobGap = knobW + 4;

    // Swell (3 knobs, single row, centered)
    int sc = swell.getCentreX() - knobW * 3 / 2 - 2;
    placeKnob(swellSens, sc, knobY1);
    placeKnob(swellAttack, sc + knobGap, knobY1);
    placeKnob(swellDepth, sc + knobGap * 2, knobY1);
    swellBypass.setBounds(swell.getX() + 4, swell.getY() + 6, 32, 22);

    // Vinyl (2 knobs, centered)
    int vc = vinyl.getCentreX() - knobW - 2;
    placeKnob(vinylYear, vc, knobY1);
    placeKnob(vinylDetune, vc + knobGap, knobY1);
    vinylBypass.setBounds(vinyl.getX() + 4, vinyl.getY() + 6, 32, 22);

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
    psycheBypass.setBounds(psyche.getX() + 4, psyche.getY() + 6, 32, 22);

    // LFO (5 knobs + sync, 2 rows)
    int lc = lfoSec.getX() + 8;
    placeKnob(lfoShape, lc, knobY1);
    placeKnob(lfoRate, lc + knobGap, knobY1);
    placeKnob(lfoDepth, lc + knobGap * 2, knobY1);
    placeKnob(lfoSyncRate, lc, knobY2);
    placeKnob(lfoPhaseOffset, lc + knobGap, knobY2);
    lfoSync.setBounds(lc + knobGap * 2, knobY2 + 10, 50, 28);
    lfoBypass.setBounds(lfoSec.getX() + 4, lfoSec.getY() + 6, 32, 22);

    // Master (bottom center)
    int my = sectionY + sectionH + 30;
    int mx = W / 2 - knobGap;
    placeKnob(masterMix, mx, my);
    placeKnob(masterGain, mx + knobGap, my);

    // Update label positions
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
    lbl->setColour(juce::Label::textColourId, Pedal::White.withAlpha(0.8f));
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
    drawPedalBackground(g);

    int W = getWidth();
    int sectionY = 85;
    int sectionH = 240;
    int sectionW = (W - 50) / 4;
    int sx0 = 15;

    drawSectionBox(g, {sx0, sectionY, sectionW, sectionH}, Pedal::SectionPink, "SWELL");
    drawSectionBox(g, {sx0 + sectionW + 5, sectionY, sectionW, sectionH}, Pedal::SectionBlue, "VINYL");
    drawSectionBox(g, {sx0 + (sectionW + 5) * 2, sectionY, sectionW, sectionH}, Pedal::SectionPurple, "PSYCHE");
    drawSectionBox(g, {sx0 + (sectionW + 5) * 3, sectionY, sectionW, sectionH}, Pedal::SectionGreen, "LFO");

    // Crayon scribbles/doodles on the pedal surface (decorative)
    drawCrayonScribble(g, 20.0f, 350.0f, 80.0f, 40.0f, Pedal::CrayonPink, 111);
    drawCrayonScribble(g, 920.0f, 370.0f, 70.0f, 35.0f, Pedal::CrayonBlue, 222);
    drawCrayonScribble(g, 450.0f, 560.0f, 90.0f, 30.0f, Pedal::CrayonGreen, 333);
    drawCrayonScribble(g, 750.0f, 345.0f, 60.0f, 50.0f, Pedal::CrayonYellow, 444);
    drawCrayonScribble(g, 150.0f, 555.0f, 70.0f, 25.0f, Pedal::CrayonPurple, 555);

    // Background sparkle stars
    for (auto& st : bgStars)
    {
        float alpha = 0.2f + 0.5f * (0.5f + 0.5f * std::sin(animTime * st.speed + st.phase));
        g.setColour(Pedal::Yellow.withAlpha(alpha * 0.5f));
        drawStar(g, st.x, st.y, st.size, alpha);
    }

    // Swimming characters (drawn on top of background, behind controls)
    drawSwimmingCharacters(g);

    drawTitle(g);

    // Master label
    int my = sectionY + sectionH + 16;
    g.setColour(Pedal::White.withAlpha(0.6f));
    g.setFont(juce::Font(13.0f).boldened());
    g.drawText("MASTER", 0, my, W, 16, juce::Justification::centred);

    // LFO info display
    {
        int lShape = static_cast<int>(lfoShape.getValue());
        int lSync = static_cast<int>(lfoSyncRate.getValue());
        bool synced = lfoSync.getToggleState();
        juce::String info = LFOProcessor::shapeName(lShape);
        if (synced)
            info += juce::String(" | ") + LFOProcessor::syncRateName(lSync);
        int lfoX = sx0 + (sectionW + 5) * 3;
        g.setColour(Pedal::White.withAlpha(0.6f));
        g.setFont(juce::Font(10.0f));
        g.drawText(info, lfoX, sectionY + sectionH - 18, sectionW, 16, juce::Justification::centred);
    }

    // Version
    g.setColour(Pedal::White.withAlpha(0.25f));
    g.setFont(juce::Font(9.0f));
    g.drawText("v3.0 // artemis", 0, getHeight() - 14, getWidth() - 8, 12, juce::Justification::centredRight);
}

// ================================================================
// Pedal background (dark brushed metal with crayon doodles)
// ================================================================
void AetherEditor::drawPedalBackground(juce::Graphics& g)
{
    auto bounds = getLocalBounds().toFloat();

    // Dark brushed metal base
    g.setColour(Pedal::Metal);
    g.fillRect(bounds);

    // Subtle horizontal brushed-metal texture
    std::mt19937 texRng(99999);
    std::uniform_real_distribution<float> texDist(0.0f, 1.0f);
    for (int y = 0; y < getHeight(); y += 2)
    {
        float alpha = texDist(texRng) * 0.06f;
        g.setColour(Pedal::White.withAlpha(alpha));
        g.drawHorizontalLine(y, 0.0f, (float)getWidth());
    }

    // Pedal outline (thick border like stamped metal)
    g.setColour(Pedal::MetalEdge);
    g.drawRect(bounds.reduced(2.0f), 4.0f);
    g.setColour(Pedal::MetalLight.withAlpha(0.3f));
    g.drawRect(bounds.reduced(6.0f), 1.0f);

    // Screw holes in corners (pedal detail)
    float screwR = 6.0f;
    juce::Colour screwCol = Pedal::MetalEdge;
    float inset = 14.0f;
    for (auto& pos : {
        juce::Point<float>(inset, inset),
        juce::Point<float>((float)getWidth() - inset, inset),
        juce::Point<float>(inset, (float)getHeight() - inset),
        juce::Point<float>((float)getWidth() - inset, (float)getHeight() - inset)
    })
    {
        g.setColour(screwCol);
        g.fillEllipse(pos.x - screwR, pos.y - screwR, screwR * 2, screwR * 2);
        g.setColour(Pedal::MetalLight.withAlpha(0.5f));
        g.drawEllipse(pos.x - screwR, pos.y - screwR, screwR * 2, screwR * 2, 1.0f);
        // Phillips head cross
        g.setColour(Pedal::MetalLight.withAlpha(0.3f));
        g.drawLine(pos.x - 3, pos.y, pos.x + 3, pos.y, 1.0f);
        g.drawLine(pos.x, pos.y - 3, pos.x, pos.y + 3, 1.0f);
    }
}

// ================================================================
// Title — rainbow bouncing AETHER
// ================================================================
void AetherEditor::drawTitle(juce::Graphics& g)
{
    juce::String title = "AETHER";
    auto font = juce::Font(44.0f).boldened();
    g.setFont(font);

    float titleW = font.getStringWidthFloat(title);
    float startX = ((float)getWidth() - titleW) * 0.5f;
    float y = 18.0f;

    juce::Colour rainbow[] = { Pedal::Red, Pedal::Orange, Pedal::Yellow,
                                Pedal::Green, Pedal::Blue, Pedal::Purple };

    for (int i = 0; i < title.length(); ++i)
    {
        juce::String ch = title.substring(i, i + 1);
        float cw = font.getStringWidthFloat(ch);
        float bounce = std::sin(animTime * 2.5f + i * 0.8f) * 5.0f;

        // Glow
        g.setColour(rainbow[i % 6].withAlpha(0.2f));
        g.drawText(ch, (int)(startX - 1), (int)(y + bounce - 1), (int)cw + 4, 55,
                   juce::Justification::left);
        g.drawText(ch, (int)(startX + 1), (int)(y + bounce + 1), (int)cw + 4, 55,
                   juce::Justification::left);

        g.setColour(rainbow[i % 6]);
        g.drawText(ch, (int)startX, (int)(y + bounce), (int)cw + 2, 55,
                   juce::Justification::left);

        startX += cw;
    }

    g.setColour(Pedal::White.withAlpha(0.4f));
    g.setFont(juce::Font(11.0f).italicised());
    g.drawText("psychedelic guitar processor", 0, 60, getWidth(), 16, juce::Justification::centred);
}

// ================================================================
// Section boxes (wobbly crayon borders on dark metal)
// ================================================================
void AetherEditor::drawSectionBox(juce::Graphics& g, juce::Rectangle<int> bounds,
                                   juce::Colour colour, const juce::String& title)
{
    auto r = bounds.toFloat().reduced(2.0f);

    // Semi-transparent fill
    g.setColour(colour);
    auto wobbled = makeWobblyRect(r, 3.0f, static_cast<unsigned int>(bounds.getX() * 7 + bounds.getY()));
    g.fillPath(wobbled);

    // Crayon-drawn border (thick, white-ish)
    g.setColour(Pedal::Outline.withAlpha(0.35f));
    g.strokePath(wobbled, juce::PathStrokeType(2.5f));

    // Section title (crayon style)
    g.setColour(Pedal::White.withAlpha(0.9f));
    g.setFont(juce::Font(13.0f).boldened());
    g.drawText(title, bounds.getX() + 38, bounds.getY() + 6, bounds.getWidth() - 42, 18,
               juce::Justification::left);
}

// ================================================================
// Wobbly rectangle
// ================================================================
juce::Path AetherEditor::makeWobblyRect(juce::Rectangle<float> r, float wobble, unsigned int seed)
{
    std::mt19937 rng(seed);
    std::uniform_real_distribution<float> dist(-wobble, wobble);
    juce::Path p;
    int steps = 10;
    p.startNewSubPath(r.getX() + dist(rng), r.getY() + dist(rng));
    for (int i = 1; i <= steps; ++i)
    {
        float t = (float)i / (float)steps;
        p.lineTo(r.getX() + r.getWidth() * t + dist(rng), r.getY() + dist(rng));
    }
    for (int i = 1; i <= steps; ++i)
    {
        float t = (float)i / (float)steps;
        p.lineTo(r.getRight() + dist(rng), r.getY() + r.getHeight() * t + dist(rng));
    }
    for (int i = 1; i <= steps; ++i)
    {
        float t = (float)i / (float)steps;
        p.lineTo(r.getRight() - r.getWidth() * t + dist(rng), r.getBottom() + dist(rng));
    }
    for (int i = 1; i <= steps; ++i)
    {
        float t = (float)i / (float)steps;
        p.lineTo(r.getX() + dist(rng), r.getBottom() - r.getHeight() * t + dist(rng));
    }
    p.closeSubPath();
    return p;
}

// ================================================================
// Crayon scribble decorations
// ================================================================
void AetherEditor::drawCrayonScribble(juce::Graphics& g, float x, float y,
                                       float w, float h, juce::Colour colour, unsigned int seed)
{
    std::mt19937 rng(seed);
    std::uniform_real_distribution<float> dx(-3.0f, 3.0f);
    std::uniform_real_distribution<float> dy(-3.0f, 3.0f);

    g.setColour(colour.withAlpha(0.15f));
    juce::Path scribble;
    scribble.startNewSubPath(x + dx(rng), y + dy(rng));
    int loops = 6;
    for (int i = 0; i < loops; ++i)
    {
        float t = (float)i / (float)loops;
        float sx = x + t * w + dx(rng);
        float sy = y + std::sin(t * 4.0f) * h * 0.5f + h * 0.5f + dy(rng);
        scribble.lineTo(sx, sy);
    }
    g.strokePath(scribble, juce::PathStrokeType(3.0f, juce::PathStrokeType::curved,
                                                  juce::PathStrokeType::rounded));
}

// ================================================================
// Swimming characters
// ================================================================
void AetherEditor::drawSwimmingCharacters(juce::Graphics& g)
{
    float totalWidth = 1020.0f + 200.0f; // screen + offscreen margins

    for (auto& s : swimmers)
    {
        // Calculate horizontal position — characters swim continuously across
        float speed = s.goingRight ? s.speed : -s.speed;
        float rawX = s.startX + animTime * speed * 30.0f; // 30fps -> pixels/sec

        // Wrap around: when going right, wrap from right edge to left; vice versa
        if (s.goingRight)
        {
            rawX = std::fmod(rawX + 100.0f, totalWidth) - 100.0f;
        }
        else
        {
            float travel = std::fmod(-animTime * s.speed * 30.0f, totalWidth);
            rawX = s.startX + travel;
            if (rawX < -100.0f) rawX += totalWidth;
        }

        // Gentle vertical bobbing (swimming motion)
        float bobY = s.y + std::sin(animTime * 1.5f + s.phaseOffset) * 12.0f;

        float phase = animTime * 2.0f + s.phaseOffset;

        switch (s.type)
        {
            case 0: drawPrincess(g, rawX, bobY, s.size, phase, s.colour); break;
            case 1: drawFairy(g, rawX, bobY, s.size, phase, s.colour); break;
            case 2: drawUnicorn(g, rawX, bobY, s.size, phase); break;
        }
    }
}

// ================================================================
// Stick-figure Princess (crayon style)
// ================================================================
void AetherEditor::drawPrincess(juce::Graphics& g, float x, float y, float size,
                                 float phase, juce::Colour dressCol)
{
    float s = size;
    float armSwing = std::sin(phase * 2.0f) * 0.3f;

    // Dress (triangle shape, crayon-drawn)
    juce::Path dress;
    dress.startNewSubPath(x, y);                         // waist
    dress.lineTo(x - s * 0.35f, y + s * 0.5f);          // left hem
    dress.lineTo(x + s * 0.35f, y + s * 0.5f);          // right hem
    dress.closeSubPath();
    g.setColour(dressCol.withAlpha(0.7f));
    g.fillPath(dress);
    g.setColour(Pedal::Outline.withAlpha(0.5f));
    g.strokePath(dress, juce::PathStrokeType(2.0f));

    // Body/torso (stick line)
    g.setColour(Pedal::Outline.withAlpha(0.6f));
    g.drawLine(x, y - s * 0.15f, x, y, 2.0f);

    // Head (circle)
    float headR = s * 0.12f;
    g.setColour(Pedal::Cream.withAlpha(0.8f));
    g.fillEllipse(x - headR, y - s * 0.15f - headR * 2, headR * 2, headR * 2);
    g.setColour(Pedal::Outline.withAlpha(0.5f));
    g.drawEllipse(x - headR, y - s * 0.15f - headR * 2, headR * 2, headR * 2, 1.5f);

    // Crown (little triangle on head)
    juce::Path crown;
    float crownY = y - s * 0.15f - headR * 2 - s * 0.02f;
    crown.startNewSubPath(x - headR * 0.7f, crownY);
    crown.lineTo(x - headR * 0.3f, crownY - s * 0.1f);
    crown.lineTo(x, crownY);
    crown.lineTo(x + headR * 0.3f, crownY - s * 0.08f);
    crown.lineTo(x + headR * 0.7f, crownY);
    g.setColour(Pedal::Yellow.withAlpha(0.8f));
    g.fillPath(crown);
    g.setColour(Pedal::Outline.withAlpha(0.4f));
    g.strokePath(crown, juce::PathStrokeType(1.5f));

    // Arms (swimming motion!)
    float armY = y - s * 0.08f;
    g.setColour(Pedal::Cream.withAlpha(0.7f));
    g.drawLine(x, armY, x - s * 0.25f - armSwing * s * 0.2f,
               armY - s * 0.08f + std::sin(phase) * s * 0.1f, 2.0f);
    g.drawLine(x, armY, x + s * 0.25f + armSwing * s * 0.2f,
               armY - s * 0.08f - std::sin(phase) * s * 0.1f, 2.0f);

    // Legs (kicking motion)
    float legY = y + s * 0.5f;
    g.drawLine(x - s * 0.05f, legY - s * 0.1f, x - s * 0.15f + std::sin(phase * 1.5f) * s * 0.08f,
               legY + s * 0.1f, 2.0f);
    g.drawLine(x + s * 0.05f, legY - s * 0.1f, x + s * 0.15f - std::sin(phase * 1.5f) * s * 0.08f,
               legY + s * 0.1f, 2.0f);

    // Eyes (dot dots)
    g.setColour(Pedal::Metal);
    float eyeY = y - s * 0.15f - headR * 1.2f;
    g.fillEllipse(x - headR * 0.4f, eyeY, 2.5f, 2.5f);
    g.fillEllipse(x + headR * 0.15f, eyeY, 2.5f, 2.5f);

    // Smile
    juce::Path smile;
    smile.addCentredArc(x, eyeY + headR * 0.5f, headR * 0.3f, headR * 0.15f,
                         0.0f, 0.1f, juce::MathConstants<float>::pi - 0.1f, true);
    g.setColour(Pedal::HotPink.withAlpha(0.6f));
    g.strokePath(smile, juce::PathStrokeType(1.2f));
}

// ================================================================
// Fairy (stick figure with wings + wand)
// ================================================================
void AetherEditor::drawFairy(juce::Graphics& g, float x, float y, float size,
                              float phase, juce::Colour glowCol)
{
    float s = size;
    float wingFlap = std::sin(phase * 4.0f) * 0.2f;

    // Wings (butterfly shape, translucent)
    g.setColour(glowCol.withAlpha(0.3f));
    float wingW = s * 0.3f + wingFlap * s * 0.15f;
    float wingH = s * 0.25f;
    g.fillEllipse(x - wingW - s * 0.05f, y - wingH * 0.5f - s * 0.05f, wingW, wingH);
    g.fillEllipse(x + s * 0.05f, y - wingH * 0.5f - s * 0.05f, wingW, wingH);
    // Lower wings (smaller)
    g.setColour(glowCol.withAlpha(0.2f));
    g.fillEllipse(x - wingW * 0.7f - s * 0.03f, y + s * 0.02f, wingW * 0.7f, wingH * 0.6f);
    g.fillEllipse(x + s * 0.03f, y + s * 0.02f, wingW * 0.7f, wingH * 0.6f);

    // Body (thin stick)
    g.setColour(Pedal::Outline.withAlpha(0.5f));
    g.drawLine(x, y - s * 0.12f, x, y + s * 0.2f, 1.8f);

    // Head
    float headR = s * 0.09f;
    g.setColour(Pedal::Cream.withAlpha(0.8f));
    g.fillEllipse(x - headR, y - s * 0.12f - headR * 2, headR * 2, headR * 2);
    g.setColour(Pedal::Outline.withAlpha(0.4f));
    g.drawEllipse(x - headR, y - s * 0.12f - headR * 2, headR * 2, headR * 2, 1.2f);

    // Wand (arm holding a star wand)
    float wandTipX = x + s * 0.35f + std::sin(phase) * s * 0.05f;
    float wandTipY = y - s * 0.2f + std::cos(phase * 0.7f) * s * 0.05f;
    g.setColour(Pedal::Outline.withAlpha(0.4f));
    g.drawLine(x + s * 0.05f, y - s * 0.05f, wandTipX, wandTipY, 1.5f);

    // Star on wand tip
    g.setColour(Pedal::Yellow.withAlpha(0.9f));
    drawStar(g, wandTipX, wandTipY, 5.0f, 1.0f);

    // Sparkle trail behind wand
    for (int i = 1; i <= 3; ++i)
    {
        float trailX = wandTipX - (float)i * 6.0f;
        float trailY = wandTipY + (float)i * 2.0f;
        float trailAlpha = 0.6f / (float)i;
        g.setColour(Pedal::Yellow.withAlpha(trailAlpha));
        drawStar(g, trailX, trailY, 2.5f, trailAlpha);
    }

    // Legs (tiny)
    float legY = y + s * 0.2f;
    g.setColour(Pedal::Cream.withAlpha(0.6f));
    g.drawLine(x - 2, legY, x - s * 0.08f + std::sin(phase) * 3, legY + s * 0.12f, 1.5f);
    g.drawLine(x + 2, legY, x + s * 0.08f - std::sin(phase) * 3, legY + s * 0.12f, 1.5f);

    // Glow aura
    g.setColour(glowCol.withAlpha(0.08f));
    g.fillEllipse(x - s * 0.3f, y - s * 0.25f, s * 0.6f, s * 0.5f);
}

// ================================================================
// Unicorn (stick figure horse with horn + rainbow mane)
// ================================================================
void AetherEditor::drawUnicorn(juce::Graphics& g, float x, float y, float size, float phase)
{
    float s = size;
    float gallop = std::sin(phase * 3.0f) * s * 0.04f;

    // Body (horizontal oval)
    g.setColour(Pedal::White.withAlpha(0.7f));
    g.fillEllipse(x - s * 0.25f, y - s * 0.08f + gallop, s * 0.5f, s * 0.18f);
    g.setColour(Pedal::Outline.withAlpha(0.4f));
    g.drawEllipse(x - s * 0.25f, y - s * 0.08f + gallop, s * 0.5f, s * 0.18f, 1.8f);

    // Head + neck
    float headX = x + s * 0.3f;
    float headY = y - s * 0.18f + gallop;
    // Neck line
    g.setColour(Pedal::Outline.withAlpha(0.4f));
    g.drawLine(x + s * 0.15f, y - s * 0.04f + gallop, headX, headY, 2.0f);
    // Head circle
    float hr = s * 0.08f;
    g.setColour(Pedal::White.withAlpha(0.7f));
    g.fillEllipse(headX - hr, headY - hr, hr * 2, hr * 2);
    g.setColour(Pedal::Outline.withAlpha(0.4f));
    g.drawEllipse(headX - hr, headY - hr, hr * 2, hr * 2, 1.5f);

    // Horn
    g.setColour(Pedal::Yellow.withAlpha(0.8f));
    juce::Path horn;
    horn.startNewSubPath(headX - 2, headY - hr);
    horn.lineTo(headX + 1, headY - hr - s * 0.15f);
    horn.lineTo(headX + 4, headY - hr);
    horn.closeSubPath();
    g.fillPath(horn);
    g.setColour(Pedal::Outline.withAlpha(0.3f));
    g.strokePath(horn, juce::PathStrokeType(1.0f));

    // Rainbow mane (colored lines flowing from neck)
    juce::Colour maneColors[] = { Pedal::Red, Pedal::Orange, Pedal::Yellow,
                                   Pedal::Green, Pedal::Blue, Pedal::Purple };
    for (int i = 0; i < 6; ++i)
    {
        float mx = x + s * 0.15f + (float)i * 3.0f;
        float maneWave = std::sin(phase * 2.0f + (float)i * 0.5f) * s * 0.04f;
        g.setColour(maneColors[i].withAlpha(0.5f));
        g.drawLine(mx, y - s * 0.06f + gallop, mx - 4.0f + maneWave,
                   y - s * 0.2f + gallop + maneWave, 2.0f);
    }

    // Legs (4 stick legs with galloping motion)
    float legBase = y + s * 0.1f + gallop;
    float legLen = s * 0.18f;
    float legPhases[] = { 0.0f, 1.5f, 3.0f, 4.5f };
    float legXs[] = { x - s * 0.18f, x - s * 0.08f, x + s * 0.08f, x + s * 0.18f };
    g.setColour(Pedal::Outline.withAlpha(0.4f));
    for (int i = 0; i < 4; ++i)
    {
        float kick = std::sin(phase * 3.0f + legPhases[i]) * s * 0.06f;
        g.drawLine(legXs[i], legBase, legXs[i] + kick, legBase + legLen, 1.8f);
    }

    // Eye
    g.setColour(Pedal::Metal);
    g.fillEllipse(headX + hr * 0.2f, headY - 1.5f, 2.5f, 2.5f);

    // Tail (rainbow, flowing)
    float tailX = x - s * 0.25f;
    float tailY = y - s * 0.02f + gallop;
    for (int i = 0; i < 4; ++i)
    {
        float tw = std::sin(phase * 1.5f + (float)i * 0.8f) * s * 0.06f;
        g.setColour(maneColors[i].withAlpha(0.4f));
        g.drawLine(tailX, tailY + (float)i * 2.0f, tailX - s * 0.15f + tw,
                   tailY + (float)i * 3.0f + tw, 2.0f);
    }
}

// ================================================================
// Star helper
// ================================================================
void AetherEditor::drawStar(juce::Graphics& g, float cx, float cy, float size, float twinkle)
{
    int points = 4;
    float outerR = size * juce::jlimit(0.3f, 1.0f, twinkle);
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
