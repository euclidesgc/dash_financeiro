from app.settings.typed import InvalidValueError, parse_money, parse_rate


def show(reader, typed):
    try:
        print(f"{reader.__name__} {typed!r}: {reader(typed)}")
    except InvalidValueError:
        print(f"{reader.__name__} {typed!r}: recusado")


for typed in ("5000.00", "inf", "nan", "1e308", "2.500,00"):
    show(parse_money, typed)
for typed in ("nan", "200", "3,52"):
    show(parse_rate, typed)
