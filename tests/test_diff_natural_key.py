"""
Testes unitários TDD para a nova regra de negócio de comparação por Chave Natural
(nome_instituicao + municipio) e gestão de relacionamentos de cursos ofertados.
"""

import os
import sys
import pytest

# Adiciona a raiz do projeto ao sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.c_aggregator.bridge import (
    normalize_natural_key,
    compare_datasets_c,
    generate_text_diagnosis_c
)


def test_normalize_natural_key_acentos_e_case():
    """
    Verifica se a normalização remove acentos, espaços extras e ajusta para minúsculas.
    """
    key1 = normalize_natural_key("Escola Técnica São José", "Esteio")
    key2 = normalize_natural_key("escola tecnica sao jose  ", "esteio")
    key3 = normalize_natural_key("ESCOLA TÉCNICA SÃO JOSÉ", "ESTEIO")

    assert key1 == "escolatecnicasaojose_esteio"
    assert key1 == key2 == key3


def test_diff_multi_tier_matching_com_prefixos_e_enderecos():
    """
    Testa a resiliência do matching contra nomes com variações de prefixos (E.E. vs EE, ETEC)
    e município embutido no endereço.
    """
    db_state = [
        {"id": 3439273967, "nome_instituicao": "E.E. PROFESSOR TOMAS AQUINO PEREIRA", "endereco": "Rua Ferreira e Souza, 102, Barão do Monte Alto - MG", "ativo": 1},
        {"id": 3439274186, "nome_instituicao": "ETEC PEDRO FERREIRA ALVES", "endereco": "Rua Ariovaldo Silveira Franco, 237, Mogi Mirim - SP", "ativo": 1}
    ]
    csv_incoming = [
        {"nome_instituicao": "EE Professor Tomas Aquino Pereira", "municipio": "Barão do Monte Alt"},
        {"nome_instituicao": "Etec Pedro Ferreira Alves", "municipio": "Mogi Mirim"}
    ]

    diff = compare_datasets_c(db_state, csv_incoming, is_parcial=True)
    # Ambas devem ser reconhecidas e herdar o ID do banco de dados (0 novas)
    assert len(diff['novos']) == 0
    assert len(diff['mantidos']) == 2
    assert diff['mantidos'][0]['id'] == 3439273967
    assert diff['mantidos'][1]['id'] == 3439274186


def test_diff_chave_natural_preserva_ids_existentes():
    """
    Garante que um registro do CSV com a mesma chave natural Herda o ID do banco de dados,
    evitando inativações indevidas e inserção de duplicatas.
    """
    db_state = [
        {
            "id": 9988776655,
            "nome_instituicao": "Escola Técnica Esteio",
            "municipio": "Esteio",
            "uf": "RS",
            "ativo": 1,
            "cursos": ["Técnico em Informática"]
        }
    ]

    # CSV importado do scraper (sem ID ou com ID temporário)
    csv_incoming = [
        {
            "nome_instituicao": "ESCOLA TÉCNICA ESTEIO",
            "municipio": "Esteio",
            "uf": "RS",
            "endereco": "Rua das Flores, 100, Esteio - RS",
            "cursos": ["Técnico em Informática", "Técnico em Enfermagem"] # Novo curso ofertado
        }
    ]

    diff = compare_datasets_c(db_state, csv_incoming)

    # Não deve criar nova instituição
    assert len(diff['novos']) == 0

    # Não deve inativar a instituição existente
    assert len(diff['inativados']) == 0

    # Deve identificar a instituição existente mantida/atualizada e preservar seu ID
    assert len(diff['mantidos']) == 1 or len(diff['alterados']) == 1
    item_processado = (diff['mantidos'] or diff['alterados'])[0]
    assert item_processado['id'] == 9988776655

    # Verifica diff de cursos ofertados
    assert diff['estatisticas_cursos']['novos_cursos_qtd'] == 1 # Enfermagem
    assert diff['estatisticas_cursos']['cursos_mantidos_qtd'] == 1 # Informática


def test_diff_chave_natural_identifica_nova_instituicao():
    """
    Garante que uma instituição realmente nova no CSV seja classificada como Nova.
    """
    db_state = [
        {"id": 101, "nome_instituicao": "Inst A", "municipio": "Porto Alegre", "ativo": 1}
    ]
    csv_incoming = [
        {"nome_instituicao": "Inst B Inédita", "municipio": "Canoas"}
    ]

    diff = compare_datasets_c(db_state, csv_incoming)
    assert len(diff['novos']) == 1
    assert diff['novos'][0]['nome_instituicao'] == "Inst B Inédita"


def test_trava_inativacao_raspagem_parcial():
    """
    Garante que em pesquisas/raspagens parciais (ex: 10 registros importados contra 100 no banco),
    a trava de segurança ZERE a lista de inativados, impedindo inativações indevidas.
    """
    db_state = [{"id": i, "nome_instituicao": f"Inst {i}", "municipio": "Esteio", "ativo": 1} for i in range(100)]
    csv_incoming = [{"nome_instituicao": f"Inst {i}", "municipio": "Esteio"} for i in range(10)]

    diff = compare_datasets_c(db_state, csv_incoming, is_parcial=True)
    assert diff['is_parcial'] is True
    assert len(diff['inativados']) == 0 # Trava ativada!

    relatorio = generate_text_diagnosis_c(diff)
    assert "PESQUISA / RASPAGEM PARCIAL DETECTADA" in relatorio
    assert "TRAVA DE SEGURANÇA ATIVADA: NENHUM REGISTRO SERÁ INATIVADO" in relatorio


def test_format_novas_instituicoes_table():
    """
    Testa a geração da tabela ASCII monospaçada para exibição de instituições novas.
    """
    from src.c_aggregator.bridge import format_novas_instituicoes_table

    novos = [
        {"snowflake_id": 123456, "nome_instituicao": "Escola Nova A", "municipio": "Esteio", "endereco": "Rua 1, 10"},
        {"snowflake_id": 123457, "nome_instituicao": "Escola Nova B", "municipio": "Canoas", "endereco": "Av 2, 20"}
    ]
    tabela = format_novas_instituicoes_table(novos)
    assert "CÓDIGO" in tabela
    assert "NOME DA INSTITUIÇÃO" in tabela
    assert "Escola Nova A" in tabela
    assert "Escola Nova B" in tabela


def test_diagnostico_texto_contem_estatisticas_de_cursos():
    """
    Verifica se o relatório descritivo inclui a análise de ofertas de cursos.
    """
    stats = {
        "total_csv": 100,
        "total_db": 100,
        "novos_qtd": 2,
        "alterados_qtd": 5,
        "inativados_qtd": 0,
        "mantidos_qtd": 93,
        "estatisticas_cursos": {
            "novos_cursos_qtd": 15,
            "cursos_descontinuados_qtd": 3,
            "cursos_mantidos_qtd": 350
        }
    }
    relatorio = generate_text_diagnosis_c(stats)
    assert "DIAGNÓSTICO ANALÍTICO DE SINCRONIZAÇÃO" in relatorio
    assert "Novas Ofertas de Cursos (Novos Vínculos): 15" in relatorio
    assert "Ofertas Descontinuadas / Encerradas: 3" in relatorio
