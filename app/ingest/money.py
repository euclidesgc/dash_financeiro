from decimal import Decimal


class FractionalCentsError(ValueError):
    def __init__(self, value: object) -> None:
        super().__init__(f"value does not convert to whole cents: {value!r}")
        self.value = value


def to_cents(value: float | str) -> int:
    # Decimal(str(value)) keeps the two decimal places the source declares;
    # value * 100 on a float rounds on its own and loses a cent silently.
    cents = Decimal(str(value)) * 100
    if cents != cents.to_integral_value():
        raise FractionalCentsError(value)
    return int(cents)
