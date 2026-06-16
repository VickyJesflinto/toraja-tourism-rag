-- ============================================================
-- TORAJA TOURISM — SAMPLE DATA
-- Jalankan SETELAH schema.sql
-- ============================================================

USE toraja_tourism;

-- ============================================================
-- TOURIST_ATTRACTIONS
-- ============================================================
INSERT INTO tourist_attractions
  (name, category, description, location, district, latitude, longitude, entry_fee, rating, is_active)
VALUES
('Ke''te Kesu''',       'budaya',
 'Desa adat Toraja paling terkenal yang masih mempertahankan arsitektur Tongkonan asli berusia ratusan tahun. Terdapat deretan lumbung padi (alang), kuburan batu kuno, dan tau-tau (patung kayu leluhur) yang diletakkan di tebing batu. Ke''te Kesu'' sering disebut sebagai "museum hidup" budaya Toraja.',
 'Ke''te Kesu'', Kec. Kesu''', 'Kesu''', -2.9731, 119.9394, 20000.00, 4.80, 1),

('Londa',               'budaya',
 'Situs pemakaman tebing batu yang sangat bersejarah. Di sini terdapat ratusan tau-tau berusia lebih dari 300 tahun berjajar di ceruk-ceruk batu. Pengunjung dapat masuk ke dalam gua tebing menggunakan lampu petromaks dan menyaksikan peti-peti mati leluhur Toraja yang tersimpan di dalamnya.',
 'Londa, Kec. Sanggalangi', 'Sanggalangi', -2.9950, 119.9183, 20000.00, 4.70, 1),

('Lemo',                'budaya',
 'Tebing makam ikonik dengan 75 lubang makam yang dipahat langsung ke dinding batu. Di depan setiap lubang berdiri tau-tau berpakaian tradisional yang menatap keluar. Lemo adalah salah satu situs pemakaman paling dramatis dan fotogenik di seluruh Toraja.',
 'Lemo, Kec. Makale Utara', 'Makale Utara', -3.0500, 119.8700, 20000.00, 4.75, 1),

('Batu Tumonga',        'alam',
 'Hamparan sawah bertingkat yang indah di ketinggian ±1300 mdpl dikelilingi kabut pagi. Terdapat lebih dari 100 menhir (batu megalitik) prasejarah yang tersebar di antara ladang. Dari sini pengunjung dapat menikmati panorama lembah Rantepao yang memukau.',
 'Batu Tumonga, Kec. Sesean', 'Sesean', -2.8710, 119.9050, 10000.00, 4.65, 1),

('Pasar Bolu Rantepao', 'budaya',
 'Pasar tradisional terbesar di Toraja yang diadakan setiap 6 hari sekali (sesuai kalender Toraja). Terkenal sebagai pasar kerbau terbesar di Indonesia — ribuan kerbau diperjualbelikan di sini. Kerbau albino (tedong bonga) bisa berharga ratusan juta rupiah. Pasar ini juga menjual babi, hasil bumi, dan kerajinan tangan.',
 'Rantepao', 'Rantepao', -2.9641, 119.8983, 0.00, 4.40, 1),

('Pallawa',             'budaya',
 'Kompleks Tongkonan (rumah adat) yang masih terawat dengan baik. Deretan tanduk kerbau yang menghiasi bagian depan rumah menunjukkan status sosial dan jumlah upacara adat yang pernah dilaksanakan oleh keluarga pemilik. Beberapa Tongkonan berusia lebih dari 300 tahun.',
 'Pallawa, Kec. Tikala', 'Tikala', -2.9200, 119.9500, 15000.00, 4.50, 1),

('Tilanga',             'alam',
 'Kolam renang alami dengan air yang sangat jernih dan menyegarkan. Terletak di lembah yang tenang, kolam ini dikelilingi pepohonan tropis yang rindang. Airnya berasal dari mata air pegunungan Toraja yang dingin dan bersih.',
 'Tilanga, Kec. Makale', 'Makale', -3.0750, 119.8550, 15000.00, 4.30, 1),

('Gunung Sesean',       'alam',
 'Puncak tertinggi di Toraja Utara dengan ketinggian ±2.150 mdpl. Perjalanan pendakian melewati hutan tropis yang masih alami dan perkampungan tradisional. Dari puncak, panorama seluruh dataran Toraja terlihat sempurna saat cuaca cerah.',
 'Kec. Sesean', 'Sesean', -2.8500, 119.9200, 0.00, 4.55, 1),

('Kambira',             'budaya',
 'Situs pemakaman bayi unik di pohon tarra yang berusia ratusan tahun. Menurut tradisi Toraja, bayi yang meninggal sebelum tumbuh gigi dikuburkan di dalam lubang pohon karena dianggap masih suci dan menyatu dengan alam. Situs ini menjadi daya tarik spiritual yang langka.',
 'Kambira, Kec. Sanggalangi', 'Sanggalangi', -2.9800, 119.9350, 10000.00, 4.45, 1),

('Sa''dan',             'budaya',
 'Desa penghasil kain tenun tradisional Toraja (kain pa''tedong dan kain sekomandi). Pengunjung dapat menyaksikan langsung proses menenun menggunakan alat tenun tradisional dan membeli kain langsung dari pengrajin. Motif tenun Toraja sangat khas dengan warna merah, hitam, dan kuning.',
 'Sa''dan, Kec. Sa''dan', 'Sa''dan', -2.8900, 119.9700, 0.00, 4.35, 1),

('Batutumonga Viewpoint','alam',
 'Titik pandang terbaik untuk menikmati keindahan panorama lembah Toraja. Dari ketinggian 1.200 mdpl, pengunjung dapat melihat hamparan sawah hijau, perkampungan tradisional dengan Tongkonan, serta pegunungan yang mengelilingi Toraja. Waktu terbaik mengunjungi adalah saat matahari terbit.',
 'Batutumonga, Kec. Sesean', 'Sesean', -2.8600, 119.9100, 5000.00, 4.60, 1),

('Museum Negeri Toraja', 'budaya',
 'Museum yang menyimpan koleksi lengkap artefak budaya Toraja: pakaian adat, perhiasan, senjata tradisional, miniatur Tongkonan, dan dokumentasi upacara adat. Tempat terbaik untuk memahami sejarah dan kebudayaan Toraja sebelum menjelajahi destinasi lainnya.',
 'Makale', 'Makale', -3.0950, 119.8600, 10000.00, 4.20, 1);


-- ============================================================
-- VISITOR_STATISTICS (2023 & 2024)
-- ============================================================
-- Ke'te Kesu' (attraction_id = 1)
INSERT INTO visitor_statistics (attraction_id, year, month, domestic, foreign_vis, total, revenue) VALUES
(1, 2024, 1,  2850, 312, 3162, 63240000), (1, 2024, 2,  2640, 298, 2938, 58760000),
(1, 2024, 3,  3120, 425, 3545, 70900000), (1, 2024, 4,  3500, 480, 3980, 79600000),
(1, 2024, 5,  3200, 410, 3610, 72200000), (1, 2024, 6,  2900, 385, 3285, 65700000),
(1, 2024, 7,  3800, 520, 4320, 86400000), (1, 2024, 8,  4100, 590, 4690, 93800000),
(1, 2024, 9,  3600, 465, 4065, 81300000), (1, 2024,10,  3300, 430, 3730, 74600000),
(1, 2024,11,  3100, 405, 3505, 70100000), (1, 2024,12,  5200, 780, 5980,119600000),
(1, 2023, 1,  2500, 280, 2780, 55600000), (1, 2023, 2,  2300, 265, 2565, 51300000),
(1, 2023, 3,  2800, 370, 3170, 63400000), (1, 2023, 4,  3100, 420, 3520, 70400000),
(1, 2023, 5,  2900, 360, 3260, 65200000), (1, 2023, 6,  2600, 335, 2935, 58700000),
(1, 2023, 7,  3400, 460, 3860, 77200000), (1, 2023, 8,  3700, 530, 4230, 84600000),
(1, 2023, 9,  3200, 410, 3610, 72200000), (1, 2023,10,  3000, 390, 3390, 67800000),
(1, 2023,11,  2800, 360, 3160, 63200000), (1, 2023,12,  4800, 710, 5510,110200000);

-- Londa (attraction_id = 2)
INSERT INTO visitor_statistics (attraction_id, year, month, domestic, foreign_vis, total, revenue) VALUES
(2, 2024, 1,  1950, 245, 2195, 43900000), (2, 2024, 2,  1820, 220, 2040, 40800000),
(2, 2024, 3,  2100, 310, 2410, 48200000), (2, 2024, 4,  2400, 360, 2760, 55200000),
(2, 2024, 5,  2200, 315, 2515, 50300000), (2, 2024, 6,  1980, 280, 2260, 45200000),
(2, 2024, 7,  2600, 385, 2985, 59700000), (2, 2024, 8,  2850, 420, 3270, 65400000),
(2, 2024, 9,  2450, 355, 2805, 56100000), (2, 2024,10,  2250, 320, 2570, 51400000),
(2, 2024,11,  2100, 295, 2395, 47900000), (2, 2024,12,  3600, 560, 4160, 83200000);

-- Lemo (attraction_id = 3)
INSERT INTO visitor_statistics (attraction_id, year, month, domestic, foreign_vis, total, revenue) VALUES
(3, 2024, 1,  2100, 290, 2390, 47800000), (3, 2024, 2,  1950, 270, 2220, 44400000),
(3, 2024, 3,  2350, 350, 2700, 54000000), (3, 2024, 4,  2700, 410, 3110, 62200000),
(3, 2024, 5,  2500, 375, 2875, 57500000), (3, 2024, 6,  2200, 330, 2530, 50600000),
(3, 2024, 7,  2900, 450, 3350, 67000000), (3, 2024, 8,  3100, 490, 3590, 71800000),
(3, 2024, 9,  2700, 400, 3100, 62000000), (3, 2024,10,  2450, 360, 2810, 56200000),
(3, 2024,11,  2300, 335, 2635, 52700000), (3, 2024,12,  4100, 630, 4730, 94600000);

-- Pasar Bolu (attraction_id = 5)
INSERT INTO visitor_statistics (attraction_id, year, month, domestic, foreign_vis, total, revenue) VALUES
(5, 2024, 1,  3500,  80, 3580,       0), (5, 2024, 2,  3200,  72, 3272,       0),
(5, 2024, 3,  3900,  95, 3995,       0), (5, 2024, 4,  4200, 110, 4310,       0),
(5, 2024, 5,  3800,  98, 3898,       0), (5, 2024, 6,  3400,  88, 3488,       0),
(5, 2024, 7,  4600, 130, 4730,       0), (5, 2024, 8,  5100, 155, 5255,       0),
(5, 2024, 9,  4400, 120, 4520,       0), (5, 2024,10,  4000, 105, 4105,       0),
(5, 2024,11,  3700,  95, 3795,       0), (5, 2024,12,  6500, 210, 6710,       0);


-- ============================================================
-- ACCOMMODATIONS
-- ============================================================
INSERT INTO accommodations
  (name, type, location, district, latitude, longitude, price_min, price_max, capacity, rating, contact, is_active)
VALUES
('Toraja Heritage Hotel',       'hotel',
 'Jl. Poros Makale No. 1, Rantepao', 'Rantepao', -2.9600, 119.8970, 850000, 2500000, 56, 4.60, '+62-423-21155', 1),

('Mentirotiku Hotel',           'hotel',
 'Jl. Landorundun No. 63, Rantepao', 'Rantepao', -2.9650, 119.9010, 350000, 900000,  40, 4.20, '+62-423-21675', 1),

('Marante Highland Resort',     'resort',
 'Jl. Poros Rantepao–Makale Km. 3', 'Rantepao', -2.9800, 119.9100, 600000, 1800000, 30, 4.50, '+62-811-4200-999', 1),

('Tongkonan Homestay Ke''te Kesu''', 'homestay',
 'Desa Ke''te Kesu''', 'Kesu''', -2.9730, 119.9390, 150000, 300000,   8, 4.55, '+62-852-4231-0000', 1),

('Batutumonga Guesthouse',      'homestay',
 'Batutumonga', 'Sesean', -2.8650, 119.9080, 200000, 400000,  12, 4.45, '+62-821-8800-1234', 1),

('Toraja Villa Batutumonga',    'villa',
 'Batutumonga, Kec. Sesean', 'Sesean', -2.8620, 119.9070, 500000, 1200000, 12, 4.70, '+62-813-5500-7788', 1),

('Rantepao Lodge',              'hotel',
 'Jl. Mappanyuki No. 8, Rantepao', 'Rantepao', -2.9670, 119.8960, 400000, 1100000, 45, 4.30, '+62-423-21433', 1),

('Sa''dan Weaving Homestay',    'homestay',
 'Desa Sa''dan', 'Sa''dan', -2.8910, 119.9680, 120000, 250000,   6, 4.35, '+62-823-4500-6677', 1),

('Pinus Toraja Hotel',          'hotel',
 'Jl. Ahmad Yani No. 12, Makale', 'Makale', -3.0960, 119.8610, 300000, 750000,  35, 4.10, '+62-423-22345', 1),

('Lolai Clouds Cottage',        'cottage',
 'Lolai (Negeri di Atas Awan), Kec. Tikala', 'Tikala', -2.9150, 119.9550, 350000, 800000, 10, 4.65, '+62-852-9900-4455', 1);


-- ============================================================
-- CULTURAL_EVENTS
-- ============================================================
INSERT INTO cultural_events
  (name, description, location, event_date, end_date, category, organizer, contact, is_recurring)
VALUES
('Lovely December Toraja',
 'Festival pariwisata terbesar Toraja yang diselenggarakan setiap bulan Desember. Menampilkan berbagai pertunjukan seni budaya, upacara adat, pesta rakyat, lomba-lomba tradisional, kuliner khas Toraja, dan wisata malam. Festival ini menjadi magnet wisatawan domestik dan mancanegara setiap tahunnya.',
 'Rantepao & Makale', '2024-12-01 08:00:00', '2024-12-31 22:00:00',
 'festival', 'Dinas Pariwisata Toraja Utara', '+62-423-21001', 1),

('Toraja International Festival (TIF)',
 'Festival budaya berkelas internasional yang menampilkan pertunjukan seni dari berbagai daerah Indonesia dan mancanegara, dikombinasikan dengan kekayaan budaya lokal Toraja. Acara ini mencakup pentas musik, tarian kolosal, pameran kerajinan tangan, dan tur budaya ke situs-situs bersejarah.',
 'Lapangan Bakti Rantepao', '2024-06-15 09:00:00', '2024-06-18 22:00:00',
 'festival', 'Pemkab Toraja Utara', '+62-423-21500', 1),

('Rambu Solo'' — Upacara Pemakaman Bangsawan',
 'Upacara pemakaman adat Toraja yang sakral dan megah. Merupakan "pesta kematian" yang berlangsung selama 3-7 hari dengan serangkaian ritual: ma''pasonglo (prosesi jenazah), ma''tinggoro tedong (penyembelihan kerbau), dan ma''randing (tarian prajurit). Jumlah kerbau yang disembelih menunjukkan status sosial almarhum.',
 'Tongkonan keluarga besar, berbagai kecamatan', '2024-07-15 07:00:00', '2024-07-20 18:00:00',
 'upacara', 'Komunitas Adat Toraja', NULL, 0),

('Rambu Tuka'' — Syukuran Tongkonan Baru',
 'Upacara syukuran untuk peresmian rumah adat Tongkonan yang baru dibangun atau direnovasi. Berbeda dengan Rambu Solo'', upacara ini bersifat gembira dan meriah. Diisi dengan tarian Ma''gellu, Ma''bugi, dan pesta makan bersama seluruh keluarga besar.',
 'Tongkonan Pallawa, Kec. Tikala', '2024-08-20 08:00:00', '2024-08-22 20:00:00',
 'upacara', 'Keluarga Besar Tongkonan Pallawa', NULL, 0),

('Pesta Panen Adat (Ma''bua'')',
 'Upacara syukuran panen padi yang diadakan oleh komunitas petani Toraja. Ritual ini melibatkan doa bersama, persembahan kepada leluhur, dan pesta makan dengan hasil panen terbaik. Diselenggarakan setelah musim panen raya selesai.',
 'Desa-desa adat di Toraja Utara', '2024-09-10 07:00:00', '2024-09-11 18:00:00',
 'upacara', 'Komunitas Petani Adat', NULL, 1),

('Pameran Tenun Tradisional Toraja',
 'Pameran dan bazaar kain tenun tradisional Toraja dari berbagai kecamatan. Pengunjung dapat menyaksikan langsung proses menenun, belajar membuat tenun, dan membeli kain berkualitas langsung dari pengrajin. Motif-motif kain: pa''tedong, pa''barre allo, dan sekomandi ditampilkan lengkap.',
 'Gedung Kesenian Rantepao', '2024-10-05 09:00:00', '2024-10-07 17:00:00',
 'pameran', 'Dinas Perindustrian Toraja Utara', '+62-423-21700', 1),

('Lovely December Toraja 2025',
 'Edisi tahun 2025 dari festival pariwisata terbesar Toraja. Tema tahun ini: "Toraja Mendunia — Budaya yang Hidup". Akan menampilkan kolaborasi seniman Toraja dengan artis internasional, konser musik tradisional dan modern, pawai budaya, dan pameran foto.',
 'Rantepao & Makale', '2025-12-01 08:00:00', '2025-12-31 22:00:00',
 'festival', 'Dinas Pariwisata Toraja Utara', '+62-423-21001', 1);


-- ============================================================
-- TOURISM_INFRASTRUCTURE
-- ============================================================
INSERT INTO tourism_infrastructure (name, type, location, stat_condition, description, last_update) VALUES
('Jalan Masuk Ke''te Kesu''',       'jalan',   'Ke''te Kesu''',         'baik',   'Jalan aspal lebar ±4m, dapat dilalui bus pariwisata ukuran sedang.',           '2024-03-15 10:00:00'),
('Toilet Umum Ke''te Kesu''',       'toilet',  'Ke''te Kesu''',         'baik',   '4 bilik toilet bersih, air mengalir, tersedia toilet difabel.',                '2024-03-15 10:00:00'),
('Loket Tiket Ke''te Kesu''',       'loket',   'Ke''te Kesu''',         'baik',   'Loket permanen dengan mesin EDC, menerima QRIS dan kartu debit.',              '2024-03-15 10:00:00'),
('Mushola Ke''te Kesu''',           'mushola', 'Ke''te Kesu''',         'baik',   'Mushola berkapasitas 20 orang, lengkap dengan tempat wudhu.',                  '2024-03-15 10:00:00'),
('Area Parkir Ke''te Kesu''',       'parkir',  'Ke''te Kesu''',         'sedang', 'Parkir tanah, kapasitas ±30 kendaraan roda 4. Belum diaspal.',                 '2024-03-15 10:00:00'),

('Jalan Masuk Londa',               'jalan',   'Londa, Sanggalangi',    'baik',   'Jalan cor beton, lebar ±3m. Terdapat tangga menuju pintu gua.',               '2024-04-10 09:00:00'),
('Toilet Umum Londa',               'toilet',  'Londa, Sanggalangi',    'sedang', '2 bilik toilet, kondisi cukup bersih. Perlu perbaikan pintu bilik.',           '2024-04-10 09:00:00'),
('Pemandu Wisata Lokal Londa',      'pusat_informasi', 'Londa',         'baik',   'Tersedia pemandu wisata lokal bersertifikat yang menguasai Bahasa Inggris.',   '2024-04-10 09:00:00'),

('Jalan Poros Rantepao–Ke''te Kesu''','jalan', 'Rantepao → Ke''te Kesu''', 'baik','Jalan provinsi beraspal mulus, jarak ±4 km dari pusat Rantepao.',            '2024-02-20 10:00:00'),
('Toilet Umum Pasar Bolu',          'toilet',  'Pasar Bolu, Rantepao',  'sedang', 'Toilet pasar tradisional. Kebersihan bergantung pada frekuensi pembersihan.', '2024-05-01 08:00:00'),
('Pusat Informasi Wisata Rantepao', 'pusat_informasi', 'Jl. Ahmad Yani, Rantepao', 'baik', 'Kantor TIC (Tourist Information Center) buka Senin–Sabtu 08.00–16.00. Tersedia brosur, peta, dan konsultasi wisata gratis.', '2024-01-15 10:00:00'),
('Jalan Menuju Batutumonga',        'jalan',   'Rantepao → Batutumonga','sedang', 'Jalan berliku naik gunung, lebar ±2.5m. Beberapa titik perlu perbaikan aspal. Tidak disarankan untuk bus besar.', '2024-03-28 09:00:00'),
('Toilet Umum Lemo',                'toilet',  'Lemo, Makale Utara',    'baik',   '3 bilik toilet bersih dengan air mengalir. Dikelola langsung oleh pengelola situs.', '2024-04-22 10:00:00'),
('Kios Kuliner Pasar Bolu',         'restoran','Pasar Bolu, Rantepao',   'baik',   'Deretan warung makan menyajikan kuliner khas Toraja: pa''piong, kapurung, dan kopi Toraja.', '2024-05-01 08:00:00'),
('Area Parkir Lemo',                'parkir',  'Lemo, Makale Utara',    'baik',   'Area parkir beraspal, kapasitas ±40 kendaraan. Tersedia petugas parkir.', '2024-04-22 10:00:00');


-- ============================================================
-- VERIFIKASI
-- ============================================================
SELECT 'tourist_attractions'    AS tabel, COUNT(*) AS jumlah FROM tourist_attractions
UNION ALL
SELECT 'visitor_statistics',   COUNT(*) FROM visitor_statistics
UNION ALL
SELECT 'accommodations',       COUNT(*) FROM accommodations
UNION ALL
SELECT 'cultural_events',      COUNT(*) FROM cultural_events
UNION ALL
SELECT 'tourism_infrastructure',COUNT(*) FROM tourism_infrastructure;
