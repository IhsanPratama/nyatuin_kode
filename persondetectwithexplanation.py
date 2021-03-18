#mengimport library yg dibutuhkan
import numpy as np
import math
import time
import sys
import cv2
import argparse
import telepot
from tensorflow.lite.python.interpreter import Interpreter

fps = ""
detectfps = ""
framecount = 0
detectframecount = 0
time1 = 0
time2 = 0

api = '1252781773:AAFY8JxGZlabX7fF9WenHG5qapg85TGpVC4' #token dari bot telegram
bot = telepot.Bot(api)

#1. ini daftar objek yg dapat dideteksinya
LABELS = [
'aeroplane','bicycle','bird','boat','bottle','bus','car','cat','chair','cow',
'diningtable','dog','horse','motorbike','person','pottedplant','sheep','sofa','train','tvmonitor']

#2. ini untuk ngatur sensitifitas dari triggernya
def CheckEntranceLineCrossing(ymax, CoorXEntranceLine):
    AbsDistance = abs(ymax - CoorXEntranceLine)

    if AbsDistance <= 5: #3. jika angka "5" semakin besar, maka akan semakin sensitif untuk triggernya
        return 1
    else:
        return 0
    
if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="ssdlite_mobilenet_v2_voc_300_integer_quant_with_postprocess.tflite", help="Path of the detection model.") #4. model dari tensorflownya
    parser.add_argument("--num_threads", type=int, default=4, help="Threads.") #5. raspi punya 4 core pada prossornya, untuk memaksimalkan kinerjanya
    args = parser.parse_args()

    model        = args.model 
    num_threads  = args.num_threads

    interpreter = Interpreter(model_path=model)
    interpreter.set_num_threads(num_threads)

    interpreter.allocate_tensors()
    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()

    cam = cv2.VideoCapture(0)
    
    window_name = "Movie" #6. nama framenya Movie
    cv2.namedWindow(window_name, cv2.WINDOW_AUTOSIZE)
    
    
    while True:
        start_time = time.perf_counter()

        ret, image = cam.read()
        
        #7. Resize and normalize image for network input
        image_height = image.shape[0]
        image_width = image.shape[1]
        frame = cv2.resize(image, (300, 300)) #8. diresize menjadi 300x300 karna pada modelnya default ukurannya 300x300 selain itu tidak bisa.
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame = np.expand_dims(frame, axis=0)
        frame = frame.astype(np.float32)
        cv2.normalize(frame, frame, -1, 1, cv2.NORM_MINMAX)
        cv2.putText(image, fps, (image_width - 170, 15), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (38, 0, 255), 1, cv2.LINE_AA) #9. untuk menampilkan tulisan fps di layar, jika tidak mau ditampilkan tinggal kasih komentar pada awal baris
        cv2.putText(image, detectfps, (image_width - 170, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (38, 0, 255), 1, cv2.LINE_AA) #10. untuk menampilkan tulisan fps di layar

        # run model
        interpreter.set_tensor(input_details[0]['index'], frame)
        interpreter.invoke()

        # get results
        boxes = interpreter.get_tensor(output_details[0]['index'])[0]
        classes = interpreter.get_tensor(output_details[1]['index'])[0]
        scores = interpreter.get_tensor(output_details[2]['index'])[0]
        count = interpreter.get_tensor(output_details[3]['index'])[0]

        CoorXEntranceLine = int(image_width / 2) #11. lokasi dari triggernya. nilai dari image_width nya = 1. jadi semakin besar nilai pembaginya (lebih dari 1) maka triggernya akan berpindah ke arah kiri. 
        cv2.line(image, (int(CoorXEntranceLine), 0 ), (int(CoorXEntranceLine), image_height), (255, 0, 100), 1) #12. untuk menampilkan triggernya di layar,  jika tidak mau ditampilkan tinggal kasih komentar pada awal baris
        # draw boxes
        for i, (box, classidx, score) in enumerate(zip(boxes, classes, scores)):
            probability = score
            
            if probability >= 0.6: #13. akan ngedeteksi jika persentase nya lebih dari 0.6, jika tidak maka nama dari objek nya tidak akan ditampilkan
                if not box[0] or not box[1] or not box[2] or not box[3]:
                    continue
                ymin = int(box[0] * image_height) #sebagai penanda dari ukuran framenya
                xmin = int(box[1] * image_width)
                ymax = int(box[2] * image_height)
                xmax = int(box[3] * image_width)

                classnum = int(classidx)
                #print('coordinates: ({}, {})-({}, {}). class: "{}". probability: {:.2f}'.format(xmin, ymin, xmax, ymax, classnum, score))
                cv2.rectangle(image, (xmin, ymin), (xmax, ymax), (0, 255, 0), 2) #14. untuk menampilkan kotak pada saat ada objek yang terdeteksi,  jika tidak mau ditampilkan tinggal kasih komentar pada awal baris
                cv2.putText(image, '{}: {:.2f}'.format(LABELS[classnum], score), (xmin, ymin - 5), cv2.FONT_HERSHEY_COMPLEX, 0.8, (255, 255, 0), 2) #15. untuk menampilkan nama dari objek yang dideteksinya, jika tidak mau ditampilkan tinggal kasih komentar pada awal baris

                CoordXCentroid = int((xmin+xmax)/2) #16.
                CoordYCentroid = int((ymin+ymax) /2) #16.
                ObjectCentroid = CoordXCentroid,CoordYCentroid #16.
                cv2.circle(image, ObjectCentroid, 1, (255 ,255 ,255), 10) #16. untuk membuat lingkaran berwarna putih yg dimana itu sebagai pemicunya. lingkaran tersebut berada di tengah2 objek yang telah dideteksi.

                #ini untuk mengaktifkan triggernya
                if(CheckEntranceLineCrossing(CoordXCentroid, CoorXEntranceLine)):
                    
                    if classnum == 14: #classnum 14 isinya person/manusia. jadi yg masuk ke triggernya cuman manusia aja, selain itu tidak bisa
                        print('ada orang')
                        cv2.imwrite("orang.jpg", image) #untuk menyimpan gambar yg telah kena triggernya

                        bot.sendMessage("281862557", "ALERT !!! Person detected in room")  #untuk memberikan notif ke telegram                    
                        bot.sendPhoto("281862557", photo=open("orang.jpg","rb")) #untuk mengirim gambar ke telegram
                    else:
                        print('tidak ada orang')

                        #ketika ada manusia yg kena triggernya maka framenya akan ngefreeze sampai gambar dikirimkan ke telegram
                        #ngefreeze nya agak lama karna gambar yg telah disimpan kemudian di upload ke server telegram, setelah itu di download oleh telegram ke botnya, untuk itu menggunakan extension .jpg karna ukuran dari file gambarnya tidak sebesar jika mengguanakan extension .png
        cow = cv2.resize(image, (720,480)) #17. mengatur ukuran frame yang ditampilkan, tidak ada hubungannya dengan yg diatas.
        cv2.imshow(window_name, cow)

        if cv2.waitKey(1)&0xFF == ord('q'):  #18. program akan berhenti jika ditekan tombol q
            break

        detectframecount += 1

        #19. sebagai perhitungan dari fpsnya
        # FPS calculation
        framecount += 1
        if framecount >= 10:
            fps = "(Playback) {:.1f} FPS".format(time1 / 10)
            detectfps = "(Detection) {:.1f} FPS".format(detectframecount / time2)
            framecount = 0
            detectframecount = 0
            time1 = 0
            time2 = 0
        end_time = time.perf_counter()
        elapsedTime = end_time - start_time
        time1 += 1 / elapsedTime
        time2 += elapsedTime


    #note
    #(255 ,255 ,255) berfungsi untuk mengatur warnanya
