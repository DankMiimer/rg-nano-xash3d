#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Integration tests for child ownership, stop escalation, output and metrics."""
from pathlib import Path
import os, signal, subprocess, sys, tempfile, time, unittest
ROOT=Path(__file__).resolve().parents[1]
BIN=Path(os.environ.get('NANO_SUPERVISOR_TEST_BIN', '/var/tmp/rg-nano-supervise-host'))

class Supervisor(unittest.TestCase):
    def start(self, directory, code):
        log=Path(directory)/'logs'
        sock=Path(directory)/'s'
        command=[str(BIN),str(log),str(sock),'--',sys.executable,'-u','-c',code]
        process=subprocess.Popen(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        deadline=time.monotonic()+3
        while not (log/'child.pid').exists() and process.poll() is None and time.monotonic()<deadline:
            time.sleep(.02)
        return process,log,sock

    def test_previous_result_is_removed_on_start(self):
        with tempfile.TemporaryDirectory() as d:
            log=Path(d)/'logs';log.mkdir()
            (log/'result.txt').write_text('stale crash result')
            p,log,sock=self.start(d,"import time; time.sleep(30)")
            self.assertFalse((log/'result.txt').exists())
            subprocess.run([str(BIN),'--stop',str(sock)],check=True)
            p.communicate(timeout=8)
            self.assertIn('requested_stop=1',(log/'result.txt').read_text())

    def test_fifo_without_reader_is_bounded(self):
        with tempfile.TemporaryDirectory() as d:
            fifo=Path(d)/'fifo'
            os.mkfifo(fifo)
            started=time.monotonic()
            result=subprocess.run([str(BIN),'--load-keys','/test/nano.key',str(fifo)],capture_output=True,timeout=5)
            self.assertEqual(result.returncode,3)
            self.assertLess(time.monotonic()-started,4.5)

    def test_fifo_command_is_one_complete_line(self):
        with tempfile.TemporaryDirectory() as d:
            fifo=Path(d)/'fifo'
            os.mkfifo(fifo)
            fd=os.open(fifo,os.O_RDONLY|os.O_NONBLOCK)
            try:
                result=subprocess.run([str(BIN),'--load-keys','/test/nano.key',str(fifo)],capture_output=True,timeout=5)
                self.assertEqual(result.returncode,0,result.stderr)
                self.assertEqual(os.read(fd,4096),b'LOAD /test/nano.key\n')
            finally:
                os.close(fd)

    def test_exit_status_and_output(self):
        with tempfile.TemporaryDirectory() as d:
            p,log,sock=self.start(d,"print('hello'); raise SystemExit(7)")
            _,err=p.communicate(timeout=5)
            self.assertEqual(p.returncode,7,err)
            self.assertIn('hello',(log/'engine.log').read_text())
            self.assertIn('exit_code=7',(log/'result.txt').read_text())
            self.assertIn('rss_kb',(log/'metrics.csv').read_text())
            self.assertFalse(sock.exists())

    def test_engine_handled_crash_across_output_chunks(self):
        with tempfile.TemporaryDirectory() as d:
            p,log,sock=self.start(d,"import sys,time; sys.stdout.write('Crash: sig'); sys.stdout.flush(); time.sleep(.25); print('nal 11 errno 0'); raise SystemExit(0)")
            p.communicate(timeout=5)
            self.assertEqual(p.returncode,0)
            result=(log/'result.txt').read_text()
            self.assertIn('exit_code=0',result)
            self.assertIn('engine_reported_signal=11',result)

    def test_crash_signal(self):
        with tempfile.TemporaryDirectory() as d:
            p,log,sock=self.start(d,"import os,signal; os.kill(os.getpid(),signal.SIGSEGV)")
            p.communicate(timeout=5)
            self.assertEqual(p.returncode,128+signal.SIGSEGV)
            self.assertIn('signal=11',(log/'result.txt').read_text())

    def test_stop_stopped_child_and_leave_unrelated_process(self):
        unrelated=subprocess.Popen([sys.executable,'-c','import time; time.sleep(30)'])
        try:
            with tempfile.TemporaryDirectory() as d:
                p,log,sock=self.start(d,"import time; print('ready'); time.sleep(30)")
                deadline=time.monotonic()+3
                while 'ready' not in (log/'engine.log').read_text() and time.monotonic()<deadline:
                    time.sleep(.02)
                child=int((log/'child.pid').read_text())
                os.kill(child,signal.SIGSTOP)
                subprocess.run([str(BIN),'--stop',str(sock)],check=True)
                p.communicate(timeout=8)
                self.assertEqual(p.returncode,128+signal.SIGTERM)
                self.assertIsNone(unrelated.poll())
                self.assertIn('requested_stop=1',(log/'result.txt').read_text())
        finally:
            unrelated.terminate()
            unrelated.wait(timeout=3)

    def test_stubborn_child_escalates(self):
        with tempfile.TemporaryDirectory() as d:
            p,log,sock=self.start(d,"import signal,time; signal.signal(signal.SIGTERM,signal.SIG_IGN); print('ready'); time.sleep(30)")
            deadline=time.monotonic()+3
            while 'ready' not in (log/'engine.log').read_text() and time.monotonic()<deadline:
                time.sleep(.02)
            subprocess.run([str(BIN),'--stop',str(sock)],check=True)
            p.communicate(timeout=9)
            self.assertEqual(p.returncode,128+signal.SIGKILL)
            self.assertIn('forced_kill=1',(log/'result.txt').read_text())

    def test_socket_ownership(self):
        with tempfile.TemporaryDirectory() as d:
            p,log,sock=self.start(d,"import time; time.sleep(30)")
            second=subprocess.run([str(BIN),str(Path(d)/'other'),str(sock),'--','/bin/true'],capture_output=True)
            self.assertEqual(second.returncode,2)
            self.assertTrue(sock.exists())
            subprocess.run([str(BIN),'--stop',str(sock)],check=True)
            p.communicate(timeout=8)

    def test_bounded_output(self):
        with tempfile.TemporaryDirectory() as d:
            p,log,sock=self.start(d,"import sys; sys.stdout.write('a'*2000000)")
            p.communicate(timeout=10)
            self.assertEqual(p.returncode,0)
            for file in log.glob('engine.log*'):
                self.assertLessEqual(file.stat().st_size,512*1024)

if __name__=='__main__':
    unittest.main()
