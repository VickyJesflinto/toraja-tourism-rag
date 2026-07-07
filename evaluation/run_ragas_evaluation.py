"""
evaluation/run_ragas_evaluation.py

Runner utama evaluasi RAGAS. Alur kerja:

    GOLDEN_DATASET (10 pertanyaan)
        -> LLMChain.chat() [chatbot produksi yang sesungguhnya, RAG + MMR]
        -> kumpulkan: jawaban aktual + konteks yang di-retrieve
        -> hitung 4 metrik RAGAS per sampel (faithfulness, answer_relevancy,
           context_precision, context_recall)
        -> agregasi skor per kategori & keseluruhan
        -> simpan laporan JSON + cetak ringkasan ke terminal

Persyaratan untuk menjalankan script ini secara nyata:
1. OPENROUTER_API_KEY harus diisi di file .env (LLM judge + chatbot
   keduanya memanggil OpenRouter, sehingga ada biaya per panggilan API)
2. Database harus sudah terisi dokumen yang relevan dengan golden dataset
   (jalankan scripts/init_db.py --seed lebih dulu, atau upload dokumen
   manual lewat halaman admin yang mencakup info di golden_dataset.py)
3. Model embedding (sentence-transformers) harus bisa diunduh -- butuh
   koneksi internet ke huggingface.co saat pertama kali dijalankan

Jika persyaratan di atas tidak terpenuhi (misal saat dijalankan di sandbox
tanpa API key/internet), gunakan --dry-run untuk memvalidasi struktur
pipeline tanpa benar-benar memanggil API eksternal.

Usage:
    python evaluation/run_ragas_evaluation.py                # evaluasi penuh
    python evaluation/run_ragas_evaluation.py --dry-run       # validasi pipeline saja
    python evaluation/run_ragas_evaluation.py --category destinasi
"""
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from evaluation.golden_dataset import GOLDEN_DATASET, GoldenSample
from evaluation.ragas_metrics import (
    faithfulness, answer_relevancy, context_precision, context_recall, RagasResult,
)
from config.settings import LLM_MODEL, RAGAS_JUDGE_MODEL


def evaluate_one_sample(sample: GoldenSample, dry_run: bool = False) -> RagasResult:
    """
    Jalankan satu sampel golden dataset melalui chatbot produksi (LLMChain),
    lalu hitung keempat metrik RAGAS berdasarkan jawaban & konteks aktual
    yang dihasilkan sistem -- bukan dari ideal_context yang dikurasi manual.
    """
    if dry_run:
        return RagasResult(
            question=sample.question,
            category=sample.category,
            difficulty=sample.difficulty,
            faithfulness_score=0.0,
            answer_relevancy_score=0.0,
            context_precision_score=0.0,
            context_recall_score=0.0,
            raw_details={"mode": "dry_run", "note": "Tidak ada panggilan API nyata"},
        )

    from rag.retrieval.llm_chain import LLMChain
    from rag.embeddings.embedder import Embedder

    chain = LLMChain()
    answer, retrieved_chunks, tokens_used, response_time = chain.chat(
        sample.question, k=5, use_mmr=True, lambda_mmr=0.5,
    )
    contexts = [c.content for c in retrieved_chunks]

    embedder = Embedder()

    faith_result = faithfulness(sample.question, answer, contexts)
    relevancy_result = answer_relevancy(sample.question, answer, embedder)
    precision_result = context_precision(sample.question, contexts)
    recall_result = context_recall(sample.ground_truth, contexts)

    return RagasResult(
        question=sample.question,
        category=sample.category,
        difficulty=sample.difficulty,
        faithfulness_score=faith_result["score"],
        answer_relevancy_score=relevancy_result["score"],
        context_precision_score=precision_result["score"],
        context_recall_score=recall_result["score"],
        raw_details={
            "actual_answer": answer,
            "retrieved_contexts": contexts,
            "tokens_used": tokens_used,
            "response_time_sec": response_time,
            "faithfulness_detail": faith_result,
            "answer_relevancy_detail": relevancy_result,
            "context_precision_detail": precision_result,
            "context_recall_detail": recall_result,
        },
    )


def aggregate_results(results):
    if not results:
        return {}

    def avg(values):
        return round(sum(values) / len(values), 4) if values else 0.0

    overall = {
        "faithfulness":      avg([r.faithfulness_score for r in results]),
        "answer_relevancy":  avg([r.answer_relevancy_score for r in results]),
        "context_precision": avg([r.context_precision_score for r in results]),
        "context_recall":    avg([r.context_recall_score for r in results]),
        "overall_score":     avg([r.overall_score for r in results]),
    }

    by_category = {}
    categories = sorted(set(r.category for r in results))
    for cat in categories:
        cat_results = [r for r in results if r.category == cat]
        by_category[cat] = {
            "n_samples":         len(cat_results),
            "faithfulness":      avg([r.faithfulness_score for r in cat_results]),
            "answer_relevancy":  avg([r.answer_relevancy_score for r in cat_results]),
            "context_precision": avg([r.context_precision_score for r in cat_results]),
            "context_recall":    avg([r.context_recall_score for r in cat_results]),
            "overall_score":     avg([r.overall_score for r in cat_results]),
        }

    by_difficulty = {}
    difficulties = sorted(set(r.difficulty for r in results))
    for diff in difficulties:
        diff_results = [r for r in results if r.difficulty == diff]
        by_difficulty[diff] = {
            "n_samples":     len(diff_results),
            "overall_score": avg([r.overall_score for r in diff_results]),
        }

    return {
        "overall": overall,
        "by_category": by_category,
        "by_difficulty": by_difficulty,
        "n_total_samples": len(results),
    }


def print_summary(aggregated, judge_model: str = None):
    print("\n" + "=" * 70)
    print("RINGKASAN HASIL EVALUASI RAGAS")
    print("=" * 70)

    o = aggregated["overall"]
    print(f"\nTotal sampel dievaluasi : {aggregated['n_total_samples']}")
    if judge_model:
        print(f"Model Judge (RAGAS)     : {judge_model}")
    print(f"\n{'Metrik':<22} {'Skor':>8}")
    print("-" * 32)
    print(f"{'Faithfulness':<22} {o['faithfulness']:>8.4f}")
    print(f"{'Answer Relevancy':<22} {o['answer_relevancy']:>8.4f}")
    print(f"{'Context Precision':<22} {o['context_precision']:>8.4f}")
    print(f"{'Context Recall':<22} {o['context_recall']:>8.4f}")
    print("-" * 32)
    print(f"{'OVERALL SCORE':<22} {o['overall_score']:>8.4f}")

    print(f"\n{'Per Kategori':<15} {'N':>4} {'Faith':>8} {'Relev':>8} {'Prec':>8} {'Recall':>8} {'Overall':>8}")
    print("-" * 70)
    for cat, scores in aggregated["by_category"].items():
        print(
            f"{cat:<15} {scores['n_samples']:>4} "
            f"{scores['faithfulness']:>8.4f} {scores['answer_relevancy']:>8.4f} "
            f"{scores['context_precision']:>8.4f} {scores['context_recall']:>8.4f} "
            f"{scores['overall_score']:>8.4f}"
        )
    print("=" * 70 + "\n")


def main():
    parser = argparse.ArgumentParser(description="Evaluasi RAGAS untuk Toraja Tourism RAG")
    parser.add_argument("--dry-run", action="store_true",
                        help="Validasi struktur pipeline tanpa panggilan API nyata")
    parser.add_argument("--category", type=str, default=None,
                        help="Filter golden dataset berdasarkan kategori tertentu")
    parser.add_argument("--output", type=str,
                        default="evaluation/ragas_report.json",
                        help="Path file output laporan JSON")
    args = parser.parse_args()

    samples = GOLDEN_DATASET
    if args.category:
        samples = [s for s in samples if s.category == args.category]

    if not samples:
        print(f"Tidak ada sampel untuk kategori '{args.category}'")
        return

    if not args.dry_run:
        print(f"\nKonfigurasi Evaluasi:")
        print(f"  Model Chatbot (di-evaluate) : {LLM_MODEL}")
        print(f"  Model Judge (RAGAS)          : {RAGAS_JUDGE_MODEL}")
        print(f"  Golden dataset               : {len(samples)} sampel")
        print()

    print(f"Mengevaluasi {len(samples)} sampel "
          f"{'(DRY RUN - tanpa panggilan API)' if args.dry_run else '(evaluasi penuh via OpenRouter)'}...")

    results = []
    for i, sample in enumerate(samples, 1):
        print(f"  [{i}/{len(samples)}] {sample.question[:60]}...")
        try:
            result = evaluate_one_sample(sample, dry_run=args.dry_run)
            results.append(result)
        except Exception as e:
            print(f"      ERROR: {e}")
            results.append(RagasResult(
                question=sample.question, category=sample.category,
                difficulty=sample.difficulty,
                faithfulness_score=0.0, answer_relevancy_score=0.0,
                context_precision_score=0.0, context_recall_score=0.0,
                raw_details={"error": str(e)},
            ))

    aggregated = aggregate_results(results)
    print_summary(aggregated, judge_model=None if args.dry_run else RAGAS_JUDGE_MODEL)

    report = {
        "generated_at": datetime.utcnow().isoformat(),
        "dry_run": args.dry_run,
        "model_chatbot": LLM_MODEL,
        "model_judge": RAGAS_JUDGE_MODEL if not args.dry_run else "N/A (dry-run)",
        "aggregated": aggregated,
        "per_sample_results": [r.to_dict() for r in results],
        "detailed_results": [
            {**r.to_dict(), "details": r.raw_details} for r in results
        ],
    }

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"Laporan lengkap disimpan ke: {output_path}")


if __name__ == "__main__":
    main()
