# SPDX-License-Identifier: GPL-3.0-or-later
from pathlib import Path
import subprocess,tempfile,os
r=Path(__file__).resolve().parents[1];native=Path(os.environ.get('NANO_NATIVE_DIR',str(r/'build/native')))
s=(native/'xash3d/engine/platform/linux/in_evdev.c').read_text()
def function(text,name):
 a=text.index(name);b=text.index('{',a);depth=1;i=b+1
 while depth:depth+=(text[i]=='{')-(text[i]=='}');i+=1
 return text[a:i]
code=r'''
#include <cassert>
#include <vector>
#include <utility>
#include <string>
#include <unistd.h>
#include <fcntl.h>
#include <sys/ioctl.h>
#include <linux/input.h>
#include "nano-controls.h"
#include "nano-control-preference.h"
#include "nano-text-menu.h"
#include "keydefs.h"
struct CV{float value;};static CV nano_control_scheme={1},nano_text_menu={0},nano_scoreboard={0},evdev_keydebug={0},m_ignore={1},m_yaw={1},m_pitch={1};
static NanoControlState nanoControls={0,0,0,-1,0};
static struct {int key_dest,state;} cls={1,5};const int key_game=1,key_menu=2,ca_active=5;
static struct {double realtime;} host={0};
static struct {int devices,fds[5];bool grab=false,chars=false,shift=false;double grabtime=0;float x=0,y=0;} evdev={};
typedef unsigned char byte;
static byte nanoIntroHeld[KEY_MAX+1]={0};
static bool introActive=false;static int introSkips=0;
bool SCR_NanoIntroActive(){return introActive;}
void SCR_NanoIntroSkip(){introActive=false;++introSkips;cls.key_dest=2;}
static std::vector<std::pair<int,int>> events;
static float precision=0;
void Cvar_SetValue(const char *name,float value){assert(!strcmp(name,"nano_look_slow"));precision=value;}
void Key_Event(int key,int down){events.emplace_back(key,down);}
void Key_ClearStates(){}void IN_MWheelEvent(int){}void CL_CharEvent(int){}int Key_ToUpper(int x){return x;}
int KeycodeFromEvdev(int key,int){return key==KEY_V?'v':0;}
#define Con_Printf(...) ((void)0)
#define XASH_INPUT 2
#define INPUT_EVDEV 2
'''
for name in ('static int NanoControlContext(', 'static void NanoControlKey(', 'void IN_EvdevFrame ('):
 code+=function(s,name)+'\n'
keys=(native/'xash3d/engine/client/input/in_keys.c').read_text()
a=keys.index('static const keyname_t keynames[]');b=keys.index('};',a)+2
code+='#include <cstdlib>\n#include <strings.h>\ntypedef struct {const char *name;int keynum;const char *binding;} keyname_t;\nstatic int keys[265];\n#define ARRAYSIZE(x) (int)(sizeof(x)/sizeof((x)[0]))\n#define Q_atoi(x) ((int)strtol(x,nullptr,0))\n#define Q_stricmp strcasecmp\n'
code+=keys[a:b]+'\n'+function(keys,'static int Key_StringToKeynum(')+'\n'
menu=(r/'upstream/cs16-client/cl_dll/menu.cpp').read_text()
code+=r'''
static std::string selectedCommand;
void ClientCmd(const char *text){selectedCommand=text;}
struct CHudMenu {int m_bitsValidSlots=0,m_nanoSelection=0;bool closed=false;int NanoKey(int down,int key);void SelectMenuItem(int);void UserCmd_OldStyleMenuClose(){closed=true;}};
'''
code+=function(menu,'int CHudMenu::NanoKey(')+'\n'+function(menu,'void CHudMenu :: SelectMenuItem(')+'\n'
code+=r'''
struct Record{unsigned long sec=0,usec=0;unsigned short type=EV_KEY,code;int value;};
static int writer;
void physical(int button,int value){Record e;e.code=59+button;e.value=value;assert(write(writer,&e,sizeof(e))==sizeof(e));IN_EvdevFrame();}
void collect(int action,int down,void* p){((std::vector<std::pair<int,int>>*)p)->emplace_back(action,down);}
int main(){
 CHudMenu menu;menu.m_bitsValidSlots=(1<<0)|(1<<2)|(1<<9);
 assert(menu.NanoKey(1,K_DOWNARROW) && menu.m_nanoSelection==1);
 menu.NanoKey(1,K_DOWNARROW);assert(menu.m_nanoSelection==3);
 menu.NanoKey(1,K_ENTER);assert(selectedCommand=="menuselect 3\n" && menu.closed);
 menu.closed=false;menu.NanoKey(1,K_BACKSPACE);assert(selectedCommand=="menuselect 10\n" && menu.closed);
 menu.closed=false;menu.m_bitsValidSlots=1;menu.NanoKey(1,K_BACKSPACE);assert(!menu.closed);
 assert(!menu.NanoKey(1,'a'));
 for(unsigned bits=0;bits<(1u<<NC_BUTTONS);++bits){
   unsigned a=NanoControlActions(bits,1),b=NanoControlActions(bits^(1u<<NC_R),1);
   unsigned movement=(1u<<NC_FORWARD)|(1u<<NC_BACK)|(1u<<NC_MOVELEFT)|(1u<<NC_MOVERIGHT);
   assert((a&movement)==(b&movement));
   bool precision=(bits&(1u<<NC_SELECT)) && !(bits&(1u<<NC_R)) && (bits&((1u<<NC_A)|(1u<<NC_B)|(1u<<NC_X)|(1u<<NC_Y)));
   assert(!!(a&(1u<<NC_SLOW))==precision);
 }
 for(int mask=1;mask<1024;++mask){
   int selected=NanoMenuSelection(mask,0,0);assert(selected>=1 && selected<=10 && (mask&(1<<(selected-1))));
   for(int i=0;i<20;++i){selected=NanoMenuSelection(mask,selected,1);assert(mask&(1<<(selected-1)));}
   for(int i=0;i<20;++i){selected=NanoMenuSelection(mask,selected,-1);assert(mask&(1<<(selected-1)));}
 }
 assert(!NanoMenuSelection(0,3,1));
 assert(NanoControlPreference("scheme 1\n",9));assert(!NanoControlPreference("scheme 1;quit\n",14));assert(!NanoControlPreference("scheme 99\n",10));
 char pref[16];assert(NanoControlPreferenceSave(pref,sizeof(pref),1)==9);assert(!strcmp(pref,"scheme 1\n"));
 // Actual evdev frame: hold movement and look, switch modifier in both orders.
 int pipefd[2];assert(pipe(pipefd)==0);fcntl(pipefd[0],F_SETFL,O_NONBLOCK);writer=pipefd[1];evdev.devices=1;evdev.fds[0]=pipefd[0];
 physical(NC_LEFT,1);physical(NC_A,1);assert(events.back()==std::make_pair(K_AUX1+NC_LOOKRIGHT-1,1));
 events.clear();physical(NC_R,1);
 assert(events.size()==2 && events[0]==std::make_pair(K_AUX1+NC_LOOKRIGHT-1,0) && events[1]==std::make_pair(K_AUX1+NC_DUCK-1,1));
 physical(NC_B,1);assert(events.back()==std::make_pair(K_AUX1+NC_JUMP-1,1));
 events.clear();physical(NC_R,0);assert(events[0].second==0 && events[1].second==0);assert(events.size()==4);
 physical(NC_A,0);physical(NC_B,0);physical(NC_LEFT,0);
 events.clear();physical(NC_L,1);assert(events.back()==std::make_pair(K_AUX1+NC_ATTACK-1,1));
 physical(NC_R,1);assert(events.back()==std::make_pair(K_AUX1+NC_ATTACK2-1,1));physical(NC_L,0);physical(NC_R,0);
 physical(NC_SELECT,1);physical(NC_R,1);assert(events.back()==std::make_pair(K_AUX1+NC_CENTER-1,1));physical(NC_R,0);physical(NC_SELECT,0);
 // A Select tap reloads only on release; either chord order never reloads.
 events.clear();physical(NC_SELECT,1);assert(events.empty());physical(NC_SELECT,0);
 assert(events.size()==2 && events[0]==std::make_pair(K_AUX1+NC_RELOAD-1,1) && events[1]==std::make_pair(K_AUX1+NC_RELOAD-1,0));
 for(int face=NC_A;face<=NC_Y;++face)for(int order=0;order<2;++order){
  events.clear();physical(order?face:NC_SELECT,1);physical(order?NC_SELECT:face,1);
  assert((nanoControls.output&(1u<<NC_SLOW)) && precision==1);physical(NC_L,1);assert(nanoControls.output&(1u<<NC_ATTACK));physical(NC_L,0);
  physical(NC_LEFT,1);assert(nanoControls.output&(1u<<NC_MOVELEFT));physical(NC_LEFT,0);
  physical(NC_SELECT,0);assert(!(nanoControls.output&(1u<<NC_SLOW)) && precision==0);physical(face,0);
  for(auto e:events)assert(e.first!=K_AUX1+NC_RELOAD-1);
 }
 physical(NC_SELECT,1);physical(NC_X,1);physical(NC_R,1);assert(!(nanoControls.output&(1u<<NC_SLOW)) && (nanoControls.output&(1u<<NC_NEXT)));
 physical(NC_R,0);assert(nanoControls.output&(1u<<NC_SLOW));physical(NC_X,0);physical(NC_SELECT,0);
 // Menu entry releases precision and never turns the held Select into reload.
 physical(NC_SELECT,1);physical(NC_Y,1);events.clear();cls.key_dest=2;IN_EvdevFrame();assert(!(nanoControls.output&(1u<<NC_SLOW)) && precision==0);
 physical(NC_SELECT,0);physical(NC_Y,0);for(auto e:events)assert(e.first!=K_AUX1+NC_RELOAD-1);cls.key_dest=1;IN_EvdevFrame();
 // Opening menus releases held game actions; returning cannot fire/look from stale holds.
 physical(NC_L,1);events.clear();cls.key_dest=2;IN_EvdevFrame();assert(events.back()==std::make_pair(K_AUX1+NC_ATTACK-1,0));
 physical(NC_A,1);assert(events.back()==std::make_pair(K_ENTER,1));events.clear();cls.key_dest=1;IN_EvdevFrame();
 assert(events.size()==1 && events[0]==std::make_pair(K_ENTER,0));events.clear();IN_EvdevFrame();assert(events.empty());
 physical(NC_A,0);physical(NC_L,0);physical(NC_L,1);assert(events.back()==std::make_pair(K_AUX1+NC_ATTACK-1,1));physical(NC_L,0);
 nano_text_menu.value=1;IN_EvdevFrame();physical(NC_UP,1);assert(events.back()==std::make_pair(K_UPARROW,1));physical(NC_UP,0);
 physical(NC_A,1);assert(events.back()==std::make_pair(K_ENTER,1));physical(NC_A,0);physical(NC_B,1);assert(events.back()==std::make_pair(K_BACKSPACE,1));physical(NC_B,0);
 // Repeated physical records don't replay single-shot weapon changes.
 nano_text_menu.value=0;nano_scoreboard.value=1;IN_EvdevFrame();physical(NC_DOWN,1);assert(events.back()==std::make_pair(K_DOWNARROW,1));physical(NC_DOWN,0);nano_scoreboard.value=0;IN_EvdevFrame();physical(NC_R,1);physical(NC_X,1);events.clear();physical(NC_X,2);assert(events.empty());physical(NC_X,0);physical(NC_R,0);
 // Save/delete are menu-only, fire once, and release before returning to play.
 cls.key_dest=key_menu;IN_EvdevFrame();events.clear();
 physical(NC_X,1);assert(events.back()==std::make_pair(K_F8,1));
 events.clear();physical(NC_X,2);assert(events.empty());
 physical(NC_Y,1);assert(events.back()==std::make_pair(K_F9,1));
 events.clear();cls.key_dest=key_game;IN_EvdevFrame();
 assert(events.size()==2 && events[0]==std::make_pair(K_F8,0) && events[1]==std::make_pair(K_F9,0));
 events.clear();IN_EvdevFrame();assert(events.empty());physical(NC_X,0);physical(NC_Y,0);
 cls.key_dest=3;IN_EvdevFrame();events.clear();physical(NC_X,1);physical(NC_Y,1);assert(events.empty());
 physical(NC_X,0);physical(NC_Y,0);cls.key_dest=key_game;IN_EvdevFrame();
 // Every physical button skips the intro, with repeats/releases consumed before menus.
 cls.key_dest=key_menu;IN_EvdevFrame();
 for(int button=0;button<NC_BUTTONS;++button){
  introActive=true;events.clear();int skips=introSkips;
  physical(button,1);assert(introSkips==skips+1 && events.empty());
  physical(button,2);physical(button,0);assert(events.empty());
 }
 // Classic-preset key records are also consumed until released.
 nano_control_scheme.value=0;introActive=true;events.clear();
 Record classic;classic.type=EV_KEY;classic.code=KEY_V;classic.value=1;
 write(writer,&classic,sizeof(classic));IN_EvdevFrame();assert(events.empty() && !introActive);
 classic.value=2;write(writer,&classic,sizeof(classic));IN_EvdevFrame();
 classic.value=0;write(writer,&classic,sizeof(classic));IN_EvdevFrame();assert(events.empty());
 nano_control_scheme.value=1;cls.key_dest=key_menu;IN_EvdevFrame();
 introActive=true;physical(NC_A,1);assert(nanoIntroHeld[59+NC_A]);
 Record introDropped;introDropped.type=EV_SYN;introDropped.code=SYN_DROPPED;introDropped.value=0;
 write(writer,&introDropped,sizeof(introDropped));IN_EvdevFrame();assert(!nanoIntroHeld[59+NC_A]);
 events.clear();physical(NC_A,2);assert(events.empty());physical(NC_A,0);
 physical(NC_A,1);assert(events.back()==std::make_pair(K_ENTER,1));physical(NC_A,0);
 cls.key_dest=key_game;IN_EvdevFrame();
 // Disabling the preset and lost-event recovery release actions.
 physical(NC_L,1);events.clear();nano_control_scheme.value=0;IN_EvdevFrame();assert(events.back()==std::make_pair(K_AUX1+NC_ATTACK-1,0));
 nano_control_scheme.value=1;physical(NC_L,0);physical(NC_L,1);events.clear();Record dropped;dropped.type=EV_SYN;dropped.code=SYN_DROPPED;dropped.value=0;write(writer,&dropped,sizeof(dropped));IN_EvdevFrame();assert(events.back()==std::make_pair(K_AUX1+NC_ATTACK-1,0));
 physical(NC_SELECT,1);physical(NC_A,1);assert(precision==1);write(writer,&dropped,sizeof(dropped));IN_EvdevFrame();assert(precision==0);physical(NC_SELECT,0);physical(NC_A,0);
 close(writer);close(pipefd[0]);
}
'''
# Resolve every generated bind through the engine's actual key-name parser.
subprocess.run(['python3',str(r/'tools/package_launchers.py'),'--native'],check=True,stdout=subprocess.DEVNULL)
import re
checks=[]
for game in ('valve','cstrike'):
 text=(r/'build/config-stage'/game/'nano-face-controls.cfg').read_text()
 binds=re.findall(r'^bind "([^"]+)" "([^"]+)"$',text,re.M)
 assert len(binds)==18
 for i,(name,action) in enumerate(binds):checks.append('assert(Key_StringToKeynum("'+name+'") == K_AUX1+'+str(i)+');')
code=code.replace('int main(){','int main(){\n'+'\n'.join(checks)+'\n')
p=r/'build/test-face-controls.cpp';p.write_text(code);exe=p.with_suffix('')
subprocess.run(['g++','-std=c++11','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-I',str(r/'src'),'-I',str(r/'upstream/xash3d/engine'),str(p),'-o',str(exe)],check=True)
subprocess.run([str(exe)],check=True)
print('Actual evdev routing: all physical combinations, modifier transitions, simultaneous actions, menu release/gating, repeat and dropped-event recovery passed.')
