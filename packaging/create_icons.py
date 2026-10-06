"""Generate consistent Windows and Store icons from the VeloraDock mark."""
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / 'veloradock' / 'public'
ASSETS = ROOT / 'packaging' / 'Assets'
ASSETS.mkdir(exist_ok=True)
PUBLIC.mkdir(exist_ok=True)
image = Image.new('RGBA', (1024, 1024), '#10283a')
draw = ImageDraw.Draw(image)
draw.rounded_rectangle((70, 70, 954, 954), radius=210, fill='#153b49')
draw.ellipse((210, 205, 814, 809), fill='#246578')
draw.polygon([(255, 330), (405, 330), (512, 615), (620, 330), (770, 330), (575, 745), (450, 745)], fill='#8af1cd')
draw.rounded_rectangle((225, 790, 800, 835), radius=22, fill='#f0d8a8')
for name, size in [('Square44x44Logo.png', 44), ('Square150x150Logo.png', 150), ('StoreLogo.png', 50)]:
    image.resize((size, size), Image.Resampling.LANCZOS).save(ASSETS / name)
image.resize((512, 512), Image.Resampling.LANCZOS).save(PUBLIC / 'logo.png')
image.save(PUBLIC / 'app.ico', sizes=[(16,16),(24,24),(32,32),(48,48),(64,64),(128,128),(256,256)])
(PUBLIC / 'logo.svg').write_text('''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1024 1024"><rect width="1024" height="1024" rx="230" fill="#10283a"/><rect x="70" y="70" width="884" height="884" rx="210" fill="#153b49"/><circle cx="512" cy="507" r="302" fill="#246578"/><path d="M255 330h150l107 285 108-285h150L575 745H450Z" fill="#8af1cd"/><rect x="225" y="790" width="575" height="45" rx="22" fill="#f0d8a8"/></svg>''', encoding='utf-8')
