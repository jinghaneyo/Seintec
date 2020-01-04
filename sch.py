from apscheduler.jobstores.base import JobLookupError
from apscheduler.schedulers.background import BackgroundScheduler
import time

class Scheduler:
    def __init__(self):
        self.sched = BackgroundScheduler()
        self.sched.start()
        self.job_id = ''

    def __del__(self):
        self.Shutdown()

    def Shutdown(self):
        self.sched.shutdown()

    def Kill_scheduler(self, job_id):
        try:
            self.sched.remove_job(job_id)
        except JobLookupError as err:
            print("fail to stop Scheduler: {err}".format(err=err))
            return

    def scheduler(self, type, job_id):
        print("{type} Scheduler Start".format(type=type))
        if type == 'interval':
            self.sched.add_job(self.hello, type, seconds=10, id=job_id, args=(type, job_id))
        elif type == 'cron':
            self.sched.add_job(self.hello, type, day_of_week='mon-fri',
                                                 hour='0-23', second='*/2',
                                                 id=job_id, args=(type, job_id))


#!/usr/bin/env python
#coding: utf-8
#file   : cron.py
#author : ning
#date   : 2014-01-06 17:13:23

#cron, we do the task in the main thread, so do not add task run more than 1 minutes
#you can start thread in your task

import time
import logging
from threading import Thread
from datetime import datetime

class Event(object):
    def __init__(self, desc, func, args=(), kwargs={}, use_thread=False):
        """
        desc: min hour day month dow
            day: 1 - num days
            month: 1 - 12
            dow: mon = 1, sun = 7
        """
        self.desc = desc 
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self.use_thread = use_thread

    #support: 
    # * 
    # 59
    # 10,20,30
    def _match(self, value, expr):
        #print 'match', value, expr
        if expr == '*':
            return True
        values = expr.split(',')
        for v in values:
            if int(v) == value:
                return True
        return False

    def matchtime(self, t):
        mins, hour, day, month, dow = self.desc.split()
        return self._match(t.minute       , mins)  and\
               self._match(t.hour         , hour)  and\
               self._match(t.day          , day)   and\
               self._match(t.month        , month) and\
               self._match(t.isoweekday() , dow)

    def check(self, t):
        if self.matchtime(t):
            if self.use_thread:
                thread.start_new_thread(self.func, self.args, self.kwargs)
            else:
                try:
                    self.func(*self.args, **self.kwargs)
                except Exception as e:
                    print(e)

class Cron(object):
    def __init__(self):
        self.events = []

    def add(self, desc, func, args=(), kwargs={}, use_thread=False):
        self.events.append(Event(desc, func, args, kwargs, use_thread))

    def run(self):
        last_run = 0
        while True:
            #wait to a new minute start
            t = time.time()
            next_minute = t - t%60 + 60
            while t < next_minute:
                sleeptime = 60 - t%60
                logging.debug('current time: %s, we will sleep %.2f seconds' %(t, sleeptime))
                time.sleep(sleeptime)
                t = time.time()

            if last_run and next_minute - last_run != 60:
                logging.warn('Cron Ignored: last_run: %s, this_time:%s' % (last_run, next_minute) )
            last_run = next_minute

            current = datetime(*datetime.now().timetuple()[:5])
            for e in self.events:
                e.check(current)
            time.sleep(0.001)
