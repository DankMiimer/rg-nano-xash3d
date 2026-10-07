# SPDX-License-Identifier: GPL-3.0-or-later
"""Exercise the actual match callbacks, bounded persistence, and bot aim function."""
from pathlib import Path
import subprocess
root=Path(__file__).resolve().parents[1]
def function(source,signature):
    start=source.index(signature);brace=source.index('{',start);depth=1;end=brace+1
    while depth:
        depth+=(source[end]=='{')-(source[end]=='}');end+=1
    return source[start:end]
code=r'''
#include <cassert>
#include <cmath>
#include <cstring>
#include <cstdlib>
#include <string>
#include <map>
#include <vector>
#include <algorithm>
#include <strings.h>
#define stricmp strcasecmp
#include "nano-match.h"
#define private public
struct CEventCallback {};
template<class T> CEventCallback VoidCb(T) {return {};}
#define PC_DONE 0
#define PC_CONFIG 1
#define PC_MULTIPLAYER 2
#define QMF_INACTIVE 1
void UI_MultiPlayer_Menu(){}
struct CMenuBaseItem {int x=0,y=0,w=0,h=0;bool nanoFont=false;void SetNanoFont(){nanoFont=true;}void SetNanoScale(float){}void SetRect(int a,int b,int c,int d){x=a;y=b;w=c;h=d;}const char *szName="";unsigned iFlags=0;CEventCallback onChanged;bool grayed=false;void SetGrayed(bool b){grayed=b;}};
struct CMenuFramework : CMenuBaseItem {
    CMenuFramework(const char*){} virtual void _Init(){} virtual void _VidInit(){} virtual void Think(){} void Hide(){}
    template<class T>void AddButton(const char*,const char*,int,T){}void AddItem(CMenuBaseItem&){}
};
struct CMenuBaseArrayModel {virtual void Update()=0;virtual int GetRows()const=0;virtual const char *GetText(int)=0;};
struct CMenuSpinControl : CMenuBaseItem {
    float value=0;CMenuBaseArrayModel *model=nullptr;
    void Setup(float,float,float){}void Setup(CMenuBaseArrayModel *m){model=m;}
    void SetCurrentValue(float n){value=n;}float GetCurrentValue(){return value;}
    const char *GetCurrentString(){return model?model->GetText((int)value):nullptr;}
};
struct CMenuCheckBox : CMenuBaseItem {bool bChecked=false;};
struct CMenuAction : CMenuBaseItem {};
struct CMenuYesNoMessageBox : CMenuBaseItem {CMenuBaseItem dlgMessage1,yes,no;enum{HIGHLIGHT_NO};void HighlightChoice(int){}CMenuBaseItem *selected=nullptr;void SetCursorToItem(CMenuBaseItem &item){selected=&item;}virtual void _VidInit(){}CEventCallback onPositive;bool shown=false;void Link(CMenuFramework*){}void SetMessage(const char*){}void Show(){shown=true;}};
static std::map<std::string,std::string> files;
static std::map<std::string,float> cvars;
static std::vector<char*> mapFiles;
static std::string commands,failFile;
struct EngFuncs {
    static char **GetFilesList(const char *pattern,int *count,bool game){assert(!strcmp(pattern,"maps/*.bsp") && game);*count=(int)mapFiles.size();return mapFiles.data();}
    static bool FileExists(const char *name,bool){return files.count(name)!=0;}
    static char *COM_LoadFile(const char *name,int *len){
        if(!files.count(name))return nullptr;
        *len=(int)files[name].size();char *p=(char*)malloc(*len);memcpy(p,files[name].data(),*len);return p;
    }
    static void COM_FreeFile(void *p){free(p);}
    static bool COM_SaveFile(const char *name,const void *text,int len){if(failFile==name)return false;files[name]=std::string((const char*)text,len);return true;}
    static bool IsMapValid(const char *name){return FileExists((std::string("maps/")+name+".bsp").c_str(),true);}
    static void ClientCmd(bool,const char *text){commands=text;}
    static float GetCvarFloat(const char *name){return cvars[name];}
    static void CvarSetValue(const char *name,float v){cvars[name]=v;}
    static void PlayBackgroundTrack(const char*,const char*){}
};
#define ADD_MENU(cmd,type,fn) void fn(){}
#include "nano-menu-match.h"
struct CV {float value;};static float lan=1;
#define CVAR_GET_FLOAT(x) (!strcmp(x,"sv_lan")?lan:cvars[x])
#define CVAR_SET_FLOAT(x,y) (cvars[x]=y)
#define Q_strlcpy(a,b) snprintf(a,sizeof(a),"%s",b)
#define STRING(x) (x)
#define CONSOLE_ECHO(...) ((void)0)
static CV cv_nano_nav_analyze={0};
static std::vector<int> TheNavAreaList;
struct Manager {bool learning=false;void LoadNavigationMap(){}bool IsLearningMap(){return learning;}void SetLearningMapFlag(){learning=true;}} manager;
Manager *TheCSBots(){return &manager;}
'''
base=root/'upstream/cs16-client/3rdparty/ReGameDLL_CS/regamedll'
init=(base/'dlls/bot/cs_bot_init.cpp').read_text()
code+=r'''
struct Vector {float x=0,y=0,z=0;float Length()const{return sqrtf(x*x+y*y+z*z);}Vector operator-(Vector b)const{Vector v;v.x=x-b.x;v.y=y-b.y;v.z=z-b.z;return v;}float&operator[](int i){return i==0?x:i==1?y:z;}};
struct Global {float time;} global={10},*gpGlobals=&global;
struct Entity {Vector origin;const char *netname="test bot";};
#define Q_max std::max
#define RANDOM_FLOAT(a,b) (b)
#define DEFAULT_FOV 90
using real_t=float;
struct CCSBot {
    float m_aimSpreadTimestamp=0,m_aimOffsetTimestamp=0;int m_iFOV=90;
    Entity entity,*pev=&entity;Vector m_lastEnemyPosition,m_aimOffsetGoal;
    bool IsViewMoving(float){return false;}void PrintIfWatched(const char*,float){}
    int learned=0,m_buyState=0;char m_name[64];
    void ResetValues(){}void SetState(int*){}void BotTouch(){}
    template<class T>void SetTouch(T){}void StartLearnProcess(){++learned;}
    void SpawnBot();void SetAimOffset(float accuracy);
};
'''
code+=function(init,'void CCSBot::SpawnBot(')
code+=r'''
#include "nano-look.h"
static NanoLookState nanoYaw={1,0.7f};
static float viewAngles[3]={-45,123,7};static bool dead=false;
static struct {int m_iIntermission;} gHUD={0};
bool CL_IsDead(){return dead;}
#define PITCH 0
struct ViewEngine {void GetViewAngles(float *out){memcpy(out,viewAngles,sizeof(viewAngles));}void SetViewAngles(float *angles){memcpy(viewAngles,angles,sizeof(viewAngles));}} gEngfuncs;
'''
code+=function((root/'upstream/cs16-client/cl_dll/input.cpp').read_text(),'static void NanoCenterView(')
code+=r'''
int main(){
    (void)&NanoLookRate;NanoCenterView();assert(viewAngles[0]==0 && viewAngles[1]==123 && viewAngles[2]==7 && nanoYaw.direction==0 && nanoYaw.held==0);
    dead=true;viewAngles[0]=25;NanoCenterView();assert(viewAngles[0]==25);dead=false;
    gHUD.m_iIntermission=1;NanoCenterView();assert(viewAngles[0]==25);gHUD.m_iIntermission=0;
    char tiny[4],out[2048];NanoMatchSettings s=NanoMatchDefaults();
    assert(s.bots==2 && s.difficulty==0 && s.analyze==0);
    assert(NanoMatchSerialize(tiny,sizeof(tiny),s)==-1);
    assert(NanoMatchStartCommand(out,sizeof(out),"de_dust;quit")==-1);
    assert(!NanoMatchMapName("../de_dust") && !NanoMatchMapName("de dust"));
    for(int diff=0;diff<4;++diff)for(int bots=0;bots<8;++bots){
        s=NanoMatchDefaults();s.difficulty=diff;s.bots=bots;
        int n=NanoMatchSerialize(out,sizeof(out),s);assert(n>0);
        NanoMatchSettings copy=NanoMatchParse(out,n);assert(copy.difficulty==diff && copy.bots==bots && !strcmp(copy.map,s.map));
        assert(NanoMatchServerConfig(out,sizeof(out),copy)>0);
        std::string cfg=out;
        assert(cfg.find("bot_quota "+std::to_string(bots)+"\n")!=std::string::npos);
        assert(cfg.find("nano_nav_analyze 0\n")!=std::string::npos);
        assert(cfg.find("bot_zombie "+std::to_string(0)+"\n")!=std::string::npos);
        assert(cfg.find("nano_bot_assist")==std::string::npos);
        assert(cfg.find("bot_difficulty "+std::to_string(diff)+"\n")!=std::string::npos);
    }
    for(int old=0;old<8;++old){std::string legacy="map de_dust\ndifficulty "+std::to_string(old)+"\n";auto migrated=NanoMatchParse(legacy.data(),legacy.size());assert(migrated.difficulty==(old>=4?old-4:0));}
    std::string bad="map de_dust;quit\nbots 999999999999999999999\ndifficulty -7\nteam 5\nwalk nan\nquit now\n";
    s=NanoMatchParse(bad.data(),bad.size());assert(!strcmp(s.map,"de_dust") && s.bots==2 && s.difficulty==0 && s.team==2 && s.walk==0);
    s=NanoMatchDefaults();s.weapons=3;s.team=2;s.friendlyFire=1;
    NanoMatchServerConfig(out,sizeof(out),s);std::string cfg=out;
    assert(cfg.find("bot_allow_pistols 0\n")!=std::string::npos && cfg.find("bot_allow_rifles 0\n")!=std::string::npos);
    assert(cfg.find("bot_join_team CT\n")!=std::string::npos && cfg.find("mp_autoteambalance 0\n")!=std::string::npos);
    assert(cfg.find("mp_friendlyfire 1\n")!=std::string::npos);
    assert(NanoMatchStartCommand(out,sizeof(out),"de_dust2")>0);
    assert(std::string(out).find("wait;wait;wait;exec listenserver.cfg;maxplayers 8;map de_dust2")!=std::string::npos);
    const char *installed[]={"maps/de_dust2.bsp","maps/cs_office.bsp","maps/de_dust.bsp","maps/de_dust.bsp","maps/bad;quit.bsp","maps/readme.txt"};
    for(auto name:installed)mapFiles.push_back(const_cast<char*>(name));
    for(auto name:installed)files[name]="map";
    files["maps/de_dust.nav"]="nav";
    CMenuNanoMatch menu;menu._Init();menu._VidInit();
    assert(menu.maps.GetRows()==3 && !strcmp(menu.maps.GetText(0),"cs_office"));
    assert(!strcmp(menu.map.GetCurrentString(),"de_dust") && files.count("nano-match.cfg")==0);
    menu.Start();assert(commands.find("map de_dust\n")!=std::string::npos);
    assert(files["nano-offline.cfg"].find("bot_difficulty 0\n")!=std::string::npos);
    menu.map.SetCurrentValue(2);menu.bots.SetCurrentValue(7);menu.difficulty.SetCurrentValue(2);menu.Changed();
    commands.clear();menu.Start();assert(commands.empty() && strstr(menu.status.szName,"No NAV"));
    CMenuNanoMatch extra(true);extra._Init();extra._VidInit();
    assert(extra.settings.bots==7 && extra.settings.difficulty==2);
    extra.analyze.bChecked=true;extra.weapons.SetCurrentValue(1);extra.round.SetCurrentValue(9);extra.Changed();
    menu.Think();assert(menu.settings.analyze==1 && !strstr(menu.status.szName,"No NAV"));
    menu.Start();assert(commands.find("map de_dust2\n")!=std::string::npos);
    assert(files["nano-offline.cfg"].find("bot_allow_rifles 0\n")!=std::string::npos);
    assert(files["nano-offline.cfg"].find("mp_roundtime 9\n")!=std::string::npos);
    nanoMatchLoaded=false;CMenuNanoMatch reopened;reopened._Init();reopened._VidInit();assert(reopened.settings.analyze==1 && reopened.settings.weapons==1 && reopened.settings.bots==7);
    cvars["host_serverstate"]=1;commands.clear();reopened.Start();assert(commands.empty() && reopened.confirm.shown && reopened.confirm.selected==&reopened.confirm.no);reopened.StartNow();assert(!commands.empty());
    failFile="nano-match.cfg";commands.clear();menu.StartNow();assert(commands.empty() && strstr(menu.status.szName,"Save failed"));
    CMenuNanoMatch unsaved(true);unsaved._Init();unsaved._VidInit();assert(unsaved.settings.bots==7 && !strcmp(unsaved.status.szName,"Save failed; try again"));
    failFile="nano-offline.cfg";commands.clear();menu.StartNow();assert(commands.empty() && strstr(menu.status.szName,"could not save"));failFile.clear();
    mapFiles.clear();CMenuNanoMatch empty;empty._Init();empty._VidInit();commands.clear();empty.Start();assert(commands.empty() && empty.map.grayed);
    CCSBot bot;
    cv_nano_nav_analyze.value=0;lan=1;bot.SpawnBot();assert(bot.learned==0 && !manager.learning && cvars["bot_quota"]==0);
    cv_nano_nav_analyze.value=1;bot.SpawnBot();assert(bot.learned==1 && manager.learning);
    manager.learning=false;cv_nano_nav_analyze.value=0;lan=0;bot.SpawnBot();assert(bot.learned==2 && manager.learning);
    manager.learning=false;lan=1;TheNavAreaList.push_back(1);bot.SpawnBot();assert(bot.learned==2 && !manager.learning);

}
'''
path=root/'build/test-nano-match.cpp';path.write_text(code)
shim=root/'build/nano-match-shim';shim.mkdir(exist_ok=True)
for name in ('SpinControl.h','CheckBox.h','Action.h','YesNoMessageBox.h'):(shim/name).write_text('// Declarations supplied by harness.\n')
exe=path.with_suffix('')
subprocess.run(['g++','-std=c++11','-fno-rtti','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-I',str(root/'src'),'-I',str(shim),str(path),'-o',str(exe)],check=True)
subprocess.run([str(exe)],check=True)
print('Actual match callbacks: choices, restart order, persistence, NAV gating, errors, four stock difficulties, legacy-choice migration and navigation behavior passed.')
