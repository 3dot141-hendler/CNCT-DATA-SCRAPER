/**
 * Controlador Javascript para a interface de Migração do CNCT Scraper.
 * Integração com Tabulator.js (Dark Theme) para colunas redimensionáveis,
 * busca unificada simultânea em Tabela Dual (MySQL vs Raspagem) e streaming SSE.
 */

document.addEventListener('DOMContentLoaded', () => {
    const btnPreview = document.getElementById('btn-carregar-preview');
    const btnCarregarBanco = document.getElementById('btn-carregar-banco');
    const btnCarregarCursosPreview = document.getElementById('btn-carregar-cursos-preview');
    const btnCarregarCursosBanco = document.getElementById('btn-carregar-cursos-banco');

    const btnSimularDiff = document.getElementById('btn-simular-diff');
    const btnAbrirModal = document.getElementById('btn-abrir-confirmacao');
    const btnCancelarModal = document.getElementById('btn-cancelar-modal');
    const btnExecutar = document.getElementById('btn-executar-sincronizacao');

    const inputBuscaUnificada = document.getElementById('input-busca-unificada');
    const selectModoBusca = document.getElementById('select-modo-busca');
    const counterDbRows = document.getElementById('counter-db-rows');
    const counterScraperRows = document.getElementById('counter-scraper-rows');

    const inputBuscaCursos = document.getElementById('input-busca-cursos');
    const selectModoBuscaCursos = document.getElementById('select-modo-busca-cursos');
    const counterDbCursosRows = document.getElementById('counter-db-cursos-rows');
    const counterScraperCursosRows = document.getElementById('counter-scraper-cursos-rows');

    const containerStats = document.getElementById('container-stats');
    const containerDiagnosis = document.getElementById('container-diagnosis');
    const textDiagnosisBody = document.getElementById('text-diagnosis-body');
    const modalConfirmacao = document.getElementById('modal-confirmacao');
    const progressContainer = document.getElementById('progress-container');

    const valNovos = document.getElementById('val-novos');
    const valAlterados = document.getElementById('val-alterados');
    const valInativados = document.getElementById('val-inativados');
    const valMantidos = document.getElementById('val-mantidos');

    const auditTimestamp = document.getElementById('audit-timestamp');
    const inputSenha = document.getElementById('input-senha-confirmacao');

    const progressBarFill = document.getElementById('progress-bar-fill');
    const progressLabelCounter = document.getElementById('progress-label-counter');
    const progressLabelItem = document.getElementById('progress-label-item');

    const dbStatInst = document.getElementById('db-stat-inst');
    const dbStatCursos = document.getElementById('db-stat-cursos');
    const dbStatUpdated = document.getElementById('db-stat-updated');

    let dadosCachePreview = [];
    let dadosCacheBanco = [];
    let dadosCacheCursosPreview = [];
    let dadosCacheCursosBanco = [];
    let dadosCacheDiff = null;

    let tabulatorScraperInstance = null;
    let tabulatorDbInstance = null;
    let tabulatorScraperCursosInstance = null;
    let tabulatorDbCursosInstance = null;

    // Utilitário para capturar token da URL
    const getTokenParam = () => {
        const urlParams = new URLSearchParams(window.location.search);
        const token = urlParams.get('token');
        return token ? `?token=${encodeURIComponent(token)}` : '';
    };

    // Carrega métricas do MySQL nos cards superiores
    async function loadDBStatus() {
        try {
            const resp = await fetch(`/api/migracao/status-banco${getTokenParam()}`, { credentials: 'include' });
            if (resp.ok) {
                const data = await resp.json();
                if (dbStatInst) dbStatInst.textContent = data.total_instituicoes.toLocaleString('pt-BR');
                if (dbStatCursos) dbStatCursos.textContent = data.total_cursos.toLocaleString('pt-BR');
                if (dbStatUpdated) dbStatUpdated.textContent = data.ultima_atualizacao || 'N/A';
            }
        } catch (e) {
            console.warn('[STATUS DB WARN] Não foi possível carregar indicadores do MySQL:', e);
        }
    }
    loadDBStatus();

    // Definição das colunas padrão do Tabulator
    const defaultColumns = [
        { title: "Snowflake ID", field: "snowflake_id", width: 150, resizable: true, tooltip: true, headerFilter: "input" },
        { title: "Instituição", field: "nome_instituicao", minWidth: 180, resizable: true, tooltip: true, headerFilter: "input" },
        { title: "Logradouro", field: "logradouro", minWidth: 140, resizable: true, tooltip: true },
        { title: "Número", field: "numero", width: 80, resizable: true },
        { title: "Bairro", field: "bairro", minWidth: 110, resizable: true },
        { title: "Município", field: "municipio", minWidth: 120, resizable: true, headerFilter: "input" },
        { 
            title: "UF", 
            field: "uf", 
            width: 60, 
            hozAlign: "center",
            formatter: cell => `<span class="badge-novo">${cell.getValue() || '-'}</span>`
        },
        { title: "CEP", field: "cep", width: 100, hozAlign: "center", resizable: true }
    ];

    // Inicializa Tabela 1: Banco MySQL
    function initDbTabulator(data = []) {
        if (tabulatorDbInstance) {
            tabulatorDbInstance.setData(data);
            if (counterDbRows) counterDbRows.textContent = `${data.length.toLocaleString('pt-BR')} registros`;
            return;
        }

        tabulatorDbInstance = new Tabulator("#tabulator-db-table", {
            data: data,
            height: "450px",
            layout: "fitDataFill",
            resizableColumnFit: true,
            pagination: "local",
            paginationSize: 20,
            paginationSizeSelector: [15, 20, 50, 100],
            paginationCounter: "rows",
            placeholder: "Clique no botão acima para carregar os registros do MySQL.",
            columns: defaultColumns
        });
    }

    // Inicializa Tabela 2: Dados Raspados (CNCT)
    function initScraperTabulator(data = []) {
        if (tabulatorScraperInstance) {
            tabulatorScraperInstance.setData(data);
            if (counterScraperRows) counterScraperRows.textContent = `${data.length.toLocaleString('pt-BR')} registros`;
            return;
        }

        tabulatorScraperInstance = new Tabulator("#tabulator-table", {
            data: data,
            height: "450px",
            layout: "fitDataFill",
            resizableColumnFit: true,
            pagination: "local",
            paginationSize: 20,
            paginationSizeSelector: [15, 20, 50, 100],
            paginationCounter: "rows",
            placeholder: "Clique no botão acima para carregar a raspagem do CNCT.",
            columns: defaultColumns
        });
    }

    // Instancia ambas as tabelas vazias inicialmente
    initDbTabulator([]);
    initScraperTabulator([]);

    // --- Tabulator para Cursos Técnicos ---
    const defaultCourseColumns = [
        { title: "Snowflake ID", field: "snowflake_id", width: 160, resizable: true, tooltip: true, headerFilter: "input" },
        { title: "ID Mec", field: "id_original", width: 80, hozAlign: "center", resizable: true },
        { title: "Nome do Curso", field: "nome_curso", minWidth: 200, resizable: true, tooltip: true, headerFilter: "input" },
        { title: "Eixo Tecnológico", field: "eixo_tecnologico", minWidth: 180, resizable: true, tooltip: true, headerFilter: "input" },
        { title: "Carga Horária", field: "carga_horaria", minWidth: 120, resizable: true, tooltip: true },
        { title: "Pré-requisito", field: "pre_requisito", minWidth: 140, resizable: true, tooltip: true },
        { title: "Campo Atuação", field: "campo_atuacao", minWidth: 140, resizable: true, tooltip: true },
        { title: "Ocupações CBO", field: "ocupacoes_cbo", minWidth: 120, resizable: true, tooltip: true }
    ];

    function initDbCursosTabulator(data = []) {
        if (tabulatorDbCursosInstance) {
            tabulatorDbCursosInstance.setData(data);
            if (counterDbCursosRows) counterDbCursosRows.textContent = `${data.length.toLocaleString('pt-BR')} registros`;
            return;
        }

        tabulatorDbCursosInstance = new Tabulator("#tabulator-db-cursos-table", {
            data: data,
            height: "450px",
            layout: "fitDataFill",
            resizableColumnFit: true,
            pagination: "local",
            paginationSize: 20,
            paginationSizeSelector: [15, 20, 50, 100],
            paginationCounter: "rows",
            placeholder: "Clique no botão acima para carregar os cursos do MySQL.",
            columns: defaultCourseColumns
        });
    }

    function initScraperCursosTabulator(data = []) {
        if (tabulatorScraperCursosInstance) {
            tabulatorScraperCursosInstance.setData(data);
            if (counterScraperCursosRows) counterScraperCursosRows.textContent = `${data.length.toLocaleString('pt-BR')} registros`;
            return;
        }

        tabulatorScraperCursosInstance = new Tabulator("#tabulator-cursos-table", {
            data: data,
            height: "450px",
            layout: "fitDataFill",
            resizableColumnFit: true,
            pagination: "local",
            paginationSize: 20,
            paginationSizeSelector: [15, 20, 50, 100],
            paginationCounter: "rows",
            placeholder: "Clique no botão acima para carregar a raspagem de cursos.",
            columns: defaultCourseColumns
        });
    }

    initDbCursosTabulator([]);
    initScraperCursosTabulator([]);

    // Dispara carregamento automático ao carregar a página
    setTimeout(() => {
        if (btnCarregarBanco) btnCarregarBanco.click();
        if (btnPreview) btnPreview.click();
        if (btnCarregarCursosBanco) btnCarregarCursosBanco.click();
        if (btnCarregarCursosPreview) btnCarregarCursosPreview.click();
    }, 300);

    // --- Filtro de Busca Unificada Simultânea de Cursos ---
    function aplicarFiltroUnificadoCursos() {
        if (!inputBuscaCursos || !selectModoBuscaCursos) return;
        const query = inputBuscaCursos.value.trim().toLowerCase();
        const modo = selectModoBuscaCursos.value;

        const customFilter = (data) => {
            if (!query) return true;
            const targetStr = [
                data.snowflake_id, data.id_original, data.nome_curso,
                data.eixo_tecnologico, data.carga_horaria, data.pre_requisito,
                data.campo_atuacao, data.ocupacoes_cbo
            ].filter(Boolean).join(' ').toLowerCase();
            
            return targetStr.includes(query);
        };

        if (modo === 'ambas' || modo === 'banco') {
            if (tabulatorDbCursosInstance) {
                if (query) tabulatorDbCursosInstance.setFilter(customFilter);
                else tabulatorDbCursosInstance.clearFilter();
            }
        }
        if (modo === 'ambas' || modo === 'raspagem') {
            if (tabulatorScraperCursosInstance) {
                if (query) tabulatorScraperCursosInstance.setFilter(customFilter);
                else tabulatorScraperCursosInstance.clearFilter();
            }
        }
    }

    if (inputBuscaCursos) inputBuscaCursos.addEventListener('input', aplicarFiltroUnificadoCursos);
    if (selectModoBuscaCursos) selectModoBuscaCursos.addEventListener('change', aplicarFiltroUnificadoCursos);

    // --- Carregadores de Cursos ---
    if (btnCarregarCursosPreview) {
        btnCarregarCursosPreview.addEventListener('click', async () => {
            btnCarregarCursosPreview.disabled = true;
            btnCarregarCursosPreview.textContent = 'Carregando Cursos...';

            try {
                const resp = await fetch(`/api/migracao/preview-cursos${getTokenParam()}`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    credentials: 'include',
                    body: JSON.stringify({})
                });

                if (!resp.ok) throw new Error('Falha ao obter cursos raspados.');

                const data = await resp.json();
                dadosCacheCursosPreview = data.amostragem || [];

                initScraperCursosTabulator(dadosCacheCursosPreview);
                aplicarFiltroUnificadoCursos();

            } catch (err) {
                alert('Erro ao carregar cursos da raspagem: ' + err.message);
            } finally {
                btnCarregarCursosPreview.disabled = false;
                btnCarregarCursosPreview.textContent = 'Carregar Cursos Raspados CNCT';
            }
        });
    }

    if (btnCarregarCursosBanco) {
        btnCarregarCursosBanco.addEventListener('click', async () => {
            btnCarregarCursosBanco.disabled = true;
            btnCarregarCursosBanco.textContent = 'Buscando Cursos MySQL...';

            try {
                const resp = await fetch(`/api/migracao/dados-banco-cursos${getTokenParam()}`, { credentials: 'include' });
                if (!resp.ok) throw new Error('Falha ao buscar cursos do banco.');

                const data = await resp.json();
                if (data.db_connected === false) {
                    alert('AVISO DE CONEXÃO COM O BANCO (VPS):\n\n' + (data.mensagem || 'Não foi possível conectar ao banco de dados MySQL.'));
                }
                dadosCacheCursosBanco = data.registros || [];

                initDbCursosTabulator(dadosCacheCursosBanco);
                aplicarFiltroUnificadoCursos();

            } catch (err) {
                alert('Erro ao carregar cursos do banco: ' + err.message);
            } finally {
                btnCarregarCursosBanco.disabled = false;
                btnCarregarCursosBanco.textContent = 'Carregar Cursos MySQL (VPS)';
            }
        });
    }

    // --- Filtro de Busca Unificada Simultânea ---
    function aplicarFiltroUnificado() {
        const query = inputBuscaUnificada.value.trim().toLowerCase();
        const modo = selectModoBusca.value;

        const customFilter = (data) => {
            if (!query) return true;
            const targetStr = [
                data.snowflake_id, data.nome_instituicao, data.logradouro,
                data.bairro, data.municipio, data.uf, data.cep, data.endereco
            ].filter(Boolean).join(' ').toLowerCase();
            
            return targetStr.includes(query);
        };

        if (modo === 'ambas' || modo === 'banco') {
            if (tabulatorDbInstance) {
                if (query) tabulatorDbInstance.setFilter(customFilter);
                else tabulatorDbInstance.clearFilter();
            }
        }
        if (modo === 'ambas' || modo === 'raspagem') {
            if (tabulatorScraperInstance) {
                if (query) tabulatorScraperInstance.setFilter(customFilter);
                else tabulatorScraperInstance.clearFilter();
            }
        }
    }

    inputBuscaUnificada.addEventListener('input', aplicarFiltroUnificado);
    selectModoBusca.addEventListener('change', aplicarFiltroUnificado);

    // 1. Carregar Dados Raspados CNCT
    btnPreview.addEventListener('click', async () => {
        btnPreview.disabled = true;
        btnPreview.textContent = 'Processando CNCT...';

        try {
            const resp = await fetch(`/api/migracao/preview-amostragem${getTokenParam()}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include',
                body: JSON.stringify({})
            });

            if (!resp.ok) throw new Error('Falha ao obter dados raspados.');

            const data = await resp.json();
            dadosCachePreview = data.amostragem || [];

            initScraperTabulator(dadosCachePreview);
            aplicarFiltroUnificado();

        } catch (err) {
            alert('Erro ao carregar dados da raspagem: ' + err.message);
        } finally {
            btnPreview.disabled = false;
            btnPreview.textContent = 'Carregar Dados Raspados CNCT';
        }
    });

    // 1.1 Carregar Registros do Banco MySQL (VPS)
    if (btnCarregarBanco) {
        btnCarregarBanco.addEventListener('click', async () => {
            btnCarregarBanco.disabled = true;
            btnCarregarBanco.textContent = 'Buscando MySQL...';

            try {
                const resp = await fetch(`/api/migracao/dados-banco${getTokenParam()}`, { credentials: 'include' });
                if (!resp.ok) throw new Error('Falha ao buscar registros do banco.');

                const data = await resp.json();
                if (data.db_connected === false) {
                    alert('⚠️ AVISO DE CONEXÃO COM O BANCO (VPS):\n\n' + (data.mensagem || 'Não foi possível conectar ao banco de dados MySQL (127.0.0.1:33060). Certifique-se de que o túnel SSH com a VPS está ativo em segundo plano.'));
                }
                dadosCacheBanco = data.registros || [];

                initDbTabulator(dadosCacheBanco);
                aplicarFiltroUnificado();

            } catch (err) {
                alert('Erro ao carregar dados do banco: ' + err.message);
            } finally {
                btnCarregarBanco.disabled = false;
                btnCarregarBanco.textContent = 'Carregar Dados MySQL (VPS)';
            }
        });
    }

    // 2. Executar Simulação de Diff e Teste de Eficiência contra a VPS
    const executarDiff = async () => {
        btnSimularDiff.disabled = true;
        btnSimularDiff.textContent = 'Comparando Banco...';

        try {
            // Se a prévia do CSV estiver vazia, garante o carregamento da raspagem primeiro
            if (!dadosCachePreview || dadosCachePreview.length === 0) {
                const respPrev = await fetch(`/api/migracao/preview-amostragem${getTokenParam()}`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    credentials: 'include',
                    body: JSON.stringify({})
                });
                if (respPrev.ok) {
                    const dataPrev = await respPrev.json();
                    dadosCachePreview = dataPrev.amostragem || [];
                    initScraperTabulator(dadosCachePreview);
                }
            }

            const resp = await fetch(`/api/migracao/simulacao-diff${getTokenParam()}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include',
                body: JSON.stringify({ registros: dadosCachePreview })
            });

            if (!resp.ok) throw new Error('Falha ao simular diff contra o MySQL.');

            const data = await resp.json();
            dadosCacheDiff = data;

            valNovos.textContent = data.estatisticas.novos_qtd.toLocaleString('pt-BR');
            valAlterados.textContent = data.estatisticas.alterados_qtd.toLocaleString('pt-BR');
            valInativados.textContent = data.estatisticas.inativados_qtd.toLocaleString('pt-BR');
            valMantidos.textContent = data.estatisticas.mantidos_qtd.toLocaleString('pt-BR');

            textDiagnosisBody.textContent = data.diagnostico_texto;

            containerStats.style.display = 'grid';
            containerDiagnosis.style.display = 'block';

            // Atualiza indicadores do banco e tabela do MySQL
            await loadDBStatus();
            if (btnCarregarBanco) btnCarregarBanco.click();

        } catch (err) {
            alert('Erro ao executar diff: ' + err.message);
        } finally {
            btnSimularDiff.disabled = false;
            btnSimularDiff.textContent = 'Executar Simulação de Diff';
        }
    };

    btnSimularDiff.addEventListener('click', executarDiff);

    // 3. Abrir Modal de Confirmação por Senha
    btnAbrirModal.addEventListener('click', () => {
        auditTimestamp.textContent = new Date().toLocaleString('pt-BR');
        modalConfirmacao.style.display = 'flex';
        inputSenha.value = '';
        inputSenha.focus();
    });

    btnCancelarModal.addEventListener('click', () => {
        modalConfirmacao.style.display = 'none';
    });

    // 4. Executar Povoamento com Streaming SSE e Barra de Progresso
    btnExecutar.addEventListener('click', async () => {
        const senha = inputSenha.value.trim();
        if (!senha) {
            alert('Por favor, digite sua senha de usuário logado.');
            return;
        }

        modalConfirmacao.style.display = 'none';
        progressContainer.style.display = 'block';
        btnAbrirModal.disabled = true;

        try {
            const inativadosIds = (dadosCacheDiff?.amostragem_diff?.inativados || []).map(i => i.id || i.snowflake_id);

            const resp = await fetch(`/api/migracao/executar${getTokenParam()}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include',
                body: JSON.stringify({
                    senha: senha,
                    registros: dadosCachePreview,
                    inativados_ids: inativadosIds
                })
            });

            if (!resp.ok) {
                const errJson = await resp.json();
                throw new Error(errJson.detail || 'Falha ao autorizar execução.');
            }

            const reader = resp.body.getReader();
            const decoder = new TextDecoder('utf-8');

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                const chunk = decoder.decode(value);
                const lines = chunk.split('\n');

                for (let line of lines) {
                    if (line.startsWith('data: ')) {
                        try {
                            const payload = JSON.parse(line.substring(6));

                            if (payload.status === 'processando') {
                                const pct = payload.percentual || 0;
                                progressBarFill.style.width = pct + '%';
                                progressLabelCounter.textContent = `${payload.atual} / ${payload.total} (${pct}%)`;
                                progressLabelItem.textContent = `Inserindo/Atualizando: ${payload.item_atual}`;
                            } else if (payload.status === 'concluido') {
                                progressBarFill.style.width = '100%';
                                progressLabelCounter.textContent = `${payload.progresso} (100%)`;
                                progressLabelItem.textContent = 'Banco de Dados 100% Sincronizado com Sucesso';
                                
                                alert(`SUCESSO: Sincronização concluída com sucesso!\n\nAuditoria Registrada:\nIP: ${payload.audit_ip}\nData: ${payload.audit_timestamp}`);
                                
                                // Executa o diff automático e atualiza os parâmetros no topo da página
                                await executarDiff();
                            } else if (payload.status === 'erro') {
                                progressContainer.style.display = 'none';
                                alert('ERRO NA MIGRAÇÃO: ' + payload.mensagem);
                            }
                        } catch (e) {
                            // Ignora trechos parciais de JSON
                        }
                    }
                }
            }

        } catch (err) {
            alert('Erro durante execução: ' + err.message);
        } finally {
            btnAbrirModal.disabled = false;
        }
    });

    // --- Handlers de Download de Relatórios de Diff (CSV e Excel Multi-Abas) ---
    const btnDownloadExcel = document.getElementById('btn-download-excel');
    const btnDownloadCsv1 = document.getElementById('btn-download-csv-1');
    const btnDownloadCsv2 = document.getElementById('btn-download-csv-2');
    const btnDownloadCsv3 = document.getElementById('btn-download-csv-3');
    const btnDownloadCsv4 = document.getElementById('btn-download-csv-4');

    if (btnDownloadExcel) {
        btnDownloadExcel.addEventListener('click', () => {
            window.location.href = `/api/migracao/download-diff/excel${getTokenParam()}`;
        });
    }

    if (btnDownloadCsv1) {
        btnDownloadCsv1.addEventListener('click', () => {
            window.location.href = `/api/migracao/download-diff/csv/1${getTokenParam()}`;
        });
    }

    if (btnDownloadCsv2) {
        btnDownloadCsv2.addEventListener('click', () => {
            window.location.href = `/api/migracao/download-diff/csv/2${getTokenParam()}`;
        });
    }

    if (btnDownloadCsv3) {
        btnDownloadCsv3.addEventListener('click', () => {
            window.location.href = `/api/migracao/download-diff/csv/3${getTokenParam()}`;
        });
    }

    if (btnDownloadCsv4) {
        btnDownloadCsv4.addEventListener('click', () => {
            window.location.href = `/api/migracao/download-diff/csv/4${getTokenParam()}`;
        });
    }
});

