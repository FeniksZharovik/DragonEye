# Dragon Eye Fuzzy Grading System - Interactive Notebook

# %%
"""
Notebook-style script for interactive image upload and step-by-step
processing (preprocessing -> segmentation -> feature extraction -> fuzzy grading).

Place the "Pilih File" upload widget immediately after the imports, before helper
functions as requested.

This file is ready to paste into a Jupyter cell or saved as a .py and opened with
Jupytext to get a proper .ipynb. Processing is done in-memory; nothing is written
to disk unless you add saving logic.
"""

# %%
# -------------------- Imports --------------------
import io
import os
import cv2
import numpy as np
import matplotlib.pyplot as plt
from skimage.feature import graycomatrix, graycoprops
from ipywidgets import FileUpload, Button, VBox, HBox, Output, Label
from IPython.display import display, clear_output
from PIL import Image
import skfuzzy as fuzz
from skfuzzy import control as ctrl

plt.rcParams['figure.figsize'] = (6, 6)

# %%
# -------------------- File upload widget (Pilih File) --------------------
# This widget appears immediately after imports as requested.

upload_widget = FileUpload(accept='image/*', multiple=False)
upload_out = Output()

print("Silakan unggah gambar (JPG/PNG). Tombol pilih file di bawah:")


def _on_upload_change(change):
    # display immediate thumbnail of uploaded file
    with upload_out:
        clear_output()
        if len(upload_widget.value) == 0:
            print('Belum ada file.')
            return
        # Grab first (and only) file
        name = list(upload_widget.value.keys())[0]
        file_info = upload_widget.value[name]
        content = file_info['content']
        try:
            pil_img = Image.open(io.BytesIO(content)).convert('RGB')
            np_img_rgb = np.array(pil_img)
            print(f"File berhasil diunggah: {name}")
            plt.imshow(np_img_rgb)
            plt.axis('off')
            plt.title('Gambar Asli (RGB)')
            plt.show()
            # store globally for processing button
            global uploaded_image_rgb, uploaded_image_bgr
            uploaded_image_rgb = np_img_rgb
            uploaded_image_bgr = cv2.cvtColor(np_img_rgb, cv2.COLOR_RGB2BGR)
        except Exception as e:
            print('Gagal membuka gambar:', e)

upload_widget.observe(_on_upload_change, names='value')

display(VBox([upload_widget, upload_out]))

# %%
# -------------------- Helper functions --------------------

def preprocess_image(img_bgr, target_size=(256, 256)):
    """Resize, denoise, convert to HSV."""
    img = cv2.resize(img_bgr, target_size)
    img = cv2.GaussianBlur(img, (3, 3), 0)
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    return hsv


def segment_image(hsv):
    """Segment buah naga berdasarkan rentang warna + background heuristik.
    Return: segmented_hsv, mask (uint8 0/255)
    """
    lower_red1 = np.array([0, 40, 40], dtype=np.uint8)
    upper_red1 = np.array([15, 255, 255], dtype=np.uint8)
    lower_red2 = np.array([160, 40, 40], dtype=np.uint8)
    upper_red2 = np.array([180, 255, 255], dtype=np.uint8)
    lower_green = np.array([35, 40, 40], dtype=np.uint8)
    upper_green = np.array([90, 255, 255], dtype=np.uint8)
    lower_yellow = np.array([20, 40, 40], dtype=np.uint8)
    upper_yellow = np.array([45, 255, 255], dtype=np.uint8)

    mask_red = cv2.bitwise_or(cv2.inRange(hsv, lower_red1, upper_red1),
                              cv2.inRange(hsv, lower_red2, upper_red2))
    mask_green = cv2.inRange(hsv, lower_green, upper_green)
    mask_yellow = cv2.inRange(hsv, lower_yellow, upper_yellow)
    mask = cv2.bitwise_or(mask_red, cv2.bitwise_or(mask_green, mask_yellow))

    # remove bright/dim background
    bg_light = cv2.inRange(hsv, np.array([0, 0, 160], dtype=np.uint8), np.array([180, 60, 255], dtype=np.uint8))
    bg_dark = cv2.inRange(hsv, np.array([0, 0, 0], dtype=np.uint8), np.array([180, 100, 50], dtype=np.uint8))
    bg_mask = cv2.bitwise_or(bg_light, bg_dark)
    mask = cv2.bitwise_and(mask, cv2.bitwise_not(bg_mask))

    kernel = np.ones((3, 3), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)

    # refine thin edges
    edge_refine = cv2.inRange(hsv, np.array([0, 0, 130], dtype=np.uint8), np.array([180, 70, 255], dtype=np.uint8))
    edge_refine = cv2.GaussianBlur(edge_refine, (5, 5), 0)
    edge_refine = cv2.dilate(edge_refine, kernel, iterations=1)
    mask = cv2.bitwise_and(mask, cv2.bitwise_not(edge_refine))

    # keep largest contour
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if contours:
        filled_mask = np.zeros_like(mask)
        cv2.drawContours(filled_mask, [max(contours, key=cv2.contourArea)], -1, 255, -1)
        mask = filled_mask

    mask_blur = cv2.GaussianBlur(mask, (3, 3), 0)
    _, mask_final = cv2.threshold(mask_blur, 100, 255, cv2.THRESH_BINARY)

    segmented = cv2.bitwise_and(hsv, hsv, mask=mask_final)
    return segmented, mask_final


def extract_features(segmented_img, mask):
    """Extract features for a single image. Returns:
    area (px), width, height, weight_est, texture_score, hue_mean
    """
    if mask is None or np.count_nonzero(mask) == 0:
        return 0.0, 0, 0, 0.0, 0.0, 0.0

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return 0.0, 0, 0, 0.0, 0.0, 0.0

    c = max(contours, key=cv2.contourArea)
    area = float(cv2.contourArea(c))
    x, y, w_box, h_box = cv2.boundingRect(c)
    w_box, h_box = int(w_box), int(h_box)

    k = 0.004
    weight_est = k * area

    hsv = segmented_img.copy()
    if len(hsv.shape) == 3:
        h_ch, s_ch, v_ch = cv2.split(hsv)
    else:
        h_ch = s_ch = v_ch = hsv

    x0, y0 = max(0, x), max(0, y)
    x1, y1 = min(hsv.shape[1], x + w_box), min(hsv.shape[0], y + h_box)
    s_crop = s_ch[y0:y1, x0:x1]
    h_crop = h_ch[y0:y1, x0:x1]
    mask_crop = mask[y0:y1, x0:x1]

    if mask_crop is None or mask_crop.size == 0 or np.count_nonzero(mask_crop) == 0:
        hue_mean = float(np.mean(h_ch[mask > 0]) / 180.0) if np.count_nonzero(mask) > 0 else 0.0
        return area, w_box, h_box, weight_est, 0.0, hue_mean

    region_s = s_crop[mask_crop > 0]
    region_h = h_crop[mask_crop > 0]

    if region_s.size == 0:
        hue_mean = float(np.mean(region_h) / 180.0) if region_h.size > 0 else 0.0
        return area, w_box, h_box, weight_est, 0.0, hue_mean

    levels = 64
    s_norm = cv2.normalize(s_crop, None, 0, levels - 1, cv2.NORM_MINMAX).astype(np.uint8)
    s_masked = np.where(mask_crop > 0, s_norm, 0).astype(np.uint8)

    if np.count_nonzero(mask_crop) < 10:
        contrast = homogeneity = energy = 0.0
    else:
        try:
            glcm = graycomatrix(
                s_masked,
                distances=[1, 2],
                angles=[0, np.pi/4, np.pi/2],
                levels=levels,
                symmetric=True,
                normed=True
            )
            contrast = float(np.mean(graycoprops(glcm, 'contrast')))
            homogeneity = float(np.mean(graycoprops(glcm, 'homogeneity')))
            energy = float(np.mean(graycoprops(glcm, 'energy')))
        except Exception:
            contrast = homogeneity = energy = 0.0

    texture_score = (homogeneity + energy) / 2.0 * (1.0 - contrast / (contrast + 1.0))
    hue_mean = float(np.mean(region_h) / 180.0) if region_h.size > 0 else 0.0

    return area, w_box, h_box, weight_est, float(texture_score), hue_mean

# %%
# -------------------- Visualization helpers --------------------


def show_bgr(img_bgr, title=None):
    img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
    plt.imshow(img_rgb)
    if title:
        plt.title(title)
    plt.axis('off')
    plt.show()


def show_hsv(hsv_img, title=None):
    try:
        bgr = cv2.cvtColor(hsv_img, cv2.COLOR_HSV2BGR)
        show_bgr(bgr, title)
    except Exception:
        plt.imshow(hsv_img if hsv_img.ndim==2 else hsv_img[:,:,0], cmap='gray')
        if title: plt.title(title)
        plt.axis('off')
        plt.show()

# %%
# -------------------- Fuzzy controllers --------------------

def make_fuzzy_size_ctrl():
    ukuran = ctrl.Antecedent(np.arange(0, 1.01, 0.01), 'ukuran')
    berat = ctrl.Antecedent(np.arange(0, 1.01, 0.01), 'berat')
    tekstur = ctrl.Antecedent(np.arange(0, 1.01, 0.01), 'tekstur')
    grade_out = ctrl.Consequent(np.arange(0, 101, 1), 'grade_out')

    ukuran['kecil'] = fuzz.trimf(ukuran.universe, [0.0, 0.0, 0.35])
    ukuran['sedang'] = fuzz.trimf(ukuran.universe, [0.3, 0.55, 0.7])
    ukuran['besar']  = fuzz.trimf(ukuran.universe, [0.6, 0.9, 1.0])

    berat['rendah']  = fuzz.trimf(berat.universe, [0.0, 0.0, 0.35])
    berat['sedang']  = fuzz.trimf(berat.universe, [0.3, 0.55, 0.7])
    berat['tinggi']  = fuzz.trimf(berat.universe, [0.6, 0.9, 1.0])

    tekstur['kasar'] = fuzz.trimf(tekstur.universe, [0.0, 0.0, 0.25])
    tekstur['normal']= fuzz.trimf(tekstur.universe, [0.2, 0.45, 0.7])
    tekstur['halus'] = fuzz.trimf(tekstur.universe, [0.4, 0.7, 1.0])

    grade_out['C'] = fuzz.trimf(grade_out.universe, [0, 0, 40])
    grade_out['B'] = fuzz.trimf(grade_out.universe, [35, 55, 75])
    grade_out['A'] = fuzz.trimf(grade_out.universe, [60, 100, 100])

    rules = [
        ctrl.Rule(ukuran['besar'] & berat['tinggi'], grade_out['A']),
        ctrl.Rule(ukuran['sedang'] & berat['tinggi'], grade_out['A']),
        ctrl.Rule(ukuran['besar'] & tekstur['normal'], grade_out['A']),
        ctrl.Rule(berat['tinggi'] & tekstur['halus'], grade_out['A']),
        ctrl.Rule(ukuran['besar'] & tekstur['halus'], grade_out['A']),
        ctrl.Rule(ukuran['sedang'] & berat['sedang'] & tekstur['halus'], grade_out['A']),

        ctrl.Rule(ukuran['sedang'] & berat['sedang'], grade_out['B']),
        ctrl.Rule(ukuran['besar'] & tekstur['kasar'], grade_out['B']),
        ctrl.Rule(ukuran['sedang'] & tekstur['normal'], grade_out['B']),
        ctrl.Rule(berat['rendah'] & tekstur['halus'], grade_out['B']),
        ctrl.Rule(ukuran['besar'] & berat['rendah'], grade_out['B']),
        ctrl.Rule(ukuran['kecil'] & berat['tinggi'], grade_out['B']),

        ctrl.Rule(ukuran['kecil'] | berat['rendah'], grade_out['C']),
        ctrl.Rule(tekstur['kasar'], grade_out['C']),
    ]

    grading_ctrl = ctrl.ControlSystem(rules)
    return grading_ctrl


def make_fuzzy_texture_ctrl():
    warna = ctrl.Antecedent(np.arange(0, 1.01, 0.01), 'warna')
    tekstur = ctrl.Antecedent(np.arange(0, 1.01, 0.01), 'tekstur')
    kondisi_out = ctrl.Consequent(np.arange(0, 101, 1), 'kondisi_out')

    warna['gelap'] = fuzz.trimf(warna.universe, [0.0, 0.0, 0.35])
    warna['normal'] = fuzz.trimf(warna.universe, [0.3, 0.55, 0.75])
    warna['cerah'] = fuzz.trimf(warna.universe, [0.7, 1.0, 1.0])

    tekstur['kasar'] = fuzz.trimf(tekstur.universe, [0.0, 0.0, 0.3])
    tekstur['normal'] = fuzz.trimf(tekstur.universe, [0.25, 0.55, 0.75])
    tekstur['halus'] = fuzz.trimf(tekstur.universe, [0.6, 1.0, 1.0])

    kondisi_out['rotten'] = fuzz.trimf(kondisi_out.universe, [0, 0, 40])
    kondisi_out['defect'] = fuzz.trimf(kondisi_out.universe, [30, 55, 70])
    kondisi_out['good'] = fuzz.trimf(kondisi_out.universe, [60, 100, 100])

    rules = [
        ctrl.Rule(warna['cerah'] & tekstur['halus'], kondisi_out['good']),
        ctrl.Rule(warna['normal'] & tekstur['normal'], kondisi_out['good']),
        ctrl.Rule(warna['gelap'] & tekstur['halus'], kondisi_out['defect']),
        ctrl.Rule(warna['normal'] & tekstur['kasar'], kondisi_out['defect']),
        ctrl.Rule(warna['gelap'] & tekstur['kasar'], kondisi_out['rotten']),
    ]

    kondisi_ctrl = ctrl.ControlSystem(rules)
    return kondisi_ctrl

# instantiate controllers
size_ctrl = make_fuzzy_size_ctrl()
texture_ctrl = make_fuzzy_texture_ctrl()

# %%
# -------------------- Interactive pipeline runner --------------------

run_button = Button(description='Jalankan pipeline', button_style='success')
process_out = Output()


def on_run_clicked(b):
    with process_out:
        clear_output()
        # check uploaded image
        if 'uploaded_image_bgr' not in globals():
            print('Belum ada gambar yang diunggah. Silakan pilih file terlebih dahulu.')
            return

        img_bgr = uploaded_image_bgr.copy()
        print('Menjalankan pipeline untuk gambar yang diunggah...')

        # show original (RGB view)
        print('Original:')
        show_bgr(img_bgr, title='Original (RGB view)')

        # preprocessing
        hsv = preprocess_image(img_bgr)
        print('Setelah preprocessing (HSV visualisasi):')
        show_hsv(hsv, title='Preprocessed (HSV -> BGR shown)')

        # segmentation
        segmented, mask = segment_image(hsv)
        print('Mask segmentasi:')
        plt.imshow(mask, cmap='gray')
        plt.title('Mask (biner)')
        plt.axis('off')
        plt.show()

        print('Hasil segmentasi (HSV visualized):')
        show_hsv(segmented, title='Segmented (HSV)')

        # feature extraction
        area, w_box, h_box, weight_est, texture_score, hue_mean = extract_features(segmented, mask)
        print('Fitur yang diekstraksi:')
        print(f'  area (px): {area:.1f}')
        print(f'  bbox: {w_box} x {h_box} px')
        print(f'  weight_est (empirik): {weight_est:.4f}')
        print(f'  texture_score: {texture_score:.4f}')
        print(f'  hue_mean (0..1): {hue_mean:.4f}')

        # normalize for fuzzy
        img_area_max = hsv.shape[0] * hsv.shape[1]
        area_norm = np.clip(area / float(img_area_max), 0.0, 1.0)
        k = 0.004
        weight_norm = np.clip(weight_est / (k * img_area_max + 1e-9), 0.0, 1.0)
        texture_norm = np.clip(texture_score, 0.0, 1.0)
        hue_norm = np.clip(hue_mean, 0.0, 1.0)

        print('Nilai normalisasi untuk fuzzy:')
        print(f'  area_norm: {area_norm:.4f}')
        print(f'  weight_norm: {weight_norm:.4f}')
        print(f'  texture_norm: {texture_norm:.4f}')
        print(f'  hue_norm: {hue_norm:.4f}')

        # fuzzy grading size
        sim = ctrl.ControlSystemSimulation(size_ctrl)
        sim.input['ukuran'] = float(area_norm)
        sim.input['berat'] = float(weight_norm)
        sim.input['tekstur'] = float(texture_norm)
        try:
            sim.compute()
            grade_score = sim.output['grade_out']
        except Exception as e:
            print('Error fuzzy (size):', e)
            grade_score = 0.0

        if grade_score >= 60:
            grade_label = 'A'
        elif grade_score >= 40:
            grade_label = 'B'
        else:
            grade_label = 'C'

        print('Hasil grading (ukuran/berat/tekstur):')
        print(f'  grade_score: {grade_score:.2f}')
        print(f'  grade_label: {grade_label}')

        # fuzzy grading texture-color
        sim2 = ctrl.ControlSystemSimulation(texture_ctrl)
        sim2.input['warna'] = float(hue_norm)
        sim2.input['tekstur'] = float(texture_norm)
        try:
            sim2.compute()
            tex_score = sim2.output['kondisi_out']
        except Exception as e:
            print('Error fuzzy (texture):', e)
            tex_score = 0.0

        if tex_score >= 60:
            tex_label = 'Good'
        elif tex_score >= 40:
            tex_label = 'Defect'
        else:
            tex_label = 'Rotten'

        print('Penilaian warna & tekstur:')
        print(f'  texture_grade_score: {tex_score:.2f}')
        print(f'  texture_grade_label: {tex_label}')

# bind button
run_button.on_click(on_run_clicked)

display(HBox([run_button]))
display(process_out)

# %%
# Notes:
# - Semua pemrosesan dilakukan di-memory: file tidak disimpan to disk by default.
# - Jika mau menyimpan hasil (segmented image atau CSV), tambahkan fungsi simpan di bagian akhir.
# - Untuk membuat .ipynb: simpan file ini and use Jupytext or paste into Jupyter Notebook.
