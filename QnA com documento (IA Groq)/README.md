# QnA_Groq

## Descrição

Este projeto permite que você faça perguntas sobre documentos PDF ou TXT usando inteligência artificial (Groq API), recebendo respostas precisas e citando as fontes do documento. Você pode usar tanto uma interface web (estilo ChatGPT, feita com Streamlit) quanto um chat de terminal, com histórico de conversas salvo para cada documento.

## Funcionalidades
- Carregue arquivos PDF ou TXT e faça perguntas sobre o conteúdo
- Histórico de conversas salvo automaticamente para cada documento
- Interface web moderna, com barra lateral para seleção de conversas e upload de novos arquivos
- Chat de terminal com múltiplas conversas, igual à interface web
- Suporte a múltiplos documentos e múltiplos históricos
- Respostas sempre citam o trecho do documento utilizado

## Estrutura de Pastas
```
QnA_Groq/
├── app.py                # Interface web (Streamlit)
├── chat_terminal.py      # Chat via terminal
├── qna_manager.py        # Lógica principal de perguntas e respostas
├── utils.py              # Funções utilitárias para pastas/conversas
├── conversas/            # Pasta onde ficam todas as conversas
│   └── <nome_conversa>/  # Subpasta para cada conversa
│       ├── <arquivo.pdf/txt>
│       └── chat_history.json
├── requirements.txt      # (Opcional) Dependências do projeto
└── README.md             # Este arquivo
```

## Requisitos
- Python 3.8+
- Instale as dependências:

```
pip install streamlit PyPDF2 python-dotenv groq tiktoken
```

## Como usar

### 1. Configurar a API do Groq
Crie um arquivo `.env` na raiz do projeto com sua chave:
```
GROQ_API_KEY=seu_token_aqui
```

### 2. Usar a interface web (recomendado)

1. Execute:
   ```
   streamlit run app.py
   ```
2. Acesse o endereço mostrado (geralmente http://localhost:8501)
3. Use a barra lateral para:
   - Iniciar nova conversa (faça upload de PDF ou TXT)
   - Selecionar conversas anteriores
   - Fazer perguntas e ver o histórico

### 3. Usar o chat de terminal

1. Execute:
   ```
   python chat_terminal.py
   ```
2. Siga o menu:
   - Inicie nova conversa (informe o caminho do PDF ou TXT)
   - Liste e selecione conversas
   - Faça perguntas e veja o histórico

## Dicas
- O histórico de cada conversa fica salvo em `conversas/<nome_conversa>/chat_history.json`
- Você pode carregar e conversar com vários documentos diferentes
- O sistema aceita arquivos PDF (texto digital) e TXT (UTF-8)
- PDFs digitalizados (imagem) não terão texto extraído corretamente

## Observações
- O projeto utiliza a API do Groq para geração de respostas. Certifique-se de ter uma chave válida.
- O limite de tokens do modelo é respeitado automaticamente.
- O código pode ser facilmente adaptado para outros formatos de documento.

---

Qualquer dúvida ou sugestão, abra uma issue ou entre em contato!

 
