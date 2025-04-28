import json
import os
import time
from datetime import datetime

POMODORO_LOG_FILE = os.path.expanduser("~/.pomodoro/pomodoro_log.json")

def monitor():
    while True:
        os.system('clear')
        if not os.path.exists(POMODORO_LOG_FILE):
            print("No Pomodoro data found.")
            time.sleep(2)
            continue

        with open(POMODORO_LOG_FILE, "r") as f:
            tasks = json.load(f)

        running_task = None
        for task in tasks:
            if task.get("state") == "running":
                running_task = task
                break

        if not running_task:
            print("No active running Pomodoro task.")
            time.sleep(2)
            continue

        total_seconds = 0
        now = datetime.now()

        for block in running_task.get("blocks", []):
            if "duration_seconds" in block:
                total_seconds += block["duration_seconds"]
            elif "start" in block and "end" not in block:
                start_time = datetime.fromisoformat(block["start"])
                total_seconds += int((now - start_time).total_seconds())

        mins, secs = divmod(total_seconds, 60)
        print(f"Task: {running_task.get('name')} [{running_task.get('phase')}] {running_task.get('key') or ''}")
        print(f"Timer: [{mins:02}:{secs:02}] Total Elapsed")

        time.sleep(1)

if __name__ == "__main__":
    monitor()
