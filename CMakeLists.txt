cmake_minimum_required(VERSION 3.22)

project(Aether VERSION 1.0.0)

# JUCE path
set(JUCE_PATH "/tmp/JUCE")
add_subdirectory(${JUCE_PATH} ${CMAKE_BINARY_DIR}/JUCE)

# Plugin target
juce_add_plugin(Aether
    COMPANY_NAME "AetherAudio"
    IS_SYNTH FALSE
    NEEDS_MIDI_INPUT FALSE
    NEEDS_MIDI_OUTPUT FALSE
    IS_MIDI_EFFECT FALSE
    EDITOR_WANTS_KEYBOARD_FOCUS FALSE
    COPY_PLUGIN_AFTER_BUILD TRUE
    PLUGIN_MANUFACTURER_CODE AeAu
    PLUGIN_CODE Athr
    FORMATS AU VST3 Standalone
    PRODUCT_NAME "Aether"
    BUNDLE_ID "com.aetheraudio.aether"
    AU_MAIN_TYPE "kAudioUnitType_Effect"
    VST3_CATEGORIES "Fx"
)

# Binary resources (background + per-section knob filmstrips)
juce_add_binary_data(AetherData
    SOURCES
        resources/background.png
        resources/knob-swell.png
        resources/knob-vinyl.png
        resources/knob-master.png
        resources/knob-psyche.png
        resources/knob-lfo.png
)

# Source files
target_sources(Aether
    PRIVATE
        src/PluginProcessor.cpp
        src/PluginProcessor.h
        src/PluginEditor.cpp
        src/PluginEditor.h
        src/dsp/TransientShaper.h
        src/dsp/VinylProcessor.h
        src/dsp/PsychedelicProcessor.h
        src/dsp/LFOProcessor.h
)

# JUCE modules
target_compile_definitions(Aether
    PUBLIC
        JUCE_WEB_BROWSER=0
        JUCE_USE_CURL=0
        JUCE_VST3_CAN_REPLACE_VST2=0
        JUCE_DISPLAY_SPLASH_SCREEN=0
)

target_link_libraries(Aether
    PRIVATE
        AetherData
        juce::juce_audio_utils
        juce::juce_dsp
        juce::juce_gui_extra
    PUBLIC
        juce::juce_recommended_config_flags
        juce::juce_recommended_lto_flags
        juce::juce_recommended_warning_flags
)
