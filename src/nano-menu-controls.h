// SPDX-License-Identifier: GPL-3.0-or-later
#ifndef NANO_MENU_CONTROLS_H
#define NANO_MENU_CONTROLS_H
#include "CheckBox.h"
#include "Action.h"
#include "nano-control-preference.h"
class CMenuNanoControls : public CMenuFramework {
public:CMenuNanoControls():CMenuFramework("CMenuNanoControls"),loading(false){}
private:
    bool loading;
    CMenuCheckBox face;
    CMenuAction status,help[8];
    void Changed() {
        if(loading)return;
        char text[16];int n=NanoControlPreferenceSave(text,sizeof(text),face.bChecked);
        status.szName=n>=0 && EngFuncs::COM_SaveFile("nano-control.cfg",text,n)
            ?"Saved; restart game to apply":"Save failed; selection unchanged";
    }
    void _Init() override {
        AddButton("Done",nullptr,PC_DONE,VoidCb(&CMenuNanoControls::Hide));
        face.szName="Face-button aiming";face.onChanged=VoidCb(&CMenuNanoControls::Changed);AddItem(face);
        status.szName="Applies on next launch";status.iFlags|=QMF_INACTIVE;AddItem(status);
        const char *labels[]={"D-pad: move; X/B: look up/down","Y/A: look left/right; L: fire","R+A: crouch; R+B: jump","R+X/Y: next/previous weapon","R+L: secondary; Select: reload","R+Select: level view",nullptr,"Select + face: quarter-speed aim"};
        labels[6]=!stricmp(gMenu.m_gameinfo.gamefolder,"cstrike")?"Start: buy; R+Start: use":"Start: use; R+Start: flashlight";
        for(int i=0;i<8;++i){help[i].szName=labels[i];help[i].iFlags|=QMF_INACTIVE;AddItem(help[i]);}
    }
    void _VidInit() override {
        loading=true;int size=0;char *data=(char*)EngFuncs::COM_LoadFile("nano-control.cfg",&size);
        face.bChecked=data && size>=0 && size<=16 && NanoControlPreference(data,(size_t)size);
        if(data)EngFuncs::COM_FreeFile(data);
        face.SetGrayed(EngFuncs::GetCvarString("nano_control_scheme")[0]==0);
        loading=false;
    }
};
ADD_MENU(menu_nano_controls,CMenuNanoControls,UI_NanoControls_Menu);
#endif
