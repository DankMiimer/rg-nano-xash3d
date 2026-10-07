// SPDX-License-Identifier: GPL-3.0-or-later
#ifndef NANO_CONTROL_PREFERENCE_H
#define NANO_CONTROL_PREFERENCE_H
#include <stddef.h>
#include <stdio.h>
#include <string.h>
static inline int NanoControlPreference(const char *data,size_t size)
{
    // One bounded data line, shared with the launcher's strict reader.
    return data && ((size==8 && !memcmp(data,"scheme 1",8)) || (size==9 && !memcmp(data,"scheme 1\n",9)));
}
static inline int NanoControlPreferenceSave(char *out,size_t size,int scheme)
{int n=snprintf(out,size,"scheme %d\n",scheme==1);return n>=0 && (size_t)n<size?n:-1;}
#endif
