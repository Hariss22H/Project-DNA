"""Convert Project DNA logo white background to transparent PNG assets."""

from pathlib import Path

from PIL import Image

SRC = Path(
    r"C:\Users\Asus\.cursor\projects\e-Hackathon\assets"
    r"\c__Users_Asus_AppData_Roaming_Cursor_User_workspaceStorage_"
    r"4c21f7789fde5f1ed5328eb038d54514_images_WhatsApp_Image_2026-08-02_at_09.44.54-b776c5de-532f-485d-8921-7bdaaf18661b.png"
)
OUT_DIR = Path(__file__).resolve().parents[1] / "public"


def make_transparent(img: Image.Image) -> Image.Image:
    img = img.convert("RGBA")
    pixels = img.load()
    w, h = img.size
    for y in range(h):
        for x in range(w):
            r, g, b, _a = pixels[x, y]
            if r > 245 and g > 245 and b > 245:
                pixels[x, y] = (r, g, b, 0)
            elif r > 230 and g > 230 and b > 230:
                whiteness = min(r, g, b)
                alpha = max(0, int(255 * (255 - whiteness) / 25))
                pixels[x, y] = (r, g, b, alpha)
    bbox = img.getbbox()
    return img.crop(bbox) if bbox else img


def lighten_for_dark_bg(img: Image.Image) -> Image.Image:
    dark = img.copy()
    pixels = dark.load()
    w, h = dark.size
    for y in range(h):
        for x in range(w):
            r, g, b, a = pixels[x, y]
            if a < 10:
                continue
            is_blueish = b > r + 25 and b > g
            luminance = 0.2126 * r + 0.7152 * g + 0.0722 * b
            if not is_blueish and luminance < 80:
                pixels[x, y] = (236, 235, 243, a)
            elif not is_blueish and luminance < 120:
                t = (120 - luminance) / 40
                nr = int(r + (236 - r) * t)
                ng = int(g + (235 - g) * t)
                nb = int(b + (243 - b) * t)
                pixels[x, y] = (nr, ng, nb, a)
    return dark


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    img = make_transparent(Image.open(SRC))
    full_path = OUT_DIR / "project-dna-logo.png"
    img.save(full_path, "PNG")
    print("full", img.size, full_path)

    iw, ih = img.size
    icon = img.crop((0, 0, int(iw * 0.28), ih))
    bbox = icon.getbbox()
    if bbox:
        icon = icon.crop(bbox)
    pad = 8
    side = max(icon.size) + pad * 2
    canvas = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    canvas.paste(icon, ((side - icon.size[0]) // 2, (side - icon.size[1]) // 2), icon)
    mark_path = OUT_DIR / "project-dna-mark.png"
    canvas.save(mark_path, "PNG")
    print("mark", canvas.size, mark_path)

    dark = lighten_for_dark_bg(img)
    dark_path = OUT_DIR / "project-dna-logo-dark.png"
    dark.save(dark_path, "PNG")
    print("dark", dark.size, dark_path)


if __name__ == "__main__":
    main()
