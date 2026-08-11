# Diretrizes Obrigatórias de Contexto e Comportamento dos Agentes de IA

Este documento estabelece as regras estritas e inegociáveis de comportamento, análise e resposta que todos os agentes de IA devem obedecer neste projeto.

---

## 1. Auditoria Completa do Código (Proibido Fazer Suposições)
- **Regra de Análise Abrangente**: Antes de emitir qualquer relatório, resposta, diagnóstico, parecer técnico ou plano de implementação, o agente DEVE inspecionar e rastrear 100% do código existente no escopo da tarefa (Front-end, Backend, Banco de Dados, Bibliotecas e Scripts).
- **Zero Suposições**: É expressamente proibido assumir o comportamento de qualquer função, rota, payload ou componente sem ter lido e verificado as linhas exatas de código envolvidas.
- **Rastreamento de Ponta a Ponta**: Quando uma tarefa envolver a execução de um fluxo, o agente deve rastrear a cadeia completa de chamadas (do clique do usuário na UI até a query final no banco de dados).

---

## 2. Proibição Absoluta do Uso de Emojis
- **Zero Emojis**: O uso de emojis em qualquer resposta, relatório, log de auditoria, tabela ASCII, interface web ou documentação gerada é **ESTRITAMENTE PROIBIDO**.
- **Comunicação Direta e Profissional**: Toda a saída de texto deve ser limpa, técnica, objetiva e formatada exclusivamente em Markdown limpo.

---

## 3. Preservação de Dados e Regras de Negócio
- **Integridade da Base**: Nenhuma alteração pode deletar registros fisicamente (`DELETE`) ou sobrescrever dados sem validação prévia de Diff.
- **Sincronização Seletiva**:
  - Registros novos $\rightarrow$ `INSERT` (com Snowflake ID de 64-bit).
  - Registros alterados/reativados $\rightarrow$ `UPDATE WHERE id = sf_id` (preservando o ID original).
  - Registros descontinuados $\rightarrow$ Soft Delete (`UPDATE SET ativo = 0`).
  - Registros mantidos $\rightarrow$ Ignorados (0 queries executadas).

---

## 4. Padrão Obrigatório de Cursors MySQL
- **Uso Estrito de Dicionários**: Todo cursor MySQL instanciado no backend deve obrigatoriamente utilizar `conn.cursor(dictionary=True)` para evitar incompatibilidade de tipos de dados com o Python e a engine em C.
