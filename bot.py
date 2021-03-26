import logging

# Dalam kasus ini aku pakai logging buat pengganti print aja sih
# referensi, cara kerja logging dll bisa baca disini
# https://gist.github.com/mariocj89/73824162a3e35d50db8e758a42e39aab


# ubah level=logging.DEBUG menjadi level=logging.INFO jika
# ingin keluar dari mode debugging atau sebaliknya
logging.basicConfig(
    format="%(threadName)s: --- %(message)s", level=logging.INFO)

logging.info("Mengimport module")

import time

# aku pake module ini buat pengganti keyword open
# penjelasan kenapa, nanti ada dibawah
import io

# queue salah satu cara paling mudah buat bikin shared variable
# referensi: https://medium.com/omarelgabrys-blog/threads-vs-queues-a71e8dc30156
import queue

import threading
import telebot
import winsound
import cv2

# untuk capture signal yg dikirim keyboard, e.g: CTRL-C
import signal

import sys

logging.info("Inisiasi Bot telegram")
bot = telebot.TeleBot(
    "1752888275:AAGoy1NhTK0K6OfXHwK0jIYqe9VP246kGkc"  # kalo ini dah paham
)
SUPERUSER = 626351605  # ganti pakai id telegrammu
DELAY = 2  # detik
FRAMESKIP = 5 # skip frame setelah x kali, video capture jalan normal
              # ini berlaku buat queuenya

logging.info("Inisisasi CascadeClasifier")
face = cv2.CascadeClassifier(
    cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
smile = cv2.CascadeClassifier(
    cv2.data.haarcascades + 'haarcascade_smile.xml')

q = queue.Queue()
stopAll = False
lastSending = None # variabel ini yg bakal dijadiin timestamp

def detectMask():
    global lastSending

    # setelah tanya2, banyak yang nyaranin buat misahin
    # fungsi detect mask dan dijalanin pake threading
    # fungsi sendAlert aku gabungin jadi satu

    logging.info("detectMask dijalankan")
    while not stopAll:
        frame = q.get()
        logging.debug(f"{frame = }")
        frame = cv2.flip(frame, 1)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2BGRA)

        # jelasin angka angka ini gan!
        # lho tak kira mas dah ngerti, soalnya aku cuma ngambil dikodingan yg mas kasih
        # kemarin

        faces = face.detectMultiScale(gray, 1.1, 5, 0, (140, 140), (250, 250))

        mask = True
        for x, y, w, h in faces:

            # yg ini juga sama
            smiles = smile.detectMultiScale(
                gray[y:y + h, x:x + w], 1.4, 5, 0, (75, 75), (90, 90))
            pesan = 'Dengan Masker'
            color = (0, 255, 0)

            for ex, ey, ew, eh in smiles:
                pesan = 'Tanpa Masker'
                color = (0, 0, 255)
                mask = False
                break

            # aku ubah gray jadi frame soalnya yg dikirim gambar abu2
            cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
            cv2.putText(frame, pesan, (x, y - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 2)

        if mask is False:
            # setelah terdeteksi tidak menggunakan masker
            # selanjutnya pastikan kalau waktu terakhir mengirim itu kurang dari DELAY
            # atau belum diset
            current = time.time()
            logging.debug(f"current = {int(current - lastSending)")
            if not lastSending or int(current - lastSending) > DELAY:
                # ubah numpy array (frame) ke bentuk format jpg
                success, jpgFrame = cv2.imencode(".jpg", frame)
                if success:
                    winsound.Beep(2500, 1000)
                    logging.info(f"Mengirim foto ke {SUPERUSER}")

                # io.BytesIO sama kaya
                #
                # cv2.imwrite("jpgFrame.jpg", jpgFrame)
                # ioBuffer = open("jpgFrame.jpg", "rb")
                #
                # hanya saja io.BytesIO nyimpen data nya bukan difile tapi
                # didalam memori, ini lebih efisien daripada harus simpen
                # terus dibuka lagi.
                #
                # referensi: https://stackoverflow.com/a/11696554

                ioBuffer = io.BytesIO(jpgFrame)
                ioBuffer.seek(0)  # penting !!
                bot.send_photo(SUPERUSER, ioBuffer,
                               caption="Terdeteksi tidak menggunakan masker")
                lastSending = current
            else:
                logging.info(f"lastSending: %s", current - (lastSending or 0))
        # ini untuk ngasih tau kalau task yg baru saja diambil (q.get) sudah selesai
        # kalau gk di panggil queue gk bakal mau lanjut ke task berikutnya
        # soalnya task yg sebelumnya dianggep belum selesai
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


# handling ctrl-C signal
def signal_handler(signal, frame):
    # kalau misal kita pencet ctrl-c nanti bakal muncul traceback
    # KeyboardInterrupt iya kan, tapi masalahnya aku gk tau tracebacknya
    # bakal muncul dimana, bisa aja pas lagi ngirim foto atau pas lagi deteksi
    # object. kalau dikasih try except disetiap fungsi bakal gk efisien kodenya
    #
    # variable stopAll ini apa sih, kok kayaknya penting banget?
    #   coba liat di bagian `while not stopAll`, maksudnya
    #   looping jalan terus kalau variable stopAll False atau not True
    #   nah kalau kita ganti stopAll jadi True ini bakal ngeberhentiin
    #   semua looping yang pakai kondisi itu, fungsi sendSignal diatas
    #   konsepnya sama

    global stopAll

    logging.debug("CTRL-C Signal Captured")
    stopAll = True

# alurnya simple gini kalau terdeteksi signal yg di daftarin
# disini `signal.SIGINT` atau CTRL-C maka panggil fungsi signal_handler
# wiki: https://en.m.wikipedia.org/wiki/Signal_(IPC)

signal.signal(signal.SIGINT, signal_handler)


# menjalankan fungsi detectMask dan bot
th = threading.Thread(target=detectMask)
th.setDaemon(True)
th.start()

logging.info("Bot Berjalan dilatar belakang")
th = threading.Thread(target=bot.polling)
th.setDaemon(True)
th.start()

logging.info("Memulai kamera")
cap = cv2.VideoCapture(0)
currentFrame = 0

while not stopAll:
    ret, frame = cap.read()

    logging.debug(f"{currentFrame = }")
    if ret and not q.full() and currentFrame > FRAMESKIP:
        q.put(frame)
        currentFrame = 0

    # update currentFrame
    currentFrame += 1
    cv2.imshow("frame", frame)

    # capture key, delay 0
    # looping tak terbatas
    key = cv2.waitKey(0)
    logging.debug(f"{key = }")
    if key == ord("q"):
        break

stopAll = True
cv2.release()
cv2.destroyAllWindows()
