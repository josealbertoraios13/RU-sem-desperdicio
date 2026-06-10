import os
import uuid
from pathlib import Path
from typing import Protocol

from fastapi import HTTPException

from smartru.paths import PROJECT_ROOT, UPLOADS_MENU_DIR, WRITABLE_UPLOADS_MENU_DIR
from smartru.repository import MenuRepository
from smartru.services.service import Service
from smartru.utils import MenuUtils, logger


class MenuStorageProvider(Protocol):
    def save(self, file_content: bytes, original_filename: str, ext: str) -> tuple[str, Path | None]:
        ...

    def resolve_access(self, image_url: str) -> dict | None:
        ...

    def cleanup_orphan(self, image_url: str, file_path: Path | None) -> None:
        ...


class LocalMenuStorageProvider:
    def __init__(self, upload_dir: Path) -> None:
        self.upload_dir = upload_dir

    @staticmethod
    def _is_allowed_local_path(upload_dir: Path, path: Path) -> bool:
        allowed_roots = [
            upload_dir.resolve(),
            WRITABLE_UPLOADS_MENU_DIR.resolve(),
            PROJECT_ROOT.resolve(),
        ]
        return any(path == root or path.is_relative_to(root) for root in allowed_roots)

    def _resolve_local_image_path(self, image_url: str) -> Path | None:
        path = Path(image_url)
        if path.is_absolute():
            resolved_path = path.resolve()
            if resolved_path.exists() and self._is_allowed_local_path(self.upload_dir, resolved_path):
                return resolved_path
            return None

        candidates = [
            self.upload_dir / image_url,
            WRITABLE_UPLOADS_MENU_DIR / image_url,
            PROJECT_ROOT / image_url,
        ]
        for candidate in candidates:
            resolved_candidate = candidate.resolve()
            if resolved_candidate.exists() and self._is_allowed_local_path(self.upload_dir, resolved_candidate):
                return resolved_candidate
        return None

    def save(self, file_content: bytes, original_filename: str, ext: str) -> tuple[str, Path | None]:
        unique_filename = f"{uuid.uuid4().hex}.{ext}"
        upload_dirs = [self.upload_dir]
        if self.upload_dir != WRITABLE_UPLOADS_MENU_DIR:
            upload_dirs.append(WRITABLE_UPLOADS_MENU_DIR)

        last_error: OSError | None = None
        for upload_dir in upload_dirs:
            file_path = upload_dir / unique_filename
            try:
                os.makedirs(upload_dir, exist_ok=True)
                with open(file_path, "wb") as f:
                    f.write(file_content)
            except OSError as exc:
                last_error = exc
                logger.warning(f"Falha ao gravar imagem em '{upload_dir}': {exc}")
                continue

            image_url = unique_filename if upload_dir == self.upload_dir else str(file_path)
            return image_url, file_path

        logger.error(f"Falha ao gravar imagem localmente: {last_error}")
        raise HTTPException(
            status_code=422,
            detail="Falha ao gravar a imagem no disco. Verifique permissões do servidor.",
        )

    def resolve_access(self, image_url: str) -> dict | None:
        local_path = self._resolve_local_image_path(image_url)
        if not local_path:
            return None
        ext = local_path.suffix.lower()
        media_type = "image/jpeg" if ext in (".jpg", ".jpeg") else "image/png"
        return {"backend": "local", "path": str(local_path), "media_type": media_type}

    def cleanup_orphan(self, image_url: str, file_path: Path | None) -> None:
        if file_path and file_path.exists():
            try:
                os.remove(file_path)
            except OSError:
                logger.warning(f"Falha ao remover arquivo órfão: {file_path}")


class S3MenuStorageProvider:
    def __init__(self) -> None:
        self.bucket = os.getenv("AWS_S3_BUCKET")
        self.prefix = os.getenv("AWS_S3_PREFIX", "menus").strip("/")
        try:
            self.expires_in = int(os.getenv("AWS_S3_PRESIGNED_EXPIRES", "900"))
        except ValueError:
            logger.warning("AWS_S3_PRESIGNED_EXPIRES inválido; usando 900 segundos.")
            self.expires_in = 900

    @staticmethod
    def _guess_content_type(filename: str) -> str:
        ext = Path(filename).suffix.lower()
        return "image/png" if ext == ".png" else "image/jpeg"

    @staticmethod
    def _build_s3_client():
        import boto3

        region = os.getenv("AWS_REGION")
        if not region:
            raise HTTPException(status_code=503, detail="AWS_REGION não configurado")
        return boto3.client("s3", region_name=region)

    def get_presigned_url(self, object_key: str) -> str:
        if not self.bucket:
            raise HTTPException(status_code=503, detail="AWS_S3_BUCKET não configurado")
        try:
            client = self._build_s3_client()
            return client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket, "Key": object_key},
                ExpiresIn=self.expires_in,
            )
        except HTTPException:
            raise
        except Exception as exc:
            logger.error(f"Erro ao gerar URL pré-assinada S3: {exc}")
            raise HTTPException(status_code=500, detail="Falha ao gerar URL da imagem")

    def save(self, file_content: bytes, original_filename: str, ext: str) -> tuple[str, Path | None]:
        if not self.bucket:
            raise HTTPException(status_code=503, detail="AWS_S3_BUCKET não configurado")

        unique_filename = f"{uuid.uuid4().hex}.{ext}"
        object_key = f"{self.prefix}/{unique_filename}" if self.prefix else unique_filename

        try:
            client = self._build_s3_client()
            client.put_object(
                Bucket=self.bucket,
                Key=object_key,
                Body=file_content,
                ContentType=self._guess_content_type(original_filename),
            )
        except HTTPException:
            raise
        except Exception as exc:
            logger.error(f"Erro ao enviar imagem para S3: {exc}")
            raise HTTPException(status_code=500, detail="Falha ao enviar imagem para storage S3")

        return object_key, None

    def resolve_access(self, image_url: str) -> dict | None:
        is_explicit_local = image_url.startswith(("/", "volumes/", "tmp/", "uploads/", "./", "../"))
        if is_explicit_local:
            return None
        return {"backend": "s3", "url": self.get_presigned_url(image_url)}

    def cleanup_orphan(self, image_url: str, file_path: Path | None) -> None:
        if not self.bucket:
            return
        try:
            client = self._build_s3_client()
            client.delete_object(Bucket=self.bucket, Key=image_url)
        except Exception:
            logger.warning(f"Falha ao remover objeto órfão no S3: {image_url}")


class MenuService(Service):
    def __init__(self) -> None:
        self.menu_repository = MenuRepository()
        self.upload_dir = UPLOADS_MENU_DIR

    @staticmethod
    def _storage_backend() -> str:
        return os.getenv("STORAGE_BACKEND", "local").strip().lower()

    def _build_storage_provider(self, backend: str) -> MenuStorageProvider:
        if backend == "s3":
            return S3MenuStorageProvider()
        return LocalMenuStorageProvider(upload_dir=self.upload_dir)

    def _get_s3_presigned_url(self, object_key: str) -> str:
        return S3MenuStorageProvider().get_presigned_url(object_key)

    def _save_menu_asset(
        self,
        storage_provider: MenuStorageProvider,
        file_content: bytes,
        filename: str,
    ) -> tuple[str, Path | None]:
        ext = MenuUtils.validate_image_extension(filename)
        MenuUtils.validate_image_size(len(file_content))
        return storage_provider.save(
            file_content=file_content,
            original_filename=filename,
            ext=ext,
        )

    def upload_menu_image(
        self,
        file_content: bytes,
        filename: str,
        uploaded_by: int | None = None,
    ) -> dict:
        ext = MenuUtils.validate_image_extension(filename)
        MenuUtils.validate_image_size(len(file_content))
        backend = self._storage_backend()
        storage_provider = self._build_storage_provider(backend)

        image_url, file_path = storage_provider.save(
            file_content=file_content,
            original_filename=filename,
            ext=ext,
        )

        try:
            result = self.menu_repository.save_menu(
                image_url=str(image_url),
                filename=filename,
                uploaded_by=uploaded_by,
            )

            if not result.get("success"):
                storage_provider.cleanup_orphan(image_url=image_url, file_path=file_path)
                raise HTTPException(
                    status_code=result.get("code", 500),
                    detail=result.get("msg", "Falha ao salvar registro no banco"),
                )

            return self.handle_response(response=result)
        except Exception:
            storage_provider.cleanup_orphan(image_url=image_url, file_path=file_path)
            raise

    def upload_weekly_menu_images(
        self,
        lunch_file_content: bytes,
        lunch_filename: str,
        dinner_file_content: bytes,
        dinner_filename: str,
        uploaded_by: int | None = None,
    ) -> dict:
        backend = self._storage_backend()
        storage_provider = self._build_storage_provider(backend)
        saved_assets: list[tuple[str, Path | None]] = []

        try:
            lunch_image_url, lunch_file_path = self._save_menu_asset(
                storage_provider=storage_provider,
                file_content=lunch_file_content,
                filename=lunch_filename,
            )
            saved_assets.append((lunch_image_url, lunch_file_path))

            dinner_image_url, dinner_file_path = self._save_menu_asset(
                storage_provider=storage_provider,
                file_content=dinner_file_content,
                filename=dinner_filename,
            )
            saved_assets.append((dinner_image_url, dinner_file_path))

            result = self.menu_repository.save_menu(
                image_url=str(lunch_image_url),
                filename=lunch_filename,
                lunch_image_url=str(lunch_image_url),
                lunch_filename=lunch_filename,
                dinner_image_url=str(dinner_image_url),
                dinner_filename=dinner_filename,
                uploaded_by=uploaded_by,
            )

            if not result.get("success"):
                raise HTTPException(
                    status_code=result.get("code", 500),
                    detail=result.get("msg", "Falha ao salvar registro no banco"),
                )

            return self.handle_response(response=result)
        except Exception:
            for image_url, file_path in saved_assets:
                storage_provider.cleanup_orphan(image_url=image_url, file_path=file_path)
            raise

    def get_current_menu(self) -> dict:
        result = self.menu_repository.get_current_menu()
        return self._with_menu_image_metadata(self.handle_response(response=result))

    def get_menu_by_id(self, menu_id: int) -> dict:
        result = self.menu_repository.get_menu_by_id(menu_id)
        return self._with_menu_image_metadata(self.handle_response(response=result))

    @staticmethod
    def _normalize_meal_type(meal_type: str) -> str:
        normalized = meal_type.strip().lower()
        if normalized in {"lunch", "almoco"}:
            return "lunch"
        if normalized in {"dinner", "jantar"}:
            return "dinner"
        raise HTTPException(status_code=400, detail="Tipo de refeicao invalido")

    @staticmethod
    def _with_menu_image_metadata(response: dict) -> dict:
        menu = response.get("data")
        if not isinstance(menu, dict):
            return response

        menu_id = menu.get("id")
        lunch_image_url = menu.get("lunch_image_url") or menu.get("image_url")
        lunch_filename = menu.get("lunch_filename") or menu.get("filename")
        dinner_image_url = menu.get("dinner_image_url")
        dinner_filename = menu.get("dinner_filename")

        menu["images"] = {
            "lunch": {
                "label": "almoco",
                "image_url": lunch_image_url,
                "filename": lunch_filename,
                "image_endpoint": f"/api/menu/image/{menu_id}/lunch" if menu_id and lunch_image_url else None,
            },
            "dinner": {
                "label": "jantar",
                "image_url": dinner_image_url,
                "filename": dinner_filename,
                "image_endpoint": f"/api/menu/image/{menu_id}/dinner" if menu_id and dinner_image_url else None,
            },
        }
        return response

    def _resolve_image_access(self, image_url: str) -> dict:
        local_provider = LocalMenuStorageProvider(upload_dir=self.upload_dir)
        local_asset = local_provider.resolve_access(image_url)
        if local_asset:
            return local_asset

        backend = self._storage_backend()
        is_explicit_local = image_url.startswith(("/", "volumes/", "tmp/", "uploads/", "./", "../"))
        is_s3_candidate = "/" in image_url and not is_explicit_local

        if backend == "s3" or is_s3_candidate:
            return {"backend": "s3", "url": self._get_s3_presigned_url(image_url)}

        raise HTTPException(status_code=404, detail="Arquivo de imagem nao encontrado no servidor")

    def get_menu_image_access(self, menu_id: int, meal_type: str = "lunch") -> dict:
        result = self.get_menu_by_id(menu_id)
        menu = result.get("data", {})
        normalized_meal_type = self._normalize_meal_type(meal_type)
        if normalized_meal_type == "dinner":
            image_url = menu.get("dinner_image_url")
        else:
            image_url = menu.get("lunch_image_url") or menu.get("image_url")
        if not image_url:
            raise HTTPException(status_code=404, detail="Arquivo de imagem não encontrado")

        return self._resolve_image_access(image_url)
