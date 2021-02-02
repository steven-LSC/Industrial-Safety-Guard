# Industrial-Safety-Guard

This is a system for checking workers’ safety equipment and counting hours. It consists of a Line chatbot and a QR code scanner.

* Line Chatbot: We use Line to build user interface, including: uploading selfies, safety equipment checking, QR code generating, encrypt time information.

* QR Code Scanner: Scan QR code to enter the construction site, get working hours.



### Demo Video
https://youtu.be/wZUJtKhuDuA

### Diagram
![image](https://github.com/steven-LSC/Industrial-Safety-Guard/blob/main/industrial%20safety%20guard%20diagram.png)

### Features
Frontend:
* Line chatbot: Upload selfie for detection, and back up the selfie taken before the last time.
* Security door: Scan QR Code. If the difference between the detection time and the passing time exceeds 10 minutes, worker cannot enter.
* Working hours calculation: Scan QR Code to get today's working hours.

Backend:
* Amazon Rekognition: Upload workers' selfie to Amazon Rekognition PPE to detect whether they are wearing masks and helmets.
* AWS S3: Upload worker selfies to AWS S3 for backup.
* Imgur API: Upload the QR Code to Imgur so that users can access it through the Line Chatbot.
* Time information: Record working hours and calculate working hours.
* Encryption and decryption: DES encryption to encrypt and decrypt of the time information.

### Tech
* Line Chatbot
* AWS S3
* AWS Rekognition
* Imgur API
* DES Encryption
* Heroku
* ngrok
