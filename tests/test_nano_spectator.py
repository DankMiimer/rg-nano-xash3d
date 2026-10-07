# SPDX-License-Identifier: GPL-3.0-or-later
"""Execute native spectator drawing/navigation across supported font sizes."""
from pathlib import Path
import subprocess, tempfile
root=Path(__file__).resolve().parents[1]
source=(root/'upstream/cs16-client/cl_dll/hud/spectator_gui.cpp').read_text()
source=source[source.index('static int NanoSpectatorWidth'):]
code=r'''
#include <cassert>
#include <cstdio>
#include <cstring>
#include <string>
#include <vector>
#include <algorithm>
using std::max;using std::min;
#define bound(a,b,c) max(a,min(b,c))
static int fontHeight=14,ScreenWidth=240,ScreenHeight=240,g_iUser1=4,g_iUser2=1;
static bool active=true,automatic=false;
static std::string command;
struct Engine {
 float pfnGetCvarFloat(const char *s){if(!strcmp(s,"nano_hud_text_height"))return fontHeight;if(!strcmp(s,"nano_hud_profile"))return active;if(!strcmp(s,"spec_autodirector"))return automatic;return 1;}
 void Cvar_SetValue(const char*,float){}
 void pfnClientCmd(char *s){command=s;}
}gEngfuncs;
#include "nano-hud-layout.h"
struct NanoHudScope{NanoHudScope(float,int,int){}};
struct Text{int x,y,w;std::string text;};static std::vector<Text> drawn;
namespace DrawUtils{
 int HudStringLen(const char *s){int n=0;for(;*s;++s)if(((unsigned char)*s&0xc0)!=0x80)n+=fontHeight/2;return n;}
 void DrawHudString(int x,int y,int right,const char *s,int,int,int){int w=HudStringLen(s);assert(x>=0 && y>=0 && x+w<=right && right<=240 && y+fontHeight<=240);drawn.push_back({x,y,w,s});}
}
static void FillRGBABlend(int x,int y,int w,int h,int,int,int,int){assert(x>=0 && y>=0 && w>=0 && h>=0 && x+w<=240 && y+h<=240);}
struct hud_player_info_t{const char *name;};
static const char *playerName="Åøö Long player with an extremely long name";
static void GetPlayerInfo(int,hud_player_info_t *p){p->name=playerName;}
#define MAX_PLAYERS 32
struct Extra{int sb_health,health,teamnumber;}g_PlayerExtraInfo[33];
static void GetTeamColor(int&r,int&g,int&b,int){r=158;g=195;b=255;}
enum{K_UPARROW=1,K_DOWNARROW,K_LEFTARROW,K_RIGHTARROW,K_ENTER,K_BACKSPACE};
class CHudSpectatorGui{
 public:
 enum{ROOT_MENU=1,MENU_OPTIONS=2,MENU_OPTIONS_SETTINGS=4,MENU_SPEC_OPTIONS=8};
 struct{int m_iCounterTerrorists=100000,m_iTerrorists=100000;char m_szTimer[32]="99:59",m_szMap[128]="de_extremely_long_map_name";}label;
 int m_menuFlags=0,nanoCursor=0;bool m_bBombPlanted=false;
 int NanoEntries(const char**,const char**);int NanoDraw();int NanoKey(int,int);
 void UserCmd_ToggleSpectatorMenu(){m_menuFlags^=ROOT_MENU;nanoCursor=0;}
 void UserCmd_ToggleSpectatorMenuOptions(){m_menuFlags^=MENU_OPTIONS;nanoCursor=0;}
 void UserCmd_ToggleSpectatorMenuOptionsSettings(){m_menuFlags^=MENU_OPTIONS_SETTINGS;nanoCursor=0;}
 void UserCmd_ToggleSpectatorMenuSpectateOptions(){m_menuFlags^=MENU_SPEC_OPTIONS;nanoCursor=0;}
};
'''+source+r'''
static bool has(const char *part){for(const auto &s:drawn)if(s.text.find(part)!=std::string::npos)return true;return false;}
int main(){
 CHudSpectatorGui ui;g_PlayerExtraInfo[1]={1000,100,2};
 for(fontHeight=12;fontHeight<=18;++fontHeight){
  for(g_iUser1=1;g_iUser1<=6;++g_iUser1){
   drawn.clear();ui.m_menuFlags=0;ui.NanoDraw();assert(has("CT:") && has("T:") && has("99:59") && has("Health:") && has("Åøö"));
   for(int flags:{1,3,7,9})for(int selected=0;selected<7;++selected){drawn.clear();ui.m_menuFlags=flags;ui.nanoCursor=selected;ui.NanoDraw();assert(has("A Select") && has("B Back"));}
  }
 }
 ui.m_menuFlags=3;ui.nanoCursor=2;ui.NanoKey(1,K_DOWNARROW);assert(ui.nanoCursor==4); // disabled PIP skipped
 ui.nanoCursor=999;command.clear();ui.NanoKey(1,K_ENTER);assert(command=="_spec_toggle_menu_options");
 ui.m_menuFlags=9;ui.NanoKey(1,K_BACKSPACE);assert(ui.m_menuFlags==1);
 ui.m_menuFlags=7;ui.NanoKey(1,K_BACKSPACE);assert(ui.m_menuFlags==3);ui.NanoKey(1,K_BACKSPACE);assert(ui.m_menuFlags==1);
 ui.NanoKey(1,K_BACKSPACE);assert(ui.m_menuFlags==0 && !ui.NanoKey(1,K_ENTER));
 fontHeight=14;ui.m_menuFlags=0;ui.m_bBombPlanted=true;automatic=true;g_iUser2=0;drawn.clear();ui.NanoDraw();assert(has("Bomb") && has("Auto") && has("Health: --"));
}
'''
with tempfile.TemporaryDirectory() as folder:
    file=Path(folder)/'spectator.cpp';file.write_text(code);exe=file.with_suffix('')
    subprocess.run(['g++','-std=c++11','-fsanitize=address,undefined','-I'+str(root/'src'),str(file),'-o',str(exe)],check=True)
    subprocess.run([str(exe)],check=True)
print('Spectator: all modes/menu pages at 12–18px, long names/scores, health, camera navigation, Back and disabled PIP passed.')
