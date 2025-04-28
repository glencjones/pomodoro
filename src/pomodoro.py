import json
import os
import time
import uuid
import logging
from datetime import datetime, timedelta
from tabulate import tabulate

DATA_DIR = os.path.expanduser("~/.pomodoro")
LOG_FILE = os.path.join(DATA_DIR, "pomodoro_log.json")
EVENT_LOG_FILE = os.path.join(DATA_DIR, "pomodoro_events.json")
TIMER_STATE_FILE = os.path.join(DATA_DIR, "timer_state.json")

logger = logging.getLogger("pomodoro")
handler = logging.StreamHandler()
formatter = logging.Formatter("[%(levelname)s] %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

class Task:
    def __init__(self, name, phase="General", key=None):
        self.id = str(uuid.uuid4())
        self.name = name
        self.phase = phase
        self.key = key
        self.state = "paused"
        self.start_time = None
        self.blocks = []

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "phase": self.phase,
            "key": self.key,
            "state": self.state,
            "start_time": self.start_time,
            "blocks": self.blocks
        }

    @staticmethod
    def from_dict(data):
        task = Task(data["name"], data["phase"], data.get("key"))
        task.id = data["id"]
        task.state = data["state"]
        task.start_time = data["start_time"]
        task.blocks = data.get("blocks", [])
        return task

    def accumulated_time(self):
        total = 0
        now = datetime.now()
        for block in self.blocks:
            if "duration_seconds" in block:
                total += block["duration_seconds"]
            elif "start" in block and "end" not in block:
                start_time = datetime.fromisoformat(block["start"])
                total += int((now - start_time).total_seconds())
        return total

class PomodoroManager:
    def __init__(self, debug=False):
        os.makedirs(DATA_DIR, exist_ok=True)
        self.tasks = self.load_tasks()
        if debug:
            logger.setLevel(logging.DEBUG)

    def load_tasks(self):
        if not os.path.exists(LOG_FILE):
            return []
        with open(LOG_FILE, "r") as f:
            data = json.load(f)
            return [Task.from_dict(d) for d in data]

    def save_tasks(self):
        with open(LOG_FILE, "w") as f:
            json.dump([task.to_dict() for task in self.tasks], f, indent=2)

    def log_event(self, task, action):
        event = {
            "timestamp": datetime.now().isoformat(),
            "task_id": task.id,
            "key": task.key,
            "action": action
        }
        events = []
        if os.path.exists(EVENT_LOG_FILE):
            with open(EVENT_LOG_FILE, "r") as f:
                events = json.load(f)
        events.append(event)
        with open(EVENT_LOG_FILE, "w") as f:
            json.dump(events, f, indent=2)
        logger.debug(f"Logged event: {event}")

    def pause_running_tasks(self):
        for task in self.tasks:
            if task.state == "running":
                self.pause_task(task.id)

    def start_task(self, name, phase="General", key=None, duration=25, monitor=False):
        self.pause_running_tasks()
        task = Task(name, phase, key)
        task.state = "running"
        task.start_time = datetime.now().isoformat()
        task.blocks.append({"start": task.start_time})
        self.tasks.append(task)
        self.save_tasks()
        self.log_event(task, "start")
        print(f"Started task: {task.name} [{task.phase}] {task.key or ''}")
        if monitor:
            self.run_timer(task, duration)

    def run_timer(self, task, duration_minutes):
        seconds = duration_minutes * 60
        start_time = time.time()
        while True:
            elapsed = int(time.time() - start_time)
            mins, secs = divmod(elapsed, 60)
            with open(TIMER_STATE_FILE, "w") as f:
                json.dump({
                    "task": task.name,
                    "key": task.key,
                    "phase": task.phase,
                    "start_time": task.start_time,
                    "duration_minutes": duration_minutes,
                    "elapsed_seconds": elapsed
                }, f)
            print(f"[{mins:02}:{secs:02}] Working...", end="\r", flush=True)
            time.sleep(1)
            if elapsed >= seconds:
                print("\n\a🔔 Pomodoro Complete! Take a break! 🔔\n")
                if os.path.exists(TIMER_STATE_FILE):
                    os.remove(TIMER_STATE_FILE)
                break

    def pause_task(self, task_id):
        for task in self.tasks:
            if task.id == task_id and task.state == "running":
                now = datetime.now()
                task.state = "paused"
                if task.blocks and "start" in task.blocks[-1] and "end" not in task.blocks[-1]:
                    start = datetime.fromisoformat(task.blocks[-1]["start"])
                    task.blocks[-1]["end"] = now.isoformat()
                    task.blocks[-1]["duration_seconds"] = int((now - start).total_seconds())
                task.start_time = None
                self.save_tasks()
                self.log_event(task, "pause")
                if os.path.exists(TIMER_STATE_FILE):
                    os.remove(TIMER_STATE_FILE)
                print(f"Paused task: {task.name}")
                return

    def pause_task_by_key(self, key):
        for task in self.tasks:
            if task.key == key and task.state == "running":
                self.pause_task(task.id)
                return
        print(f"No running task with key {key} found to pause.")

    def resume_task_by_key(self, key, duration=25, monitor=False):
        self.pause_running_tasks()
        for task in self.tasks:
            if task.key == key and task.state == "paused":
                task.state = "running"
                task.start_time = datetime.now().isoformat()
                task.blocks.append({"start": task.start_time})
                self.save_tasks()
                self.log_event(task, "resume")
                print(f"Resumed task: {task.name} [{task.phase}] {task.key}")
                if monitor:
                    self.run_timer(task, duration)
                return
        print(f"No paused task with key {key} found to resume.")

    def finish_task_by_key(self, key):
        for task in self.tasks:
            if task.key == key:
                if task.state == "running":
                    self.pause_task(task.id)
                task.state = "finished"
                task.start_time = None
                self.save_tasks()
                self.log_event(task, "finish")
                print(f"Finished task: {task.name} [{task.phase}] {task.key}")
                return
        print(f"No task found with key {key}.")

    def delete_task_by_key(self, key):
        new_tasks = [task for task in self.tasks if task.key != key]
        if len(new_tasks) == len(self.tasks):
            print(f"No task found with key {key} to delete.")
            return
        self.tasks = new_tasks
        self.save_tasks()
        print(f"Deleted task with key {key}.")

    def list_tasks(self):
        print("\nCurrent Tasks:")

        table = []
        default_limit_minutes = 25
        now = datetime.now()

        for task in self.tasks:
            total_elapsed_seconds = task.accumulated_time()
            elapsed_minutes = int(total_elapsed_seconds // 60)
            limit_minutes = default_limit_minutes
            remaining_minutes = max(limit_minutes - elapsed_minutes, 0)

            table.append([
                task.key or 'N/A',
                task.name,
                task.phase,
                task.state.upper(),
                f"{elapsed_minutes} min",
                f"{remaining_minutes} min",
                f"{limit_minutes} min"
            ])

        headers = ["Key", "Task", "Phase", "State", "Elapsed", "Remaining", "Limit"]
        print(tabulate(table, headers=headers, tablefmt="simple"))

    def switch_task(self, key, duration=25, monitor=False):
        self.pause_running_tasks()
        for task in self.tasks:
            if task.key == key:
                task.state = "running"
                task.start_time = datetime.now().isoformat()
                task.blocks.append({"start": task.start_time})
                self.save_tasks()
                self.log_event(task, "switch")
                print(f"Switched to task: {task.name}")
                if monitor:
                    self.run_timer(task, duration)
                return
        print(f"Task with key {key} not found.")

    def report(self, period="week", fmt="simple"):
        now = datetime.now()
        if period == "week":
            start_period = now - timedelta(days=7)
        elif period == "month":
            start_period = now - timedelta(days=30)
        else:
            print("Unsupported period.")
            return

        table = []
        for task in self.tasks:
            total_time = task.accumulated_time()
            if total_time > 0:
                hours, remainder = divmod(int(total_time), 3600)
                minutes = remainder // 60
                table.append([task.key or 'N/A', task.name, task.phase, f"{hours}h {minutes}m", task.state])
        headers = ["Key", "Task", "Phase", "Time Worked", "State"]
        print(tabulate(table, headers=headers, tablefmt=fmt))

    def report_events(self, fmt="simple"):
        if not os.path.exists(EVENT_LOG_FILE):
            print("No events logged yet.")
            return
        with open(EVENT_LOG_FILE, "r") as f:
            events = json.load(f)
        table = []
        for event in events:
            table.append([event['timestamp'], event['action'], event['key'] or 'N/A'])
        headers = ["Timestamp", "Action", "Key"]
        print(tabulate(table, headers=headers, tablefmt=fmt))

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Pomodoro CLI Tool")
    subparsers = parser.add_subparsers(dest="command")

    start_parser = subparsers.add_parser("start")
    start_parser.add_argument("--task", required=True)
    start_parser.add_argument("--phase", default="General")
    start_parser.add_argument("--key", default=None)
    start_parser.add_argument("--duration", type=int, default=25)
    start_parser.add_argument("--monitor", action="store_true")
    start_parser.add_argument("--debug", action="store_true")

    list_parser = subparsers.add_parser("list")

    switch_parser = subparsers.add_parser("switch")
    switch_parser.add_argument("--key", required=True)
    switch_parser.add_argument("--duration", type=int, default=25)
    switch_parser.add_argument("--monitor", action="store_true")

    pause_parser = subparsers.add_parser("pause")
    pause_parser.add_argument("--key", required=True)

    resume_parser = subparsers.add_parser("resume")
    resume_parser.add_argument("--key", required=True)
    resume_parser.add_argument("--duration", type=int, default=25)
    resume_parser.add_argument("--monitor", action="store_true")

    finish_parser = subparsers.add_parser("finish")
    finish_parser.add_argument("--key", required=True)

    delete_parser = subparsers.add_parser("delete")
    delete_parser.add_argument("--key", required=True)

    report_parser = subparsers.add_parser("report")
    report_parser.add_argument("--period", default="week")
    report_parser.add_argument("--format", default="simple")

    report_events_parser = subparsers.add_parser("report-events")
    report_events_parser.add_argument("--format", default="simple")

    args = parser.parse_args()
    manager = PomodoroManager(debug=getattr(args, 'debug', False))

    if args.command == "start":
        manager.start_task(args.task, args.phase, args.key, args.duration, monitor=args.monitor)
    elif args.command == "list":
        manager.list_tasks()
    elif args.command == "switch":
        manager.switch_task(args.key, args.duration, monitor=args.monitor)
    elif args.command == "pause":
        manager.pause_task_by_key(args.key)
    elif args.command == "resume":
        manager.resume_task_by_key(args.key, args.duration, monitor=args.monitor)
    elif args.command == "finish":
        manager.finish_task_by_key(args.key)
    elif args.command == "delete":
        manager.delete_task_by_key(args.key)
    elif args.command == "report":
        manager.report(args.period, args.format)
    elif args.command == "report-events":
        manager.report_events(args.format)
    else:
        parser.print_help()

