// Utilitários compartilhados pelas telas internas: guarda de login, navegação, dados da agenda,
// componentes (cartão, régua do dia, diálogo, aviso) e formatação de datas.
// Regra de segurança: todo texto vindo da API passa por esc() antes de entrar em innerHTML.

function exigirLogin() {
    const u = usuarioLogado();
    if (!u || !getToken()) {
        limparSessao();
        location.replace("login.html");
        throw new Error("sem sessão"); // interrompe o script da página
    }
    return u;
}

function sair() {
    limparSessao();
    location.replace("welcome.html");
}

function primeiroNome(u) {
    return String(u.nome || "").trim().split(/\s+/)[0] || "";
}

function esc(texto) {
    return String(texto ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

const $ = (id) => document.getElementById(id);

// ---------------------------------------------------------------- datas
const pad = (n) => String(n).padStart(2, "0");
const horaDe = (d) => pad(d.getHours()) + ":" + pad(d.getMinutes());
const dataCurta = (d) => pad(d.getDate()) + "/" + pad(d.getMonth() + 1);
const chaveDia = (d) => d.getFullYear() + "-" + pad(d.getMonth() + 1) + "-" + pad(d.getDate());
const deChave = (k) => { const [a, m, d] = k.split("-").map(Number); return new Date(a, m - 1, d); };
const MESES = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"];
const DIAS_SEMANA = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]; // 0 = segunda (igual ao backend)
const DIAS_CURTOS = ["dom", "seg", "ter", "qua", "qui", "sex", "sáb"]; // índice de Date.getDay()

function minutosEntre(a, b) { return Math.round((b - a) / 60000); }

function duracaoTexto(min) {
    if (min < 60) return min + " min";
    if (min >= 24 * 60) {
        const dias = Math.floor(min / 1440), resto = min % 1440;
        const txt = dias + (dias > 1 ? " dias" : " dia");
        return resto ? `${txt} e ${duracaoTexto(resto)}` : txt;
    }
    const h = Math.floor(min / 60), m = min % 60;
    return m ? `${h}h${pad(m)}` : `${h}h`;
}

function rotuloDia(d) {
    const hoje = new Date(); hoje.setHours(0, 0, 0, 0);
    const alvo = new Date(d); alvo.setHours(0, 0, 0, 0);
    const dif = Math.round((alvo - hoje) / 86400000);
    if (dif === 0) return "Hoje";
    if (dif === 1) return "Amanhã";
    if (dif === -1) return "Ontem";
    return `${DIAS_CURTOS[d.getDay()]}, ${d.getDate()} de ${MESES[d.getMonth()].slice(0, 3)}`;
}

function dataLonga(d) {
    return `${DIAS_SEMANA[(d.getDay() + 6) % 7].toLowerCase()}, ${d.getDate()} de ${MESES[d.getMonth()]}`;
}

// "2026-11-26T09:30:00" (horário local, sem fuso: é assim que o banco guarda)
function paraIsoLocal(d) {
    return `${chaveDia(d)}T${pad(d.getHours())}:${pad(d.getMinutes())}:00`;
}

function juntarDataHora(chave, hhmm) {
    const d = deChave(chave);
    const [h, m] = hhmm.split(":").map(Number);
    d.setHours(h, m, 0, 0);
    return d;
}

// ---------------------------------------------------------------- links seguros
// Só http(s) vira link clicável. Qualquer outra coisa (javascript:, data:, texto solto) é mostrada como texto.
function urlSegura(texto) {
    try {
        const u = new URL(String(texto).trim());
        return u.protocol === "https:" || u.protocol === "http:" ? u : null;
    } catch {
        return null;
    }
}

function localHtml(sala) {
    if (!sala) return "Sem local";
    const bruto = sala.localizacao_link || sala.nome;
    const u = urlSegura(bruto);
    if (!u) return esc(bruto);
    const curto = (u.host + u.pathname).replace(/\/$/, "");
    return `<a href="${esc(u.href)}" target="_blank" rel="noopener noreferrer" title="${esc(u.href)}">${esc(curto.length > 38 ? curto.slice(0, 37) + "…" : curto)}</a>`;
}

// ---------------------------------------------------------------- shell: avatar, pular-para-conteúdo, navegação
function avatarHtml(u, classe = "") {
    const ini = String(u.nome || "?").trim().charAt(0).toUpperCase();
    return `<a class="avatar ${classe}" href="perfil.html" aria-label="Abrir perfil de ${esc(u.nome)}"><span aria-hidden="true">${esc(ini)}</span></a>`;
}

function renderNav(ativo) {
    document.body.classList.add("com-nav");
    if (!document.querySelector(".pular")) {
        document.body.insertAdjacentHTML("afterbegin", '<a class="pular" href="#conteudo">Pular para o conteúdo</a>');
    }
    // símbolos do controle (△ ○ × □) são a assinatura visual do AgendaSH
    const g = (id, c1, c2) => `<linearGradient id="${id}" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="${c1}"/><stop offset="1" stop-color="${c2}"/></linearGradient>`;
    const S = (id) => `fill="none" stroke="url(#${id})" stroke-width="3.2" stroke-linejoin="round" stroke-linecap="round"`;
    const item = (id, href, rotulo, svg) =>
        `<a href="${href}" class="nav-item${ativo === id ? " ativo" : ""}"${ativo === id ? ' aria-current="page"' : ""}><svg viewBox="0 0 32 32" aria-hidden="true">${svg}</svg><span>${rotulo}</span></a>`;
    document.body.insertAdjacentHTML("beforeend", `
    <nav class="nav" aria-label="Navegação principal">
        <a class="nav-marca" href="index.html" aria-label="AgendaSH, início"><img src="img/logo-sh.webp" alt="" width="40" height="40"><span>AgendaSH</span></a>
        ${item("inicio", "index.html", "Início", `<defs>${g("ni", "#22d3ee", "#6366f1")}</defs><path d="M16 5 L28 26 H4 Z" ${S("ni")}/>`)}
        ${item("calendario", "calendario.html", "Calendário", `<defs>${g("nc", "#8b5cf6", "#22d3ee")}</defs><rect x="5.5" y="5.5" width="21" height="21" rx="4.5" ${S("nc")}/>`)}
        <a class="mais" href="calendario.html#novo" aria-label="Novo agendamento"><svg viewBox="0 0 40 40" aria-hidden="true"><defs>${g("np", "#e040fb", "#22d3ee")}</defs><path d="M20 8v24M8 20h24" fill="none" stroke="url(#np)" stroke-width="3.6" stroke-linecap="round"/></svg><span>Novo agendamento</span></a>
        ${item("reunioes", "reunioes.html", "Agenda", `<defs>${g("nr", "#6c7bff", "#22d3ee")}</defs><path d="M7 7l18 18M25 7L7 25" ${S("nr")}/>`)}
        ${item("perfil", "perfil.html", "Perfil", `<defs>${g("ns", "#a78bfa", "#e040fb")}</defs><circle cx="16" cy="16" r="10.5" ${S("ns")}/>`)}
    </nav>`);
}

// ---------------------------------------------------------------- avisos (toast) e diálogo de confirmação
function avisar(texto, tipo = "ok") {
    let area = document.querySelector(".avisos");
    if (!area) {
        area = document.createElement("div");
        area.className = "avisos";
        area.setAttribute("role", "status");
        area.setAttribute("aria-live", "polite");
        document.body.appendChild(area);
    }
    const el = document.createElement("div");
    el.className = "aviso aviso-" + tipo;
    el.innerHTML = icone(tipo === "erro" ? "warning-circle" : "check-circle") + `<span>${esc(texto)}</span>`;
    area.appendChild(el);
    setTimeout(() => { el.classList.add("saindo"); setTimeout(() => el.remove(), 260); }, tipo === "erro" ? 6000 : 3800);
}

// Substitui o confirm() do navegador: acessível, com foco no botão seguro e Esc para fechar.
function confirmar({ titulo, texto = "", ok = "Confirmar", cancelar = "Voltar", perigo = false }) {
    return new Promise((resolver) => {
        const dlg = document.createElement("dialog");
        dlg.className = "dlg";
        dlg.setAttribute("aria-labelledby", "dlgTitulo");
        dlg.innerHTML = `
            <form method="dialog">
                <h2 id="dlgTitulo">${esc(titulo)}</h2>
                ${texto ? `<p>${esc(texto)}</p>` : ""}
                <div class="dlg-acoes">
                    <button class="btn-sec" value="nao" type="submit">${esc(cancelar)}</button>
                    <button class="btn-pri${perigo ? " perigo" : ""}" value="sim" type="submit">${esc(ok)}</button>
                </div>
            </form>`;
        document.body.appendChild(dlg);
        dlg.addEventListener("close", () => { resolver(dlg.returnValue === "sim"); dlg.remove(); });
        dlg.addEventListener("click", (e) => { if (e.target === dlg) dlg.close("nao"); }); // clicar fora fecha
        dlg.showModal();
        dlg.querySelector('[value="nao"]').focus();
    });
}

// Botão com estado de carregando (evita clique duplo e mostra que algo está acontecendo)
function ocupado(botao, sim, rotulo) {
    if (!botao) return;
    if (sim) {
        botao.dataset.rotulo = botao.textContent;
        botao.disabled = true;
        botao.classList.add("carregando");
        botao.setAttribute("aria-busy", "true");
        if (rotulo) botao.textContent = rotulo;
    } else {
        botao.disabled = false;
        botao.classList.remove("carregando");
        botao.removeAttribute("aria-busy");
        if (botao.dataset.rotulo) botao.textContent = botao.dataset.rotulo;
    }
}

function esqueleto(n = 3) {
    return `<div class="esqueleto" aria-hidden="true">${'<div class="esq-linha"></div>'.repeat(n)}</div><span class="sr">Carregando…</span>`;
}

function estadoVazio(titulo, texto, href, acao) {
    return `<div class="vazio">${icone("calendar-blank", "ic vazio-ic")}<h3>${esc(titulo)}</h3>${texto ? `<p>${esc(texto)}</p>` : ""}${href ? `<a class="btn-sec" href="${href}">${esc(acao)}</a>` : ""}</div>`;
}

function estadoErro(msg) {
    return `<div class="vazio erro" role="alert">${icone("warning-circle", "ic vazio-ic")}<h3>Não deu para carregar</h3><p>${esc(msg)}</p><button class="btn-sec" type="button" data-recarregar>Tentar de novo</button></div>`;
}
document.addEventListener("click", (e) => { if (e.target.closest("[data-recarregar]")) location.reload(); });

// ---------------------------------------------------------------- dados da agenda
// Junta reuniões e eventos num formato só. `minhas` = o que aparece na agenda do usuário
// (reuniões que organiza ou para as quais foi convidado + todos os eventos da equipe).
// `ocupacoes` = tudo que ocupa alguma sala (usado para avisar conflito antes de enviar).
async function carregarAgenda(u) {
    const [reunioes, eventos, convites, salas] = await Promise.all([
        api("/reunioes"),
        api("/eventos"),
        api("/convites?id_usuario=" + encodeURIComponent(u.id_usuario)),
        api("/salas"),
    ]);
    const convidadas = new Set(convites.filter((c) => c.status_resposta !== "recusado").map((c) => c.id_reuniao));
    const porSala = Object.fromEntries(salas.map((s) => [s.id_sala, s]));
    const admin = ehAdmin();
    const norm = (x, tipo) => ({
        tipo,
        id: tipo === "evento" ? x.id_eventos : x.id_reuniao,
        titulo: x.titulo,
        descricao: x.descricao,
        id_sala: x.id_sala,
        sala: porSala[x.id_sala] || null,
        id_usuario: x.id_usuario,
        inicio: new Date(x.data_inicio),
        fim: new Date(x.data_fim),
        organizo: x.id_usuario === u.id_usuario,
        podeEditar: x.id_usuario === u.id_usuario || admin,
    });
    const todas = [...reunioes.map((r) => norm(r, "reuniao")), ...eventos.map((e) => norm(e, "evento"))]
        .sort((a, b) => a.inicio - b.inicio);
    const minhas = todas.filter((x) => x.tipo === "evento" || x.organizo || convidadas.has(x.id));
    return { todas, minhas, salas, porSala };
}

function agruparPorDia(itens) {
    const grupos = new Map();
    for (const x of itens) {
        const k = chaveDia(x.inicio);
        if (!grupos.has(k)) grupos.set(k, []);
        grupos.get(k).push(x);
    }
    return [...grupos.entries()];
}

// As tabelas reuniao/eventos exigem uma sala. Modo + Local do formulário viram (ou reaproveitam) uma sala.
function acharSala(salas, modo, local) {
    const alvo = local.trim().toLowerCase();
    return salas.find((s) => s.tipo === modo && [s.localizacao_link, s.nome].some((v) => String(v || "").trim().toLowerCase() === alvo)) || null;
}

async function obterSala(modo, local, salas) {
    const lista = salas || (await api("/salas"));
    const existente = acharSala(lista, modo, local);
    if (existente) return existente;
    return api("/salas", { method: "POST", body: { nome: local.slice(0, 100), capacidade: 10, tipo: modo, localizacao_link: local } });
}

// ---------------------------------------------------------------- cartão de compromisso
function cartaoAgenda(x, { acoes = false, mostrarDia = false } = {}) {
    const min = minutosEntre(x.inicio, x.fim);
    const multiDia = chaveDia(x.inicio) !== chaveDia(x.fim);
    const agora = new Date();
    const aoVivo = x.inicio <= agora && x.fim > agora;
    const modo = x.sala ? x.sala.tipo : "";
    const tipoNome = x.tipo === "evento" ? "Evento" : "Reunião";
    const papel = x.tipo === "evento" ? (x.organizo ? "Você criou" : "Equipe") : (x.organizo ? "Você organiza" : "Convidado");
    const fimTxt = multiDia ? `${dataCurta(x.fim)} ${horaDe(x.fim)}` : horaDe(x.fim);
    const fimHtml = multiDia ? `<span>${horaDe(x.fim)}</span><small class="ag-ate">até ${dataCurta(x.fim)}</small>` : `<span>${horaDe(x.fim)}</span>`;
    return `<article class="ag ag-${x.tipo}${aoVivo ? " ao-vivo" : ""}" data-tipo="${x.tipo}" data-id="${Number(x.id)}">
        <div class="ag-hora" aria-label="Das ${horaDe(x.inicio)} às ${fimTxt}">
            ${mostrarDia ? `<small>${esc(rotuloDia(x.inicio))}</small>` : ""}
            <b>${horaDe(x.inicio)}</b>${fimHtml}
        </div>
        <div class="ag-corpo">
            <p class="ag-tipo"><i class="ponto" aria-hidden="true"></i>${tipoNome}${aoVivo ? ' <em class="vivo">agora</em>' : ""}</p>
            <h3>${esc(x.titulo)}</h3>
            <p class="ag-meta">${icone(modo === "Online" ? "video-camera" : "map-pin")}<span class="ag-local">${localHtml(x.sala)}</span></p>
            <p class="ag-meta suave">${icone("hourglass-medium")}<span>${duracaoTexto(min)} · ${papel}</span></p>
            ${x.descricao ? `<p class="ag-desc">${esc(x.descricao)}</p>` : ""}
        </div>
        ${acoes && x.podeEditar ? `<div class="ag-acoes">
            <a class="icone-btn" href="calendario.html?editar=${x.tipo}-${Number(x.id)}" aria-label="Editar ${esc(tipoNome.toLowerCase())} ${esc(x.titulo)}">${icone("pencil-simple")}</a>
            <button class="icone-btn perigo" type="button" data-excluir aria-label="Cancelar ${esc(tipoNome.toLowerCase())} ${esc(x.titulo)}">${icone("trash")}</button>
        </div>` : ""}
    </article>`;
}

// Cancela um compromisso a partir do botão [data-excluir] de um cartão. Devolve true se apagou.
async function excluirDoCartao(botao) {
    const card = botao.closest(".ag");
    const evento = card.dataset.tipo === "evento";
    const titulo = card.querySelector("h3").textContent;
    const sim = await confirmar({
        titulo: evento ? "Cancelar este evento?" : "Cancelar esta reunião?",
        texto: `"${titulo}" sai da agenda de todo mundo. Isso não pode ser desfeito.`,
        ok: evento ? "Cancelar evento" : "Cancelar reunião",
        cancelar: "Manter",
        perigo: true,
    });
    if (!sim) return false;
    ocupado(botao, true);
    try {
        await api((evento ? "/eventos/" : "/reunioes/") + Number(card.dataset.id), { method: "DELETE" });
        avisar(evento ? "Evento cancelado." : "Reunião cancelada.");
        return true;
    } catch (e) {
        avisar(e.message, "erro");
        ocupado(botao, false);
        return false;
    }
}

// ---------------------------------------------------------------- régua do dia
// Faixa horizontal do dia: blocos dos seus compromissos, faixas hachuradas onde o local escolhido
// já está ocupado e o colchete do horário que você está marcando (vermelho se bater com algo).
// Montada com DOM + element.style (permitido pela CSP, ao contrário de style="" em HTML).
function desenharRegua(alvo, { dia, itens = [], ocupados = [], proposta = null, aoEscolherHora = null }) {
    const ini0 = deChave(chaveDia(dia));
    const fimDia = new Date(ini0.getTime() + 86400000);
    const recorta = (x) => ({ ...x, a: Math.max(x.inicio, ini0), b: Math.min(x.fim, fimDia) });
    const visiveis = [...itens, ...ocupados, ...(proposta ? [proposta] : [])].filter((x) => x.fim > ini0 && x.inicio < fimDia).map(recorta);
    let hMin = 7, hMax = 22;
    for (const x of visiveis) {
        hMin = Math.min(hMin, new Date(x.a).getHours());
        hMax = Math.max(hMax, Math.ceil((x.b - ini0) / 3600000));
    }
    hMax = Math.min(24, Math.max(hMax, hMin + 4));
    const total = (hMax - hMin) * 60;
    const pos = (d) => Math.max(0, Math.min(100, ((d - ini0) / 60000 - hMin * 60) / total * 100));

    alvo.textContent = "";
    alvo.className = "regua";
    const faixa = document.createElement("div");
    faixa.className = "regua-faixa";
    const bloco = (x, classe, rotulo) => {
        const el = document.createElement("div");
        el.className = "regua-bloco " + classe;
        el.style.left = pos(x.a) + "%";
        el.style.width = Math.max(1.2, pos(x.b) - pos(x.a)) + "%";
        el.title = rotulo;
        faixa.appendChild(el);
    };
    for (const o of ocupados.filter((x) => x.fim > ini0 && x.inicio < fimDia).map(recorta)) bloco(o, "ocupado", `Local ocupado ${horaDe(o.inicio)}–${horaDe(o.fim)}`);
    for (const x of itens.filter((x) => x.fim > ini0 && x.inicio < fimDia).map(recorta)) bloco(x, "b-" + x.tipo, `${x.titulo} ${horaDe(x.inicio)}–${horaDe(x.fim)}`);
    if (proposta && proposta.fim > proposta.inicio) bloco(recorta(proposta), "proposta" + (proposta.conflito ? " conflito" : ""), "Horário escolhido");

    const agora = new Date();
    if (agora > ini0 && agora < fimDia && agora.getHours() >= hMin && agora.getHours() < hMax) {
        const linha = document.createElement("div");
        linha.className = "regua-agora";
        linha.style.left = pos(agora) + "%";
        faixa.appendChild(linha);
    }
    if (aoEscolherHora) {
        faixa.classList.add("clicavel");
        faixa.title = "Clique para começar neste horário";
        faixa.addEventListener("click", (e) => {
            const r = faixa.getBoundingClientRect();
            const min = hMin * 60 + ((e.clientX - r.left) / r.width) * total;
            const arred = Math.min(23 * 60 + 30, Math.max(0, Math.round(min / 30) * 30));
            aoEscolherHora(pad(Math.floor(arred / 60)) + ":" + pad(arred % 60));
        });
    }
    const horas = document.createElement("div");
    horas.className = "regua-horas";
    horas.setAttribute("aria-hidden", "true");
    const passo = hMax - hMin > 12 ? 3 : 2;
    for (let h = hMin; h <= hMax; h += passo) {
        const s = document.createElement("span");
        s.textContent = pad(h % 24) + "h";
        s.style.left = ((h - hMin) * 60 / total * 100) + "%";
        horas.appendChild(s);
    }
    alvo.append(faixa, horas);
    const resumo = itens.length ? `${itens.length} compromisso(s) neste dia` : "Dia livre";
    alvo.setAttribute("role", "img");
    alvo.setAttribute("aria-label", `Régua do dia, das ${hMin}h às ${hMax}h. ${resumo}.`);
}
