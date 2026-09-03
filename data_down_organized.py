import cv2
import numpy as np
import urllib.request
import os
import shutil
from mrz.generator.td3 import TD3CodeGenerator

# --- VERHOEFF ALGORITHM UTILS ---
d_table = [
    [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
    [1, 2, 3, 4, 0, 6, 7, 8, 9, 5],
    [2, 3, 4, 0, 1, 7, 8, 9, 5, 6],
    [3, 4, 0, 1, 2, 8, 9, 5, 6, 7],
    [4, 0, 1, 2, 3, 9, 5, 6, 7, 8],
    [5, 9, 8, 7, 6, 0, 4, 3, 2, 1],
    [6, 5, 9, 8, 7, 1, 0, 4, 3, 2],
    [7, 6, 5, 9, 8, 2, 1, 0, 4, 3],
    [8, 7, 6, 5, 9, 3, 2, 1, 0, 4],
    [9, 8, 7, 6, 5, 4, 3, 2, 1, 0]
]
p_table = [
    [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
    [1, 5, 7, 6, 2, 8, 3, 0, 9, 4],
    [5, 8, 0, 3, 7, 9, 6, 1, 4, 2],
    [8, 9, 1, 6, 0, 4, 3, 5, 2, 7],
    [9, 4, 5, 3, 1, 2, 6, 8, 7, 0],
    [4, 2, 8, 6, 5, 7, 3, 9, 0, 1],
    [2, 7, 9, 3, 8, 0, 6, 4, 1, 5],
    [7, 0, 4, 6, 9, 1, 3, 2, 5, 8]
]
inv_table = [0, 4, 3, 2, 1, 5, 6, 7, 8, 9]

def generate_valid_aadhaar(base_11_digits):
    c = 0
    for i, item in enumerate(reversed(str(base_11_digits))):
        c = d_table[c][p_table[(i + 1) % 8][int(item)]]
    chk = str(inv_table[c])
    full = str(base_11_digits) + chk
    return f"{full[0:4]} {full[4:8]} {full[8:12]}"

# --- SETUP WORKSPACE ---
if os.path.exists("dataset_organized"):
    shutil.rmtree("dataset_organized")
os.makedirs("dataset_organized", exist_ok=True)

print("Downloading authentic test portraits...")
face_sources = {
    "face_m1.jpg": "https://images.pexels.com/photos/2379004/pexels-photo-2379004.jpeg?auto=compress&cs=tinysrgb&w=400",
    "face_f1.jpg": "https://images.pexels.com/photos/415829/pexels-photo-415829.jpeg?auto=compress&cs=tinysrgb&w=400",
    "face_m2.jpg": "https://images.pexels.com/photos/1222271/pexels-photo-1222271.jpeg?auto=compress&cs=tinysrgb&w=400",
    "face_f2.jpg": "https://images.pexels.com/photos/733872/pexels-photo-733872.jpeg?auto=compress&cs=tinysrgb&w=400"
}

headers = {'User-Agent': 'Mozilla/5.0'}
faces = {}

for name, url in face_sources.items():
    if not os.path.exists(name) or os.path.getsize(name) == 0:
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=10) as response, open(name, 'wb') as out_file:
                out_file.write(response.read())
            print(f"✅ Successfully downloaded: {name}")
        except Exception as e:
            print(f"⚠️ Warning: Could not download {name}: {e}")
            # Generate fallback face if download fails
            dummy_face = np.ones((300, 250, 3), dtype=np.uint8) * 180
            cv2.circle(dummy_face, (125, 120), 60, (220, 200, 180), -1)
            cv2.imwrite(name, dummy_face)
    faces[name] = cv2.imread(name)

# --- PASSPORT GENERATOR ---
def create_passport(filepath, face_img, surname, given, passport_no, country, dob, sex, expiry, is_tampered=False, is_math_forgery=False):
    img = np.ones((550, 950, 3), dtype=np.uint8) * 248
    # Background pattern simulation
    for y in range(0, 550, 20):
        cv2.line(img, (0, y), (950, y), (240, 240, 245), 1)

    cv2.putText(img, f"PASSPORT - REPUBLIC OF {country}", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.1, (110, 40, 0), 3)
    cv2.putText(img, f"Surname: {surname}", (350, 130), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 0), 2)
    cv2.putText(img, f"Given Name: {given}", (350, 180), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 0), 2)
    cv2.putText(img, f"Nationality: {country}", (350, 230), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 0), 2)
    cv2.putText(img, f"DOB: {dob[4:6]}/{dob[2:4]}/19{dob[0:2]}", (350, 280), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 0), 2)
    cv2.putText(img, f"Passport No: {passport_no}", (350, 330), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 0), 2)
    
    # Expiry visual string
    if is_tampered:
        # Visual text altered (tampered) to 2099, but MRZ remains or is modified inconsistently
        cv2.putText(img, "Expiry: 12/12/2099", (350, 380), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (30, 30, 30), 3)
    else:
        cv2.putText(img, f"Expiry: {expiry[4:6]}/{expiry[2:4]}/20{expiry[0:2]}", (350, 380), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 0), 2)

    # Add Portrait
    face = cv2.resize(face_img, (250, 300))
    img[90:390, 50:300] = face
    cv2.rectangle(img, (50, 90), (300, 390), (180, 180, 180), 2)
    
    # Generate Real ICAO TD3 MRZ Code
    gen = TD3CodeGenerator("P", country, surname, given, passport_no, country, dob, sex, expiry, "")
    mrz_str = str(gen)
    mrz_lines = mrz_str.split("\n")
    mrz1, mrz2 = mrz_lines[0], mrz_lines[1]
    
    if is_math_forgery:
        # Intentionally alter check digit in mrz2 to test mathematical checksum failure
        mrz2 = mrz2[:-2] + "99"

    # Monospace font simulation for MRZ
    cv2.putText(img, mrz1, (30, 465), cv2.FONT_HERSHEY_SIMPLEX, 0.95, (0, 0, 0), 2)
    cv2.putText(img, mrz2, (30, 515), cv2.FONT_HERSHEY_SIMPLEX, 0.95, (0, 0, 0), 2)
    
    # Tampering artifact: Add high-contrast patch over expiry or photo if tampered
    if is_tampered:
        # Add digital splice rectangle artifact with different compression
        overlay = img.copy()
        cv2.rectangle(overlay, (340, 355), (650, 395), (255, 255, 220), -1)
        cv2.putText(overlay, "Expiry: 12/12/2099", (350, 380), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 0), 2)
        img = cv2.addWeighted(overlay, 0.9, img, 0.1, 0)
        cv2.imwrite(filepath, img, [cv2.IMWRITE_JPEG_QUALITY, 70])
    else:
        cv2.imwrite(filepath, img, [cv2.IMWRITE_JPEG_QUALITY, 98])

# --- DRIVING LICENSE GENERATOR ---
def create_dl(filepath, face_img, name, dl_number, dob_str="01/01/1985", is_tampered=False):
    img = np.ones((400, 700, 3), dtype=np.uint8) * 255
    img[:] = (235, 242, 250)
    cv2.putText(img, "DRIVING LICENSE - UNION OF INDIA", (20, 45), cv2.FONT_HERSHEY_SIMPLEX, 0.95, (0, 0, 180), 3)
    cv2.putText(img, f"Name: {name}", (240, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.85, (0, 0, 0), 2)
    cv2.putText(img, f"DL No: {dl_number}", (240, 180), cv2.FONT_HERSHEY_SIMPLEX, 0.85, (0, 0, 0), 2)
    cv2.putText(img, f"DOB: {dob_str}", (240, 240), cv2.FONT_HERSHEY_SIMPLEX, 0.85, (0, 0, 0), 2)
    cv2.putText(img, "Valid Till: 15/08/2035", (240, 300), cv2.FONT_HERSHEY_SIMPLEX, 0.85, (0, 100, 0), 2)
    
    face = cv2.resize(face_img, (180, 220))
    img[90:310, 30:210] = face
    cv2.rectangle(img, (30, 90), (210, 310), (160, 160, 160), 2)
        
    quality = 70 if is_tampered else 98
    cv2.imwrite(filepath, img, [cv2.IMWRITE_JPEG_QUALITY, quality])

# --- AADHAAR CARD GENERATOR ---
def create_aadhaar(filepath, face_img, name, aadhaar_number, dob_str="01/01/1985", is_tampered=False):
    img = np.ones((400, 700, 3), dtype=np.uint8) * 255
    img[:] = (225, 245, 255)
    cv2.putText(img, "UNIQUE IDENTIFICATION AUTHORITY OF INDIA", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 110, 0), 2)
    cv2.putText(img, "AADHAAR CARD - GOVT. OF INDIA", (20, 75), cv2.FONT_HERSHEY_SIMPLEX, 0.85, (160, 40, 0), 2)
    
    cv2.putText(img, f"Name: {name}", (240, 140), cv2.FONT_HERSHEY_SIMPLEX, 0.85, (0, 0, 0), 2)
    cv2.putText(img, f"DOB: {dob_str}", (240, 200), cv2.FONT_HERSHEY_SIMPLEX, 0.85, (0, 0, 0), 2)
    cv2.putText(img, f"Aadhaar: {aadhaar_number}", (240, 270), cv2.FONT_HERSHEY_SIMPLEX, 0.95, (0, 0, 0), 3)
    
    face = cv2.resize(face_img, (180, 220))
    img[95:315, 30:210] = face
    cv2.rectangle(img, (30, 95), (210, 315), (160, 160, 160), 2)
        
    quality = 70 if is_tampered else 98
    cv2.imwrite(filepath, img, [cv2.IMWRITE_JPEG_QUALITY, quality])

# --- PROFILES CONFIGURATION ---
identities = [
    {
        "folder": "Rahul_Kumar",
        "name_full": "RAHUL KUMAR",
        "surname": "KUMAR", "given": "RAHUL",
        "passport_no": "Z898902C3",  # Clean passport
        "country": "IND",
        "dob": "850101",
        "sex": "M",
        "expiry": "300815",
        "dl": "MH-12-20150001234",
        "aadhaar_base": "54892348901",
        "face": "face_m1.jpg",
        "wrong_face": "face_m2.jpg"
    },
    {
        "folder": "Priya_Sharma",
        "name_full": "PRIYA SHARMA",
        "surname": "SHARMA", "given": "PRIYA",
        "passport_no": "P546789A1",  # Clean passport
        "country": "IND",
        "dob": "920512",
        "sex": "F",
        "expiry": "320512",
        "dl": "DL-01-20190005555",
        "aadhaar_base": "89324567123",
        "face": "face_f1.jpg",
        "wrong_face": "face_f2.jpg"
    },
    {
        "folder": "Vikram_Singh_Suspect",
        "name_full": "VIKRAM SINGH",
        "surname": "SINGH", "given": "VIKRAM",
        "passport_no": "K989802C3",  # Blacklisted Passport (Interpol Notice)
        "country": "IND",
        "dob": "800315",
        "sex": "M",
        "expiry": "280315",
        "dl": "HR-05-20110008888",
        "aadhaar_base": "12345678901",
        "face": "face_m2.jpg",
        "wrong_face": "face_m1.jpg"
    }
]

print("\n--- GENERATING STRUCTURED DATASET ---")
for person in identities:
    folder_path = os.path.join("dataset_organized", person["folder"])
    os.makedirs(folder_path, exist_ok=True)
    
    face_img = faces[person["face"]]
    wrong_face_img = faces[person["wrong_face"]]
    aadhaar_valid = generate_valid_aadhaar(person["aadhaar_base"])
    dob_fmt = f"{person['dob'][4:6]}/{person['dob'][2:4]}/19{person['dob'][0:2]}"
    
    # 1. Valid Documents
    create_passport(os.path.join(folder_path, "1_passport_valid.jpg"), face_img, 
                    person["surname"], person["given"], person["passport_no"], 
                    person["country"], person["dob"], person["sex"], person["expiry"])
    
    create_dl(os.path.join(folder_path, "2_driving_license_valid.jpg"), face_img, 
              person["name_full"], person["dl"], dob_str=dob_fmt)
    
    create_aadhaar(os.path.join(folder_path, "3_aadhaar_valid.jpg"), face_img, 
                   person["name_full"], aadhaar_valid, dob_str=dob_fmt)
    
    # 2. Tampered & Impersonator Documents
    create_passport(os.path.join(folder_path, "4_passport_tampered.jpg"), face_img, 
                    person["surname"], person["given"], person["passport_no"], 
                    person["country"], person["dob"], person["sex"], person["expiry"], is_tampered=True)
    
    create_passport(os.path.join(folder_path, "5_passport_impersonator.jpg"), wrong_face_img, 
                    person["surname"], person["given"], person["passport_no"], 
                    person["country"], person["dob"], person["sex"], person["expiry"])
                    
    create_passport(os.path.join(folder_path, "8_passport_math_forgery.jpg"), face_img, 
                    person["surname"], person["given"], person["passport_no"], 
                    person["country"], person["dob"], person["sex"], person["expiry"], is_math_forgery=True)
    
    # 3. Live Captures
    cv2.imwrite(os.path.join(folder_path, "6_live_camera_valid.jpg"), face_img)
    cv2.imwrite(os.path.join(folder_path, "7_live_camera_impersonator.jpg"), wrong_face_img)
    
    print(f"✅ Generated full suite for: {person['folder']}")

print("\n🚀 Dataset generation complete! All files saved in 'dataset_organized'.")
