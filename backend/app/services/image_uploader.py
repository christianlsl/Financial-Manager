from __future__ import annotations

import io
import uuid
from dataclasses import dataclass

from PIL import Image
from qiniu import Auth, put_data  # type: ignore

from ..core.config import settings


class ImageUploadError(Exception):
    """Raised when an image cannot be processed or uploaded."""


@dataclass
class _QiniuConfig:
    access_key: str
    secret_key: str
    bucket: str
    domain: str
    base_path: str


class ImageUploader:
    def __init__(self) -> None:
        self._max_bytes = settings.UPLOAD_MAX_SIZE_BYTES
        self._config = _QiniuConfig(
            access_key=settings.QINIU_ACCESS_KEY,
            secret_key=settings.QINIU_SECRET_KEY,
            bucket=settings.QINIU_BUCKET,
            domain=settings.QINIU_DOMAIN,
            base_path=settings.QINIU_BASE_PATH,
        )
        self._auth: Auth | None = None

    def _ensure_configured(self) -> None:
        if not all(
            [
                self._config.access_key,
                self._config.secret_key,
                self._config.bucket,
                self._config.domain,
            ]
        ):
            raise ImageUploadError("七牛云未配置，请检查config.yaml中的uploads配置")
        if self._auth is None:
            self._auth = Auth(self._config.access_key, self._config.secret_key)

    def _compress_image(self, data: bytes) -> tuple[bytes, str]:
        try:
            with Image.open(io.BytesIO(data)) as img:
                image = img.convert("RGB")
        except Exception as exc:  # pragma: no cover - invalid files
            raise ImageUploadError("无法解析上传的图片文件") from exc

        max_bytes = max(10 * 1024, self._max_bytes)
        quality = 90
        width, height = image.size

        while True:
            buffer = io.BytesIO()
            image.save(buffer, format="JPEG", quality=quality, optimize=True)
            size = buffer.tell()
            if size <= max_bytes or (quality <= 40 and max(width, height) <= 512):
                return buffer.getvalue(), "jpg"
            if quality > 50:
                quality -= 10
            else:
                width = max(1, int(width * 0.9))
                height = max(1, int(height * 0.9))
                image = image.resize((width, height), Image.LANCZOS)

    def _build_key(self, filename: str | None, ext: str) -> str:
        safe_ext = ext.lower().lstrip(".") or "jpg"
        uid = uuid.uuid4().hex
        base = self._config.base_path.strip("/")
        prefix = f"{base}/" if base else ""
        return f"{prefix}{uid}.{safe_ext}"

    def upload(self, data: bytes, filename: str | None = None) -> str:
        if not data:
            raise ImageUploadError("未接收到图片内容")
        self._ensure_configured()
        compressed, ext = self._compress_image(data)
        key = self._build_key(filename, ext)
        assert self._auth is not None  # for type checker
        token = self._auth.upload_token(self._config.bucket, key, 3600)
        ret, info = put_data(token, key, compressed)
        if info.status_code not in (200, 201) or not ret:
            raise ImageUploadError("七牛云上传失败，请稍后重试")
        domain = self._config.domain.rstrip("/")
        return f"{domain}/{key}"


uploader = ImageUploader()
