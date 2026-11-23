// Perfil: dados da conta, editar nome/e-mail, atalhos e sair.
let usuario = exigirLogin();
renderNav("perfil");

$("icUser").innerHTML = icone("user");
$("icEmail").innerHTML = icone("envelope-simple");
$("icDesde").innerHTML = icone("calendar-blank");
$("btnEditar").innerHTML = `${icone("pencil-simple")}<span>Editar perfil<small>Nome e e-mail institucional</small></span>${icone("caret-right", "ic seta")}`;
$("linkFixas").innerHTML = `${icone("repeat")}<span>Reuniões fixas<small>Séries semanais que você organiza</small></span>${icone("caret-right", "ic seta")}`;
$("linkTermos").innerHTML = `${icone("shield-check")}<span>Termos &amp; Privacidade<small>Quais dados guardamos e por quê</small></span>${icone("caret-right", "ic seta")}`;
$("btnSair").innerHTML = `${icone("sign-out")}<span>Sair da conta</span>`;

if (ehAdmin()) {
    $("linkFixas").insertAdjacentHTML("beforebegin",
        `<a class="acao" href="admin.html">${icone("users-three")}<span>Painel admin<small>Usuários e visão geral</small></span>${icone("caret-right", "ic seta")}</a>`);
}

function mostrar() {
    $("avatarGrande").innerHTML = avatarHtml(usuario, "grande");
    $("nome").textContent = primeiroNome(usuario);
    $("papel").innerHTML = ehAdmin() ? '<span class="selo">administrador</span>' : "Membro da Software House";
    $("pNome").textContent = usuario.nome;
    $("pEmail").textContent = usuario.email;
    $("pDesde").textContent = usuario.criado_em ? new Date(usuario.criado_em).toLocaleDateString("pt-BR", { day: "numeric", month: "long", year: "numeric" }) : "-";
}
mostrar();

// atualiza com o que está no servidor (ex.: "membro desde")
api("/usuarios/" + Number(usuario.id_usuario)).then((u) => { setSessao(null, u); usuario = usuarioLogado(); mostrar(); }).catch(() => {});

function alternarEdicao(abrir) {
    $("formPerfil").hidden = !abrir;
    $("btnEditar").setAttribute("aria-expanded", String(abrir));
    $("msgErro").textContent = "";
    if (abrir) { $("eNome").value = usuario.nome; $("eEmail").value = usuario.email; $("eNome").focus(); }
}
$("btnEditar").addEventListener("click", () => alternarEdicao($("formPerfil").hidden));
$("btnCancelarEd").addEventListener("click", () => { alternarEdicao(false); $("btnEditar").focus(); });

$("formPerfil").addEventListener("submit", async (e) => {
    e.preventDefault();
    const nome = $("eNome").value.trim(), email = $("eEmail").value.trim().toLowerCase();
    $("msgErro").textContent = "";
    if (!nome) { $("msgErro").textContent = "Informe seu nome."; return $("eNome").focus(); }
    if (!email) { $("msgErro").textContent = "Informe seu e-mail institucional."; return $("eEmail").focus(); }
    ocupado($("btnSalvar"), true, "Salvando…");
    try {
        const u = await api("/usuarios/" + Number(usuario.id_usuario), { method: "PUT", body: { nome, email } });
        setSessao(null, u);
        usuario = usuarioLogado();
        mostrar();
        alternarEdicao(false);
        avisar("Perfil atualizado.");
    } catch (err) {
        $("msgErro").textContent = err.message;
    } finally {
        ocupado($("btnSalvar"), false);
    }
});

$("btnSair").addEventListener("click", async () => {
    if (await confirmar({ titulo: "Sair da conta?", texto: "Você vai precisar entrar de novo com seu e-mail e senha.", ok: "Sair", cancelar: "Ficar" })) sair();
});
