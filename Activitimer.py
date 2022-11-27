# Original content by Jansen Smith, Nov 2022
# based on youtube.com/watch?v=kfjdVgKE6xY

import threading
import time
import datetime
#import pyzt
import tkinter as tk
from win10toast import ToastNotifier
from playsound import playsound


class RealtimeBudget:

    def __init__(self):
        self.log = ActivityLog()
        font_choice = ("Helvetica", 30)
        self.root = tk.Tk()
        self.root.geometry("280x160")
        self.root.title("Current Budget")

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

    def start(self):
        self.activity_button.config(text="Stop Activity")
        full_seconds = 0
        """
        hours, minutes, seconds = 0, 0, 0
        string_split = self.time_entry.get().split(":")
        if len(string_split) == 3:
            hours = string_split[0]
            minutes = string_split[1]
            seconds = string_split[2]
        elif len(string_split) == 2:
            minutes = string_split[0]
            seconds = string_split[1]
        elif len(string_split) == 1:
            seconds = string_split[0]
        else:
            print("Invalid Time Format")
            return

        hours = int(hours)
        minutes = int(minutes)
        seconds = int(seconds)

        full_seconds = hours * 60 * 60 + minutes * 60 + seconds
        """

        while True:
            full_seconds += 1

            minutes, seconds = divmod(full_seconds, 60)
            hours, minutes = divmod(minutes, 60)

            self.time_label.config(text=f"Time: {hours:02d}:{minutes:02d}:{seconds:02d}")
            self.root.update()
            time.sleep(1)

            if full_seconds > 500:
                toast = ToastNotifier()
                toast.show_toast("Realtime Budget", "Time is up!", duration=3)

#        if not self.stop_loop:

    def start_activity(self):
        #self.log.start()
        self.activity_button.config(text="Stop Activity", command=self.stop_activity)

    def stop_activity(self):
        self.activity_button.config(text="Start Activity", command=self.start_activity)


class ActivityLog:
    # Timestamp is a 2xN list, with start times in the first column and stop times in the second column
    def __init__(self):
        self.timestamps = []

    def reset(self):
        self.timestamps = []

    def start_activity(self):
        self.timestamps = self.timestamps + [(datetime.datetime.now().astimezone(),)]

    def stop_activity(self):
        self.timestamps[-1] = [self.timestamps[-1][-1], datetime.datetime.now().astimezone()]

    def total(self):
        pass

    def print(self):
        for i in range(len(log.timestamps)):
            print("Start- ", log.timestamps[i][0])
            if len(log.timestamps[i]) == 2:
                print("Stop-  ", log.timestamps[i][1])


log = ActivityLog()
log.start_activity()
time.sleep(3)
log.stop_activity()
time.sleep(2)
log.start_activity()
log.print()

#before = datetime.datetime.now().astimezone()
#time.sleep(3)
#after = datetime.datetime.now().astimezone()
#delt = after - before
#is_less = delt < datetime.timedelta(0,4)
#print("This is text", is_less)
#RealtimeBudget()
