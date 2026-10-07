# SPDX-License-Identifier: GPL-3.0-or-later
"""Exercise the real menu callbacks and saved preference model without the engine."""
from pathlib import Path
import subprocess

root=Path(__file__).resolve().parents[1]
code=r'''
#include <cassert>
#include <cmath>
#include <cstring>
#include <string>
#include <map>
#include <sstream>
#include <strings.h>
#define stricmp strcasecmp
#include "nano-settings.h"
#define private public
struct CEventCallback {};
template<class T> CEventCallback VoidCb(T) { return {}; }
#define PC_DONE 0
#define PC_CONFIG 1
#define PC_CONTROLS 2
#define QMF_INACTIVE 1
struct CMenuBaseItem { CEventCallback onChanged; const char *szName=nullptr; unsigned iFlags=0; bool grayed=false,visible=true; void SetGrayed(bool b){grayed=b;} void SetVisibility(bool b){visible=b;} };
struct CMenuFramework : CMenuBaseItem {
    CMenuFramework(const char *){}
    virtual void _Init(){} virtual void _VidInit(){} void Hide(){}
    template<class T> void AddButton(const char *,const char *,int,T){}
    void AddItem(CMenuBaseItem&){}
};
static std::map<std::string,float> cvars;
static std::string saved;
static unsigned writes;
static bool writeOK=true,native=true;
static std::string commands;static std::string controlPreference;
static struct { struct { const char *gamefolder; } m_gameinfo; } gMenu={{"cstrike"}};
struct EngFuncs {
    static char *COM_LoadFile(const char *name,int *size){const std::string &text=!strcmp(name,"nano-settings.cfg")?saved:controlPreference;*size=(int)text.size();if(!*size)return nullptr;char *out=(char*)malloc(*size);memcpy(out,text.data(),*size);return out;}
    static void COM_FreeFile(void *p){free(p);}
    static void CvarSetValue(const char *name,float value){ cvars[name]=value; }
    static const char *GetCvarString(const char *){return native?"0":"";}
    static void ClientCmd(bool,const char *text){commands=text;}
    static int COM_SaveFile(const char *name,const void *data,int len){
        if(!strcmp(name,"nano-control.cfg")){if(writeOK)controlPreference.assign((const char*)data,len);return writeOK;}
        assert(!strcmp(name,"nano-settings.cfg"));++writes;
        if(writeOK)saved.assign((const char *)data,len);
        return writeOK;
    }
};
struct CMenuSlider : CMenuBaseItem {
    float value=0;
    void Setup(float,float,float){}
    void SetCurrentValue(float x){value=x;}
    float GetCurrentValue(){return value;}
    void LinkCvar(const char *name){value=cvars[name];}
};
struct CMenuCheckBox : CMenuBaseItem { bool bChecked=false; void LinkCvar(const char *name){bChecked=cvars[name]!=0;} };
struct CMenuAction : CMenuBaseItem {};
#define ADD_MENU(cmd,type,fn) void fn(){}
#include "nano-menu-options.h"
static void LoadSaved(const std::string& text) {
    std::istringstream lines(text);std::string line;
    while(std::getline(lines,line)){
        std::istringstream tokens(line);std::string name,value;
        tokens>>name;if(name=="//" || name=="alias" || name.empty())continue;
        if(name=="set")tokens>>name;
        tokens>>value;
        if(!value.empty() && value.front()=='"')value=value.substr(1,value.size()-2);
        cvars[name]=strtof(value.c_str(),nullptr);
    }
}
int main(){
    CMenuNanoControls control;control._Init();control._VidInit();assert(!control.face.bChecked);
    control.face.bChecked=true;control.Changed();assert(controlPreference=="scheme 1\n");
    CMenuNanoControls controlsReopened;controlsReopened._Init();controlsReopened._VidInit();assert(controlsReopened.face.bChecked);
    writeOK=false;control.face.bChecked=false;control.Changed();assert(controlPreference=="scheme 1\n" && strstr(control.status.szName,"Save failed"));writeOK=true;
    controlPreference="scheme 1;quit\n";controlsReopened._VidInit();assert(!controlsReopened.face.bChecked);controlPreference.clear();
    NanoSettings s=NanoSettingsDefaults();
    s.fps=NAN;s.delay=INFINITY;s.ramp=-10;s.limitFPS=-2;
    s=NanoSettingsSanitize(s);
    assert(s.fps==30 && fabs(s.delay-0.15)<0.001 && s.ramp==0.25f && s.limitFPS==1);
    s.fps=61;s.delay=-1;s.ramp=2;s=NanoSettingsSanitize(s);
    assert(s.fps==60 && s.delay==0 && s.ramp==1.5f);
    char tiny[4];assert(NanoSettingsSerialize(tiny,sizeof(tiny),s)==-1);
    char config[1024];assert(NanoSettingsSerialize(config,sizeof(config),NanoSettingsDefaults())>0);
    LoadSaved(config);
    CMenuNanoOptions menu;menu._Init();menu._VidInit();menu.Defaults();
    assert(cvars["fps_max"]==30 && cvars["gl_vsync"]==0 && writes==1);
    assert(saved.find("fps_max \"30\"")!=std::string::npos);
    menu.fps.SetCurrentValue(45);menu.Changed();
    assert(cvars["fps_max"]==45 && !menu.fps.grayed);
    assert(!strcmp(menu.labels[0],"FPS cap: 45"));
    menu.limitFPS.bChecked=false;menu.Changed();
    assert(cvars["fps_max"]==0 && cvars["nano_fps_value"]==45);
    assert(menu.fps.grayed);
    assert(saved.find("set nano_fps_value \"45\"")!=std::string::npos);
    assert(saved.find("fps_max \"0\"")!=std::string::npos);
    menu.limitFPS.bChecked=true;menu.Changed();assert(cvars["fps_max"]==45);
    writeOK=false;menu.Changed();assert(strstr(menu.saveStatus.szName,"Save failed"));
    menu._VidInit();assert(menu.frameSleep.visible && menu.fps.GetCurrentValue()==45);
    native=false;menu._VidInit();assert(!menu.frameSleep.visible);
    writeOK=true;menu.Defaults();assert(cvars["fps_max"]==30 && cvars["nano_look_accel"]==1);
    CMenuNanoOptions aim(1);aim._Init();aim._VidInit();
    aim.yaw.SetCurrentValue(85);aim.pitch.SetCurrentValue(90);aim.fastMultiplier.SetCurrentValue(2);
    aim.Changed();
    assert(cvars["cl_yawspeed"]==85 && cvars["cl_pitchspeed"]==90 && cvars["nano_look_max_yaw"]==170);
    assert(commands.find("cl_yawspeed 170.00; cl_pitchspeed 180.00")!=std::string::npos);
    assert(commands.find("cl_yawspeed 85.00; cl_pitchspeed 90.00")!=std::string::npos);
    CMenuNanoOptions hud(2);hud._Init();hud._VidInit();
    hud.bottom.SetCurrentValue(1);hud.crosshair.SetCurrentValue(2.5f);hud.Changed();
    assert(cvars["cl_yawspeed"]==85 && cvars["nano_hud_bottom"]==1 && cvars["nano_hud_crosshair"]==2.5f);
    std::string prefs=saved;cvars.clear();LoadSaved(config);LoadSaved(prefs);
    CMenuNanoOptions reopened(1);reopened._Init();reopened._VidInit();
    assert(reopened.yaw.GetCurrentValue()==85 && reopened.bottom.GetCurrentValue()==1);
    reopened.Defaults();assert(cvars["cl_yawspeed"]==70 && cvars["nano_look_accel"]==1);
    assert(cvars["nano_hud_bottom"]==1); // reset only the active page
    hud._VidInit();hud.Defaults();assert(fabs(cvars["nano_hud_bottom"]-0.8f)<0.0001f);
    gMenu.m_gameinfo.gamefolder="valve";hud._VidInit();assert(!hud.radar.visible && hud.menuText.visible);
    assert(!strcmp(menu.saveStatus.szName,"Changes saved"));
    saved="fps_max \"57\"\nset nano_fps_value \"57\"\ncustom_option 123\n";
    cvars["fps_max"]=57;cvars["nano_fps_value"]=57;
    CMenuNanoHUD preserve;preserve._Init();preserve._VidInit();preserve.Changed();
    assert(cvars["fps_max"]==57 && cvars["nano_fps_value"]==57 && saved.find("custom_option 123")!=std::string::npos);
    assert(saved.find("fps_max \"57\"")!=std::string::npos);
    return 0;
}
'''
path=root/'build/test-nano-options.cpp'
path.parent.mkdir(parents=True,exist_ok=True);path.write_text(code,encoding='utf-8')
exe=path.with_suffix('')
shim=root/'build/nano-options-shim';shim.mkdir(exist_ok=True)
for name in ('Slider.h','CheckBox.h','Action.h'):(shim/name).write_text('// Host harness declarations supplied before the actual menu header.\n')
subprocess.run(['g++','-std=c++11','-fno-rtti','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-I',str(root/'src'),'-I',str(shim),str(path),'-o',str(exe)],check=True)
subprocess.run([str(exe)],check=True)
runner=(root/'tools/nano-run.sh').read_text(encoding='utf-8')
assert runner.index('+exec nano-controls.cfg')<runner.index('+exec nano-settings.cfg')<runner.index('+nano_profile 1')
print('Actual Nano option callbacks: live FPS/toggles, remembered value, persistence, errors and defaults passed.')
