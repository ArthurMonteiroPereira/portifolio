from qna_manager import QnAManager
import os
import json
from utils import garantir_pasta_conversas, criar_pasta_conversa

def listar_conversas():
    garantir_pasta_conversas()
    return [nome for nome in os.listdir('conversas') if os.path.isdir(os.path.join('conversas', nome))]

def escolher_conversa():
    conversas = listar_conversas()
    if not conversas:
        print("\nNenhuma conversa encontrada. Inicie uma nova!")
        return None
    print("\nConversas disponíveis:")
    for i, nome in enumerate(conversas, 1):
        print(f"{i}. {nome}")
    escolha = input("Escolha o número da conversa ou pressione Enter para cancelar: ")
    if not escolha.strip():
        return None
    try:
        idx = int(escolha) - 1
        if 0 <= idx < len(conversas):
            return conversas[idx]
    except Exception:
        pass
    print("Opção inválida.")
    return None

def criar_nova_conversa():
    garantir_pasta_conversas()
    caminho_arquivo = input("\nDigite o caminho do arquivo PDF ou TXT: ")
    if not os.path.exists(caminho_arquivo):
        print(f"Arquivo {caminho_arquivo} não encontrado!")
        return None
    import uuid
    nome_base = os.path.splitext(os.path.basename(caminho_arquivo))[0]
    nome_unico = f"{nome_base}_{uuid.uuid4().hex[:8]}"
    pasta_conversa = criar_pasta_conversa(nome_unico)
    destino = os.path.join(pasta_conversa, os.path.basename(caminho_arquivo))
    with open(caminho_arquivo, "rb") as src, open(destino, "wb") as dst:
        dst.write(src.read())
    # Cria histórico vazio
    with open(os.path.join(pasta_conversa, "chat_history.json"), "w", encoding="utf-8") as f:
        f.write("[]")
    print(f"Conversa criada: {nome_unico}")
    return nome_unico

def carregar_conversa(nome_conversa):
    pasta = os.path.join('conversas', nome_conversa)
    arquivos = os.listdir(pasta)
    arquivos_validos = [arq for arq in arquivos if arq.lower().endswith(('.pdf', '.txt'))]
    if not arquivos_validos:
        print("Nenhum arquivo PDF ou TXT encontrado nesta conversa.")
        return None, None, None
    caminho_arquivo = os.path.join(pasta, arquivos_validos[0])
    caminho_json = os.path.join(pasta, "chat_history.json")
    if not os.path.exists(caminho_json):
        historico = []
    else:
        with open(caminho_json, "r", encoding="utf-8") as f:
            historico = json.load(f)
    return caminho_arquivo, caminho_json, historico

def main():
    garantir_pasta_conversas()
    conversa_atual = None
    caminho_arquivo = None
    caminho_json = None
    historico = None
    qna = None
    
    while True:
        print("\n=== Chat com Documento PDF/TXT ===")
        print(f"Conversa atual: {conversa_atual if conversa_atual else 'Nenhuma'}")
        print("1. Iniciar nova conversa")
        print("2. Listar conversas existentes")
        print("3. Selecionar conversa")
        print("4. Fazer uma pergunta na conversa atual")
        print("5. Ver histórico da conversa atual")
        print("6. Sair")
        
        opcao = input("\nEscolha uma opção: ")
        
        if opcao == "1":
            nome = criar_nova_conversa()
            if nome:
                conversa_atual = nome
                caminho_arquivo, caminho_json, historico = carregar_conversa(conversa_atual)
                qna = QnAManager(history_file=caminho_json)
                # Carrega o arquivo
                if caminho_arquivo.lower().endswith('.pdf'):
                    qna.load_pdf(caminho_arquivo)
                elif caminho_arquivo.lower().endswith('.txt'):
                    with open(caminho_arquivo, 'r', encoding='utf-8') as f:
                        texto = f.read()
                    qna.document_text = texto
                    qna.chunks = qna._split_into_chunks(texto)
                    qna.current_document = caminho_arquivo
                print(f"Conversa '{conversa_atual}' pronta para uso!")
        elif opcao == "2":
            conversas = listar_conversas()
            if not conversas:
                print("Nenhuma conversa encontrada.")
            else:
                print("\nConversas:")
                for nome in conversas:
                    print(f"- {nome}")
        elif opcao == "3":
            nome = escolher_conversa()
            if nome:
                conversa_atual = nome
                caminho_arquivo, caminho_json, historico = carregar_conversa(conversa_atual)
                qna = QnAManager(history_file=caminho_json)
                if caminho_arquivo.lower().endswith('.pdf'):
                    qna.load_pdf(caminho_arquivo)
                elif caminho_arquivo.lower().endswith('.txt'):
                    with open(caminho_arquivo, 'r', encoding='utf-8') as f:
                        texto = f.read()
                    qna.document_text = texto
                    qna.chunks = qna._split_into_chunks(texto)
                    qna.current_document = caminho_arquivo
                print(f"Conversa '{conversa_atual}' carregada!")
        elif opcao == "4":
            if not (conversa_atual and qna and caminho_json):
                print("Nenhuma conversa selecionada. Inicie ou selecione uma conversa primeiro!")
                continue
            pergunta = input("\nDigite sua pergunta sobre o documento: ")
            resposta = qna.ask_question(pergunta)
            print("\n" + "-" * 50)
            # Atualiza histórico
            historico.append({
                "question": pergunta,
                "answer": resposta["answer"],
                "document": resposta["document"]
            })
            with open(caminho_json, "w", encoding="utf-8") as f:
                json.dump(historico, f, ensure_ascii=False, indent=2)
            print("Resposta adicionada ao histórico!")
        elif opcao == "5":
            if not (conversa_atual and historico):
                print("Nenhuma conversa selecionada ou histórico vazio.")
            else:
                print(f"\n=== Histórico da conversa '{conversa_atual}' ===")
                for i, interacao in enumerate(historico, 1):
                    print(f"\n{i}. Documento: {interacao['document']}")
                    print(f"Pergunta: {interacao['question']}")
                    print(f"Resposta: {interacao['answer']}")
                    print("-" * 50)
        elif opcao == "6":
            print("\nObrigado por usar o chat!")
            break
        else:
            print("\nOpção inválida. Por favor, tente novamente.")

if __name__ == "__main__":
    main() 