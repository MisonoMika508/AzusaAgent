# -*- coding: utf-8 -*-

from dataclasses import dataclass

from .settings import ASPECT_RATIO_TOLERANCE


@dataclass(frozen=True)
class CoordinateTransform:
    scale_x: float
    scale_y: float
    screen_width: int
    screen_height: int

    def map_element(self, element):
        x = round(element["x"] * self.scale_x)
        y = round(element["y"] * self.scale_y)
        width = round(element["width"] * self.scale_x)
        height = round(element["height"] * self.scale_y)
        center_x = round(element["center_x"] * self.scale_x)
        center_y = round(element["center_y"] * self.scale_y)

        return {
            **element,
            "x": x,
            "y": y,
            "width": width,
            "height": height,
            "center_x": center_x,
            "center_y": center_y,
            "bbox": [x, y, x + width, y + height],
            "center": [center_x, center_y],
        }


def create_coordinate_transform(
    template_width,
    template_height,
    screen_width,
    screen_height,
):
    values = (template_width, template_height, screen_width, screen_height)
    if any(int(value) <= 0 for value in values):
        return None, "invalid_resolution"

    template_ratio = template_width / template_height
    screen_ratio = screen_width / screen_height
    ratio_delta = abs(screen_ratio - template_ratio) / template_ratio
    if ratio_delta > ASPECT_RATIO_TOLERANCE:
        return None, "aspect_ratio_mismatch"

    scale_x = screen_width / template_width
    scale_y = screen_height / template_height
    scale_delta = abs(scale_x - scale_y) / max(scale_x, scale_y)
    if scale_delta > ASPECT_RATIO_TOLERANCE:
        return None, "non_uniform_scaling"

    return CoordinateTransform(
        scale_x=scale_x,
        scale_y=scale_y,
        screen_width=screen_width,
        screen_height=screen_height,
    ), ""
