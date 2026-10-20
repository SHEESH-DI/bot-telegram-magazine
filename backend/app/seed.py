"""Два демонстрационных товара; запускать явно, не при старте реплик."""

from io import BytesIO

from PIL import Image

from app.db import connect
from app.storage import save_photo


def main():
    for name, color, key, price in [
        ("Кружка", "lightblue", "demo/cup.jpg", 49900),
        ("Блокнот", "khaki", "demo/notebook.jpg", 29900),
    ]:
        buffer = BytesIO()
        Image.new("RGB", (320, 240), color).save(buffer, format="JPEG")
        save_photo(key, buffer.getvalue())
        with connect() as conn:
            conn.execute(
                "INSERT INTO product (name, image_key, price_kopecks) VALUES (%s, %s, %s) ON CONFLICT (image_key) DO NOTHING",
                (name, key, price),
            )
    print("Демонстрационные товары добавлены")


if __name__ == "__main__":
    main()
