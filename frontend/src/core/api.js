// Cliente HTTP básico da API. Trocar API_URL quando houver ambiente publicado.
const API_URL = "http://localhost:8000";

async function api(caminho, opcoes = {}) {
    let resp;
    try {
        resp = await fetch(API_URL + caminho, {
            headers: { "Content-Type": "application/json" },
            ...opcoes,
            body: opcoes.body ? JSON.stringify(opcoes.body) : undefined,
        });
    } catch {
        throw new Error("Não foi possível conectar ao servidor. Verifique sua conexão e tente novamente.");
    }
    if (resp.status === 204) return null;
    const dados = await resp.json().catch(() => ({}));
    if (!resp.ok) {
        // Formato da API: {detail, codigo, request_id}. detail pode ser lista no formato antigo do FastAPI.
        const detalhe = Array.isArray(dados.detail) ? dados.detail.map((d) => d.msg).join("; ") : dados.detail;
        const erro = new Error(detalhe || "Erro ao falar com o servidor");
        erro.status = resp.status;
        erro.codigo = dados.codigo;
        throw erro;
    }
    return dados;
}

// TODO(front): trocar por token JWT quando a task B1 estiver pronta
function usuarioLogado() {
    return JSON.parse(localStorage.getItem("usuario") || "null");
}
