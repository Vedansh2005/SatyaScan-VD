import cv2
import numpy as np
import urllib.request
import os
import shutil
import random

# --- SETUP WORKSPACE ---
if os.path.exists("dataset_v2"):
    shutil.rmtree("dataset_v2")
os.makedirs("dataset_v2", exist_ok=True)

print("Downloading authentic test portraits from direct image repositories...")

# More diverse face sources
face_sources = {
    "face_m1.jpg": "https://images.pexels.com/photos/2379004/pexels-photo-2379004.jpeg?auto=compress&cs=tinysrgb&w=400",
    "face_f1.jpg": "https://images.pexels.com/photos/415829/pexels-photo-415829.jpeg?auto=compress&cs=tinysrgb&w=400",
    "face_m2.jpg": "https://images.pexels.com/photos/1222271/pexels-photo-1222271.jpeg?auto=compress&cs=tinysrgb&w=400",
    "face_f2.jpg": "https://images.pexels.com/photos/733872/pexels-photo-733872.jpeg?auto=compress&cs=tinysrgb&w=400"
}

headers = {'User-Agent': 'Mozilla/5.0'}
faces = {}

for name, url in face_sources.items():
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as response, open(name, 'wb') as out_file:
            out_file.write(response.read())
        faces[name] = cv2.imread(name)
        print(f"✅ Successfully downloaded: {name}")
    except Exception as e:
        print(f"❌ Failed to download {name}: {e}")

# --- PASSPORT GENERATOR ---
def create_passport(filename, face_img, surname, given, mrz1, mrz2, is_tampered=False):
    img = np.ones((550, 950, 3), dtype=np.uint8) * 250
    cv2.putText(img, "PASSPORT - REPUBLIC OF INDIA", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (100, 50, 0), 3)
    cv2.putText(img, f"Surname: {surname}", (350, 150), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
    cv2.putText(img, f"Given Name: {given}", (350, 200), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
    cv2.putText(img, "Nationality: IND", (350, 250), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
    
    color = (50, 50, 50) if is_tampered else (0, 0, 0)
    expiry_text = "Expiry: 15/08/2030" if not is_tampered else "Expiry: 99/99/9999" # fake expiry
    cv2.putText(img, expiry_text, (350, 300), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 3 if is_tampered else 2)

    face = cv2.resize(face_img, (250, 300))
    img[100:400, 50:300] = face
        
    cv2.putText(img, mrz1, (30, 470), cv2.FONT_HERSHEY_COMPLEX, 1.1, (0, 0, 0), 3)
    cv2.putText(img, mrz2, (30, 520), cv2.FONT_HERSHEY_COMPLEX, 1.1, (0, 0, 0), 3)
    
    cv2.imwrite(f"dataset_v2/{filename}", img, [cv2.IMWRITE_JPEG_QUALITY, 80 if is_tampered else 100])
    print(f"✅ Saved Passport: {filename}")

# --- DRIVING LICENSE GENERATOR ---
def create_dl(filename, face_img, name, dl_number, is_tampered=False):
    img = np.ones((400, 700, 3), dtype=np.uint8) * 255
    img[:] = (230, 240, 250)
    cv2.putText(img, "DRIVING LICENSE - UNION OF INDIA", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 200), 3)
    cv2.putText(img, f"Name: {name}", (250, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 0), 2)
    cv2.putText(img, f"DL No: {dl_number}", (250, 190), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 0), 2)
    
    face = cv2.resize(face_img, (180, 220))
    img[100:320, 30:210] = face
        
    cv2.imwrite(f"dataset_v2/{filename}", img, [cv2.IMWRITE_JPEG_QUALITY, 85 if is_tampered else 100])
    print(f"✅ Saved DL: {filename}")


# --- BATCH RUN DATA ---
identities = [
    {
        "surname": "KUMAR", "given": "RAHUL", 
        "mrz1": "P<INDKUMAR<<RAHUL<<<<<<<<<<<<<<<<<<<<<<<<<<<",
        "mrz2": "K989802C36IND8501015M3008159<<<<<<<<<<<<<<08",
        "dl": "MH-12-20150001234", "face": "face_m1.jpg"
    },
    {
        "surname": "SHARMA", "given": "PRIYA", 
        "mrz1": "P<INDSHARMA<<PRIYA<<<<<<<<<<<<<<<<<<<<<<<<<<",
        "mrz2": "S456789A12IND9205124F3205128<<<<<<<<<<<<<<04",
        "dl": "DL-01-20190005555", "face": "face_f1.jpg"
    }
]

print("\n--- GENERATING DATASET V2 ---")
for idx, person in enumerate(identities):
    face_img = faces[person["face"]]
    
    # Valid Documents
    create_passport(f"pass_{idx}_valid.jpg", face_img, person["surname"], person["given"], person["mrz1"], person["mrz2"])
    create_dl(f"dl_{idx}_valid.jpg", face_img, f"{person['given']} {person['surname']}", person["dl"])
    
    # Fake Tampered (Bad Pixels)
    create_passport(f"pass_{idx}_fake_tampered.jpg", face_img, person["surname"], person["given"], person["mrz1"], person["mrz2"], is_tampered=True)
    
    # Fake Impersonator (Wrong face)
    wrong_face = faces["face_m2.jpg" if "f" in person["face"] else "face_f2.jpg"]
    create_passport(f"pass_{idx}_fake_impersonator.jpg", wrong_face, person["surname"], person["given"], person["mrz1"], person["mrz2"])
    
    # Fake DL Mismatch (Wrong name)
    create_dl(f"dl_{idx}_fake_mismatch.jpg", face_img, f"FAKE {person['surname']}", person["dl"])

    # Live feed images
    cv2.imwrite(f"dataset_v2/live_{idx}_valid.jpg", face_img)
    cv2.imwrite(f"dataset_v2/live_{idx}_impersonator.jpg", wrong_face)

print("\n🚀 Extended Dataset V2 Generated successfully in 'dataset_v2' folder!")
