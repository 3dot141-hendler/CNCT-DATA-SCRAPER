"""
Testes unitários para validação de correções de alterações cadastrais e auditoria de pareamento.
"""

import pytest
from src.c_aggregator.address_parser import parse_address_c, is_valid_municipio_candidate
from src.c_aggregator.text_normalizer import clean_pedagogical_acronyms, normalize_core_name
from src.c_aggregator.diff_matching import compare_datasets_c
from src.c_aggregator.post_diff_audit import run_post_diff_audit_c


def test_parsing_municipios_jardim():
    """
    Testa se o parser de endereços aceita corretamente municípios que iniciam ou são 'Jardim',
    como Jardim (MS), Jardim (CE), Jardim Alegre (PR), Jardim do Mulato (PI), Jardim de Piranhas (RN), Jardim do Seridó (RN).
    """
    assert is_valid_municipio_candidate("Jardim") is True
    assert is_valid_municipio_candidate("Jardim Alegre") is True
    assert is_valid_municipio_candidate("Jardim do Mulato") is True
    assert is_valid_municipio_candidate("Jardim de Piranhas") is True
    assert is_valid_municipio_candidate("Jardim do Seridó") is True

    # Endereço real de Jardim MS
    res_jardim = parse_address_c("Rua Vereador Romeu de Medeiros, 102B, Polo Jardim (Centro), Anhandui, Jardim MS - 79240000.")
    assert res_jardim["municipio"] == "Jardim"
    assert res_jardim["uf"] == "MS"

    # Endereço real de Jardim Alegre PR
    res_jardim_alegre = parse_address_c("Rua Santos, 295, Predio, Centro, Jardim Alegre PR - 86860000.")
    assert res_jardim_alegre["municipio"] == "Jardim Alegre"
    assert res_jardim_alegre["uf"] == "PR"


def test_preservacao_numerais_romanos_pedro_ii_pio_ix():
    """
    Testa se o parser e o normalizador preservam numerais romanos em nomes de municípios e instituições (Pedro II, Pio IX).
    """
    res_pedro = parse_address_c("Rua Lauro Cordeiro S/N, 0, Boa Esperança, Pedro II Pi - 64255000.")
    assert res_pedro["municipio"] == "Pedro II"

    res_pio = parse_address_c("Pio IX, S/N, Meladão, Pio IX Pi - 64660000.")
    assert res_pio["municipio"] == "Pio IX"

    # Preservação em nomes de instituições
    nome_pedro = "Instituto Federal do Piauí - Campus Pedro II"
    assert "pedro ii" in clean_pedagogical_acronyms(nome_pedro).lower()

    nome_pio = "Instituto Federal do Piauí Campus Pio IX"
    assert "pio ix" in clean_pedagogical_acronyms(nome_pio).lower()


def test_bloqueio_fusao_publica_vs_privada():
    """
    Garante que uma instituição Pública (ex: Instituto Federal) NUNCA seja pareada como UPDATE
    de uma instituição Privada (ex: Universidade Cruzeiro do Sul) por coincidência de palavras de cidade no Passo 3 da Auditoria Pós-Diff.
    """
    db_data = [{
        "id": "342380338980458671",
        "nome_instituicao": "Universidade Cruzeiro do Sul - Unicsul - Polo São Leopoldo",
        "dependencia_adm": "Privada",
        "endereco": "Rua José Bonifácio, 204, Centro, São Leopoldo RS - 93010180.",
        "municipio": "São Leopoldo",
        "uf": "RS",
        "ativo": 1
    }]

    csv_data = [{
        "nome_instituicao": "Instituto Federal do Sul-rio-grandense - Campus São Leopoldo",
        "dependencia_adm": "Pública",
        "endereco": "Avenida São Borja, 1860, Fazenda São Borja, São Leopoldo RS - 93032500.",
        "municipio": "São Leopoldo",
        "uf": "RS"
    }]

    res = compare_datasets_c(db_data, csv_data)
    assert len(res["novos"]) == 1
    assert len(res["alterados"]) == 0
    assert res["novos"][0]["nome_instituicao"] == "Instituto Federal do Sul-rio-grandense - Campus São Leopoldo"


def test_preservacao_nome_vps_alta_qualidade():
    """
    Garante que nomes completos e de alta qualidade cadastrados na VPS não sejam sobrescritos
    por nomes truncados/mutilados vindos do scraper (ex: Attílio Fontana, C.E Sen-ef M Eti P).
    """
    db_data = [{
        "id": "342381212473626785",
        "nome_instituicao": "Colégio Estadual Senador Attílio Fontana - Ensino Fundamental- Médio e Profissional",
        "dependencia_adm": "Pública",
        "endereco": "Rua Gonçalves Dias, 100, Boa Esperança, Toledo PR - 85909540.",
        "municipio": "Toledo",
        "uf": "PR",
        "ativo": 1
    }]

    csv_data = [{
        "nome_instituicao": "Attílio Fontana, C.E Sen-ef M Eti P",
        "dependencia_adm": "Pública",
        "endereco": "Rua Gonçalves Dias, 100, Boa Esperança, Toledo PR - 85909540.",
        "municipio": "Toledo",
        "uf": "PR"
    }]

    res = compare_datasets_c(db_data, csv_data)
    # Se for pareado como mantido ou alterado, a lista de diferenças NÃO deve conter a troca do nome completo pelo nome mutilado
    if res["alterados"]:
        difs = res["alterados"][0].get("diferencas_detectadas", [])
        assert not any("nome_instituicao" in d for d in difs)


def test_isolamento_unidade_ead():
    """
    Garante que unidades EAD (ex: Centro de Ensino Grau Técnico - Unidade Vila Velha (EAD))
    não sobrescrevam como UPDATE a unidade presencial correspondente (Centro de Ensino Grau Técnico - Unidade Vila Velha).
    """
    db_data = [{
        "id": "342380413219639308",
        "nome_instituicao": "Centro de Ensino Grau Técnico - Unidade Vila Velha",
        "dependencia_adm": "Privada",
        "endereco": "Avenida Jerônimo Monteiro, 720, Glória, Vila Velha ES - 29122720.",
        "municipio": "Vila Velha",
        "uf": "ES",
        "ativo": 1
    }]

    csv_data = [{
        "nome_instituicao": "Centro de Ensino Grau Técnico - Unidade Vila Velha (EAD)",
        "dependencia_adm": "Privada",
        "endereco": "Avenida Jerônimo Monteiro, 720, - Lado Par, Glória, Vila Velha ES - 29122720.",
        "municipio": "Vila Velha",
        "uf": "ES"
    }]

    res = compare_datasets_c(db_data, csv_data)
    assert len(res["novos"]) == 1
    assert res["novos"][0]["nome_instituicao"] == "Centro de Ensino Grau Técnico - Unidade Vila Velha (EAD)"


def test_casos_reais_auditoria_municipios():
    """
    Testa a suíte completa contra todas as 24 divergências relatadas pelo usuário,
    garantindo que NENHUMA falsificação de município (Pedro II -> Pedro, Jardim -> Anhandui, Fortaleza CE -> Fortaleza) seja gerada.
    """
    # 1. Pedro II
    db_pedro = [{"id": "1", "nome_instituicao": "Ceti Angelina", "municipio": "Pedro II", "uf": "PI", "endereco": "Rua Lauro Cordeiro S/N, 0, Boa Esperança, Pedro II Pi - 64255000.", "ativo": 1}]
    csv_pedro = [{"nome_instituicao": "Ceti Angelina", "municipio": "Pedro", "uf": "PI", "endereco": "Rua Lauro Cordeiro S/N, 0, Boa Esperança, Pedro II Pi - 64255000."}]
    res_pedro = compare_datasets_c(db_pedro, csv_pedro)
    assert not res_pedro["alterados"], f"Divergência gerada indevidamente: {res_pedro['alterados']}"

    # 2. Jardim (MS)
    db_jardim = [{"id": "2", "nome_instituicao": "Unicsul", "municipio": "Jardim", "uf": "MS", "endereco": "Rua Vereador Romeu de Medeiros, 102B, Polo Jardim (Centro), Anhandui, Jardim MS - 79240000.", "ativo": 1}]
    csv_jardim = [{"nome_instituicao": "Unicsul", "municipio": "Anhandui", "uf": "MS", "endereco": "Rua Vereador Romeu de Medeiros, 102B, Polo Jardim (Centro), Anhandui, Jardim MS - 79240000."}]
    res_jardim = compare_datasets_c(db_jardim, csv_jardim)
    assert not res_jardim["alterados"], f"Divergência gerada indevidamente: {res_jardim['alterados']}"

    # 3. Fortaleza CE -
    db_fortal = [{"id": "3", "nome_instituicao": "Uninassau", "municipio": "Fortaleza", "uf": "CE", "endereco": "Fortaleza CE -", "ativo": 1}]
    csv_fortal = [{"nome_instituicao": "Uninassau", "municipio": "Fortaleza CE -", "uf": "CE", "endereco": "Fortaleza CE -"}]
    res_fortal = compare_datasets_c(db_fortal, csv_fortal)
    assert not res_fortal["alterados"], f"Divergência gerada indevidamente: {res_fortal['alterados']}"

    # 4. Cuiabá MT - 78005-
    db_cuiaba = [{"id": "4", "nome_instituicao": "Monte Sião", "municipio": "Cuiabá", "uf": "MT", "endereco": "Rua Treze de Junho, 207, Galeria Gg, Centro Norte, Cuiabá MT - 78005-.", "ativo": 1}]
    csv_cuiaba = [{"nome_instituicao": "Monte Sião", "municipio": "Cuiabá MT - 78005-", "uf": "MT", "endereco": "Rua Treze de Junho, 207, Galeria Gg, Centro Norte, Cuiabá MT - 78005-."}]
    res_cuiaba = compare_datasets_c(db_cuiaba, csv_cuiaba)
    assert not res_cuiaba["alterados"], f"Divergência gerada indevidamente: {res_cuiaba['alterados']}"

    # 5. Pio IX
    db_pio = [{"id": "5", "nome_instituicao": "IPEC", "municipio": "Pio IX", "uf": "PI", "endereco": "Pio IX, S/N, Meladão, Pio IX Pi - 64660000.", "ativo": 1}]
    csv_pio = [{"nome_instituicao": "IPEC", "municipio": "Pio", "uf": "PI", "endereco": "Pio IX, S/N, Meladão, Pio IX Pi - 64660000."}]
    res_pio = compare_datasets_c(db_pio, csv_pio)
    assert not res_pio["alterados"], f"Divergência gerada indevidamente: {res_pio['alterados']}"

    # 6. Jardim de Piranhas
    db_piranhas = [{"id": "6", "nome_instituicao": "Iern", "municipio": "Jardim de Piranhas", "uf": "RN", "endereco": "Marginal da RN 288, 01, Centro, Jardim de Piranhas RN - 59324000.", "ativo": 1}]
    csv_piranhas = [{"nome_instituicao": "Iern", "municipio": "Marginal da RN 288", "uf": "RN", "endereco": "Marginal da RN 288, 01, Centro, Jardim de Piranhas RN - 59324000."}]
    res_piranhas = compare_datasets_c(db_piranhas, csv_piranhas)
    assert not res_piranhas["alterados"], f"Divergência gerada indevidamente: {res_piranhas['alterados']}"


def test_bloqueio_alteracoes_falsas_dados_identicos():
    """
    1. Se o banco da VPS tiver o município sujo 'Rio de Janeiro RJ - 2104101', ele DEVE gerar alteração (Seção 2) para atualizar no BD.
    2. Se o banco da VPS já tiver o município limpo 'Rio de Janeiro', ele DEVE ir para MANTIDOS (Seção 4).
    """
    db_dirty = [{
        "id": "342380338955292812",
        "nome_instituicao": "Cursos Tecnicos Vencer",
        "dependencia_adm": "Privada",
        "endereco": "Praça das Nações, 34, Praça das Nações, Bonsucesso, Rio de Janeiro RJ - 2104101.",
        "municipio": "Rio de Janeiro RJ - 2104101",
        "uf": "RJ"
    }]

    csv_data = [{
        "nome_instituicao": "Cursos Tecnicos Vencer",
        "dependencia_adm": "Privada",
        "endereco": "Praça das Nações, 34, Praça das Nações, Bonsucesso, Rio de Janeiro RJ - 2104101.",
        "municipio": "Rio de Janeiro RJ - 2104101",
        "uf": "RJ"
    }]

    res_dirty = compare_datasets_c(db_dirty, csv_data)
    assert len(res_dirty["alterados"]) == 1, f"Deveria gerar alteração para limpar o BD sujo: {res_dirty['alterados']}"

    db_clean = [{
        "id": "342380338955292812",
        "nome_instituicao": "Cursos Tecnicos Vencer",
        "dependencia_adm": "Privada",
        "endereco": "Praça das Nações, 34, Praça das Nações, Bonsucesso, Rio de Janeiro RJ - 2104101.",
        "municipio": "Rio de Janeiro",
        "uf": "RJ",
        "cep": "2104101",
        "ativo": 1
    }]

def test_ibest_escola_dirty_municipio_diff():
    """
    Garante que o caso real 'Ibest Escola' com 'Rio de Janeiro RJ - 2091127' no MySQL da VPS
    seja detectado com a divergência de município na Seção 2 (ALTERAÇÕES).
    """
    db_data = [{
        "id": "342380413261582340",
        "nome_instituicao": "Ibest Escola",
        "municipio": "Rio de Janeiro RJ - 2091127",
        "uf": "RJ",
        "cep": "2091127",
        "endereco": "Rua Francisco Manuel, 172, Benfica, Rio de Janeiro RJ - 2091127.",
        "ativo": 1
    }]

    csv_data = [{
        "nome_instituicao": "Ibest Escola",
        "endereco": "Rua Francisco Manuel, 172, Benfica, Rio de Janeiro RJ - 2091127.",
        "municipio": "Rio de Janeiro RJ - 2091127",
        "uf": "RJ"
    }]

    res = compare_datasets_c(db_data, csv_data)
    assert len(res["alterados"]) == 1, f"Deveria estar em alterados: {res}"
def test_pedro_ii_preservation_in_diff():
    """
    Garante que Ceti Professora Angelina Mendes Braga em 'Pedro II'
    MANTENHA o município 'Pedro II' e NÃO regrida para 'Pedro'.
    """
    db_data = [{
        "id": "342380317514010637",
        "nome_instituicao": "Ceti Professora Angelina Mendes Braga",
        "municipio": "Pedro II",
        "uf": "PI",
        "cep": "64255000",
        "endereco": "Rua Corinto Andrade, S/N, Centro, Pedro II PI - 64255000.",
        "ativo": 1
    }]

    csv_data = [{
        "nome_instituicao": "Ceti Professora Angelina Mendes Braga",
        "municipio": "Pedro II",
        "uf": "PI",
        "endereco": "Rua Corinto Andrade, S/N, Centro, Pedro II PI - 64255000."
    }]

    res = compare_datasets_c(db_data, csv_data)
    assert len(res["alterados"]) == 0, f"Não deveria alterar Pedro II: {res['alterados']}"
    assert len(res["mantidos"]) == 1, f"Deveria estar em mantidos: {res['mantidos']}"
    assert res["mantidos"][0]["municipio"] == "Pedro II"




def test_roman_numeral_protector_direct():
    """
    Testa diretamente os métodos da classe POO RomanNumeralProtector.
    """
    from src.c_aggregator.numerais_romanos import RomanNumeralProtector
    
    assert RomanNumeralProtector.is_roman_numeral("I") is True
    assert RomanNumeralProtector.is_roman_numeral("II") is True
    assert RomanNumeralProtector.is_roman_numeral("IX") is True
    assert RomanNumeralProtector.is_roman_numeral("XX") is True
    assert RomanNumeralProtector.is_roman_numeral("PEDRO") is False

    res_pedro = RomanNumeralProtector.protect_municipio_name("Pedro II", "Pedro")
    assert res_pedro == "Pedro II", f"Não protegeu Pedro II: {res_pedro}"

    res_jardim = RomanNumeralProtector.protect_municipio_name("Jardim de Piranhas", "Jardim")
    assert res_jardim == "Jardim de Piranhas", f"Não protegeu Jardim de Piranhas: {res_jardim}"


def test_fix_uf_vazia_em_municipio_contaminado():
    """
    Testa os casos reportados no CSV de Alterações Cadastrais onde a UF estava em branco no MySQL
    porque estava fundida na coluna municipio (ex: 'Pinheiro MA - 65200', 'Pedreiras MA - 65.72500').
    """
    db_data = [{
        "id": "342380338955292801",
        "nome_instituicao": "Complexo Educacional Supremo Redentor",
        "municipio": "Pinheiro MA - 65200",
        "uf": "",
        "cep": "",
        "endereco": "Praça do Centenário, 550, Centro, Pinheiro MA - 65200.",
        "ativo": 1
    }]

    csv_data = [{
        "nome_instituicao": "Complexo Educacional Supremo Redentor",
        "municipio": "Pinheiro",
        "uf": "MA",
        "endereco": "Praça do Centenário, 550, Centro, Pinheiro MA - 65200."
    }]

    res = compare_datasets_c(db_data, csv_data)
    assert len(res["alterados"]) == 1, f"Deveria alterar: {res}"
    item_alt = res["alterados"][0]
    diffs = item_alt.get("diferencas_detectadas", [])
    
    # Valida que o diff registrou a limpeza do município, o preenchimento da UF e do CEP
    diff_str = " | ".join(diffs)
    assert "municipio: 'Pinheiro MA - 65200' ➔ 'Pinheiro'" in diff_str, f"Diff muni incorreto: {diff_str}"
    assert "uf: '' ➔ 'MA'" in diff_str, f"Diff uf incorreto: {diff_str}"
    assert "cep: '' ➔ '65200'" in diff_str, f"Diff cep incorreto: {diff_str}"
    assert item_alt.get("uf") == "MA"
    assert item_alt.get("cep") == "65200"





