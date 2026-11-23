// "Voltar" volta para a página anterior quando houver uma; senão, vai para a entrada.
document.getElementById("voltar").addEventListener("click", (e) => {
    if (history.length > 1) { e.preventDefault(); history.back(); }
});
