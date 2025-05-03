# Para rodar: streamlit run app.py
import streamlit as st
from utils import garantir_pasta_conversas
import os

def main():
    garantir_pasta_conversas()
    st.set_page_config(page_title="Chat com PDF", layout="wide")
    st.title("Chat com Documento PDF")
    st.sidebar.title("Conversas")
    conversas = [nome for nome in os.listdir('conversas') if os.path.isdir(os.path.join('conversas', nome))]
    conversa_selecionada = None
    if conversas:
        conversa_selecionada = st.sidebar.radio("Selecione uma conversa:", conversas)
    if st.sidebar.button("+ Nova conversa"):
        st.session_state['nova_conversa'] = True
    st.write("Bem-vindo! Use a barra lateral para iniciar ou selecionar uma conversa.")

    # Upload de PDF ou TXT para nova conversa
    if st.session_state.get('nova_conversa', False):
        st.subheader("Nova conversa")
        uploaded_file = st.file_uploader("Faça upload de um PDF ou TXT", type=["pdf", "txt"])
        if uploaded_file is not None:
            import uuid
            from utils import criar_pasta_conversa
            nome_base = os.path.splitext(uploaded_file.name)[0]
            nome_unico = f"{nome_base}_{uuid.uuid4().hex[:8]}"
            caminho_conversa = criar_pasta_conversa(nome_unico)
            caminho_arquivo = os.path.join(caminho_conversa, uploaded_file.name)
            with open(caminho_arquivo, "wb") as f:
                f.write(uploaded_file.getbuffer())
            # Cria histórico vazio
            caminho_json = os.path.join(caminho_conversa, "chat_history.json")
            with open(caminho_json, "w", encoding="utf-8") as f:
                f.write("[]")
            st.success(f"Conversa criada com sucesso: {nome_unico}")
            st.session_state['nova_conversa'] = False
            st.rerun()

    # Exibir chat da conversa selecionada
    if conversa_selecionada:
        st.subheader(f"Conversa: {conversa_selecionada}")
        caminho_conversa = os.path.join('conversas', conversa_selecionada)
        # Descobrir nome do arquivo
        arquivos = os.listdir(caminho_conversa)
        arquivos_validos = [arq for arq in arquivos if arq.lower().endswith(('.pdf', '.txt'))]
        if arquivos_validos:
            st.write(f"**Documento:** {arquivos_validos[0]}")
        # Carregar histórico
        caminho_json = os.path.join(caminho_conversa, "chat_history.json")
        import json
        if os.path.exists(caminho_json):
            with open(caminho_json, "r", encoding="utf-8") as f:
                historico = json.load(f)
        else:
            historico = []
        # Mostrar histórico
        if historico:
            st.markdown("---")
            st.markdown("**Histórico:**")
            for item in historico:
                st.markdown(f"**Pergunta:** {item.get('question','')}")
                st.markdown(f"**Resposta:** {item.get('answer','')}")
                st.markdown("---")
        # Campo para nova pergunta
        st.markdown("### Nova pergunta")
        pergunta = st.text_input("Digite sua pergunta:", key=f"pergunta_{conversa_selecionada}")
        if st.button("Enviar", key=f"enviar_{conversa_selecionada}"):
            if not pergunta.strip():
                st.warning("Digite uma pergunta antes de enviar.")
            elif not arquivos_validos:
                st.error("Arquivo não encontrado para esta conversa.")
            else:
                from qna_manager import QnAManager
                caminho_arquivo = os.path.join(caminho_conversa, arquivos_validos[0])
                qna = QnAManager(history_file=caminho_json)
                # Carrega o arquivo (PDF ou TXT)
                with st.spinner("Processando pergunta..."):
                    if caminho_arquivo.lower().endswith('.pdf'):
                        qna.load_pdf(caminho_arquivo)
                    elif caminho_arquivo.lower().endswith('.txt'):
                        with open(caminho_arquivo, 'r', encoding='utf-8') as f:
                            texto = f.read()
                        qna.document_text = texto
                        qna.chunks = qna._split_into_chunks(texto)
                        qna.current_document = caminho_arquivo
                    resposta = qna.ask_question(pergunta)
                # Atualiza histórico
                historico.append({
                    "question": pergunta,
                    "answer": resposta["answer"],
                    "document": resposta["document"]
                })
                with open(caminho_json, "w", encoding="utf-8") as f:
                    json.dump(historico, f, ensure_ascii=False, indent=2)
                st.success("Resposta adicionada ao histórico!")
                st.rerun()

if __name__ == "__main__":
    main() 