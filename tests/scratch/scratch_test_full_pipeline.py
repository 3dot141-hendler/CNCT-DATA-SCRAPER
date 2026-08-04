import json
from src.scraper.pipeline import ScraperPipeline

def test_pipeline():
    print("=" * 80)
    print("EXECUTANDO TESTE DE INTEGRACAO DO PIPELINE CNCT SCRAPER (2 CURSOS)")
    print("=" * 80 + "\n")

    pipeline = ScraperPipeline()
    result = pipeline.run(max_courses=2)

    print("\nRESULTADO DO PIPELINE:")
    print(json.dumps(result, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    test_pipeline()
