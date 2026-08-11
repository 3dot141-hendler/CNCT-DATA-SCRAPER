#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>
#include "aggregator.h"

// Estrutura de dados para o endereco parsed
typedef struct {
    char logradouro[256];
    char numero[256];
    char complemento[256];
    char bairro[256];
    char municipio[256];
    char uf[8];
    char cep[16];
} ParsedAddress;

// Função auxiliar para remover espaços em branco nas extremidades
static void trim(char *str) {
    if (!str) return;
    char *p = str;
    int l = strlen(p);
    while (isspace(p[l - 1]) || p[l - 1] == '.') p[--l] = 0;
    while (*p && isspace(*p)) p++;
    memmove(str, p, l + 1);
}

// Limpa caracteres especiais do CEP
static void sanitize_cep(const char *raw_cep, char *out_cep) {
    if (!raw_cep) {
        out_cep[0] = '\0';
        return;
    }
    int idx = 0;
    for (int i = 0; raw_cep[i] != '\0' && idx < 10; i++) {
        if (isdigit(raw_cep[i])) {
            out_cep[idx++] = raw_cep[i];
        }
    }
    out_cep[idx] = '\0';
}

// Algoritmo de parsing de endereço nativo em C
int parse_address_native(const char *raw_endereco, ParsedAddress *out) {
    if (!raw_endereco || strlen(raw_endereco) == 0 || strcasecmp(raw_endereco, "não informado") == 0) {
        memset(out, 0, sizeof(ParsedAddress));
        return 0;
    }

    memset(out, 0, sizeof(ParsedAddress));
    char buffer[1024];
    strncpy(buffer, raw_endereco, sizeof(buffer) - 1);
    trim(buffer);

    // 1. Tenta identificar UF e CEP no final da string (ex: " ... RS 93260-006" ou " ... RS 93260006")
    char *last_space = strrchr(buffer, ' ');
    if (last_space) {
        char possible_cep[32] = {0};
        strncpy(possible_cep, last_space + 1, sizeof(possible_cep) - 1);
        trim(possible_cep);
        
        char clean_cep[16] = {0};
        sanitize_cep(possible_cep, clean_cep);
        
        if (strlen(clean_cep) == 8) {
            strncpy(out->cep, clean_cep, sizeof(out->cep) - 1);
            *last_space = '\0'; // Trunca o CEP do buffer
            trim(buffer);
            
            // Verifica UF logo antes do CEP
            char *uf_space = strrchr(buffer, ' ');
            if (uf_space && strlen(uf_space + 1) == 2) {
                strncpy(out->uf, uf_space + 1, sizeof(out->uf) - 1);
                *uf_space = '\0';
                trim(buffer);
            }
        }
    }

    // 2. Se UF ainda não encontrada, busca no final da string restante por sigla de 2 letras
    if (strlen(out->uf) == 0) {
        char *uf_space = strrchr(buffer, ' ');
        if (uf_space && strlen(uf_space + 1) == 2) {
            strncpy(out->uf, uf_space + 1, sizeof(out->uf) - 1);
            *uf_space = '\0';
            trim(buffer);
        }
    }

    // 3. Separação por vírgulas para Logradouro, Número, Complemento, Bairro, Município
    char *tokens[10];
    int count = 0;
    char *token = strtok(buffer, ",");

    while (token != NULL && count < 10) {
        trim(token);
        if (strlen(token) > 0) {
            tokens[count++] = token;
        }
        token = strtok(NULL, ",");
    }

    if (count >= 1) {
        strncpy(out->municipio, tokens[count - 1], sizeof(out->municipio) - 1);
    }
    if (count == 2) {
        strncpy(out->logradouro, tokens[0], sizeof(out->logradouro) - 1);
    } else if (count == 3) {
        strncpy(out->logradouro, tokens[0], sizeof(out->logradouro) - 1);
        strncpy(out->numero, tokens[1], sizeof(out->numero) - 1);
    } else if (count == 4) {
        strncpy(out->logradouro, tokens[0], sizeof(out->logradouro) - 1);
        strncpy(out->numero, tokens[1], sizeof(out->numero) - 1);
        strncpy(out->bairro, tokens[2], sizeof(out->bairro) - 1);
    } else if (count >= 5) {
        strncpy(out->logradouro, tokens[0], sizeof(out->logradouro) - 1);
        strncpy(out->numero, tokens[1], sizeof(out->numero) - 1);
        strncpy(out->complemento, tokens[2], sizeof(out->complemento) - 1);
        strncpy(out->bairro, tokens[3], sizeof(out->bairro) - 1);
    }

    return 1;
}
