import csv
import os
import re
import sys

import cv2
import numpy as np

KELAS = {"b": "botol", "n": "bukan_botol"}
WARNA = {"botol": (0, 200, 0), "bukan_botol": (0, 0, 255)}  # BGR
EKSTENSI = {".jpg", ".jpeg", ".png", ".bmp"}
UKURAN_MIN = 24  # sisi crop minimal (piksel)
TARGET = 50      # minimal crop per kelas
KOLOM = ["nama_file", "kelas", "tanggal", "kondisi_cahaya", "foto_sumber", "kotak"]

SINI = os.path.dirname(os.path.abspath(__file__))
KELUAR = os.path.join(SINI, "dataset_raw")
CSV_PATH = os.path.join(KELUAR, "metadata.csv")


def baca(jalur):
    """Baca gambar; kembalikan None kalau file tidak bisa dibaca."""
    try:
        data = np.fromfile(jalur, dtype=np.uint8)
    except OSError as e:
        print(f"  [lewati] tidak bisa dibuka: {e}")
        return None
    return cv2.imdecode(data, cv2.IMREAD_COLOR)


def simpan_png(jalur, gambar):
    ok, buf = cv2.imencode(".png", gambar)
    if ok:
        buf.tofile(jalur)


def tanggal_dari_nama(nama):
    m = re.search(r"(20\d{6})", nama)
    if not m:
        return "tidak_diketahui"
    g = m.group(1)
    return f"{g[:4]}-{g[4:6]}-{g[6:]}"


def tulis_csv(rows):
    with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=KOLOM)
        w.writeheader()
        w.writerows(rows)


def hitung(rows):
    jumlah = {k: 0 for k in KELAS.values()}
    for r in rows:
        if r["kelas"] in jumlah:
            jumlah[r["kelas"]] += 1
    return jumlah


def teks_ke_kotak(teks):
    try:
        x, y, w, h = (int(v) for v in teks.split(","))
        return x, y, w, h
    except (ValueError, AttributeError):
        return None


def nama_crop_baru(kelas, tanggal, cahaya, stem):
    """Cari nomor urut yang belum dipakai supaya file lama tidak tertimpa."""
    n = 1
    while True:
        nama = f"{kelas}_{tanggal}_{cahaya}_{stem}_{n:03d}.png"
        if not os.path.exists(os.path.join(KELUAR, kelas, nama)):
            return nama
        n += 1


# ---------- persiapan ----------
mode_semua = "--semua" in sys.argv
argumen = [a for a in sys.argv[1:] if not a.startswith("--")]

if argumen:
    folder_sumber = argumen[0]
else:
    folder_sumber = input("Tempel path folder foto asli: ")
folder_sumber = folder_sumber.strip().strip('"')

if not os.path.isdir(folder_sumber):
    print("Folder tidak ditemukan:", folder_sumber)
    sys.exit(1)

cahaya_baru = input("Kondisi cahaya foto di folder ini (mis. lab_terang): ").strip()
cahaya_baru = cahaya_baru.replace(" ", "_") or "tidak_dicatat"

for k in KELAS.values():
    os.makedirs(os.path.join(KELUAR, k), exist_ok=True)

rows = []
if os.path.exists(CSV_PATH):
    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
for r in rows:
    r.setdefault("kotak", "")
    if r["kotak"] is None:
        r["kotak"] = ""

sudah = {r["foto_sumber"] for r in rows}
cahaya_foto = {r["foto_sumber"]: r["kondisi_cahaya"] for r in rows}

semua = sorted(
    n for n in os.listdir(folder_sumber)
    if os.path.splitext(n)[1].lower() in EKSTENSI
)
if mode_semua:
    antrean = semua
    print(f"MODE --semua: membuka ulang semua foto ({len(semua)}).")
else:
    antrean = [n for n in semua if n not in sudah]
    print(f"Foto di folder: {len(semua)} | sudah diproses: {len(semua) - len(antrean)} "
          f"| tersisa: {len(antrean)}")

print("\nKUNCI:  b = tandai BOTOL | n = tandai BUKAN BOTOL | u = batalkan crop terakhir (foto ini)")
print("        s = foto berikutnya | q = keluar")
print("Saat menggambar kotak: tarik dengan mouse, tekan ENTER untuk simpan, C untuk batal.")
print("Pesan 'Select a ROI...' dari OpenCV itu normal.\n")

gagal = []

# ---------- loop utama ----------
berhenti = False
for nama in antrean:
    if berhenti:
        break
    img = baca(os.path.join(folder_sumber, nama))
    if img is None:
        print("Gagal baca:", nama)
        gagal.append(nama)
        continue

    tanggal = tanggal_dari_nama(nama)
    stem = os.path.splitext(nama)[0]
    cahaya = cahaya_foto.get(nama, cahaya_baru)  # foto lama tetap pakai label aslinya
    dibuat = []  # (jalur_file, baris_csv, kotak, kelas)

    while True:
        dasar = img.copy()
        # kotak lama (hanya ada kalau sudah tersimpan di metadata)
        for r in rows:
            if r["foto_sumber"] == nama:
                kotak = teks_ke_kotak(r.get("kotak", ""))
                if kotak and r["kelas"] in WARNA:
                    x, y, w, h = kotak
                    cv2.rectangle(dasar, (x, y), (x + w, y + h), WARNA[r["kelas"]], 1)
        # kotak baru di sesi ini
        for (_, _, (x, y, w, h), kelas) in dibuat:
            cv2.rectangle(dasar, (x, y), (x + w, y + h), WARNA[kelas], 2)

        tampil = dasar.copy()
        j = hitung(rows)
        teks = f"botol:{j['botol']}  bukan_botol:{j['bukan_botol']} (target {TARGET})  | {nama}"
        cv2.putText(tampil, teks, (8, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.45,
                    (0, 255, 255), 1, cv2.LINE_AA)
        cv2.putText(tampil, "b=botol  n=bukan  u=undo  s=lanjut  q=keluar",
                    (8, 470), cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                    (0, 255, 255), 1, cv2.LINE_AA)
        cv2.imshow("foto", tampil)
        k = cv2.waitKey(0) & 0xFF

        if k == ord("q"):
            berhenti = True
            break
        if k == ord("s"):
            break
        if k == ord("u"):
            if dibuat:
                jalur, baris, _, _ = dibuat.pop()
                if os.path.exists(jalur):
                    os.remove(jalur)
                rows.remove(baris)
                tulis_csv(rows)
            continue
        if chr(k) in KELAS:
            kelas = KELAS[chr(k)]
            x, y, w, h = cv2.selectROI("foto", dasar, showCrosshair=False)
            if w < UKURAN_MIN or h < UKURAN_MIN:
                print("Kotak terlalu kecil atau dibatalkan, tidak disimpan.")
                continue
            potongan = img[y:y + h, x:x + w]
            nama_crop = nama_crop_baru(kelas, tanggal, cahaya, stem)
            jalur = os.path.join(KELUAR, kelas, nama_crop)
            simpan_png(jalur, potongan)
            baris = {
                "nama_file": nama_crop,
                "kelas": kelas,
                "tanggal": tanggal,
                "kondisi_cahaya": cahaya,
                "foto_sumber": nama,
                "kotak": f"{x},{y},{w},{h}",
            }
            rows.append(baris)
            dibuat.append((jalur, baris, (x, y, w, h), kelas))
            tulis_csv(rows)

cv2.destroyAllWindows()
j = hitung(rows)
print("\nSelesai sesi ini.")
for kelas in KELAS.values():
    status = "OK" if j[kelas] >= TARGET else f"kurang {TARGET - j[kelas]}"
    print(f"Total {kelas:<12}: {j[kelas]}  ({status})")
print("Metadata          :", CSV_PATH)
if gagal:
    print(f"\n{len(gagal)} foto gagal dibaca (dilewati):")
    for n in gagal[:20]:
        print("  -", n)
    if len(gagal) > 20:
        print(f"  ... dan {len(gagal) - 20} lainnya")