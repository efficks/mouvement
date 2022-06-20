import pathlib
from pynput import mouse
from datetime import date, datetime, timezone
from threading import Thread, Lock
import time
import pytz
import json
import os

EST = pytz.timezone('America/Montreal')

DATA_LOCK = Lock()
firstmove = datetime.now(timezone.utc)
lastmove = datetime.now(timezone.utc)

def loadSaved():
    global lastmove, firstmove
    if os.path.exists("saved.json"):
        with open("saved.json", "r", encoding="utf=8") as fh:
            with DATA_LOCK:
                data = json.load(fh)
                firstmove = datetime.fromtimestamp(data["firstmove"], tz=timezone.utc)
                lastmove = datetime.fromtimestamp(data["lastmove"], tz=timezone.utc)

class SaveThread(Thread):
    def __init__(self):
        super().__init__()

    def run(self) -> None:
        while True:
            with open("saved.json", "w", encoding="utf=8") as fh:
                with DATA_LOCK:
                    json.dump({
                        "firstmove":firstmove.timestamp(),
                        "lastmove":lastmove.timestamp()
                    },fh)
            time.sleep(60)

def save():
    if not os.path.exists('report.csv'):
        fh = open("report.csv", "w")
        fh.close()
    mtime = pathlib.Path('report.csv').stat().st_mtime
    mtime = datetime.fromtimestamp(mtime, tz=timezone.utc)
    with DATA_LOCK:
        if lastmove.astimezone(EST).date() != mtime.date():
            with open("report.csv", "a") as fh:
                fh.write(f"{firstmove.astimezone(EST).isoformat()}, {lastmove.astimezone(EST).isoformat()}\n")

class DailySaveThread(Thread):
    def __init__(self):
        super().__init__()

    def run(self) -> None:
        while True:
            save()
            time.sleep(60)

def on_move(x,y):
    global lastmove, firstmove
    with DATA_LOCK:
        lastmove = datetime.now(timezone.utc)
        if firstmove.astimezone(EST).date() != lastmove.astimezone(EST).date():
            firstmove = lastmove

def main():
    loadSaved()
    save()
    st = SaveThread()
    st.start()

    dst = DailySaveThread()
    dst.start()

    with mouse.Listener(on_move=on_move) as listener:
        listener.join()

    dst.join()
    st.join()

if __name__ == '__main__':
    main()