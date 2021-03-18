import cv2
# winsound sepertinya gk terlalu dibutuhin gantinya import io
import io
import telebot
import threading
import winsound

# windsound dibutuhin gan biar keluar suara tittt ketika ada yang ga pake masker

api = "1752888275:AAGoy1NhTK0K6OfXHwK0jIYqe9VP246kGkc"
bot = telebot.TeleBot(api)
ID_TELE = "626351605"

face = cv2.CascadeClassifier(
    cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
smile = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_smile.xml')
cap = cv2.VideoCapture(0)


def sendAlert(frame):
    # aku ambil sebagian kode dari https://stackoverflow.com/a/52865864
    # sama file satunya
    success, jpgBuffer = cv2.imencode(".jpg", frame)
    if success:
        temp = io.BytesIo()
        temp.save(jpgBuffer)
        temp.seek(0)  # penting!!

        bot.sendMessage(ID_TELE, "Tidak pakai masker")
        bot.sendPhoto(ID_TELE, ('temp.jpg', temp))


while True:
    ret, frame = cap.read()
    frame = cv2.flip(frame, 1)
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2BGRA)
    #faces = face.detectMultiScale(gray, 1.1, 5,0,(140,140),(250,250))
    faces = face.detectMultiScale(gray, 1.1, 5, 0, (140, 140), (250, 250))
    mask = True

    for x, y, w, h in faces:
        smiles = smile.detectMultiScale(
            gray[y:y + h, x:x + w], 1.4, 5, 0, (75, 75), (90, 90))
        #smiles = smile.detectMultiScale(gray[y:y + h, x:x + w], 1.4, 5, 0, (75, 75), (90, 90))
        pesan = 'Dengan Masker'
        color = (0, 255, 0)

        # for ex, ey, ew, eh in smiles:
        if smiles:
            pesan = 'Tanpa Masker'
            color = (0, 0, 255)

            mask = False
            # karna disini kedeteksi tanpa masker otomatis mask jadi False
            # dan kayaknya gk perlu pakai looping

        cv2.rectangle(gray, (x, y), (x + w, y + h), color, 2)
        cv2.putText(gray, pesan, (x, y - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 2)

    if mask is False:
        # nah trigger nya disini
        # kenapa gk diatas aja?
        # karena gk mau ada kejadian ngirim file berkali2

        if threading.active_count() == 1:
            # wajib 1
            # artinya, gk ada thread lain yg lagi ngejalanin fungsi sendAlert

            th = threading.Thread(sendAlert, args=(frame,))
            th.start()

    cv2.imshow('frame', gray)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
