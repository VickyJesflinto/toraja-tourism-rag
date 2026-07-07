"""
tests/test_chunker.py

Unit test untuk rag/ingestion/chunker.py (TextChunker).
Modul ini murni logika Python (tidak ada dependensi DB/network),
sehingga diuji langsung tanpa fixture database.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from rag.ingestion.chunker import TextChunker, TextChunk


class TestTextChunkerBasic:
    def test_short_text_returns_single_chunk(self):
        """Teks lebih pendek dari chunk_size harus dikembalikan sebagai 1 chunk saja."""
        chunker = TextChunker(chunk_size=1000, overlap=200)
        text = "Toraja adalah destinasi wisata budaya di Sulawesi Selatan."
        result = chunker.chunk(text)

        assert len(result) == 1
        assert result[0].content == text
        assert result[0].chunk_index == 0

    def test_empty_text_returns_single_empty_chunk(self):
        chunker = TextChunker(chunk_size=1000, overlap=200)
        result = chunker.chunk("")
        assert len(result) == 1
        assert result[0].content == ""

    def test_metadata_is_attached_to_chunk(self):
        chunker = TextChunker(chunk_size=1000, overlap=200)
        meta = {"source": "test.pdf", "page": 1}
        result = chunker.chunk("Teks singkat.", base_metadata=meta)
        assert result[0].metadata == meta

    def test_metadata_defaults_to_empty_dict_when_none(self):
        chunker = TextChunker(chunk_size=1000, overlap=200)
        result = chunker.chunk("Teks singkat.")
        assert result[0].metadata == {}

    def test_metadata_not_shared_by_reference_across_chunks(self):
        """Setiap chunk harus punya dict metadata sendiri (bukan reference yang sama)."""
        chunker = TextChunker(chunk_size=50, overlap=10)
        meta = {"source": "doc.pdf"}
        long_text = "Kalimat satu yang agak panjang. " * 10
        result = chunker.chunk(long_text, base_metadata=meta)

        assert len(result) > 1
        result[0].metadata["modified"] = True
        assert "modified" not in result[1].metadata


class TestTextChunkerSplitting:
    def test_long_text_splits_into_multiple_chunks(self):
        chunker = TextChunker(chunk_size=100, overlap=20)
        long_text = (
            "Toraja terkenal dengan upacara adat Rambu Solo. "
            "Wisatawan datang dari berbagai negara untuk menyaksikan ritual ini. "
            "Selain itu, terdapat juga situs Ke'te Kesu yang menakjubkan. "
            "Londa dan Lemo juga menjadi destinasi favorit wisatawan."
        )
        result = chunker.chunk(long_text)
        assert len(result) > 1

    def test_chunk_index_increments_sequentially(self):
        chunker = TextChunker(chunk_size=50, overlap=10)
        long_text = "Kalimat pendek. " * 20
        result = chunker.chunk(long_text)

        indices = [c.chunk_index for c in result]
        assert indices == list(range(len(result)))

    def test_no_chunk_exceeds_size_drastically(self):
        chunker = TextChunker(chunk_size=100, overlap=20)
        text = "Kalimat singkat satu. " * 30
        result = chunker.chunk(text)

        for c in result:
            assert len(c.content) <= chunker.chunk_size * 2

    def test_all_sentences_preserved_no_data_loss(self):
        chunker = TextChunker(chunk_size=80, overlap=15)
        sentences = [
            "Toraja memiliki banyak destinasi wisata budaya.",
            "Ke'te Kesu adalah salah satu yang paling terkenal.",
            "Selain itu Londa juga menarik banyak wisatawan.",
            "Lemo dikenal dengan tau-tau di tebing batu.",
        ]
        text = " ".join(sentences)
        result = chunker.chunk(text)
        combined = " ".join(c.content for c in result)

        for sentence in sentences:
            assert sentence in combined


class TestTextChunkerOverlap:
    def test_overlap_creates_shared_content_between_chunks(self):
        chunker = TextChunker(chunk_size=60, overlap=30)
        text = (
            "Kalimat nomor satu cukup panjang untuk diuji. "
            "Kalimat nomor dua juga cukup panjang untuk diuji. "
            "Kalimat nomor tiga melengkapi pengujian overlap. "
            "Kalimat nomor empat menjadi penutup teks ini."
        )
        result = chunker.chunk(text)

        if len(result) > 1:
            all_words_per_chunk = [set(c.content.split()) for c in result]
            overlap_found = any(
                len(all_words_per_chunk[i] & all_words_per_chunk[i + 1]) > 0
                for i in range(len(all_words_per_chunk) - 1)
            )
            assert overlap_found, "Tidak ditemukan kata yang overlap antar chunk berurutan"

    def test_zero_overlap_still_works(self):
        chunker = TextChunker(chunk_size=50, overlap=0)
        text = "Kalimat satu. Kalimat dua. Kalimat tiga. Kalimat empat. " * 5
        result = chunker.chunk(text)
        assert len(result) >= 1


class TestTextChunkerEdgeCases:
    def test_text_with_no_sentence_terminators(self):
        chunker = TextChunker(chunk_size=50, overlap=10)
        text = "kata " * 100
        result = chunker.chunk(text)
        assert len(result) >= 1
        assert "kata" in result[0].content

    def test_text_with_multiple_punctuation_marks(self):
        chunker = TextChunker(chunk_size=1000, overlap=200)
        text = "Apakah ini destinasi wisata? Ya! Ini sangat indah."
        result = chunker.chunk(text)
        assert len(result) == 1

    def test_very_small_chunk_size(self):
        chunker = TextChunker(chunk_size=5, overlap=2)
        text = "Ini adalah kalimat yang jauh lebih panjang dari ukuran chunk."
        result = chunker.chunk(text)
        assert len(result) >= 1

    def test_single_very_long_sentence_without_split_point(self):
        chunker = TextChunker(chunk_size=30, overlap=5)
        text = "Ini adalah satu kalimat yang sangat panjang sekali tanpa ada tanda baca apapun di tengahnya"
        result = chunker.chunk(text)
        assert len(result) >= 1
        assert result[0].content != ""


class TestTextChunkDataclass:
    def test_textchunk_default_metadata_is_independent(self):
        c1 = TextChunk(content="a", chunk_index=0)
        c2 = TextChunk(content="b", chunk_index=1)

        c1.metadata["key"] = "value"
        assert "key" not in c2.metadata
