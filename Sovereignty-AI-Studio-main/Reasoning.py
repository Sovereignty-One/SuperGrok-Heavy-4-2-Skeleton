chat = client.chat.create(
    model="supergrok-heavy-4-2",
    store_messages=True,
    use_encrypted_content=True   # ← this flag
)
