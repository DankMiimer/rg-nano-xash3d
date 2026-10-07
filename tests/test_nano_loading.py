# SPDX-License-Identifier: GPL-3.0-or-later
"""Test the real loading bar and rate-limited engine progress callback."""
from pathlib import Path
import os, subprocess, tempfile
root=Path(__file__).resolve().parents[1]
native=Path(os.environ.get('NANO_NATIVE_DIR',str(root/'build/native')))
bar=(root/'upstream/cs16-client/3rdparty/mainui_cpp/controls/ProgressBar.cpp').read_text()
bar=bar[bar.index('float CMenuProgressBar::GetValue'):]
engine=(native/'xash3d/engine/client/cl_main.c').read_text()
helper=engine[engine.index('static void CL_NanoResourceProgress'):engine.index('qboolean CL_PrecacheResources')]
code=r'''
#include <cassert>
#include <cmath>
#include <algorithm>
using std::max;using std::min;
#define bound(a,b,c) max(a,min(b,c))
#define Q_max(a,b) max(a,b)
static float percent;static bool nano=true;
namespace EngFuncs{static float GetCvarFloat(const char*){return percent;}}
struct{float realTime;}uiStatic;
struct Pos{int x,y;};struct Size{int w,h;};
struct Rect{int x,y,w,h;};static Rect rects[8];static int fills;
static void UI_FillRect(int x,int y,int w,int h,unsigned){assert(x>=0 && y>=0 && w>=0 && h>=0 && x+w<=240 && y+h<=240);rects[fills++]={x,y,w,h};}
static void UI_FillRect(Pos p,Size s,unsigned c){UI_FillRect(p.x,p.y,s.w,s.h,c);}
static void UI_DrawRectangle(Pos,Size,unsigned){}
static bool NanoThemeEnabled(){return nano;}
static unsigned NanoThemeField(){return 0;}static unsigned NanoThemeAccent(){return 1;}
static void NanoThemeBevel(int x,int y,int w,int h,unsigned c,bool){UI_FillRect(x,y,w,h,c);}
static unsigned uiInputBgColor,uiInputFgColor,colorBase;
class CMenuProgressBar{public:float m_flMin=0,m_flMax=100,m_flValue=0;const char *m_szCvarName="scr_loading";Pos m_scPos={20,158};Size m_scSize={200,14};float GetValue()const;void Draw();};
'''+bar+r'''
typedef bool qboolean;
static double clockTime;static int beginCount,endCount,menuCount;static float cvarValue;
enum{ca_active=4};struct{int state=2;}cls;struct{bool background=false;}cl;
struct{double realtime=123;}host;
static float Cvar_VariableValue(const char*){return nano;}
static void Cvar_SetValue(const char*,float x){cvarValue=x;assert(x>=0 && x<=100);}
static double Platform_DoubleTime(){return clockTime;}
static void Begin(bool active){assert(!active);++beginCount;}
static void Mode(bool two){assert(two);}
static void End(){++endCount;}
static void UI_UpdateMenu(double){++menuCount;}
struct{bool initialized=true;struct{void(*R_BeginFrame)(bool)=Begin;void(*R_Set2DMode)(bool)=Mode;void(*R_EndFrame)()=End;}dllFuncs;}ref;
'''+helper+r'''
int main(){
 CMenuProgressBar bar;
 for(float progress:{-10.f,0.f,1.f,50.f,100.f,150.f})for(float time:{0.f,.5f,1.25f,2.f}){
  percent=progress;uiStatic.realTime=time;fills=0;bar.Draw();assert(fills==2);
  assert(rects[1].x>=22 && rects[1].x+rects[1].w<=218 && rects[1].y==160 && rects[1].h==10);
  if(percent<=0)assert(rects[1].w==49);if(percent>=100)assert(rects[1].w==196);
 }
 bar.m_szCvarName=nullptr;bar.m_flValue=.6f;assert(bar.GetValue()==.6f);
 double next=0;CL_NanoResourceProgress(0,20,&next,true);assert(cvarValue==0 && beginCount==1);
 clockTime=.1;CL_NanoResourceProgress(3,20,&next,false);assert(cvarValue==15 && beginCount==1);
 clockTime=.3;CL_NanoResourceProgress(10,20,&next,false);assert(cvarValue==50 && beginCount==2);
 CL_NanoResourceProgress(20,20,&next,true);assert(cvarValue==100 && beginCount==3);
 assert(beginCount==endCount && beginCount==menuCount);
 cls.state=ca_active;CL_NanoResourceProgress(0,0,&next,true);assert(beginCount==3);
 cls.state=2;cl.background=true;CL_NanoResourceProgress(0,0,&next,true);assert(beginCount==3);
 cl.background=false;nano=false;CL_NanoResourceProgress(0,0,&next,true);assert(beginCount==3);
}
'''
with tempfile.TemporaryDirectory() as folder:
    file=Path(folder)/'loading.cpp';file.write_text(code);exe=file.with_suffix('')
    subprocess.run(['g++','-std=c++11','-fsanitize=address,undefined',str(file),'-o',str(exe)],check=True)
    subprocess.run([str(exe)],check=True)
print('Loading: visible busy segment, bounded real progress, forced final update, 4Hz redraw limit and gameplay/background exclusions passed.')
