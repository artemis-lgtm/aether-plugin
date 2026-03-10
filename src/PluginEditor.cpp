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
        // Analog LED built into the pedal board
        // Note: bypass param is inverted — "on" = bypassed (OFF), "off" = active (ON)
        bool active = !on;
        float ledR = juce::jmin(bounds.getWidth(), bounds.getHeight()) * 0.42f;
        auto center = bounds.getCentre();
        auto ledRect = juce::Rectangle<float>(center.x - ledR, center.y - ledR, ledR * 2, ledR * 2);

        // Chrome bezel ring
        g.setColour(juce::Colour(0xFF888888));
        g.fillEllipse(ledRect.expanded(3.0f));
        g.setColour(juce::Colour(0xFFAAAAAA));
        g.drawEllipse(ledRect.expanded(3.0f), 1.5f);
        g.setColour(juce::Colour(0xFF555555));
        g.drawEllipse(ledRect.expanded(1.5f), 1.0f);

        if (active)
        {
            // Outer glow (ambient light spill)
            g.setColour(juce::Colour(0x25FF1010));
            g.fillEllipse(ledRect.expanded(10.0f));
            g.setColour(juce::Colour(0x40FF2020));
            g.fillEllipse(ledRect.expanded(6.0f));

            // Bright red LED
            juce::ColourGradient grad(juce::Colour(0xFFFF4040), center.x - ledR * 0.3f, center.y - ledR * 0.3f,
                                       juce::Colour(0xFFBB0000), center.x + ledR, center.y + ledR, true);
            g.setGradientFill(grad);
            g.fillEllipse(ledRect);

            // Hot spot (specular highlight)
            g.setColour(juce::Colour(0x80FFFFFF));
            g.fillEllipse(center.x - ledR * 0.35f, center.y - ledR * 0.4f, ledR * 0.5f, ledR * 0.4f);
        }
        else
        {
            // Dark LED (off) — deep red, barely visible
            juce::ColourGradient grad(juce::Colour(0xFF3A1515), center.x, center.y - ledR * 0.3f,
                                       juce::Colour(0xFF1A0808), center.x, center.y + ledR, true);
            g.setGradientFill(grad);
            g.fillEllipse(ledRect);

            // Subtle glass reflection even when off
            g.setColour(juce::Colour(0x18FFFFFF));
            g.fillEllipse(center.x - ledR * 0.3f, center.y - ledR * 0.35f, ledR * 0.4f, ledR * 0.3f);
        }

        // Glass dome edge
        g.setColour(juce::Colour(0x30000000));
        g.drawEllipse(ledRect, 0.8f);
    }
    else
    {
        // Sync toggle: small LED-style indicator, no text
        float ledSize = juce::jmin(bounds.getWidth(), bounds.getHeight()) * 0.6f;
        auto ledBounds = bounds.withSizeKeepingCentre(ledSize, ledSize);
        g.setColour(on ? juce::Colour(0xDDFF2020) : juce::Colour(0x66444444));
        g.fillEllipse(ledBounds);
        g.setColour(juce::Colour(0x40000000));
        g.drawEllipse(ledBounds, 1.0f);
        if (on)
        {
            // Glow when active
            g.setColour(juce::Colour(0x30FF0000));
            g.fillEllipse(ledBounds.expanded(3.0f));
        }
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

    // Load per-knob random-color filmstrips
    loadStrip(lnfSwellSens,      BinaryData::knobswellsens_png,      BinaryData::knobswellsens_pngSize);
    loadStrip(lnfSwellAttack,    BinaryData::knobswellattack_png,    BinaryData::knobswellattack_pngSize);
    loadStrip(lnfSwellDepth,     BinaryData::knobswelldepth_png,     BinaryData::knobswelldepth_pngSize);
    loadStrip(lnfVinylYear,      BinaryData::knobvinylyear_png,      BinaryData::knobvinylyear_pngSize);
    loadStrip(lnfVinylDetune,    BinaryData::knobvinyldetune_png,    BinaryData::knobvinyldetune_pngSize);
    loadStrip(lnfPsycheShimmer,  BinaryData::knobpsycheshimmer_png,  BinaryData::knobpsycheshimmer_pngSize);
    loadStrip(lnfPsycheSpace,    BinaryData::knobpsychespace_png,    BinaryData::knobpsychespace_pngSize);
    loadStrip(lnfPsycheMod,      BinaryData::knobpsychemod_png,      BinaryData::knobpsychemod_pngSize);
    loadStrip(lnfPsycheWarp,     BinaryData::knobpsychewarp_png,     BinaryData::knobpsychewarp_pngSize);
    loadStrip(lnfPsycheMix,      BinaryData::knobpsychemix_png,      BinaryData::knobpsychemix_pngSize);
    loadStrip(lnfPsycheNotches,  BinaryData::knobpsychenotches_png,  BinaryData::knobpsychenotches_pngSize);
    loadStrip(lnfPsycheSweep,    BinaryData::knobpsychesweep_png,    BinaryData::knobpsychesweep_pngSize);
    loadStrip(lnfLfoShape,       BinaryData::knoblfoshape_png,       BinaryData::knoblfoshape_pngSize);
    loadStrip(lnfLfoRate,        BinaryData::knoblforate_png,        BinaryData::knoblforate_pngSize);
    loadStrip(lnfLfoDepth,       BinaryData::knoblfodepth_png,       BinaryData::knoblfodepth_pngSize);
    loadStrip(lnfLfoSyncRate,    BinaryData::knoblfosyncrate_png,    BinaryData::knoblfosyncrate_pngSize);
    loadStrip(lnfLfoPhase,       BinaryData::knoblfophase_png,       BinaryData::knoblfophase_pngSize);
    loadStrip(lnfMasterMix,      BinaryData::knobmastermix_png,      BinaryData::knobmastermix_pngSize);
    loadStrip(lnfMasterGain,     BinaryData::knobmastergain_png,     BinaryData::knobmastergain_pngSize);

    setSize(1020, 620);

    auto setupKnob = [&](juce::Slider& s, FilmstripLookAndFeel& lnf) {
        s.setSliderStyle(juce::Slider::RotaryHorizontalVerticalDrag);
        s.setTextBoxStyle(juce::Slider::NoTextBox, false, 0, 0);
        s.setLookAndFeel(&lnf);
        addAndMakeVisible(s);
    };

    setupKnob(swellSens, lnfSwellSens);
    setupKnob(swellAttack, lnfSwellAttack);
    setupKnob(swellDepth, lnfSwellDepth);
    setupKnob(vinylYear, lnfVinylYear);
    setupKnob(vinylDetune, lnfVinylDetune);
    setupKnob(psycheShimmer, lnfPsycheShimmer);
    setupKnob(psycheSpace, lnfPsycheSpace);
    setupKnob(psycheMod, lnfPsycheMod);
    setupKnob(psycheWarp, lnfPsycheWarp);
    setupKnob(psycheMix, lnfPsycheMix);
    setupKnob(psycheNotches, lnfPsycheNotches);
    setupKnob(psycheSweep, lnfPsycheSweep);
    setupKnob(lfoShape, lnfLfoShape);
    setupKnob(lfoRate, lnfLfoRate);
    setupKnob(lfoDepth, lnfLfoDepth);
    setupKnob(lfoSyncRate, lnfLfoSyncRate);
    setupKnob(lfoPhaseOffset, lnfLfoPhase);
    setupKnob(masterMix, lnfMasterMix);
    setupKnob(masterGain, lnfMasterGain);

    for (auto* b : { &swellBypass, &vinylBypass, &psycheBypass, &lfoBypass, &lfoSync, &lfoUpbeat })
    {
        b->setLookAndFeel(&bypassLnf);  // shared LnF for bypass LED drawing
        addAndMakeVisible(*b);
    }

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
    aLfoUpbeat     = std::make_unique<ButtonAttachment>(apvts, "lfoUpbeat",     lfoUpbeat);

    startTimerHz(30); // 30fps for LFO waveform display animation
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
    for (auto* b : { &swellBypass, &vinylBypass, &psycheBypass, &lfoBypass, &lfoSync, &lfoUpbeat })
        b->setLookAndFeel(nullptr);
}

// ================================================================
// Timer — drives neon flicker animation
// ================================================================
void AetherEditor::timerCallback()
{
    neonTime += 1.0f / 30.0f;

    // Repaint LFO display pocket area
    repaint(665, 388, 140, 125);
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
    // Bypass LEDs: 24x24, next to section header tapes
    int ledS = 24;
    swellBypass.setBounds(255 - ledS/2, 195, ledS, ledS);  // scooted left

    vinylYear.setBounds  (80  - K/2, 355 - K/2, K, K);
    vinylDetune.setBounds(160 - K/2, 355 - K/2, K, K);
    vinylBypass.setBounds(230 - ledS/2, 310, ledS, ledS);  // moved right a lot

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
    psycheBypass.setBounds(psycheStart + psycheGap*6 + K/2 - 10, 195, ledS, ledS);  // scooted left

    lfoShape.setBounds(455 - K/2, 410 - K/2, K, K);
    lfoRate.setBounds (535 - K/2, 410 - K/2, K, K);
    lfoDepth.setBounds(615 - K/2, 410 - K/2, K, K);
    lfoSyncRate.setBounds    (455 - K/2, 485 - K/2, K, K);
    lfoPhaseOffset.setBounds (535 - K/2, 485 - K/2, K, K);
    // Sync inside LFO pocket (pocket is 670,393 -> 800,508)
    lfoSync.setBounds(680, 490, 16, 16);
    lfoUpbeat.setBounds(760, 490, 16, 16);
    lfoBypass.setBounds(658, 358, ledS, ledS);  // up and right a little
}

// ================================================================
// LFO Display Pocket — carved recessed window showing waveform
// ================================================================
void AetherEditor::drawLfoPocket(juce::Graphics& g)
{
    // Pocket position (right of LFO knobs, above portrait)
    float px = 670.0f, py = 393.0f, pw = 130.0f, ph = 115.0f;
    float r = 4.0f; // corner radius

    // Carved bevel: dark edge top-left (shadow), light edge bottom-right (highlight)
    // Outer shadow (makes it look recessed INTO the surface)
    g.setColour(juce::Colour(0x60000000));
    g.drawRoundedRectangle(px - 1, py - 1, pw + 2, ph + 2, r + 1, 2.0f);

    // Inner highlight on bottom-right edge
    g.setColour(juce::Colour(0x30FFFFFF));
    g.drawLine(px + r, py + ph + 1, px + pw - r, py + ph + 1, 1.0f);
    g.drawLine(px + pw + 1, py + r, px + pw + 1, py + ph - r, 1.0f);

    // Dark recessed background
    juce::ColourGradient pocketBg(juce::Colour(0xFF0A0A0A), px, py,
                                   juce::Colour(0xFF1A1A18), px, py + ph, false);
    g.setGradientFill(pocketBg);
    g.fillRoundedRectangle(px, py, pw, ph, r);

    // Inner bevel shadow (top-left inside edge = dark, bottom-right = light)
    g.setColour(juce::Colour(0x40000000));
    g.drawLine(px + 1, py + 1, px + pw - 1, py + 1, 1.5f);
    g.drawLine(px + 1, py + 1, px + 1, py + ph - 1, 1.5f);
    g.setColour(juce::Colour(0x18FFFFFF));
    g.drawLine(px + 2, py + ph - 1, px + pw - 1, py + ph - 1, 1.0f);
    g.drawLine(px + pw - 1, py + 2, px + pw - 1, py + ph - 1, 1.0f);

    // ---- Waveform display area (top part of pocket) ----
    float waveX = px + 8.0f, waveY = py + 6.0f;
    float waveW = pw - 16.0f, waveH = 55.0f;

    // Subtle grid lines (oscilloscope style)
    g.setColour(juce::Colour(0x15FFFFFF));
    for (int i = 1; i < 4; i++)
    {
        float gy = waveY + waveH * (float)i / 4.0f;
        g.drawHorizontalLine((int)gy, waveX, waveX + waveW);
    }
    g.drawVerticalLine((int)(waveX + waveW * 0.5f), waveY, waveY + waveH);

    // Draw the LFO waveform
    int shape = static_cast<int>(lfoShape.getValue());
    float phase = neonTime * 1.5f; // slow animation phase
    juce::Colour waveColor(0xFFFF6030); // warm amber like analog displays

    juce::Path wavePath;
    int numPoints = (int)waveW;
    for (int i = 0; i <= numPoints; i++)
    {
        float t = (float)i / (float)numPoints;
        float x = waveX + t * waveW;
        float tp = std::fmod(t * 2.0f + phase, 1.0f); // two cycles, animated

        float val = 0.0f;
        switch (shape)
        {
            case 0: // Sine
                val = std::sin(tp * 6.2832f);
                break;
            case 1: // Triangle
                val = 4.0f * std::abs(tp - 0.5f) - 1.0f;
                break;
            case 2: // Square
                val = tp < 0.5f ? 1.0f : -1.0f;
                break;
            case 3: // Saw up
                val = 2.0f * tp - 1.0f;
                break;
            case 4: // Saw down
                val = 1.0f - 2.0f * tp;
                break;
            case 5: // Sample & Hold (stepped random)
            {
                int step = static_cast<int>(tp * 8.0f);
                val = std::sin((float)step * 2.7f + 1.3f);
                break;
            }
            default:
                val = std::sin(tp * 6.2832f);
                break;
        }

        float y = waveY + waveH * 0.5f - val * (waveH * 0.4f);
        if (i == 0)
            wavePath.startNewSubPath(x, y);
        else
            wavePath.lineTo(x, y);
    }

    // Glow underneath the waveform line
    g.setColour(waveColor.withAlpha(0.15f));
    g.strokePath(wavePath, juce::PathStrokeType(6.0f));
    g.setColour(waveColor.withAlpha(0.3f));
    g.strokePath(wavePath, juce::PathStrokeType(3.0f));
    // Bright core line
    g.setColour(waveColor);
    g.strokePath(wavePath, juce::PathStrokeType(1.5f));

    // ---- Text display area (bottom part of pocket) ----
    float textY = waveY + waveH + 6.0f;
    float textH = ph - waveH - 18.0f;

    // Shape name
    juce::String shapeName = LFOProcessor::shapeName(shape);

    // Sync rate if synced
    bool synced = lfoSync.getToggleState();
    juce::String rateName;
    if (synced)
    {
        int syncR = static_cast<int>(lfoSyncRate.getValue());
        rateName = LFOProcessor::syncRateName(syncR);
    }
    else
    {
        float rate = (float)lfoRate.getValue();
        rateName = juce::String(rate, 1) + " Hz";
    }

    // Draw shape name
    g.setColour(waveColor);
    g.setFont(juce::Font(12.0f).boldened());
    g.drawText(shapeName, (int)waveX, (int)textY, (int)waveW, (int)(textH * 0.5f),
               juce::Justification::centred);

    // Draw rate below
    g.setColour(waveColor.withAlpha(0.7f));
    g.setFont(juce::Font(10.0f));
    g.drawText(rateName, (int)waveX, (int)(textY + textH * 0.45f), (int)waveW, (int)(textH * 0.5f),
               juce::Justification::centred);

    // SYNC and UPBEAT labels inside pocket (next to their buttons)
    g.setColour(waveColor.withAlpha(0.5f));
    g.setFont(juce::Font(8.0f));
    g.drawText("SYN", 673, 491, 24, 14, juce::Justification::centredLeft);
    g.drawText("UP", 748, 491, 24, 14, juce::Justification::centredLeft);
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

    // Neon borders are baked into the background texture — no overlay needed

    // ---- LFO display pocket (carved into pedal) ----
    drawLfoPocket(g);
}
