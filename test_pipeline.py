import os
import torch
import easyocr
from mrz.checker.td3 import TD3CodeChecker
from PIL import Image, ImageChops, ImageEnhance
from facenet_pytorch import MTCNN, InceptionResnetV1
import cv2

print("1. Testing Face Verification Engine (PyTorch)...")
# This will download the MTCNN face detection weights and VGGFace2 recognition weights
mtcnn = MTCNN(keep_all=False)
resnet = InceptionResnetV1(pretrained='vggface2').eval()
print("✅ Face models loaded successfully.")

print("\n2. Testing OCR Engine...")
# This will download the EasyOCR text detection and recognition weights
reader = easyocr.Reader(['en'])
print("✅ EasyOCR loaded successfully.")

print("\n3. Testing MRZ Mathematical Checker...")
# A dummy ICAO 9303 standard MRZ string (Passport)
dummy_mrz = (
    "P<UTOERIKSSON<<ANNA<MARIA<<<<<<<<<<<<<<<<<<<\n"
    "L898902C36UTO7408122F1204159ZE184226B<<<<<10"
)
try:
    checker = TD3CodeChecker(dummy_mrz)
    if bool(checker):
        print("✅ MRZ Checksum algorithm working.")
except Exception as e:
    print(f"MRZ Error: {e}")

print("\n4. Testing Tamper Forensics (Pillow/ELA)...")
# Create a dummy blank image to test the Image processing pipeline
dummy_img = Image.new('RGB', (100, 100), color = 'white')
dummy_img.save("test_dummy.jpg", "JPEG", quality=100)
re_saved = dummy_img.copy()
re_saved.save("test_dummy_90.jpg", "JPEG", quality=90)
# Calculate difference (Error Level Analysis baseline)
diff = ImageChops.difference(dummy_img, Image.open("test_dummy_90.jpg"))
extrema = diff.getextrema()
print(f"✅ Pillow ELA module working. Extrema: {extrema}")

# Cleanup dummy files
os.remove("test_dummy.jpg")
os.remove("test_dummy_90.jpg")

print("\n🚀 ALL SYSTEMS GO! Disconnect from Wi-Fi and run this script again to prove it works offline.")
