#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <inttypes.h>
#include "aggregator.h"

typedef struct {
    int total_csv;
    int total_db;
    int novos_qtd;
    int alterados_qtd;
    int inativados_qtd;
    int mantidos_qtd;
} DiffSummaryStats;

// Gera a string de diagnóstico textual descritivo para fundamentar a decisão do usuário
int generate_text_diagnosis_native(const DiffSummaryStats *stats, char *out_text, size_t max_len) {
    if (!stats || !out_text) return 0;

    snprintf(out_text, max_len,
        "===================================================================\n"
        "       DIAGNÓSTICO ANALÍTICO DE SINCRONIZAÇÃO E IMPACTO NO BANCO    \n"
        "===================================================================\n"
        "Total de Registros Analisados no CSV Importado: %d\n"
        "Total de Registros Atuais no Banco de Dados:    %d\n"
        "-------------------------------------------------------------------\n"
        " -> Novos Registros a Inserir:                 %d (IDs Snowflake gerados)\n"
        " -> Registros Existentes a Atualizar:           %d\n"
        " -> Registros a Inativar (ativo=0):             %d (Preservados por Soft Delete)\n"
        " -> Registros Mantidos Sem Alteração:           %d\n"
        "-------------------------------------------------------------------\n"
        "RECOMENDAÇÃO DE DECISÃO:\n"
        "Todos os novos registros receberão chaves únicas Snowflake (64-bit).\n"
        "Nenhum registro será excluído fisicamente (DELETE) do MySQL.\n"
        "Os registros ausentes na nova carga receberão a marcação ativo = 0\n"
        "e serão registrados no log auditado de auditoria com IP, data e hora.\n"
        "===================================================================\n",
        stats->total_csv,
        stats->total_db,
        stats->novos_qtd,
        stats->alterados_qtd,
        stats->inativados_qtd,
        stats->mantidos_qtd
    );

    return 1;
}
