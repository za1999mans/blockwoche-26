
from ai_wrapper import AI, Config, TTS

Config.default_provider =  "openai"# "deepseek"
Config.deepseek_default_model = "gpt-4o-mini" # "deepseek-chat"

# ------

#antwort = AI.chat(prompt="Hallo, Ich bin Alex und studiere Informatik")
#print(antwort)

# print(AI.chat(prompt="weißt du noch wer ich bin?"))


# print("".join(AI.stream(prompt="Hallo, Ich bin Alex und studiere Informatik", print_live=True)))

"""
chat = AI.session(system_prompt="Du bist ein Programmierassistenz und Hilfst mir bei meinen Code und antwortest mir immer höflich und auf Deutsch zurück")

print(chat.ask("Hallo, ich bin Alex! Wie geht es dir"))
print(chat.ask("weißt du noch wer ich bin?"))

print(chat.history())
"""



"""
schema= '{"name": "string", "age": "integer"}"'

result = AI.structured(prompt="My name is Alice and I am 30 years old.", schema=schema)
print(result)
"""
# print(TTS.list_voices())

print(TTS.speak_to_file("Hallo, ich bin Alex! Wie geht es dir", output_path="audios/hallo.mp3", voice="cedar"))
