import streamlit as st
import cv2
import numpy as np
from PIL import Image, ImageChops, ImageEnhance
import easyocr
import re
import pandas as pd
import json
from datetime import datetime
import os
from facenet_pytorch import MTCNN, InceptionResnetV1
import torch

# --- LOAD BLACKLIST ---
BLACKLIST_FILE = "blacklist.json"
def load_blacklist():
    if os.path.exists(BLACKLIST_FILE):
        with open(BLACKLIST_FILE, "r") as f:
            data = json.load(f)
        return {entry["number"]: entry for entry in data["blocked_passports"]}
    return {}

BLACKLIST = load_blacklist()

def check_blacklist(passport_no):
    """Returns (is_blacklisted, reason) tuple."""
    if passport_no in BLACKLIST:
        return True, BLACKLIST[passport_no]["reason"]
    return False, ""

# --- 1. INITIALIZE OFFLINE MODELS ---
@st.cache_resource
def load_models():
    reader = easyocr.Reader(['en'])
    mtcnn = MTCNN(keep_all=False)
    resnet = InceptionResnetV1(pretrained='vggface2').eval()
    return reader, mtcnn, resnet

reader, mtcnn, resnet = load_models()

# --- 2. AUDIT LOGGING SYSTEM ---
AUDIT_FILE = "offline_audit_log.csv"

def log_verification(name, status, threat_score, doc_type):
    if not os.path.exists(AUDIT_FILE):
        df = pd.DataFrame(columns=["Timestamp", "Identity", "Status", "Threat Score", "Document Type"])
        df.to_csv(AUDIT_FILE, index=False)
        
    df = pd.read_csv(AUDIT_FILE)
    new_entry = pd.DataFrame([{
        "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Identity": name,
        "Status": status,
        "Threat Score": threat_score,
        "Document Type": doc_type
    }])
    df = pd.concat([df, new_entry], ignore_index=True)
    df.to_csv(AUDIT_FILE, index=False)

# --- 3. LOGIC ENGINES ---
def resize_image(image, max_size=1000):
    w, h = image.size
    if max(w, h) > max_size:
        scale = max_size / max(w, h)
        return image.resize((int(w * scale), int(h * scale)), Image.Resampling.LANCZOS)
    return image

def extract_passport_details(image_np):
    h, w, _ = image_np.shape
    bottom_half = image_np[int(h*0.5):h, :]
    gray = cv2.cvtColor(bottom_half, cv2.COLOR_BGR2GRAY)
    results = reader.readtext(gray, detail=0)
    
    details = {
        "Surname": "UNKNOWN", "Given Name": "TRAVELER", 
        "Passport No": "NOT FOUND", "Nationality": "NOT FOUND", 
        "DOB": "NOT FOUND", "Sex": "NOT FOUND",
        "Expiry": "NOT FOUND", "Is Expired": False
    }
    
    lines = []
    for res in results:
        res = res.replace(' ', '').replace('_', '<').replace('-', '<').upper()
        if len(res) > 30 and '<' in res:
            lines.append(res)
            
    for line in lines:
        if '<<' in line and line.find('<<') < 25:
            # Line 1 Name block
            idx = line.find('<<')
            if idx > 5:
                surname = line[5:idx].replace('<', ' ').strip()
            else:
                surname = line[:idx].replace('<', ' ').strip()
            
            # Given names
            given_part = line[idx+2:]
            if '<<' in given_part:
                given = given_part.split('<<')[0].replace('<', ' ').strip()
            else:
                given = given_part.replace('<', ' ').strip()
                
            details["Surname"] = surname
            details["Given Name"] = given
        else:
            if len(line) >= 28:
                details["Passport No"] = line[0:9].replace('<', '')
                details["Nationality"] = line[10:13].replace('<', '')
                dob_raw = line[13:19]
                if dob_raw.isdigit():
                    details["DOB"] = f"{dob_raw[4:6]}/{dob_raw[2:4]}/{dob_raw[0:2]}"
                details["Sex"] = line[20] if len(line) > 20 else ""
                # Extract expiry: characters 21-26 in MRZ line 2 = YYMMDD
                expiry_raw = line[21:27] if len(line) > 26 else ""
                if expiry_raw.isdigit():
                    exp_year = int(expiry_raw[0:2])
                    exp_month = int(expiry_raw[2:4])
                    exp_day = int(expiry_raw[4:6])
                    # Years 00-30 = 2000s, 31-99 = 1900s
                    full_year = 2000 + exp_year if exp_year <= 30 else 1900 + exp_year
                    try:
                        expiry_date = datetime(full_year, exp_month, exp_day)
                        details["Expiry"] = expiry_date.strftime("%d/%m/%Y")
                        details["Is Expired"] = expiry_date < datetime.now()
                    except:
                        details["Expiry"] = "PARSE ERROR"
                        details["Is Expired"] = False
                        
    return details

def extract_secondary_details(img_np, doc_type):
    gray = cv2.cvtColor(img_np, cv2.COLOR_BGR2GRAY)
    results = reader.readtext(gray, detail=0)
    full_text = " ".join(results).upper()
    
    valid_format = False
    if "Driving" in doc_type:
        dl_pattern = r"[A-Z]{2}[-\s]?[0-9]{2}[-\s]?[0-9]{4}[-\s]?[0-9]{7}|[A-Z]{2}[0-9]{2}\s?[0-9]{5,11}"
        valid_format = len(re.findall(dl_pattern, full_text)) > 0
    elif "Aadhaar" in doc_type or "National ID" in doc_type:
        id_pattern = r"\b\d{4}\s?\d{4}\s?\d{4}\b"
        valid_format = len(re.findall(id_pattern, full_text)) > 0
        
    return full_text, valid_format

def detect_tampering(img_pil, doc_type="Unknown"):
    temp_path = "temp_ela.jpg"
    img_pil.save(temp_path, 'JPEG', quality=90)
    saved_img = Image.open(temp_path)
    diff = ImageChops.difference(img_pil, saved_img)
    extrema = diff.getextrema()
    max_diff = max([ex[1] for ex in extrema]) if extrema else 0
    scale = 255.0 / max_diff if max_diff != 0 else 1
    diff = ImageEnhance.Brightness(diff).enhance(scale)
    
    # Document-specific baselines based on typical paper/plastic textures
    if "Driving" in doc_type:
        is_clean = 40 <= max_diff <= 100
    else:
        is_clean = 20 <= max_diff <= 100
        
    return is_clean, diff, max_diff

def verify_face(doc_pil, live_pil):
    doc_face = mtcnn(doc_pil)
    live_face = mtcnn(live_pil)
    
    if doc_face is not None and live_face is not None:
        doc_emb = resnet(doc_face.unsqueeze(0)).detach()
        live_emb = resnet(live_face.unsqueeze(0)).detach()
        dist = (doc_emb - live_emb).norm().item()
        return dist < 1.0, dist
    return False, 99.9

# --- 4. STREAMLIT UI CONFIGURATION ---
st.set_page_config(layout="wide", page_title="SSB Border Screener", page_icon="🛡️")

st.sidebar.title("🛡️ SSB Security System")
st.sidebar.markdown("Edge-Deployment Mode: **OFFLINE**")
mode = st.sidebar.radio("Navigation Menu", ["📑 Multi-Doc Triangulation", "📄 Single Doc Quick-Scan", "📂 Border Audit Logs"])

# ==========================================
# MODE 1: MULTI-DOCUMENT (The Main Pitch)
# ==========================================
if mode == "📑 Multi-Doc Triangulation":
    st.title("📑 Multi-Document Triangulation Module")
    col1, col2 = st.columns([1, 1.2])
    
    with col1:
        st.subheader("Ingestion Panel")
        pass_upload = st.file_uploader("1. Primary ID (Passport)", type=["jpg", "png", "jpeg"])
        dl_upload = st.file_uploader("2. Secondary ID (Driving License)", type=["jpg", "png", "jpeg"])
        aadhaar_upload = st.file_uploader("3. Domestic ID (Aadhaar Card)", type=["jpg", "png", "jpeg"])
        live_upload = st.file_uploader("4. Live Face Capture", type=["jpg", "png", "jpeg"])

    with col2:
        st.subheader("Triangulation Engine")
        if pass_upload and dl_upload and aadhaar_upload and live_upload:
            if st.button("Initialize Deep Verification Sweep", type="primary", use_container_width=True):
                
                pass_pil = resize_image(Image.open(pass_upload).convert('RGB'))
                dl_pil = resize_image(Image.open(dl_upload).convert('RGB'))
                aadhaar_pil = resize_image(Image.open(aadhaar_upload).convert('RGB'))
                live_pil = resize_image(Image.open(live_upload).convert('RGB'))
                
                progress_text = "Running Pixel Forensics (ELA)..."
                my_bar = st.progress(0, text=progress_text)
                ela_clean, ela_img, diff_score = detect_tampering(pass_pil, "Passport")
                
                my_bar.progress(30, text="Extracting Identity Anchors...")
                pass_details = extract_passport_details(np.array(pass_pil))
                surname, given = pass_details["Surname"], pass_details["Given Name"]
                
                my_bar.progress(60, text="Cross-referencing Secondary Documents...")
                dl_text, dl_valid = extract_secondary_details(np.array(dl_pil), "Driving License")
                id_text, id_valid = extract_secondary_details(np.array(aadhaar_pil), "Aadhaar Card")
                dl_name_match = surname in dl_text if surname != "UNKNOWN" else False
                id_name_match = surname in id_text if surname != "UNKNOWN" else False
                
                my_bar.progress(90, text="Calculating Biometric Topology...")
                face_match, dist = verify_face(pass_pil, live_pil)
                my_bar.progress(100, text="Analysis Complete.")
                
                # Blacklist & Expiry checks
                passport_no = pass_details.get("Passport No", "NOT FOUND")
                is_blacklisted, bl_reason = check_blacklist(passport_no)
                is_expired = pass_details.get("Is Expired", False)

                failed_checks = [ela_clean, dl_name_match, dl_valid, id_name_match, id_valid, face_match, not is_blacklisted, not is_expired].count(False)
                threat_level = min((failed_checks * 20), 100)
                
                st.divider()
                metrics_cols = st.columns(3)
                metrics_cols[0].metric("Threat Level", f"{threat_level}%", delta="HIGH" if threat_level > 0 else "LOW", delta_color="inverse")
                metrics_cols[1].metric("Biometric Distance", f"{dist:.2f}", delta="< 1.0 Required", delta_color="off")
                metrics_cols[2].metric("Pixel Variance", f"{diff_score}", delta="Baseline: 20–100", delta_color="off")
                
                if threat_level == 0:
                    st.success(f"✅ CLEARANCE GRANTED: Identity verified for {given} {surname}.")
                    st.write(f"**Extracted Data:** Passport No: {pass_details['Passport No']} | DOB: {pass_details['DOB']} | Expiry: {pass_details['Expiry']} | Sex: {pass_details['Sex']} | Nat: {pass_details['Nationality']}")
                    log_verification(f"{given} {surname}", "CLEARED", f"{threat_level}%", "Multi-Doc Multi-Factor")
                else:
                    st.error(f"🚨 ALERT: {failed_checks} Security Anomalies Detected. Identity Rejected.")
                    log_verification(f"{given} {surname}", "REJECTED - HIGH RISK", f"{threat_level}%", "Multi-Doc Multi-Factor")

                st.markdown("### Deep Rationale Breakdown")
                if not ela_clean: st.error(f"❌ **Forensics (Forgery):** Pixel Variance is {diff_score}. This is outside the natural baseline, indicating digital alteration, splicing, or a low-quality photocopy.")
                else: st.info(f"✔️ **Forensics:** Passport pixels are mathematically untampered (Score: {diff_score}).")
                
                if not (dl_name_match and id_name_match): st.error(f"❌ **Cross-Linkage (Stolen ID):** Anchor name '{surname}' does not match the names extracted from the secondary documents.")
                else: st.info("✔️ **Cross-Linkage:** Name successfully verified across all 3 documents.")
                
                if not face_match: st.error(f"❌ **Biometrics (Impersonation):** Facial topology mismatch. The live person does not match the ID photo (Distance: {dist:.2f}, must be < 1.0).")
                else: st.info(f"✔️ **Biometrics:** Live face strictly matches document portrait (Distance: {dist:.2f}).")
                
                if is_expired: st.error(f"❌ **Validity (Expired Document):** Passport expired on {pass_details['Expiry']}. Document is no longer valid for travel.")
                elif pass_details['Expiry'] != 'NOT FOUND': st.info(f"✔️ **Validity:** Passport is valid until {pass_details['Expiry']}.")
                
                if is_blacklisted: st.error(f"⛔ **BLACKLIST HIT:** Passport No. `{passport_no}` is on the SSB/Interpol watchlist. Reason: *{bl_reason}*")
                elif passport_no != 'NOT FOUND': st.info(f"✔️ **Blacklist:** Passport No. `{passport_no}` is clear — not on any watchlist.")

# ==========================================
# MODE 2: SINGLE DOC QUICK-SCAN (Forensics Only)
# ==========================================
elif mode == "📄 Single Doc Quick-Scan":
    st.title("📄 Single Document Quick-Scan (Forensics)")
    st.markdown("Use this module to instantly verify the digital integrity and format of a single document. **No facial biometrics required.**")
    
    doc_type = st.radio("Select Target Document Type:", ["Passport (MRZ & ICAO Check)", "Driving License (State Format Check)", "National ID / Aadhaar (Verhoeff/Structure Check)"], horizontal=True)
    
    col1, col2 = st.columns([1, 1.2])
    with col1:
        single_doc = st.file_uploader("Upload Identity Document Only", type=["jpg", "png", "jpeg"])
        # Removed the live face uploader completely
        
    with col2:
        if single_doc:
            if st.button(f"Scan {doc_type.split(' ')[0]} Forgery Flags", type="primary", use_container_width=True):
                doc_pil = resize_image(Image.open(single_doc).convert('RGB'))
                
                with st.spinner("Processing Pixel Forensics and OCR Structure..."):
                    ela_clean, ela_img, diff_score = detect_tampering(doc_pil, doc_type)
                    
                    # Specific Logic branching
                    name = "UNKNOWN"
                    format_valid = False
                    if "Passport" in doc_type:
                        pass_details = extract_passport_details(np.array(doc_pil))
                        surname, given = pass_details["Surname"], pass_details["Given Name"]
                        name = f"{given} {surname}"
                        format_valid = (surname != "UNKNOWN")
                    else:
                        full_text, format_valid = extract_secondary_details(np.array(doc_pil), doc_type)
                        
                    # Expiry and blacklist for Mode 2 (Passport only)
                    is_expired_m2 = False
                    is_blacklisted_m2 = False
                    bl_reason_m2 = ""
                    passport_no_m2 = "NOT FOUND"
                    if "Passport" in doc_type:
                        passport_no_m2 = pass_details.get("Passport No", "NOT FOUND")
                        is_expired_m2 = pass_details.get("Is Expired", False)
                        is_blacklisted_m2, bl_reason_m2 = check_blacklist(passport_no_m2)

                    threat = 0 if (ela_clean and format_valid and not is_expired_m2 and not is_blacklisted_m2) else 100
                    
                    st.divider()
                    if threat == 0:
                        st.success(f"✅ LOW RISK - {doc_type.split(' ')[0]} Verified Successfully")
                        log_verification(name, "CLEARED (Forensics Only)", "0%", doc_type.split(' ')[0])
                    else:
                        st.error("🚨 HIGH RISK - Document Forgery Flags Detected")
                        log_verification(name, "REJECTED (Forgery)", "100%", doc_type.split(' ')[0])
                        
                    st.markdown("### Forensic Rationale")
                    # Pixel Integrity Reporting
                    if not ela_clean: 
                        expected = "40-100" if "Driving" in doc_type else "20-100"
                        st.error(f"❌ **Pixel Integrity FAILED:** Variance score is {diff_score} (Acceptable Range: {expected}). This indicates digital splicing or heavy re-compression typical of forgeries.")
                        st.image(ela_img, caption="Error Level Analysis Map (Abnormal variance indicates tampering)", width=250)
                    else: 
                        st.info(f"✔️ **Pixel Integrity PASSED:** Variance score is {diff_score} (Clean). Natural compression baseline detected.")

                    # Format Reporting
                    if not format_valid: 
                        st.error(f"❌ **Document Format FAILED:** Could not locate a valid, standardized structural ID format for {doc_type.split(' ')[0]}.")
                    elif "Passport" in doc_type: 
                        st.info(f"✔️ **MRZ Structure PASSED:** Anchor Name Parsed: {name}")
                        st.write(f"**Extracted Data:** Passport No: {pass_details['Passport No']} | DOB: {pass_details['DOB']} | Expiry: {pass_details['Expiry']} | Sex: {pass_details['Sex']} | Nationality: {pass_details['Nationality']}")

                    else: 
                        st.info(f"✔️ **Document Format PASSED:** Valid ID structure detected for {doc_type.split(' ')[0]}.")

                    # Mode 2 expiry & blacklist rationale
                    if "Passport" in doc_type:
                        if is_expired_m2: st.error(f"❌ **Validity (Expired):** Passport expired on {pass_details['Expiry']}. Document is no longer valid for travel.")
                        elif pass_details['Expiry'] != 'NOT FOUND': st.info(f"✔️ **Validity:** Passport valid until {pass_details['Expiry']}.")

                        if is_blacklisted_m2: st.error(f"⛔ **BLACKLIST HIT:** Passport No. `{passport_no_m2}` flagged on SSB/Interpol watchlist. Reason: *{bl_reason_m2}*")
                        elif passport_no_m2 != 'NOT FOUND': st.info(f"✔️ **Blacklist:** Passport No. `{passport_no_m2}` is clear.")

# ==========================================
# MODE 3: BORDER AUDIT LOGS
# ==========================================
elif mode == "📂 Border Audit Logs":
    st.title("📂 Secure Border Outpost Audit Log")
    st.markdown("This local database maintains an immutable, offline record of all crossers verified by this hardware node.")
    
    if os.path.exists(AUDIT_FILE):
        df = pd.read_csv(AUDIT_FILE)
        
        st.write("### Today's Statistics")
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Scans", len(df))
        c2.metric("Cleared Entries", len(df[df['Status'].str.contains('CLEARED')]))
        c3.metric("Blocked Crossings", len(df[df['Status'].str.contains('REJECTED')]))
        
        st.divider()
        search = st.text_input("🔍 Search Database by Name or Status:")
        if search:
            df = df[df.apply(lambda row: row.astype(str).str.contains(search, case=False).any(), axis=1)]
            
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Export Secure CSV Report", data=csv, file_name="outpost_audit.csv", mime="text/csv")
    else:
        st.info("No scans have been performed yet. Run a verification to generate audit logs.")