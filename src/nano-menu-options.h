// SPDX-License-Identifier: GPL-3.0-or-later
// Copyright (c) 2026 rg-nano-xash3d contributors
// Included once by each Configuration.cpp; reuses upstream controls and artwork.
#ifndef NANO_MENU_OPTIONS_H
#define NANO_MENU_OPTIONS_H
#include "Slider.h"
#include "CheckBox.h"
#include "Action.h"
#include "nano-settings.h"

class CMenuNanoOptions : public CMenuFramework
{
public:
    explicit CMenuNanoOptions(int page=0) : CMenuFramework(page==0?"CMenuNanoPerformance":page==1?"CMenuNanoAiming":"CMenuNanoHUD"), page(page) {}
private:
    int page;
    CMenuCheckBox limitFPS, frameSleep, lookAccel;
    CMenuSlider fps, delay, ramp, yaw, pitch, fastMultiplier;
    CMenuSlider bottom, side, radar, crosshair, menuText;
    CMenuAction saveStatus;
    char labels[11][48];

    NanoSettings ReadControls()
    {
        NanoSettings s=NanoSettingsDefaultsForGame(!stricmp(gMenu.m_gameinfo.gamefolder,"cstrike"));
        s.limitFPS=limitFPS.bChecked;s.frameSleep=frameSleep.bChecked;s.lookAccel=lookAccel.bChecked;
        s.fps=fps.GetCurrentValue();s.delay=delay.GetCurrentValue();s.ramp=ramp.GetCurrentValue();
        s.yaw=yaw.GetCurrentValue();s.pitch=pitch.GetCurrentValue();s.fastMultiplier=fastMultiplier.GetCurrentValue();
        s.bottom=bottom.GetCurrentValue();s.side=side.GetCurrentValue();s.radar=radar.GetCurrentValue();
        s.crosshair=crosshair.GetCurrentValue();s.menu=menuText.GetCurrentValue();
        return NanoSettingsSanitize(s);
    }
    void Labels()
    {
        snprintf(labels[0],sizeof(labels[0]),"FPS cap: %.0f",fps.GetCurrentValue());
        snprintf(labels[1],sizeof(labels[1]),"Turn delay: %.2f s",delay.GetCurrentValue());
        snprintf(labels[2],sizeof(labels[2]),"Turn ramp: %.2f s",ramp.GetCurrentValue());
        snprintf(labels[3],sizeof(labels[3]),"Horizontal aim: %.0f deg/s",yaw.GetCurrentValue());
        snprintf(labels[4],sizeof(labels[4]),"Vertical aim: %.0f deg/s",pitch.GetCurrentValue());
        snprintf(labels[5],sizeof(labels[5]),"Original L fast aim: %.2fx",fastMultiplier.GetCurrentValue());
        snprintf(labels[6],sizeof(labels[6]),"Bottom HUD: %.1f%%",100*bottom.GetCurrentValue());
        snprintf(labels[7],sizeof(labels[7]),"Side HUD: %.1f%%",100*side.GetCurrentValue());
        snprintf(labels[8],sizeof(labels[8]),"Radar: %.0f%%",100*radar.GetCurrentValue());
        snprintf(labels[9],sizeof(labels[9]),"Crosshair: %.0f%%",100*crosshair.GetCurrentValue());
        snprintf(labels[10],sizeof(labels[10]),"HUD text: %.0f px",menuText.GetCurrentValue());
        fps.SetGrayed(!limitFPS.bChecked);delay.SetGrayed(!lookAccel.bChecked);ramp.SetGrayed(!lookAccel.bChecked);
    }
    static int SettingPage(const char *line) {
        char key[64]={0},value[64]={0};sscanf(line,"%63s %63s",key,value);
        if(!strcmp(key,"set") || !strcmp(key,"alias")){strcpy(key,value);if(key[0]=='"'){memmove(key,key+1,strlen(key));char *end=strchr(key,'"');if(end)*end=0;}}
        const char *performance[]={"nano_fps_limit","nano_fps_value","fps_max","gl_vsync","nano_frame_sleep"};
        const char *aim[]={"nano_look_accel","nano_look_delay","nano_look_ramp","nano_aim_yaw","nano_aim_pitch","nano_aim_fast_multiplier","cl_yawspeed","cl_pitchspeed","nano_look_max_yaw","nano_look_fast","+nano_aim","-nano_aim"};
        const char *hud[]={"nano_hud_bottom","nano_hud_side","nano_hud_radar","nano_hud_crosshair","nano_hud_menu","nano_hud_text_height","nano_ui_profile_version","hud_scale"};
        for(unsigned i=0;i<sizeof(performance)/sizeof(performance[0]);i++)if(!strcmp(key,performance[i]))return 0;
        for(unsigned i=0;i<sizeof(aim)/sizeof(aim[0]);i++)if(!strcmp(key,aim[i]))return 1;
        for(unsigned i=0;i<sizeof(hud)/sizeof(hud[0]);i++)if(!strcmp(key,hud[i]))return 2;
        return -1;
    }
    bool SavePage(const char *serialized,int length) {
        int oldLength=0;char *old=(char*)EngFuncs::COM_LoadFile("nano-settings.cfg",&oldLength);
        if(!old)return EngFuncs::COM_SaveFile("nano-settings.cfg",serialized,length)!=0;
        char merged[4096];int used=0;bool fits=true;
        for(int pass=0;pass<2 && fits;pass++) {
            const char *p=pass?serialized:old;int remaining=pass?length:oldLength;
            while(remaining>0 && fits) {
                int n=0;while(n<remaining && p[n]!='\n')++n;if(n<remaining)++n;
                char line[1024];int copy=n<(int)sizeof(line)-1?n:(int)sizeof(line)-1;memcpy(line,p,copy);line[copy]=0;
                if(pass?SettingPage(line)==page:SettingPage(line)!=page) {
                    if(used+n+1>=(int)sizeof(merged)){fits=false;break;}
                    memcpy(merged+used,p,n);used+=n;if(merged[used-1]!='\n')merged[used++]='\n';
                }
                p+=n;remaining-=n;
            }
        }
        EngFuncs::COM_FreeFile(old);
        return fits && EngFuncs::COM_SaveFile("nano-settings.cfg",merged,used)!=0;
    }
    void Changed()
    {
        NanoSettings s=ReadControls();
        const char *names[]={"nano_fps_limit","nano_fps_value","fps_max","gl_vsync","nano_frame_sleep",
            "nano_look_accel","nano_look_delay","nano_look_ramp","nano_aim_yaw","nano_aim_pitch","nano_aim_fast_multiplier",
            "cl_yawspeed","cl_pitchspeed","nano_look_max_yaw","nano_look_fast",
            "nano_hud_bottom","nano_hud_side","nano_hud_radar","nano_hud_crosshair","nano_hud_text_height"};
        const float values[]={(float)s.limitFPS,s.fps,s.limitFPS?s.fps:0,0,(float)s.frameSleep,
            (float)s.lookAccel,s.delay,s.ramp,s.yaw,s.pitch,s.fastMultiplier,
            s.yaw,s.pitch,s.yaw*s.fastMultiplier,0,s.bottom,s.side,s.radar,s.crosshair,s.menu};
        for(unsigned i=0;i<sizeof(names)/sizeof(names[0]);++i)if((i<5?0:i<15?1:2)==page)EngFuncs::CvarSetValue(names[i],values[i]);
        char aim[256];
        if(page==1 && NanoSettingsAimCommands(aim,sizeof(aim),s)>=0) EngFuncs::ClientCmd(false,aim);
        Labels();
        char text[1024];
        int length=NanoSettingsSerialize(text,sizeof(text),s);
        saveStatus.szName=length>=0 && SavePage(text,length)
            ? "Changes saved" : "Save failed; changes are temporary";
    }
    void Defaults()
    {
        NanoSettings s=NanoSettingsDefaultsForGame(!stricmp(gMenu.m_gameinfo.gamefolder,"cstrike"));
        if (page==0) {
            limitFPS.bChecked=s.limitFPS;frameSleep.bChecked=s.frameSleep;fps.SetCurrentValue(s.fps);
        } else if (page==1) {
            lookAccel.bChecked=s.lookAccel;delay.SetCurrentValue(s.delay);ramp.SetCurrentValue(s.ramp);
            yaw.SetCurrentValue(s.yaw);pitch.SetCurrentValue(s.pitch);fastMultiplier.SetCurrentValue(s.fastMultiplier);
        } else {
            bottom.SetCurrentValue(s.bottom);side.SetCurrentValue(s.side);radar.SetCurrentValue(s.radar);
            crosshair.SetCurrentValue(s.crosshair);menuText.SetCurrentValue(s.menu);
        }
        Changed();
    }
    void _Init() override
    {
        limitFPS.szName="Limit FPS";frameSleep.szName="Sleep between frames";lookAccel.szName="Look acceleration";
        CMenuSlider *sliders[]={&fps,&delay,&ramp,&yaw,&pitch,&fastMultiplier,&bottom,&side,&radar,&crosshair,&menuText};
        for (unsigned i=0;i<sizeof(sliders)/sizeof(sliders[0]);++i) sliders[i]->szName=labels[i];
        fps.Setup(15,60,5);delay.Setup(0,0.5f,0.05f);ramp.Setup(0.25f,1.5f,0.05f);
        yaw.Setup(30,120,5);pitch.Setup(30,150,5);fastMultiplier.Setup(1,4,0.25f);
        bool cs=!stricmp(gMenu.m_gameinfo.gamefolder,"cstrike");
        bottom.Setup(0.6f,2.0f,cs?0.05f:0.125f);
        side.Setup(0.6f,2.0f,cs?0.05f:0.125f);
        radar.Setup(0.25f,0.75f,0.05f);crosshair.Setup(1,3,0.25f);menuText.Setup(12,18,2);
        AddButton("Done",nullptr,PC_DONE,VoidCb(&CMenuNanoOptions::Hide));
        CMenuBaseItem *performance[]={&limitFPS,&fps,&frameSleep};
        CMenuBaseItem *aiming[]={&yaw,&pitch,&fastMultiplier,&lookAccel,&delay,&ramp};
        CMenuBaseItem *hud[]={&bottom,&side,&radar,&crosshair,&menuText};
        CMenuBaseItem **rows=page==0?performance:page==1?aiming:hud;
        unsigned count=page==0?3:page==1?6:5;
        for (unsigned i=0;i<count;++i) { rows[i]->onChanged=VoidCb(&CMenuNanoOptions::Changed);AddItem(*rows[i]); }
        AddButton("Reset these settings",nullptr,PC_CONFIG,VoidCb(&CMenuNanoOptions::Defaults));
        saveStatus.szName="Changes save automatically";saveStatus.iFlags|=QMF_INACTIVE;AddItem(saveStatus);
    }
    void _VidInit() override
    {
        // Read every group before saving: another page's choices must be retained.
        limitFPS.LinkCvar("nano_fps_limit");fps.LinkCvar("nano_fps_value");
        frameSleep.LinkCvar("nano_frame_sleep");lookAccel.LinkCvar("nano_look_accel");
        delay.LinkCvar("nano_look_delay");ramp.LinkCvar("nano_look_ramp");
        yaw.LinkCvar("nano_aim_yaw");pitch.LinkCvar("nano_aim_pitch");fastMultiplier.LinkCvar("nano_aim_fast_multiplier");
        bottom.LinkCvar("nano_hud_bottom");side.LinkCvar("nano_hud_side");radar.LinkCvar("nano_hud_radar");
        crosshair.LinkCvar("nano_hud_crosshair");menuText.LinkCvar("nano_hud_text_height");
        frameSleep.SetVisibility(EngFuncs::GetCvarString("nano_profile")[0]!=0);
        bool cs=!stricmp(gMenu.m_gameinfo.gamefolder,"cstrike");
        radar.SetVisibility(cs);menuText.SetVisibility(true);
        Labels();
    }
};
class CMenuNanoPerformance : public CMenuNanoOptions { public: CMenuNanoPerformance():CMenuNanoOptions(0){} };
class CMenuNanoAiming : public CMenuNanoOptions { public: CMenuNanoAiming():CMenuNanoOptions(1){} };
class CMenuNanoHUD : public CMenuNanoOptions { public: CMenuNanoHUD():CMenuNanoOptions(2){} };
ADD_MENU(menu_nano_performance,CMenuNanoPerformance,UI_NanoPerformance_Menu);
ADD_MENU(menu_nano_aiming,CMenuNanoAiming,UI_NanoAiming_Menu);
ADD_MENU(menu_nano_hud,CMenuNanoHUD,UI_NanoHUD_Menu);
#include "nano-menu-controls.h"
class CMenuNanoSettings : public CMenuFramework {
public: CMenuNanoSettings():CMenuFramework("CMenuNanoOptions"){}
private:
    void _Init() override {
        AddButton("Performance",nullptr,PC_CONFIG,UI_NanoPerformance_Menu);
        AddButton("Aiming",nullptr,PC_CONTROLS,UI_NanoAiming_Menu);
        AddButton("Control scheme",nullptr,PC_CONTROLS,UI_NanoControls_Menu);
        AddButton("HUD sizes",nullptr,PC_CONFIG,UI_NanoHUD_Menu);
        AddButton("Done",nullptr,PC_DONE,VoidCb(&CMenuNanoSettings::Hide));
    }
};
ADD_MENU(menu_nano_options,CMenuNanoSettings,UI_NanoOptions_Menu);
#endif
