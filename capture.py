import os
import sys
from datetime import datetime

import cv2
import numpy as np

indeks = int(sys.argv[1]) if len(sys.argv) > 1 else 0
folder = sys.argv[2] if len(sys.argv) > 2 else r"C:\RET503_data\foto_redup"
os.makedirs(folder, exist_ok=True)

cap = cv2.VideoCapture(indeks, cv2.CAP_DSHOW)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

if not cap.isOpened():
    print(f"Kamera indeks {indeks} tidak bisa dibuka.")
    print("Coba indeks lain, misalnya: python capture.py 1")
    sys.exit(1)

ok, frame = cap.read()
if not ok:
    print("Gagal membaca frame dari kamera.")
    cap.release()
    sys.exit(1)

h, w = frame.shape[:2]
print(f"Kamera indeks {indeks} | ukuran frame: {w} x {h}")
if (w, h) != (640, 480):
    print("PERHATIAN: ukuran bukan 640x480. Foto lama berukuran 640x480.")
print("Folder simpan :", folder)
print("SPASI = simpan foto | q = keluar\n")

jumlah = 0
while True:
    ok, frame = cap.read()
    if not ok:
        print("Frame gagal dibaca, berhenti.")
        break

    abu = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    terang = float(np.mean(abu))

    tampil = frame.copy()
    cv2.putText(tampil, f"tersimpan: {jumlah} | kecerahan: {terang:.0f}/255",
                (8, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.55,
                (0, 255, 255), 1, cv2.LINE_AA)
    cv2.putText(tampil, "SPASI=simpan  q=keluar", (8, 470),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1, cv2.LINE_AA)
    cv2.imshow("capture", tampil)

    k = cv2.waitKey(1) & 0xFF
    if k == ord("q"):
        break
    if k == 32:  # spasi
        nama = datetime.now().strftime("%Y%m%d_%H%M%S_%f") + ".jpg"
        jalur = os.path.join(folder, nama)
        sukses, buf = cv2.imencode(".jpg", frame)
        if sukses:
            buf.tofile(jalur)
            jumlah += 1
            print(f"[{jumlah}] {nama} | kecerahan {terang:.0f}")

cap.release()
cv2.destroyAllWindows()
print(f"\nSelesai. {jumlah} foto tersimpan di {folder}")