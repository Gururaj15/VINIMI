# VINIMI - Vision and Natural Language Intelligence for Monitoring Industrial Safety

This project focuses on **ensuring workplace safety compliance** by detecting personnel, identifying individuals, and verifying whether they are wearing appropriate **Personal Protective Equipment (PPE)** such as helmets. The pipeline integrates **face recognition**, **helmet detection**, and a **vision-language interface** for querying images and videos.

---

## Project Architecture

![VINIMI Architecture](https://github.com/vinimifall2025-ops/VINIMI/blob/main/images/simple_architecture.png)

*Figure: Architecture of VINIMI pipeline, showing dataset preparation, face recognition and helmet detection.*

---

## What We Have Done

### 1. Synthetic Dataset Creation
- Generated **450 photo-realistic images** using **Stable Diffusion (Realistic Vision V5.1)**.  
  - 225 images with helmets, 225 without helmets.  
- Each person assigned **unique metadata**: name, gender, age, appearance traits.  
- **50+ diverse construction & industrial scenes** included.  
- Images organized into `helmet/` and `no_helmet/` directories.  
- [Wiki Page: Synthetic Dataset](https://github.com/vinimifall2025-ops/VINIMI/wiki/Synthetic-Dataset)

---

### 2. Real-world Dataset Creation
- Collected **real images and videos** with actual helmets under **varied lighting and construction scenarios**.  
- Captured images **with and without helmets** for the same participants.  
- Ensured **gender diversity** to reduce bias.  
- Recorded **short videos** to simulate real-life monitoring situations.  
- Systematic naming convention: `<name><index>` (e.g., `ravi1`, `ravi2`).  
- [Wiki Page: Real-world Dataset](https://github.com/vinimifall2025-ops/VINIMI/wiki/Dataset-Preparation-(Real%E2%80%90world))

---

### 3. Metadata Preparation
- Prepared **metadata for both images and videos**.  
  - Image metadata CSV: maps filename → person name → unique mobile number.  
  - Video metadata CSV: maps video filename → person name → unique mobile number.  
- Enables **identity mapping** for face recognition and helmet compliance tracking.  
- [Wiki Page: Metadata Preparation](https://github.com/vinimifall2025-ops/VINIMI/wiki/Metadata-Preparation-(Real%E2%80%90world))

---

### 4. Face Recognition (Images)
- Used **DeepFace** (VGG-Face) to extract **embeddings** for each face image.  
- Compared embeddings using **cosine similarity** to recognize individuals.  
- Visualized results with **bounding boxes** and **name + phone overlay**.  
- [Wiki Page: Face Recognition - Images](https://github.com/vinimifall2025-ops/VINIMI/wiki/Face-Embedding-&-Recognition-Pipeline)

---

### 5. Face Recognition (Videos)
- Sampled **key frames** from videos (e.g., N=6 per video).  
- Extracted face embeddings **frame-wise**.  
- Used **majority voting** across frames to decide final identity.  
- Visualized **best match frame** with bounding boxes and name label.  
- [Wiki Page: Face Recognition - Videos](https://github.com/vinimifall2025-ops/VINIMI/wiki/Face-Recognition-in-Videos:-Pipeline-&-Majority-Voting)

---

### 6. Helmet Detection
- Used **YOLOv8 (pretrained)** for helmet/hardhat detection in images and videos.  
- For videos, applied **frame sampling** and tracked the **best detection frame**.  
- Integrated with **DeepFace** to create a **unified safety monitoring pipeline**:
  - Detect helmet status per frame  
  - Recognize the person using embeddings  
  - Apply majority voting for video identity  
  - Overlay bounding boxes and labels for visualization  
- Enables **automated alerts** tied to actual individuals.  
- [Wiki Page: Helmet Detection + Face Recognition](https://github.com/vinimifall2025-ops/VINIMI/wiki/Helmet-Detection-&-Face-Recognition:-YOLO---DeepFace-Unified-Pipeline)

---

## Next Steps - Getting Started

To **clone the repository, set up your local environment, and run VINIMI locally**, please refer to the comprehensive setup guide:

📖 **[LOCAL_SETUP.md](./LOCAL_SETUP.md)** - Complete setup instructions for macOS, Windows, and Linux

This guide includes:
- ✅ Prerequisites and dependencies
- ✅ MySQL database setup from SQL dump
- ✅ Environment file configuration (.env)
- ✅ Backend installation and startup
- ✅ Frontend installation and startup
- ✅ Troubleshooting common issues
- ✅ Platform-specific instructions

### Future Enhancements

- Integrate **alerting system** to notify individuals via SMS if safety violations are detected.  
- Extend **Vision-Language Q&A** to allow intuitive queries like "Is this person wearing a helmet?" or "Who is this?"  
- Add **real-time dashboard** with violation analytics and reporting.
- Implement **multi-camera support** for enterprise deployments.
- Deploy **mobile app** for worker check-in and alert notifications.

---

## References & Wiki

For **detailed explanations, example images/videos, and step-by-step documentation**, please refer to the project wiki:  

[VINIMI Project Wiki](https://github.com/vinimifall2025-ops/VINIMI/wiki)
