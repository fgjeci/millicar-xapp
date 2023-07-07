from threading import Thread, Event, Timer
from datetime import time, datetime

# global _inter_optimizer_timer
# global _optimizer_timer

class InterOptimizationTimer(Timer):

    def __init__(self, interval, optimization_timer:Timer, args=None, kwargs=None):
        Timer.__init__(self, interval, None, args=args, kwargs=kwargs)
        self.optimization_timer = optimization_timer
        self._reset = False

    def reset_timer(self):
        self._reset = True
        self.finished.set()
        self.finished.clear()
        self._reset=False

    def cancel(self):
        """Stop the timer if it hasn't finished yet."""
        self.finished.set()

    def run(self):
        print("Starting inter optimization timer ")
        # print("Running inter optimization state " + str(self.finished.is_set()))
        self.finished.wait(self.interval)
        if not self.finished.is_set() and not self._reset:
            self.finished.set()
            print("Reseting the optimization timer "   + str(datetime.now()))
            # _optimizer_timer.finished.clear()
            self.optimization_timer.finished.clear()


class OptimizerTimer(Timer):
    def __init__(self, interval, function, inter_optimizer_timer: Timer, args=None, kwargs=None):
        Timer.__init__(self, interval, function, args=args, kwargs=kwargs)
        self.inter_optimizer_timer = inter_optimizer_timer
        self._reset = False


    def cancel(self):
        """Stop the timer if it hasn't finished yet."""
        self.finished.set()

    def reset_timer(self):
        self._reset = True
        self.finished.set()
        self.finished.clear()
        self._reset=False

    def run(self):
        print("Starting optimization timer at time ")
        # print("Running optimization state " + str(self.finished.is_set()))
        self.finished.wait(self.interval)
        if not self.finished.is_set() and not self._reset:
            # print("Running the optimization function "  + str(datetime.now()))
            self.function(*self.args, **self.kwargs)
            # start the second timer
            self.finished.set()
            # if _inter_optimizer_timer is not None:
            #     _inter_optimizer_timer.finished.clear()
            #     _inter_optimizer_timer.run()
            if self.inter_optimizer_timer is not None:
                self.inter_optimizer_timer.finished.clear()
                self.inter_optimizer_timer.run()
        

        