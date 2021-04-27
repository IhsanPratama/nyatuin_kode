import logging
logging.basicConfig(
    format="%(threadName)s: --- %(message)s", level=logging.INFO)

logging.info("Mengimport module")

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

# semua frame akan disimpan disini
frame_tanpa_masker = queue.Queue()
raw_frame = queue.Queue()

jumlahThreadDetectMask = 3

stopAll = False

frame_start_time = time.time()
frame_counter = 0
FPS = 0

fontFace = cv2.FONT_HERSHEY_SIMPLEX

# posisi text / koordinat
coordinate = (10, 30)

# Skala font / ukuran font
# rumus: ukuran font asli dikali n
fontScale = 1

# warna font: putih
fontColor = (255, 255, 255)

# tipe line
lineType = 2

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
        frame = frame_tanpa_masker.get()

        sec = int(time.time() - timestamp)
        if sec > interval:
            with lock:
                timestamp = time.time()

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
                    total_dilewati = 0
        else:
            total_dilewati += 1
        frame_tanpa_masker.task_done()


logging.info("Inisisasi HaarCascadeClasifier")
face = cv2.CascadeClassifier(
    cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
smile = cv2.CascadeClassifier(
    cv2.data.haarcascades + 'haarcascade_smile.xml')

def detectMask():
    while not stopAll:
        frame = raw_frame.get()
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

            cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
            cv2.putText(frame, pesan, (x, y - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 2)

        # lewati frame jika thread dalam kondisi lock tidak peduli mask
        # bernilai False
        if mask is False and not lock.locked():
            frame_tanpa_masker.put(frame)
        raw_frame.task_done()


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


def cleanup(*args):
    global stopAll

    stopAll = True
    cv2.release()
    cv2.destroyAllWindows()

    sys.exit(0)


signal.signal(signal.SIGINT, cleanup)

# Thread Process
th = threading.Thread(target=sendAlert)
th.setDaemon(True)
th.start()

for _ in range(jumlahThreadDetectMask):
    th = threading.Thread(target=detectMask)
    th.setDaemon(True)
    th.start()

logging.info("Bot Berjalan dilatar belakang")
th = threading.Thread(target=bot.polling)
th.setDaemon(True)
th.start()

# =======

logging.info("Memulai kamera")
cap = cv2.VideoCapture(0)

while not stopAll:
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.flip(frame, 1)

    # lewati frame jika thread dalam kondisi lock (frame sedang
    # dikirim keclient telegram)
    if not lock.locked():
        raw_frame.put(frame)

    # tambah 1 setiap frame yang berhasil diambil
    frame_counter += 1

    # hitung durasi
    elapsed_time = time.time() - frame_start_time
    if elapsed_time > 1:
        # rumus: jumlah frame dibagi durasi
        FPS = int(frame_counter / elapsed_time)

        # XXX: harusnya dapet fps lebih dari 50, soalnya frame diproses dilatar belakang
        # lupa kalau didalem loop masih ada detectMultiScale, jadi kisaran fps yg didapet
        # sekitar 15-30 mungkin lebih

        # reset
        frame_counter = 0
        frame_start_time = time.time()

    # FPS berubah setiap 1 detik
    cv2.putText(
        img=frame,
        text='FPS: %s' % FPS,
        org=coordinate,
        fontFace=fontFace,
        fontScale=fontScale,
        color=fontColor,
        lineType=lineType
    )

    cv2.imshow("frame", frame)
    if cv2.waitKey(1) and 0xFF == ord("q"):
        break

cleanup()
