// SPDX-License-Identifier: GPL-3.0-or-later
#include <linux/random.h>
#include <sys/ioctl.h>
#include <fcntl.h>
#include <unistd.h>
#include <stdio.h>
int main(int argc,char **argv) {
 struct {int entropy_count;int buf_size;unsigned char buf[256];} seed;
 if(argc!=2)return 2;
 FILE *in=fopen(argv[1],"rb");if(!in)return 3;
 seed.buf_size=fread(seed.buf,1,sizeof seed.buf,in);fclose(in);
 if(seed.buf_size<32)return 4;
 seed.entropy_count=seed.buf_size*8;
 int fd=open("/dev/random",O_RDWR); if(fd<0)return 5;
 int ret=ioctl(fd,RNDADDENTROPY,&seed);close(fd);
 return ret<0?6:0;
}
