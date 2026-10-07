// SPDX-License-Identifier: GPL-3.0-or-later
#ifndef NANO_MENU_THEME_H
#define NANO_MENU_THEME_H
#include "../BaseMenu.h"

// Native menus share the established geometry; colours follow WON / TrackerScheme.
static inline bool NanoThemeEnabled() {
    return ScreenWidth<=320 && EngFuncs::GetCvarFloat("nano_hud_profile");
}
static inline bool NanoThemeCS() {return !stricmp(gMenu.m_gameinfo.gamefolder,"cstrike");}
static inline unsigned NanoThemePanel() {return NanoThemeCS()?0xff4c5844u:0xff383838u;}
static inline unsigned NanoThemeField() {return NanoThemeCS()?0xff3e4637u:0xff292929u;}
static inline unsigned NanoThemeLight() {return NanoThemeCS()?0xff889180u:0xff818181u;}
static inline unsigned NanoThemeDark() {return NanoThemeCS()?0xff282e22u:0xff191919u;}
static inline unsigned NanoThemeAccent() {return NanoThemeCS()?0xffc4b550u:0xfff0b418u;}

static inline void NanoThemeApply() {
    if(!NanoThemeEnabled())return;
    uiPromptBgColor=NanoThemePanel();uiInputBgColor=NanoThemeField();
    uiInputFgColor=NanoThemeLight();
    uiPromptTextColor=NanoThemeCS()?0xffd8ded3u:0xfff0b418u;
    uiInputTextColor=uiPromptTextColor;
    uiPromptFocusColor=NanoThemeCS()?0xffc4b550u:0xffffff00u;
    uiColorHelp=NanoThemeCS()?0xffa0aa95u:0xffa0a0a0u;
}
static inline void NanoThemeBevel(int x,int y,int w,int h,unsigned fill,bool inset=false) {
    if(w<2 || h<2)return;
    unsigned light=inset?NanoThemeDark():NanoThemeLight();
    unsigned dark=inset?NanoThemeLight():NanoThemeDark();
    UI_FillRect(x,y,w,h,fill);
    UI_FillRect(x,y,w,1,light);UI_FillRect(x,y,1,h,light);
    UI_FillRect(x,y+h-1,w,1,dark);UI_FillRect(x+w-1,y,1,h,dark);
}
static inline const char *NanoThemeTitle(const char *name) {
    struct Title {const char *name,*text;};
    static const Title titles[]={
        {"CMenuOptions","Options"},{"CMenuAudio","Audio"},{"CMenuControls","Controls"},
        {"CAdvancedControls","Advanced controls"},{"CMenuGameOptions","Game options"},
        {"CMenuVideo","Video"},{"CMenuVidOptions","Video options"},{"CMenuVidModes","Video modes"},
        {"CMenuNewGame","New Game"},{"CMenuMultiplayer","Multiplayer"},
        {"CMenuCreateGame","Create game"},{"CMenuServerBrowser","Servers"},{"CMenuServerInfo","Server info"},
        {"CMenuPlayerSetup","Customize"},{"CMenuCrosshair","Crosshair"},
        {"CMenuLoadGame","Load Game"},{"CMenuSaveGame","Save/Load Game"},{"CMenuSaveLoad","Save/Load Game"},
        {"CMenuNanoOptions","Nano settings"},{"CMenuNanoControls","Nano controls"},
        {"CMenuNanoPerformance","Performance"},{"CMenuNanoAiming","Aiming"},{"CMenuNanoHUD","HUD"},
        {"CMenuNanoMatch","New Game"},{"CMenuNanoMatchAdvanced","Advanced match"},
        {"CMenuFileDialog","Choose file"},{"CMenuInputDevices","Input devices"},
        {"CMenuGamePad","Gamepad"},{"CMenuGyro","Gyroscope"},
        {"CMenuTouchButtons","Touch buttons"},{"CMenuTouchEdit","Edit touch controls"},{"CMenuTouchOptions","Touch options"},
        {"CMenuCustomGame","Change game"},{"ScriptConfig","Game options"}
    };
    for(unsigned i=0;i<sizeof(titles)/sizeof(titles[0]);++i)
        if(!strcmp(name,titles[i].name))return !strcmp(name,"CMenuOptions") && !NanoThemeCS()?"Configuration":titles[i].text;
    return "Options";
}

// Loaded once by BackgroundBitmap, including the low-memory renderer path.
// Assets are prepared from the user's game files, outside the source repository.
void NanoMenuDrawBackdrop(bool allowWorld=false);
void NanoMenuDrawLogo();
#endif
