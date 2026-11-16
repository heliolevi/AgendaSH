// Utilitários compartilhados pelas telas internas: guarda de login, navegação e leitura de reuniões.

function exigirLogin() {
    const u = usuarioLogado();
    if (!u || !getToken()) {
        limparSessao();
        location.href = "welcome.html";
    }
    return u;
}

function sair() {
    limparSessao();
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
    const g = (id, c1, c2) => `<linearGradient id="${id}" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="${c1}"/><stop offset="1" stop-color="${c2}"/></linearGradient>`;
    const S = (id) => `fill="none" stroke="url(#${id})" stroke-width="3.2" stroke-linejoin="round" stroke-linecap="round"`;
    const item = (id, href, rotulo, svg) =>
        `<a href="${href}" class="${ativo === id ? "ativo" : ""}">${svg}<span>${rotulo}</span></a>`;
    document.body.insertAdjacentHTML("beforeend", `
    <nav class="nav" aria-label="Navegação principal">
        ${item("inicio", "index.html", "Início", `<svg viewBox="0 0 32 32"><defs>${g("ni", "#22d3ee", "#6366f1")}</defs><path d="M16 5 L28 26 H4 Z" ${S("ni")}/></svg>`)}
        ${item("calendario", "calendario.html", "Calendário", `<svg viewBox="0 0 32 32"><defs>${g("nc", "#8b5cf6", "#22d3ee")}</defs><rect x="5.5" y="5.5" width="21" height="21" rx="4.5" ${S("nc")}/></svg>`)}
        <a class="mais" href="calendario.html" title="Nova reunião" aria-label="Nova reunião"><svg viewBox="0 0 40 40"><defs>${g("np", "#e040fb", "#22d3ee")}</defs><path d="M20 8v24M8 20h24" fill="none" stroke="url(#np)" stroke-width="3.6" stroke-linecap="round"/></svg></a>
        ${item("reunioes", "reunioes.html", "Reuniões", `<svg viewBox="0 0 32 32"><defs>${g("nr", "#6c7bff", "#22d3ee")}</defs><path d="M7 7l18 18M25 7L7 25" ${S("nr")}/></svg>`)}
        ${item("perfil", "perfil.html", "Configurações", `<svg viewBox="0 0 32 32"><defs>${g("ns", "#a78bfa", "#e040fb")}</defs><circle cx="16" cy="16" r="10.5" ${S("ns")}/></svg>`)}
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

const BADGE = `<img src="img/icon-192.png" alt="" width="42" height="42" loading="lazy">`;
const IC_RELOGIO = `<svg viewBox="0 0 24 24" fill="none" stroke="#a78bfa" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/></svg>`;
const IC_LOCAL = `<svg class="loc-ic" viewBox="0 0 24 24" fill="none" stroke="#22d3ee" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 21s7-6.2 7-11a7 7 0 1 0-14 0c0 4.8 7 11 7 11Z"/><circle cx="12" cy="10" r="2.6"/></svg>`;
const IC_LIXO = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 7h16M9 7V5h6v2M6 7l1 13h10l1-13"/></svg>`;

function cartaoReuniao(r, u, comExcluir = false) {
    const local = r.sala ? r.sala.localizacao_link || r.sala.nome : "Sem local";
    const modo = r.sala ? r.sala.tipo : "";
    const podeExcluir = comExcluir && r.id_usuario === u.id_usuario;
    return `<div class="reuniao">
        <div class="icone">${BADGE}</div>
        <div class="info">
            <h3>${esc(r.titulo)}</h3>
            <div class="linha">${IC_RELOGIO} ${dataCurta(r.inicio)} · ${horaDe(r.inicio)}</div>
            <div class="linha">${IC_LOCAL} ${esc(local)}${modo ? " (" + esc(modo) + ")" : ""}</div>
        </div>
        ${podeExcluir ? `<button class="excluir" data-id="${r.id_reuniao}" title="Cancelar reunião" aria-label="Cancelar reunião">${IC_LIXO}</button>` : ""}
    </div>`;
}

// ---- eventos ----
// Todos os eventos de hoje em diante (eventos são da equipe, não dependem de convite), com a sala anexada.
async function listarEventos() {
    const [eventos, salas] = await Promise.all([api("/eventos"), api("/salas")]);
    const porSala = Object.fromEntries(salas.map((s) => [s.id_sala, s]));
    return eventos
        .map((e) => ({ ...e, inicio: new Date(e.data_inicio), fim: new Date(e.data_fim), sala: porSala[e.id_sala] || null }))
        .sort((a, b) => a.inicio - b.inicio);
}

function cartaoEvento(e, u, comExcluir = false) {
    const local = e.sala ? e.sala.localizacao_link || e.sala.nome : "Sem local";
    const modo = e.sala ? e.sala.tipo : "";
    const podeExcluir = comExcluir && e.id_usuario === u.id_usuario;
    return `<div class="reuniao evento">
        <div class="icone">${BADGE}</div>
        <div class="info">
            <h3>${esc(e.titulo)} <span class="selo">evento</span></h3>
            <div class="linha">${IC_RELOGIO} ${dataCurta(e.inicio)} · ${horaDe(e.inicio)} às ${horaDe(e.fim)}</div>
            <div class="linha">${IC_LOCAL} ${esc(local)}${modo ? " (" + esc(modo) + ")" : ""}</div>
        </div>
        ${podeExcluir ? `<button class="excluir" data-tipo="evento" data-id="${e.id_eventos}" title="Cancelar evento" aria-label="Cancelar evento">${IC_LIXO}</button>` : ""}
    </div>`;
}

// ---- salas e datas ----
// As tabelas reuniao/eventos exigem uma sala. Modo + Local do formulário viram (ou reaproveitam) uma sala.
async function obterSala(modo, local) {
    const salas = await api("/salas");
    const existente = salas.find((s) => s.tipo === modo && (s.localizacao_link === local || s.nome === local));
    if (existente) return existente;
    return api("/salas", { method: "POST", body: { nome: local.slice(0, 100), capacidade: 10, tipo: modo, localizacao_link: local } });
}

const DIAS_SEMANA = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]; // 0 = segunda (igual ao backend)
