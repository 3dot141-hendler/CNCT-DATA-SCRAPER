"""
Testes unitarios para a classe SnowflakeGenerator.
Verifica unicidade, concorrencia thread-safe e ordenacao monotonica dos IDs de 64 bits.
"""

import pytest
import concurrent.futures
from src.utils.snowflake import SnowflakeGenerator


def test_snowflake_uniqueness():
    generator = SnowflakeGenerator(datacenter_id=1, worker_id=1)
    generated_ids = set()

    for _ in range(10000):
        snowflake_id = generator.generate_id()
        assert snowflake_id not in generated_ids, "ID duplicado detectado"
        assert isinstance(snowflake_id, int), "Snowflake ID deve ser um inteiro"
        assert 0 <= snowflake_id < (1 << 63), "Snowflake ID deve ser um inteiro de 64 bits positivo"
        generated_ids.add(snowflake_id)


def test_snowflake_multithreading_concurrency():
    generator = SnowflakeGenerator(datacenter_id=2, worker_id=3)
    generated_ids = set()
    total_threads = 20
    ids_per_thread = 500

    def worker_task():
        return [generator.generate_id() for _ in range(ids_per_thread)]

    with concurrent.futures.ThreadPoolExecutor(max_workers=total_threads) as executor:
        futures = [executor.submit(worker_task) for _ in range(total_threads)]
        for future in concurrent.futures.as_completed(futures):
            results = future.result()
            for sf_id in results:
                assert sf_id not in generated_ids, f"Colisao detectada em ambiente multithread: {sf_id}"
                generated_ids.add(sf_id)

    assert len(generated_ids) == total_threads * ids_per_thread


def test_snowflake_monotonic_ordering():
    generator = SnowflakeGenerator()
    id1 = generator.generate_id()
    id2 = generator.generate_id()
    assert id2 > id1, "IDs gerados sequencialmente devem ser monotonicamente crescentes"
