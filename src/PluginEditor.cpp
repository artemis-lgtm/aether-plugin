#include "PluginEditor.h"
#include "dsp/LFOProcessor.h"
#include "BinaryData.h"
#include <cmath>

// ================================================================
// Filmstrip Look & Feel
// ================================================================
AetherEditor::FilmstripLookAndFeel::FilmstripLookAndFeel()
{
    setColour(juce::Label::textColourId, juce::Colour(0xFF222222));
}

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
    int srcY = 0;

    // Scale to fit the slider bounds
    float scale = juce::jmin((float)w / (float)frameW, (float)h / (float)frameW);
    float drawW = (float)frameW * scale;
    float drawH = (float)frameW * scale;
    float drawX = (float)x + ((float)w - drawW) * 0.5f;
    float drawY = (float)y + ((float)h - drawH) * 0.5f;

    g.drawImage(knobStrip,
                (int)drawX, (int)drawY, (int)drawW, (int)drawH,
                srcX, srcY, frameW, frameW);
}

void AetherEditor::FilmstripLookAndFeel::drawToggleButton(
    juce::Graphics& g, juce::ToggleButton& button, bool, bool)
{
    auto bounds = button.getLocalBounds().toFloat().reduced(2.0f);
    bool on = button.getToggleState();
    bool isBypass = button.getButtonText().length() == 1;

    if (isBypass)
    {
        g.setColour(on ? juce::Colour(0xCCFF6B6B) : juce::Colour(0xCC6BCB77));
        g.fillRoundedRectangle(bounds, 6.0f);
        g.setColour(juce::Colour(0x40000000));
        g.drawRoundedRectangle(bounds, 6.0f, 1.5f);
        g.setColour(juce::Colour(0xFFFFFFFF));
        g.setFont(juce::Font(11.0f).boldened());
        g.drawText(on ? "OFF" : "ON", bounds, juce::Justification::centred);
    }
    else
    {
        g.setColour(on ? juce::Colour(0xCC00CEC9) : juce::Colour(0xCCBBBBBB));
        g.fillRoundedRectangle(bounds, 6.0f);
        g.setColour(juce::Colour(0x40000000));
        g.drawRoundedRectangle(bounds, 6.0f, 1.5f);
        g.setColour(on ? juce::Colour(0xFFFFFFFF) : juce::Colour(0xFF222222));
        g.setFont(juce::Font(10.0f).boldened());
        g.drawText(button.getButtonText(), bounds, juce::Justification::centred);
    }
}

// ================================================================
// Constructor
// ================================================================
AetherEditor::AetherEditor(AetherProcessor& p)
    : AudioProcessorEditor(&p), processor(p)
{
    // Load images from binary resources
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
    std::mt19937 rng(54321);
    std::uniform_real_distribution<float> yDist(100.0f, 540.0f);
    std::uniform_real_distribution<float> sizeDist(22.0f, 38.0f);
    std::uniform_real_distribution<float> speedDist(0.25f, 0.9f);
    std::uniform_real_distribution<float> phaseDist(0.0f, 6.28f);
    std::uniform_int_distribution<int> typeDist(0, 2);
    std::uniform_int_distribution<int> dirDist(0, 1);

    juce::Colour colors[] = {
        juce::Colour(0xFFFF6B6B), juce::Colour(0xFFFF69B4), juce::Colour(0xFFFF8C42),
        juce::Colour(0xFF6BCB77), juce::Colour(0xFFBB6BD9), juce::Colour(0xFF00CEC9)
    };

    for (int i = 0; i < 6; ++i)
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
    int sectionW = (W - 50) / 4;
    int sx0 = 15;
    int knobY1 = sectionY + 45;
    int knobY2 = sectionY + 45 + knobH + labelH + pad;
    int knobGap = knobW + 6;

    // Swell
    int sc = sx0 + sectionW / 2 - knobW * 3 / 2 - 4;
    swellSens.setBounds(sc, knobY1, knobW, knobH);
    swellAttack.setBounds(sc + knobGap, knobY1, knobW, knobH);
    swellDepth.setBounds(sc + knobGap * 2, knobY1, knobW, knobH);
    swellBypass.setBounds(sx0 + 6, sectionY + 8, 34, 24);

    // Vinyl
    int vx = sx0 + sectionW + 5;
    int vc = vx + sectionW / 2 - knobW - 4;
    vinylYear.setBounds(vc, knobY1, knobW, knobH);
    vinylDetune.setBounds(vc + knobGap, knobY1, knobW, knobH);
    vinylBypass.setBounds(vx + 6, sectionY + 8, 34, 24);

    // Psyche
    int px = sx0 + (sectionW + 5) * 2;
    int pc = px + 4;
    int pGap = knobW + 1;
    psycheShimmer.setBounds(pc, knobY1, knobW, knobH);
    psycheSpace.setBounds(pc + pGap, knobY1, knobW, knobH);
    psycheMod.setBounds(pc + pGap * 2, knobY1, knobW, knobH);
    psycheWarp.setBounds(pc + pGap * 3, knobY1, knobW, knobH);
    psycheMix.setBounds(pc, knobY2, knobW, knobH);
    psycheNotches.setBounds(pc + pGap, knobY2, knobW, knobH);
    psycheSweep.setBounds(pc + pGap * 2, knobY2, knobW, knobH);
    psycheBypass.setBounds(px + 6, sectionY + 8, 34, 24);

    // LFO
    int lx = sx0 + (sectionW + 5) * 3;
    int lc = lx + 8;
    lfoShape.setBounds(lc, knobY1, knobW, knobH);
    lfoRate.setBounds(lc + knobGap, knobY1, knobW, knobH);
    lfoDepth.setBounds(lc + knobGap * 2, knobY1, knobW, knobH);
    lfoSyncRate.setBounds(lc, knobY2, knobW, knobH);
    lfoPhaseOffset.setBounds(lc + knobGap, knobY2, knobW, knobH);
    lfoSync.setBounds(lc + knobGap * 2, knobY2 + 12, 52, 28);
    lfoBypass.setBounds(lx + 6, sectionY + 8, 34, 24);

    // Master
    int my = sectionY + 240 + 40;
    int mx = W / 2 - knobGap;
    masterMix.setBounds(mx, my, knobW, knobH);
    masterGain.setBounds(mx + knobGap, my, knobW, knobH);

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
    lbl->setColour(juce::Label::textColourId, juce::Colour(0xCC000000));
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
    // Draw the pre-rendered background image
    if (backgroundImg.isValid())
        g.drawImage(backgroundImg, getLocalBounds().toFloat());
    else
        g.fillAll(juce::Colour(0xFF5DADE2)); // fallback sky blue

    // Section boxes (semi-transparent white panels on top of background)
    int sectionW = (getWidth() - 50) / 4;
    int sectionY = 100;
    int sectionH = 240;
    int sx0 = 15;

    struct SectionInfo { int x; juce::Colour border; const char* title; };
    SectionInfo sections[] = {
        { sx0,                        juce::Colour(0xFFFF69B4), "SWELL" },
        { sx0 + sectionW + 5,        juce::Colour(0xFFFF8C42), "VINYL" },
        { sx0 + (sectionW + 5) * 2,  juce::Colour(0xFF9B59B6), "PSYCHE" },
        { sx0 + (sectionW + 5) * 3,  juce::Colour(0xFF2ECC71), "LFO" }
    };

    for (auto& sec : sections)
    {
        // Semi-transparent white fill
        g.setColour(juce::Colour(0x70FFFFFF));
        g.fillRoundedRectangle((float)sec.x, (float)sectionY, (float)sectionW, (float)sectionH, 10.0f);

        // Colored border (crayon-thick)
        g.setColour(sec.border);
        g.drawRoundedRectangle((float)sec.x, (float)sectionY, (float)sectionW, (float)sectionH, 10.0f, 3.0f);

        // Section title
        g.setFont(juce::Font(15.0f).boldened());
        g.drawText(sec.title, sec.x + 38, sectionY + 5, sectionW - 44, 22, juce::Justification::left);
    }

    // Master section label
    g.setColour(juce::Colour(0xB0000000));
    g.setFont(juce::Font(15.0f).boldened());
    g.drawText("M A S T E R", 0, sectionY + sectionH + 14, getWidth(), 22, juce::Justification::centred);

    // Animated swimming characters (on top of background, behind controls)
    drawSwimmingCharacters(g);

    // Animated bouncing title
    drawTitle(g);

    // LFO info display
    int lfoX = 15 + (sectionW + 5) * 3;
    int lShape = static_cast<int>(lfoShape.getValue());
    int lSyncR = static_cast<int>(lfoSyncRate.getValue());
    bool synced = lfoSync.getToggleState();
    juce::String info = LFOProcessor::shapeName(lShape);
    if (synced)
        info += juce::String(" | ") + LFOProcessor::syncRateName(lSyncR);
    g.setColour(juce::Colour(0x80000000));
    g.setFont(juce::Font(10.0f));
    g.drawText(info, lfoX, sectionY + sectionH - 18, sectionW, 16, juce::Justification::centred);
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
    float y = 35.0f;

    juce::Colour rainbow[] = {
        juce::Colour(0xFFFF6B6B), juce::Colour(0xFFFF8C42), juce::Colour(0xFFFFE066),
        juce::Colour(0xFF6BCB77), juce::Colour(0xFF00CEC9), juce::Colour(0xFFBB6BD9)
    };

    for (int i = 0; i < title.length(); ++i)
    {
        juce::String ch = title.substring(i, i + 1);
        float cw = font.getStringWidthFloat(ch);
        float bounce = std::sin(animTime * 2.5f + i * 0.8f) * 6.0f;

        // White outline for readability
        g.setColour(juce::Colour(0xAAFFFFFF));
        for (int dx = -1; dx <= 1; dx++)
            for (int dy = -1; dy <= 1; dy++)
                if (dx || dy)
                    g.drawText(ch, (int)(startX + dx), (int)(y + bounce + dy), (int)cw + 2, 55,
                               juce::Justification::left);

        // Shadow
        g.setColour(juce::Colour(0x40000000));
        g.drawText(ch, (int)(startX + 2), (int)(y + bounce + 2), (int)cw + 2, 55,
                   juce::Justification::left);

        // Rainbow letter
        g.setColour(rainbow[i % 6]);
        g.drawText(ch, (int)startX, (int)(y + bounce), (int)cw + 2, 55,
                   juce::Justification::left);

        startX += cw;
    }
}

// ================================================================
// Swimming characters
// ================================================================
void AetherEditor::drawSwimmingCharacters(juce::Graphics& g)
{
    float totalWidth = 1220.0f;
    for (auto& s : swimmers)
    {
        float rawX;
        if (s.goingRight)
            rawX = std::fmod(animTime * s.speed * 30.0f + s.phaseOffset * 100.0f, totalWidth) - 100.0f;
        else
            rawX = 1120.0f - std::fmod(animTime * s.speed * 30.0f + s.phaseOffset * 100.0f, totalWidth);

        float bobY = s.y + std::sin(animTime * 1.5f + s.phaseOffset) * 10.0f;
        float phase = animTime * 2.0f + s.phaseOffset;

        switch (s.type)
        {
            case 0: drawMushroom(g, rawX, bobY, s.size, phase, s.colour); break;
            case 1: drawGhost(g, rawX, bobY, s.size, phase); break;
            case 2: drawAlien(g, rawX, bobY, s.size, phase, s.colour); break;
        }
    }
}

void AetherEditor::drawMushroom(juce::Graphics& g, float x, float y, float size,
                                 float phase, juce::Colour cap)
{
    float s = size;
    float wobble = std::sin(phase * 2.0f) * 2.0f;

    g.setColour(juce::Colour(0xCCF0F4F8));
    g.fillRect(x - s * 0.12f + wobble, y, s * 0.24f, s * 0.35f);
    g.setColour(juce::Colour(0x66000000));
    g.drawRect(x - s * 0.12f + wobble, y, s * 0.24f, s * 0.35f, 1.5f);

    juce::Path capPath;
    capPath.addCentredArc(x + wobble, y, s * 0.4f, s * 0.28f, 0.0f,
                           juce::MathConstants<float>::pi, juce::MathConstants<float>::twoPi, true);
    capPath.closeSubPath();
    g.setColour(cap);
    g.fillPath(capPath);
    g.setColour(juce::Colour(0x66000000));
    g.strokePath(capPath, juce::PathStrokeType(2.0f));

    g.setColour(juce::Colour(0xB3FFFFFF));
    g.fillEllipse(x - s * 0.15f + wobble, y - s * 0.18f, s * 0.1f, s * 0.08f);
    g.fillEllipse(x + s * 0.08f + wobble, y - s * 0.22f, s * 0.08f, s * 0.07f);

    g.setColour(juce::Colour(0x99000000));
    g.fillEllipse(x - s * 0.06f + wobble, y + s * 0.08f, 3, 3);
    g.fillEllipse(x + s * 0.04f + wobble, y + s * 0.08f, 3, 3);
    juce::Path smile;
    smile.addCentredArc(x + wobble, y + s * 0.16f, s * 0.06f, s * 0.03f,
                         0.0f, 0.2f, juce::MathConstants<float>::pi - 0.2f, true);
    g.strokePath(smile, juce::PathStrokeType(1.2f));
}

void AetherEditor::drawGhost(juce::Graphics& g, float x, float y, float size, float phase)
{
    float s = size;
    float float_ = std::sin(phase * 2.0f) * 4.0f;

    juce::Path body;
    body.startNewSubPath(x - s * 0.25f, y + s * 0.3f + float_);
    body.lineTo(x - s * 0.25f, y - s * 0.1f + float_);
    body.addCentredArc(x, y - s * 0.1f + float_, s * 0.25f, s * 0.2f,
                        0.0f, juce::MathConstants<float>::pi, juce::MathConstants<float>::twoPi, false);
    body.lineTo(x + s * 0.25f, y + s * 0.3f + float_);
    body.lineTo(x + s * 0.15f, y + s * 0.22f + float_);
    body.lineTo(x + s * 0.05f, y + s * 0.3f + float_);
    body.lineTo(x - s * 0.05f, y + s * 0.22f + float_);
    body.lineTo(x - s * 0.15f, y + s * 0.3f + float_);
    body.closeSubPath();

    g.setColour(juce::Colour(0xD9FFFFFF));
    g.fillPath(body);
    g.setColour(juce::Colour(0x4D000000));
    g.strokePath(body, juce::PathStrokeType(1.8f));

    g.setColour(juce::Colour(0xFF000000));
    g.fillEllipse(x - s * 0.1f, y - s * 0.05f + float_, 5, 6);
    g.fillEllipse(x + s * 0.06f, y - s * 0.05f + float_, 5, 6);

    g.setColour(juce::Colour(0x66FF69B4));
    g.fillEllipse(x - s * 0.18f, y + s * 0.04f + float_, s * 0.1f, s * 0.06f);
    g.fillEllipse(x + s * 0.1f, y + s * 0.04f + float_, s * 0.1f, s * 0.06f);

    g.setColour(juce::Colour(0x66000000));
    g.fillEllipse(x - 2, y + s * 0.1f + float_, 4, 3);
}

void AetherEditor::drawAlien(juce::Graphics& g, float x, float y, float size,
                              float phase, juce::Colour body)
{
    float s = size;
    float bob = std::sin(phase * 1.5f) * 3.0f;

    g.setColour(body.withAlpha(0.7f));
    g.fillEllipse(x - s * 0.22f, y - s * 0.15f + bob, s * 0.44f, s * 0.5f);
    g.setColour(juce::Colour(0x66000000));
    g.drawEllipse(x - s * 0.22f, y - s * 0.15f + bob, s * 0.44f, s * 0.5f, 1.8f);

    g.setColour(body.withAlpha(0.8f));
    g.fillEllipse(x - s * 0.25f, y - s * 0.42f + bob, s * 0.5f, s * 0.35f);
    g.setColour(juce::Colour(0x66000000));
    g.drawEllipse(x - s * 0.25f, y - s * 0.42f + bob, s * 0.5f, s * 0.35f, 1.8f);

    float eyeY = y - s * 0.3f + bob;
    g.setColour(juce::Colour(0xFFFFFFFF));
    g.fillEllipse(x - s * 0.18f, eyeY, s * 0.1f, s * 0.08f);
    g.fillEllipse(x - s * 0.04f, eyeY - s * 0.02f, s * 0.1f, s * 0.08f);
    g.fillEllipse(x + s * 0.1f, eyeY, s * 0.1f, s * 0.08f);
    g.setColour(juce::Colour(0xFF000000));
    g.fillEllipse(x - s * 0.15f, eyeY + s * 0.01f, 3, 3);
    g.fillEllipse(x, eyeY - s * 0.01f, 3, 3);
    g.fillEllipse(x + s * 0.13f, eyeY + s * 0.01f, 3, 3);

    g.setColour(body.darker(0.2f));
    g.drawLine(x, y - s * 0.42f + bob, x - s * 0.1f, y - s * 0.58f + bob, 1.5f);
    g.drawLine(x, y - s * 0.42f + bob, x + s * 0.1f, y - s * 0.58f + bob, 1.5f);
    g.setColour(juce::Colour(0xFFFFE066));
    g.fillEllipse(x - s * 0.1f - 3, y - s * 0.58f + bob - 3, 6, 6);
    g.fillEllipse(x + s * 0.1f - 3, y - s * 0.58f + bob - 3, 6, 6);
}
