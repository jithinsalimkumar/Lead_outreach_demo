"""
Settings router — manage API keys and configuration (admin-only).

Values are stored encrypted in the database and displayed masked
in API responses. Only admins can view or update settings.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.deps import require_admin
from app.models.setting import Setting
from app.models.user import User
from app.schemas.settings import SettingOut, SettingUpdate
from app.services.encryption import decrypt_value, encrypt_value, mask_value

router = APIRouter(prefix="/api/settings", tags=["settings"])

# Known setting keys — these are the API keys the system will use
KNOWN_KEYS = [
    "brightdata_api_key",
    "prospeo_api_key",
    "vibe_prospecting_api_key",
    "instantly_api_key",
]


@router.get("", response_model=list[SettingOut])
async def list_settings(
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """
    List all settings with masked values.

    Returns all known API key settings. If a key hasn't been set yet,
    it's returned with a placeholder masked value.
    """
    result = await db.execute(select(Setting))
    existing = {s.key: s for s in result.scalars().all()}

    settings_list = []
    for key in KNOWN_KEYS:
        if key in existing:
            setting = existing[key]
            # Decrypt the value to mask it (show last 4 chars)
            try:
                decrypted = decrypt_value(setting.encrypted_value)
                masked = mask_value(decrypted)
            except Exception:
                masked = "****error"

            settings_list.append(SettingOut(
                id=setting.id,
                key=setting.key,
                masked_value=masked,
                updated_by=setting.updated_by,
                updated_at=setting.updated_at,
            ))
        else:
            # Key not yet configured — show as empty
            settings_list.append(SettingOut(
                id=uuid.uuid4(),  # Placeholder ID
                key=key,
                masked_value="Not configured",
                updated_by=None,
                updated_at=None,
            ))

    return settings_list


@router.put("/{key}", response_model=SettingOut)
async def update_setting(
    key: str,
    body: SettingUpdate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """
    Update or create a setting value (admin-only).

    The value is encrypted before being stored in the database.
    """
    if key not in KNOWN_KEYS:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown setting key. Must be one of: {', '.join(KNOWN_KEYS)}",
        )

    encrypted = encrypt_value(body.value)

    # Try to find existing setting
    result = await db.execute(select(Setting).where(Setting.key == key))
    setting = result.scalar_one_or_none()

    if setting:
        # Update existing
        setting.encrypted_value = encrypted
        setting.updated_by = admin.id
    else:
        # Create new
        setting = Setting(
            key=key,
            encrypted_value=encrypted,
            updated_by=admin.id,
        )
        db.add(setting)

    await db.commit()
    await db.refresh(setting)

    return SettingOut(
        id=setting.id,
        key=setting.key,
        masked_value=mask_value(body.value),
        updated_by=setting.updated_by,
        updated_at=setting.updated_at,
    )
