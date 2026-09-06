def _components(color: str) -> tuple[int, int, int]:
    digits = color.strip().lstrip("#")
    if len(digits) == 3:
        digits = "".join(digit * 2 for digit in digits)
    if len(digits) != 6:
        raise ValueError(f"expected a 3 or 6 digit hex color, got {color!r}")
    return int(digits[0:2], 16), int(digits[2:4], 16), int(digits[4:6], 16)


def _channel(value: int) -> float:
    share = value / 255
    if share <= 0.03928:
        return share / 12.92
    return ((share + 0.055) / 1.055) ** 2.4


def _relative_luminance(color: str) -> float:
    red, green, blue = _components(color)
    return 0.2126 * _channel(red) + 0.7152 * _channel(green) + 0.0722 * _channel(blue)


def contrast_ratio(hex_a: str, hex_b: str) -> float:
    first = _relative_luminance(hex_a)
    second = _relative_luminance(hex_b)
    lighter = max(first, second)
    darker = min(first, second)
    return (lighter + 0.05) / (darker + 0.05)
