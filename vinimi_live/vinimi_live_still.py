#!/usr/bin/env python
# coding: utf-8

# In[5]:


import os
import pymysql
from pymysql.cursors import DictCursor

LOCAL_DB_HOST = os.getenv("LOCAL_DB_HOST", "127.0.0.1")
LOCAL_DB_PORT = int(os.getenv("LOCAL_DB_PORT", "3306"))
LOCAL_DB_USER = os.getenv("LOCAL_DB_USER", "root")
LOCAL_DB_PASS = os.getenv("LOCAL_DB_PASS", "Rajini@123")
LOCAL_DB_NAME = os.getenv("LOCAL_DB_NAME", "vinimi_local")


def getconn():
    return pymysql.connect(
        host=LOCAL_DB_HOST,
        port=LOCAL_DB_PORT,
        user=LOCAL_DB_USER,
        password=LOCAL_DB_PASS,
        database=LOCAL_DB_NAME,
        charset="utf8mb4",
        cursorclass=DictCursor,
        autocommit=True,
    )

# Test the connection and fetch table names
conn = getconn()
cursor = conn.cursor()
cursor.execute("SHOW TABLES;")
print(cursor.fetchall())
cursor.close()
conn.close()


# In[6]:


from PIL import Image, ImageDraw
import matplotlib.pyplot as plt

def create_tick_icon(size=256):
    img = Image.new('RGBA', (size, size), (0,0,0,0))
    draw = ImageDraw.Draw(img)
    # Green circle background
    draw.ellipse([16,16,size-16,size-16], fill=(0,200,0,230), outline=(255,255,255,255), width=8)
    # White tick mark
    tick = [
        (size*0.35, size*0.65),
        (size*0.50, size*0.80),
        (size*0.75, size*0.30)
    ]
    draw.line(tick, fill=(255,255,255,255), width=22, joint="curve")
    return img

def create_cross_icon(size=256):
    img = Image.new('RGBA', (size, size), (0,0,0,0))
    draw = ImageDraw.Draw(img)
    # Red circle background
    draw.ellipse([16,16,size-16,size-16], fill=(220,0,0,230), outline=(255,255,255,255), width=8)
    # White cross (X)
    cross1 = [(size*0.32, size*0.32), (size*0.68, size*0.68)]
    cross2 = [(size*0.68, size*0.32), (size*0.32, size*0.68)]
    draw.line(cross1, fill=(255,255,255,255), width=20)
    draw.line(cross2, fill=(255,255,255,255), width=20)
    return img

# Create icons
tick_img = create_tick_icon()
cross_img = create_cross_icon()

# Display icons in notebook output
plt.figure(figsize=(4,2))
plt.subplot(1,2,1)
plt.imshow(tick_img)
plt.axis('off')
plt.title('Tick')

plt.subplot(1,2,2)
plt.imshow(cross_img)
plt.axis('off')
plt.title('Cross')

plt.tight_layout()
plt.show()


# In[9]:


get_ipython().system('pip install opencv-python pandas deepface ultralytics pillow')


# In[21]:


import cv2
import numpy as np
import os
from ultralytics import YOLO
from deepface import DeepFace
import pandas as pd
from datetime import datetime
from PIL import Image, ImageDraw
import pymysql

# --- DB CONFIG ---
MODEL_PATH = "/Users/rajiniboini/Desktop/projectV/v2.0/backendlive/vinimi_live/best.pt"

def get_table_as_df(table_name):
    conn = getconn()
    df = pd.read_sql(f"SELECT * FROM {table_name}", conn)
    conn.close()
    return df

# Load DB data to RAM
emb_df = get_table_as_df("embeddings")
filenames = emb_df['filename'].values
asset_ids = emb_df['asset_id'].values
embeddings = np.vstack([np.fromstring(str(row["embedding"]), sep=',') for _, row in emb_df.iterrows()])

image_df = get_table_as_df("image")
worker_df = get_table_as_df("worker")
location_df = get_table_as_df("location")

meta = image_df.merge(worker_df[['id', 'phone']], left_on="worker_id", right_on="id", how="left")
meta = meta.merge(location_df[['id', 'name', 'address']], left_on="location_id", right_on="id", how="left", suffixes=('', '_location'))
imageid_to_info = {}
for _, row in meta.iterrows():
    imageid = row['asset_id'] if pd.notnull(row['asset_id']) else os.path.splitext(row['filename'])[0]
    imageid_to_info[imageid] = {
        'name': row.get('name', 'Unknown'),
        'phone': row.get('phone', 'Unknown'),
        'location': row.get('name_location', 'Unknown'),
        'address': row.get('address', 'Unknown')
    }

# Icons in-memory
def create_tick_icon(size=64):
    img = Image.new('RGBA', (size, size), (0,0,0,0))
    draw = ImageDraw.Draw(img)
    draw.ellipse([8,8,size-8,size-8], fill=(0,200,0,230), outline=(255,255,255,255), width=4)
    tick = [
        (size*0.35, size*0.65),
        (size*0.50, size*0.80),
        (size*0.75, size*0.30)
    ]
    draw.line(tick, fill=(255,255,255,255), width=int(size/12), joint="curve")
    return np.array(img)

def create_cross_icon(size=64):
    img = Image.new('RGBA', (size, size), (0,0,0,0))
    draw = ImageDraw.Draw(img)
    draw.ellipse([8,8,size-8,size-8], fill=(220,0,0,230), outline=(255,255,255,255), width=4)
    cross1 = [(size*0.32, size*0.32), (size*0.68, size*0.68)]
    cross2 = [(size*0.68, size*0.32), (size*0.32, size*0.68)]
    draw.line(cross1, fill=(255,255,255,255), width=int(size/12))
    draw.line(cross2, fill=(255,255,255,255), width=int(size/12))
    return np.array(img)

def overlay_icon_bgr(frame, icon_rgba, x, y):
    h, w = icon_rgba.shape[:2]
    alpha = icon_rgba[:,:,3] / 255.0
    for c in range(3):
        frame[y:y+h, x:x+w, c] = (alpha * icon_rgba[:,:,c] + (1-alpha) * frame[y:y+h, x:x+w, c]).astype(np.uint8)
    return frame

def cosine_sim_vectorized(query_emb, gallery_mat):
    q = np.asarray(query_emb, dtype=np.float32)
    q = q / (np.linalg.norm(q) + 1e-8)
    G = np.array(gallery_mat) / (np.linalg.norm(gallery_mat, axis=1, keepdims=True) + 1e-8)
    return np.dot(G, q)

def recognize_face_live(frame):
    temp_path = "live_temp_face.jpg"
    cv2.imwrite(temp_path, frame)
    FACE_SIM_THRESHOLD = 0.3
    try:
        results = DeepFace.represent(img_path=temp_path, model_name='VGG-Face', enforce_detection=True)
        if results and isinstance(results, list):
            emb = np.array(results[0]["embedding"], dtype=np.float32)
            emb = emb / (np.linalg.norm(emb) + 1e-8)
            sims = cosine_sim_vectorized(emb, embeddings)
            best_idx = int(np.argmax(sims))
            best_sim = float(sims[best_idx])
            if best_sim >= FACE_SIM_THRESHOLD:
                found_asset_id = asset_ids[best_idx]
                found_info = imageid_to_info.get(found_asset_id, {
                    "name": "Unknown", "phone": "Unknown", "location": "Unknown", "address": "Unknown"})
            else:
                found_info = {"name": "Unknown", "phone": "Unknown", "location": "Unknown", "address": "Unknown"}
        else:
            found_info = {"name": "Unknown", "phone": "Unknown", "location": "Unknown", "address": "Unknown"}
    except Exception:
        found_info = {"name": "Unknown", "phone": "Unknown", "location": "Unknown", "address": "Unknown"}
    finally:
        if os.path.exists(temp_path): os.remove(temp_path)
    return found_info

def helmet_detect_live(frame, model, confidence=0.25):
    results = model(frame, conf=confidence)
    helmet_on = False
    best_conf = 0.0
    best_label = None
    best_box = None
    res = results[0] if results and len(results)>0 else None
    if res and hasattr(res, "boxes") and res.boxes is not None:
        names = res.names
        for box in res.boxes:
            conf = float(box.conf[0].item())
            cls_id = int(box.cls[0].item())
            label = names[cls_id]
            xyxy = box.xyxy[0].cpu().numpy().astype(int)
            if conf > best_conf:
                best_conf = conf
                best_label = label
                best_box = xyxy
        if best_box is not None and best_label is not None:
            norm_label = best_label.lower().replace("-", "").replace("_", "")
            if ("no" not in norm_label) and (("hardhat" in norm_label) or ("helmet" in norm_label)):
                helmet_on = True
    return helmet_on

model = YOLO(MODEL_PATH)
tick_icon = create_tick_icon()
cross_icon = create_cross_icon()

# Logging session
log_records, last_logged, unknown_counter, unknown_frames = [], set(), {}, {}
BUFFER_UNKNOWN_FRAMES = 3
cap = cv2.VideoCapture(0)
frame_num = 0

try:
    while True:
        ret, frame = cap.read()
        if not ret: break
        display_frame = frame.copy()
        if frame_num % 30 == 0:
            person_info = recognize_face_live(frame)
            helmet_status = helmet_detect_live(frame, model)
            person_id = f"{person_info['name']}_{person_info['phone']}"
            # Unknown (DB insert logic)
            if person_info['name'] == "Unknown":
                unknown_counter[person_id] = unknown_counter.get(person_id, 0) + 1
                if person_id not in unknown_frames: unknown_frames[person_id] = []
                unknown_frames[person_id].append(frame.copy())
                if unknown_counter[person_id] == BUFFER_UNKNOWN_FRAMES:
                    print("ALERT: Unknown 3x – prompt add-to-db here!")
                    # Add popup/UI and DB-insert logic here if desired
            else:
                unknown_counter[person_id] = 0
                unknown_frames.pop(person_id, None)
            # Deduplication
            if person_id not in last_logged:
                log_entry = {
                    "timestamp": datetime.now(),
                    "name": person_info["name"],
                    "phone": person_info["phone"],
                    "location": person_info["location"],
                    "address": person_info["address"],
                    "helmet_on": bool(helmet_status)
                }
                log_records.append(log_entry)
                last_logged.add(person_id)
        # Display
        icon = tick_icon if helmet_status else cross_icon
        display_frame = overlay_icon_bgr(display_frame, icon, 10, 10)
        cv2.putText(display_frame, f"Name: {person_info['name']}", (30, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,255,255), 2)
        cv2.putText(display_frame, f"Phone: {person_info['phone']}", (30, 135), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,255,255), 2)
        cv2.putText(display_frame, f"Loc: {person_info['location']}", (30, 170), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,255,255), 2)
        cv2.putText(display_frame, f"Addr: {person_info['address']}", (30, 205), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,255,255), 2)
        status_txt = "HELMET ON" if helmet_status else "NO HELMET"
        cv2.putText(display_frame, status_txt, (30, 240), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0) if helmet_status else (0,0,255), 2)
        cv2.imshow("Live VLM Safety", display_frame)
        if cv2.waitKey(1) & 0xFF == ord('q'): break
        frame_num += 1
finally:
    cap.release()
    cv2.destroyAllWindows()
    # Save log to CSV at end
    log_df = pd.DataFrame(log_records)
    log_df.to_csv("session_log.csv", index=False)
    print("Session CSV saved as session_log.csv")

import matplotlib.pyplot as plt

cv2.namedWindow("Live VLM Safety", cv2.WINDOW_NORMAL)
cv2.setWindowProperty("Live VLM Safety", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

unknown_images_to_show = []

try:
    while True:
        ret, frame = cap.read()
        if not ret: break
        display_frame = frame.copy()
        if frame_num % 30 == 0:
            person_info = recognize_face_live(frame)
            helmet_status = helmet_detect_live(frame, model)
            person_id = f"{person_info['name']}_{person_info['phone']}"
            # Unknown logic (show, store images)
            if person_info['name'] == "Unknown":
                unknown_counter[person_id] = unknown_counter.get(person_id, 0) + 1
                if person_id not in unknown_frames: unknown_frames[person_id] = []
                unknown_frames[person_id].append(frame.copy())
                if unknown_counter[person_id] == BUFFER_UNKNOWN_FRAMES:
                    print("ALERT: Unknown 3x – prompt add-to-db here!")
                    # For end-of-session display:
                    unknown_images_to_show = unknown_frames[person_id][-3:]
            else:
                unknown_counter[person_id] = 0
                unknown_frames.pop(person_id, None)
            # Deduplication
            if person_id not in last_logged:
                log_entry = {
                    "timestamp": datetime.now(),
                    "name": person_info["name"],
                    "phone": person_info["phone"],
                    "location": person_info["location"],
                    "address": person_info["address"],
                    "helmet_on": bool(helmet_status)
                }
                log_records.append(log_entry)
                last_logged.add(person_id)
        # Display
        icon = tick_icon if helmet_status else cross_icon
        display_frame = overlay_icon_bgr(display_frame, icon, 10, 10)
        cv2.putText(display_frame, f"Name: {person_info['name']}", (30, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,255,255), 2)
        cv2.putText(display_frame, f"Phone: {person_info['phone']}", (30, 135), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,255,255), 2)
        cv2.putText(display_frame, f"Loc: {person_info['location']}", (30, 170), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,255,255), 2)
        cv2.putText(display_frame, f"Addr: {person_info['address']}", (30, 205), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,255,255), 2)
        status_txt = "HELMET ON" if helmet_status else "NO HELMET"
        cv2.putText(display_frame, status_txt, (30, 240), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0) if helmet_status else (0,0,255), 2)
        cv2.imshow("Live VLM Safety", display_frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
        frame_num += 1
finally:
    cap.release()
    cv2.destroyAllWindows()
    # Save log to CSV at end
    log_df = pd.DataFrame(log_records)
    log_df.to_csv("session_log.csv", index=False)
    print("Session CSV saved as session_log.csv")

# After quitting, display unknown faces
if unknown_images_to_show:
    print("Three frames of the unknown person:")
    plt.figure(figsize=(15,5))
    for idx, img in enumerate(unknown_images_to_show):
        plt.subplot(1, 3, idx+1)
        plt.imshow(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        plt.title(f"Unknown #{idx+1}")
        plt.axis('off')
    plt.show()


# In[17]:


import pandas as pd

# Load the session log
log_df = pd.read_csv("session_log.csv")

# Show the DataFrame contents
print(log_df)


# In[ ]:





# In[23]:


import cv2
import numpy as np
import os
from ultralytics import YOLO
from deepface import DeepFace
import pandas as pd
from datetime import datetime
from PIL import Image, ImageDraw
import matplotlib.pyplot as plt
import pymysql

# Load DB data to RAM
emb_df = get_table_as_df("embeddings")
filenames = emb_df['filename'].values
asset_ids = emb_df['asset_id'].values
embeddings = np.vstack([np.fromstring(str(row["embedding"]), sep=',') for _, row in emb_df.iterrows()])

image_df = get_table_as_df("image")
worker_df = get_table_as_df("worker")
location_df = get_table_as_df("location")

meta = image_df.merge(worker_df[['id', 'phone']], left_on="worker_id", right_on="id", how="left")
meta = meta.merge(location_df[['id', 'name', 'address']], left_on="location_id", right_on="id", how="left", suffixes=('', '_location'))
imageid_to_info = {}
for _, row in meta.iterrows():
    imageid = row['asset_id'] if pd.notnull(row['asset_id']) else os.path.splitext(row['filename'])[0]
    imageid_to_info[imageid] = {
        'name': row.get('name', 'Unknown'),
        'phone': row.get('phone', 'Unknown'),
        'location': row.get('name_location', 'Unknown'),
        'address': row.get('address', 'Unknown')
    }

def create_tick_icon(size=64):
    img = Image.new('RGBA', (size, size), (0,0,0,0))
    draw = ImageDraw.Draw(img)
    draw.ellipse([8,8,size-8,size-8], fill=(0,200,0,230), outline=(255,255,255,255), width=4)
    tick = [
        (size*0.35, size*0.65),
        (size*0.50, size*0.80),
        (size*0.75, size*0.30)
    ]
    draw.line(tick, fill=(255,255,255,255), width=int(size/12), joint="curve")
    return np.array(img)

def create_cross_icon(size=64):
    img = Image.new('RGBA', (size, size), (0,0,0,0))
    draw = ImageDraw.Draw(img)
    draw.ellipse([8,8,size-8,size-8], fill=(220,0,0,230), outline=(255,255,255,255), width=4)
    cross1 = [(size*0.32, size*0.32), (size*0.68, size*0.68)]
    cross2 = [(size*0.68, size*0.32), (size*0.32, size*0.68)]
    draw.line(cross1, fill=(255,255,255,255), width=int(size/12))
    draw.line(cross2, fill=(255,255,255,255), width=int(size/12))
    return np.array(img)

def overlay_icon_bgr(frame, icon_rgba, x, y):
    h, w = icon_rgba.shape[:2]
    alpha = icon_rgba[:,:,3] / 255.0
    for c in range(3):
        frame[y:y+h, x:x+w, c] = (alpha * icon_rgba[:,:,c] + (1-alpha) * frame[y:y+h, x:x+w, c]).astype(np.uint8)
    return frame

def cosine_sim_vectorized(query_emb, gallery_mat):
    q = np.asarray(query_emb, dtype=np.float32)
    q = q / (np.linalg.norm(q) + 1e-8)
    G = np.array(gallery_mat) / (np.linalg.norm(gallery_mat, axis=1, keepdims=True) + 1e-8)
    return np.dot(G, q)

def recognize_face_live(frame):
    temp_path = "live_temp_face.jpg"
    cv2.imwrite(temp_path, frame)
    FACE_SIM_THRESHOLD = 0.3
    try:
        results = DeepFace.represent(img_path=temp_path, model_name='VGG-Face', enforce_detection=True)
        if results and isinstance(results, list):
            emb = np.array(results[0]["embedding"], dtype=np.float32)
            emb = emb / (np.linalg.norm(emb) + 1e-8)
            sims = cosine_sim_vectorized(emb, embeddings)
            best_idx = int(np.argmax(sims))
            best_sim = float(sims[best_idx])
            if best_sim >= FACE_SIM_THRESHOLD:
                found_asset_id = asset_ids[best_idx]
                found_info = imageid_to_info.get(found_asset_id, {
                    "name": "Unknown", "phone": "Unknown", "location": "Unknown", "address": "Unknown"})
            else:
                found_info = {"name": "Unknown", "phone": "Unknown", "location": "Unknown", "address": "Unknown"}
        else:
            found_info = {"name": "Unknown", "phone": "Unknown", "location": "Unknown", "address": "Unknown"}
    except Exception:
        found_info = {"name": "Unknown", "phone": "Unknown", "location": "Unknown", "address": "Unknown"}
    finally:
        if os.path.exists(temp_path): os.remove(temp_path)
    return found_info

def helmet_detect_live(frame, model, confidence=0.25):
    results = model(frame, conf=confidence)
    helmet_on = False
    best_conf = 0.0
    best_label = None
    best_box = None
    res = results[0] if results and len(results)>0 else None
    if res and hasattr(res, "boxes") and res.boxes is not None:
        names = res.names
        for box in res.boxes:
            conf = float(box.conf[0].item())
            cls_id = int(box.cls[0].item())
            label = names[cls_id]
            xyxy = box.xyxy[0].cpu().numpy().astype(int)
            if conf > best_conf:
                best_conf = conf
                best_label = label
                best_box = xyxy
        if best_box is not None and best_label is not None:
            norm_label = best_label.lower().replace("-", "").replace("_", "")
            if ("no" not in norm_label) and (("hardhat" in norm_label) or ("helmet" in norm_label)):
                helmet_on = True
    return helmet_on

model = YOLO(MODEL_PATH)
tick_icon = create_tick_icon()
cross_icon = create_cross_icon()

# Logging/session
log_records, last_logged, unknown_counter, unknown_frames = [], set(), {}, {}
BUFFER_UNKNOWN_FRAMES = 3
frame_num = 0
unknown_images_to_show = []
cap = cv2.VideoCapture(0)

cv2.namedWindow("Live VLM Safety", cv2.WINDOW_NORMAL)
try:
    cv2.setWindowProperty("Live VLM Safety", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
except Exception:
    cv2.resizeWindow("Live VLM Safety", 1920, 1080)

try:
    while True:
        ret, frame = cap.read()
        if not ret: break
        display_frame = frame.copy()
        if frame_num % 30 == 0:
            person_info = recognize_face_live(frame)
            helmet_status = helmet_detect_live(frame, model)
            person_id = f"{person_info['name']}_{person_info['phone']}"
            if person_info['name'] == "Unknown":
                unknown_counter[person_id] = unknown_counter.get(person_id, 0) + 1
                if person_id not in unknown_frames: unknown_frames[person_id] = []
                unknown_frames[person_id].append(frame.copy())
                if unknown_counter[person_id] == BUFFER_UNKNOWN_FRAMES:
                    print("ALERT: Unknown 3x – prompt add-to-db here!")
                    unknown_images_to_show = unknown_frames[person_id][-3:]
            else:
                unknown_counter[person_id] = 0
                unknown_frames.pop(person_id, None)
            if person_id not in last_logged:
                log_entry = {
                    "timestamp": datetime.now(),
                    "name": person_info["name"],
                    "phone": person_info["phone"],
                    "location": person_info["location"],
                    "address": person_info["address"],
                    "helmet_on": bool(helmet_status)
                }
                log_records.append(log_entry)
                last_logged.add(person_id)
        icon = tick_icon if helmet_status else cross_icon
        display_frame = overlay_icon_bgr(display_frame, icon, 10, 10)
        cv2.putText(display_frame, f"Name: {person_info['name']}", (30, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,255,255), 2)
        cv2.putText(display_frame, f"Phone: {person_info['phone']}", (30, 135), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,255,255), 2)
        cv2.putText(display_frame, f"Loc: {person_info['location']}", (30, 170), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,255,255), 2)
        cv2.putText(display_frame, f"Addr: {person_info['address']}", (30, 205), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,255,255), 2)
        status_txt = "HELMET ON" if helmet_status else "NO HELMET"
        cv2.putText(display_frame, status_txt, (30, 240), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0) if helmet_status else (0,0,255), 2)
        cv2.imshow("Live VLM Safety", display_frame)
        if cv2.waitKey(1) & 0xFF == ord('q'): break
        frame_num += 1
finally:
    cap.release()
    cv2.destroyAllWindows()
    log_df = pd.DataFrame(log_records)
    log_df.to_csv("session_log.csv", index=False)
    print("Session CSV saved as session_log.csv")

if unknown_images_to_show:
    print("Three frames of the unknown person:")
    plt.figure(figsize=(15,5))
    for idx, img in enumerate(unknown_images_to_show):
        plt.subplot(1, 3, idx+1)
        plt.imshow(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        plt.title(f"Unknown #{idx+1}")
        plt.axis('off')
    plt.show()


# In[ ]:





# In[ ]:





# In[ ]:





# In[43]:


print("Worker Columns:", worker_df.columns)
print("Image Columns:", image_df.columns)
print("Company Columns:", company_df.columns)


# In[ ]:





# In[ ]:





# In[75]:


import cv2
import numpy as np
import os
from ultralytics import YOLO
from deepface import DeepFace
import pandas as pd
from datetime import datetime
from PIL import Image, ImageDraw
import matplotlib.pyplot as plt
import pymysql

# Load DB data to RAM
emb_df = get_table_as_df("embeddings")
filenames = emb_df['filename'].values
asset_ids = emb_df['asset_id'].values
embeddings = np.vstack([np.fromstring(str(row["embedding"]), sep=',') for _, row in emb_df.iterrows()])

image_df = get_table_as_df("image")
worker_df = get_table_as_df("worker")
location_df = get_table_as_df("location")

# Correct meta merge for company inclusion
meta = image_df.merge(
    worker_df[['id', 'phone', 'company_id']], left_on="worker_id", right_on="id", how="left", suffixes=('', '_worker')
).merge(
    location_df[['id', 'name', 'address']], left_on="location_id", right_on="id", how="left", suffixes=('', '_location')
).merge(
    get_table_as_df('company')[['id', 'name']], left_on="company_id", right_on="id", how="left", suffixes=('', '_company')
)

imageid_to_info = {}
for _, row in meta.iterrows():
    imageid = row['asset_id'] if pd.notnull(row['asset_id']) else os.path.splitext(row['filename'])[0]
    imageid_to_info[imageid] = {
        'name': row.get('name', 'Unknown'),
        'phone': row.get('phone', 'Unknown'),
        'location': row.get('name_location', 'Unknown'),
        'address': row.get('address', 'Unknown'),
        'company': row.get('name_company', 'Unknown')
    }


def create_tick_icon(size=64):
    img = Image.new('RGBA', (size, size), (0,0,0,0))
    draw = ImageDraw.Draw(img)
    draw.ellipse([8,8,size-8,size-8], fill=(0,200,0,230), outline=(255,255,255,255), width=4)
    tick = [
        (size*0.35, size*0.65),
        (size*0.50, size*0.80),
        (size*0.75, size*0.30)
    ]
    draw.line(tick, fill=(255,255,255,255), width=int(size/12), joint="curve")
    return np.array(img)

def create_cross_icon(size=64):
    img = Image.new('RGBA', (size, size), (0,0,0,0))
    draw = ImageDraw.Draw(img)
    draw.ellipse([8,8,size-8,size-8], fill=(220,0,0,230), outline=(255,255,255,255), width=4)
    cross1 = [(size*0.32, size*0.32), (size*0.68, size*0.68)]
    cross2 = [(size*0.68, size*0.32), (size*0.32, size*0.68)]
    draw.line(cross1, fill=(255,255,255,255), width=int(size/12))
    draw.line(cross2, fill=(255,255,255,255), width=int(size/12))
    return np.array(img)

def overlay_icon_bgr(frame, icon_rgba, x, y):
    h, w = icon_rgba.shape[:2]
    alpha = icon_rgba[:,:,3] / 255.0
    for c in range(3):
        frame[y:y+h, x:x+w, c] = (alpha * icon_rgba[:,:,c] + (1-alpha) * frame[y:y+h, x:x+w, c]).astype(np.uint8)
    return frame

def cosine_sim_vectorized(query_emb, gallery_mat):
    q = np.asarray(query_emb, dtype=np.float32)
    q = q / (np.linalg.norm(q) + 1e-8)
    G = np.array(gallery_mat) / (np.linalg.norm(gallery_mat, axis=1, keepdims=True) + 1e-8)
    return np.dot(G, q)

def recognize_face_live(frame):
    temp_path = "live_temp_face.jpg"
    cv2.imwrite(temp_path, frame)
    FACE_SIM_THRESHOLD = 0.3
    face_box = None
    try:
        results = DeepFace.represent(img_path=temp_path, model_name='VGG-Face', enforce_detection=True)
        if results and isinstance(results, list):
            emb = np.array(results[0]["embedding"], dtype=np.float32)
            emb = emb / (np.linalg.norm(emb) + 1e-8)
            sims = cosine_sim_vectorized(emb, embeddings)
            best_idx = int(np.argmax(sims))
            best_sim = float(sims[best_idx])
            face_box = results[0].get("facial_area", None)
            if best_sim >= FACE_SIM_THRESHOLD:
                found_asset_id = asset_ids[best_idx]
                found_info = imageid_to_info.get(found_asset_id, {
                "name": "Unknown", "phone": "Unknown", "location": "Unknown", "address": "Unknown", "company": "Unknown"})
            else:
                found_info = {"name": "Unknown", "phone": "Unknown", "location": "Unknown", "address": "Unknown", "company": "Unknown"}
        else:
            found_info = {"name": "Unknown", "phone": "Unknown", "location": "Unknown", "address": "Unknown", "company": "Unknown"}
    except Exception:
        found_info = {"name": "Unknown", "phone": "Unknown", "location": "Unknown", "address": "Unknown", "company": "Unknown"}
    finally:
        if os.path.exists(temp_path): os.remove(temp_path)
    return found_info, face_box


def helmet_detect_live(frame, model, confidence=0.25):
    results = model(frame, conf=confidence)
    helmet_on = False
    best_conf = 0.0
    best_label = None
    best_box = None
    res = results[0] if results and len(results)>0 else None
    if res and hasattr(res, "boxes") and res.boxes is not None:
        names = res.names
        for box in res.boxes:
            conf = float(box.conf[0].item())
            cls_id = int(box.cls[0].item())
            label = names[cls_id]
            xyxy = box.xyxy[0].cpu().numpy().astype(int)
            if conf > best_conf:
                best_conf = conf
                best_label = label
                best_box = xyxy
        if best_box is not None and best_label is not None:
            norm_label = best_label.lower().replace("-", "").replace("_", "")
            if ("no" not in norm_label) and (("hardhat" in norm_label) or ("helmet" in norm_label)):
                helmet_on = True
    return helmet_on

model = YOLO(MODEL_PATH)
tick_icon = create_tick_icon()
cross_icon = create_cross_icon()

# Logging/session
log_records, last_logged, unknown_counter, unknown_frames = [], set(), {}, {}
BUFFER_UNKNOWN_FRAMES = 3
frame_num = 0
unknown_images_to_show = []
cap = cv2.VideoCapture(0)

cv2.namedWindow("Live VLM Safety", cv2.WINDOW_NORMAL)
try:
    cv2.setWindowProperty("Live VLM Safety", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
except Exception:
    cv2.resizeWindow("Live VLM Safety", 1920, 1080)

unknown_mode = False  # New flag for unknown detection

try:
    while True:
        ret, frame = cap.read()
        if not ret: break
        display_frame = frame.copy()
        if unknown_mode:
            # Capture 3 samples of unknown
            if len(unknown_images_to_show) < 3:
                unknown_images_to_show.append(frame.copy())
                cv2.putText(display_frame, f"Capturing unknown image {len(unknown_images_to_show)}/3...", (30, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,255), 3)
                cv2.imshow("Live VLM Safety", display_frame)
                cv2.waitKey(500)
            else:
                break
        else:
            if frame_num % 30 == 0:
                person_info, face_box = recognize_face_live(frame)
                helmet_status = helmet_detect_live(frame, model)
                person_id = f"{person_info['name']}_{person_info['phone']}"
                # Unknown routine
                if person_info['name'] == "Unknown":
                    unknown_counter[person_id] = unknown_counter.get(person_id, 0) + 1
                    if person_id not in unknown_frames: unknown_frames[person_id] = []
                    unknown_frames[person_id].append(frame.copy())
                    if unknown_counter[person_id] == BUFFER_UNKNOWN_FRAMES:
                        print("ALERT: Unknown 3x – stopping live feed.")
                        unknown_mode = True
                        continue
                else:
                    unknown_counter[person_id] = 0
                    unknown_frames.pop(person_id, None)
                if person_id not in last_logged:
                    log_entry = log_entry = {
                                "timestamp": datetime.now(),
                                "name": person_info.get("name", "Unknown"),
                                "phone": person_info.get("phone", "Unknown"),
                                "location": person_info.get("location", "Unknown"),
                                "address": person_info.get("address", "Unknown"),
                                "company": person_info.get("company", "Unknown"),
                                "helmet_on": bool(helmet_status)
}

                    log_records.append(log_entry)
                    last_logged.add(person_id)
            # Draw bounding box over face
            color = (0, 255, 0) if person_info["name"] != "Unknown" and helmet_status else (0, 0, 255)
            if face_box is not None:
                x, y, w, h = face_box.get('x',0), face_box.get('y',0), face_box.get('w',0), face_box.get('h',0)
                cv2.rectangle(display_frame, (x, y), (x+w, y+h), color, 3)
            icon = tick_icon if helmet_status else cross_icon
            display_frame = overlay_icon_bgr(display_frame, icon, 10, 10)
            cv2.putText(display_frame, f"Name: {person_info['name']}", (30, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,255,255), 2)
            cv2.putText(display_frame, f"Phone: {person_info['phone']}", (30, 135), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,255,255), 2)
            cv2.putText(display_frame, f"Loc: {person_info['location']}", (30, 170), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,255,255), 2)
            cv2.putText(display_frame, f"Addr: {person_info['address']}", (30, 205), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,255,255), 2)
            cv2.putText(display_frame, f"Company: {person_info['company']}", (30, 270), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,255,255), 2)

            status_txt = "HELMET ON" if helmet_status else "NO HELMET"
            cv2.putText(display_frame, status_txt, (30, 240), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0) if helmet_status else (0,0,255), 2)
            cv2.imshow("Live VLM Safety", display_frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
            frame_num += 1
finally:
    cap.release()
    cv2.destroyAllWindows()
    log_df = pd.DataFrame(log_records)
    log_df.to_csv("session_log.csv", index=False)
    print("Session CSV saved as session_log.csv")

# Interactive manual entry for unknown person
if unknown_mode and len(unknown_images_to_show) == 3:
    print("Looks like you're not in the database! Please enter the user details below:")
    name = input("Enter name: ")
    phone = input("Enter phone: ")
    location = input("Enter location: ")
    address = input("Enter address: ")
    print("\n=== New Person Details ===")
    print(f"Name: {name}")
    print(f"Phone: {phone}")
    print(f"Location: {location}")
    print(f"Address: {address}")
    print("Showing captured images:")
    plt.figure(figsize=(15,5))
    for idx, img in enumerate(unknown_images_to_show):
        plt.subplot(1, 3, idx+1)
        plt.imshow(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        plt.title(f"Unknown #{idx+1}")
        plt.axis('off')
    plt.show()


# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[11]:


import cv2
import numpy as np
import os
from ultralytics import YOLO
from deepface import DeepFace
import pandas as pd
from datetime import datetime
from PIL import Image, ImageDraw
import pymysql

DISPLAY_W, DISPLAY_H = 640, 480  # Change these to your preferred display size

emb_df = get_table_as_df("embeddings")
filenames = emb_df['filename'].values
asset_ids = emb_df['asset_id'].values
embeddings = np.vstack([np.fromstring(str(row["embedding"]), sep=',') for _, row in emb_df.iterrows()])

image_df = get_table_as_df("image")
worker_df = get_table_as_df("worker")
location_df = get_table_as_df("location")
company_df = get_table_as_df("company")

meta = image_df.merge(
    worker_df[['id', 'phone', 'company_id']], left_on="worker_id", right_on="id", how="left", suffixes=('', '_worker')
).merge(
    location_df[['id', 'name', 'address']], left_on="location_id", right_on="id", how="left", suffixes=('', '_location')
).merge(
    company_df[['id', 'name']], left_on="company_id", right_on="id", how="left", suffixes=('', '_company')
)

imageid_to_info = {}
for _, row in meta.iterrows():
    imageid = row['asset_id'] if pd.notnull(row['asset_id']) else os.path.splitext(row['filename'])[0]
    imageid_to_info[imageid] = {
        'name': row.get('name', 'Unknown'),
        'phone': row.get('phone', 'Unknown'),
        'location': row.get('name_location', 'Unknown'),
        'address': row.get('address', 'Unknown'),
        'company': row.get('name_company', 'Unknown')
    }

def create_tick_icon(size=38):
    img = Image.new('RGBA', (size, size), (0,0,0,0))
    draw = ImageDraw.Draw(img)
    draw.ellipse([6,6,size-6,size-6], fill=(0,200,0,230), outline=(255,255,255,255), width=3)
    tick = [
        (size*0.33, size*0.66), (size*0.5, size*0.85), (size*0.77, size*0.24)
    ]
    draw.line(tick, fill=(255,255,255,255), width=int(size/10), joint="curve")
    return np.array(img)

def create_cross_icon(size=38):
    img = Image.new('RGBA', (size, size), (0,0,0,0))
    draw = ImageDraw.Draw(img)
    draw.ellipse([6,6,size-6,size-6], fill=(220,0,0,230), outline=(255,255,255,255), width=3)
    c1 = [(size*0.32, size*0.32), (size*0.68, size*0.68)]
    c2 = [(size*0.68, size*0.32), (size*0.32, size*0.68)]
    draw.line(c1, fill=(255,255,255,255), width=int(size/10))
    draw.line(c2, fill=(255,255,255,255), width=int(size/10))
    return np.array(img)

def overlay_icon_bgr(frame, icon_rgba, x, y):
    h, w = icon_rgba.shape[:2]
    alpha = icon_rgba[:,:,3] / 255.0
    for c in range(3):
        frame[y:y+h, x:x+w, c] = (alpha * icon_rgba[:,:,c] + (1-alpha) * frame[y:y+h, x:x+w, c]).astype(np.uint8)
    return frame

def cosine_sim_vectorized(query_emb, gallery_mat):
    q = np.asarray(query_emb, dtype=np.float32)
    q = q / (np.linalg.norm(q) + 1e-8)
    G = np.array(gallery_mat) / (np.linalg.norm(gallery_mat, axis=1, keepdims=True) + 1e-8)
    return np.dot(G, q)

def detect_faces(frame):
    dets = DeepFace.extract_faces(frame, enforce_detection=False, detector_backend="opencv", align=False)
    faces, boxes = [], []
    for d in dets:
        boxes.append(d['facial_area'])
        faces.append(d['face'])
    return faces, boxes

FACE_SIM_THRESHOLD = 0.7
def recognize_face(face_img):
    temp_img = "temp_face.jpg"
    cv2.imwrite(temp_img, face_img)
    default = {'name': 'Unknown', 'phone': 'Unknown','location':'Unknown','address':'Unknown','company':'Unknown'}
    try:
        reps = DeepFace.represent(img_path=temp_img, model_name='VGG-Face', enforce_detection=False)
        if reps and isinstance(reps, list):
            emb = np.array(reps[0]["embedding"], dtype=np.float32)
            sims = cosine_sim_vectorized(emb, embeddings)
            best_idx = int(np.argmax(sims))
            best_sim = float(sims[best_idx])
            if best_sim >= FACE_SIM_THRESHOLD:
                found_asset_id = asset_ids[best_idx]
                found_info = imageid_to_info.get(found_asset_id, default)
                return found_info
    except Exception:
        pass
    finally:
        if os.path.exists(temp_img): os.remove(temp_img)
    return default

def helmet_detect_live(frame, model, confidence=0.25):
    results = model(frame, conf=confidence)
    helmet_on = False
    best_conf = 0.0
    best_label = None
    best_box = None
    res = results[0] if results and len(results) > 0 else None
    if res and hasattr(res, "boxes") and res.boxes is not None:
        names = res.names
        for box in res.boxes:
            conf = float(box.conf[0].item())
            cls_id = int(box.cls[0].item())
            label = names[cls_id]
            xyxy = box.xyxy[0].cpu().numpy().astype(int)
            if conf > best_conf:
                best_conf = conf
                best_label = label
                best_box = xyxy
        if best_box is not None and best_label is not None:
            norm_label = best_label.lower().replace("-", "").replace("_", "")
            if ("no" not in norm_label) and (("hardhat" in norm_label) or ("helmet" in norm_label)):
                helmet_on = True
    return helmet_on
# ... [All your imports and database setup as you posted] ...
# ...
model = YOLO(MODEL_PATH)
tick_icon = create_tick_icon()
cross_icon = create_cross_icon()

log_records = []
unknown_state = {}
current_display_frame = None
resize_ratio_x, resize_ratio_y = 1.0, 1.0

def click_callback(event, x, y, flags, param):
    global unknown_state, current_display_frame, resize_ratio_x, resize_ratio_y
    if event == cv2.EVENT_LBUTTONDOWN and current_display_frame is not None:
        x_orig = int(x * resize_ratio_x)
        y_orig = int(y * resize_ratio_y)
        best_id, min_dist = None, float('inf')
        for unk_id, unk_data in unknown_state.items():
            x0, y0, w, h = unk_data["box"]
            cx, cy = x0 + w // 2, y0 + h // 2
            dist = np.hypot(x_orig - cx, y_orig - cy)
            if dist < min_dist and dist < 40:
                min_dist, best_id = dist, unk_id
        if best_id is not None:
            unk_data = unknown_state[best_id]
            if unk_data.get("done", False):
                return
            if unk_data["count"] < 3:
                unk_data["count"] += 1
                x0, y0, w, h = unk_data["box"]
                h_img, w_img = current_display_frame.shape[:2]
                x1, y1 = max(0, min(x0, w_img-1)), max(0, min(y0, h_img-1))
                x2, y2 = max(0, min(x0+w, w_img)), max(0, min(y0+h, h_img))
                crop_img = current_display_frame[y1:y2, x1:x2].copy()
                filename = f"{best_id}_{unk_data['count']}.jpg"
                cv2.imwrite(filename, crop_img)
                print(f"Image captured: {filename}")

cv2.namedWindow("Live VLM Safety", cv2.WINDOW_NORMAL)
cv2.setMouseCallback("Live VLM Safety", click_callback)
try:
    cv2.setWindowProperty("Live VLM Safety", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
except Exception:
    cv2.resizeWindow("Live VLM Safety", DISPLAY_W, DISPLAY_H)

cap = cv2.VideoCapture(0)
try:
    while True:
        ret, frame = cap.read()
        if not ret: break
        current_display_frame = frame.copy()
        faces, boxes = detect_faces(frame)
        helmet_status = helmet_detect_live(frame, model)
        # Only keep unknowns who have not completed registration
        unknown_state = {k: v for k, v in unknown_state.items() if not v.get("done", False)}
        frame_unknowns = 0
        display_frame = frame.copy()
        for i, (face, box) in enumerate(zip(faces, boxes)):
            person_info = recognize_face(face)
            color = (0, 210, 0) if person_info['name'] != "Unknown" and helmet_status else (0, 0, 210)
            x, y, w, h = box.get('x',0), box.get('y',0), box.get('w',0), box.get('h',0)
            cv2.rectangle(display_frame, (x, y), (x+w, y+h), color, 2)
            icon = tick_icon if helmet_status else cross_icon
            display_frame = overlay_icon_bgr(display_frame, icon, x, y-42 if y-42>10 else y+10)
            font = cv2.FONT_HERSHEY_SIMPLEX
            cv2.putText(display_frame, person_info.get('name','Unknown'), (x, y-8), font, 0.62, color, 2)
            cv2.putText(display_frame, f"Phone: {person_info.get('phone','Unknown')}", (x, y+h+18), font, 0.5, (255,255,0), 1)
            cv2.putText(display_frame, f"Company: {person_info.get('company','Unknown')}", (x, y+h+36), font, 0.5, (160,255,160), 1)
            cv2.putText(display_frame, f"Location: {person_info.get('location','Unknown')}", (x, y+h+54), font, 0.5, (120,200,255), 1)
            if person_info["name"] == "Unknown":
                min_dist = float('inf')
                match_id = None
                cx, cy = x + w // 2, y + h // 2
                for uid, ud in unknown_state.items():
                    bx, by, bw, bh = ud["box"]
                    mcx, mcy = bx + bw // 2, by + bh // 2
                    dist = np.hypot(cx - mcx, cy - mcy)
                    if dist < min_dist and dist < 40:
                        min_dist = dist
                        match_id = uid
                if match_id is None:
                    match_id = f"{cx}_{cy}"
                    unknown_state[match_id] = {"count": 0, "box": (x, y, w, h), "done": False, "confirmation": False}
                unknown_state[match_id]["box"] = (x, y, w, h)
                # --------- Overlay logic ---------
                if not unknown_state[match_id].get("done", False) and unknown_state[match_id]["count"] < 3:
                    frame_unknowns += 1
                    left = 3 - unknown_state[match_id]["count"]
                    msg = f"Unknown detected! Click {left} more times."
                    y_label = max(y-30, 10)
                    cv2.putText(display_frame, msg, (x, y_label), font, 0.53, (0,0,255), 2)
                elif unknown_state[match_id]["count"] == 3 and not unknown_state[match_id].get("confirmation", False):
                    msg = "Images taken! Please enter details..."
                    y_label = max(y-30, 10)
                    cv2.putText(display_frame, msg, (x, y_label), font, 0.57, (255,180,0), 2)
                    unknown_state[match_id]["confirmation"] = True
                    print("\n=== Person images captured! ===")
                    name = input("Enter name: ")
                    phone = input("Enter phone: ")
                    company = input("Enter company: ")
                    location = input("Enter location: ")
                    print(f"\nDetails entered:\nName: {name}\nPhone: {phone}\nCompany: {company}\nLocation: {location}")
                    print("Captured files:")
                    for click_idx in range(1, 4):
                        filename = f"{match_id}_{click_idx}.jpg"
                        new_name = f"{name}{click_idx}.jpg"
                        print(f"{new_name}")
                        os.rename(filename, new_name)
                        img = cv2.imread(new_name)
                        if img is not None:
                            cv2.imshow(new_name, img)
                    input("Press Enter to continue...")
                    unknown_state[match_id]["done"] = True
            log_records.append({
                "timestamp": datetime.now(),
                "name": person_info.get("name", "Unknown"),
                "phone": person_info.get("phone", "Unknown"),
                "location": person_info.get("location", "Unknown"),
                "address": person_info.get("address", "Unknown"),
                "company": person_info.get("company", "Unknown"),
                "helmet_on": bool(helmet_status)
            })
        if frame_unknowns > 0:
            cv2.putText(display_frame, f"Total unknowns now: {frame_unknowns}", (30, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,0,255), 2)
        resize_ratio_x = current_display_frame.shape[1] / DISPLAY_W
        resize_ratio_y = current_display_frame.shape[0] / DISPLAY_H
        disp = cv2.resize(display_frame, (DISPLAY_W, DISPLAY_H))
        cv2.imshow("Live VLM Safety", disp)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
finally:
    cap.release()
    cv2.destroyAllWindows()
    pd.DataFrame(log_records).to_csv("session_log.csv", index=False)
    print("Session CSV saved as session_log.csv")




# In[13]:


import pandas as pd

df = pd.read_csv("session_log.csv")
df  # this automatically shows as a table/grid in notebook UI


# In[17]:


import cv2
import matplotlib.pyplot as plt

images = []
for i in range(1, 4):
    img = cv2.imread(f"graj{i}.jpg")
    if img is not None:
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)  # convert for correct display
        images.append(img_rgb)
    else:
        print(f"gg{i}.jpg not found")

if images:
    plt.figure(figsize=(12, 4))
    for idx, img in enumerate(images):
        plt.subplot(1, 3, idx+1)
        plt.imshow(img)
        plt.title(f"Captured Image {idx+1}")
        plt.axis('off')
    plt.show()
else:
    print("No images found!")


# In[ ]:
