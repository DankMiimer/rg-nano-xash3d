// SPDX-License-Identifier: GPL-3.0-or-later
#ifndef NANO_SAVE_BROWSER_H
#define NANO_SAVE_BROWSER_H
#include <cstring>
// Keep the selected save in the three-row viewport without a scroll indicator.
static inline int NanoSaveWindow(int selected,int count,int start) {
    if(count<=3)return 0;
    if(selected<start)start=selected;
    if(selected>=start+3)start=selected-2;
    if(start<0)start=0;
    if(start>count-3)start=count-3;
    return start;
}
// Save filenames become quoted engine command arguments. Reject delimiters,
// retaining ordinary user names, spaces and UTF-8 characters.
static inline bool NanoSaveNameValid(const char *name) {
    return name && *name && !strpbrk(name,"\";\r\n/\\");
}
#endif
