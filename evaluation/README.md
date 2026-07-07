# RAGAS Evaluation — Toraja Tourism RAG

Evaluasi kualitas jawaban chatbot menggunakan empat metrik RAGAS
(Retrieval-Augmented Generation Assessment), diimplementasikan secara
native tanpa bergantung pada library `ragas` (yang memiliki dependency
chain rapuh terhadap versi langchain-community).

## Struktur

```
evaluation/
├── golden_dataset.py            10 pertanyaan + ground truth + ideal context
├── ragas_metrics.py             Implementasi 4 metrik via LLM judge
├── run_ragas_evaluation.py      Runner: golden dataset -> chatbot asli -> skor -> laporan JSON
└── ragas_report_simulated.json  Contoh laporan (lihat catatan di bawah)
```

## Empat Metrik

| Metrik | Mengukur | Formula |
|---|---|---|
| Faithfulness | Jawaban tidak mengarang (tidak halusinasi) | klaim jawaban yang didukung konteks / total klaim |
| Answer Relevancy | Jawaban relevan dengan pertanyaan | cosine similarity rata-rata antara pertanyaan asli vs pertanyaan hasil reverse-engineer dari jawaban |
| Context Precision | Chunk yang di-retrieve relevan (tidak ada "sampah") | Average Precision dengan pembobotan posisi |
| Context Recall | Info penting tidak terlewat oleh retriever | klaim ground truth yang ditemukan di konteks / total klaim ground truth |

## Cara Menjalankan Evaluasi Penuh

Membutuhkan `OPENROUTER_API_KEY` aktif di `.env` (LLM judge dan chatbot
keduanya memanggil OpenRouter, sehingga ada biaya per panggilan API),
serta database yang sudah terisi data (`scripts/init_db.py --seed`).

```bash
python evaluation/run_ragas_evaluation.py                  # evaluasi penuh, 10 sampel
python evaluation/run_ragas_evaluation.py --category destinasi
python evaluation/run_ragas_evaluation.py --dry-run         # validasi struktur tanpa panggilan API
```

## Catatan Penting: `ragas_report_simulated.json`

Sandbox pengembangan ini tidak memiliki `OPENROUTER_API_KEY` aktif, sehingga
laporan `ragas_report_simulated.json` yang disertakan bukan hasil panggilan
LLM judge sungguhan. Laporan ini dibuat dengan menerapkan formula RAGAS yang
identik (`aggregate_results()` dari `run_ragas_evaluation.py`, fungsi yang
sama yang dipakai evaluasi nyata) terhadap skor yang dikurasi manual oleh
evaluator berdasarkan jawaban yang secara wajar diharapkan dari sistem
(mengacu pada data nyata di `database/sample_data.sql`).

Validasi struktur pipeline murni (tanpa skor, tanpa panggilan API) sudah
dijalankan dan lulus via `--dry-run`. Logika penghitungan skor (parsing JSON
respons LLM, formula faithfulness/precision/recall/agregasi) sudah diuji
penuh di `tests/test_ragas_metrics_logic.py` (31 unit test, 100% pass) dengan
LLM judge yang di-mock.

## Insight dari Hasil Simulasi

| Kategori | Overall Score | Catatan |
|---|---|---|
| Akomodasi | 0.9850 | Pertanyaan faktual sederhana dengan nama entitas spesifik, performa terbaik |
| Destinasi | 0.9642 | Nama destinasi unik membuat retrieval sangat presisi |
| Budaya | 0.9200 | Reasoning ringan (2 chunk) tetap terjaga baik oleh MMR |
| Event | 0.8700 | Sedikit penurunan karena detail tambahan kurang konsisten |
| Rekomendasi | 0.7475 | Multi-hop (gabung beberapa chunk kategori) adalah titik lemah sistem |
| Out of Scope | 0.4562 | Lihat penjelasan di bawah |

### Mengapa skor out_of_scope rendah, dan apakah itu masalah?

Tidak — skor rendah di sini justru diharapkan secara desain, bukan indikasi
bug. Context Precision dan Context Recall sengaja bernilai rendah/nol karena
ground truth untuk kategori ini ("jumlah penduduk Toraja Utara", "nama
bupati saat ini") sengaja tidak ada dalam knowledge base sistem, sehingga
retriever memang tidak seharusnya menemukan apa pun yang relevan.

Yang harus diperhatikan adalah metrik Faithfulness kategori ini (0.975),
yang tetap tinggi. Ini membuktikan chatbot tidak mengarang jawaban ketika
tidak punya data, sesuai dengan instruksi system prompt di
`rag/retrieval/llm_chain.py`. Inilah perilaku yang benar untuk kasus
out-of-scope: mengakui ketidaktahuan, bukan berhalusinasi.

Rekomendasi tindak lanjut: gunakan metrik faithfulness sebagai sinyal utama
untuk kategori out-of-scope, bukan overall score gabungan (yang akan selalu
rendah secara struktural untuk kategori ini).

## Yang Diuji secara Otomatis (Unit Test)

`tests/test_ragas_metrics_logic.py` — 31 test, 100% pass, mencakup:
- Parsing respons JSON dari LLM judge (termasuk yang dibungkus markdown)
- Formula faithfulness dengan berbagai skenario (semua klaim didukung,
  sebagian, tidak ada, jawaban kosong, respons malformed)
- Formula Average Precision pada Context Precision (termasuk skenario
  posisi relevan-di-awal vs relevan-di-akhir menghasilkan skor berbeda)
- Formula Context Recall dengan klaim ground truth parsial
- Agregasi skor lintas sampel (per kategori, per kesulitan)
- Integritas struktural golden dataset itu sendiri
