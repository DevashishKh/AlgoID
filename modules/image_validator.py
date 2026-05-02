"""
modules/image_validator.py
Validates whether an uploaded image is likely a microscopy image.

Multi-check heuristic pipeline (no heavy ML required):
  1. Aspect ratio       - microscope frames are near-square
  2. Colour saturation  - microscopy is low-saturation / near-greyscale
  3. Sky detection      - bright blue upper region = outdoor photo
  4. Skin-tone check    - skin-dominated = portrait / selfie
  5. Edge density       - biological samples have fine, dense edges
  6. Background unif.   - microscopes have large uniform background regions
  7. EXIF metadata      - smartphone EXIF (GPS, Make=Apple/Samsung) -> reject
"""

import numpy as np
from PIL import Image, ExifTags

# ---- Thresholds -------------------------------------------------------------
T = {
    "max_aspect_ratio":               2.2,
    "max_saturation_normal":          90,
    "max_saturation_strict":          60,
    "min_background_fraction_normal": 0.10,
    "min_background_fraction_strict": 0.15,
    "min_edge_density":               0.02,
    "max_edge_density":               0.65,
    "max_sky_fraction":               0.15,
    "max_skin_fraction":              0.20,
    "min_accept_score_normal":        0.45,
    "min_accept_score_strict":        0.60,
}

REJECTION_MESSAGES = {
    "aspect_ratio": "Image is too wide/tall — microscopy frames are near-square.",
    "saturation":   "Image appears too colourful for a microscopy photo.",
    "sky":          "Sky-like blue regions detected — this looks like an outdoor photo.",
    "skin":         "Skin-tone regions detected — this looks like a portrait or selfie.",
    "exif_camera":  "Smartphone/consumer-camera EXIF detected — upload a microscope image.",
    "exif_gps":     "GPS metadata found — microscope images never contain GPS data.",
    "low_score":    "Image does not match the expected profile of a microscopy image.",
}

PHONE_BRANDS = {
    "apple", "samsung", "huawei", "xiaomi", "oppo", "vivo", "google",
    "oneplus", "motorola", "nokia", "realme", "iphone", "android", "sony",
}
SCOPE_BRANDS = {
    "olympus", "leica", "zeiss", "nikon instruments", "keyence",
    "motic", "optika", "euromex", "labomed", "carl zeiss",
}


def validate_microscopy_image(image, strict=False):
    """
    Validate that the image is likely a microscopy photograph.

    Parameters
    ----------
    image  : PIL.Image.Image
    strict : bool  -- apply tighter thresholds

    Returns
    -------
    dict
        is_valid : bool
        score    : float  0-1  (higher = more microscopy-like)
        reasons  : list[str]  human-readable rejection reasons
        checks   : dict       per-check detail
    """
    img_rgb = image.convert("RGB")
    arr = np.array(img_rgb, dtype=np.float32)
    h, w = arr.shape[:2]

    checks = {}
    reasons = []
    score_parts = []

    # 1. Aspect ratio
    ratio = max(w, h) / max(min(w, h), 1)
    ar_ok = ratio <= T["max_aspect_ratio"]
    checks["aspect_ratio"] = {"value": round(ratio, 2), "ok": ar_ok}
    score_parts.append(1.0 if ar_ok else 0.0)
    if not ar_ok:
        reasons.append(REJECTION_MESSAGES["aspect_ratio"])

    # 2. Colour saturation via HSV
    hsv_arr = np.array(img_rgb.convert("HSV"), dtype=np.float32)
    mean_sat = float(hsv_arr[:, :, 1].mean())
    sat_lim = T["max_saturation_strict"] if strict else T["max_saturation_normal"]
    sat_ok = mean_sat <= sat_lim
    checks["saturation"] = {"value": round(mean_sat, 1), "ok": sat_ok}
    sat_score = max(0.0, 1.0 - (mean_sat - sat_lim) / max(sat_lim, 1))
    score_parts.append(min(sat_score, 1.0))
    if not sat_ok and mean_sat > sat_lim * 1.5:
        reasons.append(REJECTION_MESSAGES["saturation"])

    # 3. Sky detection (blue dominance in top third)
    top = arr[: h // 3, :, :]
    sky_mask = (
        (top[:, :, 2] > 120)
        & (top[:, :, 2] > top[:, :, 0] + 20)
        & (top[:, :, 2] > top[:, :, 1] + 10)
    )
    sky_frac = float(sky_mask.sum()) / max(sky_mask.size, 1)
    sky_ok = sky_frac <= T["max_sky_fraction"]
    checks["sky_fraction"] = {"value": round(sky_frac, 3), "ok": sky_ok}
    score_parts.append(1.0 if sky_ok else max(0.0, 1.0 - sky_frac * 5))
    if not sky_ok:
        reasons.append(REJECTION_MESSAGES["sky"])

    # 4. Skin-tone detection
    r = arr[:, :, 0]
    g = arr[:, :, 1]
    b = arr[:, :, 2]
    skin_mask = (
        (r > 95)
        & (g > 40)
        & (b > 20)
        & (r > g)
        & (r > b)
        & (np.abs(r.astype(int) - g.astype(int)) > 15)
        & (r - np.minimum(g, b) > 15)
    )
    skin_frac = float(skin_mask.sum()) / max(skin_mask.size, 1)
    skin_ok = skin_frac <= T["max_skin_fraction"]
    checks["skin_fraction"] = {"value": round(skin_frac, 3), "ok": skin_ok}
    score_parts.append(1.0 if skin_ok else max(0.0, 1.0 - skin_frac * 4))
    if not skin_ok:
        reasons.append(REJECTION_MESSAGES["skin"])

    # 5. Edge density (Sobel approximation)
    grey = np.mean(arr, axis=2)
    gx = np.abs(np.diff(grey, axis=1))
    gy = np.abs(np.diff(grey, axis=0))
    edge_density = float(
        (gx[: gy.shape[0], :] + gy[:, : gx.shape[1]]).mean()
    ) / 255.0
    edge_ok = T["min_edge_density"] <= edge_density <= T["max_edge_density"]
    checks["edge_density"] = {"value": round(edge_density, 4), "ok": edge_ok}
    if edge_density < T["min_edge_density"]:
        edge_score = edge_density / T["min_edge_density"]
    elif edge_density > T["max_edge_density"]:
        edge_score = max(0.0, 1.0 - (edge_density - T["max_edge_density"]))
    else:
        edge_score = 1.0
    score_parts.append(edge_score)

    # 6. Background uniformity
    median_val = float(np.median(grey))
    bg_frac = float((np.abs(grey - median_val) < 25).sum()) / max(grey.size, 1)
    bg_lim = (
        T["min_background_fraction_strict"]
        if strict
        else T["min_background_fraction_normal"]
    )
    bg_ok = bg_frac >= bg_lim
    checks["background_uniformity"] = {"value": round(bg_frac, 3), "ok": bg_ok}
    score_parts.append(min(bg_frac / max(bg_lim, 0.01), 1.0))

    # 7. EXIF metadata
    exif_camera = False
    exif_gps = False
    try:
        exif_raw = image._getexif() if hasattr(image, "_getexif") else None
        if exif_raw:
            tag_map = {v: k for k, v in ExifTags.TAGS.items()}
            for tag_name in ["Make", "Model", "Software"]:
                tid = tag_map.get(tag_name)
                if tid and tid in exif_raw:
                    val = str(exif_raw[tid]).lower()
                    if any(b in val for b in PHONE_BRANDS):
                        exif_camera = True
            gps_tid = tag_map.get("GPSInfo")
            if gps_tid and gps_tid in exif_raw:
                exif_gps = True
    except Exception:
        pass

    checks["exif_camera"] = {"value": exif_camera, "ok": not exif_camera}
    checks["exif_gps"] = {"value": exif_gps, "ok": not exif_gps}
    score_parts.append(0.0 if exif_camera else 1.0)
    score_parts.append(0.0 if exif_gps else 1.0)
    if exif_camera:
        reasons.append(REJECTION_MESSAGES["exif_camera"])
    if exif_gps:
        reasons.append(REJECTION_MESSAGES["exif_gps"])

    # Final score and verdict
    final_score = sum(score_parts) / len(score_parts)
    min_score = (
        T["min_accept_score_strict"] if strict else T["min_accept_score_normal"]
    )
    hard_fail = any([not ar_ok, not sky_ok, not skin_ok, exif_camera, exif_gps])
    is_valid = (not hard_fail) and (final_score >= min_score)
    if not is_valid and not reasons:
        reasons.append(REJECTION_MESSAGES["low_score"])

    return {
        "is_valid": is_valid,
        "score": round(final_score, 3),
        "reasons": reasons,
        "checks": checks,
    }


def validation_summary_html(result):
    """Return a compact HTML badge for display in Streamlit."""
    colour = "#27ae60" if result["is_valid"] else "#e74c3c"
    bg = "#eafaf1" if result["is_valid"] else "#fdedec"
    icon = "OK" if result["is_valid"] else "REJECTED"
    label = (
        "Accepted as microscopy image"
        if result["is_valid"]
        else "Not a microscopy image"
    )
    pct = result["score"] * 100
    items = "".join("<li>{}</li>".format(r) for r in result["reasons"])
    ul = (
        "<ul style='margin:6px 0 0;padding-left:1.2rem'>{}</ul>".format(items)
        if items
        else ""
    )
    return (
        "<div style='border:1px solid {colour};border-radius:8px;"
        "padding:10px 14px;background:{bg}'>"
        "<strong style='color:{colour}'>[{icon}] {label}</strong> "
        "<span style='color:#555;font-size:0.85rem'>(score: {pct:.0f}%)</span>"
        "{ul}</div>"
    ).format(colour=colour, bg=bg, icon=icon, label=label, pct=pct, ul=ul)
