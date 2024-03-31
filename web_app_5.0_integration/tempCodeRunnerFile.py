def extract_price_from_image(image_path):
    try:
        #Open OCR Subprocess
        process = subprocess.Popen(['python', 'C:/Users/gedam/OneDrive/Desktop/Design_Engineering_Features/Demo/ocr1.py', image_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

         #Set a timeout of 60 seconds
        output, _ = process.communicate(timeout=180) 

        print('returned out put : ', output)

        #split output list
        prices = output.decode('utf-8').split('\r\n')
        print('prices : ',prices)

        return prices