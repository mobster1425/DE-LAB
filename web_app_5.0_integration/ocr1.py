from PIL import Image
import pytesseract
import re
import sys #for setting path

# Set the path to the Tesseract executable
pytesseract.pytesseract.tesseract_cmd = r'C:/Users/gedam/AppData/Local/Programs/Tesseract-OCR/tesseract.exe'

def extract_text_from_image(image_path):
    try:
        # Open the image file
        image = Image.open(image_path)

        # Use Tesseract to do OCR on the image
        text = pytesseract.image_to_string(image)

        return text
    
    except Exception as e:
        print(f"Error extracting text: {str(e)}")
        return None

def extract_prices_from_text(text):
    try:
        # Define regex pattern to find numeric values
        pattern = r'\d+\.\d{2}'  # Matches a decimal number with two digits after the decimal point

        # Search for numeric values using regex
        matches = re.findall(pattern, text)

        if matches:
            # Convert the extracted strings to float and return
            prices = [float(match) for match in matches]
            return prices
        else:
            return None
        
    except Exception as e:
        print(f"Error extracting prices: {str(e)}")
        return None

def extract_prices_from_image(image_path):
    try:
        # Extract text from the image
        extracted_text = extract_text_from_image(image_path)

        if extracted_text:
            # Extract prices from the extracted text
            prices = extract_prices_from_text(extracted_text)
            print('in ocr : before final return : ',prices)
            return prices #FINAL RETURN OF THIS CODE
        else:
            print("In OCR: Extracted text is empty")
            return None
        
    except Exception as e:
        print(f"Error processing image: {str(e)}")
        return None


#SET PATH
    
if __name__ == "__main__":
    # Check if an image path is provided as a command-line argument
    if len(sys.argv) != 2:
        print("Usage: python OCR.py <image_path>")
        sys.exit(1)

    # Extract text and total amount from the provided image
    image_path = sys.argv[1]
    prices = extract_prices_from_image(image_path)
    print('In OCR Final prices:', prices)  # Debugging statement