import json
import os
from typing import Dict, List, Tuple
from dotenv import load_dotenv
from groq import Groq
from PyPDF2 import PdfReader
import re
from time import sleep
import tiktoken

# Carrega as variáveis de ambiente
load_dotenv()

class QnAManager:
    def __init__(self, history_file: str = "chat_history.json"):
        self.history_file = history_file
        self.chat_history: List[Dict] = self._load_history()
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        self.document_text = ""
        self.current_document = ""
        self.chunks = []
        self.encoding = tiktoken.get_encoding("cl100k_base")  # Codificação compatível com modelos mais recentes
        
        # Mixtral-8x7b-32768 tem contexto total de 32768 tokens
        self.max_tokens = 32768
        self.max_response_tokens = 2048
        self.system_message = "Você é um assistente que analisa trechos de documentos e fornece respostas precisas, sempre citando as fontes quando encontra informações relevantes."
        
        # Calcula tokens fixos do prompt
        self.system_tokens = len(self.encoding.encode(self.system_message))
        self.prompt_template_tokens = len(self.encoding.encode("""Com base no seguinte trecho (#X) do documento:

[CHUNK]

Pergunta: [QUESTION]

Por favor, forneça uma resposta baseada nas informações deste trecho.
Se encontrar informações relevantes, SEMPRE cite o trecho específico usado.
Se não houver informações relevantes para a pergunta neste trecho, responda apenas 'NADA_RELEVANTE'."""))
        
        # Margem de segurança para outros metadados
        self.safety_margin = 500
        
        # O tamanho do chunk será calculado dinamicamente em _get_chunk_answer
        self.chunk_size = 8000  # Valor inicial, será ajustado conforme a pergunta
        self.batch_size = 3

    def _load_history(self) -> List[Dict]:
        """Carrega o histórico do chat ou cria um novo se não existir."""
        try:
            with open(self.history_file, 'r', encoding='utf-8') as file:
                return json.load(file)
        except FileNotFoundError:
            return []

    def _save_history(self):
        """Salva o histórico do chat."""
        with open(self.history_file, 'w', encoding='utf-8') as file:
            json.dump(self.chat_history, file, ensure_ascii=False, indent=2)

    def _split_into_chunks(self, text: str) -> List[str]:
        """Divide o texto em chunks com sobreposição."""
        chunks = []
        paragraphs = text.split('\n')
        current_chunk = ""
        
        print("\nDividindo o documento em partes menores...")
        total_chars = len(text)
        processed_chars = 0
        
        for paragraph in paragraphs:
            if len(current_chunk) + len(paragraph) > self.chunk_size:
                # Se o chunk atual já está grande o suficiente, salva ele
                if current_chunk:
                    chunks.append(current_chunk.strip())
                    processed_chars += len(current_chunk)
                    print(f"Progresso: {min(100, int((processed_chars/total_chars) * 100))}%", end='\r')
                current_chunk = paragraph
            else:
                # Adiciona o parágrafo ao chunk atual
                if current_chunk:
                    current_chunk += "\n" + paragraph
                else:
                    current_chunk = paragraph
        
        # Adiciona o último chunk se houver
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        print(f"\nDocumento dividido em {len(chunks)} partes")
        return chunks

    def load_pdf(self, pdf_path: str):
        """Carrega e processa um documento PDF."""
        try:
            print(f"\nCarregando o documento: {pdf_path}")
            self.current_document = pdf_path
            reader = PdfReader(pdf_path)
            text = ""
            total_pages = len(reader.pages)
            
            print(f"Total de páginas: {total_pages}")
            for i, page in enumerate(reader.pages, 1):
                text += page.extract_text() + "\n"
                print(f"Processando página {i}/{total_pages}", end='\r')
            
            print("\nExtraindo texto concluído!")
            self.document_text = text
            self.chunks = self._split_into_chunks(text)
            return True
        except Exception as e:
            print(f"\nErro ao carregar o PDF: {str(e)}")
            return False

    def _process_chunk_batch(self, chunks: List[str], question: str, start_index: int) -> List[str]:
        """Processa um lote de chunks e retorna suas respostas."""
        answers = []
        for i, chunk in enumerate(chunks):
            chunk_index = start_index + i
            print(f"Analisando parte {chunk_index + 1}/{len(self.chunks)}...", end='\r')
            
            try:
                answer = self._get_chunk_answer(chunk, question, chunk_index)
                answers.append(answer)
            except Exception as e:
                print(f"\nErro ao processar chunk {chunk_index + 1}: {str(e)}")
                answers.append("NADA_RELEVANTE")
                sleep(1)  # Pequena pausa em caso de erro
                
        return answers

    def _count_tokens(self, text: str) -> int:
        """Conta o número de tokens em um texto."""
        return len(self.encoding.encode(text))

    def _get_chunk_answer(self, chunk: str, question: str, chunk_index: int) -> str:
        """Obtém uma resposta de um chunk específico."""
        # Calcula tokens disponíveis para o chunk
        question_tokens = self._count_tokens(question)
        fixed_tokens = (
            self.system_tokens +          # Mensagem do sistema
            self.prompt_template_tokens + # Template do prompt
            question_tokens +             # Pergunta do usuário
            self.max_response_tokens +    # Tokens reservados para resposta
            self.safety_margin           # Margem de segurança
        )
        
        available_tokens = self.max_tokens - fixed_tokens
        current_chunk_tokens = self._count_tokens(chunk)
        
        if current_chunk_tokens > available_tokens:
            # Se o chunk for maior que o espaço disponível, trunca
            chunk = self.encoding.decode(self.encoding.encode(chunk)[:available_tokens])
        
        prompt = f"""Com base no seguinte trecho (#{chunk_index + 1}) do documento:

{chunk}

Pergunta: {question}

Por favor, forneça uma resposta baseada nas informações deste trecho.
Se encontrar informações relevantes, SEMPRE cite o trecho específico usado.
Se não houver informações relevantes para a pergunta neste trecho, responda apenas 'NADA_RELEVANTE'."""

        try:
            completion = self.client.chat.completions.create(
                model="gemma2-9b-it",
                messages=[
                    {"role": "system", "content": self.system_message},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1024
            )
            return completion.choices[0].message.content.strip()
        except Exception as e:
            print(f"\nErro na API do Groq: {str(e)}")
            sleep(2)
            return "NADA_RELEVANTE"

    def _combine_answers(self, chunk_answers: List[str], question: str) -> str:
        """Combina as respostas de todos os chunks em uma resposta final coerente."""
        # Filtra respostas sem informações relevantes
        relevant_answers = [ans for ans in chunk_answers if ans != "NADA_RELEVANTE"]
        
        if not relevant_answers:
            return "Não encontrei informações sobre isso no documento."

        combined_answers = "\n\n".join(relevant_answers)
        
        prompt = f"""Responda à pergunta "{question}" usando apenas as informações abaixo:

{combined_answers}

Regras para a resposta:
1. Comece respondendo diretamente à pergunta
2. Para cada informação fornecida, SEMPRE cite a fonte específica do documento
3. Organize as informações de forma lógica
4. Se houver informações contraditórias, indique-as claramente
5. Não mencione o processo de análise ou combinação de informações
6. Não use numeração de trechos que não contêm informações
7. Mantenha um tom natural e direto, como se estivesse conversando com o usuário
8. Se uma informação aparecer em múltiplos trechos, cite apenas a fonte mais completa"""

        try:
            print("\nGerando resposta...")
            completion = self.client.chat.completions.create(
                model="gemma2-9b-it",
                messages=[
                    {"role": "system", "content": "Você é um assistente que responde perguntas de forma direta e precisa, sempre citando as fontes do documento. Mantenha um tom natural e evite mencionar detalhes técnicos do processamento."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=2048,
                stream=True
            )

            collected_messages = []

            # Limpa a linha atual
            print("\033[K", end="\r")
            
            # Processa o stream de tokens
            for chunk in completion:
                chunk_message = chunk.choices[0].delta.content  # Extrai o texto do chunk
                
                if chunk_message:
                    collected_messages.append(chunk_message)  # Adiciona à lista de mensagens
                    print(chunk_message, end="", flush=True)  # Mostra o texto gradualmente
            
            print("\n")  # Nova linha após terminar
            
            # Retorna a mensagem completa sem imprimir novamente
            return "".join(collected_messages)

        except Exception as e:
            print(f"\nErro ao combinar respostas: {str(e)}")
            return "Erro ao combinar as informações encontradas. Por favor, tente novamente."

    def ask_question(self, question: str) -> Dict:
        """Processa uma pergunta usando todos os chunks do documento em lotes."""
        if not self.chunks:
            return {
                "answer": "Nenhum documento foi carregado ainda. Por favor, carregue um PDF primeiro.",
                "source": None
            }

        print(f"\nProcessando {len(self.chunks)} partes do documento em lotes de {self.batch_size}...")

        # Map: Obtém respostas de todos os chunks em lotes
        chunk_answers = []
        for i in range(0, len(self.chunks), self.batch_size):
            batch = self.chunks[i:i + self.batch_size]
            print(f"\nProcessando lote {(i//self.batch_size) + 1}/{(len(self.chunks) + self.batch_size - 1)//self.batch_size}")
            
            batch_answers = self._process_chunk_batch(batch, question, i)
            chunk_answers.extend(batch_answers)
            
            # Pequena pausa entre lotes para evitar sobrecarga
            if i + self.batch_size < len(self.chunks):
                print("Aguardando para processar próximo lote...")
                sleep(1)

        print("\nCombinando todas as informações encontradas...")
        
        # Reduce: Combina todas as respostas
        final_answer = self._combine_answers(chunk_answers, question)

        # Não imprime a resposta aqui, pois já foi impressa no streaming
        response = {
            "question": question,
            "answer": final_answer,
            "document": self.current_document
        }

        # Salva no histórico
        self.chat_history.append(response)
        self._save_history()

        # Retorna silenciosamente
        return response

    def get_chat_history(self) -> List[Dict]:
        """Retorna o histórico completo do chat."""
        return self.chat_history 