from together import Together

# 🔐 Tu clave API directamente en el constructor
client = Together(
    api_key="97301d064786753021066a79298e18af22d5d545140f99994373bf3ac82c1210"  # Reemplaza con tu clave real
)

# 💬 Prompt interactivo tipo chat
while True:
    prompt = input("🧠 PROMPT: ")
    if prompt.strip().lower() == "exit":
        print("👋 Nos vemos pronto.")
        break

    try:
        response = client.chat.completions.create(
            model="deepseek-ai/DeepSeek-V3",  # Puedes probar otros como llama-3
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )
        respodel = response.choices[0].message.content
        print(f"""═══ GABO AI ════════════════════════════:\n""")
        print(respodel)
        print("")
    except Exception as e:
        print(f"⚠️ Error: {e}")

