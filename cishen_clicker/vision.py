from __future__ import annotations

from pathlib import Path

from .config import Thresholds
from .model import Candidate, Cell, GridConfig, Rect, iter_grid_cells


def load_templates(templates_dir: Path) -> list:
    cv2, _np = _cv()
    templates = []
    if not templates_dir.exists():
        return templates

    for path in sorted(templates_dir.glob("*")):
        if path.suffix.lower() not in {".png", ".jpg", ".jpeg", ".bmp"}:
            continue
        image = cv2.imread(str(path), cv2.IMREAD_COLOR)
        if image is not None:
            templates.append((path.name, image))
    return templates


def analyze_grid(image, grid: GridConfig, thresholds: Thresholds, templates: list | None = None) -> list[Candidate]:
    templates = templates or []
    candidates = []

    for cell in iter_grid_cells(grid):
        cell_image = crop_rect(image, cell.rect)
        score, reason = score_cell(cell_image, thresholds, templates)
        reachable = reason not in {"empty-crop", "unreachable"}
        candidates.append(
            Candidate(
                cell=cell,
                score=score,
                clickable=reachable and score >= thresholds.min_score,
                reason=reason,
                reachable=reachable,
            )
        )

    return candidates


def detect_login_conflict_dialog(image) -> bool:
    cv2, np = _cv()
    if image.size == 0:
        return False

    height, width = image.shape[:2]
    if height < 200 or width < 200:
        return False

    center = image[
        round(height * 0.30) : round(height * 0.72),
        round(width * 0.08) : round(width * 0.92),
    ]
    lower_center = image[
        round(height * 0.48) : round(height * 0.68),
        round(width * 0.16) : round(width * 0.84),
    ]
    if center.size == 0 or lower_center.size == 0:
        return False

    hsv_center = cv2.cvtColor(center, cv2.COLOR_BGR2HSV)
    white_mask = (
        (hsv_center[:, :, 1] <= 35)
        & (hsv_center[:, :, 2] >= 215)
    )
    white_ratio = float(np.count_nonzero(white_mask) / white_mask.size)

    hsv_lower = cv2.cvtColor(lower_center, cv2.COLOR_BGR2HSV)
    hue = hsv_lower[:, :, 0]
    saturation = hsv_lower[:, :, 1]
    value = hsv_lower[:, :, 2]
    green_mask = (
        (hue >= 45)
        & (hue <= 85)
        & (saturation >= 80)
        & (value >= 120)
    )
    green_ratio = float(np.count_nonzero(green_mask) / green_mask.size)

    return white_ratio >= 0.42 and green_ratio >= 0.035


def score_cell(cell_image, thresholds: Thresholds, templates: list) -> tuple[float, str]:
    cv2, np = _cv()
    if cell_image.size == 0:
        return 0.0, "empty-crop"

    if not _is_reachable_cell(cell_image, thresholds, cv2, np):
        return 0.0, "unreachable"

    template_score, template_name = _best_template_score(cell_image, templates)
    if template_score >= thresholds.template_threshold:
        brightness, saturation = _brightness_saturation(cell_image)
        if brightness >= thresholds.min_brightness and saturation >= thresholds.min_saturation:
            return template_score, f"template:{template_name}"
        return template_score * 0.65, f"dim-template:{template_name}"

    brightness, saturation = _brightness_saturation(cell_image)
    mineral_score, mineral_reason = _mineral_color_score(cell_image, thresholds, cv2, np)
    if mineral_score >= thresholds.min_score:
        return mineral_score, mineral_reason
    shape_score, shape_reason = _mineral_shape_score(cell_image, thresholds, cv2, np)
    if shape_score >= thresholds.min_score:
        return shape_score, shape_reason

    edge_score = _edge_score(cell_image, cv2, np)
    color_score = min(1.0, max(0.0, (saturation - thresholds.min_saturation) / 80.0))
    light_score = min(1.0, max(0.0, (brightness - thresholds.min_brightness) / 90.0))
    content_score = min(1.0, edge_score * 2.4 + color_score * 0.45)
    score = min(mineral_score, min(1.0, content_score * 0.40 + light_score * 0.20))

    if content_score < thresholds.min_content_score:
        return min(score, thresholds.min_score - 0.05), "low-mineral-color"
    if brightness < thresholds.min_brightness:
        return min(score, thresholds.min_score - 0.05), "dim"
    if saturation < thresholds.min_saturation:
        return min(score, thresholds.min_score - 0.05), "low-saturation"
    return min(score, thresholds.min_score - 0.05), "low-mineral-color"


def crop_rect(image, rect: Rect):
    x1 = max(0, round(rect.x))
    y1 = max(0, round(rect.y))
    x2 = max(x1, round(rect.x + rect.width))
    y2 = max(y1, round(rect.y + rect.height))
    return image[y1:y2, x1:x2]


def annotate_candidates(image, candidates: list[Candidate], min_score: float):
    cv2, _np = _cv()
    annotated = image.copy()
    for candidate in candidates:
        rect = candidate.cell.rect
        p1 = (round(rect.x), round(rect.y))
        p2 = (round(rect.x + rect.width), round(rect.y + rect.height))
        if not candidate.reachable:
            color = (150, 150, 150)
        elif candidate.clickable and candidate.score >= min_score:
            color = (0, 220, 0)
        else:
            color = (80, 80, 230)
        cv2.rectangle(annotated, p1, p2, color, 2)
        cv2.putText(
            annotated,
            f"{candidate.cell.row},{candidate.cell.col} {candidate.score:.2f}",
            (p1[0] + 3, p1[1] + 15),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.42,
            color,
            1,
            cv2.LINE_AA,
        )
    return annotated


def _best_template_score(cell_image, templates: list) -> tuple[float, str]:
    cv2, _np = _cv()
    best_score = 0.0
    best_name = ""
    for name, template in templates:
        if template.shape[0] > cell_image.shape[0] or template.shape[1] > cell_image.shape[1]:
            continue
        result = cv2.matchTemplate(cell_image, template, cv2.TM_CCOEFF_NORMED)
        _min_val, max_val, _min_loc, _max_loc = cv2.minMaxLoc(result)
        if max_val > best_score:
            best_score = float(max_val)
            best_name = name
    return best_score, best_name


def _brightness_saturation(image) -> tuple[float, float]:
    cv2, _np = _cv()
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    return float(hsv[:, :, 2].mean()), float(hsv[:, :, 1].mean())


def _is_reachable_cell(image, thresholds: Thresholds, cv2, np) -> bool:
    center = _center_crop(image, margin_ratio=0.18)
    hsv = cv2.cvtColor(center, cv2.COLOR_BGR2HSV)
    value = hsv[:, :, 2]
    bright_ratio = float(np.count_nonzero(value >= thresholds.min_reachable_brightness) / value.size)
    upper_value = float(np.percentile(value, 75))
    return (
        upper_value >= thresholds.min_reachable_brightness
        and bright_ratio >= thresholds.min_reachable_bright_pixel_ratio
    )


def _mineral_color_score(image, thresholds: Thresholds, cv2, np) -> tuple[float, str]:
    center = _center_crop(image, margin_ratio=0.14)
    hsv = cv2.cvtColor(center, cv2.COLOR_BGR2HSV)
    hue = hsv[:, :, 0]
    saturation = hsv[:, :, 1]
    value = hsv[:, :, 2]

    red_mask = (((hue <= 12) | (hue >= 168)) & (saturation >= 90) & (value >= 150))
    orange_mask = ((hue >= 13) & (hue <= 26) & (saturation >= 85) & (value >= 170))
    yellow_mask = ((hue >= 27) & (hue <= 42) & (saturation >= 70) & (value >= 160))
    purple_mask = ((hue >= 135) & (hue <= 165) & (saturation >= 60) & (value >= 150))
    blue_mask = ((hue >= 95) & (hue <= 130) & (saturation >= 55) & (value >= 90))

    ratios = {
        "red": float(np.count_nonzero(red_mask) / red_mask.size),
        "orange": float(np.count_nonzero(orange_mask) / orange_mask.size),
        "yellow": float(np.count_nonzero(yellow_mask) / yellow_mask.size),
        "purple": float(np.count_nonzero(purple_mask) / purple_mask.size),
        "blue": float(np.count_nonzero(blue_mask) / blue_mask.size),
    }
    best_name, best_ratio = max(ratios.items(), key=lambda item: item[1])
    if best_ratio < thresholds.min_mineral_color_ratio:
        return min(0.6, best_ratio / max(thresholds.min_mineral_color_ratio, 0.001) * 0.55), "low-mineral-color"

    score = min(1.0, 0.62 + best_ratio * 1.8)
    reason_prefix = "valuable-color" if best_name in {"red", "orange", "yellow", "purple"} else "mineral-color"
    return score, f"{reason_prefix}:{best_name}"


def _mineral_shape_score(image, thresholds: Thresholds, cv2, np) -> tuple[float, str]:
    center = _center_crop(image, margin_ratio=0.18)
    hsv = cv2.cvtColor(center, cv2.COLOR_BGR2HSV)
    hue = hsv[:, :, 0]
    saturation = hsv[:, :, 1]
    value = hsv[:, :, 2]
    gray = cv2.cvtColor(center, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 45, 130)

    edge_ratio = float(np.count_nonzero(edges) / edges.size)
    dark_edge_ratio = float(np.count_nonzero((edges > 0) & (value < 150)) / edges.size)
    brown_detail_ratio = float(
        np.count_nonzero((hue >= 8) & (hue <= 28) & (saturation >= 45) & (value >= 45))
        / value.size
    )

    if edge_ratio >= 0.04 and dark_edge_ratio >= 0.035 and brown_detail_ratio >= 0.035:
        return min(1.0, 0.66 + edge_ratio * 1.5 + brown_detail_ratio * 0.2), "mineral-shape"
    return 0.0, "low-mineral-shape"


def _center_crop(image, margin_ratio: float):
    height, width = image.shape[:2]
    margin_x = min(width // 2, max(0, round(width * margin_ratio)))
    margin_y = min(height // 2, max(0, round(height * margin_ratio)))
    return image[margin_y : height - margin_y, margin_x : width - margin_x]


def _edge_score(image, cv2, np) -> float:
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 50, 140)
    return float(np.count_nonzero(edges) / edges.size)


def _cv():
    try:
        import cv2
        import numpy as np
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "Missing vision dependencies. Install them with: python -m pip install -r requirements.txt"
        ) from exc
    return cv2, np
