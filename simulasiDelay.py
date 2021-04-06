import threading
import time
import random
import queue

interval = 5
stopAll = False
q = queue.Queue()

lock = threading.Lock()

timestamp = time.time()
is_not_sending = False
def sendAlert(thread):
    global timestamp, is_not_sending

    while not stopAll:
        i, q.get()

        sec = int(time.time() - timestamp)
        if sec >= interval and is_not_sending:
            with lock:
                timestamp = time.time()
            print ("\n--- [thread-%s] processed [seconds=%s, interval=%s, is_not_sending=%s]" % (thread,
                sec, interval, is_not_sending
            ))
            time.sleep(random.randrange(5))
        else:
            print("[thread-%s] waiting [seconds=%s] [%s]" % (thread, sec, i), end="\r")
            with lock:
                is_not_sending = not is_not_sending
            time.sleep(random.random())
        q.task_done()

for i in range(1):
    th = threading.Thread(target=sendAlert, args=(i, ))
    th.setDaemon(True)
    th.start()

for i in range(100000000000):
    q.put(i)
q.join()
