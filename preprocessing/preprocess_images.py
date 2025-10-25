from __future__ import annotations
import os
import sys
import time
import math
import json
import argparse
import logging
import shutil
from pathlib import Path
from dataclasses import dataclass
from typing import Tuple, Optional, Dict, Any, List
import concurrent.futures

import numpy as np
import pandas as pd
import cv2
from PIL import Image, ImageOps

# Optional libs
try:
    from sklearn.cluster import KMeans
    HAS_SKLEARN = True
except Exception:
    HAS_SKLEARN = False

try:
    from tqdm import tqdm
except Exception:
    tqdm = None

# ----------------------------
# Helpers
# ----------------------------

def setup_logging(verbose: bool = False):
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="[%(asctime)s] %(levelname)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        force=True,
    )


def ensure_dir(path: str):
    Path(path).mkdir(parents=True, exist_ok=True)


def imread_unicode(path: str, unchanged: bool = False) -> Optional[np.ndarray]:
    """Read image safely even when path contains unicode on Windows."""
    try:
        arr = np.fromfile(path, dtype=np.uint8)
        if arr.size == 0:
            return None
        flag = cv2.IMREAD_UNCHANGED if unchanged else cv2.IMREAD_COLOR
        img = cv2.imdecode(arr, flag)
        return img
    except Exception as e:
        logging.debug("imread_unicode failed for %s: %s", path, e)
        return None


def imwrite_unicode(path: str, img: np.ndarray, quality: int = 95) -> bool:
    """Unicode-safe write. Automatically picks format by suffix. Handles alpha.
    Returns True on success.
    """
    try:
        p = Path(path)
        ensure_dir(str(p.parent))
        ext = p.suffix.lower()
        if ext == "":
            ext = ".jpg"
            path = str(p) + ext
        # Ensure proper encoding flags
        if ext in (".jpg", ".jpeg"):
            # drop alpha if present
            if img.ndim == 3 and img.shape[2] == 4:
                img2 = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
            else:
                img2 = img
            ok, enc = cv2.imencode(ext, img2, [int(cv2.IMWRITE_JPEG_QUALITY), int(quality)])
        elif ext == ".png":
            ok, enc = cv2.imencode(ext, img, [int(cv2.IMWRITE_PNG_COMPRESSION), 3])
        else:
            ok, enc = cv2.imencode(ext, img)
        if not ok:
            logging.error("cv2.imencode failed for %s", path)
            return False
        enc.tofile(path)
        return True
    except Exception as e:
        logging.exception("imwrite_unicode failed for %s: %s", path, e)
        return False


def load_image_exif(path: str, use_exif: bool = True, unchanged: bool = False) -> Optional[np.ndarray]:
    """Load image with EXIF orientation applied if requested."""
    try:
        if use_exif:
            im = Image.open(path)
            im = ImageOps.exif_transpose(im)
            im = im.convert("RGB")
            arr = np.asarray(im)
            bgr = cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)
            return bgr
        else:
            return imread_unicode(path, unchanged=unchanged)
    except Exception:
        return imread_unicode(path, unchanged=unchanged)


# ----------------------------
# Configuration
# ----------------------------
@dataclass
class PreprocessConfig:
    raw_dir: str = "raw_data"
    out_dir: str = "dataset"
    target_size: Tuple[int, int] = (224, 224)
    margin: float = 0.06
    min_contour_area_fraction: float = 0.0008
    use_exif: bool = True
    use_clahe: bool = True
    clahe_clip: float = 2.0
    clahe_grid: Tuple[int, int] = (8, 8)
    save_quality: int = 95
    debug: bool = False
    save_intermediates: bool = False
    force: bool = False
    verbose: bool = False
    autotune_samples: Optional[int] = None
    review_mode: bool = False
    review_save_path: str = "dataset_review"
    reject_folder_name: str = "rejects"
    sample_downscale: int = 4
    kmeans_clusters: int = 3
    hsv_ranges: Optional[List[Tuple[Tuple[int,int,int], Tuple[int,int,int]]]] = None
    timestamp_format: str = "%Y%m%d_%H%M%S"
    crop_mask_coverage_threshold: float = 0.12
    margin_increment_steps: Tuple[float,...] = (0.06, 0.10, 0.18)
    max_attempts: int = 4
    seed: int = 42
    mode: str = "preprocess"
    verbose_intermediate: bool = False
    workers: int = max(1, (os.cpu_count() or 1) - 1)
    fast: bool = False


# ----------------------------
# Color & enhancement
# ----------------------------

def grey_world_balance(bgr: np.ndarray) -> np.ndarray:
    img = bgr.astype(np.float32)
    means = img.mean(axis=(0,1))
    global_mean = means.mean()
    scales = np.where(means > 1e-6, global_mean / (means + 1e-8), 1.0)
    balanced = img * scales
    return np.clip(balanced, 0, 255).astype(np.uint8)


def apply_clahe_bgr(bgr: np.ndarray, clip=2.0, grid=(8,8)) -> np.ndarray:
    try:
        lab = cv2.cvtColor(bgr, cv2.COLOR_BGR2LAB)
        l,a,b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=clip, tileGridSize=grid)
        l2 = clahe.apply(l)
        lab2 = cv2.merge([l2,a,b])
        return cv2.cvtColor(lab2, cv2.COLOR_LAB2BGR)
    except Exception:
        return bgr


# ----------------------------
# Mask primitives (optimized)
# ----------------------------

def mask_by_hsv_adaptive(bgr: np.ndarray) -> np.ndarray:
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    h = hsv[:,:,0]
    hist = cv2.calcHist([h],[0],None,[180],[0,180]).flatten()
    hist = cv2.GaussianBlur(hist.reshape(-1,1),(5,1),0).flatten()
    peaks = np.argsort(hist)[-6:][::-1]
    candidate = None
    for p in peaks:
        if 8 <= p <= 60:
            candidate = p
            break
    if candidate is None:
        candidate = int(peaks[0]) if peaks.size else 30
    peak = int(candidate)
    width = 14 if 10 < peak < 140 else 20
    low = max(0, peak - width)
    high = min(179, peak + width)
    mask1 = cv2.inRange(hsv, np.array((low,40,30),dtype=np.uint8), np.array((high,255,255),dtype=np.uint8))
    mask2 = cv2.inRange(hsv, np.array((30,30,20),dtype=np.uint8), np.array((90,255,255),dtype=np.uint8))
    mask = cv2.bitwise_or(mask1, mask2)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(7,7))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)
    return mask


def mask_by_otsu(bgr: np.ndarray) -> np.ndarray:
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray,(5,5),0)
    _, m = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    if np.count_nonzero(m) < m.size / 2:
        m = cv2.bitwise_not(m)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5,5))
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, kernel, iterations=2)
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, kernel, iterations=1)
    return m


def mask_by_edges(bgr: np.ndarray) -> np.ndarray:
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 60, 160)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5,5))
    m = cv2.dilate(edges, kernel, iterations=2)
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, kernel, iterations=2)
    return m


# Lightweight GrabCut wrapper (optional)
def mask_by_grabcut(bgr: np.ndarray, iter_count: int = 3) -> np.ndarray:
    h,w = bgr.shape[:2]
    mask = np.zeros((h,w), np.uint8)
    rect = (int(w*0.05), int(h*0.05), max(2,int(w*0.9)), max(2,int(h*0.9)))
    bgd = np.zeros((1,65), np.float64)
    fgd = np.zeros((1,65), np.float64)
    try:
        cv2.grabCut(bgr, mask, rect, bgd, fgd, iter_count, cv2.GC_INIT_WITH_RECT)
        mask2 = np.where((mask==2)|(mask==0), 0, 1).astype('uint8')*255
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(5,5))
        mask2 = cv2.morphologyEx(mask2, cv2.MORPH_CLOSE, kernel, iterations=2)
        mask2 = cv2.morphologyEx(mask2, cv2.MORPH_OPEN, kernel, iterations=1)
        return mask2
    except Exception as e:
        logging.debug("grabcut failed: %s", e)
        return np.zeros((h,w), dtype=np.uint8)


# KMeans-based HSV cluster mask (optional and downscaled)
def mask_hsv_kmeans(bgr: np.ndarray, downscale: int=4, n_clusters: int=3) -> Optional[np.ndarray]:
    if not HAS_SKLEARN:
        return None
    H0,W0 = bgr.shape[:2]
    if min(H0,W0) < 32:
        return None
    small = cv2.resize(bgr, (max(32, W0//downscale), max(32, H0//downscale)), interpolation=cv2.INTER_AREA)
    hsv = cv2.cvtColor(small, cv2.COLOR_BGR2HSV)
    X = hsv.reshape(-1,3).astype(np.float32)
    try:
        k = min(n_clusters, max(2, int(len(X)/1000)))
        km = KMeans(n_clusters=k, random_state=0, n_init="auto").fit(X)
        labels = km.labels_
        centers = km.cluster_centers_
        # prefer clusters with high saturation*value
        scores = centers[:,1] * centers[:,2]
        idx = int(np.argmax(scores))
        mask_small = (labels.reshape(hsv.shape[:2]) == idx).astype(np.uint8) * 255
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(5,5))
        mask_small = cv2.morphologyEx(mask_small, cv2.MORPH_CLOSE, kernel, iterations=2)
        mask_small = cv2.morphologyEx(mask_small, cv2.MORPH_OPEN, kernel, iterations=1)
        mask = cv2.resize(mask_small, (W0, H0), interpolation=cv2.INTER_NEAREST)
        return mask
    except Exception as e:
        logging.debug("hsv_kmeans failed: %s", e)
        return None


# ----------------------------
# Postprocess utilities
# ----------------------------

def mask_postprocess(mask: Optional[np.ndarray], min_area: int = 500, make_convex: bool = False) -> np.ndarray:
    if mask is None:
        return np.zeros((0,0), dtype=np.uint8)
    m = (mask>0).astype(np.uint8)*255
    if m.size == 0:
        return m
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(5,5))
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, kernel, iterations=2)
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, kernel, iterations=1)
    cnts, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    out = np.zeros_like(m)
    for c in cnts:
        a = int(cv2.contourArea(c))
        if a >= min_area:
            if make_convex:
                hull = cv2.convexHull(c)
                cv2.drawContours(out, [hull], -1, 255, -1)
            else:
                cv2.drawContours(out, [c], -1, 255, -1)
    out = cv2.morphologyEx(out, cv2.MORPH_CLOSE, kernel, iterations=1)
    return out


def largest_component_mask(mask: np.ndarray, min_area: int = 100) -> Optional[np.ndarray]:
    if mask is None or mask.size == 0:
        return None
    cnts, _ = cv2.findContours(mask.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not cnts:
        return None
    areas = [cv2.contourArea(c) for c in cnts]
    idx = int(np.argmax(areas))
    if areas[idx] < min_area:
        return None
    out = np.zeros_like(mask)
    cv2.drawContours(out, [cnts[idx]], -1, 255, -1)
    return out


# def compute_mask_coverage(mask: np.ndarray, crop_shape: Tuple[int,int]) -> float:
#     if mask is None or mask.size == 0:
#         return 0.0
#     h,w = crop_shape[:2]
#     total = h * w
#     if total == 0:
#         return 0.0
#     foreground = int(np.count_nonzero(mask))
#     return foreground / float(total)


# ----------------------------
# Rotation-aware crop
# ----------------------------

# def rotate_crop_by_box(bgr: np.ndarray, box: np.ndarray, margin_frac: float) -> np.ndarray:
#     pts = np.asarray(box, dtype=np.float32)
#     if pts.size == 0:
#         return np.zeros((0,0,3), dtype=np.uint8)
#     rect = cv2.minAreaRect(pts)
#     (cx,cy),(w,h),angle = rect
#     if w <= 0 or h <= 0:
#         return np.zeros((0,0,3), dtype=np.uint8)
#     M = cv2.getRotationMatrix2D((cx,cy), angle, 1.0)
#     H, W = bgr.shape[:2]
#     rotated = cv2.warpAffine(bgr, M, (W, H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)
#     ones = np.ones((pts.shape[0],1), dtype=np.float32)
#     pts_h = np.hstack([pts, ones])
#     rot_pts = (M @ pts_h.T).T
#     x_min = float(rot_pts[:,0].min()); y_min = float(rot_pts[:,1].min())
#     x_max = float(rot_pts[:,0].max()); y_max = float(rot_pts[:,1].max())
#     max_side = max(x_max - x_min, y_max - y_min, 1.0)
#     pad = int(round(max_side * float(margin_frac)))
#     x0 = int(max(0, math.floor(x_min - pad))); y0 = int(max(0, math.floor(y_min - pad)))
#     x1 = int(min(W, math.ceil(x_max + pad))); y1 = int(min(H, math.ceil(y_max + pad)))
#     if x1 <= x0 or y1 <= y0:
#         return np.zeros((0,0,3), dtype=np.uint8)
#     crop = rotated[y0:y1, x0:x1]
#     return crop


def resized_fill(img: np.ndarray, th: int, tw: int) -> np.ndarray:
    H, W = img.shape[:2]
    if H == 0 or W == 0:
        return np.zeros((th, tw, 3), dtype=np.uint8)
    scale = max(tw / W, th / H)
    new_w = int(round(W * scale)); new_h = int(round(H * scale))
    interp = cv2.INTER_CUBIC if scale > 1 else cv2.INTER_AREA
    resized = cv2.resize(img, (new_w, new_h), interpolation=interp)
    left = max(0, (new_w - tw) // 2); top = max(0, (new_h - th) // 2)
    cropped = resized[top: top + th, left: left + tw]
    return cropped


# ----------------------------
# Fusion segmentation (lightweight by default)
# ----------------------------

def default_hsv_ranges():
    return [
        ((15, 60, 60), (45, 255, 255)),
        ((30, 30, 20), (90, 255, 255)),
    ]


def combined_segmentation(bgr: np.ndarray, cfg: PreprocessConfig, debug_prefix: Optional[str] = None) -> Dict[str,Any]:
    meta = {}
    img = bgr.copy()
    H,W = img.shape[:2]
    img_bal = grey_world_balance(img)
    if cfg.use_clahe:
        img_bal = apply_clahe_bgr(img_bal, cfg.clahe_clip, cfg.clahe_grid)

    # base masks
    mask_hsv = mask_by_hsv_adaptive(img_bal)
    mask_otsu = mask_by_otsu(img_bal)
    mask_edge = mask_by_edges(img_bal)

    # combine --- keep operation cheap for fast mode
    fused = cv2.bitwise_or(mask_hsv, mask_otsu)
    fused = cv2.bitwise_or(fused, mask_edge)

    if not cfg.fast:
        # optional heavier methods
        grab = mask_by_grabcut(img_bal)
        fused = cv2.bitwise_or(fused, grab)
        if HAS_SKLEARN:
            kmask = mask_hsv_kmeans(img_bal, downscale=cfg.sample_downscale, n_clusters=cfg.kmeans_clusters)
            if kmask is not None:
                fused = cv2.bitwise_or(fused, kmask)
    else:
        kmask = None

    # cleanup
    min_area = max(150, int(cfg.min_contour_area_fraction * float(H*W)))
    cleaned = mask_postprocess(fused, min_area)
    largest = largest_component_mask(cleaned, min_area=min_area)

    coverage = float((largest>0).sum()) / float(H*W) if (largest is not None and largest.size != 0) else 0.0
    meta.update({'coverage': coverage, 'min_area': min_area, 'has_kmeans': (kmask is not None) if 'kmask' in locals() else False})

    if cfg.save_intermediates and debug_prefix:
        inter_dir = Path(debug_prefix).parent
        ensure_dir(str(inter_dir))
        imwrite_unicode(str(inter_dir / (Path(debug_prefix).stem + "_balanced.jpg")), img_bal)
        imwrite_unicode(str(inter_dir / (Path(debug_prefix).stem + "_fused_mask.png")), fused)
        if largest is not None:
            imwrite_unicode(str(inter_dir / (Path(debug_prefix).stem + "_largest_mask.png")), largest)

    return {
        'img_bal': img_bal,
        'mask_hsv': mask_hsv,
        'mask_otsu': mask_otsu,
        'mask_edge': mask_edge,
        'fused': fused,
        'cleaned': cleaned,
        'largest': largest,
        'meta': meta,
    }


def draw_overlay(bgr: np.ndarray, mask: np.ndarray, alpha: float = 0.38) -> np.ndarray:
    vis = bgr.copy()
    color = (0,255,0)
    colored = np.zeros_like(bgr)
    if mask is not None and mask.shape[:2] == bgr.shape[:2]:
        colored[mask>0] = color
    overlay = cv2.addWeighted(vis, 1.0, colored, alpha, 0)
    if mask is not None and mask.size:
        cnts, _ = cv2.findContours((mask>0).astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cv2.drawContours(overlay, cnts, -1, (0,200,255), 2)
    return overlay


# ----------------------------
# Processing single image (preprocessing-focused)
# ----------------------------

def prepare_image(img: np.ndarray, cfg: PreprocessConfig) -> np.ndarray:
    img_bal = grey_world_balance(img)
    if cfg.use_clahe:
        img_bal = apply_clahe_bgr(img_bal, cfg.clahe_clip, cfg.clahe_grid)
    return img_bal

def process_single_image(src: str, dst: str, cfg: PreprocessConfig, intermediates_root: Optional[str] = None, tuned_params: Optional[Dict[str,Any]] = None) -> Dict[str,Any]:
    """Simplified image processing: color balance, CLAHE, and resize (no cropping)."""
    meta = {"src": src, "dst": dst, "status": "unknown", "timestamp": time.strftime(cfg.timestamp_format)}
    try:
        img = load_image_exif(src, use_exif=cfg.use_exif)
        if img is None:
            meta["status"] = "read_failed"
            logging.warning("Failed to read %s", src)
            return meta

        # Basic preprocessing (white balance + CLAHE)
        img_bal = prepare_image(img, cfg)

        # Resize ke ukuran target
        th, tw = cfg.target_size
        out = cv2.resize(img_bal, (tw, th), interpolation=cv2.INTER_AREA)

        # Simpan hasil
        ensure_dir(str(Path(dst).parent))
        saved = imwrite_unicode(dst, out, quality=cfg.save_quality)
        meta["status"] = "ok" if saved else "save_failed"
        meta["final_w"], meta["final_h"] = tw, th
        return meta

    except Exception as e:
        logging.exception("Error processing %s: %s", src, e)
        meta["status"] = "error"
        meta["exception"] = str(e)
        return meta


# def process_single_image(src: str, dst: str, cfg: PreprocessConfig, intermediates_root: Optional[str] = None, tuned_params: Optional[Dict[str,Any]] = None) -> Dict[str,Any]:
#     meta = {"src": src, "dst": dst, "status": "unknown", "timestamp": time.strftime(cfg.timestamp_format)}
#     try:
#         img = load_image_exif(src, use_exif=cfg.use_exif)
#         if img is None:
#             meta['status'] = 'read_failed'
#             logging.warning("Failed to read %s", src)
#             return meta
#         H0, W0 = img.shape[:2]
#         meta['orig_w'] = int(W0); meta['orig_h'] = int(H0)

#         area = float(H0 * W0)
#         min_contour_area = max(int(max(100, cfg.min_contour_area_fraction * area)), 100)
#         margin = tuned_params.get('margin', cfg.margin) if tuned_params else cfg.margin

#         img_bal = prepare_image(img, cfg)

#         if cfg.save_intermediates and intermediates_root:
#             inter_dir = Path(intermediates_root) / Path(src).parent.name
#             ensure_dir(str(inter_dir))
#             imwrite_unicode(str(inter_dir / (Path(src).stem + "_balanced.jpg")), img_bal, quality=95)

#         # build base mask quickly
#         mask_hsv = mask_by_hsv_adaptive(img_bal)
#         mask_otsu = mask_by_otsu(img_bal)
#         mask_edge = mask_by_edges(img_bal)
#         combined = cv2.bitwise_or(mask_hsv, cv2.bitwise_or(mask_otsu, mask_edge))
#         kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5,5))
#         combined = cv2.morphologyEx(combined, cv2.MORPH_CLOSE, kernel, iterations=2)
#         combined = cv2.morphologyEx(combined, cv2.MORPH_OPEN, kernel, iterations=1)

#         if cfg.save_intermediates and intermediates_root:
#             inter_dir = Path(intermediates_root) / Path(src).parent.name
#             imwrite_unicode(str(inter_dir / (Path(src).stem + "_mask_combined.png")), combined, quality=100)

#         # Attempts to locate the object using increasingly permissive strategies
#         attempt = 0
#         used_strategy = None
#         crop_img = None
#         crop_mask = None

#         while attempt < cfg.max_attempts:
#             if attempt == 0:
#                 target_mask = combined.copy(); try_margin = margin
#             elif attempt == 1:
#                 kernel2 = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9,9))
#                 target_mask = cv2.morphologyEx(combined, cv2.MORPH_CLOSE, kernel2, iterations=2)
#                 try_margin = margin
#             elif attempt == 2:
#                 target_mask = mask_hsv.copy(); try_margin = margin + 0.02
#             else:
#                 target_mask = combined.copy(); try_margin = margin + cfg.margin_increment_steps[min(attempt - 3, len(cfg.margin_increment_steps)-1)]

#             lamr = largest_contour_minarea_rect(target_mask, min_contour_area)
#             if lamr:
#                 box, cnt, cnt_area = lamr
#                 crop_img = rotate_crop_by_box(img_bal, box, try_margin)
#                 crop_mask = rotate_crop_by_box(target_mask, box, try_margin)
#                 used_strategy = f"minarea_attempt_{attempt}"
#             else:
#                 crop_img = None; crop_mask = None

#             if crop_img is not None and crop_img.size:
#                 coverage = compute_mask_coverage((crop_mask>0).astype(np.uint8), crop_img.shape[:2])
#                 meta['coverage'] = float(coverage)
#                 if coverage >= cfg.crop_mask_coverage_threshold:
#                     meta['status'] = 'ok'
#                     break
#             attempt += 1

#         # KMeans fallback (only if enabled and sklearn present)
#         if (crop_img is None or meta.get('coverage',0.0) < cfg.crop_mask_coverage_threshold) and HAS_SKLEARN and not cfg.fast:
#             km_mask = mask_hsv_kmeans(img_bal, downscale=cfg.sample_downscale, n_clusters=cfg.kmeans_clusters)
#             if km_mask is not None:
#                 if cfg.save_intermediates and intermediates_root:
#                     inter_dir = Path(intermediates_root) / Path(src).parent.name
#                     imwrite_unicode(str(inter_dir / (Path(src).stem + "_mask_kmeans.png")), km_mask, quality=100)
#                 lamr2 = largest_contour_minarea_rect(km_mask, max(200, int(min_contour_area/2)))
#                 if lamr2:
#                     box2, cnt2, area2 = lamr2
#                     crop_img2 = rotate_crop_by_box(img_bal, box2, margin + 0.02)
#                     crop_mask2 = rotate_crop_by_box(km_mask, box2, margin + 0.02)
#                     cov2 = compute_mask_coverage((crop_mask2>0).astype(np.uint8), crop_img2.shape[:2])
#                     if cov2 >= cfg.crop_mask_coverage_threshold:
#                         crop_img = crop_img2; crop_mask = crop_mask2
#                         used_strategy = 'kmeans_minarea'
#                         meta['coverage'] = float(cov2); meta['status'] = 'ok'

#         # Axis bbox fallback
#         if (crop_img is None) or (meta.get('coverage',0.0) < cfg.crop_mask_coverage_threshold):
#             cnt_bbox = largest_component_bbox_from_mask(combined, min_area=max(50, int(min_contour_area/4)))
#             if cnt_bbox is not None:
#                 x,y,w,h = cnt_bbox
#                 pad = int(round(max(w,h) * (margin + 0.02)))
#                 x0 = max(0, x - pad); y0 = max(0, y - pad); x1 = min(W0, x + w + pad); y1 = min(H0, y + h + pad)
#                 crop_img = img_bal[y0:y1, x0:x1]
#                 crop_mask = combined[y0:y1, x0:x1]
#                 used_strategy = 'axis_bbox_fallback'
#                 cov = compute_mask_coverage((crop_mask>0).astype(np.uint8), crop_img.shape[:2])
#                 meta['coverage'] = float(cov)
#                 if cov >= cfg.crop_mask_coverage_threshold:
#                     meta['status'] = 'ok'

#         # Center fallback
#         if (crop_img is None) or (meta.get('coverage',0.0) < cfg.crop_mask_coverage_threshold):
#             side = int(round(min(H0, W0) * 0.85))
#             cx, cy = W0//2, H0//2
#             x0 = max(0, cx - side//2); y0 = max(0, cy - side//2)
#             x1 = min(W0, x0 + side); y1 = min(H0, y0 + side)
#             crop_img = img_bal[y0:y1, x0:x1]
#             used_strategy = 'center_fallback'
#             crop_mask = combined[y0:y1, x0:x1]
#             meta['coverage'] = float(compute_mask_coverage((crop_mask>0).astype(np.uint8), crop_img.shape[:2]))
#             meta['status'] = 'fallback_center'

#         if crop_img is None or crop_img.size == 0:
#             meta['status'] = 'crop_failed'
#             logging.error("Crop failed entirely for %s", src)
#             return meta

#         # Resize and save
#         th, tw = cfg.target_size
#         out = resized_fill(crop_img, th, tw)

#         if cfg.save_intermediates and intermediates_root:
#             inter_dir = Path(intermediates_root) / Path(src).parent.name
#             ensure_dir(str(inter_dir))
#             imwrite_unicode(str(inter_dir / (Path(src).stem + "_crop_raw.jpg")), crop_img, quality=95)
#             if crop_mask is not None:
#                 imwrite_unicode(str(inter_dir / (Path(src).stem + "_crop_mask.png")), crop_mask, quality=100)

#         Path(dst).parent.mkdir(parents=True, exist_ok=True)
#         if Path(dst).exists() and not cfg.force:
#             meta['status'] = 'skipped'
#             return meta
#         saved = imwrite_unicode(dst, out, quality=cfg.save_quality)
#         if not saved:
#             meta['status'] = 'save_failed'
#             return meta

#         meta['status'] = 'ok' if meta.get('status') != 'fallback_center' else 'fallback_center'
#         meta['used_strategy'] = used_strategy
#         meta['final_w'] = int(tw); meta['final_h'] = int(th)
#         return meta

#     except Exception as e:
#         logging.exception("Exception processing %s: %s", src, e)
#         meta['status'] = 'error'
#         meta['exception'] = str(e)
#         return meta


# ----------------------------
# Utilities used in pipeline
# ----------------------------

# def largest_contour_minarea_rect(mask: np.ndarray, min_area: int):
#     cnts, _ = cv2.findContours(mask.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
#     if not cnts:
#         return None
#     areas = [cv2.contourArea(c) for c in cnts]
#     idx = int(np.argmax(areas))
#     if areas[idx] < min_area:
#         return None
#     cnt = cnts[idx]
#     rect = cv2.minAreaRect(cnt)
#     box = cv2.boxPoints(rect).astype(int)
#     return box, cnt, areas[idx]


# def largest_component_bbox_from_mask(mask: np.ndarray, min_area: int):
#     cnts, _ = cv2.findContours(mask.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
#     if not cnts:
#         return None
#     areas = [cv2.contourArea(c) for c in cnts]
#     idx = int(np.argmax(areas))
#     if areas[idx] < min_area:
#         return None
#     x,y,w,h = cv2.boundingRect(cnts[idx])
#     return (x,y,w,h)


# ----------------------------
# Batch driver + autotune
# ----------------------------

def collect_input_mapping(raw_dir: str) -> Dict[str, List[str]]:
    p = Path(raw_dir)
    if not p.exists():
        return {}
    classes = [x for x in sorted(p.iterdir()) if x.is_dir()]
    mapping = {}
    for c in classes:
        files = [str(f) for f in sorted(c.rglob("*")) if f.suffix.lower() in (".jpg",".jpeg",".png",".bmp",".tiff")]
        mapping[c.name] = files
    return mapping


# def autotune_parameters(cfg: PreprocessConfig, sample_n: int = 30) -> Dict[str, Any]:
#     np.random.seed(cfg.seed)
#     mapping = collect_input_mapping(cfg.raw_dir)
#     paths = []
#     for cls, files in mapping.items():
#         paths.extend(files)
#     if not paths:
#         raise FileNotFoundError("No files found for autotune")
#     sample_n = min(sample_n, len(paths))
#     samples = list(np.random.choice(paths, sample_n, replace=False))
#     margins_to_try = [0.02, 0.04, 0.06, 0.08, 0.10, 0.14, 0.18]
#     good_margins = []
#     logging.info("Autotune: sampling %d images", len(samples))
#     for p in samples:
#         img = load_image_exif(p, use_exif=cfg.use_exif)
#         if img is None:
#             continue
#         img_bal = prepare_image(img, cfg)
#         combined = mask_by_hsv_adaptive(img_bal)
#         combined = cv2.bitwise_or(combined, mask_by_otsu(img_bal))
#         combined = cv2.bitwise_or(combined, mask_by_edges(img_bal))
#         kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(5,5))
#         combined = cv2.morphologyEx(combined, cv2.MORPH_CLOSE, kernel, iterations=2)
#         area = float(img.shape[0] * img.shape[1])
#         min_contour_area = max(int(area * cfg.min_contour_area_fraction), 100)
#         found_good = False
#         for m in margins_to_try:
#             lamr = largest_contour_minarea_rect(combined, min_contour_area)
#             if lamr:
#                 box, cnt, cnt_area = lamr
#                 crop_img = rotate_crop_by_box(img_bal, box, m)
#                 crop_mask = rotate_crop_by_box(combined, box, m)
#                 cov = compute_mask_coverage((crop_mask > 0).astype(np.uint8), crop_img.shape[:2])
#                 if cov >= cfg.crop_mask_coverage_threshold:
#                     good_margins.append(m); found_good = True; break
#         if not found_good and HAS_SKLEARN and not cfg.fast:
#             kmask = mask_hsv_kmeans(img_bal, downscale=cfg.sample_downscale, n_clusters=cfg.kmeans_clusters)
#             if kmask is not None:
#                 lamr2 = largest_contour_minarea_rect(kmask, max(200, int(min_contour_area/2)))
#                 if lamr2:
#                     box2, cnt2, _ = lamr2
#                     m2 = cfg.margin
#                     crop_img = rotate_crop_by_box(img_bal, box2, m2)
#                     crop_mask = rotate_crop_by_box(kmask, box2, m2)
#                     cov2 = compute_mask_coverage((crop_mask>0).astype(np.uint8), crop_img.shape[:2])
#                     if cov2 >= cfg.crop_mask_coverage_threshold:
#                         good_margins.append(m2)
#     if not good_margins:
#         logging.warning("Autotune found nothing consistent; using default margin %.3f", cfg.margin)
#         return {"margin": cfg.margin}
#     chosen = float(np.median(np.array(good_margins)))
#     logging.info("Autotune chosen margin = %.4f (from %d good samples)", chosen, len(good_margins))
#     return {"margin": chosen}


def run_pipeline(cfg: PreprocessConfig, tuned: Optional[Dict[str,Any]] = None):
    mapping = collect_input_mapping(cfg.raw_dir)
    if not mapping:
        logging.error("No classes found in %s", cfg.raw_dir)
        return
    ensure_dir(cfg.out_dir)
    review_root = Path(cfg.review_save_path)
    if cfg.review_mode:
        ensure_dir(str(review_root)); ensure_dir(str(review_root / cfg.reject_folder_name))
    intermediates_root = None
    if cfg.save_intermediates or cfg.debug:
        intermediates_root = str(Path(cfg.out_dir) / "_intermediates")
        ensure_dir(intermediates_root)

    results = []
    items = []
    for cls, files in mapping.items():
        out_cls = Path(cfg.out_dir) / cls
        out_cls.mkdir(parents=True, exist_ok=True)
        for f in files:
            dst = str(out_cls / Path(f).name)
            items.append((f, dst, cls))

    total = len(items)
    logging.info("Processing %d images across %d classes (mode=%s, workers=%d, fast=%s)", total, len(mapping), cfg.mode, cfg.workers, cfg.fast)
    iterator = items if tqdm is None else tqdm(items, desc="Processing", ncols=120)

    # concurrency
    def worker(entry):
        src, dst, cls = entry
        if Path(dst).exists() and not cfg.force:
            return {"src": src, "dst": dst, "class": cls, "status": "skipped"}
        meta = process_single_image(src, dst, cfg, intermediates_root, tuned_params=tuned)
        meta['class'] = cls
        return meta

    if cfg.workers > 1:
        with concurrent.futures.ThreadPoolExecutor(max_workers=cfg.workers) as ex:
            futures = [ex.submit(worker, it) for it in iterator]
            for fut in concurrent.futures.as_completed(futures):
                try:
                    res = fut.result()
                except Exception as e:
                    logging.exception("Worker exception: %s", e)
                    res = {"status": "error", "exception": str(e)}
                results.append(res)
    else:
        for it in iterator:
            results.append(worker(it))

    # write metadata
    ts = time.strftime(cfg.timestamp_format)
    meta_csv = Path(cfg.out_dir) / f"metadata_{ts}.csv"
    try:
        df = pd.DataFrame(results)
        df.to_csv(str(meta_csv), index=False)
        summary = {
            "total": len(results),
            "ok": int((df['status']=='ok').sum()) if 'status' in df.columns else 0,
            "skipped": int((df['status']=='skipped').sum()) if 'status' in df.columns else 0,
            "failed": int((df['status']!='ok').sum()) if 'status' in df.columns else 0,
        }
        json_path = Path(cfg.out_dir) / f"summary_{ts}.json"
        with open(str(json_path), "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)
        logging.info("Saved metadata %s and summary %s", str(meta_csv), str(json_path))
    except Exception:
        logging.exception("Failed to write metadata/summary")


# ----------------------------
# Simple interactive review
# ----------------------------

def interactive_review(cfg: PreprocessConfig):
    review_dir = Path(cfg.review_save_path) / cfg.reject_folder_name
    if not review_dir.exists():
        logging.error("No review rejects found at %s", str(review_dir))
        return
    files = list(review_dir.glob("*"))
    if not files:
        logging.info("No files to review.")
        return
    idx = 0
    while idx < len(files):
        f = files[idx]
        src = str(f)
        logging.info("Reviewing %s (%d/%d)", src, idx+1, len(files))
        preview = imread_unicode(src)
        if preview is None:
            logging.warning("Cannot read preview %s", src)
            idx += 1
            continue
        cv2.imshow("Review (y accept / n reject / q quit)", preview)
        k = cv2.waitKey(0) & 0xFF
        if k == ord('y'):
            logging.info("Accepted %s", src); idx += 1
        elif k == ord('n'):
            logging.info("Rejected %s", src); idx += 1
        elif k == ord('q'):
            logging.info("User requested quit review"); break
        else:
            logging.info("Key %d pressed; skipping", k); idx += 1
    cv2.destroyAllWindows()


# ----------------------------
# Self-test (synthetic)
# ----------------------------

def create_synthetic_dataset(base_dir: str = "tmp_raw", classes: int = 3, per_class: int = 6):
    ensure_dir(base_dir)
    rng = np.random.RandomState(0)
    for ci in range(classes):
        cdir = Path(base_dir) / f"grade_{ci}"
        ensure_dir(str(cdir))
        for i in range(per_class):
            h = rng.randint(300,800); w = rng.randint(300,800)
            img = np.ones((h,w,3), dtype=np.uint8)*255
            color = (int(rng.randint(10,220)), int(rng.randint(80,250)), int(rng.randint(80,250)))
            center = (w//2, h//2); axes = (w//4, h//6); angle = rng.randint(0,359)
            cv2.ellipse(img, center, axes, angle, 0, 360, color, -1)
            fname = str(cdir / f"image_{i}.jpg")
            imwrite_unicode(fname, img, quality=95)
    return base_dir


def run_self_test():
    tmp = create_synthetic_dataset()
    cfg = PreprocessConfig(raw_dir=tmp, out_dir='tmp_dataset_out', debug=True, save_intermediates=True, verbose=True, force=True, workers=1)
    tuned = None
    run_pipeline(cfg, tuned)
    shutil.rmtree(tmp, ignore_errors=True)
    shutil.rmtree('tmp_dataset_out', ignore_errors=True)
    print("Self-test done (temp folders removed)")


# ----------------------------
# CLI
# ----------------------------

def parse_cli():
    p = argparse.ArgumentParser(description="Robust preprocessing for Sortir Buah Jagung")
    p.add_argument("--raw_dir", type=str, default=None)
    p.add_argument("--out_dir", type=str, default=None)
    p.add_argument("--target_size", nargs=2, type=int, default=None, help="H W")
    p.add_argument("--margin", type=float, default=None)
    p.add_argument("--min_area_frac", type=float, default=None)
    p.add_argument("--no_exif", action="store_true")
    p.add_argument("--no_clahe", action="store_true")
    p.add_argument("--debug", action="store_true")
    p.add_argument("--save_intermediates", action="store_true")
    p.add_argument("--force", action="store_true")
    p.add_argument("--verbose", action="store_true")
    p.add_argument("--autotune", type=int, default=None, help="autotune with N samples")
    p.add_argument("--review", action="store_true")
    p.add_argument("--self_test", action="store_true")
    p.add_argument("--tune", type=str, default=None, help="HSV tuner for single image")
    p.add_argument("--mode", type=str, default="preprocess", choices=("preprocess","segmentation"), help="Operation mode")
    p.add_argument("--workers", type=int, default=None, help="Number of worker threads (default = cpu-1)")
    p.add_argument("--fast", action="store_true", help="Enable fast mode (skip expensive segmentation)")
    return p.parse_args()


def main():
    args = parse_cli()
    cfg = PreprocessConfig()
    if args.raw_dir: cfg.raw_dir = args.raw_dir
    if args.out_dir: cfg.out_dir = args.out_dir
    if args.target_size: cfg.target_size = (int(args.target_size[0]), int(args.target_size[1]))
    if args.margin is not None: cfg.margin = float(args.margin)
    if args.min_area_frac is not None: cfg.min_contour_area_fraction = float(args.min_area_frac)
    if args.no_exif: cfg.use_exif = False
    if args.no_clahe: cfg.use_clahe = False
    if args.debug: cfg.debug = True
    if args.save_intermediates: cfg.save_intermediates = True
    if args.force: cfg.force = True
    if args.verbose: cfg.verbose = True
    if args.autotune: cfg.autotune_samples = int(args.autotune)
    if args.review: cfg.review_mode = True
    if args.tune: pass
    cfg.mode = args.mode
    if args.workers is not None:
        cfg.workers = max(1, int(args.workers))
    if args.fast:
        cfg.fast = True

    setup_logging(cfg.verbose)

    if args.self_test:
        run_self_test(); return

    if args.tune:
        hsv_tuner(args.tune); return

    if not Path(cfg.raw_dir).exists():
        logging.error("raw_dir '%s' not found. Place images under raw_data/<class>", cfg.raw_dir)
        sys.exit(2)

    Path(cfg.out_dir).mkdir(parents=True, exist_ok=True)

    tuned = None
    # if cfg.autotune_samples:
    #     try:
    #         tuned = autotune_parameters(cfg, sample_n=cfg.autotune_samples)
    #         logging.info("Autotune result: %s", str(tuned))
    #     except Exception:
    #         logging.exception("Autotune failed; continuing with defaults")

    run_pipeline(cfg, tuned)

    if cfg.review_mode:
        logging.info("Starting interactive review (requires GUI).")
        try:
            interactive_review(cfg)
        except Exception:
            logging.exception("Interactive review failed or not supported here.")

    logging.info("Processing complete.")


if __name__ == "__main__":
    main()
