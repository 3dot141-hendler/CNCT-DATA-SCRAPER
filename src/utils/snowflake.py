"""
Gerador de Snowflake IDs de 64 bits thread-safe (Python).

Estrutura do ID de 64-bits:
- 1 bit reservado (sinal, sempre 0)
- 41 bits: Timestamp em milissegundos decorridos desde o custom epoch
- 5 bits: Datacenter ID
- 5 bits: Worker ID
- 12 bits: Contador de sequencia incremental
"""

import time
import threading


class SnowflakeGenerator:
    """
    Classe responsavel por gerar inteiros unicos de 64 bits no padrao Snowflake.
    Garante unicidade em ambientes concorrentes atraves de threading.Lock.
    """

    def __init__(self, datacenter_id: int = 1, worker_id: int = 1, epoch: int = 1704067200000):
        # 2024-01-01T00:00:00Z em milissegundos como epoch customizado
        self.epoch = epoch
        self.datacenter_id = datacenter_id & 0x1F  # 5 bits (0-31)
        self.worker_id = worker_id & 0x1F          # 5 bits (0-31)
        
        self.sequence = 0
        self.last_timestamp = -1
        self.lock = threading.Lock()

    def _current_timestamp(self) -> int:
        """
        Retorna o timestamp atual em milissegundos.
        """
        return int(time.time() * 1000)

    def generate_id(self) -> int:
        """
        Gera o proximo Snowflake ID de 64-bits com protecao de lock.
        """
        with self.lock:
            timestamp = self._current_timestamp()

            if timestamp < self.last_timestamp:
                # Caso ocorra recuo de relogio, ajusta para o ultimo timestamp conhecido
                timestamp = self.last_timestamp

            if timestamp == self.last_timestamp:
                self.sequence = (self.sequence + 1) & 0xFFF  # 12 bits (0-4095)
                if self.sequence == 0:
                    # Estouro de sequencia na mesma milissegundo: aguarda a proxima
                    while timestamp <= self.last_timestamp:
                        timestamp = self._current_timestamp()
            else:
                self.sequence = 0

            self.last_timestamp = timestamp

            # Composicao bit a bit
            snowflake_id = (
                ((timestamp - self.epoch) << 22) |
                (self.datacenter_id << 17) |
                (self.worker_id << 12) |
                self.sequence
            )
            return snowflake_id


# Instancia singleton para uso compartilhado
snowflake_default = SnowflakeGenerator(datacenter_id=1, worker_id=1)

def get_snowflake_id() -> int:
    """
    Funcao utilitaria global para obter um novo Snowflake ID.
    """
    return snowflake_default.generate_id()
