import os

from fastapi import APIRouter, Depends, File, HTTPException, Security, UploadFile
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from services import MenuService
from utils import logger

router = APIRouter(prefix="/menu", tags=["menu"])
menu_service = MenuService()
security = HTTPBearer(auto_error=False)


def verify_admin_token(credentials: HTTPAuthorizationCredentials = Security(security)) -> str:
    """Verifica se o token de autenticacao e valido para operacoes admin."""
    admin_key = os.getenv("ADMIN_API_KEY")

    if not admin_key:
        logger.warning("ADMIN_API_KEY not configured - menu upload endpoint disabled")
        raise HTTPException(
            status_code=503,
            detail="Upload de cardapio nao configurado. Contate o administrador.",
        )

    if not credentials or credentials.credentials != admin_key:
        raise HTTPException(
            status_code=401,
            detail="Token de autenticacao invalido ou ausente",
        )

    return "admin"


@router.post("/upload")
async def upload_menu_image(
    file: UploadFile | None = File(None),
    dinner_file: UploadFile | None = File(None),
    lunch_file: UploadFile | None = File(None),
    _admin: str = Depends(verify_admin_token),
):
    """
    Upload do cardapio da semana (PNG/JPG). Rota protegida por ADMIN_API_KEY.

    - **file**: Imagem principal do cardapio/almoco (PNG ou JPG, max 10MB)
    - **dinner_file**: Imagem opcional do cardapio do jantar (PNG ou JPG, max 10MB)
    """
    primary_file = file or lunch_file
    if not primary_file or not primary_file.filename:
        raise HTTPException(status_code=400, detail="Arquivo e obrigatorio")

    primary_content = await primary_file.read()

    try:
        if not dinner_file:
            result = menu_service.upload_menu_image(
                file_content=primary_content,
                filename=primary_file.filename,
            )
            return result

        if not dinner_file.filename:
            raise HTTPException(status_code=400, detail="Imagem do jantar e obrigatoria")

        dinner_content = await dinner_file.read()
        result = menu_service.upload_weekly_menu_images(
            lunch_file_content=primary_content,
            lunch_filename=primary_file.filename,
            dinner_file_content=dinner_content,
            dinner_filename=dinner_file.filename,
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro no upload de cardapio: {e}")
        raise HTTPException(
            status_code=500,
            detail="Erro interno ao fazer upload do cardapio",
        )


@router.get("/current")
async def get_current_menu():
    """
    Retorna o cardapio mais recente. Rota publica.
    Retorna 404 se nenhum cardapio existir.
    """
    return menu_service.get_current_menu()


@router.get("/image/{menu_id}")
async def get_menu_image(menu_id: int):
    """
    Serve a imagem do almoco pelo ID. Rota publica mantida por compatibilidade.
    """
    asset = menu_service.get_menu_image_access(menu_id)
    if asset.get("backend") == "s3":
        return RedirectResponse(url=asset["url"], status_code=307)
    return FileResponse(asset["path"], media_type=asset["media_type"])


@router.get("/image/{menu_id}/{meal_type}")
async def get_menu_meal_image(menu_id: int, meal_type: str):
    """
    Serve a imagem do cardapio pelo ID e tipo de refeicao: lunch/almoco ou dinner/jantar.
    """
    asset = menu_service.get_menu_image_access(menu_id, meal_type=meal_type)
    if asset.get("backend") == "s3":
        return RedirectResponse(url=asset["url"], status_code=307)
    return FileResponse(asset["path"], media_type=asset["media_type"])
