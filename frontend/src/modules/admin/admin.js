// Painel admin: contadores e gestão de usuários. O backend exige papel 'admin' em todas as rotas /admin.
const usuario = exigirLogin();
$("avatar").innerHTML = avatarHtml(usuario);
renderNav("perfil");

if (!ehAdmin()) {
    $("bloqueado").hidden = false;
    $("bloqueado").insertAdjacentHTML("afterbegin", icone("shield-check", "ic vazio-ic"));
} else {
    $("conteudoAdmin").hidden = false;
    carregar();
}

async function carregar() {
    try {
        const [resumo, usuarios] = await Promise.all([api("/admin/resumo"), api("/admin/usuarios")]);
        $("resumo").innerHTML = [
            ["Usuários", resumo.usuarios],
            ["Reuniões", resumo.reunioes],
            ["Salas e locais", resumo.salas],
            ["Convites", resumo.convites],
        ].map(([r, n]) => `<div class="admin-card"><b>${Number(n) || 0}</b><span>${r}</span></div>`).join("");
        $("listaUsuarios").innerHTML = usuarios.length ? usuarios.map(cartaoUsuario).join("") : estadoVazio("Nenhum usuário", "");
    } catch (e) {
        $("listaUsuarios").innerHTML = estadoErro(e.message);
    }
}

function cartaoUsuario(us) {
    const admin = us.papel === "admin";
    const souEu = us.id_usuario === usuario.id_usuario;
    return `<article class="admin-user" data-id="${Number(us.id_usuario)}" data-nome="${esc(us.nome)}">
        <div class="admin-user-info">
            <h3>${esc(us.nome)} ${admin ? '<span class="selo">admin</span>' : ""}${souEu ? '<span class="selo">você</span>' : ""}</h3>
            <p>${esc(us.email)}</p>
        </div>
        <div class="admin-user-acoes">
            <button class="btn-sec" type="button" data-acao="papel" data-papel="${admin ? "membro" : "admin"}" ${souEu ? "disabled" : ""}>${admin ? "Tornar membro" : "Tornar admin"}</button>
            <button class="btn-sec perigo" type="button" data-acao="remover" ${souEu ? "disabled" : ""}>Excluir</button>
        </div>
    </article>`;
}

$("listaUsuarios").addEventListener("click", async (ev) => {
    const b = ev.target.closest("button[data-acao]");
    if (!b || b.disabled) return;
    const card = b.closest(".admin-user");
    const id = Number(card.dataset.id), nome = card.dataset.nome;
    const remover = b.dataset.acao === "remover";
    const sim = await confirmar(remover
        ? { titulo: "Excluir este usuário?", texto: `A conta de ${nome} será apagada. Isso não pode ser desfeito.`, ok: "Excluir conta", cancelar: "Manter", perigo: true }
        : { titulo: b.dataset.papel === "admin" ? "Tornar administrador?" : "Tirar acesso de administrador?", texto: `${nome} ${b.dataset.papel === "admin" ? "poderá gerenciar usuários e ver o painel admin." : "volta a ser membro comum."}`, ok: "Confirmar" });
    if (!sim) return;
    ocupado(b, true);
    try {
        if (remover) await api("/admin/usuarios/" + id, { method: "DELETE" });
        else await api("/admin/usuarios/" + id, { method: "PATCH", body: { papel: b.dataset.papel } });
        avisar(remover ? "Usuário excluído." : "Papel atualizado.");
        carregar();
    } catch (e) {
        avisar(e.message, "erro");
        ocupado(b, false);
    }
});
