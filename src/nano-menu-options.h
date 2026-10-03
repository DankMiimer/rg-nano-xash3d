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
    explicit CMenuNanoOptions(int page=0) : CMenuFramework("CMenuNanoOptions"), page(page) {}
private:
    int page;
    CMenuCheckBox limitFPS, frameSleep, lookAccel;
    CMenuSlider fps, delay, ramp, yaw, pitch, fastMultiplier;
    CMenuSlider bottom, side, radar, crosshair, menuText;
    CMenuAction saveStatus;
    char labels[11][48];

    NanoSettings ReadControls()
    {
        NanoSettings s=NanoSettingsDefaults();
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
        snprintf(labels[5],sizeof(labels[5]),"L fast aim: %.2fx",fastMultiplier.GetCurrentValue());
        snprintf(labels[6],sizeof(labels[6]),"Bottom HUD: %.1f%%",100*bottom.GetCurrentValue());
        snprintf(labels[7],sizeof(labels[7]),"Side HUD: %.1f%%",100*side.GetCurrentValue());
        snprintf(labels[8],sizeof(labels[8]),"Radar: %.0f%%",100*radar.GetCurrentValue());
        snprintf(labels[9],sizeof(labels[9]),"Crosshair: %.0f%%",100*crosshair.GetCurrentValue());
        snprintf(labels[10],sizeof(labels[10]),"Team/buy text: %.0f%%",100*menuText.GetCurrentValue());
        fps.SetGrayed(!limitFPS.bChecked);delay.SetGrayed(!lookAccel.bChecked);ramp.SetGrayed(!lookAccel.bChecked);
    }
    void Changed()
    {
        NanoSettings s=ReadControls();
        const char *names[]={"nano_fps_limit","nano_fps_value","fps_max","gl_vsync","nano_frame_sleep",
            "nano_look_accel","nano_look_delay","nano_look_ramp","nano_aim_yaw","nano_aim_pitch","nano_aim_fast_multiplier",
            "cl_yawspeed","cl_pitchspeed","nano_look_max_yaw","nano_look_fast",
            "nano_hud_bottom","nano_hud_side","nano_hud_radar","nano_hud_crosshair","nano_hud_menu"};
        const float values[]={(float)s.limitFPS,s.fps,s.limitFPS?s.fps:0,0,(float)s.frameSleep,
            (float)s.lookAccel,s.delay,s.ramp,s.yaw,s.pitch,s.fastMultiplier,
            s.yaw,s.pitch,s.yaw*s.fastMultiplier,0,s.bottom,s.side,s.radar,s.crosshair,s.menu};
        for (unsigned i=0;i<sizeof(names)/sizeof(names[0]);++i) EngFuncs::CvarSetValue(names[i],values[i]);
        char aim[256];
        if (NanoSettingsAimCommands(aim,sizeof(aim),s)>=0) EngFuncs::ClientCmd(false,aim);
        Labels();
        char text[1024];
        int length=NanoSettingsSerialize(text,sizeof(text),s);
        saveStatus.szName=length>=0 && EngFuncs::COM_SaveFile("nano-settings.cfg",text,length)
            ? "Changes saved" : "Save failed; changes are temporary";
    }
    void Defaults()
    {
        NanoSettings s=NanoSettingsDefaults();
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
        bottom.Setup(0.75f,1.125f,0.025f);side.Setup(0.75f,1.5f,0.025f);
        radar.Setup(0.25f,0.75f,0.05f);crosshair.Setup(1,3,0.25f);menuText.Setup(1,1.25f,0.05f);
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
        crosshair.LinkCvar("nano_hud_crosshair");menuText.LinkCvar("nano_hud_menu");
        frameSleep.SetVisibility(EngFuncs::GetCvarString("nano_profile")[0]!=0);
        bool cs=!stricmp(gMenu.m_gameinfo.gamefolder,"cstrike");
        radar.SetVisibility(cs);menuText.SetVisibility(cs);
        Labels();
    }
};
class CMenuNanoPerformance : public CMenuNanoOptions { public: CMenuNanoPerformance():CMenuNanoOptions(0){} };
class CMenuNanoAiming : public CMenuNanoOptions { public: CMenuNanoAiming():CMenuNanoOptions(1){} };
class CMenuNanoHUD : public CMenuNanoOptions { public: CMenuNanoHUD():CMenuNanoOptions(2){} };
ADD_MENU(menu_nano_performance,CMenuNanoPerformance,UI_NanoPerformance_Menu);
ADD_MENU(menu_nano_aiming,CMenuNanoAiming,UI_NanoAiming_Menu);
ADD_MENU(menu_nano_hud,CMenuNanoHUD,UI_NanoHUD_Menu);
class CMenuNanoSettings : public CMenuFramework {
public: CMenuNanoSettings():CMenuFramework("CMenuNanoOptions"){}
private:
    void _Init() override {
        AddButton("Performance",nullptr,PC_CONFIG,UI_NanoPerformance_Menu);
        AddButton("Aiming",nullptr,PC_CONTROLS,UI_NanoAiming_Menu);
        AddButton("HUD sizes",nullptr,PC_CONFIG,UI_NanoHUD_Menu);
        AddButton("Done",nullptr,PC_DONE,VoidCb(&CMenuNanoSettings::Hide));
    }
};
ADD_MENU(menu_nano_options,CMenuNanoSettings,UI_NanoOptions_Menu);
#endif
