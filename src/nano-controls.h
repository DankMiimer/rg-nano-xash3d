// SPDX-License-Identifier: GPL-3.0-or-later
#ifndef NANO_CONTROLS_H
#define NANO_CONTROLS_H
#include <stdint.h>
// Physical order matches the private keymap's evdev codes 59..70.
enum {NC_UP,NC_DOWN,NC_LEFT,NC_RIGHT,NC_A,NC_B,NC_X,NC_Y,NC_L,NC_R,NC_START,NC_SELECT,NC_BUTTONS};
enum {NC_NONE,NC_FORWARD,NC_BACK,NC_MOVELEFT,NC_MOVERIGHT,NC_LOOKRIGHT,NC_LOOKDOWN,NC_LOOKUP,NC_LOOKLEFT,
 NC_ATTACK,NC_RELOAD,NC_PRIMARY,NC_DUCK,NC_JUMP,NC_NEXT,NC_PREV,NC_ATTACK2,NC_EXTRA,NC_CENTER,
 NC_UIUP,NC_UIDOWN,NC_UILEFT,NC_UIRIGHT,NC_CONFIRM,NC_CANCEL,NC_SLOW,NC_UISAVE,NC_UIDELETE};
typedef struct {uint16_t down,blocked;uint32_t output;int context,selectUsed;} NanoControlState;
typedef void (*NanoControlEmit)(int action,int down,void *opaque);
static inline uint32_t NanoControlActions(uint16_t buttons,int context)
{
    static const int normal[NC_BUTTONS]={NC_FORWARD,NC_BACK,NC_MOVELEFT,NC_MOVERIGHT,NC_LOOKRIGHT,NC_LOOKDOWN,NC_LOOKUP,NC_LOOKLEFT,NC_ATTACK,NC_NONE,NC_PRIMARY,NC_NONE};
    static const int modified[NC_BUTTONS]={NC_FORWARD,NC_BACK,NC_MOVELEFT,NC_MOVERIGHT,NC_DUCK,NC_JUMP,NC_NEXT,NC_PREV,NC_ATTACK2,NC_NONE,NC_EXTRA,NC_CENTER};
    static const int menu[NC_BUTTONS]={NC_UIUP,NC_UIDOWN,NC_UILEFT,NC_UIRIGHT,NC_CONFIRM,NC_CANCEL,NC_NONE,NC_NONE,NC_NONE,NC_NONE,NC_NONE,NC_NONE};
    const int *map=context==1?((buttons&(1u<<NC_R))?modified:normal):menu;
    uint32_t out=0;
    for(int i=0;i<NC_BUTTONS;++i)if((buttons&(1u<<i)) && map[i])out|=1u<<map[i];
    if(context==0 && (buttons&(1u<<NC_X)))out|=1u<<NC_UISAVE;
    if(context==0 && (buttons&(1u<<NC_Y)))out|=1u<<NC_UIDELETE;
    if(context==1 && !(buttons&(1u<<NC_R)) && (buttons&(1u<<NC_SELECT)) &&
       (buttons&((1u<<NC_A)|(1u<<NC_B)|(1u<<NC_X)|(1u<<NC_Y))))out|=1u<<NC_SLOW;
    return out;
}
static inline void NanoControlUpdate(NanoControlState *s,int context,NanoControlEmit emit,void *opaque)
{
    if(s->context!=-1 && s->context!=context){s->blocked|=s->down;s->selectUsed=1;}
    s->context=context;s->blocked&=s->down;
    uint32_t next=NanoControlActions(s->down & ~s->blocked,context);
    uint32_t old=s->output;s->output=next;
    // Release former actions before pressing replacements, including modifier changes.
    for(int i=1;i<=NC_UIDELETE;++i)if((old&(1u<<i)) && !(next&(1u<<i)))emit(i,0,opaque);
    for(int i=1;i<=NC_UIDELETE;++i)if((next&(1u<<i)) && !(old&(1u<<i)))emit(i,1,opaque);
}
static inline void NanoControlEvent(NanoControlState *s,int button,int value,int context,NanoControlEmit emit,void *opaque)
{
    if(button<0 || button>=NC_BUTTONS || value==2)return;
    NanoControlUpdate(s,context,emit,opaque);
    // Defer reload to a plain Select release so aim/center chords never reload.
    int reload=!value && button==NC_SELECT && (s->down&(1u<<NC_SELECT)) &&
        !s->selectUsed && context==1 && !(s->blocked&(1u<<NC_SELECT));
    if(value){if(button==NC_SELECT && !(s->down&(1u<<NC_SELECT)))s->selectUsed=context!=1;s->down|=1u<<button;}
    else{s->down&=~(1u<<button);s->blocked&=~(1u<<button);}
    if((s->down&(1u<<NC_SELECT)) &&
       (s->down&((1u<<NC_R)|(1u<<NC_A)|(1u<<NC_B)|(1u<<NC_X)|(1u<<NC_Y))))s->selectUsed=1;
    NanoControlUpdate(s,context,emit,opaque);
    if(reload){emit(NC_RELOAD,1,opaque);emit(NC_RELOAD,0,opaque);}
}
static inline void NanoControlRelease(NanoControlState *s,NanoControlEmit emit,void *opaque)
{s->down=0;s->blocked=0;s->selectUsed=0;NanoControlUpdate(s,s->context,emit,opaque);s->context=-1;}
#endif
