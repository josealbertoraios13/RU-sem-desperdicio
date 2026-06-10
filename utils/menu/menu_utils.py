"""
    Utilitários para validação de imagens do cardápio.
"""

from fastapi import HTTPException

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


class MenuUtils:
    @staticmethod
    def validate_image_extension(filename: str) -> str:
        """Valida a extensão do arquivo e retorna a extensão normalizada."""
        if not filename:
            raise HTTPException(
                status_code=400,
                detail={"msg": "Nome do arquivo é obrigatório"}
            )

        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail={
                    "msg": f"Formato inválido. Aceitos: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
                }
            )

        # Normaliza jpeg para jpg
        return "jpg" if ext == "jpeg" else ext

    @staticmethod
    def validate_image_size(file_size: int) -> None:
        """Valida o tamanho do arquivo."""
        if file_size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail={
                    "msg": f"Arquivo muito grande. Máximo: {MAX_FILE_SIZE // (1024*1024)}MB"
                }
            )
