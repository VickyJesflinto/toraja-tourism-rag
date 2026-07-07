"""
tests/test_ragas_metrics_logic.py

Unit test untuk logika murni di evaluation/ragas_metrics.py dan
evaluation/run_ragas_evaluation.py -- bagian yang tidak memanggil LLM
(parsing JSON, formula precision/recall, agregasi statistik).

Pemanggilan LLM aktual (_call_judge_llm) di-mock sepenuhnya di sini, karena
itu bukan logika yang perlu diuji secara unit (sudah pasti tergantung respons
API eksternal) -- yang diuji adalah bagaimana hasil respons tersebut diproses
menjadi skor numerik yang benar.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest


class TestParseJsonResponse:
    def test_parses_plain_json_array(self):
        from evaluation.ragas_metrics import _parse_json_response
        result = _parse_json_response('["a", "b", "c"]')
        assert result == ["a", "b", "c"]

    def test_parses_json_wrapped_in_markdown_code_block(self):
        from evaluation.ragas_metrics import _parse_json_response
        raw = '```json\n["klaim 1", "klaim 2"]\n```'
        result = _parse_json_response(raw)
        assert result == ["klaim 1", "klaim 2"]

    def test_parses_plain_object(self):
        from evaluation.ragas_metrics import _parse_json_response
        result = _parse_json_response('{"supported": true}')
        assert result == {"supported": True}

    def test_raises_on_invalid_json(self):
        from evaluation.ragas_metrics import _parse_json_response
        with pytest.raises(Exception):
            _parse_json_response("ini bukan json sama sekali")


class TestCosineSimilarityHelper:
    def test_identical_vectors_similarity_one(self):
        import numpy as np
        from evaluation.ragas_metrics import _cosine_similarity
        v = np.array([1.0, 2.0, 3.0])
        assert abs(_cosine_similarity(v, v) - 1.0) < 1e-6

    def test_zero_vector_returns_zero_safely(self):
        import numpy as np
        from evaluation.ragas_metrics import _cosine_similarity
        a = np.zeros(5)
        b = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        assert _cosine_similarity(a, b) == 0.0


class TestFaithfulnessFormula:
    """Faithfulness = jumlah klaim yang didukung konteks / total klaim."""

    def test_all_claims_supported_gives_score_one(self, monkeypatch):
        import evaluation.ragas_metrics as m

        call_sequence = [
            '["Ke\'te Kesu adalah desa wisata", "Memiliki rumah Tongkonan"]',
            '{"supported": true}',
            '{"supported": true}',
        ]
        calls = iter(call_sequence)
        monkeypatch.setattr(m, "_call_judge_llm", lambda *a, **kw: next(calls))

        result = m.faithfulness("Apa itu Ke'te Kesu?", "Ke'te Kesu adalah desa wisata dengan Tongkonan.",
                                 ["Ke'te Kesu adalah desa wisata budaya dengan rumah Tongkonan."])
        assert result["score"] == 1.0
        assert result["n_supported"] == 2
        assert result["n_total"] == 2

    def test_half_claims_supported_gives_score_half(self, monkeypatch):
        import evaluation.ragas_metrics as m

        call_sequence = [
            '["Klaim benar", "Klaim mengarang"]',
            '{"supported": true}',
            '{"supported": false}',
        ]
        calls = iter(call_sequence)
        monkeypatch.setattr(m, "_call_judge_llm", lambda *a, **kw: next(calls))

        result = m.faithfulness("pertanyaan", "jawaban dengan 1 klaim benar 1 mengarang", ["konteks"])
        assert result["score"] == 0.5

    def test_no_claims_supported_gives_score_zero(self, monkeypatch):
        import evaluation.ragas_metrics as m

        call_sequence = [
            '["Klaim halusinasi 1", "Klaim halusinasi 2"]',
            '{"supported": false}',
            '{"supported": false}',
        ]
        calls = iter(call_sequence)
        monkeypatch.setattr(m, "_call_judge_llm", lambda *a, **kw: next(calls))

        result = m.faithfulness("pertanyaan", "jawaban mengarang total", ["konteks tidak relevan"])
        assert result["score"] == 0.0

    def test_empty_answer_returns_zero_without_calling_llm(self, monkeypatch):
        import evaluation.ragas_metrics as m

        called = {"count": 0}
        def fail_if_called(*a, **kw):
            called["count"] += 1
            return "{}"
        monkeypatch.setattr(m, "_call_judge_llm", fail_if_called)

        result = m.faithfulness("pertanyaan", "", ["konteks"])
        assert result["score"] == 0.0
        assert called["count"] == 0

    def test_malformed_llm_response_does_not_crash(self, monkeypatch):
        import evaluation.ragas_metrics as m

        monkeypatch.setattr(m, "_call_judge_llm", lambda *a, **kw: "ini bukan json sama sekali")

        result = m.faithfulness("pertanyaan", "jawaban", ["konteks"])
        assert result["score"] == 0.0


class TestAnswerRelevancyFormula:
    def test_relevancy_uses_average_of_similarities(self, monkeypatch):
        import evaluation.ragas_metrics as m
        import numpy as np

        monkeypatch.setattr(
            m, "_call_judge_llm",
            lambda *a, **kw: '["pertanyaan reverse 1", "pertanyaan reverse 2"]'
        )

        class FakeEmbedderForTest:
            def encode_query(self, text):
                h = hash(text) % 1000
                vec = np.zeros(10)
                vec[h % 10] = 1.0
                return vec

        result = m.answer_relevancy("pertanyaan asli", "jawaban", FakeEmbedderForTest())
        assert "score" in result
        assert 0.0 <= result["score"] <= 1.0
        assert len(result["similarities"]) == 2

    def test_empty_answer_returns_zero(self, monkeypatch):
        import evaluation.ragas_metrics as m

        called = {"count": 0}
        def track_call(*a, **kw):
            called["count"] += 1
            return "{}"
        monkeypatch.setattr(m, "_call_judge_llm", track_call)

        class DummyEmbedder:
            def encode_query(self, text):
                import numpy as np
                return np.zeros(10)

        result = m.answer_relevancy("pertanyaan", "", DummyEmbedder())
        assert result["score"] == 0.0
        assert called["count"] == 0


class TestContextPrecisionFormula:
    """Context Precision menggunakan Average Precision: hanya posisi yang
    relevan dihitung precision@k-nya, lalu dirata-rata."""

    def test_all_contexts_relevant_gives_score_one(self, monkeypatch):
        import evaluation.ragas_metrics as m
        monkeypatch.setattr(m, "_call_judge_llm", lambda *a, **kw: '{"relevant": true}')

        result = m.context_precision("pertanyaan", ["konteks 1", "konteks 2", "konteks 3"])
        assert result["score"] == 1.0
        assert result["n_relevant"] == 3

    def test_no_contexts_relevant_gives_score_zero(self, monkeypatch):
        import evaluation.ragas_metrics as m
        monkeypatch.setattr(m, "_call_judge_llm", lambda *a, **kw: '{"relevant": false}')

        result = m.context_precision("pertanyaan", ["konteks tidak relevan 1", "konteks tidak relevan 2"])
        assert result["score"] == 0.0

    def test_relevant_first_then_irrelevant_scores_higher_than_reverse(self, monkeypatch):
        """
        Skenario kunci Average Precision: [relevan, tidak_relevan] harus
        mendapat skor lebih tinggi daripada [tidak_relevan, relevan],
        karena retriever yang baik menempatkan chunk relevan di posisi atas.
        """
        import evaluation.ragas_metrics as m

        responses_a = iter(['{"relevant": true}', '{"relevant": false}'])
        monkeypatch.setattr(m, "_call_judge_llm", lambda *a, **kw: next(responses_a))
        result_a = m.context_precision("q", ["relevan", "tidak relevan"])

        responses_b = iter(['{"relevant": false}', '{"relevant": true}'])
        monkeypatch.setattr(m, "_call_judge_llm", lambda *a, **kw: next(responses_b))
        result_b = m.context_precision("q", ["tidak relevan", "relevan"])

        assert result_a["score"] > result_b["score"]
        assert result_a["score"] == 1.0
        assert result_b["score"] == 0.5

    def test_empty_contexts_returns_zero(self):
        from evaluation.ragas_metrics import context_precision
        result = context_precision("pertanyaan", [])
        assert result["score"] == 0.0


class TestContextRecallFormula:
    def test_all_ground_truth_claims_attributed_gives_score_one(self, monkeypatch):
        import evaluation.ragas_metrics as m

        call_sequence = [
            '["klaim ground truth 1", "klaim ground truth 2"]',
            '{"attributed": true}',
            '{"attributed": true}',
        ]
        calls = iter(call_sequence)
        monkeypatch.setattr(m, "_call_judge_llm", lambda *a, **kw: next(calls))

        result = m.context_recall("ground truth lengkap", ["konteks yang menjawab semuanya"])
        assert result["score"] == 1.0

    def test_partial_ground_truth_attributed_gives_partial_score(self, monkeypatch):
        import evaluation.ragas_metrics as m

        call_sequence = [
            '["klaim 1 ada di konteks", "klaim 2 hilang dari konteks", "klaim 3 hilang"]',
            '{"attributed": true}',
            '{"attributed": false}',
            '{"attributed": false}',
        ]
        calls = iter(call_sequence)
        monkeypatch.setattr(m, "_call_judge_llm", lambda *a, **kw: next(calls))

        result = m.context_recall("ground truth dengan 3 klaim", ["konteks parsial"])
        # Toleransi 1e-4 karena context_recall() membulatkan skor ke 4 desimal
        # (round(score, 4)), sehingga 1/3 = 0.333333... dibulatkan jadi 0.3333.
        assert abs(result["score"] - (1/3)) < 1e-4

    def test_empty_ground_truth_returns_zero(self):
        from evaluation.ragas_metrics import context_recall
        result = context_recall("", ["konteks"])
        assert result["score"] == 0.0


class TestRagasResultAggregation:
    def test_overall_score_is_average_of_four_metrics(self):
        from evaluation.ragas_metrics import RagasResult

        r = RagasResult(
            question="q", category="destinasi", difficulty="factual",
            faithfulness_score=1.0, answer_relevancy_score=0.8,
            context_precision_score=0.6, context_recall_score=0.4,
        )
        expected = (1.0 + 0.8 + 0.6 + 0.4) / 4
        assert abs(r.overall_score - expected) < 1e-6

    def test_to_dict_contains_all_fields(self):
        from evaluation.ragas_metrics import RagasResult

        r = RagasResult(
            question="Apa itu Toraja?", category="destinasi", difficulty="factual",
            faithfulness_score=0.9, answer_relevancy_score=0.85,
            context_precision_score=0.75, context_recall_score=0.95,
        )
        d = r.to_dict()
        assert d["question"] == "Apa itu Toraja?"
        assert d["category"] == "destinasi"
        assert d["faithfulness"] == 0.9
        assert "overall" in d


class TestAggregateResultsAcrossSamples:
    def test_aggregate_computes_correct_overall_average(self):
        from evaluation.ragas_metrics import RagasResult
        from evaluation.run_ragas_evaluation import aggregate_results

        results = [
            RagasResult("q1", "destinasi", "factual", 1.0, 1.0, 1.0, 1.0),
            RagasResult("q2", "destinasi", "factual", 0.0, 0.0, 0.0, 0.0),
        ]
        agg = aggregate_results(results)
        assert agg["overall"]["faithfulness"] == 0.5
        assert agg["overall"]["overall_score"] == 0.5

    def test_aggregate_groups_by_category_correctly(self):
        from evaluation.ragas_metrics import RagasResult
        from evaluation.run_ragas_evaluation import aggregate_results

        results = [
            RagasResult("q1", "destinasi", "factual", 1.0, 1.0, 1.0, 1.0),
            RagasResult("q2", "akomodasi", "factual", 0.5, 0.5, 0.5, 0.5),
        ]
        agg = aggregate_results(results)
        assert agg["by_category"]["destinasi"]["overall_score"] == 1.0
        assert agg["by_category"]["akomodasi"]["overall_score"] == 0.5
        assert agg["by_category"]["destinasi"]["n_samples"] == 1

    def test_aggregate_handles_empty_results_list(self):
        from evaluation.run_ragas_evaluation import aggregate_results
        assert aggregate_results([]) == {}

    def test_aggregate_groups_by_difficulty_correctly(self):
        from evaluation.ragas_metrics import RagasResult
        from evaluation.run_ragas_evaluation import aggregate_results

        results = [
            RagasResult("q1", "destinasi", "factual", 1.0, 1.0, 1.0, 1.0),
            RagasResult("q2", "rekomendasi", "multi_hop", 0.2, 0.2, 0.2, 0.2),
        ]
        agg = aggregate_results(results)
        assert agg["by_difficulty"]["factual"]["overall_score"] == 1.0
        assert agg["by_difficulty"]["multi_hop"]["overall_score"] == 0.2


class TestGoldenDatasetIntegrity:
    """Validasi struktural golden dataset itu sendiri."""

    def test_all_samples_have_non_empty_question(self):
        from evaluation.golden_dataset import GOLDEN_DATASET
        for sample in GOLDEN_DATASET:
            assert sample.question.strip() != ""

    def test_all_samples_have_non_empty_ground_truth(self):
        from evaluation.golden_dataset import GOLDEN_DATASET
        for sample in GOLDEN_DATASET:
            assert sample.ground_truth.strip() != ""

    def test_all_samples_have_valid_difficulty(self):
        from evaluation.golden_dataset import GOLDEN_DATASET
        valid_difficulties = {"factual", "reasoning", "multi_hop", "out_of_scope"}
        for sample in GOLDEN_DATASET:
            assert sample.difficulty in valid_difficulties

    def test_out_of_scope_samples_have_empty_ideal_context(self):
        from evaluation.golden_dataset import get_dataset_by_difficulty
        oos_samples = get_dataset_by_difficulty("out_of_scope")
        assert len(oos_samples) > 0
        for sample in oos_samples:
            assert sample.ideal_context == []

    def test_dataset_summary_counts_match_actual_data(self):
        from evaluation.golden_dataset import GOLDEN_DATASET, summary
        s = summary()
        assert s["total_samples"] == len(GOLDEN_DATASET)
        assert sum(s["by_category"].values()) == len(GOLDEN_DATASET)
        assert sum(s["by_difficulty"].values()) == len(GOLDEN_DATASET)
