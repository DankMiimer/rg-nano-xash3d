# SPDX-License-Identifier: GPL-3.0-or-later
"""Render both clients' actual native ammo branch through the engine transform."""
import os,subprocess
from pathlib import Path
root=Path(__file__).resolve().parents[1];native=Path(os.environ.get('NANO_NATIVE_DIR','/var/tmp/rg-nano-xash3d-source-build'))
def block(source,start):
 brace=source.index('{',start);end=brace+1;depth=1
 while depth:depth+=(source[end]=='{')-(source[end]=='}');end+=1
 return source[start:end]
engine=(native/'xash3d/engine/client/dll_int/cl_game.c').read_text()
transform=block(engine,engine.index('void SPR_AdjustSize('))
for name,source,dw,dh,scale in [('hl',native/'hlsdk/cl_dll/ammo.cpp',12,16,2.0),('cs',root/'upstream/cs16-client/cl_dll/ammo.cpp',20,25,.8)]:
 text=source.read_text();start=text.index('if(NanoHudActive())',text.index('int CHudAmmo::Draw('));draw=block(text,start)
 code=r'''
#include <cassert>
#include <cstdio>
#include <cmath>
#include <cstring>
#include <vector>
#define max(a,b) ((a)>(b)?(a):(b))
#define Q_max max
#include "nano-hud-transform.h"
struct cvar_t{float value;};
static cvar_t profile={1},scaleVar={1},ax={0},ay={0},dx={0},dy={0},pixels={0},bottom={DEFAULT_SCALE};
static cvar_t *nano_hud_profile=&profile,*nano_hud_scale=&scaleVar,*nano_hud_ax=&ax,*nano_hud_ay=&ay,*nano_hud_dx=&dx,*nano_hud_dy=&dy,*nano_hud_pixels=&pixels;
static int nanoCrosshairDrawing=0;
static float Cvar_VariableValue(const char*){return 1;}
static struct{int width,height;}refState={240,240};
static struct{struct{int iWidth,iHeight;}scrInfo;}clgame={{240,240}};
static cvar_t *get(const char *s){if(!strcmp(s,"nano_hud_profile"))return &profile;if(!strcmp(s,"nano_hud_bottom"))return &bottom;if(!strcmp(s,"nano_hud_element_scale"))return &scaleVar;if(!strcmp(s,"nano_hud_anchor_x"))return &ax;if(!strcmp(s,"nano_hud_anchor_y"))return &ay;if(!strcmp(s,"nano_hud_offset_x"))return &dx;if(!strcmp(s,"nano_hud_offset_y"))return &dy;return &profile;}
static float val(const char *s){return get(s)->value;}static void set(const char*s,float v){get(s)->value=v;}
static struct{cvar_t*(*pfnGetCvarPointer)(const char*);float(*pfnGetCvarFloat)(const char*);void(*Cvar_SetValue)(const char*,float);}gEngfuncs={get,val,set};
struct wrect_t{int left,top,right,bottom;};
static std::vector<wrect_t>rectangles;
void SPR_AdjustSize(float*,float*,float*,float*);
static void record(int x,int y,int w,int h){float a=x,b=y,c=w,d=h;SPR_AdjustSize(&a,&b,&c,&d);rectangles.push_back({(int)a,(int)b,(int)(a+c),(int)(b+d)});}
static const int AmmoWidth=DIGIT_WIDTH,ScreenWidth=240;
static struct HUD{struct{int iWidth,iHeight;}m_scrinfo={240,240};int m_iFontHeight=DIGIT_HEIGHT;wrect_t cross={0,0,16,16};wrect_t GetSpriteRect(int){return cross;}int GetSpriteIndex(const char*){return 0;}int DrawHudNumber(int x,int y,int,int,int,int,int){record(x,y,3*AmmoWidth,m_iFontHeight);return x+3*AmmoWidth;}}gHUD;
namespace DrawUtils {static int DrawHudNumber(int x,int y,int f,int v,int r,int g,int b){return gHUD.DrawHudNumber(x,y,f,v,r,g,b);}}
#include "nano-hud-layout.h"
#include "nano-hud-scope.h"
static struct{int CountAmmo(int){return 999;}}gWR;
static void FillRGBA(int x,int y,int w,int h,int,int,int,int){record(x,y,w,h);}
static void SPR_Set(int,int,int,int){}
static void SPR_DrawAdditive(int,int x,int y,wrect_t *r){record(x,y,r->right-r->left,r->bottom-r->top);}
#define DHN_3DIGITS 1
struct weapon{int iClip,iAmmoType,iAmmo2Type;wrect_t rcAmmo,rcAmmo2;int hAmmo,hAmmo2;};
static int render(weapon *pw){int iFlags=0,r=255,g=140,b=0,a=255;
''' + draw + r'''return 0;}
int main(){
 for(float s: {DEFAULT_SCALE,MAX_SCALE})for(int clip: {-1,0,9,999})for(int icon: {16,24,32})for(int secondary: {0,1}){
  bottom.value=s;rectangles.clear();weapon w={clip,1,secondary,{0,0,icon,DIGIT_HEIGHT},{0,0,16,DIGIT_HEIGHT},1,2};assert(render(&w)==1);
  float healthEnd=4+(8+HEALTH_RESERVE*AmmoWidth)*s;
  for(auto r:rectangles){if(!(r.left>=4 && r.top>=0 && r.right<=237 && r.bottom<=237))fprintf(stderr,"scale %.2f clip %d icon %d secondary %d: %d %d %d %d\n",s,clip,icon,secondary,r.left,r.top,r.right,r.bottom);assert(r.left>=4 && r.top>=0 && r.right<=237 && r.bottom<=237);
   if(r.bottom>240-(int)ceilf(2*DIGIT_HEIGHT*s)-8)assert(r.left>=healthEnd-1);
  }
  assert(scaleVar.value==1 && dx.value==0 && dy.value==0);
 }
}
'''
 code=code.replace('DEFAULT_SCALE',str(scale)+'f').replace('MAX_SCALE','2.0f' if name=='hl' else '1.0f').replace('DIGIT_WIDTH',str(dw)).replace('DIGIT_HEIGHT',str(dh)).replace('HEALTH_RESERVE','4.1f' if name=='hl' else '3.5f')
 code=code.replace('namespace DrawUtils {static int','namespace DrawUtils {int')
 code=code.replace('static int render(',transform+'\nstatic int render(')
 out=root/'build'/('test-native-ammo-'+name+'.cpp');out.write_text(code);exe=out.with_suffix('')
 subprocess.run(['g++','-std=c++11','-Wall','-Wextra','-fsanitize=address,undefined','-I'+str(root/'src'),str(out),'-o',str(exe)],check=True);subprocess.run([str(exe)],check=True)
 print(name+': native ammo counters, wide icons, split rows, secondary ammo, bounds and health/armor clearance passed')
