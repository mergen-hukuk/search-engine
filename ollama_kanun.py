import ollama

inp = """\
4857 sayılı İş Kanununun 63 üncü maddesinde çalışma süresi haftada en çok 45 saat olarak belirtilmiştir.\
"""

response = ollama.chat(
    model='llama3.2:1b',
    messages=[
        {'role': 'system', 'content': 'your job is to catch and parse laws, \
            articles and their respective numbers in a json, \
            [always use the tool provided]\
            [if there is no answer write 0 instead]'},
        {'role': 'user', 'content': inp},
    ],
    tools=[
        {
            "type": "function",
            "function": {
                "name": "parse_law",
                "description": "Bir cümle veya metin üzerinde işlem yaparak kanun adı, madde ve numarayı çıkartır.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "number": {
                            "type": "integer",
                            "description": "Kanundaki madde numarası. (örneğin: 4857 sayılı kanun)"
                        },
                        "law": {
                            "type": "string",
                            "description": "Metinde bahsedilen kanun adı. (örnek: İş Kanunu, Mülkiyet Kanunu, vb.)"
                        },
                        "article": {
                            "type": "integer",
                            "description": "Kanun referansındaki madde numarası. (örneğin: 63. madde)"
                        }
                    },
                    "required": ["number", "article", "law"]
                }
            }
        }
    ]
)

print(response.message)