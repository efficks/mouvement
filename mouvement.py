
from concurrent.futures import Future, ThreadPoolExecutor
from datetime import date, datetime, timedelta
import os
import time
from pynput import mouse
import psutil

def locked_screen()->bool:
    for proc in psutil.process_iter():
        if(proc.name() == "LogonUI.exe"):
            return True
    return False

class Recorder:
    def __init__(self, file):
        self.__file = file
    
    def record(self):
        n = datetime.now().time().strftime('%H:%M')
        if not locked_screen():
            self.__write_info()
    
    def __write_info(self):
        with open(self.__file, "r+b") as fh:
            try:  # catch OSError in case of a one line file 
                fh.seek(-2, os.SEEK_END)
                while fh.read(1) != b'\n':
                    fh.seek(-2, os.SEEK_CUR)
                position = fh.tell()-2
                last_line = fh.read()
            except OSError as e:
                fh.seek(0)
                last_line = None
                position = fh.tell()
        
            new_line = True
            begin = datetime.now().time()
            end = datetime.now().time()
            if last_line is not None:
                last_line = last_line.decode(encoding="utf-8")
                if last_line is not None and ',' in last_line:
                    splitted = last_line.split(',')
                    try:
                        dt = datetime.strptime(splitted[0], '%Y-%m-%d').date()
                    except ValueError:
                        dt = None
                    if dt == datetime.now().date():
                        new_line = False
                        begin = datetime.strptime(splitted[1], '%H:%M').time()
            
            if not new_line:
                fh.truncate(position)
                fh.seek(position)
            else:
                fh.seek(0,os.SEEK_END)

            today = datetime.now().date()
            delta:timedelta = datetime.combine(date.min, end) - datetime.combine(date.min, begin)
            
            hours, remainder = divmod(delta.total_seconds(), 3600)
            minutes, seconds = divmod(remainder, 60)
            delta_str = "{:02}:{:02}".format(int(hours), int(minutes))
            fh.write(f"{os.linesep}{today.strftime('%Y-%m-%d')},{begin.strftime('%H:%M')},{end.strftime('%H:%M')},{delta_str}".encode("utf-8"))
        

class MouseObserver:
    def __init__(self, timeout = timedelta(seconds=60)):
        self.__callback = []
        self.__timeout = timeout.total_seconds()
        self.__lastcall = 0
        self.__listener = mouse.Listener(on_move=self.__detect)
        self.__executor = ThreadPoolExecutor(max_workers=1)
        self.__last_minute = -1
        self.__count = 10
    
    def start(self):
        self.__listener.start()
    
    def join(self):
        self.__listener.join()

    def add_callback(self, cb):
        self.__callback.append(cb)
    
    def __detect(self, x, y):
        self.__count += 1
        if self.__count >= 10:
            self.__count = 0
            current_minute = datetime.now().minute
            if self.__last_minute != current_minute:
                self.__last_minute = current_minute
                for cb in self.__callback:
                    future = self.__executor.submit(cb)
                    future.add_done_callback(self.end_cb)

    def end_cb(self, future:Future):
        exc = future.exception()
        if exc is not None:
            print(exc)
        
def main():
    recorder = Recorder("test.txt")

    mouse_observer = MouseObserver()
    mouse_observer.add_callback(recorder.record)
    mouse_observer.start()

    print("started")

    mouse_observer.join()

if __name__ == "__main__":
    main()