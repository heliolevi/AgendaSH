// Início: próximo compromisso em destaque, régua de hoje e os próximos 7 dias agrupados por dia.
const usuario = exigirLogin();
$("nome").textContent = primeiroNome(usuario);
$("avatar").innerHTML = avatarHtml(usuario);
$("tHoje").textContent = "Hoje, " + dataLonga(new Date());
renderNav("inicio");

function textoContagem(x) {
    const agora = new Date();
    if (x.inicio <= agora) return { agora: true, texto: `Acontecendo agora · termina às ${horaDe(x.fim)}` };
    const min = minutosEntre(agora, x.inicio);
    if (min < 60) return { texto: `Começa em ${min} min` };
    if (min < 24 * 60) return { texto: `Começa em ${duracaoTexto(Math.round(min / 5) * 5)}` };
    return { texto: `${rotuloDia(x.inicio)}` };
}

function desenharDestaque(prox) {
    if (!prox) {
        $("destaque").innerHTML = `<div class="destaque">
            <p class="destaque-rotulo">${icone("check-circle")}Próximo compromisso</p>
            <h2>Agenda livre</h2>
            <p class="sub">Nada marcado para os próximos dias.</p>
            <a class="btn-pri espaco-topo" href="calendario.html#novo">${icone("calendar-plus")}Agendar</a>
        </div>`;
        return;
    }
    const c = textoContagem(prox);
    const multi = chaveDia(prox.inicio) !== chaveDia(prox.fim);
    $("destaque").innerHTML = `<article class="destaque">
        <p class="destaque-rotulo">${icone("clock")}${prox.tipo === "evento" ? "Próximo evento" : "Próxima reunião"} · ${esc(rotuloDia(prox.inicio))}</p>
        <h2>${esc(prox.titulo)}</h2>
        <p class="destaque-hora">${horaDe(prox.inicio)}<span>até</span>${multi ? esc(dataCurta(prox.fim)) + " " : ""}${horaDe(prox.fim)}</p>
        <p class="ag-meta">${icone(prox.sala && prox.sala.tipo === "Presencial" ? "map-pin" : "video-camera")}<span class="ag-local">${localHtml(prox.sala)}</span></p>
        <p class="destaque-conta${c.agora ? " agora" : ""}">${icone("hourglass-medium")}${esc(c.texto)}</p>
    </article>`;
}

function desenharLista(itens) {
    if (!itens.length) {
        $("lista").innerHTML = estadoVazio("Semana livre", "Você não tem reuniões nem eventos nos próximos 7 dias.", "calendario.html#novo", "Agendar agora");
        return;
    }
    $("lista").innerHTML = agruparPorDia(itens).map(([k, xs]) => {
        const d = deChave(k);
        return `<section class="dia-grupo" aria-label="${esc(dataLonga(d))}">
            <h3>${esc(rotuloDia(d))}${["Hoje", "Amanhã"].includes(rotuloDia(d)) ? `<span>${dataCurta(d)}</span>` : ""}</h3>
            <div class="lista">${xs.map((x) => cartaoAgenda(x, { acoes: true })).join("")}</div>
        </section>`;
    }).join("");
}

async function carregar() {
    try {
        const { minhas } = await carregarAgenda(usuario);
        const agora = new Date();
        const limite = new Date(); limite.setHours(0, 0, 0, 0); limite.setDate(limite.getDate() + 8);
        const futuras = minhas.filter((x) => x.fim > agora);
        const semana = futuras.filter((x) => x.inicio < limite);
        const hoje = minhas.filter((x) => chaveDia(x.inicio) <= chaveDia(agora) && chaveDia(x.fim) >= chaveDia(agora));
        const restantesHoje = hoje.filter((x) => x.fim > agora).length;

        $("resumoDia").textContent = restantesHoje
            ? `Você tem ${restantesHoje} compromisso${restantesHoje > 1 ? "s" : ""} ainda hoje.`
            : semana.length ? "Hoje está livre. Veja o que vem pela frente." : "Sua agenda está livre. Que tal marcar algo?";
        desenharDestaque(futuras[0]);
        desenharRegua($("reguaHoje"), { dia: agora, itens: hoje });
        desenharLista(semana);
    } catch (e) {
        $("resumoDia").textContent = "";
        $("lista").innerHTML = estadoErro(e.message);
    }
}

$("lista").addEventListener("click", async (e) => {
    const b = e.target.closest("[data-excluir]");
    if (b && (await excluirDoCartao(b))) carregar();
});

carregar();
setInterval(() => { if (!document.hidden) carregar(); }, 5 * 60 * 1000); // contagem regressiva e "agora" se atualizam sozinhos
