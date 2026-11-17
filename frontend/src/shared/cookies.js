// Aviso de cookies/armazenamento. O app usa localStorage só para login e preferências.
(function () {
    const CHAVE = "agendash_cookies_ok";
    if (localStorage.getItem(CHAVE)) return;
    const el = document.createElement("div");
    el.className = "cookies";
    el.setAttribute("role", "dialog");
    el.setAttribute("aria-label", "Aviso de cookies");
    el.innerHTML =
        '<p>Guardamos dados no seu navegador apenas para manter seu login e preferências. ' +
        'Veja os <a href="termos.html">Termos &amp; Privacidade</a>.</p>' +
        '<button type="button" id="cookiesOk">Aceitar</button>';
    document.body.appendChild(el);
    document.getElementById("cookiesOk").addEventListener("click", () => {
        localStorage.setItem(CHAVE, "1");
        el.remove();
    });
})();
