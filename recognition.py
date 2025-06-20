import face_recognition

known_image = face_recognition.load_image_file("known_image.jpg")
unknown_image = face_recognition.load_image_file("unknown_image2.jpg")

known_encoding = face_recognition.face_encodings(known_image)[0]
unknown_encoding = face_recognition.face_encodings(unknown_image)[0]

results = face_recognition.compare_faces([known_encoding], unknown_encoding)
answer = "Si" if results[0] else "No"

print("L'immagine sconosciuta e' quella di una persona conosciuta:", answer)