const msg = document.getElementById("msgErro");

const formLogin = document.getElementById("formLogin");
if (formLogin) {
    formLogin.addEventListener("submit", entrar);
    document.getElementById("btnLogin").addEventListener("click", entrar);
}

async function entrar(e) {
    e.preventDefault();
    msg.textContent = "";
    try {
        const usuario = await api("/auth/login", {
            method: "POST",
            body: {
                email: document.getElementById("loginUsuario").value.trim(),
                senha: document.getElementById("loginSenha").value,
            },
        });
        localStorage.setItem("usuario", JSON.stringify(usuario));
        location.href = "index.html";
    } catch (erro) {
        msg.textContent = erro.message;
    }
}

const formCadastro = document.getElementById("formCadastro");
if (formCadastro) {
    formCadastro.addEventListener("submit", async (e) => {
        e.preventDefault();
        msg.textContent = "";
        const nome = document.getElementById("cadUsuario").value.trim();
        const senha = document.getElementById("cadSenha").value;
        if (nome.length < 4) return (msg.textContent = "Usuário precisa de no mínimo 4 caracteres");
        if (senha.length < 6) return (msg.textContent = "Senha precisa de no mínimo 6 caracteres");
        if (senha !== document.getElementById("cadConfirma").value) return (msg.textContent = "As senhas não conferem");
        try {
            await api("/usuarios", {
                method: "POST",
                body: { nome, email: document.getElementById("cadEmail").value.trim(), senha },
            });
            location.href = "login.html";
        } catch (erro) {
            msg.textContent = erro.message;
        }
    });
}
