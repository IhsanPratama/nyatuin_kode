import logging
logging.basicConfig(
    format="%(threadName)s: --- %(message)s", level=logging.INFO)

logging.info("Mengimport module")
import time
import io
import queue
import threading
import telebot
import winsound
import cv2
import signal
import sys

logging.info("Inisiasi Bot telegram")
bot = telebot.TeleBot(
    "1752888275:AAGoy1NhTK0K6OfXHwK0jIYqe9VP246kGkc"
)
SUPERUSER = 1643763065  # ganti pakai id telegrammu

q = queue.Queue()
stopAll = False


def sendAlert():
    logging.info("sendAlert dijalankan")
    while not stopAll:
        frame = q.get()
        winsound.Beep(2500, 1000)

        success, jpgFrame = cv2.imencode(".jpg", frame)
        if success:
            logging.info(f"Mengirim foto ke {userId}")
            ioBuffer = io.BytesIO(frame.read())
            ioBuffer.seek(0)  # penting !!
            bot.send_photo(userId, ioBuffer,
                           caption="Terdeteksi tidak menggunakan masker")
        q.task_done()


def startCapture():
    logging.info("Inisisasi CascadeClasifier")
    face = cv2.CascadeClassifier(
        cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    smile = cv2.CascadeClassifier(
        cv2.data.haarcascades + 'haarcascade_smile.xml')

    logging.info("Memulai kamera")
    cap = cv2.VideoCapture(0)

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
                logging.info("Terdeteksi tanpa masker")
                pesan = 'Tanpa Masker'
                color = (0, 0, 255)
                mask = False
                break

            # aku ubah gray jadi frame soalnya yg dikirim gambar abu2
            cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
            cv2.putText(frame, pesan, (x, y - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 2)
        if mask is False:
            logging.info("Menambahkan item ke dalam queue")
            q.put(frame)
            break


logging.info("Thread dijalankan")
th = threading.Thread(target=sendAlert)
th.setDaemon(True)
th.start()

th = threading.Thread(target=startCapture)
th.setDaemon(True)
th.start()


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

def ctrlChandler(signal, frame):
    global stopAll
    stopAll = True
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

logging.info("Bot Berjalan")
bot.polling()
