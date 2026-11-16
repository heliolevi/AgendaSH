// Cliente HTTP da API + sessao por token (JWT). Trocar API_URL quando houver ambiente publicado.
const API_URL = "http://localhost:8000";
const TOKEN_KEY = "agendash_token";

function getToken() {
    return localStorage.getItem(TOKEN_KEY);
}

function setSessao(token, usuario) {
    if (token) localStorage.setItem(TOKEN_KEY, token);
    if (usuario) localStorage.setItem("usuario", JSON.stringify(usuario));
}

function limparSessao() {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem("usuario");
}

const PAGINAS_PUBLICAS = /(welcome|login|cadastro|esqueciSenha)\.html$/;

async function api(caminho, opcoes = {}) {
    const headers = { "Content-Type": "application/json", ...(opcoes.headers || {}) };
    const token = getToken();
    if (token) headers["Authorization"] = "Bearer " + token;

    let resp;
    try {
        resp = await fetch(API_URL + caminho, {
            ...opcoes,
            headers,
            body: opcoes.body ? JSON.stringify(opcoes.body) : undefined,
        });
    } catch {
        throw new Error("Nao foi possivel conectar ao servidor. Verifique sua conexao e tente novamente.");
    }

    // Token invalido/expirado numa rota protegida: encerra a sessao e volta para a entrada.
    if (resp.status === 401 && !caminho.startsWith("/auth/")) {
        limparSessao();
        if (!PAGINAS_PUBLICAS.test(location.pathname)) location.href = "welcome.html";
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

function usuarioLogado() {
    return JSON.parse(localStorage.getItem("usuario") || "null");
}

function ehAdmin() {
    const u = usuarioLogado();
    return !!u && u.papel === "admin";
}
