import threading
import time
import random
import queue

interval = 10
stopAll = False
q = queue.Queue()

lock = threading.Lock()

timestamp = time.time()
is_not_sending = False


def sendAlert(thread):
    global timestamp, is_not_sending

    skipped = 0
    while not stopAll:
        i = q.get()

        sec = int(time.time() - timestamp)
        if sec > interval:
            with lock:
                print("\n--- [thread-%s] processed [seconds=%s, interval=%s, skipped=%s]" % (thread,
                                                                                             sec, interval, skipped
                                                                                             ))
                timestamp = time.time()
                time.sleep(5)
            skipped = 0
        else:
            print("[thread-%s] waiting [seconds=%s] [%s]" %
                  (thread, sec, q.qsize()), end="\r")
            time.sleep(random.random())
            skipped += 1
        q.task_done()


th = threading.Thread(target=sendAlert, args=("1", ))
# th.setDaemon(True)
th.start()

for i in range(100000000000):
    if not lock.locked():
        q.put(i)
        time.sleep(0.3)
    print(f"{q.qsize()=}")
q.join()
