# Relatório do Incidente e Regra de Prevenção: Instanciação de Cursors MySQL

## 1. Descrição do Incidente
Durante o processo de sincronização e gravação no banco de dados MySQL da VPS, o sistema informava o término da requisição HTTP, mas nenhuma alteração era efetivamente gravada nas tabelas. O banco permanecia inalterado devido a um `conn.rollback()` disparado silenciosamente.

---

## 2. Causa Raiz Técnica
- **Instanciação Incompleta do Cursor**: Na rota `/api/migracao/executar` em `src/backend/routes/migracao_enderecos.py`, o cursor do banco foi instanciado utilizando `cursor = conn.cursor()` em vez de `cursor = conn.cursor(dictionary=True)`.
- **Incompatibilidade de Tipos**: O MySQL Connector retornou tuplas puras do Python em vez de dicionários.
- **Falha em Tempo de Execução**: Quando a função `compare_datasets_c` em `src/c_aggregator/bridge.py` tentou acessar os campos utilizando `.get()`, o Python lançou a exceção `AttributeError: 'tuple' object has no attribute 'get'`.
- **Desfazimento da Transação**: O bloco `try...except` capturou a exceção e executou `conn.rollback()`, desfazendo qualquer inserção ou atualização antes que o `conn.commit()` pudesse ser chamado.

---

## 3. Ação Corretiva Aplicada
No arquivo `src/backend/routes/migracao_enderecos.py`, a criação do cursor foi corrigida para:

```python
# Padrão Obrigatório
cursor = conn.cursor(dictionary=True)
```

---

## 4. Regra Estrita de Prevenção (Diretriz do Projeto)
- **Obrigatoriedade do `dictionary=True`**: Toda e qualquer função ou rota que instanciar um cursor do MySQL Connector neste projeto DEVE obrigatoriamente utilizar `conn.cursor(dictionary=True)`.
- **Proibição de Cursors Padrão**: É proibido o uso de `conn.cursor()` sem o argumento `dictionary=True`, pois inviabiliza o consumo dos dados por dicionários no Python e na engine C.
- **Validação em Tratamento de Erros**: Blocos `except` em rotas de gravação devem registrar o erro com log completo antes de invocar `conn.rollback()`.
