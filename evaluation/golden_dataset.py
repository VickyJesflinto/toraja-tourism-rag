"""
evaluation/golden_dataset.py

Golden dataset untuk evaluasi RAGAS sistem RAG Toraja Tourism.

Setiap entri terdiri dari:
- question        : pertanyaan yang akan diajukan ke chatbot
- ground_truth     : jawaban referensi yang benar (dikurasi manual dari data nyata)
- ideal_context    : potongan teks yang seharusnya ditemukan oleh retriever
                      agar bisa menjawab pertanyaan dengan benar (dipakai untuk
                      Context Recall -- mengukur apakah retriever menemukan info
                      yang seharusnya ditemukan)
- category         : kategori pertanyaan, untuk analisis per-kategori
- difficulty       : level kesulitan (factual / reasoning / multi-hop / out-of-scope)

Dataset ini dibuat berdasarkan data yang sama dengan database/sample_data.sql
(destinasi, akomodasi, event budaya Toraja yang sudah diverifikasi dari sumber
nyata: Liputan6, IDN Times, detikcom, toraja.info).

Kategori "out-of-scope" sengaja disertakan untuk menguji apakah chatbot jujur
mengakui tidak tahu, bukan mengarang jawaban (uji ketahanan terhadap halusinasi).
"""
from dataclasses import dataclass
from typing import List


@dataclass
class GoldenSample:
    question: str
    ground_truth: str
    ideal_context: List[str]
    category: str
    difficulty: str   # factual | reasoning | multi_hop | out_of_scope


GOLDEN_DATASET: List[GoldenSample] = [

    # FACTUAL -- jawaban langsung dari satu fakta di database
    GoldenSample(
        question="Apa itu Ke'te Kesu'?",
        ground_truth=(
            "Ke'te Kesu' adalah desa wisata budaya bersejarah di Toraja dengan "
            "rumah adat Tongkonan dan situs pemakaman kuno yang masih terawat. "
            "Kawasan ini telah dinominasikan sebagai Situs Warisan Dunia UNESCO."
        ),
        ideal_context=[
            "Ke'te Kesu' adalah desa wisata bersejarah dengan rumah adat Tongkonan "
            "dan situs pemakaman kuno yang masih terawat. Kawasan ini telah "
            "dinominasikan sebagai Situs Warisan Dunia UNESCO."
        ],
        category="destinasi",
        difficulty="factual",
    ),
    GoldenSample(
        question="Berapa harga tiket masuk ke Londa?",
        ground_truth="Harga tiket masuk Londa adalah Rp 20.000.",
        ideal_context=[
            "Londa, Sanggalangi', entry_fee 20000.00",
        ],
        category="destinasi",
        difficulty="factual",
    ),
    GoldenSample(
        question="Di mana lokasi Patung Yesus Memberkati?",
        ground_truth=(
            "Patung Yesus Memberkati (Buntu Burake) berlokasi di Burake, "
            "Kecamatan Makale, hanya 15 menit dari Kota Makale."
        ),
        ideal_context=[
            "Monumen Patung Yesus Memberkati setinggi 40 meter yang berdiri di "
            "dataran tinggi Kecamatan Burake, hanya 15 menit dari Kota Makale."
        ],
        category="destinasi",
        difficulty="factual",
    ),
    GoldenSample(
        question="Kapan Toraja Highland Festival 2025 diadakan?",
        ground_truth="Toraja Highland Festival 2025 diadakan pada 11-13 Desember 2025.",
        ideal_context=[
            "Toraja Highland Festival 2025 ... 2025-12-11 sampai 2025-12-13, "
            "di Gedung Art Center Rantepao."
        ],
        category="event",
        difficulty="factual",
    ),
    GoldenSample(
        question="Berapa kisaran harga kamar di Toraja Heritage Hotel?",
        ground_truth="Toraja Heritage Hotel memiliki kisaran harga Rp 850.000 - Rp 2.500.000 per malam.",
        ideal_context=[
            "Toraja Heritage Hotel, hotel, price_min 850000, price_max 2500000"
        ],
        category="akomodasi",
        difficulty="factual",
    ),

    # REASONING -- perlu menggabungkan/menyimpulkan dari konteks
    GoldenSample(
        question="Destinasi apa yang cocok untuk melihat matahari terbit di atas awan?",
        ground_truth=(
            "Lolai (Negeri di Atas Awan) adalah destinasi yang menawarkan pemandangan "
            "lautan awan dari ketinggian 1.300 mdpl, sangat cocok untuk melihat matahari "
            "terbit di atas awan."
        ),
        ideal_context=[
            "Lolai - To' Tombi (Negeri di Atas Awan): destinasi yang menawarkan "
            "pemandangan lautan awan yang memesona dari ketinggian 1.300 mdpl."
        ],
        category="rekomendasi",
        difficulty="reasoning",
    ),
    GoldenSample(
        question="Apa perbedaan antara Rambu Solo' dan Rambu Tuka'?",
        ground_truth=(
            "Rambu Solo' adalah upacara pemakaman adat Toraja yang bersifat sakral "
            "dan duka, melibatkan penyembelihan kerbau. Sedangkan Rambu Tuka' adalah "
            "upacara syukuran yang bersifat gembira, terkait peresmian Tongkonan baru "
            "atau pernikahan adat."
        ),
        ideal_context=[
            "Rambu Solo' -- Upacara Pemakaman Adat: upacara pemakaman adat Toraja yang "
            "sakral dan megah, melibatkan ma'tinggoro tedong (penyembelihan kerbau).",
            "Rambu Tuka' -- Syukuran Tongkonan & Pernikahan Adat: upacara syukuran "
            "bersifat gembira terkait peresmian Tongkonan baru atau pernikahan adat.",
        ],
        category="budaya",
        difficulty="reasoning",
    ),

    # MULTI-HOP -- butuh menggabungkan info dari beberapa dokumen/chunk
    GoldenSample(
        question=(
            "Jika saya ingin mengunjungi situs pemakaman tebing batu yang murah "
            "dan dekat dengan hotel budget, destinasi dan hotel apa yang cocok?"
        ),
        ground_truth=(
            "Untuk situs pemakaman tebing batu, Londa dan Lemo adalah pilihan dengan "
            "tiket masuk Rp 20.000. Untuk hotel budget terdekat, Toraja Sanggalangi "
            "Homestay berlokasi dekat Londa & Lemo dengan harga sekitar Rp 140.000 - "
            "Rp 320.000 per malam."
        ),
        ideal_context=[
            "Londa, Sanggalangi', entry_fee 20000.00 -- situs pemakaman tebing batu",
            "Lemo, Makale Utara, entry_fee 20000.00 -- tebing makam ikonik",
            "Toraja Sanggalangi Homestay, dekat Londa & Lemo, price_min 140000, price_max 320000",
        ],
        category="rekomendasi",
        difficulty="multi_hop",
    ),

    # OUT OF SCOPE -- sengaja menanyakan hal yang TIDAK ada di database
    GoldenSample(
        question="Berapa total penduduk Kabupaten Toraja Utara tahun 2026?",
        ground_truth=(
            "Informasi mengenai jumlah penduduk Toraja Utara tidak tersedia dalam "
            "database sistem ini. Sistem hanya jujur menyatakan tidak memiliki data "
            "tersebut, tidak boleh mengarang angka."
        ),
        ideal_context=[],
        category="out_of_scope",
        difficulty="out_of_scope",
    ),
    GoldenSample(
        question="Siapa nama bupati Toraja Utara saat ini?",
        ground_truth=(
            "Informasi mengenai nama bupati saat ini tidak tersedia secara pasti dalam "
            "database sistem (kecuali disebutkan tersirat dalam konteks event tertentu). "
            "Sistem seharusnya tidak mengarang nama pejabat yang tidak terverifikasi."
        ),
        ideal_context=[],
        category="out_of_scope",
        difficulty="out_of_scope",
    ),
]


def get_dataset_by_category(category: str) -> List[GoldenSample]:
    return [s for s in GOLDEN_DATASET if s.category == category]


def get_dataset_by_difficulty(difficulty: str) -> List[GoldenSample]:
    return [s for s in GOLDEN_DATASET if s.difficulty == difficulty]


def summary() -> dict:
    from collections import Counter
    cat_counts = Counter(s.category for s in GOLDEN_DATASET)
    diff_counts = Counter(s.difficulty for s in GOLDEN_DATASET)
    return {
        "total_samples": len(GOLDEN_DATASET),
        "by_category": dict(cat_counts),
        "by_difficulty": dict(diff_counts),
    }


if __name__ == "__main__":
    import json
    print(json.dumps(summary(), indent=2, ensure_ascii=False))
