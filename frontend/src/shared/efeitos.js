// Animações leves e OPCIONAIS (progressive enhancement). Não pré-escondem nada quando as libs
// não carregam (sem cartão invisível) e não baixam nada se o usuário pediu menos movimento.
// Subset proposital: GSAP (entrada + toque) + Motion One (revela no scroll) + Lenis (scroll suave).
// Libs HOSPEDADAS LOCALMENTE em vendor/ (sem CDN: não dependem de rede nem são bloqueadas por adblock).
// Sem Three.js/Spline/Framer/shadcn para não pesar o site.
(function () {
    if (matchMedia("(prefers-reduced-motion: reduce)").matches) return;

    function carregar(src) {
        return new Promise((ok, falhou) => {
            const s = document.createElement("script");
            s.src = src; s.defer = true; s.onload = ok; s.onerror = falhou;
            document.head.appendChild(s);
        });
    }

    Promise.allSettled([
        carregar("vendor/gsap.min.js"),
        carregar("vendor/motion.min.js"),
        carregar("vendor/lenis.min.js"),
    ]).then(() => {
        // GSAP: entrada em cascata das seções (uma vez) + micro-interação de toque
        if (window.gsap) {
            const alvos = document.querySelectorAll(
                ".auth-marca, .auth-cartao, .secao, .cal, .form-reuniao, .form-fixa, .boas-vindas, .logo, .hero-badge, .admin-cards"
            );
            if (alvos.length) {
                gsap.from(alvos, { opacity: 0, y: 12, duration: 0.45, stagger: 0.05, ease: "power2.out", clearProps: "all" });
            }
            document.querySelectorAll(".btn, .mini, .aba, .nav a, .btn-fixas, .acao").forEach((b) => {
                b.addEventListener("pointerdown", () => gsap.to(b, { scale: 0.96, duration: 0.08 }));
                const volta = () => gsap.to(b, { scale: 1, duration: 0.18, ease: "power2.out" });
                b.addEventListener("pointerup", volta);
                b.addEventListener("pointerleave", volta);
            });
        }

        // Motion One: revela cartões com uma mola conforme entram na tela.
        // Só esconde se a lib carregou (se falhar no CDN, os cartões ficam visíveis normalmente).
        const M = window.Motion;
        if (M && M.inView && M.animate) {
            const cartoes = document.querySelectorAll(".reuniao, .painel, .admin-user");
            cartoes.forEach((el) => {
                el.style.opacity = "0";
                M.inView(el, () => {
                    M.animate(
                        el,
                        { opacity: [0, 1], transform: ["translateY(14px) scale(.98)", "none"] },
                        { duration: 0.55, easing: M.spring ? M.spring({ stiffness: 240, damping: 26 }) : "ease-out" }
                    );
                    return () => {};
                }, { margin: "0px 0px -8% 0px" });
            });
            // rede de segurança: se algo falhar no reveal, nada fica invisível
            setTimeout(() => cartoes.forEach((el) => {
                if (getComputedStyle(el).opacity === "0") el.style.opacity = "1";
            }), 1600);
        }

        // Lenis: scroll suave quando a página realmente rola
        if (window.Lenis) {
            const lenis = new window.Lenis({ duration: 1.0, smoothWheel: true, wheelMultiplier: 0.9 });
            const raf = (t) => { lenis.raf(t); requestAnimationFrame(raf); };
            requestAnimationFrame(raf);
        }
    });
})();
