"""Política de e-mail institucional da UNDB (tarefa T6).

Só entram dois tipos de e-mail:

  ALUNO        002-02NNNN...@aluno.undb.edu.br   (matrícula começando com 002-02, domínio EXATO)
  PROFESSOR/   nome.sobrenome@undb.edu.br        (domínio EXATO; local começa com letra)
  COLABORADOR

Tudo que não casar é recusado: Gmail, Outlook, Yahoo, outros domínios e e-mails de golpe.

Defesas contra e-mail de golpe (cada uma tem teste em tests/test_email_policy.py):
  1. Comparação do domínio por IGUALDADE, nunca "contém"/"termina com":
     `undb.edu.br.golpe.net`, `xundb.edu.br` e `evil.undb.edu.br` são recusados.
  2. Só ASCII: bloqueia letras parecidas de outros alfabetos (ex.: "у" cirílico no lugar de "y")
     e `xn--` (punycode) no domínio.
  3. Exatamente um "@"; sem espaço, quebra de linha, vírgula, `<` `>` ou aspas
     (bloqueia `a@undb.edu.br,hacker@gmail.com`, `"x@gmail.com"@undb.edu.br` e injeção de cabeçalho).
  4. Parte local por regex restrita (`fullmatch`, sem `+tag`, sem pontos duplicados).
  5. Domínio sem ponto final (`undb.edu.br.`) e tamanho máximo de 100 (limite da coluna no banco).

Isto prova que o endereço *tem o formato* da UNDB. Quem prova que a pessoa *recebe* naquela
caixa é o código de confirmação por e-mail (T9/T13). As duas coisas juntas fecham a verificação.

Configuração (variáveis de ambiente, com padrão da UNDB):
  EMAIL_DOMINIO_ALUNO        padrão aluno.undb.edu.br
  EMAIL_PREFIXO_ALUNO        padrão 002-02
  EMAIL_DOMINIOS_PROFESSOR   padrão undb.edu.br   (lista separada por vírgula)
"""
import os
import re

TAMANHO_MAX = 100  # coluna usuario.email é VARCHAR(100)

MSG_FORMATO = "E-mail inválido."
MSG_NAO_UNDB = (
    "Use seu e-mail institucional da UNDB: "
    "002-02XXXXXX@aluno.undb.edu.br (aluno) ou nome@undb.edu.br (professor/colaborador)."
)

# Parte local de professor/colaborador: começa com letra; letras, números e separadores . _ - (sem repetir).
_LOCAL_PROFESSOR = re.compile(r"[a-z][a-z0-9]*(?:[._-][a-z0-9]+)*")
# Rótulos do domínio: letras/números/hífen, sem começar nem terminar com hífen.
_DOMINIO = re.compile(r"(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}")


def _config() -> tuple[str, str, frozenset[str]]:
    dominio_aluno = os.getenv("EMAIL_DOMINIO_ALUNO", "aluno.undb.edu.br").strip().lower()
    prefixo_aluno = os.getenv("EMAIL_PREFIXO_ALUNO", "002-02").strip()
    professores = os.getenv("EMAIL_DOMINIOS_PROFESSOR", "undb.edu.br")
    dominios = frozenset(d.strip().lower() for d in professores.split(",") if d.strip())
    return dominio_aluno, prefixo_aluno, dominios


def validar_email_undb(email: str) -> tuple[str, str]:
    """Valida e normaliza (minúsculas). Retorna (email, tipo) com tipo 'aluno' ou 'professor'.
    Levanta ValueError com mensagem pronta para o usuário."""
    if not isinstance(email, str):
        raise ValueError(MSG_FORMATO)
    email = email.strip().lower()

    # Barreiras gerais, antes de olhar o domínio (itens 2, 3 e 5 do cabeçalho).
    if not email or len(email) > TAMANHO_MAX or not email.isascii() or email.count("@") != 1:
        raise ValueError(MSG_FORMATO)
    if re.search(r"[\s,;<>()\[\]\\\"'`]", email):
        raise ValueError(MSG_FORMATO)

    local, dominio = email.split("@")
    if not local or not _DOMINIO.fullmatch(dominio) or "xn--" in dominio:
        raise ValueError(MSG_FORMATO)

    dominio_aluno, prefixo_aluno, dominios_professor = _config()

    # Item 1: igualdade exata do domínio.
    if dominio == dominio_aluno:
        if re.fullmatch(re.escape(prefixo_aluno) + r"\d{1,10}", local):
            return email, "aluno"
        raise ValueError(f"E-mail de aluno deve começar com {prefixo_aluno} (ex.: {prefixo_aluno}1234@{dominio_aluno}).")

    if dominio in dominios_professor:
        if _LOCAL_PROFESSOR.fullmatch(local):
            return email, "professor"
        raise ValueError(MSG_FORMATO)

    raise ValueError(MSG_NAO_UNDB)
