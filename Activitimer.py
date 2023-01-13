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
    """
    Main timer application class.

    This class represents the main timer application, which includes a graphical
    user interface (GUI) that allows the user to start and stop a timer for an
    activity, and displays the elapsed time for the activity in the GUI. The
    application also includes a notification feature that sends a notification
    when the elapsed time exceeds a certain threshold.

    Attributes:
        act1 (ActivityLog): An instance of the ActivityLog class to track
            start and stop times for activities.
        activity (bool): A flag to indicate whether the timer is currently
            running or not.
        activity_button (tk.Button): A button widget to start and stop the
            timer.
        root (tk.Tk): The main window of the application.
        time_label (tk.Label): A label widget to display the elapsed time
            for the activity.
    """

    def __init__(self):
        """
        Initialize attributes and create GUI.
        """

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
        """
        Start a new thread to run the start() method.
        """

        print("Clock Starting")
        t = threading.Thread(target=self.start)
        t.start()

    def alarm(self):
        """
        Send a notification using the toast object when the elapsed time
        for an activity exceeds a certain threshold.
        """

        toast = ToastNotifier()
        toast.show_toast("Activitimer", "Time is up!", duration=3)

    def start(self):
        """
        Run the timer in a separate thread.

        This method updates the time_label widget to display the elapsed time
        for the activity, calls the set_button() method to update the
        activity_button widget based on the current status of the timer, and
        pauses for a short period of time before repeating.
        """

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
        """
        Update the activity_button widget based on the current status of the timer.
        """

        act1_latest_state = self.act1.latest_state()
        if act1_latest_state == 'activity1_start':
            self.activity_true()
        elif act1_latest_state == 'activity1_stop' or act1_latest_state == 'reset_time':
            self.activity_false()
        pass

    def activity_true(self):
        """
        Set the activity flag to True and update the activity_button widget to
        show "Stop Activity" and run the stop_activity() method when clicked.
        """

        self.activity = True
        self.activity_button.config(text="Stop Activity", command=self.stop_activity)

    def activity_false(self):
        """
        Set the activity flag to False and update the activity_button widget to
        show "Start Activity" and run the start_activity() method when clicked.
        """

        self.activity = False
        self.activity_button.config(text="Start Activity", command=self.start_activity)

    def start_activity(self):
        """
        Start a new activity by calling the activity1_start() method of the act1 object.
        """

        self.act1.activity1_start()

    def stop_activity(self):
        """
        Stop the current activity by calling the activity1_stop() method of the act1 object.
        """

        self.act1.activity1_stop()


class ActivityLog:
    """
    Activity log class.

    This class represents a log of activities, and keeps track of the start and stop
    times for each activity. It provides methods to start and stop the timer, and
    calculate the elapsed time for all activities.

    Attributes:
        hrs_per_day (float): The number of hours per day available for activities.
        log (list): A list of start and stop times for activities.
    """

    def __init__(self):
        """
        Initialize the activity log and try to load the log from the 'eventlog.json' file.
        If the file is not found or there is an error loading it, reset the timer.
        """

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
        """
        Start a new activity by adding a new entry to the log list with the current
        time as the start time.
        Append a new event line marked "activity1_start"
        """

        self.append_entry("activity1_start")

    def activity1_stop(self):
        """
        Stop the current activity by adding the current time as the stop time to
        the latest entry in the log list.
        Append a new event line marked "activity1_stop"
        """
        self.append_entry("activity1_stop")

    def reset(self):
        """
        Reset the activity log and set the hrs_per_day attribute to 1.5.
        """

        # Append a new event line marked "reset_time"
        self.append_entry("reset_time")

    def append_entry(self, pass_str):
        self.log.append(LogEntry(pass_str, time.time()))
        self.save_file()

    def time_avail(self):
        """
        Calculate the elapsed time for all activities in the log list and return the
        remaining time based on the hrs_per_day attribute.

        This method iterates through the log list and adds up the elapsed time for
        each activity. It then subtracts the total elapsed time from the hrs_per_day
        attribute to get the remaining time.
        """

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
        """
        Return the current state of the timer based on the latest entry in the log list.

        If the latest entry has a start time but no stop time, return 'activity1_start'.
        If the latest entry has both a start and stop time, return 'activity1_stop'.
        If the log list is empty, return 'reset_time'.
        """

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
        """
        Try to load the activity log from the specified file.

        If the file is found and successfully loaded, return True. If the file
        is not found or there is an error loading it, return False.

        Args:
            filename (str): The name of the file to load the log from.

        Returns:
            bool: True if the file was found and successfully loaded, False otherwise.
        """

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

if __name__ == '__main__':

    act = Activitimer()
