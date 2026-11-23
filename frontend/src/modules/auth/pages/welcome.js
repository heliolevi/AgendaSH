// Quem já tem sessão válida vai direto para o início.
if (usuarioLogado() && getToken()) location.replace("index.html");
