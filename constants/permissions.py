# permissions.py

# === ✅ ALLOWED PERMISSIONS ===
BASE_ALLOWED = {
    "read_message_history": True,
    "read_messages": True,
    "send_messages": True,
    "embed_links": True,
    "attach_files": True,
    "add_reactions": True,
    "use_external_emojis": True,
    "use_external_stickers": True,
    "use_external_apps": True,
    "use_embedded_activities": True,
    "use_application_commands": True,
    
}

# === 🚫 DENIED PERMISSIONS ===
BASE_DENIED = {
    "create_public_threads": False,
    "create_private_threads": False,
    "manage_channels": False,
    "manage_permissions": False,
    "manage_webhooks": False,
    "manage_messages": False,
    "manage_threads": False,
    "create_instant_invite": False,
    "send_messages_in_threads": False,
    "send_voice_messages": False,
    "send_polls": False,
    "send_tts_messages": False,
    "mention_everyone": False,
}

# === 👤 Member Permissions ===
MEMBER_PERMISSIONS = {
    **BASE_ALLOWED,
    **BASE_DENIED
}

# === 💎 VIP Member Permissions (Extra: public thread creation) ===
VIP_MEMBER_PERMISSIONS = {
    **BASE_ALLOWED,
    "create_public_threads": True,
    **{k: v for k, v in BASE_DENIED.items() if k != "create_public_threads"}
}

# === 🛡 Staff Permissions (Extra: manage_messages) ===
STAFF_PERMISSIONS = {
    **BASE_ALLOWED,
    "manage_messages": True,
    **BASE_DENIED
}
