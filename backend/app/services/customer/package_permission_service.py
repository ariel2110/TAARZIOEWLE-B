
from __future__ import annotations
from sqlalchemy.orm import Session
from app.models.package_field_permission import PackageFieldPermission

DEFAULTS = {
    'Demo': [
        {'field_key':'phone','is_allowed':True,'requires_review':False,'display_group':'contact'},
        {'field_key':'address','is_allowed':True,'requires_review':True,'display_group':'contact'},
        {'field_key':'short_description','is_allowed':True,'requires_review':True,'display_group':'content'},
    ],
    'Starter': [
        {'field_key':'phone','is_allowed':True,'requires_review':False,'display_group':'contact'},
        {'field_key':'address','is_allowed':True,'requires_review':True,'display_group':'contact'},
        {'field_key':'short_description','is_allowed':True,'requires_review':True,'display_group':'content'},
        {'field_key':'whatsapp_text','is_allowed':True,'requires_review':True,'display_group':'content'},
    ],
    'Business': [
        {'field_key':'phone','is_allowed':True,'requires_review':False,'display_group':'contact'},
        {'field_key':'address','is_allowed':True,'requires_review':False,'display_group':'contact'},
        {'field_key':'short_description','is_allowed':True,'requires_review':True,'display_group':'content'},
        {'field_key':'whatsapp_text','is_allowed':True,'requires_review':True,'display_group':'content'},
        {'field_key':'opening_hours','is_allowed':True,'requires_review':True,'display_group':'operations'},
    ],
}

class PackagePermissionService:
    def list_for_package(self, db: Session, package_name: str) -> list[dict]:
        rows = db.query(PackageFieldPermission).filter(PackageFieldPermission.package_name == package_name).order_by(PackageFieldPermission.id.asc()).all()
        if rows:
            return [
                {'field_key': r.field_key, 'is_allowed': r.is_allowed, 'requires_review': r.requires_review, 'display_group': r.display_group}
                for r in rows
            ]
        return DEFAULTS.get(package_name, DEFAULTS['Demo'])
