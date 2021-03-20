import time  # kasih penjelasan tiap library yang di import
import io
import queue
import threading
import telebot
import winsound
import cv2
import signal
import sys
import logging
logging.basicConfig(
    format="%(threadName)s: --- %(message)s", level=logging.INFO)  # bagian ini gan buat apa ?
# jelasin gan per baris koding biar ane paham
logging.info("Mengimport module")

logging.info("Inisiasi Bot telegram")
bot = telebot.TeleBot(
    "1752888275:AAGoy1NhTK0K6OfXHwK0jIYqe9VP246kGkc"  # kalo ini dah paham
)
SUPERUSER = 626351605  # ganti pakai id telegrammu
DELAY = 2  # detik masih belum  ngaruh. langsung brebett aja banyak foto

q = queue.Queue()  # jelasin ini gan
stopAll = False
lastSending = None  # varibel ini yg bakal dijadiin timestamp


def sendAlert():  # jelasin proses ini sampe bawah
    # referensi penggunaan global variable
    # https://stackoverflow.com/questions/4693120/use-of-global-keyword-in-python
    global lastSending

    logging.info("sendAlert dijalankan")
    while not stopAll:
        frame = q.get()
        # ubah numpy array (frame) ke bentuk format jpg
        success, jpgFrame = cv2.imencode(".jpg", frame)
        if success:
            winsound.Beep(2500, 1000)
            lastSending = time.time()
            logging.info(f"Mengirim foto ke {SUPERUSER}")
            # referensi: https://stackoverflow.com/a/11696554
            ioBuffer = io.BytesIO(jpgFrame)
            ioBuffer.seek(0)  # penting !!
            bot.send_photo(SUPERUSER, ioBuffer,
                           caption="Terdeteksi tidak menggunakan masker")

            # update timestamp setelah berhasil mengirim foto

        q.task_done()  # jelasin gan


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
def signal_handler(signal, frame):  # jelasin ini gan
    global stopAll
    stopAll = True


signal.signal(signal.SIGINT, signal_handler)  # jelasin ini gan nyampe bawah


# menjalankan fungsi sendAlert dan bot
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

while not stopAll:

    # deteksi wajah dan lain lain
    ret, frame = cap.read()
    frame = cv2.flip(frame, 1)
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2BGRA)
    # jelasin angka angka ini gan
    faces = face.detectMultiScale(gray, 1.1, 5, 0, (140, 140), (250, 250))

    mask = True
    for x, y, w, h in faces:
        smiles = smile.detectMultiScale(
            gray[y:y + h, x:x + w], 1.4, 5, 0, (75, 75), (90, 90))  # sama ini juga
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
        # setelah terdeteksi tidak menggunakan masker
        # selanjutnya pastikan kalau waktu terakhir mengirim itu kurang dari DELAY
        # atau belum diset
        if not lastSending or int(time.time() - lastSending) > DELAY:
            logging.info("Menambahkan frame ke dalam queue")
            q.put(frame)  # jelasin bagian ini

    cv2.imshow("frame", frame)
    # aku ambil kode dari sini
    # https://stackoverflow.com/a/52913689
    if cv2.waitKey(1) and 0xFF == ord("q"):
        break

cv2.release()
cv2.destroyAllWindows()
