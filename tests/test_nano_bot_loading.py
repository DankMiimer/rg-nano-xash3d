# SPDX-License-Identifier: GPL-3.0-or-later
"""Exercise the actual BotProgress parser, stage transitions and loading input gate."""
from pathlib import Path
import subprocess,tempfile
r=Path(__file__).resolve().parents[1]
s=(r/'upstream/cs16-client/cl_dll/hud/timer.cpp').read_text()
def function(s,name):
 a=s.index(name);e=s.index('{',a)+1;d=1
 while d:d+=(s[e]=='{')-(s[e]=='}');e+=1
 return s[a:e]
f=function(s,'int CHudProgressBar::MsgFunc_BotProgress(')
code=r"""
#include <cassert>
#include <cstring>
#include <algorithm>
#include "nano-bot-loading.h"
using std::max;
enum {UPDATE_BOTPROGRESS=0,CREATE_BOTPROGRESS=1,REMOVE_BOTPROGRESS=2,HUD_DRAW=1};
static float flagValue=0;static bool profile=true;
bool NanoHudActive(){return profile;}
const char *Localize(const char *s){return s;}
struct {void Cvar_SetValue(const char*,float v){flagValue=v;}} gEngfuncs;
struct BufferReader {const unsigned char *p;int size,pos=0;BufferReader(const char*,void *v,int n):p((const unsigned char*)v),size(n){}int ReadByte(){assert(pos<size);return p[pos++];}const char *ReadString(){assert(pos<size);const char *s=(const char*)p+pos;assert(memchr(s,0,size-pos));pos+=strlen(s)+1;return s;}};
struct CHudProgressBar {NanoBotLoading nanoLoading;int m_iDuration=0,m_iFlags=0;float m_fPercent=0;char m_szHeader[256]={0};const char *m_szLocalizedHeader=nullptr;int MsgFunc_BotProgress(const char*,int,void*);};
"""+f+r"""
int main(){
 CHudProgressBar bar;
 unsigned char start[]={1,'#','C','Z','e','r','o','_','L','e','a','r','n','i','n','g','M','a','p',0};
 bar.MsgFunc_BotProgress("BotProgress",sizeof(start),start);
 assert(bar.nanoLoading.active && bar.nanoLoading.stage==1 && flagValue==1 && bar.m_szLocalizedHeader[0]);
 // The state persists across frames with no server progress messages.
 for(int i=0;i<1000;i++)assert(bar.nanoLoading.active);
 unsigned char alpha[]={1,'#','C','Z','e','r','o','_','H','i','d','i','n','g','S','p','o','t','s',0};
 bar.MsgFunc_BotProgress("BotProgress",sizeof(alpha),alpha);assert(bar.nanoLoading.stage==2);
 float prior=bar.nanoLoading.progress;
 for(int p:{0,10,50,30,100}){bar.nanoLoading.Message(0,p,"#CZero_HidingSpots");assert(bar.nanoLoading.progress>=prior);prior=bar.nanoLoading.progress;}
 bar.nanoLoading.Message(1,0,"#CZero_ApproachPoints");assert(bar.nanoLoading.stage==3 && bar.nanoLoading.progress==prior);
 unsigned char hide[]={2};bar.MsgFunc_BotProgress("BotProgress",sizeof(hide),hide);assert(!bar.nanoLoading.active && flagValue==0);
 bar.MsgFunc_BotProgress("BotProgress",sizeof(start),start);assert(bar.nanoLoading.progress==0 && bar.nanoLoading.stage==1);
 profile=false;bar.MsgFunc_BotProgress("BotProgress",sizeof(start),start);assert(flagValue==0);
}
"""
inputs=(r/'upstream/cs16-client/cl_dll/input.cpp').read_text()
a=inputs.index('    if(NanoHudActive() && gHUD.m_ProgressBar.nanoLoading.active)',inputs.index('void DLLEXPORT CL_CreateMove'))
e=inputs.index('\n\tfloat spd;',a)
gate=inputs[a:e]
code=code.replace('struct {void Cvar_SetValue(const char*,float v){flagValue=v;}} gEngfuncs;', 'struct {void Cvar_SetValue(const char*,float v){flagValue=v;}void GetViewAngles(float *v){v[0]=10;v[1]=20;v[2]=0;}} gEngfuncs;')
code=code.replace('int main(){',r"""
struct {CHudProgressBar m_ProgressBar;} gHUD;
struct Cmd {float viewangles[3],forwardmove,sidemove,upmove;int buttons,impulse,weaponselect;};
static int in_impulse=5,g_weaponselect=7,bitsCalls=0;
int CL_ButtonBits(int){++bitsCalls;return 123;}
void MakeMove(Cmd *cmd){
"""+gate+r"""
 cmd->buttons=123;
}
int main(){
 gHUD.m_ProgressBar.nanoLoading.active=true;Cmd cmd;memset(&cmd,0xff,sizeof(cmd));MakeMove(&cmd);
 assert(cmd.forwardmove==0 && cmd.sidemove==0 && cmd.upmove==0 && cmd.buttons==0 && cmd.impulse==0 && cmd.weaponselect==0);
 assert(cmd.viewangles[0]==10 && cmd.viewangles[1]==20 && bitsCalls==1 && in_impulse==0 && g_weaponselect==0);
 gHUD.m_ProgressBar.nanoLoading.active=false;MakeMove(&cmd);assert(cmd.buttons==123);
""")
with tempfile.TemporaryDirectory() as d:
 p=Path(d)/'test.cpp';p.write_text(code);exe=p.with_suffix('')
 subprocess.run(['g++','-std=c++11','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-I'+str(r/'src'),str(p),'-o',str(exe)],check=True)
 subprocess.run([str(exe)],check=True)
print('BotProgress: title parsing, idle-frame persistence, combined monotonic stages, finish, restart and non-Nano flag passed.')
