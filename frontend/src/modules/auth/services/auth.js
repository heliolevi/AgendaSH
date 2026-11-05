const msg = document.getElementById("msgErro");

const formLogin = document.getElementById("formLogin");
if (formLogin) formLogin.addEventListener("submit", entrar);

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
        const email = document.getElementById("cadEmail").value.trim();
        const senha = document.getElementById("cadSenha").value;
        if (!nome) return (msg.textContent = "Informe seu nome");
        if (!email) return (msg.textContent = "Informe seu e-mail");
        if (senha.length < 6) return (msg.textContent = "Senha precisa de no mínimo 6 caracteres");
        try {
            await api("/usuarios", { method: "POST", body: { nome, email, senha } });
            // já entra direto após criar a conta
            const usuario = await api("/auth/login", { method: "POST", body: { email, senha } });
            localStorage.setItem("usuario", JSON.stringify(usuario));
            location.href = "index.html";
        } catch (erro) {
            msg.textContent = erro.message;
        }
    });
}

// Recuperar senha: a API ainda não tem rota para isso (precisa de envio de e-mail/token).
const formRecuperar = document.getElementById("formRecuperar");
if (formRecuperar) {
    formRecuperar.addEventListener("submit", (e) => {
        e.preventDefault();
        const nova = document.getElementById("recSenha").value;
        if (nova.length < 6) return (msg.textContent = "Senha precisa de no mínimo 6 caracteres");
        if (nova !== document.getElementById("recConfirma").value) return (msg.textContent = "As senhas não conferem");
        msg.textContent = "Recuperação de senha ainda não disponível nesta versão. Fale com o administrador.";
    });
}
