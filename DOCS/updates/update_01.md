# Histórico de Atualizações - CNCT Scraper (Versão 2.2.4)
## Documentação das Atualizações: Integração com Tabulator.js (Dark Theme) no Frontend

> **Projeto**: `CNCT_SCRAPER` (Microserviço do Esteio Conecta)  
> **Data da Atualização**: 06/08/2026  
> **Versão**: 2.2.4  

---

## 📋 Resumo Executivo das Implementações (v2.2.4)

Para resolver a limitação de espaço dentro de iFrames e oferecer uma experiência visual de classe empresarial, a tabela de amostragem do Frontend foi migrada para a biblioteca **Tabulator.js (Midnight/Dark Theme)**:

1. **Colunas Redimensionáveis pelo Usuário (`resizableColumnFit: true`)**:
   - Cada borda de coluna pode ser arrastada com o ponteiro do mouse para ajustar a largura desejada diretamente no iFrame.
2. **Filtros Rápidos nos Cabeçalhos (`headerFilter: "input"`)**:
   - Campos de busca dinâmica por texto adicionados nos cabeçalhos (`Snowflake ID`, `Instituição`, `Município`), permitindo filtrar milhares de registros instantaneamente.
3. **Ajuste Automático para iFrames (`layout: "fitDataFill"`)**:
   - O layout expande ou contrai de acordo com o viewport do iFrame do Esteio Conecta sem deformar os textos ou criar lacunas indesejadas.
4. **Tooltips Automáticos e Paginação Nativa**:
   - Dicas de texto completo ao passar o mouse em células cortadas e controles de paginação nativos integrados ao rodapé da tabela.

---

## 🛠️ Arquivos Modificados nesta Versão

- **`frontend/migracao.html`** `[ATUALIZADO]`:
  - Adicionados os links de CSS e JS do **Tabulator.js 5.5.2** (Midnight Dark Theme).
  - Substituída a tabela estática pelo container inteligente `<div id="tabulator-table"></div>`.
- **`frontend/js/migracao.js`** `[ATUALIZADO]`:
  - Instanciação do `Tabulator("#tabulator-table")` com formatação dinâmica, busca nos cabeçalhos e ordenação nativa.

---

## 📌 Diretrizes de Portas e Serviços

- 🏛️ Esteio Conecta (Portal Principal): `http://127.0.0.1:8080` (Porta 8080)
- 🤖 CNCT Scraper (Microserviço): `http://127.0.0.1:8000` (Porta 8000)
- 🚚 Migração de Endereços: `http://127.0.0.1:8000/migracao`
