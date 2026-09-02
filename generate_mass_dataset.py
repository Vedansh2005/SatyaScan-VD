
import cv2
import numpy as np
import urllib.request
import os
import shutil

# --- 1. SETUP WORKSPACE (CLEAN OLD DATA) ---
if os.path.exists("dataset"):
    shutil.rmtree("dataset") # Delete the old folder entirely
os.makedirs("dataset", exist_ok=True)

print("Downloading base biometric faces...")
faces = {
    "face1.jpg": "https://raw.githubusercontent.com/ageitgey/face_recognition/master/examples/obama.jpg",
    "face2.jpg": "https://raw.githubusercontent.com/ageitgey/face_recognition/master/examples/biden.jpg"
}
for name, url in faces.items():
    if not os.path.exists(name):
        urllib.request.urlretrieve(url, name)

print("\n--- GENERATING LIVE CAPTURES ---")
cv2.imwrite("dataset/live_1_valid.jpg", cv2.imread("face1.jpg"))
print("✅ Saved: live_1_valid.jpg")

cv2.imwrite("dataset/live_2_impersonator.jpg", cv2.imread("face2.jpg"))
print("✅ Saved: live_2_impersonator.jpg")

img1 = cv2.imread("face1.jpg")
cv2.imwrite("dataset/live_3_alt_angle.jpg", img1[20:img1.shape[0]-20, 20:img1.shape[1]-20])
print("✅ Saved: live_3_alt_angle.jpg")

# --- 2. PASSPORT GENERATOR ---
def create_passport(filename, face_path, mrz1, mrz2, bg_color=(255, 255, 255), is_tampered=False):
    img = np.ones((550, 950, 3), dtype=np.uint8)
    img[:] = bg_color
    
    cv2.putText(img, "PASSPORT - REPUBLIC OF UTOPIA", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0,0,0), 3)
    cv2.putText(img, "Name: ERIKSSON, ANNA MARIA", (350, 150), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,0), 2)
    cv2.putText(img, "Nationality: UTOPIA", (350, 220), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,0), 2)
    
    if is_tampered:
        cv2.putText(img, "Expiry: 12/12/2099", (350, 290), cv2.FONT_HERSHEY_SIMPLEX, 1, (50,50,50), 3)
    else:
        cv2.putText(img, "Expiry: 26/02/2026", (350, 290), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,0), 2)

    face = cv2.resize(cv2.imread(face_path), (250, 300))
    img[100:400, 50:300] = face
    
    cv2.putText(img, mrz1, (30, 470), cv2.FONT_HERSHEY_SIMPLEX, 1.1, (0,0,0), 3)
    cv2.putText(img, mrz2, (30, 520), cv2.FONT_HERSHEY_SIMPLEX, 1.1, (0,0,0), 3)
    
    cv2.imwrite(f"dataset/{filename}", img, [cv2.IMWRITE_JPEG_QUALITY, 80 if is_tampered else 100])
    print(f"✅ Saved: {filename}")

# --- 3. DRIVING LICENSE GENERATOR ---
def create_dl(filename, face_path, name, dl_number, is_tampered=False):
    img = np.ones((400, 700, 3), dtype=np.uint8) * 255
    img[:] = (240, 230, 200) 
    
    cv2.putText(img, "DRIVING LICENSE - UNION OF INDIA", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,200), 3)
    
    color = (50, 50, 50) if is_tampered else (0,0,0)
    thickness = 3 if is_tampered else 2
    
    cv2.putText(img, f"Name: {name}", (250, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, thickness)
    cv2.putText(img, f"DL No: {dl_number}", (250, 190), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0,0,0), 2)
    cv2.putText(img, "DOB: 12/08/1974", (250, 260), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0,0,0), 2)
    
    face = cv2.resize(cv2.imread(face_path), (180, 220))
    img[100:320, 30:210] = face
    
    cv2.imwrite(f"dataset/{filename}", img, [cv2.IMWRITE_JPEG_QUALITY, 85 if is_tampered else 100])
    print(f"✅ Saved: {filename}")

# --- 4. EXECUTE GENERATION ---
valid_mrz1 = "P<UTOERIKSSON<<ANNA<MARIA<<<<<<<<<<<<<<<<<<<"
valid_mrz2 = "L898902C36UTO7408122F1204159ZE184226B<<<<<10"
invalid_mrz2 = "L898902C36UTO9908122F1204159ZE184226B<<<<<10"

print("\n--- GENERATING PASSPORTS ---")
create_passport("pass_1_valid.jpg", "face1.jpg", valid_mrz1, valid_mrz2, bg_color=(255, 255, 255))
create_passport("pass_2_valid.jpg", "face1.jpg", valid_mrz1, valid_mrz2, bg_color=(245, 245, 250))
create_passport("pass_3_valid.jpg", "face1.jpg", valid_mrz1, valid_mrz2, bg_color=(250, 240, 240))
create_passport("pass_4_fake_math.jpg", "face1.jpg", valid_mrz1, invalid_mrz2)
create_passport("pass_5_fake_tampered.jpg", "face1.jpg", valid_mrz1, valid_mrz2, is_tampered=True)

print("\n--- GENERATING DRIVING LICENSES ---")
create_dl("dl_1_valid_MH.jpg", "face1.jpg", "ERIKSSON ANNA MARIA", "MH-12-20100001234")
create_dl("dl_2_valid_GA.jpg", "face1.jpg", "ANNA ERIKSSON", "GA-03-20220009999")
create_dl("dl_3_valid_DL.jpg", "face1.jpg", "ERIKSSON A.", "DL-01-20190005555")
create_dl("dl_4_fake_name.jpg", "face1.jpg", "FRAUDSON ANNA", "MH-12-20100001234")
create_dl("dl_5_fake_regex.jpg", "face1.jpg", "ERIKSSON ANNA", "INVALID-DL-FORMAT", is_tampered=True)

print("\n🚀 DONE! 13 Files successfully generated in the 'dataset' folder.")
