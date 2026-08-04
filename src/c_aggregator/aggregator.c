#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <inttypes.h>
#include "aggregator.h"

// Funcao auxiliar para alocacao e adicao de ID de curso
static void add_course_id(InstitutionRecord *inst, uint64_t course_id) {
    if (inst->course_count >= inst->course_capacity) {
        size_t new_capacity = inst->course_capacity == 0 ? INITIAL_CAPACITY : inst->course_capacity * 2;
        uint64_t *new_array = (uint64_t *)realloc(inst->course_ids, new_capacity * sizeof(uint64_t));
        if (!new_array) {
            fprintf(stderr, "Erro de alocacao de memoria ao agregar curso\n");
            return;
        }
        inst->course_ids = new_array;
        inst->course_capacity = new_capacity;
    }
    
    // Evita duplicatas
    for (size_t i = 0; i < inst->course_count; i++) {
        if (inst->course_ids[i] == course_id) {
            return;
        }
    }
    
    inst->course_ids[inst->course_count++] = course_id;
}

int process_aggregation(const char *institutions_file, const char *relations_file, const char *output_file) {
    FILE *f_inst = fopen(institutions_file, "r");
    if (!f_inst) {
        fprintf(stderr, "Erro ao abrir arquivo de instituicoes: %s\n", institutions_file);
        return 1;
    }

    // Leitura das instituicoes base
    char line[MAX_LINE_LENGTH];
    size_t inst_count = 0;
    size_t inst_capacity = INITIAL_CAPACITY;
    InstitutionRecord *institutions = (InstitutionRecord *)malloc(inst_capacity * sizeof(InstitutionRecord));

    // Ignora cabecalho
    if (fgets(line, sizeof(line), f_inst) == NULL) {
        fclose(f_inst);
        free(institutions);
        return 1;
    }

    while (fgets(line, sizeof(line), f_inst)) {
        if (inst_count >= inst_capacity) {
            inst_capacity *= 2;
            institutions = (InstitutionRecord *)realloc(institutions, inst_capacity * sizeof(InstitutionRecord));
        }

        InstitutionRecord *rec = &institutions[inst_count];
        memset(rec, 0, sizeof(InstitutionRecord));

        // Leitura com SCNu64 para uint64_t
        uint64_t sf_id = 0;
        char nome[256] = {0}, dep[64] = {0}, end[512] = {0}, tel[64] = {0}, email[128] = {0}, site[256] = {0};

        // Formato CSV separado por tab/virgula seguro
        int parsed = sscanf(line, "%" SCNu64 ";%255[^;];%63[^;];%511[^;];%63[^;];%127[^;];%255[^\n]",
                            &sf_id, nome, dep, end, tel, email, site);

        if (parsed >= 1) {
            rec->inst_snowflake_id = sf_id;
            strncpy(rec->inst_nome, nome, sizeof(rec->inst_nome) - 1);
            strncpy(rec->dependencia_adm, dep, sizeof(rec->dependencia_adm) - 1);
            strncpy(rec->endereco, end, sizeof(rec->endereco) - 1);
            strncpy(rec->telefone, tel, sizeof(rec->telefone) - 1);
            strncpy(rec->email, email, sizeof(rec->email) - 1);
            strncpy(rec->homepage, site, sizeof(rec->homepage) - 1);
            rec->course_ids = NULL;
            rec->course_count = 0;
            rec->course_capacity = 0;
            inst_count++;
        }
    }
    fclose(f_inst);

    // Leitura do arquivo de relacoes entre Instituicao e Curso (uint64_t -> uint64_t)
    FILE *f_rel = fopen(relations_file, "r");
    if (f_rel) {
        // Ignora cabecalho relacoes
        fgets(line, sizeof(line), f_rel);
        uint64_t inst_sf_id = 0;
        uint64_t course_sf_id = 0;

        while (fscanf(f_rel, "%" SCNu64 ";%" SCNu64 "\n", &inst_sf_id, &course_sf_id) == 2) {
            for (size_t i = 0; i < inst_count; i++) {
                if (institutions[i].inst_snowflake_id == inst_sf_id) {
                    add_course_id(&institutions[i], course_sf_id);
                    break;
                }
            }
        }
        fclose(f_rel);
    }

    // Escrita do CSV Final csv_instituicoes.csv
    FILE *f_out = fopen(output_file, "w");
    if (!f_out) {
        fprintf(stderr, "Erro ao criar arquivo de saida: %s\n", output_file);
        for (size_t i = 0; i < inst_count; i++) free(institutions[i].course_ids);
        free(institutions);
        return 1;
    }

    // Cabecalho oficial
    fprintf(f_out, "snowflake_id;nome_instituicao;dependencia_adm;endereco;telefone;email;homepage;cursos_ofertados_ids\n");

    for (size_t i = 0; i < inst_count; i++) {
        InstitutionRecord *rec = &institutions[i];

        // Formatacao estrita de uint64_t com PRIu64
        fprintf(f_out, "%" PRIu64 ";\"%s\";\"%s\";\"%s\";\"%s\";\"%s\";\"%s\";\"[",
                rec->inst_snowflake_id, rec->inst_nome, rec->dependencia_adm,
                rec->endereco, rec->telefone, rec->email, rec->homepage);

        for (size_t j = 0; j < rec->course_count; j++) {
            fprintf(f_out, "%" PRIu64 "%s", rec->course_ids[j], (j + 1 < rec->course_count) ? ", " : "");
        }
        fprintf(f_out, "]\"\n");
    }

    fclose(f_out);

    // Liberacao de memoria
    for (size_t i = 0; i < inst_count; i++) {
        if (institutions[i].course_ids) {
            free(institutions[i].course_ids);
        }
    }
    free(institutions);

    return 0;
}

int main(int argc, char *argv[]) {
    if (argc < 4) {
        fprintf(stderr, "Uso: %s <institutions.csv> <relations.csv> <output_institutions.csv>\n", argv[0]);
        return 1;
    }

    return process_aggregation(argv[1], argv[2], argv[3]);
}
