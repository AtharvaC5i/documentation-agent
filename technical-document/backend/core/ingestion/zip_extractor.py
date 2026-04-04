import os
import zipfile
import io
from fastapi import UploadFile


async def extract_zip(upload_file: UploadFile, dest: str) -> None:
    """
    Reads an uploaded zip file and extracts its contents to the destination directory.
    Handles nested top-level folder flattening automatically.
    """
    os.makedirs(dest, exist_ok=True)
    content = await upload_file.read()

    with zipfile.ZipFile(io.BytesIO(content)) as zf:
        members = zf.namelist()

        # Detect and strip common top-level folder prefix
        prefix = ""
        if members:
            top_level = {m.split("/")[0] for m in members if "/" in m}
            if len(top_level) == 1:
                prefix = top_level.pop() + "/"

        for member in members:
            stripped = member[len(prefix):] if member.startswith(prefix) else member
            if not stripped:
                continue

            target_path = os.path.join(dest, stripped)

            if member.endswith("/"):
                os.makedirs(target_path, exist_ok=True)
            else:
                os.makedirs(os.path.dirname(target_path), exist_ok=True)
                with zf.open(member) as src, open(target_path, "wb") as dst:
                    dst.write(src.read())