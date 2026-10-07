// SPDX-License-Identifier: MIT
// Copyright (c) 2026 rg-nano-xash3d contributors
// Permission is hereby granted, free of charge, to any person obtaining a copy
// of this software and associated documentation files, to deal in the Software
// without restriction, including without limitation the rights to use, copy,
// modify, merge, publish, distribute, sublicense, and/or sell copies, and to
// permit persons to whom the Software is furnished to do so, subject to the
// following conditions: the above copyright notice and this permission notice
// shall be included in all copies or substantial portions of the Software.
// THE SOFTWARE IS PROVIDED AS IS, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
// IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
// FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
// AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
// LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
// OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
// THE SOFTWARE.
#ifndef NANO_SETTINGS_H
#define NANO_SETTINGS_H
#include <math.h>
#include <stdio.h>
#include <stddef.h>

typedef struct {
    int limitFPS, frameSleep, lookAccel;
    float fps, delay, ramp;
    float yaw, pitch, fastMultiplier;
    float bottom, side, radar, crosshair, menu;
} NanoSettings;

static inline NanoSettings NanoSettingsDefaults(void)
{
    NanoSettings s={1,1,1,30,0.15f,0.75f,70,75,3,2.0f,2.0f,0.5f,1.5f,14};
    return s;
}

static inline NanoSettings NanoSettingsDefaultsForGame(int cs)
{
    NanoSettings s=NanoSettingsDefaults();
    if(cs) {s.bottom=s.side=0.8f;s.crosshair=2;}
    return s;
}

static inline float NanoSettingsStep(float value,float low,float high,float step,float fallback)
{
    if (!isfinite(value)) value=fallback;
    if (value<low) value=low;
    if (value>high) value=high;
    return low+roundf((value-low)/step)*step;
}

static inline NanoSettings NanoSettingsSanitize(NanoSettings s)
{
    s.limitFPS=!!s.limitFPS; s.frameSleep=!!s.frameSleep; s.lookAccel=!!s.lookAccel;
    s.fps=NanoSettingsStep(s.fps,15,60,5,30);
    s.delay=NanoSettingsStep(s.delay,0,0.5f,0.05f,0.15f);
    s.ramp=NanoSettingsStep(s.ramp,0.25f,1.5f,0.05f,0.75f);
    s.yaw=NanoSettingsStep(s.yaw,30,120,5,70);
    s.pitch=NanoSettingsStep(s.pitch,30,150,5,75);
    s.fastMultiplier=NanoSettingsStep(s.fastMultiplier,1,4,0.25f,3);
    // Native canvas: layout stacks groups when a selected size needs more room.
    s.bottom=NanoSettingsStep(s.bottom,0.6f,2.0f,0.025f,1.5f);
    s.side=NanoSettingsStep(s.side,0.6f,2.0f,0.025f,1.5f);
    s.radar=NanoSettingsStep(s.radar,0.25f,0.75f,0.05f,0.5f);
    s.crosshair=NanoSettingsStep(s.crosshair,1,3,0.25f,2);
    s.menu=NanoSettingsStep(s.menu,12,18,2,14);
    return s;
}

static inline int NanoSettingsAimCommands(char *buffer,size_t size,NanoSettings settings)
{
    NanoSettings s=NanoSettingsSanitize(settings);
    int n=snprintf(buffer,size,
        "alias \"+nano_aim\" \"nano_look_fast 1; cl_yawspeed %.2f; cl_pitchspeed %.2f\"\n"
        "alias \"-nano_aim\" \"nano_look_fast 0; cl_yawspeed %.2f; cl_pitchspeed %.2f\"\n",
        s.yaw*s.fastMultiplier,s.pitch*s.fastMultiplier,s.yaw,s.pitch);
    return n>=0 && (size_t)n<size ? n : -1;
}

static inline int NanoSettingsSerialize(char *buffer,size_t size,NanoSettings settings)
{
    NanoSettings s=NanoSettingsSanitize(settings);
    char aim[256];
    if (NanoSettingsAimCommands(aim,sizeof(aim),s)<0) return -1;
    // Numeric whitelist only. Remember the slider value even when its toggle is off.
    int n=snprintf(buffer,size,
        "// Saved Nano settings; this game's choices override launcher defaults.\n"
        "set nano_fps_limit \"%d\"\nset nano_fps_value \"%.0f\"\n"
        "fps_max \"%.0f\"\ngl_vsync \"0\"\n"
        "set nano_frame_sleep \"%d\"\nnano_look_accel \"%d\"\n"
        "nano_look_delay \"%.2f\"\nnano_look_ramp \"%.2f\"\n"
        "set nano_aim_yaw \"%.0f\"\nset nano_aim_pitch \"%.0f\"\nset nano_aim_fast_multiplier \"%.2f\"\n"
        "cl_yawspeed \"%.0f\"\ncl_pitchspeed \"%.0f\"\nnano_look_max_yaw \"%.2f\"\nnano_look_fast \"0\"\n"
        "set nano_hud_bottom \"%.3f\"\nset nano_hud_side \"%.3f\"\nset nano_hud_radar \"%.2f\"\n"
        "set nano_hud_crosshair \"%.2f\"\nset nano_hud_menu \"1\"\nset nano_hud_text_height \"%.0f\"\nset nano_ui_profile_version \"3\"\n%s",
        s.limitFPS,s.fps,s.limitFPS?s.fps:0,s.frameSleep,s.lookAccel,s.delay,s.ramp,
        s.yaw,s.pitch,s.fastMultiplier,s.yaw,s.pitch,s.yaw*s.fastMultiplier,
        s.bottom,s.side,s.radar,s.crosshair,s.menu,aim);
    return n>=0 && (size_t)n<size ? n : -1;
}
#endif
