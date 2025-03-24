import cv2

face_cascade = cv2.CascadeClassifier('model/absensi/haarcascade_frontalface_default.xml')

def detect_faces_from_camera(timeout=5):
    cap = cv2.VideoCapture(0)
    result_face = None
    start_time = cv2.getTickCount()

    while True:
        ret, frame = cap.read()
        if not ret:
            continue

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.2, minNeighbors=5)

        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
            result_face = gray[y:y+h, x:x+w]

        cv2.imshow('Face Detection', frame)

        if (cv2.getTickCount() - start_time)/cv2.getTickFrequency() > timeout:
            break
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    return result_face
