// Cliente HTTP da API + sessão por token (JWT).
// Ao publicar a API em outro endereço, troque API_URL aqui E o connect-src da meta CSP das páginas.
const API_URL = "http://localhost:8000";
const TOKEN_KEY = "agendash_token";
const TEMPO_LIMITE_MS = 15000;

// ---- anti-clickjacking ----
// frame-ancestors não funciona em <meta> CSP; até o servidor mandar o cabeçalho, a página se recusa a rodar dentro de iframe.
if (window.top !== window.self) {
    document.documentElement.style.display = "none";
    try { window.top.location.replace(window.self.location.href); } catch { /* origem diferente: segue escondida */ }
}

// ---- token ----
function lerPayload(token) {
    try {
        const corpo = token.split(".")[1].replace(/-/g, "+").replace(/_/g, "/");
        const bytes = Uint8Array.from(atob(corpo), (c) => c.charCodeAt(0));
        return JSON.parse(new TextDecoder().decode(bytes));
    } catch {
        return null;
    }
}

function tokenValido(token) {
    const p = token && lerPayload(token);
    return !!p && typeof p.exp === "number" && p.exp * 1000 > Date.now() + 5000;
}

function getToken() {
    const t = localStorage.getItem(TOKEN_KEY);
    if (t && !tokenValido(t)) {
        limparSessao();
        return null;
    }
    return t;
}

function setSessao(token, usuario) {
    if (token) localStorage.setItem(TOKEN_KEY, token);
    if (usuario) {
        // só o necessário para a interface; nada de senha, código ou hash
        const { id_usuario, nome, email, criado_em, papel } = usuario;
        localStorage.setItem("usuario", JSON.stringify({ id_usuario, nome, email, criado_em, papel }));
    }
}

function limparSessao() {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem("usuario");
}

const PAGINAS_PUBLICAS = /(welcome|login|cadastro|esqueciSenha|termos|404)\.html$/;

async function api(caminho, opcoes = {}) {
    const headers = { Accept: "application/json", ...(opcoes.headers || {}) };
    if (opcoes.body) headers["Content-Type"] = "application/json";
    const token = getToken();
    if (token) headers.Authorization = "Bearer " + token;

    const controle = new AbortController();
    const relogio = setTimeout(() => controle.abort(), TEMPO_LIMITE_MS);
    let resp;
    try {
        resp = await fetch(API_URL + caminho, {
            method: opcoes.method || "GET",
            headers,
            body: opcoes.body ? JSON.stringify(opcoes.body) : undefined,
            credentials: "omit",   // a sessão vai no cabeçalho, nunca em cookie
            cache: "no-store",
            redirect: "error",
            referrerPolicy: "no-referrer",
            signal: controle.signal,
        });
    } catch (e) {
        const erro = new Error(e.name === "AbortError"
            ? "O servidor demorou para responder. Tente de novo em instantes."
            : "Não foi possível conectar ao servidor. Verifique sua conexão e tente novamente.");
        erro.status = 0;
        throw erro;
    } finally {
        clearTimeout(relogio);
    }

    // Token inválido/expirado numa rota protegida: encerra a sessão e volta para o login.
    if (resp.status === 401 && !caminho.startsWith("/auth/")) {
        limparSessao();
        if (!PAGINAS_PUBLICAS.test(location.pathname)) location.replace("login.html?expirou=1");
    }

    if (resp.status === 204) return null;
    const dados = await resp.json().catch(() => ({}));
    if (!resp.ok) {
        // Formato da API: {detail, codigo, request_id}. detail pode ser lista no formato antigo do FastAPI.
        const detalhe = Array.isArray(dados.detail)
            ? dados.detail.map((d) => String(d.msg || "").replace(/^Value error, /, "")).join("; ")
            : dados.detail;
        const erro = new Error(typeof detalhe === "string" && detalhe ? detalhe : "Erro ao falar com o servidor");
        erro.status = resp.status;
        erro.codigo = dados.codigo;
        throw erro;
    }
    return dados;
}

function usuarioLogado() {
    try {
        return JSON.parse(localStorage.getItem("usuario") || "null");
    } catch {
        return null;
    }
}

// O papel vem do token assinado (não do perfil salvo, que qualquer um edita no navegador).
// Isso só decide o que MOSTRAR: quem barra de verdade é o backend.
function ehAdmin() {
    const p = lerPayload(getToken() || "");
    return !!p && p.papel === "admin";
}
