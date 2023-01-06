# Original content by Jansen Smith, Nov 2022
# based on youtube.com/watch?v=kfjdVgKE6xY

import threading
import time
# import numpy as np
import datetime
# import pyzt
import tkinter as tk
from win10toast import ToastNotifier
# from playsound import playsound
import json
from os.path import exists


class Activitimer:

    def __init__(self):
        self.act1 = ActivityLog()
        font_choice = ("Helvetica", 30)
        self.root = tk.Tk()
        self.root.geometry("335x160")
        self.root.title("Activitimer")

        #        self.time_entry = tk.Entry(self.root, font=font_choice)
        #        self.time_entry.grid(row=0, column=0, columnspan=2, padx=5, pady=5)

        self.time_label = tk.Label(self.root, font=font_choice, text="Time: 00:00:00")
        self.time_label.grid(row=0, column=0, columnspan=2, padx=5, pady=5)

        self.activity_button = tk.Button(self.root, font=font_choice,
                                         text="Start Activity", command=self.start_activity)
        self.activity_button.grid(row=1, column=0, columnspan=2, padx=5, pady=5)

        self.activity = False

        self.start_thread()
        self.root.mainloop()

    def start_thread(self):
        print("Clock Starting")
        t = threading.Thread(target=self.start)
        t.start()

    def alarm(self):
        toast = ToastNotifier()
        toast.show_toast("Activitimer", "Time is up!", duration=3)

    def start(self):
        while True:
            full_seconds_true = self.act1.time_avail()

            if full_seconds_true < 0:
                full_seconds = -full_seconds_true
                self.time_label.config(fg="red")
            else:
                full_seconds = full_seconds_true
                self.time_label.config(fg="black")

            minutes, seconds = divmod(full_seconds, 60)
            hours, minutes = divmod(minutes, 60)

            self.time_label.config(text=f"Time: {int(hours):02d}:{int(minutes):02d}:{seconds:05.2f}")
            self.set_button()
            self.root.update()
            time.sleep(0.01)

            if full_seconds_true < 0 and self.activity:
                alarm = threading.Thread(target=self.alarm())
                alarm.start()

    #        if not self.stop_loop:

    def set_button(self):
        act1_latest_state = self.act1.latest_state()
        if act1_latest_state == 'activity1_start':
            self.activity_true()
        elif act1_latest_state == 'activity1_stop' or act1_latest_state == 'reset_time':
            self.activity_false()
        pass

    def activity_true(self):
        self.activity = True
        self.activity_button.config(text="Stop Activity", command=self.stop_activity)

    def activity_false(self):
        self.activity = False
        self.activity_button.config(text="Start Activity", command=self.start_activity)

    def start_activity(self):
        self.act1.activity1_start()

    def stop_activity(self):
        self.act1.activity1_stop()


class ActivityLog:
    # Timestamp is a 2xN list, with start times in the first column and stop times in the second column
    def __init__(self):
        self.hrs_per_day = 1.5
        self.log = []
        loaded = self.try_to_load_file('eventlog.json')
        if not loaded:
            self.reset()
            inject_hrs = 1
            inject_secs = inject_hrs * 3600
            self.log[0].timestamp = self.log[0].timestamp - inject_secs * 16
            self.save_file()

    def activity1_start(self):
        # Append a new event line marked "activity1_start"
        self.append_entry("activity1_start")

    def activity1_stop(self):
        # Append a new event line marked "activity1_stop"
        self.append_entry("activity1_stop")

    def reset(self):
        # Append a new event line marked "reset_time"
        self.append_entry("reset_time")

    def append_entry(self, pass_str):
        self.log.append(LogEntry(pass_str, time.time()))
        self.save_file()

    def time_avail(self):
        time_gathered = self.time_gathered()
        time_spent = self.time_spent()
        time_avail = time_gathered - time_spent
        return time_avail

    def time_gathered(self):
        return (time.time() - self.last_reset()) * (self.hrs_per_day / 24)

    def time_spent(self):
        time_spent = 0
        culled, is_started = self.culled_legacy(self.last_reset())
        for x in culled:
            if x.event == "activity1_stop":
                time_spent += x.timestamp
            elif x.event == "activity1_start":
                time_spent -= x.timestamp
            else:
                raise Exception("The log should only have start and stop activities here. "
                                "Something has gone terribly wrong.")
        if is_started:
            time_spent += time.time()-self.log[-1].timestamp
        return time_spent

    def culled_legacy(self, timestamp):
        # returns the log, with all entries BEFORE a given timestamp removed
        # does not itself modify the existing log
        culled = []
        is_started = False
        for x in self.log:
            if x.timestamp > timestamp:
                culled.append(x)
        if bool(culled) and culled[-1].event == "activity1_start":
            is_started = True
            culled = culled[0:-1]
        return culled, is_started

    def last_reset(self):
        last_timestamp = 0
        for x in self.log:
            if x.event == "reset_time" and x.timestamp > last_timestamp:
                last_timestamp = x.timestamp
        return last_timestamp

    def sort(self):
        #untested
        self.log = sorted(self.log, key=lambda x: x.timestamp, reverse=False)

    def latest_state(self):
        return self.log[-1].event

    def print(self):
        print(self.toJSON())

    def toJSON(self):
        toJSON = {
            "eventlog": []
        }
        for x in self.log:
            toJSON["eventlog"].append({"event": x.event, "timestamp": x.timestamp})
        return json.dumps(toJSON, sort_keys=True, indent=None)

    def fromJSON(self, json_data):
        for entry in json_data['eventlog']:
            self.log.append(LogEntry(entry['event'], entry['timestamp']))

    def save_file(self):
        saved = False
        with open('eventlog.json', 'w', encoding='utf-8') as f:
            #json.dump(self.toJSON(), f, ensure_ascii=False, indent=4)
            f.write(self.toJSON())
        saved = True
        return saved

    def load_file(self, filename):
        with open(filename, 'r', encoding='utf-8') as f:
            json_data = json.load(f)
        return json_data

    def try_to_load_file(self, filename):
        loaded = False
        json_data = []
        if exists(filename):
            json_data = self.load_file(filename)
            self.fromJSON(json_data)
            loaded = True
        return loaded




class LogEntry:
    # Represents a single timestamped event in the log

    def __init__(self, event_name, timestamp_epoch):
        self.event = event_name
        self.timestamp = timestamp_epoch

    def __repr__(self):
        return '{' + self.event + ' @ ' + str(self.timestamp) + '}'


"""    def reset(self):
        self.time_avail = 0
        self.last_time_reset = time.time()"""

#    self.time_avail
#    self.time_earned = (now - last time reset) * budget/24
#    self.time_spent =

if __name__ == '__main__':
    #act = ActivityLog()

    """log.timestamps = {
      "timestamps": [
        {"event": "reset_time", "timestamp": 1669591502.1348062},
        {"event": "activity1_start", "timestamp": 1669591585.721765},
        {"event": "activity1_stop", "timestamp": 1669591605.3921225},
        {"event": "reset_time", "timestamp": 1669591619.0003414},
        {"event": "activity1_start", "timestamp": 1669591665.3338575},
        {"event": "activity1_stop", "timestamp": 1669591707.532953}
      ]
    }"""

    #act = ActivityLog()
    """act.log = [
        LogEntry('reset_time', 1669591502.1348062),
        LogEntry('activity1_start', 1669591585.721765),
        LogEntry('activity1_stop', 1669591605.3921225),
        LogEntry('reset_time', 1669591619.0003414),
        LogEntry('activity1_start', 1669591665.3338575),
        LogEntry('activity1_stop', 1669591707.532953),
    ]
    act.save_file()"""
    #act.print()

    #log_sorted = sorted(act.log, key=lambda x: x.event)
        #sorted(employees, key=lambda x: x.name)

    # log.start_activity()
    # time.sleep(3)
    # log.stop_activity()
    # time.sleep(2)
    # log.start_activity()
    # time.sleep(2)
    # log.stop_activity()
    #print(log_sorted)
    # log.print()

    # before = datetime.datetime.now().astimezone()
    # time.sleep(3)
    # after = datetime.datetime.now().astimezone()
    # delt = after - before
    # is_less = delt < datetime.timedelta(0,4)
    # print("This is text", is_less)
    act = Activitimer()
