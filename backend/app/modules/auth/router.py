from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, Field, field_validator

from app.core.auth import criar_token
from app.core.database import get_conn
from app.core.email_policy import validar_email_undb
from app.core.email_sender import EmailNaoEnviado, enviar_codigo
from app.core.security import hash_senha, verificar_senha
from app.core import throttle
from app.modules.usuarios import repository as usuarios_repo
from app.modules.usuarios.schemas import UsuarioOut
from app.modules.verificacao import service as codigos

router = APIRouter(prefix="/auth", tags=["auth"])

MSG_CODIGO_ENVIADO = "Enviamos um codigo de 6 digitos para o seu e-mail."
MSG_CODIGO_SENHA = "Se o e-mail estiver cadastrado, enviamos um codigo de 6 digitos para ele."


class LoginIn(BaseModel):
    email: str
    senha: str


class LoginOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    usuario: UsuarioOut


class CodigoCadastroIn(BaseModel):
    email: str = Field(max_length=100)

    @field_validator("email")
    @classmethod
    def email_da_undb(cls, v: str) -> str:
        return validar_email_undb(v)[0]  # mesma regra do cadastro; ja volta em minusculas


class EsqueciSenhaIn(BaseModel):
    email: str = Field(max_length=100)


class RedefinirSenhaIn(BaseModel):
    email: str = Field(max_length=100)
    codigo: str = Field(pattern=r"^\d{6}$")
    nova_senha: str = Field(min_length=6, max_length=128)


def _enviar(email: str, codigo: str, finalidade: str) -> None:
    try:
        enviar_codigo(email, codigo, finalidade, codigos.VALIDADE_MIN)
    except EmailNaoEnviado as e:
        raise HTTPException(503, e.publico)


def _enviar_sem_erro(email: str, codigo: str, finalidade: str) -> None:
    try:
        enviar_codigo(email, codigo, finalidade, codigos.VALIDADE_MIN)
    except EmailNaoEnviado:
        pass  # ja registrado no log por email_sender


def _autenticar(conn, email: str, senha: str, request: Request) -> dict:
    """Confere e-mail/senha com protecao anti forca-bruta. Devolve o usuario ou levanta 401/429."""
    ip = request.client.host if request.client else "desconhecido"
    chave = f"{ip}|{(email or '').strip().lower()}"
    espera = throttle.segundos_de_bloqueio(chave)
    if espera:
        raise HTTPException(429, f"Muitas tentativas de login. Tente novamente em {espera // 60 + 1} min.")
    usuario = usuarios_repo.buscar_por_email(conn, email)
    if not usuario or not verificar_senha(senha, usuario["senha_hash"]):
        throttle.registrar_falha(chave)
        raise HTTPException(401, "E-mail ou senha invalidos")
    throttle.limpar(chave)
    return usuario


def _token_do_usuario(usuario: dict) -> str:
    return criar_token(
        usuario["id_usuario"], usuario.get("papel", "membro"),
        nome=usuario["nome"], email=usuario["email"],
    )


@router.post("/login", response_model=LoginOut)
def login(dados: LoginIn, request: Request, conn=Depends(get_conn)):
    """Login do app: devolve o token e os dados do usuario (sem a senha)."""
    usuario = _autenticar(conn, dados.email, dados.senha, request)
    return {"access_token": _token_do_usuario(usuario), "token_type": "bearer", "usuario": usuario}


@router.post("/token")
def token(request: Request, form: OAuth2PasswordRequestForm = Depends(), conn=Depends(get_conn)):
    """Compativel com o botao 'Authorize' do /docs (OAuth2 password flow). username = e-mail."""
    usuario = _autenticar(conn, form.username, form.password, request)
    return {"access_token": _token_do_usuario(usuario), "token_type": "bearer"}


@router.post("/cadastro/enviar-codigo")
def enviar_codigo_cadastro(dados: CodigoCadastroIn, conn=Depends(get_conn)):
    """Passo 1 do cadastro: manda o codigo para o e-mail institucional. Sem ele, POST /usuarios recusa."""
    if usuarios_repo.buscar_por_email(conn, dados.email):
        raise HTTPException(409, "E-mail ja cadastrado")
    codigo = codigos.emitir(conn, dados.email, "cadastro")
    _enviar(dados.email, codigo, "cadastro")  # se o envio falhar, a requisicao desfaz o codigo gravado
    return {"detail": MSG_CODIGO_ENVIADO, "expira_em_minutos": codigos.VALIDADE_MIN}


@router.post("/esqueci-senha")
def esqueci_senha(dados: EsqueciSenhaIn, tarefas: BackgroundTasks, conn=Depends(get_conn)):
    """Manda o codigo para o e-mail da conta. A resposta e a mesma exista a conta ou nao."""
    email = dados.email.strip().lower()
    codigo = codigos.emitir(conn, email, "senha")  # limite de envios vale para qualquer e-mail (nao revela contas)
    if usuarios_repo.buscar_por_email(conn, email):
        # em segundo plano: a resposta (conteudo e tempo) fica igual para e-mail existente ou nao, e falha de SMTP
        # nao revela que a conta existe (o motivo vai para o log)
        tarefas.add_task(_enviar_sem_erro, email, codigo, "senha")
    return {"detail": MSG_CODIGO_SENHA, "expira_em_minutos": codigos.VALIDADE_MIN}


@router.post("/redefinir-senha")
def redefinir_senha(dados: RedefinirSenhaIn, conn=Depends(get_conn)):
    """Troca a senha com o codigo recebido por e-mail (vale 10 min, uso unico, 5 tentativas)."""
    email = dados.email.strip().lower()
    codigos.validar(conn, email, "senha", dados.codigo)
    usuario = usuarios_repo.buscar_por_email(conn, email)
    if not usuario:
        raise HTTPException(400, "Codigo invalido ou expirado.")
    usuarios_repo.atualizar_senha(conn, usuario["id_usuario"], hash_senha(dados.nova_senha))
    return {"detail": "Senha alterada. Entre com a nova senha."}
