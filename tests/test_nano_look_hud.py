# SPDX-License-Identifier: GPL-3.0-or-later
"""Exercise the actual helpers and both patched client yaw functions."""
from pathlib import Path
import os, subprocess
root=Path(__file__).resolve().parents[1]
native=Path(os.environ.get('NANO_NATIVE_DIR',str(root/'build/native')))
code=r'''#include <assert.h>
#include <math.h>
#include "nano-look.h"
#include "nano-hud-transform.h"
#include "nano-crosshair.h"
struct cvar_t { float value; };
struct kbutton_t { int state; };
static kbutton_t in_speed, in_strafe, in_right, in_left, in_klook, in_forward, in_back, in_lookup, in_lookdown;
static cvar_t yaw={70}, pitch={75}, angle={0.67f}, down={89}, up={89};
static cvar_t en={1}, delay={0.15f}, ramp={0.75f}, maximum={210}, fast={0};
static cvar_t *cl_yawspeed=&yaw, *cl_pitchspeed=&pitch, *cl_anglespeedkey=&angle, *cl_pitchdown=&down, *cl_pitchup=&up;
static cvar_t *nano_look_accel=&en, *nano_look_delay=&delay, *nano_look_ramp=&ramp, *nano_look_max_yaw=&maximum, *nano_look_fast=&fast;
static NanoLookState nanoYaw={0,0};
#define YAW 1
#define PITCH 0
#define ROLL 2
static float anglemod(float x) { return x; }
static float CL_KeyState(kbutton_t *b) { float held=(b->state & 1)?1:0; b->state &= 1; return held; }
'''
engine=(native/'xash3d/engine/client/dll_int/cl_game.c').read_text()
start=engine.index('static void SPR_AdjustTexCoords(');brace=engine.index('{',start);depth=1;end=brace+1
while depth:
    depth+=(engine[end]=='{')-(engine[end]=='}');end+=1
uv=engine[start:end]
code += r'''
static cvar_t *nano_hud_profile=&en;
typedef bool qboolean;
struct { int width,height; } refState={240,240};
struct { struct { int iWidth,iHeight; } scrInfo; } clgame={{369,369}};
#define PARM_TEX_FILTERING 0
#define REF_GET_PARM(a,b) ((void)(a),(void)(b),0)
''' + uv
start=engine.index('void SPR_AdjustSize(');brace=engine.index('{',start);depth=1;end=brace+1
while depth:
    depth+=(engine[end]=='{')-(engine[end]=='}');end+=1
code += r'''
#include <string.h>
static cvar_t scaleVar={1}, axVar={0}, ayVar={0}, dxVar={0}, dyVar={0}, pixelVar={0}, bottomVar={1.125f};
static cvar_t *nano_hud_scale=&scaleVar, *nano_hud_ax=&axVar, *nano_hud_ay=&ayVar;
static cvar_t *nano_hud_dx=&dxVar, *nano_hud_dy=&dyVar, *nano_hud_pixels=&pixelVar;
static int nanoCrosshairDrawing;
static float Cvar_VariableValue(const char *) { return 2; }
static bool extension=true;
static cvar_t *MockCvar(const char *name) {
    if (!extension) return 0;
    if (!strcmp(name,"nano_hud_profile")) return &en;
    if (!strcmp(name,"nano_hud_element_scale")) return &scaleVar;
    if (!strcmp(name,"nano_hud_anchor_x")) return &axVar;
    if (!strcmp(name,"nano_hud_anchor_y")) return &ayVar;
    if (!strcmp(name,"nano_hud_offset_x")) return &dxVar;
    if (!strcmp(name,"nano_hud_offset_y")) return &dyVar;
    if (!strcmp(name,"nano_hud_bottom")) return &bottomVar;
    return 0;
}
static float MockFloat(const char *name) { cvar_t *v=MockCvar(name); return v?v->value:0; }
static void MockSet(const char *name,float value) { cvar_t *v=MockCvar(name); if(v) v->value=value; }
struct MockEngine { cvar_t *(*pfnGetCvarPointer)(const char *); float (*pfnGetCvarFloat)(const char *); void (*Cvar_SetValue)(const char *,float); };
static MockEngine gEngfuncs={MockCvar,MockFloat,MockSet};
struct MockHUD { struct { int iWidth,iHeight; } m_scrinfo; };
static MockHUD gHUD={{369,369}};
#include "nano-hud-scope.h"
''' + engine[start:end]

for name,src in [('hl',native/'hlsdk/cl_dll/input.cpp'),('cs',root/'upstream/cs16-client/cl_dll/input.cpp')]:
    text=src.read_text();start=text.index('void CL_AdjustAngles');brace=text.index('{',start);depth=1;end=brace+1
    while depth:
        depth+=(text[end]=='{')-(text[end]=='}');end+=1
    fn=text[start:end]
    checks=r'''
int main() {
    NanoLookState s={0,0};
    assert(NanoLookRate(&s,1,1,0.01f,0.15f,0.75f,70,210,0)==70);
    float previous=70;
    for(int i=0;i<100;i++) {
        float rate=NanoLookRate(&s,1,0,0.01f,0.15f,0.75f,70,210,0);
        assert(rate>=previous && rate<=210);previous=rate;
    }
    assert(previous==210);
    assert(NanoLookRate(&s,-1,0,0.01f,0.15f,0.75f,70,210,0)==70);
    NanoLookRate(&s,0,0,0.01f,0.15f,0.75f,70,210,0);
    assert(NanoLookRate(&s,-1,0,0.01f,0.15f,0.75f,70,210,0)==70);
    assert(NanoLookRate(&s,1,0,0.01f,0.15f,0.75f,70,210,1)==210);
    assert(NanoLookRate(&s,1,0,0.01f,0.15f,0.75f,70,210,0)==70);
    NanoLookState a={0,0},b={0,0};
    NanoLookRate(&a,1,1,0,0.15f,0.75f,70,210,0);
    NanoLookRate(&b,1,1,0,0.15f,0.75f,70,210,0);
    float ra=0,rb=0;
    for(int i=0;i<30;i++) ra=NanoLookRate(&a,1,0,1.0f/30,0.15f,0.75f,70,210,0);
    for(int i=0;i<100;i++) rb=NanoLookRate(&b,1,0,0.01f,0.15f,0.75f,70,210,0);
    assert(fabsf(ra-rb)<0.01f);
    assert(NanoLookRate(&a,1,0,1.0f,0.15f,0.75f,70,210,0)==70);
    float v[3]={0,0,0};in_right.state=3;
    CL_AdjustAngles(0.01f,v);assert(fabsf(v[YAW]+0.7f)<0.001f);
    for(int i=0;i<100;i++) CL_AdjustAngles(0.01f,v);
    float oldYaw=v[YAW];CL_AdjustAngles(0.01f,v);assert(fabsf(v[YAW]-oldYaw+2.1f)<0.001f);
    // R strafing: no yaw, and turn-key state remains available for sidemove.
    in_strafe.state=1;oldYaw=v[YAW];CL_AdjustAngles(0.01f,v);
    assert(v[YAW]==oldYaw && (in_right.state&1));
    in_klook.state=1;in_forward.state=1;v[PITCH]=0;
    for(int i=0;i<100;i++) CL_AdjustAngles(0.01f,v);
    assert(fabsf(v[PITCH]+75)<0.01f); // pitch never ramps
    float x=20,y=220,w=24,h=16;
    NanoHudRect(&x,&y,&w,&h,240,240,1.125f,0,1);
    assert(x==23 && y==218 && w==27 && h==18);
    x=210;y=220;w=24;h=16;
    NanoHudRect(&x,&y,&w,&h,240,240,1.125f,1,1);
    assert(x==206 && y==218 && w==27 && h==18);
    x=0;y=0;w=80;h=80;
    NanoHudRect(&x,&y,&w,&h,240,240,0.5f,0,0);
    assert(x==0 && y==0 && w==40 && h==40);
    x=120;y=120;w=0.65f;h=3.25f;
    NanoHudRect(&x,&y,&w,&h,240,240,1,0.5f,0.5f);
    assert(x==120 && y==120 && w==1 && h==3);
    x=-8;y=0;w=8;h=8;
    NanoHudRect(&x,&y,&w,&h,240,240,NAN,NAN,NAN);
    assert(x==-8 && w==8 && h==8);
    // Exercise the actual scope and engine: complete blocks at both lower edges.
    {
        NanoHudScope health("nano_hud_bottom",0,1);
        health.Place(10,330,100,354,0,1);
        float hx=10,hy=330,hw=90,hh=24;
        SPR_AdjustSize(&hx,&hy,&hw,&hh);
        assert(hx>=0 && hx<=2 && hy+hh<=240 && hy+hh>=238);
        float savedDX=dxVar.value,savedDY=dyVar.value;
        {
            NanoHudScope ammo("nano_hud_bottom",1,1);
            ammo.Place(210,330,366,354,1,1);
            float ax=210,ay=330,aw=156,ah=24;
            SPR_AdjustSize(&ax,&ay,&aw,&ah);
            assert(ax+aw<=240 && ax+aw>=238 && ay+ah<=240);
            assert(ax>hx+hw); // groups do not overlap
        }
        assert(scaleVar.value==1.125f && axVar.value==0 && ayVar.value==1);
        assert(dxVar.value==savedDX && dyVar.value==savedDY);
    }
    assert(scaleVar.value==1 && axVar.value==0 && ayVar.value==0 && dxVar.value==0 && dyVar.value==0);
    extension=false;
    { NanoHudScope fallback("nano_hud_bottom",0,1); fallback.Place(10,330,100,354,0,1); }
    assert(scaleVar.value==1 && dxVar.value==0 && dyVar.value==0);
    extension=true;
    // Physical crosshair fills bypass logical integer truncation exactly once.
    pixelVar.value=1;x=112;y=120;w=5;h=1;
    SPR_AdjustSize(&x,&y,&w,&h);
    assert(x==112 && y==120 && w==5 && h==1);
    pixelVar.value=0;
    NanoCrosshairRect arms[4];
    for (int size=239; size<=241; ++size) for (int gap=0; gap<18; ++gap) {
        NanoCrosshairRects(size,size,gap+0.35f,5.4f,arms);
        int center=size/2;
        assert(arms[0].w==arms[1].w && arms[2].h==arms[3].h);
        assert(arms[0].x+arms[0].w-1==2*center-arms[1].x);
        assert(arms[0].x==2*center-(arms[1].x+arms[1].w-1));
        assert(arms[2].y+arms[2].h-1==2*center-arms[3].y);
        assert(arms[2].y==2*center-(arms[3].y+arms[3].h-1));
        assert(arms[0].y==center && arms[1].y==center);
        assert(arms[2].x==center && arms[3].x==center);
    }
    float s1=32,s2=48,t1=16,t2=40;
    SPR_AdjustTexCoords(1,256,128,&s1,&t1,&s2,&t2);
    assert(s1==0.125f && s2==0.1875f && t1==0.125f && t2==0.3125f);
    en.value=0;s1=32;s2=48;t1=16;t2=40;
    SPR_AdjustTexCoords(1,256,128,&s1,&t1,&s2,&t2);
    assert(s1==32.5f/256 && s2==47.5f/256 && t1==16.5f/128 && t2==39.5f/128);
    return 0;
}
'''
    out=root/'build'/('test-nano-'+name+'.cpp');out.write_text(code+fn+checks)
    exe=out.with_suffix('')
    subprocess.run(['g++','-std=c++11','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-fno-omit-frame-pointer','-I'+str(root/'src'),str(out),'-o',str(exe)],check=True)
    subprocess.run([str(exe)],check=True)
    print(name+': yaw ramp, release/reversal, fast override, unchanged pitch/strafe, HUD anchors/pixel coverage passed')
