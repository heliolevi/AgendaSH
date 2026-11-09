// Utilitários compartilhados pelas telas internas: guarda de login, navegação e leitura de reuniões.

function exigirLogin() {
    const u = usuarioLogado();
    if (!u) location.href = "welcome.html";
    return u;
}

function sair() {
    localStorage.removeItem("usuario");
    location.href = "welcome.html";
}

function primeiroNome(u) {
    return (u.nome || "").trim().split(/\s+/)[0] || "";
}

function esc(texto) {
    const d = document.createElement("div");
    d.textContent = texto ?? "";
    return d.innerHTML;
}

const pad = (n) => String(n).padStart(2, "0");
const horaDe = (d) => pad(d.getHours()) + ":" + pad(d.getMinutes());
const dataCurta = (d) => pad(d.getDate()) + "/" + pad(d.getMonth() + 1);
const chaveDia = (d) => d.getFullYear() + "-" + pad(d.getMonth() + 1) + "-" + pad(d.getDate());

// ---- cabeçalho (avatar) e barra inferior ----
function avatarHtml(u, classe = "") {
    const ini = (u.nome || "?").trim().charAt(0).toUpperCase();
    return `<a class="avatar ${classe}" href="perfil.html" title="Perfil">${esc(ini)}</a>`;
}

function renderNav(ativo) {
    const stroke = (cor) => `fill="none" stroke="${cor}" stroke-width="3" stroke-linejoin="round" stroke-linecap="round"`;
    const item = (id, href, rotulo, svg) =>
        `<a href="${href}" class="${ativo === id ? "ativo" : ""}">${svg}<span>${rotulo}</span></a>`;
    document.body.insertAdjacentHTML("beforeend", `
    <nav class="nav">
        ${item("inicio", "index.html", "Início", `<svg viewBox="0 0 32 32"><path d="M16 5 L28 26 H4 Z" ${stroke("#22d3ee")}/></svg>`)}
        ${item("calendario", "calendario.html", "Calendário", `<svg viewBox="0 0 32 32"><rect x="5" y="5" width="22" height="22" rx="3" ${stroke("#8b5cf6")}/></svg>`)}
        <a class="mais" href="calendario.html" title="Nova reunião"><svg viewBox="0 0 40 40"><path d="M20 7v26M7 20h26" ${stroke("#e040fb")}/></svg></a>
        ${item("reunioes", "reunioes.html", "Reuniões", `<svg viewBox="0 0 32 32"><path d="M6 6l20 20M26 6L6 26" ${stroke("#6c7bff")}/></svg>`)}
        ${item("perfil", "perfil.html", "Configurações", `<svg viewBox="0 0 32 32"><circle cx="16" cy="16" r="11" ${stroke("#a78bfa")}/></svg>`)}
    </nav>`);
}

// ---- dados ----
// Reuniões em que o usuário é organizador ou convidado, com a sala anexada, ordenadas por início.
async function minhasReunioes(u) {
    const [reunioes, convites, salas] = await Promise.all([
        api("/reunioes"),
        api("/convites?id_usuario=" + u.id_usuario),
        api("/salas"),
    ]);
    const convidadas = new Set(convites.filter((c) => c.status_resposta !== "recusado").map((c) => c.id_reuniao));
    const porSala = Object.fromEntries(salas.map((s) => [s.id_sala, s]));
    return reunioes
        .filter((r) => r.id_usuario === u.id_usuario || convidadas.has(r.id_reuniao))
        .map((r) => ({ ...r, inicio: new Date(r.data_inicio), fim: new Date(r.data_fim), sala: porSala[r.id_sala] || null }))
        .sort((a, b) => a.inicio - b.inicio);
}

const ICONE_REUNIAO = `<svg viewBox="0 0 32 32" fill="none" stroke="#6f7dff" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round">
    <rect x="4" y="6" width="24" height="22" rx="4" fill="#3b3fd6"/><path d="M10 3v5M22 3v5M10 17l4 4 8-8" stroke="#fff"/></svg>`;

function cartaoReuniao(r, u, comExcluir = false) {
    const local = r.sala ? r.sala.localizacao_link || r.sala.nome : "Sem local";
    const modo = r.sala ? r.sala.tipo : "";
    const podeExcluir = comExcluir && r.id_usuario === u.id_usuario;
    return `<div class="reuniao">
        <div class="icone">${ICONE_REUNIAO}</div>
        <div class="info">
            <h3>${esc(r.titulo)}</h3>
            <div class="linha">🕒 ${dataCurta(r.inicio)} · ${horaDe(r.inicio)}</div>
            <div class="linha">📍 ${esc(local)}${modo ? " (" + esc(modo) + ")" : ""}</div>
        </div>
        ${podeExcluir ? `<button class="excluir" data-id="${r.id_reuniao}" title="Cancelar reunião">🗑</button>` : ""}
    </div>`;
}
