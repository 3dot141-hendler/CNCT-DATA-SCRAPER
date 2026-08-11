/* Manipulador Principal de Navegação de Abas e Requisições REST */

document.addEventListener("DOMContentLoaded", () => {
    // 1. Controle de Alternância de Abas
    const tabButtons = document.querySelectorAll(".tab-btn");
    const tabContents = document.querySelectorAll(".tab-content");

    tabButtons.forEach(button => {
        button.addEventListener("click", () => {
            const targetTab = button.getAttribute("data-tab");

            tabButtons.forEach(btn => btn.classList.remove("active"));
            tabContents.forEach(content => content.classList.remove("active"));

            button.classList.add("active");
            document.getElementById(targetTab).classList.add("active");
        });
    });

    // Função utilitária para capturar o token da URL se presente
    const getTokenParam = () => {
        const urlParams = new URLSearchParams(window.location.search);
        const token = urlParams.get('token');
        return token ? `&token=${encodeURIComponent(token)}` : '';
    };

    // Atualizar os links de download com o token da URL para funcionar no iframe
    const updateDownloadLinks = () => {
        const urlParams = new URLSearchParams(window.location.search);
        const token = urlParams.get('token');
        if (!token) return;

        document.querySelectorAll('a[download]').forEach(link => {
            let baseHref = link.getAttribute('data-base-href');
            if (!baseHref) {
                baseHref = link.getAttribute('href').split('?')[0];
                link.setAttribute('data-base-href', baseHref);
            }
            link.setAttribute('href', `${baseHref}?token=${encodeURIComponent(token)}`);
        });
    };
    updateDownloadLinks();

    // Consulta automática do total de cursos cadastrados no MEC ao carregar a página
    const fetchTotalCursosMEC = async () => {
        const infoElement = document.getElementById("info-total-cursos-mec");
        const maxCoursesInput = document.getElementById("max-courses");
        if (!infoElement) return;

        // Define valor padrão imediato para evitar exibição contínua de "Consultando..."
        infoElement.textContent = `Total de cursos atuais no MEC: 215`;

        try {
            const tokenParam = getTokenParam() ? `?${getTokenParam().replace(/^&/, '')}` : '';
            const resp = await fetch(`/api/scraper/total-cursos-mec${tokenParam}`, { credentials: "include" });
            if (resp.ok) {
                const data = await resp.json();
                const total = data.total_cursos_mec || 215;
                infoElement.textContent = `Total de cursos atuais no MEC: ${total}`;
                if (maxCoursesInput) maxCoursesInput.max = total;
            }
        } catch (err) {
            infoElement.textContent = `Total de cursos atuais no MEC: 215`;
        }
    };
    fetchTotalCursosMEC();

    // 2. Disparo de Raspagem via REST API
    const startBtn = document.getElementById("btn-start-scraper");
    const maxCoursesInput = document.getElementById("max-courses");

    if (startBtn) {
        startBtn.addEventListener("click", async () => {
            const maxCourses = parseInt(maxCoursesInput.value) || 5;
            startBtn.disabled = true;
            startBtn.textContent = "Processando...";

            try {
                const response = await fetch(`/api/scraper/start?max_courses=${maxCourses}${getTokenParam()}`, {
                    method: "POST",
                    credentials: "include"
                });
                const data = await response.json();

                if (response.ok) {
                    if (window.terminal) {
                        window.terminal.appendLog(`[START] ${data.message}`, "success");
                    }
                } else {
                    alert(data.detail || "Erro ao iniciar a raspagem.");
                }
            } catch (err) {
                alert("Falha de conexão com o servidor FastAPI.");
            } finally {
                setTimeout(() => {
                    startBtn.disabled = false;
                    startBtn.textContent = "Iniciar Raspagem";
                }, 3000);
            }
        });
    }

    // 3. Visualização de Amostragem de Dados
    const refreshDataBtn = document.getElementById("btn-refresh-data");
    const dataContainer = document.getElementById("data-preview-container");

    if (refreshDataBtn) {
        refreshDataBtn.addEventListener("click", async () => {
            try {
                const tokenParam = getTokenParam();
                const resCursos = await fetch(`/api/data/cursos?limit=5${tokenParam}`, { credentials: "include" });
                const dataCursos = await resCursos.json();

                const resInst = await fetch(`/api/data/instituicoes?limit=5${tokenParam}`, { credentials: "include" });
                const dataInst = await resInst.json();

                let html = "";

                if (dataCursos.cursos && dataCursos.cursos.length > 0) {
                    html += `<h3 style="color: var(--accent-blue); margin-bottom: 0.5rem;">Cursos Raspados (${dataCursos.cursos.length} amostras):</h3>`;
                    html += `<pre style="background:#010409; padding:1rem; border-radius:6px; font-family:var(--font-mono); font-size:0.8rem; overflow-x:auto; margin-bottom:1.5rem;">${JSON.stringify(dataCursos.cursos, null, 2)}</pre>`;
                }

                if (dataInst.instituicoes && dataInst.instituicoes.length > 0) {
                    html += `<h3 style="color: var(--accent-green); margin-bottom: 0.5rem;">Instituições Agregadas (${dataInst.instituicoes.length} amostras):</h3>`;
                    html += `<pre style="background:#010409; padding:1rem; border-radius:6px; font-family:var(--font-mono); font-size:0.8rem; overflow-x:auto;">${JSON.stringify(dataInst.instituicoes, null, 2)}</pre>`;
                }

                if (!html) {
                    html = `<p style="color: var(--text-secondary);">Nenhum arquivo CSV gerado ainda. Execute a raspagem no terminal primeiro.</p>`;
                }

                dataContainer.innerHTML = html;
            } catch (err) {
                dataContainer.innerHTML = `<p style="color: var(--accent-red);">Erro ao carregar dados: ${err.message}</p>`;
            }
        });
    }
});
