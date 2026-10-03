// SPDX-License-Identifier: GPL-3.0-or-later
// Small Linux game supervisor. Stop requests target only its own child group.
#define _GNU_SOURCE
#include <errno.h>
#include <fcntl.h>
#include <poll.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <sys/un.h>
#include <sys/wait.h>
#include <time.h>
#include <unistd.h>

#define LOG_LIMIT (512UL * 1024UL)
#define STOP_GRACE_MS 5000
static volatile sig_atomic_t interrupted;
static void on_signal(int sig) { interrupted = sig; }
static long long now_ms(void) {
    struct timespec t;
    clock_gettime(CLOCK_MONOTONIC, &t);
    return (long long)t.tv_sec * 1000 + t.tv_nsec / 1000000;
}
typedef struct { FILE *file; char path[1024]; size_t size; } log_t;
static int open_log(log_t *log, const char *dir, const char *name) {
    if (snprintf(log->path, sizeof(log->path), "%s/%s", dir, name) >= (int)sizeof(log->path)) return -1;
    char previous[1040];
    snprintf(previous, sizeof(previous), "%s.1", log->path);
    if (rename(log->path, previous) < 0 && errno != ENOENT) return -1;
    log->file = fopen(log->path, "w");
    log->size = 0;
    return log->file ? 0 : -1;
}
static int write_log(log_t *log, const char *data, size_t len) {
    if (!log->file) return -1;
    if (log->size + len > LOG_LIMIT) {
        char previous[1040];
        snprintf(previous, sizeof(previous), "%s.1", log->path);
        fclose(log->file);
        log->file = NULL;
        if (rename(log->path, previous) < 0) return -1;
        log->file = fopen(log->path, "w");
        log->size = 0;
        if (!log->file) return -1;
    }
    if (fwrite(data, 1, len, log->file) != len || fflush(log->file)) return -1;
    log->size += len;
    return 0;
}
// Xash's own crash handler can print the signal and then exit with code zero.
static int scan_reported_signal(char tail[80], const char *data, size_t len, int previous) {
    char text[4096+80+1];
    size_t old=strlen(tail);
    memcpy(text,tail,old);
    memcpy(text+old,data,len);
    text[old+len]=0;
    for(char *p=text;(p=strstr(p,"Crash: signal "))!=NULL;p++) {
        int sig=0;
        if(sscanf(p,"Crash: signal %d",&sig)==1 && sig>0 && sig<65) previous=sig;
    }
    size_t keep=old+len<79?old+len:79;
    memcpy(tail,text+old+len-keep,keep);
    tail[keep]=0;
    return previous;
}
static unsigned long long read_key(const char *path, const char *key) {
    char line[256], word[80];
    unsigned long long value = 0, result = 0;
    FILE *f = fopen(path, "r");
    if (!f) return 0;
    while (fgets(line, sizeof(line), f))
        if (sscanf(line, "%79s %llu", word, &value) == 2 && !strcmp(word, key)) { result = value; break; }
    fclose(f);
    return result;
}
static void sample(log_t *log, pid_t pid, long long started) {
    char path[80], line[4096], output[512];
    unsigned long long minflt=0, majflt=0, utime=0, stime=0;
    snprintf(path, sizeof(path), "/proc/%d/stat", pid);
    FILE *f = fopen(path, "r");
    if (f) {
        if (fgets(line, sizeof(line), f)) {
            char *p = strrchr(line, ')'), *save = NULL;
            if (p) {
                int field = 3;
                for (char *v = strtok_r(p+1, " ", &save); v; v = strtok_r(NULL, " ", &save), ++field) {
                    if (field==10) minflt=strtoull(v,NULL,10);
                    if (field==12) majflt=strtoull(v,NULL,10);
                    if (field==14) utime=strtoull(v,NULL,10);
                    if (field==15) stime=strtoull(v,NULL,10);
                }
            }
        }
        fclose(f);
    }
    snprintf(path, sizeof(path), "/proc/%d/status", pid);
    int n = snprintf(output, sizeof(output), "%lld,%d,%llu,%llu,%llu,%llu,%llu,%llu,%llu,%llu,%llu\n",
        now_ms()-started, pid, read_key(path,"VmRSS:"), read_key("/proc/meminfo","MemAvailable:"),
        read_key("/proc/meminfo","SwapFree:"), read_key("/proc/vmstat","pswpin"),
        read_key("/proc/vmstat","pswpout"), minflt, majflt, utime, stime);
    if (n > 0 && n < (int)sizeof(output)) write_log(log, output, (size_t)n);
}
static int stop_request(const char *path) {
    struct sockaddr_un addr = { .sun_family = AF_UNIX };
    if (strlen(path) >= sizeof(addr.sun_path)) return 2;
    strcpy(addr.sun_path, path);
    int fd = socket(AF_UNIX, SOCK_DGRAM|SOCK_CLOEXEC, 0);
    if (fd < 0) return 2;
    int ok = sendto(fd, "stop", 4, 0, (struct sockaddr*)&addr, sizeof(addr)) == 4;
    if (!ok) perror("stop request");
    close(fd);
    return ok ? 0 : 3;
}
// A single nonblocking write avoids hanging when the key daemon has no reader.
static int load_keys(const char *config, const char *fifo) {
    char command[1024];
    if (strchr(config, '\n') || strchr(config, '\r')) return 2;
    int len=snprintf(command,sizeof(command),"LOAD %s\n",config);
    if(len<0 || len>=(int)sizeof(command)) return 2;
    long long deadline=now_ms()+3000;
    do {
        int fd=open(fifo,O_WRONLY|O_NONBLOCK|O_CLOEXEC);
        if(fd>=0) {
            struct stat st;
            if(fstat(fd,&st) || !S_ISFIFO(st.st_mode)) { close(fd); return 2; }
            ssize_t n=write(fd,command,(size_t)len);
            close(fd);
            if(n==len) return 0;
            if(n>=0 || (errno!=EAGAIN && errno!=EINTR)) return 3;
        } else if(errno!=ENXIO && errno!=ENOENT && errno!=EINTR) return 3;
        struct timespec delay={0,50000000};
        nanosleep(&delay,NULL);
    } while(now_ms()<deadline);
    fprintf(stderr,"Key daemon did not accept LOAD within three seconds\n");
    return 3;
}
static void child_signal(pid_t pid, int sig) {
    if (kill(-pid, sig) < 0 && errno == ESRCH) kill(pid, sig);
}
int main(int argc, char **argv) {
    signal(SIGPIPE,SIG_IGN);
    if (argc == 4 && !strcmp(argv[1], "--load-keys")) return load_keys(argv[2],argv[3]);
    if (argc == 3 && !strcmp(argv[1], "--stop")) return stop_request(argv[2]);
    if (argc < 5 || strcmp(argv[3], "--")) {
        fprintf(stderr, "usage: %s LOG_DIR SOCKET_PATH -- COMMAND [ARGS...]\n       %s --stop SOCKET_PATH\n", argv[0], argv[0]);
        return 2;
    }
    const char *dir=argv[1], *sockpath=argv[2];
    struct sockaddr_un addr = { .sun_family=AF_UNIX };
    if (strlen(sockpath) >= sizeof(addr.sun_path)) return 2;
    strcpy(addr.sun_path,sockpath);
    int sock=socket(AF_UNIX,SOCK_DGRAM|SOCK_NONBLOCK|SOCK_CLOEXEC,0);
    if (sock<0 || bind(sock,(struct sockaddr*)&addr,sizeof(addr))) {
        perror("supervisor socket (already running or stale socket)");
        if(sock>=0) close(sock);
        return 2; // Never unlink a socket owned by another live supervisor.
    }
    chmod(sockpath,0600);
    if(mkdir(dir,0700) && errno!=EEXIST) { perror("log directory"); close(sock); unlink(sockpath); return 2; }
    char resultpath[1024];
    if(snprintf(resultpath,sizeof(resultpath),"%s/result.txt",dir)>=(int)sizeof(resultpath) ||
       (unlink(resultpath)<0 && errno!=ENOENT)) {
        perror("previous result"); close(sock); unlink(sockpath); return 2;
    }
    log_t engine={0}, metrics={0};
    int pipes[2];
    if(open_log(&engine,dir,"engine.log") || open_log(&metrics,dir,"metrics.csv") || pipe2(pipes,O_CLOEXEC)) {
        perror("supervisor logs/pipe");
        if(engine.file) fclose(engine.file);
        if(metrics.file) fclose(metrics.file);
        close(sock); unlink(sockpath); return 2;
    }
    const char *header="elapsed_ms,pid,rss_kb,available_kb,swap_free_kb,pswpin_pages,pswpout_pages,minflt,majflt,utime_ticks,stime_ticks\n";
    write_log(&metrics,header,strlen(header));
    struct sigaction action={0};
    action.sa_handler=on_signal;
    sigemptyset(&action.sa_mask);
    sigaction(SIGTERM,&action,NULL); sigaction(SIGINT,&action,NULL); sigaction(SIGHUP,&action,NULL);
    signal(SIGPIPE,SIG_IGN);
    pid_t pid=fork();
    if(pid==0) {
        signal(SIGTERM,SIG_DFL); signal(SIGINT,SIG_DFL); signal(SIGHUP,SIG_DFL);
        if(setsid()<0) _exit(126);
        dup2(pipes[1],STDOUT_FILENO); dup2(pipes[1],STDERR_FILENO);
        close(pipes[0]); close(pipes[1]); close(sock);
        execvp(argv[4],argv+4);
        perror("exec"); _exit(127);
    }
    close(pipes[1]);
    if(pid<0) { perror("fork"); close(pipes[0]); close(sock); unlink(sockpath); fclose(engine.file); fclose(metrics.file); return 2; }
    fcntl(pipes[0],F_SETFL,O_NONBLOCK);
    char pidpath[1024];
    snprintf(pidpath,sizeof(pidpath),"%s/child.pid",dir);
    FILE *pf=fopen(pidpath,"w");
    if(pf) { fprintf(pf,"%d\n",pid); fclose(pf); }
    long long started=now_ms(), next_sample=started, stop_at=0, ended_at=0;
    int status=0, ended=0, eof=0, killed=0, log_failed=0, reported_signal=0;
    char crash_tail[80]={0};
    fprintf(stderr,"supervisor: child=%d clock_ticks=%ld\n",pid,sysconf(_SC_CLK_TCK));
    while(!ended || (!eof && now_ms()-ended_at<2000)) {
        struct pollfd fds[2]={{eof ? -1 : pipes[0],POLLIN|POLLHUP,0},{sock,POLLIN,0}};
        poll(fds,2,200);
        char data[4096];
        ssize_t n;
        if(fds[1].revents&POLLIN) {
            n=recv(sock,data,sizeof(data),0);
            if(n==4 && !memcmp(data,"stop",4)) interrupted=SIGTERM;
        }
        if(interrupted && !stop_at && !ended) {
            stop_at=now_ms();
            fprintf(stderr,"supervisor: requested stop\n");
            child_signal(pid,SIGCONT);
            child_signal(pid,SIGTERM);
        }
        if(stop_at && !killed && !ended && now_ms()-stop_at>=STOP_GRACE_MS) {
            fprintf(stderr,"supervisor: escalating to SIGKILL\n");
            child_signal(pid,SIGKILL);
            killed=1;
        }
        // Bound each drain pass so continuous output cannot starve stop handling.
        for(int i=0;i<32;i++) {
            n=read(pipes[0],data,sizeof(data));
            if(n>0) { reported_signal=scan_reported_signal(crash_tail,data,(size_t)n,reported_signal); if(!log_failed && write_log(&engine,data,(size_t)n)) { log_failed=1; perror("engine log"); } }
            else { if(n==0) eof=1; break; }
        }
        if(!ended && now_ms()>=next_sample) { sample(&metrics,pid,started); next_sample=now_ms()+2000; }
        if(!ended && waitpid(pid,&status,WNOHANG)==pid) { ended=1; ended_at=now_ms(); }
    }
    char result[160];
    int rc=WIFEXITED(status)?WEXITSTATUS(status):128+WTERMSIG(status);
    snprintf(result,sizeof(result),"elapsed_ms=%lld\nexit_code=%d\nsignal=%d\nengine_reported_signal=%d\nrequested_stop=%d\nforced_kill=%d\n",
        now_ms()-started,rc,WIFSIGNALED(status)?WTERMSIG(status):0,reported_signal,stop_at!=0,killed);
    FILE *rf=fopen(resultpath,"w");
    if(rf) { fputs(result,rf); fclose(rf); }
    fprintf(stderr,"supervisor: %s",result);
    if(engine.file) fclose(engine.file);
    if(metrics.file) fclose(metrics.file);
    close(pipes[0]); close(sock); unlink(sockpath); unlink(pidpath);
    return rc;
}
