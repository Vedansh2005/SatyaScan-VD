import cv2
import numpy as np
import urllib.request
import os
import shutil

# --- 1. SETUP WORKSPACE ---
if os.path.exists("dataset"):
    shutil.rmtree("dataset")
os.makedirs("dataset", exist_ok=True)

print("Downloading authentic test portraits from direct image repositories...")

# Direct static image sources with custom headers to prevent 403/404 blocks
face_sources = {
    "face1.jpg": "https://raw.githubusercontent.com/opencv/opencv/4.x/samples/data/lena.jpg",
    "face2.jpg": "https://images.pexels.com/photos/220453/pexels-photo-220453.jpeg?auto=compress&cs=tinysrgb&w=400",
    "face3.jpg": "https://images.pexels.com/photos/415829/pexels-photo-415829.jpeg?auto=compress&cs=tinysrgb&w=400"
}

headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'}

for name, url in face_sources.items():
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as response, open(name, 'wb') as out_file:
            out_file.write(response.read())
        print(f"✅ Successfully downloaded: {name}")
    except Exception as e:
        print(f"❌ Failed to download {name} from {url}: {e}")

# Verify downloads loaded into OpenCV
face1_img = cv2.imread("face1.jpg")
face2_img = cv2.imread("face2.jpg")
face3_img = cv2.imread("face3.jpg")

if face1_img is None or face2_img is None or face3_img is None:
    raise RuntimeError("Could not load downloaded face images. Check network connection.")

print("\n--- GENERATING LIVE CAPTURES ---")
cv2.imwrite("dataset/live_1_valid_primary.jpg", face1_img)
cv2.imwrite("dataset/live_2_valid_secondary.jpg", face3_img)
cv2.imwrite("dataset/live_3_impersonator.jpg", face2_img)

# Slight crop to simulate realistic camera perspective shift
cv2.imwrite("dataset/live_4_alt_angle.jpg", face1_img[15:-15, 15:-15])
print("✅ Saved Live Test Photos")

# --- PASSPORT GENERATOR ---
def create_passport(filename, face_img, mrz1, mrz2, is_tampered=False):
    img = np.ones((550, 950, 3), dtype=np.uint8) * 255
    cv2.putText(img, "PASSPORT - REPUBLIC OF UTOPIA", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 0), 3)
    cv2.putText(img, "Name: ERIKSSON, ANNA MARIA", (350, 150), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
    cv2.putText(img, "Nationality: UTOPIA", (350, 220), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
    
    color = (50, 50, 50) if is_tampered else (0, 0, 0)
    expiry_text = "Expiry: 26/02/2099" if is_tampered else "Expiry: 26/02/2026"
    cv2.putText(img, expiry_text, (350, 290), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 3 if is_tampered else 2)

    face = cv2.resize(face_img, (250, 300))
    img[100:400, 50:300] = face
        
    cv2.putText(img, mrz1, (30, 470), cv2.FONT_HERSHEY_SIMPLEX, 1.1, (0, 0, 0), 3)
    cv2.putText(img, mrz2, (30, 520), cv2.FONT_HERSHEY_SIMPLEX, 1.1, (0, 0, 0), 3)
    
    cv2.imwrite(f"dataset/{filename}", img, [cv2.IMWRITE_JPEG_QUALITY, 80 if is_tampered else 100])
    print(f"✅ Saved Passport: {filename}")

# --- DRIVING LICENSE GENERATOR ---
def create_dl(filename, face_img, name, dl_number, is_tampered=False):
    img = np.ones((400, 700, 3), dtype=np.uint8) * 255
    img[:] = (240, 230, 200)
    cv2.putText(img, "DRIVING LICENSE - UNION OF INDIA", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 200), 3)
    cv2.putText(img, f"Name: {name}", (250, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 0), 2)
    cv2.putText(img, f"DL No: {dl_number}", (250, 190), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 0), 2)
    
    face = cv2.resize(face_img, (180, 220))
    img[100:320, 30:210] = face
        
    cv2.imwrite(f"dataset/{filename}", img, [cv2.IMWRITE_JPEG_QUALITY, 85 if is_tampered else 100])
    print(f"✅ Saved DL: {filename}")

# --- DOMESTIC ID CARD GENERATOR ---
def create_id_card(filename, face_img, name, id_number):
    img = np.ones((450, 750, 3), dtype=np.uint8) * 255
    cv2.putText(img, "GOVERNMENT ID - SECURE VERIFICATION", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (200, 0, 0), 2)
    cv2.putText(img, f"Name: {name}", (250, 140), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 0), 2)
    cv2.putText(img, f"ID No: {id_number}", (250, 220), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 0), 2)
    
    face = cv2.resize(face_img, (180, 220))
    img[100:320, 30:210] = face
        
    cv2.imwrite(f"dataset/{filename}", img)
    print(f"✅ Saved ID Card: {filename}")

# --- BATCH RUN ---
valid_mrz1 = "P<UTOERIKSSON<<ANNA<MARIA<<<<<<<<<<<<<<<<<<<"
valid_mrz2 = "L898902C36UTO7408122F1204159ZE184226B<<<<<10"

print("\n--- GENERATING PASSPORTS (3 Valid, 2 Fake) ---")
create_passport("pass_1_valid.jpg", face1_img, valid_mrz1, valid_mrz2, is_tampered=False)
create_passport("pass_2_valid.jpg", face1_img, valid_mrz1, valid_mrz2, is_tampered=False)
create_passport("pass_3_valid.jpg", face1_img, valid_mrz1, valid_mrz2, is_tampered=False)
create_passport("pass_4_fake_tampered.jpg", face1_img, valid_mrz1, valid_mrz2, is_tampered=True)
create_passport("pass_5_fake_impersonator.jpg", face2_img, valid_mrz1, valid_mrz2, is_tampered=False)

print("\n--- GENERATING DRIVING LICENSES (3 Valid, 2 Fake) ---")
create_dl("dl_1_valid.jpg", face1_img, "ERIKSSON ANNA MARIA", "MH-12-20100001234")
create_dl("dl_2_valid.jpg", face1_img, "ANNA ERIKSSON", "GA-03-20220009999")
create_dl("dl_3_valid.jpg", face1_img, "ERIKSSON A.", "DL-01-20190005555")
create_dl("dl_4_fake_mismatch.jpg", face1_img, "FRAUDSON ANNA", "MH-12-20100001234")
create_dl("dl_5_fake_tampered.jpg", face1_img, "ERIKSSON ANNA MARIA", "INVALID-FORMAT", is_tampered=True)

print("\n--- GENERATING DOMESTIC ID CARDS (3 Valid, 2 Fake) ---")
create_id_card("id_1_valid.jpg", face1_img, "ERIKSSON ANNA MARIA", "XXXX-XXXX-1234")
create_id_card("id_2_valid.jpg", face1_img, "ANNA ERIKSSON", "XXXX-XXXX-5678")
create_id_card("id_3_valid.jpg", face1_img, "ERIKSSON A.", "XXXX-XXXX-9012")
create_id_card("id_4_fake_mismatch.jpg", face1_img, "WRONG NAME", "XXXX-XXXX-1234")
create_id_card("id_5_fake_impersonator.jpg", face2_img, "ERIKSSON ANNA MARIA", "XXXX-XXXX-1234")

print("\n🚀 Extended Dataset with High-Res Realistic Portraits Generated!")