# SPDX-License-Identifier: GPL-2.0-or-later
"""Exercise the persistent objective drawing path and scope on real client code."""
from pathlib import Path
import subprocess
root=Path(__file__).resolve().parents[1]
s=(root/'upstream/cs16-client/cl_dll/text_message.cpp').read_text()
start=s.index('void CHudTextMessage::InitHUDData()');actual=s[start:]
code=r'''
#include <cassert>
#include <cstring>
#include <map>
#include <string>
#include <vector>
struct Engine {
 std::map<std::string,float> values;
 float pfnGetCvarFloat(const char *s){return values[s];}
 void *pfnGetCvarPointer(const char *){return this;}
 void Cvar_SetValue(const char *s,float f){values[s]=f;}
}gEngfuncs;
struct {struct {int iWidth=240,iHeight=240;}m_scrinfo;}gHUD;
#define ScreenWidth 240
#define ScreenHeight 240
#include "nano-hud-layout.h"
#include "nano-hud-scope.h"
struct Cell{float x,y,w,h;};static std::vector<Cell> cells;
namespace DrawUtils {
int ConsoleStringLen(const char *s){return strlen(s)*7;}
void DrawConsoleString(int x,int y,const char *s){
 float k=gEngfuncs.pfnGetCvarFloat("nano_hud_element_scale");
 float ax=gEngfuncs.pfnGetCvarFloat("nano_hud_anchor_x")*240,ay=gEngfuncs.pfnGetCvarFloat("nano_hud_anchor_y")*240;
 cells.push_back({ax+(x-ax)*k,ay+(y-ay)*k,ConsoleStringLen(s)*k,14*k});
}}
struct CHudTextMessage {char nanoCenterText[1024]={0};float nanoCenterUntil=0;int m_iFlags=0;void InitHUDData();int Draw(float);};
'''+actual+r'''
int main(){
 gEngfuncs.values={{"nano_hud_profile",1},{"nano_hud_text_height",14},{"nano_hud_element_scale",1}};
 CHudTextMessage message;strcpy(message.nanoCenterText,"Bomb has been planted! Stay clear of the explosion.");message.nanoCenterUntil=8;message.m_iFlags=1;
 for(float time: {1.f,2.f,7.99f}){
  cells.clear();message.Draw(time);assert(cells.size()>1);
  for(auto c:cells){assert(c.x>=7 && c.x+c.w<=233 && c.y>=0 && c.y+c.h<=240);assert(c.h==16);}
  assert(gEngfuncs.pfnGetCvarFloat("nano_hud_element_scale")==1 && message.m_iFlags==1);
 }
 gEngfuncs.values["nano_text_menu"]=1;cells.clear();message.Draw(7);assert(cells.empty() && message.m_iFlags==1);gEngfuncs.values["nano_text_menu"]=0;
 cells.clear();message.Draw(8);assert(cells.empty() && message.m_iFlags==0);
 message.InitHUDData();assert(message.nanoCenterText[0]==0 && message.nanoCenterUntil==0);
}
'''
p=root/'build/ui-profile-v2/objective-test.cpp';p.write_text(code);exe=p.with_suffix('')
subprocess.run(['g++','-std=c++11','-fsanitize=address,undefined','-I'+str(root/'src'),str(p),'-o',str(exe)],check=True)
subprocess.run([str(exe)],check=True)
print('Persistent objectives: 16px cells, wrapping, bounds, full display duration, expiry and scope restoration passed.')
