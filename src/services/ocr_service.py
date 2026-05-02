import pytesseract
from PIL import Image
import io

class OCRService:
    @staticmethod
    def extract_tokens(file_bytes: bytes):
        image = Image.open(io.BytesIO(file_bytes))
        
        data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
        
        tokens = []
        full_text_list = []
        
        for i in range(len(data['text'])):
            word = data['text'][i].strip()

            if word:
                token = {
                    "text": word,
                    "confidence": float(data['conf'][i]),
                    "x": data['left'][i],
                    "y": data['top'][i],
                    "width": data['width'][i],
                    "height": data['height'][i]
                }
                tokens.append(token)
                full_text_list.append(word)
        
        return tokens, " ".join(full_text_list)