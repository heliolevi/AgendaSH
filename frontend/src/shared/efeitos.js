// Movimento leve e OPCIONAL (progressive enhancement): um único momento de entrada por tela
// e um retorno tátil ao tocar nos botões. Nada fica escondido se a biblioteca não carregar,
// e nada roda se o sistema pedir menos movimento.
// Lenis (scroll suave) e Motion One saíram: o scroll suave atrapalhava o painel fixo do
// formulário no PC e o "revelar ao rolar" escondia cartões que chegam depois da API.
// Os arquivos continuam em vendor/ caso a equipe queira voltar com eles.
(function () {
    if (matchMedia("(prefers-reduced-motion: reduce)").matches) return;

    const s = document.createElement("script");
    s.src = "vendor/gsap.min.js";
    s.defer = true;
    s.onload = () => {
        if (!window.gsap) return;
        const alvos = document.querySelectorAll(
            ".topo, .grade-inicio > *, .grade-agendar > *, .grade-fixas > *, .estreita > *, .admin-cards, .auth-marca, .auth-cartao, .logo, .boas-vindas, .perfil-cabeca"
        );
        if (alvos.length) {
            gsap.from(alvos, { opacity: 0, y: 10, duration: 0.4, stagger: 0.05, ease: "power2.out", clearProps: "opacity,transform" });
        }
        // retorno tátil (delegado: vale também para botões criados depois)
        document.addEventListener("pointerdown", (e) => {
            const b = e.target.closest(".btn, .btn-pri, .btn-sec, .chip, .nav-item, .mais, .icone-btn");
            if (!b || b.disabled) return;
            gsap.to(b, { scale: 0.97, duration: 0.08 });
            const volta = () => { gsap.to(b, { scale: 1, duration: 0.2, ease: "power2.out", clearProps: "transform" }); b.removeEventListener("pointerup", volta); b.removeEventListener("pointerleave", volta); };
            b.addEventListener("pointerup", volta);
            b.addEventListener("pointerleave", volta);
        });
    };
    document.head.appendChild(s);
})();
