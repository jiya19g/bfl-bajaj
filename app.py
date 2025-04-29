from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import pytesseract
from PIL import Image
import io
import cv2
import numpy as np
import re
from typing import Optional

# Initialize FastAPI app
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"],  
)

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


def preprocess_image(image: Image.Image) -> np.ndarray:
    """Preprocess the image to optimize for OCR."""
    img = np.array(image.convert('RGB'))  # Convert PIL image to NumPy array
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)  # Convert to grayscale
    thresh = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2
    )
    kernel = np.ones((2, 2), np.uint8)
    processed = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel, iterations=1)
    return processed

def extract_text_from_image(image: Image.Image) -> str:
    """Extract text using OCR."""
    processed_img = preprocess_image(image)
    pil_img = Image.fromarray(processed_img)  # Convert back to PIL image
    text = pytesseract.image_to_string(pil_img, lang='eng', config='--psm 6 --oem 3')
    return text.strip()


def clean_test_name(name):
    name = re.sub(r'\b\d+\b', '', name)
    return ' '.join(name.split())

def fix_unit(unit):
    unit = unit.replace('mmo1/1', 'mmol/L')
    unit = unit.replace('mmoI/1', 'mmol/L')
    return unit

def parse_lab_report(text):
    results = []
    lines = text.splitlines()

    line_pattern = re.compile(
        r"([\w\s\(\)\-\/\.]+?)\s+([><]?[0-9]+(?:\.[0-9]*)?)\s*([a-zA-Z\/%]*)\s*[.\[\(]?\s*([0-9.]*)\s*[-–to]*\s*([0-9.]+)\s*[\]\)]?",
        re.IGNORECASE
    )

    for line in lines:
        line = line.strip()
        if not line:
            continue

        match = line_pattern.search(line)
        if match:
            test_name = match.group(1).strip()
            result_value = match.group(2).strip()
            unit = fix_unit(match.group(3))
            ref_min = match.group(4)
            ref_max = match.group(5)

            if "eGFR" in test_name and result_value.startswith(">"):
                result_value = float(result_value[1:])
            else:
                result_value = float(result_value)

            test_name = clean_test_name(test_name)

            try:
                if ref_max in ['', '.']:
                    continue
                if ref_min in ['', '.']:
                    ref_min = float(ref_max)
                else:
                    ref_min = float(ref_min)
                ref_max = float(ref_max)
            except ValueError:
                continue

            if ref_min > ref_max:
                ref_min, ref_max = ref_max, ref_min

            if (result_value > 1000 or ref_min > 1000 or ref_max > 1000) and unit.lower() not in ['mg/dl', 'mmol/l', 'millions/cumm', 'ml/min/1.73sq.m']:
                continue

            out_of_range = result_value < ref_min or result_value > ref_max

            results.append({
                "test_name": test_name,
                "result_value": result_value,
                "unit": unit,
                "bio_reference_range": f"{ref_min}-{ref_max}",
                "lab_test_out_of_range": out_of_range
            })

    return results

@app.get("/")
def read_root():
    return {"message": "FastAPI OCR service is running!"}


@app.post("/upload/")
async def upload_image(file: UploadFile = File(...)):
    try:
        
        image_bytes = await file.read()
        image = Image.open(io.BytesIO(image_bytes))
        
        
        extracted_text = extract_text_from_image(image)
        
        
        structured_data = parse_lab_report(extracted_text)
        
        
        return JSONResponse(content=structured_data)
    
    except Exception as e:
        return JSONResponse(status_code=400, content={"message": str(e)})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
