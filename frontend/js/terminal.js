/* Gerenciador de WebSocket e Renderização do Terminal */

class TerminalController {
    constructor(bodyId, statusId) {
        self = this;
        this.terminalBody = document.getElementById(bodyId);
        this.statusText = document.getElementById(statusId);
        this.socket = null;
        this.reconnectInterval = 3000;

        this.initWebSocket();
    }

    initWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const urlParams = new URLSearchParams(window.location.search);
        const token = urlParams.get('token');
        const tokenParam = token ? `?token=${encodeURIComponent(token)}` : '';
        const wsUrl = `${protocol}//${window.location.host}/ws/terminal${tokenParam}`;

        this.socket = new WebSocket(wsUrl);

        this.socket.onopen = () => {
            this.statusText.textContent = "Conectado";
            this.statusText.style.color = "#3fb950";
            this.appendLog("[CONEXAO] Canal WebSocket estabelecido com o servidor backend.", "success");
        };

        this.socket.onmessage = (event) => {
            this.appendLog(event.data);
        };

        this.socket.onclose = () => {
            this.statusText.textContent = "Desconectado";
            this.statusText.style.color = "#f85149";
            setTimeout(() => this.initWebSocket(), this.reconnectInterval);
        };

        this.socket.onerror = (err) => {
            this.statusText.textContent = "Erro WS";
            this.statusText.style.color = "#f85149";
        };
    }

    appendLog(rawMessage, forcedClass = "") {
        const line = document.createElement("div");
        line.className = "log-line";

        if (forcedClass) {
            line.classList.add(forcedClass);
        } else if (rawMessage.includes("[ERRO]") || rawMessage.includes("Error")) {
            line.classList.add("erro");
        } else if (rawMessage.includes("[AVISO]")) {
            line.classList.add("aviso");
        } else if (rawMessage.includes("[SUCESSO]")) {
            line.classList.add("success");
        } else {
            line.classList.add("info");
        }

        line.textContent = rawMessage;
        this.terminalBody.appendChild(line);

        // Autoscroll para o final do terminal
        this.terminalBody.scrollTop = this.terminalBody.scrollHeight;
    }

    clear() {
        this.terminalBody.innerHTML = "";
    }
}

// Inicializar quando o DOM estiver pronto
document.addEventListener("DOMContentLoaded", () => {
    window.terminal = new TerminalController("terminal-body", "ws-status-text");
});
