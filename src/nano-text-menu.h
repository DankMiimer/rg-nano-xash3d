// SPDX-License-Identifier: GPL-3.0-or-later
#ifndef NANO_TEXT_MENU_H
#define NANO_TEXT_MENU_H
static inline int NanoMenuSelection(int valid,int selected,int direction)
{
    if(!(valid&1023))return 0;
    if(selected<1 || selected>10 || !(valid&(1<<(selected-1))))selected=0;
    if(!direction && selected)return selected;
    for(int i=0;i<10;++i){
        selected=direction<0?(selected>1?selected-1:10):(selected<10?selected+1:1);
        if(valid&(1<<(selected-1)))return selected;
    }
    return 0;
}
#endif
