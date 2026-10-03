import csv
import math
import os
import random
import shutil
import sys

SINI = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(SINI, "dataset_raw")
CSV_PATH = os.path.join(RAW, "metadata.csv")
OUT = os.path.join(SINI, "dataset")
SPLIT_CSV = os.path.join(SINI, "split_info.csv")

RASIO_VAL = 0.20
SEED = 42
MIN_VAL_PER_KELAS = 10

if not os.path.exists(CSV_PATH):
    print("metadata.csv tidak ditemukan:", CSV_PATH)
    sys.exit(1)

with open(CSV_PATH, newline="", encoding="utf-8") as f:
    rows = list(csv.DictReader(f))

# buang baris yang file crop-nya sudah tidak ada
valid = []
for r in rows:
    jalur = os.path.join(RAW, r["kelas"], r["nama_file"])
    if os.path.exists(jalur):
        valid.append(r)
    else:
        print("[lewati] file tidak ada:", r["nama_file"])
rows = valid

kelas_list = sorted({r["kelas"] for r in rows})
total = {k: sum(1 for r in rows if r["kelas"] == k) for k in kelas_list}
print("Total crop per kelas:", total)

if len(kelas_list) < 2:
    print("Butuh minimal 2 kelas.")
    sys.exit(1)

# kelompokkan crop per foto sumber
per_foto = {}
for r in rows:
    per_foto.setdefault(r["foto_sumber"], []).append(r)

foto = sorted(per_foto)
random.Random(SEED).shuffle(foto)

target_val = {k: math.ceil(RASIO_VAL * total[k]) for k in kelas_list}
val_count = {k: 0 for k in kelas_list}
foto_val = set()

for fs in foto:
    if all(val_count[k] >= target_val[k] for k in kelas_list):
        break
    foto_val.add(fs)
    for r in per_foto[fs]:
        val_count[r["kelas"]] += 1

# jangan sampai semua foto masuk val
if len(foto_val) >= len(foto):
    print("Foto terlalu sedikit untuk dibagi. Tambah foto baru.")
    sys.exit(1)

# buat ulang folder dataset dari nol
if os.path.exists(OUT):
    shutil.rmtree(OUT)

hitung = {"train": {k: 0 for k in kelas_list}, "val": {k: 0 for k in kelas_list}}
info = []
for r in rows:
    bagian = "val" if r["foto_sumber"] in foto_val else "train"
    tujuan = os.path.join(OUT, bagian, r["kelas"])
    os.makedirs(tujuan, exist_ok=True)
    shutil.copy2(os.path.join(RAW, r["kelas"], r["nama_file"]), tujuan)
    hitung[bagian][r["kelas"]] += 1
    info.append({
        "nama_file": r["nama_file"],
        "kelas": r["kelas"],
        "split": bagian,
        "foto_sumber": r["foto_sumber"],
        "kondisi_cahaya": r["kondisi_cahaya"],
    })

with open(SPLIT_CSV, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(info[0].keys()))
    w.writeheader()
    w.writerows(info)

# cek kebocoran: tidak boleh ada foto sumber di train dan val sekaligus
foto_train = {r["foto_sumber"] for r in rows if r["foto_sumber"] not in foto_val}
bocor = foto_train & foto_val

print("\n" + "=" * 50)
print(f"Foto sumber : {len(foto)} (train {len(foto_train)}, val {len(foto_val)})")
for bagian in ("train", "val"):
    print(f"{bagian:<6}: {hitung[bagian]}")
print("Cek kebocoran:", "AMAN (tidak ada foto di dua bagian)" if not bocor else f"BOCOR: {bocor}")
print("Info lengkap  :", SPLIT_CSV)

for k in kelas_list:
    if hitung["val"][k] < MIN_VAL_PER_KELAS:
        print(f"PERHATIAN: val kelas '{k}' hanya {hitung['val'][k]} crop (disarankan >= {MIN_VAL_PER_KELAS}).")
    if hitung["train"][k] < 30:
        print(f"PERHATIAN: train kelas '{k}' hanya {hitung['train'][k]} crop.")