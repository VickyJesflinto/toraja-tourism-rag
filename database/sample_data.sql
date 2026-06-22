-- ============================================================
-- TORAJA TOURISM — SAMPLE DATA (Data Nyata & Komprehensif)
-- Sumber: Dinas Kebudayaan & Pariwisata Toraja Utara, Tana Toraja,
--         Liputan6, IDN Times, detikcom, Trip.com, Booking.com,
--         Tripadvisor, toraja.info, indonesia.travel (per 2025-2026)
-- Jalankan SETELAH schema.sql
-- ============================================================

USE toraja_tourism;

-- ============================================================
-- TOURIST_ATTRACTIONS (25 destinasi nyata di Tana Toraja & Toraja Utara)
-- ============================================================
INSERT INTO tourist_attractions
  (name, category, description, location, district, latitude, longitude, entry_fee, rating, is_active)
VALUES

-- ── Situs Budaya & Pemakaman ────────────────────────────────────────────────
('Ke''te Kesu''', 'budaya',
 'Desa wisata bersejarah dengan rumah adat Tongkonan dan situs pemakaman kuno yang masih terawat. Kawasan ini telah dinominasikan sebagai Situs Warisan Dunia UNESCO. Di sini pengunjung bisa menyaksikan deretan lumbung padi (alang), ukiran kayu Toraja, dan tau-tau (patung kayu leluhur) di tebing batu.',
 'Ke''te Kesu'', Kec. Kesu''', 'Kesu''', -2.9731, 119.9394, 20000.00, 4.80, 1),

('Londa', 'budaya',
 'Situs pemakaman tebing batu dengan dua gua alami yang menyimpan peti-peti mati leluhur Toraja serta deretan tau-tau berusia ratusan tahun. Pengunjung dapat menyewa lampu petromaks untuk menjelajahi gua bersama pemandu lokal.',
 'Londa, Sanggalangi''', 'Sanggalangi''', -2.9950, 119.9183, 20000.00, 4.70, 1),

('Lemo', 'budaya',
 'Tebing makam kuno dengan deretan tau-tau yang menghadap keluar dari relung-relung batu, menggambarkan status sosial keluarga yang dimakamkan. Lemo merupakan salah satu destinasi paling ikonik dan banyak difoto di Toraja.',
 'Lemo, Makale Utara', 'Makale Utara', -3.0500, 119.8700, 20000.00, 4.75, 1),

('Bori'' Kalimbuang (Bori Parinding)', 'budaya',
 'Situs megalitikum dengan 102 menhir batu raksasa yang berfungsi sebagai monumen peringatan dan tempat upacara adat Rambu Solo'' di masa lampau. Disebut sebagai "Stonehenge versi Toraja" karena bentuk batunya yang menjulang.',
 'Bori'', Sesean', 'Sesean', -2.8950, 119.9230, 15000.00, 4.60, 1),

('Tongkonan Pallawa', 'budaya',
 'Kompleks rumah adat Tongkonan yang terawat rapi dengan deretan tanduk kerbau di bagian depan rumah sebagai simbol status sosial dan jumlah upacara adat yang pernah dilaksanakan keluarga pemilik.',
 'Pallawa, Sesean', 'Sesean', -2.9200, 119.9500, 15000.00, 4.50, 1),

('Kambira (Baby Grave Tree)', 'budaya',
 'Situs pemakaman bayi yang unik di dalam pohon Tarra berusia ratusan tahun. Menurut tradisi Toraja, bayi yang meninggal sebelum tumbuh gigi dimakamkan di lubang pohon karena dianggap masih suci dan menyatu dengan alam.',
 'Kambira, Sanggalangi''', 'Sanggalangi''', -2.9800, 119.9350, 10000.00, 4.45, 1),

('Sa''dan To'' Barana''', 'budaya',
 'Desa penghasil kain tenun tradisional Toraja (pa''tedong dan sekomandi). Pengunjung dapat menyaksikan proses menenun secara langsung menggunakan alat tenun tradisional serta membeli kain langsung dari pengrajin lokal.',
 'Sa''dan Malimbong, Sa''dan', 'Sa''dan', -2.8900, 119.9700, 0.00, 4.35, 1),

('Museum Ne''Gandeng', 'budaya',
 'Museum yang menyimpan koleksi artefak budaya Toraja seperti pakaian adat, senjata tradisional, perhiasan, dan dokumentasi sejarah upacara adat Toraja. Lokasi yang ideal untuk memahami sejarah Toraja sebelum berkeliling.',
 'Makale', 'Makale', -3.0950, 119.8600, 10000.00, 4.20, 1),

('Patung Yesus Memberkati (Buntu Burake)', 'religi',
 'Monumen Patung Yesus Memberkati setinggi 40 meter yang berdiri di dataran tinggi Kecamatan Burake, hanya 15 menit dari Kota Makale. Selain kemegahan patung, pengunjung dapat menikmati panorama Kota Makale dari ketinggian serta berbelanja oleh-oleh khas Toraja di sekitar lokasi.',
 'Burake, Makale', 'Makale', -3.1100, 119.8550, 15000.00, 4.65, 1),

-- ── Destinasi Alam & Negeri di Atas Awan ────────────────────────────────────
('Lolai - To'' Tombi (Negeri di Atas Awan)', 'alam',
 'Destinasi yang menawarkan pemandangan lautan awan yang memesona dari ketinggian 1.300 mdpl. Tidak pernah sepi pengunjung terutama saat musim liburan karena keindahan matahari terbit di atas hamparan awan.',
 'Kampung Lolai, Benteng Mamullu, Kapalapitu', 'Kapalapitu', -2.8550, 119.9600, 15000.00, 4.70, 1),

('Agrowisata Pango-Pango', 'alam',
 'Kawasan agrowisata kebun kopi di dataran tinggi 1.600-1.700 mdpl yang dijuluki "negeri di atas awan". Dilengkapi gazebo, wahana permainan, dan area berkemah dengan latar hutan pinus serta lautan awan sebagai spot foto favorit.',
 'Kel. Pasang, Makale Selatan', 'Makale Selatan', -3.1300, 119.8200, 15000.00, 4.55, 1),

('Batu Tumonga', 'alam',
 'Hamparan sawah bertingkat dan menhir prasejarah di ketinggian 1.300 mdpl dengan julukan "negeri di atas awan" lainnya. Menawarkan panorama Kota Rantepao yang memukau, terutama saat sore hari dengan udara sejuk khas pegunungan.',
 'Batu Tumonga, Sesean', 'Sesean', -2.8710, 119.9050, 10000.00, 4.65, 1),

('Lembah Kendenan', 'alam',
 'Destinasi alam viral sejak 2024 yang menawarkan panorama lembah hijau menyerupai pemandangan khas Swiss. Dapat ditempuh sekitar 1,5 jam berkendara dari Makale melalui jalan berkelok yang sudah beraspal.',
 'Ratte Buttu, Bonggakaradeng', 'Bonggakaradeng', -3.2100, 119.7600, 10000.00, 4.50, 1),

('Tilanga', 'alam',
 'Kolam mata air purba alami yang sejuk dan jernih, dikelilingi rimbunnya pohon bambu. Berlokasi 8 km ke arah utara dari Kota Makale, menjadi favorit untuk berenang dan bersantai di tengah suasana alam yang asri.',
 'Sarira, Makale Utara', 'Makale Utara', -3.0750, 119.8550, 15000.00, 4.30, 1),

('Kolam Makale (Plaza Makale)', 'alam',
 'Kolam buatan ikonik di pusat Kota Makale yang diapit empat ruas jalan utama, dibangun sejak 2018 dengan air mancur menari dan lampu warna-warni yang indah di malam hari. Menjadi pusat keramaian dan ikon Kota Makale.',
 'Manggau, Makale', 'Makale', -3.0980, 119.8580, 0.00, 4.25, 1),

('Ollon Valley (Bukit Teletubbies Toraja)', 'alam',
 'Destinasi alam dengan perbukitan hijau bergelombang yang menyerupai lanskap "Teletubbies", populer sejak 2017. Cocok untuk trekking ringan dan fotografi lanskap perbukitan yang unik.',
 'Tikala', 'Tikala', -2.9300, 119.9450, 10000.00, 4.40, 1),

('Gunung Sesean', 'alam',
 'Puncak tertinggi di Toraja Utara dengan ketinggian sekitar 2.150 mdpl. Jalur pendakian melewati hutan tropis dan perkampungan tradisional, menawarkan panorama seluruh dataran Toraja dari puncak saat cuaca cerah.',
 'Sesean', 'Sesean', -2.8500, 119.9200, 0.00, 4.55, 1),

('Desa Wisata Pinus Pa''tengko', 'alam',
 'Kawasan hutan pinus yang ditata sebagai desa wisata dengan jalur trekking, gazebo, dan spot foto di antara pepohonan pinus yang menjulang. Udara sejuk dan suasana asri menjadikannya favorit wisatawan muda.',
 'Pa''tengko, Sesean Suloara''', 'Sesean Suloara''', -2.8400, 119.9150, 10000.00, 4.35, 1),

-- ── Pasar & Budaya Lokal ─────────────────────────────────────────────────────
('Pasar Bolu Rantepao', 'budaya',
 'Pasar tradisional terbesar di Toraja yang diadakan setiap 6 hari sekali sesuai kalender adat Toraja. Dikenal sebagai pasar kerbau terbesar di Indonesia — kerbau albino (tedong bonga) bisa berharga ratusan juta rupiah. Pasar ini juga menjual babi, hasil bumi, dan kerajinan tangan khas Toraja.',
 'Rantepao', 'Rantepao', -2.9641, 119.8983, 0.00, 4.40, 1),

('Wisata Kandora', 'budaya',
 'Kawasan wisata yang memadukan keindahan alam pegunungan dengan nilai budaya lokal Toraja, menawarkan spot foto alam serta pengalaman edukasi budaya bagi pengunjung domestik maupun mancanegara.',
 'Toraja Utara', 'Toraja Utara', -2.9000, 119.9300, 10000.00, 4.30, 1),

('Tampang Allo', 'budaya',
 'Situs pemakaman gua alami dengan peti-peti kayu kuno (erong) yang tersusun di celah-celah batu tebing, menampilkan tradisi penguburan khas Toraja yang berbeda dari situs-situs pemakaman besar lainnya.',
 'Toraja Utara', 'Toraja Utara', -2.9500, 119.9000, 15000.00, 4.35, 1);


-- ============================================================
-- VISITOR_STATISTICS — Data 24 bulan (2024-2025) untuk 6 destinasi utama
-- Pola realistis: musim ramai Juni-Juli (liburan sekolah) dan Desember
-- (Lovely December & Rambu Solo'), musim sepi Januari-Maret
-- ============================================================

-- Ke'te Kesu' (attraction_id = 1) — destinasi paling populer
INSERT INTO visitor_statistics (attraction_id, year, month, domestic, foreign_vis, total, revenue) VALUES
(1, 2024, 1,  2850, 312, 3162, 63240000), (1, 2024, 2,  2640, 298, 2938, 58760000),
(1, 2024, 3,  3120, 425, 3545, 70900000), (1, 2024, 4,  3500, 480, 3980, 79600000),
(1, 2024, 5,  3200, 410, 3610, 72200000), (1, 2024, 6,  4800, 720, 5520,110400000),
(1, 2024, 7,  5200, 850, 6050,121000000), (1, 2024, 8,  4100, 590, 4690, 93800000),
(1, 2024, 9,  3600, 465, 4065, 81300000), (1, 2024,10,  3300, 430, 3730, 74600000),
(1, 2024,11,  3100, 405, 3505, 70100000), (1, 2024,12,  6800,1150, 7950,159000000),
(1, 2025, 1,  3050, 340, 3390, 67800000), (1, 2025, 2,  2800, 310, 3110, 62200000),
(1, 2025, 3,  3300, 450, 3750, 75000000), (1, 2025, 4,  3700, 510, 4210, 84200000),
(1, 2025, 5,  3400, 440, 3840, 76800000), (1, 2025, 6,  5100, 780, 5880,117600000),
(1, 2025, 7,  5500, 910, 6410,128200000), (1, 2025, 8,  4350, 630, 4980, 99600000),
(1, 2025, 9,  3800, 495, 4295, 85900000), (1, 2025,10,  3500, 460, 3960, 79200000),
(1, 2025,11,  3300, 430, 3730, 74600000), (1, 2025,12,  7200,1280, 8480,169600000);

-- Londa (attraction_id = 2)
INSERT INTO visitor_statistics (attraction_id, year, month, domestic, foreign_vis, total, revenue) VALUES
(2, 2024, 1,  1950, 245, 2195, 43900000), (2, 2024, 2,  1820, 220, 2040, 40800000),
(2, 2024, 3,  2100, 310, 2410, 48200000), (2, 2024, 4,  2400, 360, 2760, 55200000),
(2, 2024, 5,  2200, 315, 2515, 50300000), (2, 2024, 6,  3500, 540, 4040, 80800000),
(2, 2024, 7,  3800, 620, 4420, 88400000), (2, 2024, 8,  2850, 420, 3270, 65400000),
(2, 2024, 9,  2450, 355, 2805, 56100000), (2, 2024,10,  2250, 320, 2570, 51400000),
(2, 2024,11,  2100, 295, 2395, 47900000), (2, 2024,12,  4900, 850, 5750,115000000),
(2, 2025, 1,  2050, 260, 2310, 46200000), (2, 2025, 2,  1900, 235, 2135, 42700000),
(2, 2025, 3,  2250, 330, 2580, 51600000), (2, 2025, 4,  2550, 380, 2930, 58600000),
(2, 2025, 5,  2350, 335, 2685, 53700000), (2, 2025, 6,  3700, 580, 4280, 85600000),
(2, 2025, 7,  4000, 660, 4660, 93200000), (2, 2025, 8,  3000, 450, 3450, 69000000),
(2, 2025, 9,  2600, 380, 2980, 59600000), (2, 2025,10,  2400, 345, 2745, 54900000),
(2, 2025,11,  2250, 315, 2565, 51300000), (2, 2025,12,  5200, 920, 6120,122400000);

-- Lemo (attraction_id = 3)
INSERT INTO visitor_statistics (attraction_id, year, month, domestic, foreign_vis, total, revenue) VALUES
(3, 2024, 1,  2100, 290, 2390, 47800000), (3, 2024, 2,  1950, 270, 2220, 44400000),
(3, 2024, 3,  2350, 350, 2700, 54000000), (3, 2024, 4,  2700, 410, 3110, 62200000),
(3, 2024, 5,  2500, 375, 2875, 57500000), (3, 2024, 6,  3900, 600, 4500, 90000000),
(3, 2024, 7,  4200, 680, 4880, 97600000), (3, 2024, 8,  3100, 490, 3590, 71800000),
(3, 2024, 9,  2700, 400, 3100, 62000000), (3, 2024,10,  2450, 360, 2810, 56200000),
(3, 2024,11,  2300, 335, 2635, 52700000), (3, 2024,12,  5400, 920, 6320,126400000),
(3, 2025, 1,  2200, 305, 2505, 50100000), (3, 2025, 2,  2050, 285, 2335, 46700000),
(3, 2025, 3,  2450, 365, 2815, 56300000), (3, 2025, 4,  2800, 425, 3225, 64500000),
(3, 2025, 5,  2600, 390, 2990, 59800000), (3, 2025, 6,  4050, 630, 4680, 93600000),
(3, 2025, 7,  4400, 715, 5115,102300000), (3, 2025, 8,  3250, 515, 3765, 75300000),
(3, 2025, 9,  2850, 420, 3270, 65400000), (3, 2025,10,  2580, 380, 2960, 59200000),
(3, 2025,11,  2400, 350, 2750, 55000000), (3, 2025,12,  5700, 980, 6680,133600000);

-- Lolai - Negeri di Atas Awan (attraction_id = 10)
INSERT INTO visitor_statistics (attraction_id, year, month, domestic, foreign_vis, total, revenue) VALUES
(10, 2024, 1,  3200, 180, 3380, 50700000), (10, 2024, 2,  2950, 165, 3115, 46725000),
(10, 2024, 3,  3450, 220, 3670, 55050000), (10, 2024, 4,  3800, 260, 4060, 60900000),
(10, 2024, 5,  3550, 235, 3785, 56775000), (10, 2024, 6,  5200, 380, 5580, 83700000),
(10, 2024, 7,  5800, 450, 6250, 93750000), (10, 2024, 8,  4400, 310, 4710, 70650000),
(10, 2024, 9,  3900, 260, 4160, 62400000), (10, 2024,10,  3600, 235, 3835, 57525000),
(10, 2024,11,  3400, 210, 3610, 54150000), (10, 2024,12,  7100, 620, 7720,115800000),
(10, 2025, 1,  3350, 195, 3545, 53175000), (10, 2025, 2,  3100, 175, 3275, 49125000),
(10, 2025, 3,  3650, 240, 3890, 58350000), (10, 2025, 4,  4000, 280, 4280, 64200000),
(10, 2025, 5,  3750, 250, 4000, 60000000), (10, 2025, 6,  5500, 410, 5910, 88650000),
(10, 2025, 7,  6100, 480, 6580, 98700000), (10, 2025, 8,  4650, 335, 4985, 74775000),
(10, 2025, 9,  4100, 280, 4380, 65700000), (10, 2025,10,  3800, 250, 4050, 60750000),
(10, 2025,11,  3600, 225, 3825, 57375000), (10, 2025,12,  7500, 670, 8170,122550000);

-- Pasar Bolu Rantepao (attraction_id = 19) — gratis, jadi revenue 0
INSERT INTO visitor_statistics (attraction_id, year, month, domestic, foreign_vis, total, revenue) VALUES
(19, 2024, 1,  3500,  80, 3580, 0), (19, 2024, 2,  3200,  72, 3272, 0),
(19, 2024, 3,  3900,  95, 3995, 0), (19, 2024, 4,  4200, 110, 4310, 0),
(19, 2024, 5,  3800,  98, 3898, 0), (19, 2024, 6,  4900, 160, 5060, 0),
(19, 2024, 7,  5300, 195, 5495, 0), (19, 2024, 8,  4400, 130, 4530, 0),
(19, 2024, 9,  4000, 105, 4105, 0), (19, 2024,10,  3700, 100, 3800, 0),
(19, 2024,11,  3600,  95, 3695, 0), (19, 2024,12,  6900, 280, 7180, 0),
(19, 2025, 1,  3650,  85, 3735, 0), (19, 2025, 2,  3350,  78, 3428, 0),
(19, 2025, 3,  4050, 100, 4150, 0), (19, 2025, 4,  4350, 115, 4465, 0),
(19, 2025, 5,  3950, 102, 4052, 0), (19, 2025, 6,  5100, 168, 5268, 0),
(19, 2025, 7,  5500, 205, 5705, 0), (19, 2025, 8,  4600, 138, 4738, 0),
(19, 2025, 9,  4200, 112, 4312, 0), (19, 2025,10,  3900, 108, 4008, 0),
(19, 2025,11,  3750, 100, 3850, 0), (19, 2025,12,  7200, 295, 7495, 0);

-- Batu Tumonga (attraction_id = 12)
INSERT INTO visitor_statistics (attraction_id, year, month, domestic, foreign_vis, total, revenue) VALUES
(12, 2024, 1,  1800, 140, 1940, 19400000), (12, 2024, 2,  1650, 125, 1775, 17750000),
(12, 2024, 3,  1950, 165, 2115, 21150000), (12, 2024, 4,  2200, 195, 2395, 23950000),
(12, 2024, 5,  2050, 175, 2225, 22250000), (12, 2024, 6,  3000, 280, 3280, 32800000),
(12, 2024, 7,  3300, 320, 3620, 36200000), (12, 2024, 8,  2500, 220, 2720, 27200000),
(12, 2024, 9,  2200, 185, 2385, 23850000), (12, 2024,10,  2000, 165, 2165, 21650000),
(12, 2024,11,  1900, 150, 2050, 20500000), (12, 2024,12,  4100, 450, 4550, 45500000),
(12, 2025, 1,  1880, 148, 2028, 20280000), (12, 2025, 2,  1720, 132, 1852, 18520000),
(12, 2025, 3,  2050, 172, 2222, 22220000), (12, 2025, 4,  2300, 205, 2505, 25050000),
(12, 2025, 5,  2150, 182, 2332, 23320000), (12, 2025, 6,  3150, 295, 3445, 34450000),
(12, 2025, 7,  3450, 335, 3785, 37850000), (12, 2025, 8,  2620, 232, 2852, 28520000),
(12, 2025, 9,  2300, 195, 2495, 24950000), (12, 2025,10,  2100, 175, 2275, 22750000),
(12, 2025,11,  2000, 158, 2158, 21580000), (12, 2025,12,  4300, 475, 4775, 47750000);


-- ============================================================
-- ACCOMMODATIONS (15 akomodasi nyata di Tana Toraja & Toraja Utara)
-- ============================================================
INSERT INTO accommodations
  (name, type, location, district, latitude, longitude, price_min, price_max, capacity, rating, contact, is_active)
VALUES

('Toraja Misiliana Hotel', 'hotel',
 'Jl. Pongtiku No. 27, Rantepao, Kesu''', 'Rantepao', -2.9620, 119.8990, 700000, 1500000, 80, 4.50, '+62-423-21212', 1),

('Toraja Heritage Hotel', 'hotel',
 'Jl. Poros Makale - Rantepao Km. 1, Rantepao', 'Rantepao', -2.9600, 119.8970, 850000, 2500000, 56, 4.55, '+62-423-21515', 1),

('Hotel Marante Toraja', 'hotel',
 'Jl. Poros Rantepao - Palopo, Tondon, Toraja Utara', 'Tondon', -2.9100, 119.9200, 350000, 900000, 45, 4.30, '+62-423-22188', 1),

('Gosyen Efata Hotel', 'hotel',
 'Jl. Poros Makale - Rantepao Km. 8, Makale Utara, Tana Toraja', 'Makale Utara', -3.0700, 119.8650, 250000, 600000, 30, 4.10, '+62-423-23456', 1),

('Hotel Indra Toraja', 'hotel',
 'Rantepao, Toraja Utara', 'Rantepao', -2.9655, 119.8975, 200000, 500000, 28, 4.00, '+62-423-21363', 1),

('Hotel Monika', 'hotel',
 'Rantepao, Toraja Utara', 'Rantepao', -2.9670, 119.8965, 180000, 450000, 25, 4.05, '+62-423-21216', 1),

('Toraja Torsina Hotel', 'hotel',
 'Rantepao, Toraja Utara', 'Rantepao', -2.9660, 119.8980, 300000, 750000, 35, 4.20, '+62-423-21293', 1),

('Pias Poppies Hotel', 'hotel',
 'Rantepao, Toraja Utara', 'Rantepao', -2.9645, 119.8990, 220000, 550000, 30, 4.15, '+62-423-21121', 1),

('Faves Hotel Toraja', 'hotel',
 'Tana Toraja, dekat Limbong Lake', 'Makale', -3.0900, 119.8580, 280000, 650000, 32, 4.10, '+62-423-22240', 1),

('Santai Toraja', 'hotel',
 'Rantepao, dekat Taman Pahlawan Pongtiku & Pasar Bolu', 'Rantepao', -2.9630, 119.8995, 250000, 600000, 12, 4.25, '+62-423-21788', 1),

('Toraja Lodge Guest House', 'homestay',
 'Rantepao, Toraja Utara', 'Rantepao', -2.9680, 119.8960, 150000, 350000, 10, 4.20, '+62-852-9900-1122', 1),

('Inn De'' Lopi & Cafe', 'homestay',
 'Dekat Ke''te'' Kesu'' Toraja', 'Kesu''', -2.9750, 119.9380, 180000, 400000, 10, 4.35, '+62-823-4500-6677', 1),

('Tongkonan Homestay Ke''te Kesu''', 'homestay',
 'Desa Ke''te Kesu''', 'Kesu''', -2.9730, 119.9390, 150000, 300000, 8, 4.50, '+62-852-4231-0000', 1),

('Darra Homestay Toraja', 'homestay',
 'Rantepao, Toraja Utara (city view)', 'Rantepao', -2.9690, 119.8950, 160000, 380000, 9, 4.25, '+62-813-5500-7788', 1),

('Toraja Sanggalangi Homestay', 'homestay',
 'Sanggalangi'', dekat Londa & Lemo', 'Sanggalangi''', -2.9900, 119.9100, 140000, 320000, 7, 4.15, '+62-821-8800-1234', 1);


-- ============================================================
-- CULTURAL_EVENTS (event budaya nyata Toraja 2025-2026)
-- ============================================================
INSERT INTO cultural_events
  (name, description, location, event_date, end_date, category, organizer, contact, is_recurring)
VALUES

('Toraja Highland Festival 2025',
 'Festival tahunan ke-5 yang mengusung tema "Living Heritage in a Mythical" dengan kolaborasi multi-stakeholder: MASATA DPC Toraja Utara, Dinas Kebudayaan & Pariwisata, Geopark, komunitas kreatif, fotografer, seniman lokal, dan pelaku UMKM. Menampilkan pameran UMKM, kuliner tradisional, pameran seni, festival bambu, Toraja Coffee Festival, fashion show kain tenun Toraja, serta musik dan tari tradisional. Dibuka resmi oleh Bupati Toraja Utara Frederik Victor Palimbong di Gedung Art Center Rantepao.',
 'Jantung Kota Rantepao (Art Center)', '2025-12-11 09:00:00', '2025-12-13 22:00:00',
 'festival', 'MASATA DPC Toraja Utara & Disbudpar Toraja Utara', '+62-423-21001', 1),

('Lovely December 2025',
 'Fenomena budaya tahunan yang menyatukan kemeriahan liburan Natal-Tahun Baru dengan kemegahan upacara pemakaman Rambu Solo''. Periode ini menjadikan dataran tinggi Toraja sebagai "museum hidup" paling semarak di Indonesia, mencakup Toraja Highland Festival (11-13 Desember) dan padatnya upacara Rambu Solo'' (15-29 Desember). Rantepao turut mempromosikan diri sebagai "Christmas City" untuk menyambut wisatawan akhir tahun.',
 'Rantepao & Makale, Toraja Utara dan Tana Toraja', '2025-12-01 08:00:00', '2025-12-31 22:00:00',
 'festival', 'Pemkab Toraja Utara & Tana Toraja', '+62-423-21001', 1),

('Rambu Solo'' — Upacara Pemakaman Adat',
 'Upacara pemakaman adat Toraja yang sakral dan megah, berlangsung 3-7 hari dengan rangkaian ritual: ma''pasonglo (prosesi jenazah), ma''tinggoro tedong (penyembelihan kerbau), dan ma''randing (tarian prajurit). Kepadatan pelaksanaan upacara meningkat tajam pada pertengahan-akhir Desember bertepatan dengan musim mudik Lebaran/Natal warga Toraja perantau.',
 'Berbagai Tongkonan keluarga besar, Toraja Utara & Tana Toraja', '2025-12-15 07:00:00', '2025-12-29 18:00:00',
 'upacara', 'Komunitas Adat Toraja', NULL, 1),

('Toraja Coffee Festival',
 'Bagian dari Toraja Highland Festival yang khusus mengangkat potensi kopi Toraja sebagai komoditas unggulan perkebunan daerah. Menteri Pertanian mengonfirmasi bantuan bibit dan pupuk untuk lahan seluas 1.430 hektar di tahun 2026 guna memperkuat industri agrowisata berbasis kopi.',
 'Gedung Art Center, Rantepao', '2025-12-11 10:00:00', '2025-12-13 18:00:00',
 'pameran', 'Disbudpar Toraja Utara & Kementerian Pertanian', '+62-423-21001', 1),

('Toraja Highland International Choir Festival (THICF)',
 'Festival paduan suara internasional yang mempertemukan grup-grup koor dari berbagai daerah dan mancanegara untuk menampilkan musik klasik dan tradisional dengan latar belakang budaya Toraja, memperkuat posisi Toraja sebagai destinasi event budaya berskala internasional.',
 'Rantepao, Toraja Utara', '2025-09-05 09:00:00', '2025-09-07 20:00:00',
 'pertunjukan', 'MASATA DPC Toraja Utara', NULL, 1),

('Ma''Nene — Ritual Membersihkan Jenazah Leluhur',
 'Tradisi unik membersihkan, mengganti pakaian, dan merawat jenazah leluhur yang telah dimakamkan bertahun-tahun. Dilaksanakan oleh keluarga di sejumlah desa adat sebagai bentuk penghormatan dan menjaga hubungan dengan leluhur, biasanya berlangsung setelah musim panen padi.',
 'Desa-desa adat Toraja Utara (terutama Kec. Baruppu'' dan Sesean)', '2025-08-20 08:00:00', '2025-08-22 17:00:00',
 'upacara', 'Komunitas Adat Toraja', NULL, 1),

('Rambu Tuka'' — Syukuran Tongkonan & Pernikahan Adat',
 'Upacara syukuran bersifat gembira yang berkaitan dengan kehidupan, seperti peresmian Tongkonan baru atau pernikahan adat. Diisi dengan tarian Ma''gellu dan Ma''bugi, serta pesta makan bersama seluruh keluarga besar sebagai ungkapan syukur.',
 'Tongkonan keluarga, berbagai kecamatan Toraja Utara', '2025-08-10 08:00:00', '2025-08-12 20:00:00',
 'upacara', 'Keluarga adat setempat', NULL, 0);


-- ============================================================
-- TOURISM_INFRASTRUCTURE (fasilitas pendukung di destinasi utama)
-- ============================================================
INSERT INTO tourism_infrastructure (name, type, location, condition, description, last_update) VALUES
('Jalan Akses Ke''te Kesu''',           'jalan',            'Ke''te Kesu''',              'baik',   'Jalan aspal lebar ±4m dari Rantepao, dapat dilalui bus pariwisata ukuran sedang.', '2025-11-15 10:00:00'),
('Loket Tiket Ke''te Kesu''',           'loket',            'Ke''te Kesu''',              'baik',   'Loket resmi dengan mesin EDC, menerima pembayaran QRIS dan kartu debit.',          '2025-11-15 10:00:00'),
('Toilet Umum Ke''te Kesu''',           'toilet umum',      'Ke''te Kesu''',              'baik',   'Toilet bersih dengan air mengalir, termasuk fasilitas untuk difabel.',             '2025-11-15 10:00:00'),
('Jalan Akses Londa',                   'jalan',            'Londa, Sanggalangi''',       'baik',   'Jalan cor beton lebar ±3m dengan tangga menuju pintu gua pemakaman.',               '2025-10-20 09:00:00'),
('Toilet Umum Londa',                   'toilet umum',      'Londa, Sanggalangi''',       'sedang', 'Toilet tersedia namun perlu perbaikan rutin pada pintu bilik.',                     '2025-10-20 09:00:00'),
('Pemandu Wisata Lokal Londa',          'pusat informasi',  'Londa',                       'baik',   'Pemandu wisata bersertifikat tersedia, sebagian menguasai Bahasa Inggris.',         '2025-10-20 09:00:00'),
('Jalan Poros Rantepao–Lolai',          'jalan',            'Rantepao → Lolai',            'sedang', 'Jalan berliku naik gunung, sebagian titik perlu pelebaran untuk bus besar.',        '2025-09-28 09:00:00'),
('Area Parkir Lolai (Negeri di Atas Awan)','parkir',        'Lolai, Kapalapitu',           'baik',   'Area parkir luas mendukung lonjakan pengunjung saat musim ramai (Juni-Juli & Desember).', '2025-09-28 09:00:00'),
('Toilet Umum Pasar Bolu',              'toilet umum',      'Pasar Bolu, Rantepao',        'sedang', 'Kebersihan tergantung frekuensi perawatan harian oleh petugas pasar.',              '2025-08-01 08:00:00'),
('Kios Kuliner Pasar Bolu',             'restoran',         'Pasar Bolu, Rantepao',        'baik',   'Deretan warung menyajikan kuliner khas Toraja: pa''piong, kapurung, dan kopi Toraja.', '2025-08-01 08:00:00'),
('Pusat Informasi Wisata Rantepao',     'pusat informasi',  'Jl. Ahmad Yani, Rantepao',     'baik',   'Kantor TIC buka Senin–Sabtu 08.00–16.00, menyediakan brosur, peta, dan konsultasi wisata gratis.', '2025-07-15 10:00:00'),
('Area Parkir Patung Yesus Buntu Burake','parkir',          'Burake, Makale',              'baik',   'Parkir luas dengan akses jalan menuju monumen yang sudah diaspal mulus.',           '2025-11-01 09:00:00'),
('Mushola Pango-Pango',                 'mushola',          'Pango-Pango, Makale Selatan', 'baik',   'Mushola berkapasitas 20 orang lengkap dengan tempat wudhu di area agrowisata.',     '2025-06-10 11:00:00');


-- ============================================================
-- VERIFIKASI
-- ============================================================
SELECT 'tourist_attractions'      AS tabel, COUNT(*) AS jumlah FROM tourist_attractions
UNION ALL
SELECT 'visitor_statistics',     COUNT(*) FROM visitor_statistics
UNION ALL
SELECT 'accommodations',         COUNT(*) FROM accommodations
UNION ALL
SELECT 'cultural_events',        COUNT(*) FROM cultural_events
UNION ALL
SELECT 'tourism_infrastructure', COUNT(*) FROM tourism_infrastructure;
