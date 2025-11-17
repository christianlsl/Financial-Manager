from __future__ import annotations

"""
Qiniu image upload helper.

Reads configuration from app.core.config.settings (backed by config.yaml),
compresses input image to be <= max_size, uploads to Qiniu, and returns the
public URL of the uploaded image.

Usage:
	from .upload_to_qiniu import upload_image_bytes
	url = upload_image_bytes(data_bytes, filename="example.png")
"""

import io
import uuid
from typing import Tuple

from PIL import Image  # type: ignore
from qiniu import Auth, put_data  # type: ignore

try:
	from ..core.config import settings
except Exception:  # Allow running as a script without package context
	import sys
	import pathlib

	sys.path.append(str(pathlib.Path(__file__).resolve().parents[2]))
	from app.core.config import settings  # type: ignore


class QiniuUploadError(Exception):
	pass


def _ensure_qiniu_auth() -> Auth:
	access_key = settings.QINIU_ACCESS_KEY
	secret_key = settings.QINIU_SECRET_KEY
	bucket = settings.QINIU_BUCKET
	domain = settings.QINIU_DOMAIN
	if not (access_key and secret_key and bucket and domain):
		raise QiniuUploadError("七牛云未配置，请在config.yaml中填写uploads.qiniu相关配置")
	return Auth(access_key, secret_key)


def _compress_to_limit(data: bytes, max_bytes: int) -> Tuple[bytes, str]:
	"""Compress image bytes to JPEG <= max_bytes (best effort), returns (bytes, ext)."""
	if not data:
		raise QiniuUploadError("未接收到图片内容")
	try:
		with Image.open(io.BytesIO(data)) as img:
			image = img.convert("RGB")
	except Exception as exc:
		raise QiniuUploadError("无法解析图片文件") from exc

	# Hard minimum to avoid infinite loops with tiny limits
	target = max(10 * 1024, int(max_bytes))
	quality = 90
	width, height = image.size

	while True:
		buf = io.BytesIO()
		image.save(buf, format="JPEG", quality=quality, optimize=True)
		size = buf.tell()
		if size <= target or (quality <= 40 and max(width, height) <= 512):
			return buf.getvalue(), "jpg"
		if quality > 50:
			quality -= 10
		else:
			width = max(1, int(width * 0.9))
			height = max(1, int(height * 0.9))
			image = image.resize((width, height), Image.LANCZOS)


def _build_object_key(filename: str | None, ext: str) -> str:
	base = settings.QINIU_BASE_PATH.strip("/") if getattr(settings, "QINIU_BASE_PATH", "") else "sales-images"
	uid = uuid.uuid4().hex
	ext = (ext or "jpg").lstrip(".")
	prefix = f"{base}/" if base else ""
	return f"{prefix}{uid}.{ext}"


def upload_image_bytes(data: bytes, filename: str | None = None) -> str:
	"""Compress and upload image bytes to Qiniu. Returns the public URL."""
	auth = _ensure_qiniu_auth()
	bucket = settings.QINIU_BUCKET
	domain = settings.QINIU_DOMAIN.rstrip("/")
	max_bytes = getattr(settings, "UPLOAD_MAX_SIZE_BYTES", 500 * 1024)

	compressed, ext = _compress_to_limit(data, max_bytes)
	key = _build_object_key(filename, ext)
	token = auth.upload_token(bucket, key, 3600)
	ret, info = put_data(token, key, compressed)
	if info.status_code not in (200, 201) or not ret:
		print(f"上传失败: {info}, 返回值: {ret}")
		raise QiniuUploadError("七牛云上传失败，请稍后重试")
	return f"{domain}/{key}"


def _cli() -> int:
	import argparse
	import os
	import sys

	parser = argparse.ArgumentParser(description="Upload an image file to Qiniu and print its URL.")
	parser.add_argument("path",default="~/projects2/ffsubsync.png", help="Path to the image file")
	args = parser.parse_args()

	file_path = args.path
	if not os.path.isfile(file_path):
		print(f"文件不存在: {file_path}", file=sys.stderr)
		return 2
	try:
		with open(file_path, "rb") as f:
			data = f.read()
		url = upload_image_bytes(data, filename=os.path.basename(file_path))
		print(url)
		return 0
	except QiniuUploadError as e:
		print(f"上传失败: {e}", file=sys.stderr)
		return 1
	except Exception as e:  # pragma: no cover - safety
		print(f"发生错误: {e}", file=sys.stderr)
		return 1


if __name__ == "__main__":
	raise SystemExit(_cli())

