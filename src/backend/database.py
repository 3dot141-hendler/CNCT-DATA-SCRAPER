"""
Módulo de conexão ao MySQL (VPS via Túnel SSH / Local) e inicialização da tabela de auditoria LOGS_AUDITORIA_MIGRACAO.
"""

import os
import mysql.connector
from mysql.connector import Error
from src.backend.config import DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME


def get_db_connection():
    """
    Estabelece e retorna a conexão MySQL com o banco de dados.
    """
    try:
        conn = mysql.connector.connect(
            host=DB_HOST,
            port=int(DB_PORT),
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            connect_timeout=10
        )
        return conn
    except Error as e:
        print(f"[DATABASE ERROR] Falha ao conectar ao MySQL ({DB_HOST}:{DB_PORT}): {e}")
        return None


def init_audit_table():
    """
    Garante a criação da tabela LOGS_AUDITORIA_MIGRACAO se não existir.
    """
    conn = get_db_connection()
    if not conn:
        print("[DATABASE WARN] Não foi possível conectar ao banco para inicializar tabela de auditoria.")
        return False

    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS LOGS_AUDITORIA_MIGRACAO (
                id BIGINT PRIMARY KEY,
                usuario_id BIGINT NOT NULL,
                usuario_email VARCHAR(255) NOT NULL,
                ip_origem VARCHAR(45) NOT NULL,
                data_hora DATETIME NOT NULL,
                total_inseridos INT DEFAULT 0,
                total_atualizados INT DEFAULT 0,
                total_inativados INT DEFAULT 0,
                diagnostico_resumo TEXT,
                criado_em DATETIME DEFAULT CURRENT_TIMESTAMP
            );
        """)
        conn.commit()
        cursor.close()
        conn.close()
        print("[DATABASE OK] Tabela LOGS_AUDITORIA_MIGRACAO verificada/criada com sucesso.")
        return True
    except Exception as e:
        print(f"[DATABASE ERROR] Erro ao criar tabela de auditoria: {e}")
        if conn and conn.is_connected():
            conn.close()
        return False
