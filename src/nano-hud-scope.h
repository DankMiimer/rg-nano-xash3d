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
#ifndef NANO_HUD_SCOPE_H
#define NANO_HUD_SCOPE_H
#include <string.h>
class NanoHudScope {
    float oldScale, oldX, oldY, oldDX, oldDY;
    float scale, anchorX, anchorY;
    bool enabled;
public:
    NanoHudScope(const char *setting, float x, float y) {
        float value=gEngfuncs.pfnGetCvarFloat(setting);
        // Retain the physical footprint of radar and sprite crosshairs.
        if (!strcmp(setting,"nano_hud_radar") || !strcmp(setting,"nano_hud_crosshair")) value*=0.65f;
        Init(value,x,y);
    }
    NanoHudScope(float value,float x,float y) { Init(value,x,y); }
    float Scale() const { return enabled ? scale : 1.0f; }
    void Init(float value,float x,float y) {
        enabled = gEngfuncs.pfnGetCvarPointer("nano_hud_element_scale") &&
            gEngfuncs.pfnGetCvarFloat("nano_hud_profile") != 0;
        if (!enabled) return;
        oldScale = gEngfuncs.pfnGetCvarFloat("nano_hud_element_scale");
        oldX = gEngfuncs.pfnGetCvarFloat("nano_hud_anchor_x");
        oldY = gEngfuncs.pfnGetCvarFloat("nano_hud_anchor_y");
        oldDX = gEngfuncs.pfnGetCvarFloat("nano_hud_offset_x");
        oldDY = gEngfuncs.pfnGetCvarFloat("nano_hud_offset_y");
        scale = value;
        anchorX = x; anchorY = y;
        if (!(scale >= 0.25f && scale <= 4.0f)) scale = 1.0f;
        gEngfuncs.Cvar_SetValue("nano_hud_element_scale", scale);
        gEngfuncs.Cvar_SetValue("nano_hud_anchor_x", x);
        gEngfuncs.Cvar_SetValue("nano_hud_anchor_y", y);
        gEngfuncs.Cvar_SetValue("nano_hud_offset_x", 0);
        gEngfuncs.Cvar_SetValue("nano_hud_offset_y", 0);
    }
    // Move the complete group, including its widest numbers, to a screen edge.
    // Bounds/offsets are in HUD coordinates; the engine converts to pixels once.
    void Place(float left, float top, float right, float bottom,
        float targetX, float targetY, float insetX = 2, float insetY = 2) {
        if (!enabled) return;
        float width = (right-left)*scale, height = (bottom-top)*scale;
        float x = anchorX*gHUD.m_scrinfo.iWidth + (left-anchorX*gHUD.m_scrinfo.iWidth)*scale;
        float y = anchorY*gHUD.m_scrinfo.iHeight + (top-anchorY*gHUD.m_scrinfo.iHeight)*scale;
        gEngfuncs.Cvar_SetValue("nano_hud_offset_x",
            insetX + targetX*(gHUD.m_scrinfo.iWidth-2*insetX-width) - x);
        gEngfuncs.Cvar_SetValue("nano_hud_offset_y",
            insetY + targetY*(gHUD.m_scrinfo.iHeight-2*insetY-height) - y);
    }
    void Reset() {
        if (!enabled) return;
        gEngfuncs.Cvar_SetValue("nano_hud_element_scale", oldScale);
        gEngfuncs.Cvar_SetValue("nano_hud_anchor_x", oldX);
        gEngfuncs.Cvar_SetValue("nano_hud_anchor_y", oldY);
        gEngfuncs.Cvar_SetValue("nano_hud_offset_x", oldDX);
        gEngfuncs.Cvar_SetValue("nano_hud_offset_y", oldDY);
        enabled = false;
    }
    ~NanoHudScope() { Reset(); }
private:
    NanoHudScope(const NanoHudScope &);
    NanoHudScope &operator=(const NanoHudScope &);
};
#endif
