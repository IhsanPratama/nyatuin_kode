import logging
logging.basicConfig(
    format="%(threadName)s: --- %(message)s", level=logging.INFO)

logging.info("Mengimport module")

import sys
import signal
import cv2
import telebot
import threading
import queue
import time
import simpleaudio as sa
import tempfile

from telethon import TelegramClient
from telethon import events
import asyncio

import nest_asyncio
nest_asyncio.apply()

# cara bikin API_ID & API_HASH, bisa baca langsung di official docnya
# https://core.telegram.org/api/obtaining_api_id
API_ID = ""
API_HASH = ""

logging.info("Inisiasi Bot telegram")
client = TelegramClient("session/botsession", API_ID, API_KEY)
client.start(
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
                tmp = tempfile.NamedTemporaryFile(suffix='.jpg')

                logging.info(f"Mengirim file {tmp.name!r} ke {SUPERUSER}")
                tmp.write(jpgFrame)

                client.loop.run_until_complete(client.send_file(SUPERUSER, tmp.name,
                               caption="Terdeteksi tidak menggunakan masker"))
        else:
            total_dilewati += 1
        q.task_done()


@client.on(events.NewMessage(pattern=r"^/start"))
async def action_start(event):
    sender = await event.get_sender()
    nama = sender.first_name
    lastname = sender.last_name
    await event.reply("Hello apa kabar {} {}".format(nama, lastname))


@client.on(events.NewMessage(pattern=r"^/help"))
async def send_welcome(event):
    await event.reply("perlu apa gaes?")

@client.on(events.NewMessage(pattern=r"^/stop"))
async def sendSignal(message):
    global stopAll

    sender = await client.get_sender()
    if sender.id == SUPERUSER:
        await event.reply("Video Capture dihentikan")
        cleanup()


def remove_item_queue():
    while not q.empty():
        try:
            q.get(timeout=1)
        except Exception:
            pass


def cleanup(*args, **kwargs):
    global stopAll
    stopAll = True

    cv2.release()
    cv2.destroyAllWindows()

    remove_item_queue()

    if client.is_connected:
        client.loop.run_until_complete(client.disconnect())

    sys.exit(0)

signal.signal(signal.SIGINT, cleanup)

th = threading.Thread(target=sendAlert)
th.setDaemon(True)
th.start()

# life hack, karena telethon itu asyncronous dan entah kenapa
# ketika ngejalanin client, listenernya malah gk bisa kepanggil
# listener: @client.on

def loop_inside_thread(loop):
    asyncio.set_event_loop(loop)
    # jika error / gagal konek ganti client.disconnected jadi
    # client.run_until_disconnected()
    loop.run_until_complete(client.disconnected)

logging.info("Bot Berjalan dilatar belakang")
th = threading.Thread(target=loop_inside_thread, args=(client.loop,))
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
FPS = 0

# list default font:
#   FONT_HERSHEY_COMPLEX
#   FONT_HERSHEY_COMPLEX_SMALL
#   FONT_HERSHEY_DUPLEX
#   FONT_HERSHEY_PLAIN
#   FONT_HERSHEY_SCRIPT_COMPLEX
#   FONT_HERSHEY_SCRIPT_SIMPLEX
#   FONT_HERSHEY_SIMPLEX
#   FONT_HERSHEY_TRIPLEX
#   FONT_ITALIC
fontFace = cv2.FONT_HERSHEY_SIMPLEX

# posisi text / koordinat
coordinate = (10, 10)

# Skala font / ukuran font
# rumus: ukuran font asli dikali n
fontScale = 1

# warna font: putih
fontColor = (255, 255, 255)

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

    # tambah 1 setiap frame yang berhasil diambil
    frame_counter += 1

    # hitung durasi
    elapsed_time = time.time() - frame_start_time
    if (elapsed_time) > 1:
        # rumus: jumlah frame dibagi durasi
        FPS = str(int(frame_counter / elapsed_time))

        # XXX: harusnya dapet fps lebih dari 50, soalnya frame diproses dilatar belakang
        # lupa kalau didalem loop masih ada detectMultiScale, jadi kisaran fps yg didapet
        # sekitar 15-30 mungkin lebih

        # logging.info("FPS: %s", fps)

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
        color=fontColor
    )

    cv2.imshow("frame", frame)
    if cv2.waitKey(1) and 0xFF == ord("q"):
        break

cleanup()
