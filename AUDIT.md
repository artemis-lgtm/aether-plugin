# Aether v2.2 DSP Audit -- Post-Logic Pro Testing
*Austin's feedback: "no craftsmanship," barely any audible modulation, LFO doesn't work*

## Root Cause Analysis

### Problem 1: Modulations are too subtle / volume drops
**VinylProcessor detune:**
- `detuneDepth` max is only 200 samples at 44.1kHz = ~4.5ms of delay swing
- Real vinyl wow/flutter ranges from 0.1% to 2% of playback speed
- At 44.1kHz, 2% drift needs ~882 sample excursion, not 200
- **The "volume goes down" issue**: The wow/flutter section multiplies gain by `pitchMod = 1.0 + (wow + flutter)`. At max warp, this modulates +-0.3%. That's NOTHING. Real wow/flutter should modulate the PITCH via delay line, not multiply gain. My implementation fakes it with amplitude modulation instead of actual pitch modulation.

**PsychedelicProcessor chorus/phaser:**
- Chorus depth maxes at 0.005 * sr = ~220 samples. That's OK for chorus.
- BUT: chorus mix is hardcoded at 70/30 dry/wet. Should be controllable.
- The notch sweep Q is 2.5 -- too narrow. Real Enigma sweep uses wider notches (Q 0.5-1.5) for a more audible effect.
- Sweep rate 0.05-1.5 Hz range is reasonable but the LFO is single sine -- real units use more complex modulation.

### Problem 2: LFO is invisible and unintuitive
**What Xfer LFO Tool has that we don't:**
1. **Visual grid editor** -- THE feature. You SEE the waveform shape on a grid. You can DRAW custom curves with nodes/tension. This is 80% of the product.
2. **12 switchable graphs** per preset
3. **Node snapping** to grid (Ctrl-click snaps to beat division, Shift-click creates step pairs)
4. **Routing matrix** -- shape can target Volume, Pan, Filter Cutoff, Resonance independently
5. **MIDI retrigger** -- cycle restarts on note-on
6. **Scope view** -- see the LFO affecting the actual audio in real time
7. **Smooth control** -- prevents clicks at cycle boundaries
8. **PWM/Swing** controls for rhythmic variation

**What we have:** A dropdown shape selector and a rate knob. No visual feedback. No grid. The user can't see what the LFO is doing.

### Problem 3: Wow/Flutter is gain modulation, not pitch modulation
**Current (wrong):**
```cpp
float pitchMod = 1.0f + wow + flutter;
processed *= pitchMod;  // This just changes volume slightly!
```
**Should be:** Modulate the delay read position (which we already do for detune but NOT for wow/flutter). The wow/flutter should add to the delay line modulation, not multiply the signal amplitude.

## Plan for v3.0

### Phase 1: Fix the DSP (make it sound right)
1. **VinylProcessor:** Move wow/flutter into the delay line modulation (pitch-shift, not gain). Increase detune excursion range. Both wow and flutter should modulate the playback speed, which means modulating the delay read position.
2. **PsychedelicProcessor:** Widen notch Q to 0.7-1.2. Increase chorus depth range. Add controllable wet/dry. Consider all-pass filter chain for proper phaser (instead of notch filters).
3. **LFO:** Needs complete rethink -- see Phase 2.

### Phase 2: Visual LFO Grid Editor (the real product)
1. Build a JUCE Component that draws a grid with beat divisions
2. Store waveform as array of nodes with (time, value, tension) 
3. Interpolate between nodes using cubic bezier or catmull-rom
4. Display current playback position as animated cursor
5. Allow click-drag to create/move nodes
6. Snap to grid based on sync rate
7. This replaces the shape dropdown entirely

### Phase 3: Polish
1. Preset system with factory presets
2. Per-section bypass buttons that actually work visually
3. Proper gain staging throughout
4. A/B comparison
