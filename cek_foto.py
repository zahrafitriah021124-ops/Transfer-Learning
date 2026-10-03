import os
import sys

import cv2
import numpy as np

EKSTENSI = {".jpg", ".jpeg", ".png", ".bmp"}

if len(sys.argv) > 1:
    folder = sys.argv[1]
else:
    folder = input("Tempel path folder foto: ")
folder = folder.strip().strip('"')

if not os.path.isdir(folder):
    print("Folder tidak ditemukan:", folder)
    sys.exit(1)

semua = sorted(
    n for n in os.listdir(folder)
    if os.path.splitext(n)[1].lower() in EKSTENSI
)

bisa = 0
gagal = []
ukuran = set()

for n in semua:
    jalur = os.path.join(folder, n)
    try:
        data = np.fromfile(jalur, dtype=np.uint8)
        img = cv2.imdecode(data, cv2.IMREAD_COLOR)
    except OSError as e:
        gagal.append((n, "tidak bisa dibuka"))
        continue
    if img is None:
        gagal.append((n, "isi file rusak"))
        continue
    bisa += 1
    h, w = img.shape[:2]
    ukuran.add((w, h))

print("=" * 50)
print("Folder            :", folder)
print("Total file gambar :", len(semua))
print("Bisa dibaca       :", bisa)
print("Gagal dibaca      :", len(gagal))
print("Ukuran (w,h)      :", sorted(ukuran))
for n, sebab in gagal[:15]:
    print(f"  - {n}  ({sebab})")
if len(gagal) > 15:
    print(f"  ... dan {len(gagal) - 15} lainnya")