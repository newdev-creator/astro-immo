import os

import cloudinary
import cloudinary.uploader

cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
)


async def upload_image(file_bytes: bytes, folder: str = "immo") -> str:
    result = cloudinary.uploader.upload(
        file_bytes,
        folder=folder,
        transformation=[
            {"width": 1200, "height": 800, "crop": "fill", "quality": "auto"}
        ],
    )
    return result["secure_url"]


async def delete_image(url: str) -> None:
    # Extrait le public_id depuis l'URL Cloudinary
    parts = url.split("/")
    public_id = (
        "/".join(parts[-2:])
        .replace(".jpg", "")
        .replace(".png", "")
        .replace(".webp", "")
    )
    cloudinary.uploader.destroy(public_id)
