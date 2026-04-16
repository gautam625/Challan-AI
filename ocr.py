import re
import cv2
import numpy as np
import pytesseract
from pathlib import Path

# ── Tesseract path (Windows only; ignored on Linux) ──────────────────────────
import sys, os
if sys.platform == "win32":
    pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    os.environ['TESSDATA_PREFIX'] = r"C:\Program Files\Tesseract-OCR\tessdata"

# ── Load cascade ONCE ─────────────────────────────────────────────────────────
_CASCADE_PATH = Path(__file__).parent / "haarcascade_russian_plate_number.xml"
_cascade = cv2.CascadeClassifier(str(_CASCADE_PATH))

# ── Compiled patterns ─────────────────────────────────────────────────────────
_PLATE_RE   = re.compile(r'[A-Z]{2}[0-9]{2}[A-Z]{1,3}[0-9]{4}')
_STRIP_RE   = re.compile(r'[^A-Z0-9]')

# ── Tesseract config (2 passes: psm 7 on gray, psm 8 on thresh) ───────────────
_TESS_CFG = r'--oem 3 --psm 7 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
_TESS_CFG2= r'--oem 3 --psm 8 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'

# character substitution map (index → expected type)
_ALPHA_IDX = {0, 1, 4, 5}
_NUM_IDX   = {2, 3, 6, 7, 8, 9}
_TO_ALPHA  = {'0':'O','1':'I','8':'B'}
_TO_NUM    = {'O':'0','I':'1','B':'8','Z':'2'}


def _fix_format(text: str) -> str:
    chars = list(_STRIP_RE.sub('', text.upper()))
    if len(chars) < 8:
        return ''.join(chars)
    for i, ch in enumerate(chars):
        if i in _ALPHA_IDX:
            chars[i] = _TO_ALPHA.get(ch, ch)
        elif i in _NUM_IDX:
            chars[i] = _TO_NUM.get(ch, ch)
    return ''.join(chars)


def _preprocess(plate_bgr: np.ndarray):
    """Return (gray_upscaled, adaptive_thresh)."""
    gray = cv2.cvtColor(plate_bgr, cv2.COLOR_BGR2GRAY)
    gray = cv2.resize(gray, None, fx=2.5, fy=2.5, interpolation=cv2.INTER_CUBIC)
    kernel = np.array([[0,-1,0],[-1,5,-1],[0,-1,0]])
    gray = cv2.filter2D(gray, -1, kernel)
    gray = cv2.bilateralFilter(gray, 9, 17, 17)
    thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 11, 2)
    return gray, thresh


def detect_plate(img_bgr: np.ndarray):
    gray_full = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    plates = _cascade.detectMultiScale(gray_full, scaleFactor=1.1, minNeighbors=4)
    annotated = img_bgr.copy()
    if len(plates) == 0:
        return annotated, None
    x, y, w, h = plates[0]
    cv2.rectangle(annotated, (x, y), (x+w, y+h), (0, 0, 255), 3)
    return annotated, img_bgr[y:y+h, x:x+w]


def read_plate(plate_bgr: np.ndarray) -> str:
    """
    OCR on a plate ROI.  Returns a cleaned plate string or 'UNKNOWN'.
    """
    gray, thresh = _preprocess(plate_bgr)

    candidates = []
    for img, cfg in [(gray, _TESS_CFG), (thresh, _TESS_CFG2)]:
        raw = pytesseract.image_to_string(img, config=cfg)
        fixed = _fix_format(raw)
        m = _PLATE_RE.search(fixed)
        if m:
            candidates.append(m.group())

    if candidates:
        # pick the most common candidate (handles tie with first)
        return max(set(candidates), key=candidates.count)

    # fallback: longest cleaned string
    best = ""
    for img, cfg in [(gray, _TESS_CFG)]:
        raw = _STRIP_RE.sub('', pytesseract.image_to_string(img, config=cfg).upper())
        if len(raw) > len(best):
            best = raw
    return best or "UNKNOWN"
