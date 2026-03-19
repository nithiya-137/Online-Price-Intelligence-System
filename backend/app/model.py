import tensorflow as tf
from tensorflow.keras.applications.mobilenet_v2 import MobileNetV2, decode_predictions
import numpy as np
import os
import io
import hashlib
from concurrent.futures import ThreadPoolExecutor
from PIL import Image, ImageFilter

# ── Model Loading ──────────────────────────────────────────────────────────────
print("Loading MobileNetV2 model...")
model = MobileNetV2(weights="imagenet")
print("Model loaded. Warming up...")
model.predict(np.zeros((1, 224, 224, 3)), verbose=0)
print("Warmup complete.")

# ── OCR Setup ─────────────────────────────────────────────────────────────────
try:
    import pytesseract
    TESSERACT_PATHS = [
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Users\nilay\AppData\Local\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    ]
    for p in TESSERACT_PATHS:
        if os.path.exists(p):
            pytesseract.pytesseract.tesseract_cmd = p
            break
except ImportError:
    pytesseract = None

executor = ThreadPoolExecutor(max_workers=4)
prediction_cache = {}


# ── FULL ImageNet → Product Mapping ───────────────────────────────────────────
IMAGENET_TO_PRODUCT = {
    # Smartphones & Tablets
    "cellular_telephone":   "Smartphone",
    "mobile_phone":         "Smartphone",
    "hand-held_computer":   "Smartphone",
    "handheld_computer":    "Smartphone",
    "phone":                "Smartphone",
    "pager":                "Smartphone",
    "iPod":                 "Apple iPod",
    "ipod":                 "Apple iPod",
    "remote_control":       "Smartphone",
    "joystick":             "Smartphone",
    "dial_telephone":       "Landline Phone",
    "pay-phone":            "Landline Phone",
    "pay_phone":            "Landline Phone",
    "tablet_computer":      "Tablet",

    # Laptops & Computers
    "laptop":               "Laptop",
    "notebook":             "Laptop",
    "laptop_computer":      "Laptop",
    "desktop_computer":     "Desktop Computer",
    "personal_computer":    "Desktop PC",
    "monitor":              "Computer Monitor",
    "screen":               "Computer Monitor",
    "television":           "Smart TV",
    "home_theater":         "Home Theater System",
    "projector":            "HD Projector",

    # Keyboards, Mice, Peripherals
    "computer_keyboard":    "Mechanical Keyboard",
    "keyboard":             "Mechanical Keyboard",
    "computer_mouse":       "Wireless Mouse",
    "mouse":                "Wireless Mouse",
    "trackball":            "Trackball Mouse",
    "printer":              "Inkjet Printer",
    "modem":                "WiFi Router",
    "hard_disc":            "External Hard Drive",
    "hard_disk":            "External Hard Drive",
    "calculator":           "Calculator",

    # Cameras
    "digital_camera":       "Digital Camera",
    "camera":               "Digital Camera",
    "reflex_camera":        "DSLR Camera",
    "Polaroid_camera":      "Instant Camera",
    "polaroid_camera":      "Instant Camera",
    "movie_camera":         "Video Camera",
    "camcorder":            "Video Camera",
    "camera_lens":          "Camera Lens",
    "tripod":               "Camera Tripod",

    # Audio
    "loudspeaker":          "Bluetooth Speaker",
    "speaker":              "Bluetooth Speaker",
    "microphone":           "Studio Microphone",
    "headphone":            "Headphones",
    "earphone":             "Wireless Earbuds",
    "harmonica":            "Wireless Earbuds",
    "ocarina":              "Wireless Earbuds",
    "whistle":              "Wireless Earbuds",
    "radio":                "Portable Speaker",
    "cassette_player":      "Portable Speaker",

    # Wearables
    "wristwatch":           "Smartwatch",
    "digital_watch":        "Smartwatch",
    "analog_clock":         "Watch",
    "watch":                "Smartwatch",
    "sundial":              "Smartwatch",
    "sunglasses":           "Sunglasses",
    "sunglass":             "Sunglasses",
    "goggle":               "Sports Goggles",
    "sweatshirt":           "Sweatshirt",
    "jersey":               "Sports Jersey",
    "suit":                 "Formal Suit",

    # Footwear
    "running_shoe":         "Running Shoes",
    "shoe":                 "Sports Shoes",
    "sneaker":              "Sneakers",
    "sandal":               "Sandals",
    "clog":                 "Clogs",
    "loafer":               "Loafers",
    "boot":                 "Boots",
    "cowboy_boot":          "Cowboy Boots",
    "athletic_shoe":        "Athletic Shoes",
    "flip-flop":            "Flip Flops",

    # Bags & Accessories
    "backpack":             "Laptop Backpack",
    "rucksack":             "Backpack",
    "handbag":              "Handbag",
    "purse":                "Purse",
    "wallet":               "Leather Wallet",
    "briefcase":            "Briefcase",
    "suitcase":             "Travel Suitcase",
    "umbrella":             "Umbrella",

    # Skincare & Beauty
    "lotion":               "Body Lotion",
    "sunscreen":            "Sunscreen",
    "pill_bottle":          "Skincare",
    "soap_dispenser":       "Face Wash",
    "vial":                 "Skincare Serum",
    "perfume":              "Perfume",
    "lipstick":             "Lipstick",
    "hair_dryer":           "Hair Dryer",
    "electric_razor":       "Electric Shaver",
    "shampoo":              "Shampoo",
    "cream":                "Face Cream",
    "bottle":               "Skincare Product",
    "petri_dish":           "Skincare",
    "beaker":               "Skincare Bottle",
    "pot":                  "Face Cream",
    "vase":                 "Skincare Jar",
    "medicine_chest":       "Skincare Kit",
    "water_bottle":         "Water Bottle",
    "canteen":              "Water Bottle",

    # Gaming
    "game_controller":      "Gaming Controller",
    "space_invaders":       "Gaming Console",
    "jigsaw_puzzle":        "Board Game",
    "chessboard":           "Chess Set",

    # Home Appliances
    "refrigerator":         "Refrigerator",
    "washing_machine":      "Washing Machine",
    "dishwasher":           "Dishwasher",
    "vacuum":               "Vacuum Cleaner",
    "vacuum_cleaner":       "Vacuum Cleaner",
    "blender":              "Blender",
    "coffee_maker":         "Coffee Maker",
    "espresso_maker":       "Espresso Machine",
    "toaster":              "Toaster",
    "microwave":            "Microwave Oven",
    "iron":                 "Steam Iron",
    "clothes_iron":         "Steam Iron",
    "hair_dryer":           "Hair Dryer",
    "hair_straightener":    "Hair Straightener",
    "curling_iron":         "Hair Curler",
    "air_conditioner":      "Air Conditioner",
    "ceiling_fan":          "Ceiling Fan",
    "electric_fan":         "Table Fan",

    # Kitchen
    "frying_pan":           "Frying Pan",
    "wok":                  "Wok",
    "ladle":                "Kitchen Ladle",
    "spatula":              "Cooking Spatula",
    "strainer":             "Kitchen Strainer",
    "grater":               "Box Grater",
    "pressure_cooker":      "Pressure Cooker",

    # Furniture
    "table_lamp":           "Table Lamp",
    "floor_lamp":           "Floor Lamp",
    "couch":                "Sofa",
    "pillow":               "Pillow",

    # Tools
    "power_drill":          "Power Drill",
    "screwdriver":          "Screwdriver",
    "hammer":               "Hammer",
    "wrench":               "Wrench",

    # Sports & Fitness
    "dumbbell":             "Dumbbell",
    "barbell":              "Barbell",
    "treadmill":            "Treadmill",
    "bicycle":              "Bicycle",
    "basketball":           "Basketball",
    "soccer_ball":          "Football",
    "tennis_ball":          "Tennis Ball",
    "golf_ball":            "Golf Ball",
    "golf_club":            "Golf Club",

    # Books & Stationery
    "book_jacket":          "Book",
    "ballpoint":            "Ball Pen",
    "pencil_box":           "Pencil Box",
    "pencil_sharpener":     "Pencil Sharpener",
    "rubber_eraser":        "Eraser",
    "ruler":                "Ruler",

    # Toys
    "teddy":                "Teddy Bear",
    "teddy_bear":           "Teddy Bear",
    "doll":                 "Doll",

    # Misc Electronics
    "power_strip":          "Extension Board",
    "extension_cord":       "Extension Board",
    "adapter":              "Charger Adapter",
    "modem":                "WiFi Router",
}


# ── Confusion Label Groups ─────────────────────────────────────────────────────
PHONE_CONFUSION_LABELS = {
    "remote_control", "cellular_telephone", "mobile_phone",
    "hand-held_computer", "handheld_computer", "ipod", "pager",
    "harmonica", "ruler", "spatula", "loudspeaker",
    "oboe", "flute", "clarinet",
}

LAPTOP_CONFUSION_LABELS = {
    "monitor", "screen", "television", "notebook",
    "laptop", "desktop_computer", "book_jacket",
}

EARBUDS_CONFUSION_LABELS = {
    "harmonica", "ocarina", "whistle", "iPod",
    "pill", "marble", "ping-pong_ball",
}

SKINCARE_KEYWORDS = {
    "pill_bottle", "lotion", "soap_dispenser", "vial", "shampoo",
    "perfume", "lipstick", "hair_dryer", "electric_razor", "bottle",
    "beaker", "petri_dish", "pot", "sunscreen", "cream", "vase",
}

# Brand sets for OCR matching
PHONE_BRANDS     = {"apple", "samsung", "oneplus", "xiaomi", "realme", "oppo", "vivo", "nokia", "motorola", "google"}
LAPTOP_BRANDS    = {"dell", "hp", "lenovo", "asus", "acer", "microsoft", "apple", "lg", "toshiba", "huawei"}
BEAUTY_BRANDS    = {"neutrogena", "nivea", "lakme", "biore", "cetaphil", "pupa", "mamaearth", "wow", "biotique", "himalaya", "loreal", "garnier", "dove"}
SHOE_BRANDS      = {"nike", "adidas", "puma", "reebok", "skechers", "bata", "woodland", "new balance", "asics", "converse"}
APPLIANCE_BRANDS = {"bosch", "philips", "lg", "samsung", "whirlpool", "godrej", "haier", "panasonic", "hitachi", "siemens"}
ALL_BRANDS       = PHONE_BRANDS | LAPTOP_BRANDS | BEAUTY_BRANDS | SHOE_BRANDS | APPLIANCE_BRANDS


# ── Visual Signal Helpers ──────────────────────────────────────────────────────

def _get_aspect_ratio(raw_bytes: bytes) -> float:
    """Returns height/width. >1 = portrait, <1 = landscape."""
    try:
        img = Image.open(io.BytesIO(raw_bytes))
        w, h = img.size
        return h / w if w > 0 else 1.0
    except Exception:
        return 1.0


def _get_color_profile(raw_bytes: bytes) -> dict:
    """
    Analyses image at low resolution (64x64) to detect:
    - white_fraction:    how much is pure white (product photo background)
    - dark_fraction:     how much is near-black (dark phone/laptop body)
    - light_fraction:    how much is light-coloured (skincare, white products)
    - colorful_fraction: how much has high saturation (shoes, clothing, packaging)
    """
    try:
        img = Image.open(io.BytesIO(raw_bytes)).convert("RGB").resize((64, 64))
        arr = np.array(img, dtype=np.float32)

        white_fraction    = float(np.all(arr > 220, axis=2).mean())
        dark_fraction     = float(np.all(arr < 60,  axis=2).mean())
        light_fraction    = float(np.all(arr > 180, axis=2).mean())

        max_c = arr.max(axis=2)
        min_c = arr.min(axis=2)
        saturation = max_c - min_c
        colorful_fraction = float((saturation > 60).mean())

        return {
            "white":    white_fraction,
            "dark":     dark_fraction,
            "light":    light_fraction,
            "colorful": colorful_fraction,
        }
    except Exception:
        return {"white": 0, "dark": 0, "light": 0, "colorful": 0}


def _get_edge_density(raw_bytes: bytes) -> float:
    """
    Returns mean edge density in the centre of the image (0.0–1.0).
    High = complex device (keyboard, camera). Low = smooth product (phone, bottle).
    """
    try:
        img = Image.open(io.BytesIO(raw_bytes)).convert("L").resize((128, 128))
        edges = img.filter(ImageFilter.FIND_EDGES)
        arr = np.array(edges, dtype=np.float32)
        h, w = arr.shape
        cx, cy = h // 2, w // 2
        pad_h, pad_w = int(h * 0.3), int(w * 0.3)
        center = arr[cx - pad_h:cx + pad_h, cy - pad_w:cy + pad_w]
        return float(center.mean()) / 255.0
    except Exception:
        return 0.5


# ── OCR Helper ────────────────────────────────────────────────────────────────

def _run_ocr(raw_bytes: bytes) -> str:
    if not pytesseract or not raw_bytes:
        return ""
    try:
        img = Image.open(io.BytesIO(raw_bytes))
        max_dim = 1024
        if max(img.size) > max_dim:
            scale = max_dim / max(img.size)
            new_size = (int(img.size[0] * scale), int(img.size[1] * scale))
            img = img.resize(new_size, Image.Resampling.LANCZOS)
        return pytesseract.image_to_string(img).strip().lower()
    except Exception as e:
        print(f"OCR error: {e}")
        return ""


# ── Label Cleaner ─────────────────────────────────────────────────────────────

def _clean_label(raw_label: str) -> str:
    if raw_label in IMAGENET_TO_PRODUCT:
        return IMAGENET_TO_PRODUCT[raw_label]
    lower = raw_label.lower()
    if lower in IMAGENET_TO_PRODUCT:
        return IMAGENET_TO_PRODUCT[lower]
    for key, product in IMAGENET_TO_PRODUCT.items():
        if key.lower() in lower or lower in key.lower():
            return product
    return raw_label.replace("_", " ").title()


# ── Cache ─────────────────────────────────────────────────────────────────────

def _get_image_hash(image_bytes: bytes) -> str:
    return hashlib.sha256(image_bytes).hexdigest()


# ── Main Prediction Function ──────────────────────────────────────────────────

def predict_image(processed_image: np.ndarray, top_k: int = 5, raw_bytes: bytes = None) -> list:
    """
    Multi-signal product identification system.

    Pipeline:
      1. Run MobileNetV2 for top-5 labels
      2. In parallel: OCR, aspect ratio, colour profile, edge density
      3. Apply 7-layer heuristic voting (lowest to highest priority):
            Stationery → Skincare → Earbuds → Laptop → Phone → LowConfFallback → OCR Brand
      4. Return predictions list with search_query, label, confidence
    """
    try:
        # ── Cache check ───────────────────────────────────────────────────
        img_hash = None
        if raw_bytes:
            img_hash = _get_image_hash(raw_bytes)
            if img_hash in prediction_cache:
                print(f"[Cache] Hit {img_hash[:8]}")
                return prediction_cache[img_hash]

        # ── Launch parallel visual analysis ───────────────────────────────
        ocr_future    = executor.submit(_run_ocr, raw_bytes)            if raw_bytes else None
        aspect_future = executor.submit(_get_aspect_ratio, raw_bytes)   if raw_bytes else None
        color_future  = executor.submit(_get_color_profile, raw_bytes)  if raw_bytes else None
        edge_future   = executor.submit(_get_edge_density, raw_bytes)   if raw_bytes else None

        # ── Model inference ───────────────────────────────────────────────
        predictions = model.predict(processed_image, verbose=0)
        decoded = decode_predictions(predictions, top=top_k)[0]

        results = []
        for _, label, score in decoded:
            results.append({
                "label": label,
                "search_query": _clean_label(label),
                "confidence": float(score),
            })

        top_confidence = results[0]["confidence"] if results else 0.0

        # ── Collect parallel results ──────────────────────────────────────
        ocr_text = ""
        try:
            ocr_text = ocr_future.result(timeout=10) if ocr_future else ""
        except Exception:
            pass

        aspect_ratio = 1.0
        try:
            aspect_ratio = aspect_future.result(timeout=3) if aspect_future else 1.0
        except Exception:
            pass

        colors = {"white": 0, "dark": 0, "light": 0, "colorful": 0}
        try:
            colors = color_future.result(timeout=3) if color_future else colors
        except Exception:
            pass

        edge_density = 0.5
        try:
            edge_density = edge_future.result(timeout=3) if edge_future else 0.5
        except Exception:
            pass

        labels_lower = {r["label"].lower() for r in results}

        # ────────────────────────────────────────────────────────────────────
        # HEURISTIC VOTING — 7 layers, lowest to highest priority
        # Each layer inserts a boosted result at index 0 if triggered.
        # Later layers override earlier ones.
        # ────────────────────────────────────────────────────────────────────

        # H1: Stationery
        if any(x in labels_lower for x in {"rubber_eraser", "pencil_box", "pencil_sharpener"}):
            results.insert(0, {
                "label": "stationery_inferred",
                "search_query": "Pencil Set",
                "confidence": results[0]["confidence"],
                "boosted": True,
            })

        # H2: Skincare / Bottle
        is_skincare_label = any(kw in labels_lower for kw in SKINCARE_KEYWORDS)
        is_skincare_shape = (
            colors["white"] > 0.40
            and colors["dark"] < 0.15
            and colors["colorful"] < 0.25
            and edge_density < 0.35
        )
        if is_skincare_label or (is_skincare_shape and top_confidence < 0.30):
            best_skincare = next(
                (r for r in results if r["label"].lower() in SKINCARE_KEYWORDS),
                results[0]
            )
            results.insert(0, {
                "label": best_skincare["label"],
                "search_query": best_skincare["search_query"],
                "confidence": max(best_skincare["confidence"], 0.55),
                "boosted": True,
                "reason": "Skincare shape/label detected",
            })

        # H3: Earbuds
        is_earbud_label = any(x in labels_lower for x in EARBUDS_CONFUSION_LABELS)
        is_earbud_shape = (
            colors["white"] > 0.50
            and 0.85 < aspect_ratio < 1.15
            and edge_density < 0.25
        )
        if is_earbud_label and is_earbud_shape:
            results.insert(0, {
                "label": "earbuds_inferred",
                "search_query": "Wireless Earbuds",
                "confidence": min(0.80, results[0]["confidence"] + 0.15),
                "boosted": True,
                "reason": "Earbuds shape + confusion label",
            })

        # H4: Laptop
        is_laptop_label = any(x in labels_lower for x in LAPTOP_CONFUSION_LABELS)
        is_laptop_shape = (
            aspect_ratio < 0.85
            and edge_density > 0.40
            and colors["dark"] > 0.20
        )
        if is_laptop_label and is_laptop_shape:
            results.insert(0, {
                "label": "laptop_inferred",
                "search_query": "Laptop",
                "confidence": min(0.88, results[0]["confidence"] + 0.15),
                "boosted": True,
                "reason": "Laptop: landscape + keyboard edges",
            })

        # H5: Smartphone
        is_phone_label = any(x in labels_lower for x in PHONE_CONFUSION_LABELS)
        is_phone_shape = (
            aspect_ratio > 1.4
            and colors["dark"] > 0.08
            and colors["white"] > 0.25
        )
        is_phone_visual_only = (
            aspect_ratio > 1.55
            and colors["dark"] > 0.12
            and colors["white"] > 0.30
            and edge_density < 0.30
        )
        if (is_phone_label and is_phone_shape) or is_phone_visual_only:
            boosted_conf = min(0.90, results[0]["confidence"] + 0.20)
            print(
                f"[PhoneFix] Boosting to Smartphone "
                f"(labels={labels_lower & PHONE_CONFUSION_LABELS}, "
                f"portrait={aspect_ratio:.2f}, dark={colors['dark']:.2f}, white={colors['white']:.2f})"
            )
            results.insert(0, {
                "label": "smartphone_inferred",
                "search_query": "Smartphone",
                "confidence": boosted_conf,
                "boosted": True,
                "reason": "Phone heuristic: shape + label voting",
            })

        # H6: Low-confidence fallback
        # If model confidence < 0.15, use only visual signals to avoid absurd outputs
        if top_confidence < 0.15:
            if aspect_ratio > 1.4 and colors["dark"] > 0.08:
                fallback_query = "Smartphone"
            elif aspect_ratio < 0.85 and edge_density > 0.35:
                fallback_query = "Laptop"
            elif colors["white"] > 0.50 and colors["colorful"] < 0.20:
                fallback_query = "Skincare Product"
            elif colors["colorful"] > 0.35:
                fallback_query = "Sports Shoes"
            else:
                fallback_query = "Electronics"

            print(f"[LowConfFallback] conf={top_confidence:.3f}, fallback={fallback_query}")
            results.insert(0, {
                "label": "visual_fallback",
                "search_query": fallback_query,
                "confidence": 0.40,
                "boosted": True,
                "reason": f"Low model confidence ({top_confidence:.2f}), visual signals used",
            })

        # H7: OCR Brand Override — highest priority
        if ocr_text:
            detected_brand = next((b for b in ALL_BRANDS if b in ocr_text), "")
            if detected_brand:
                brand_title = detected_brand.title()
                if detected_brand in PHONE_BRANDS:
                    search_q = f"{brand_title} Smartphone"
                elif detected_brand in LAPTOP_BRANDS:
                    search_q = f"{brand_title} Laptop"
                elif detected_brand in BEAUTY_BRANDS:
                    search_q = f"{brand_title} Skincare"
                elif detected_brand in SHOE_BRANDS:
                    search_q = f"{brand_title} Shoes"
                elif detected_brand in APPLIANCE_BRANDS:
                    search_q = f"{brand_title} Appliance"
                else:
                    search_q = f"{brand_title} Product"

                print(f"[OCR Brand] '{brand_title}' → '{search_q}'")
                results.insert(0, {
                    "label": "OCR_BRAND_DETECTION",
                    "search_query": search_q,
                    "confidence": 0.97,
                    "boosted": True,
                    "reason": f"Brand '{brand_title}' detected via OCR",
                })

            elif any(kw in ocr_text for kw in {"sunscreen", "spf", "sunblock", "uv", "serum", "moisturizer"}):
                results.insert(0, {
                    "label": "OCR_SKINCARE",
                    "search_query": "Sunscreen Skincare",
                    "confidence": 0.93,
                    "boosted": True,
                    "reason": "Skincare text detected via OCR",
                })

        # ── Save to cache ──────────────────────────────────────────────────
        if img_hash:
            if len(prediction_cache) > 100:
                prediction_cache.clear()
            prediction_cache[img_hash] = results

        return results

    except Exception as e:
        print(f"[predict_image ERROR] {e}")
        return []
