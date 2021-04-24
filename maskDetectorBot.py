import logging
logging.basicConfig(
    format="%(threadName)s: --- %(message)s", level=logging.INFO)

logging.info("Mengimport module")

# TODO: implementasi audio

import simpleaudio as sa
import time
import io
import queue
import threading
import telebot
import cv2
import signal
import sys

logging.info("Inisiasi Bot telegram")
bot = telebot.TeleBot(
    "1752888275:AAGoy1NhTK0K6OfXHwK0jIYqe9VP246kGkc"
)
SUPERUSER = 626351605  # ganti pakai id telegrammu

q = queue.Queue()
stopAll = False

# interval = delay
interval = 2
timestamp = time.time()
lock = threading.Lock()

wave_obj = sa.WaveObject.from_wave_file("sound/voice.wav")

def sendAlert():
    """
    # penjabaran sederhana with lock
    # lock = threading.Lock()

    # tahan thread agar tidak terjadi konflik antar thread  saat mengganti
    # global variabel
    lock.aquire()

    try:
        # lakukan process disini
    finally:

        # release / jalankan lagi thread
        lock.release()
    """

    global timestamp
    logging.info("sendAlert dijalankan")

    total_dilewati = 0
    while not stopAll:
        frame = q.get()

        sec = int(time.time() - timestamp)
        if sec > interval:
            with lock:
                # reset timestamp
                timestamp = time.time()
                total_dilewati = 0

            success, jpgFrame = cv2.imencode(".jpg", frame)
            if success:
                play_obj = wave_obj.play()
                play_obj.wait_done()
                logging.info(f"melewati {total_dilewati} frame")
                logging.info(f"Mengirim foto ke {SUPERUSER}")
                ioBuffer = io.BytesIO(jpgFrame)
                ioBuffer.seek(0)  # penting !!
                bot.send_photo(SUPERUSER, ioBuffer,
                               caption="Terdeteksi tidak menggunakan masker")
        else:
            total_dilewati += 1
        q.task_done()


@bot.message_handler(commands=['start'])
def action_start(message):
    nama = message.from_user.first_name
    lastname = message.from_user.last_name
    bot.reply_to(message, "Hello apa kabar {} {}".format(nama, lastname))


@bot.message_handler(commands=['help'])
def send_welcome(message):
    bot.reply_to(message, "perlu apa gaes?")


@bot.message_handler(commands=["stop"], func=lambda x: x.from_user.id == SUPERUSER)
def sendSignal(message):
    global stopAll
    bot.reply_to(message, "Video Capture dihentikan")
    stopAll = True


def remove_item_queue():
    while not q.empty():
        try:
            q.get(timeout=1)
        except Exception:
            pass


def signal_handler(signal, frame):
    global stopAll
    stopAll = True
    cv2.release()
    cv2.destroyAllWindows()
    remove_item_queue()

    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)

th = threading.Thread(target=sendAlert)
th.setDaemon(True)
th.start()

logging.info("Bot Berjalan dilatar belakang")
th = threading.Thread(target=bot.polling)
th.setDaemon(True)
th.start()

logging.info("Inisisasi CascadeClasifier")
face = cv2.CascadeClassifier(
    cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
smile = cv2.CascadeClassifier(
    cv2.data.haarcascades + 'haarcascade_smile.xml')

logging.info("Memulai kamera")
cap = cv2.VideoCapture(0)

frame_start_time = time.time()
frame_counter = 0

while not stopAll:
    ret, frame = cap.read()
    frame = cv2.flip(frame, 1)
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2BGRA)
    faces = face.detectMultiScale(gray, 1.1, 5, 0, (140, 140), (250, 250))

    mask = True
    for x, y, w, h in faces:
        smiles = smile.detectMultiScale(
            gray[y:y + h, x:x + w], 1.4, 5, 0, (75, 75), (90, 90))
        pesan = 'Dengan Masker'
        color = (0, 255, 0)

        for ex, ey, ew, eh in smiles:
            logging.debug("Terdeteksi tanpa masker")
            pesan = 'Tanpa Masker'
            color = (0, 0, 255)
            mask = False
            break

        # aku ubah gray jadi frame soalnya yg dikirim gambar abu2
        cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
        cv2.putText(frame, pesan, (x, y - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 2)
    if mask is False:
        q.put(frame)

    cv2.imshow("frame", frame)
    if cv2.waitKey(1) and 0xFF == ord("q"):
        break

    # tambah 1 setiap frame yang berhasil diambil
    frame_counter += 1

    # hitung durasi
    elapsed_time = time.time() - frame_start_time
    if (elapsed_time) > 1:
         # rumus: jumlah frame dibagi durasi
         fps = str(int(frame_counter / elapsed_time))

         # harusnya dapet fps lebih dari 50, soalnya frame diproses dilatar belakang
         logging.info("FPS:", fps)
         # kalau mau ditampilin di layar, gunain cv2.putText kayak yg diatas

         # reset
         frame_counter = 0
         frame_start_time = time.time()

cv2.release()
cv2.destroyAllWindows()
remove_item_queue()
