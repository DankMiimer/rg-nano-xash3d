# SPDX-License-Identifier: GPL-3.0-or-later
"""Verify actual CS input dispatch when visible HUD interfaces overlap."""
from pathlib import Path
import subprocess,tempfile
root=Path(__file__).resolve().parents[1]
s=(root/'upstream/cs16-client/cl_dll/input.cpp').read_text()
a=s.index('int DLLEXPORT HUD_Key_Event(');b=s.index('{',a);i=b+1;depth=1
while depth:depth+=(s[i]=='{')-(s[i]=='}');i+=1
function=s[a:i]
code=r'''
#include <cassert>
#include <vector>
#include <cstring>
enum {K_ESCAPE=27,K_AUX1=200,OBS_IN_EYE=4,OBS_CHASE_LOCKED=1,OBS_CHASE_FREE=2,OBS_MAP_CHASE=6,INSET_OFF=0};
static int g_iUser1=0;static bool profile=true;static int lastMode=0;
static bool NanoHudActive(){return profile;}
#define DLLEXPORT
static std::vector<int> calls;
struct Layer { Layer(int n):id(n){} int id;bool claim=false;bool m_fMenuDisplayed=true;int NanoKey(int,int){calls.push_back(id);return claim;} };
static struct {struct {struct {bool active=false;} nanoLoading;} m_ProgressBar;struct {void SetModes(int mode,int){lastMode=mode;}} m_Spectator;Layer m_Menu={3},m_Scoreboard={1},m_SpectatorGui={2};} gHUD;
static struct {float pfnGetCvarFloat(const char*){return 1;}} gEngfuncs;
struct Menu {void Key(int,int){calls.push_back(4);}};static Menu legacy;static Menu *g_pMenu=&legacy;
'''+function+r'''
int main(){
 for(int mask=0;mask<8;++mask){
  gHUD.m_Scoreboard.claim=mask&1;gHUD.m_SpectatorGui.claim=mask&2;gHUD.m_Menu.claim=mask&4;
  calls.clear();int result=HUD_Key_Event(1,133,"");
  assert(calls[0]==1);
  if(mask&1){assert(calls.size()==1&&result==0);continue;}
  assert(calls[1]==2);
  if(mask&2){assert(calls.size()==2&&result==0);continue;}
  assert(calls[2]==3);
  if(mask&4){assert(calls.size()==3&&result==0);continue;}
  assert(calls[3]==4&&result==1);
 }
 gHUD.m_Scoreboard.claim=gHUD.m_SpectatorGui.claim=gHUD.m_Menu.claim=false;
 gHUD.m_ProgressBar.nanoLoading.active=true;
 assert(HUD_Key_Event(1,211,"")==0);assert(HUD_Key_Event(0,211,"")==1);
 assert(HUD_Key_Event(1,K_ESCAPE,"")==1);
 gHUD.m_ProgressBar.nanoLoading.active=false;gHUD.m_Menu.m_fMenuDisplayed=false;
 for(int current:{1,2,3,4,5,6}) {
  g_iUser1=current;lastMode=0;assert(HUD_Key_Event(1,K_AUX1+10,"")==0);
  assert(lastMode==(current==4?1:(current==1||current==2)?6:4));
  lastMode=0;assert(HUD_Key_Event(0,K_AUX1+10,"")==0);assert(lastMode==0);
 }
 g_iUser1=0;assert(HUD_Key_Event(1,K_AUX1+10,"")==1);
}
''' 
with tempfile.TemporaryDirectory(prefix='nano-hud-input-') as folder:
 p=Path(folder)/'test.cpp';p.write_text(code);exe=Path(folder)/'test'
 subprocess.run(['g++','-std=c++11','-Wall','-Wextra','-fsanitize=address,undefined',str(p),'-o',str(exe)],check=True)
 subprocess.run([str(exe)],check=True)
print('HUD input: visible scoreboard and spectator controls take priority over underlying buy/team menus.')
