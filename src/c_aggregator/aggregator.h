#ifndef AGGREGATOR_H
#define AGGREGATOR_H

#include <stdint.h>
#include <inttypes.h>

#define MAX_LINE_LENGTH 8192
#define INITIAL_CAPACITY 64

// Estrutura para armazenar a instituicao e a lista agregada de Snowflake IDs de cursos ofertados
typedef struct {
    uint64_t inst_snowflake_id;
    char inst_nome[256];
    char dependencia_adm[64];
    char endereco[512];
    char telefone[64];
    char email[128];
    char homepage[256];
    
    uint64_t *course_ids;
    size_t course_count;
    size_t course_capacity;
} InstitutionRecord;

// Funcao de agregacao principal
int process_aggregation(const char *institutions_file, const char *relations_file, const char *output_file);

#endif // AGGREGATOR_H
