import streamlit as st
import spacy
from spacytextblob.spacytextblob import SpacyTextBlob
import pandas as pd
import io
from pypdf import PdfReader  # Biblioteca para extrair texto de PDFs

# 1. Configuração da Página
st.set_page_config(
    page_title="Analisador de Sentimentos NLP",
    page_icon="🧠",
    layout="centered"
)

# 2. Inicialização do Modelo spaCy (com Cache para performance)
@st.cache_resource
def carregar_modelo():
    nlp = spacy.load("en_core_web_sm")
    nlp.add_pipe('spacytextblob')
    return nlp

nlp = carregar_modelo()

# 3. Interface do Usuário
st.title("🧠 Analisador de Sentimentos com spaCy")
st.write("Faça o upload de um documento `.txt`, `.xlsx` ou `.pdf` para identificar o sentimento.")

# COMPONENTE DE UPLOAD ATUALIZADO: Agora aceita PDF também!
arquivo_carregado = st.file_uploader("Escolha seu arquivo", type=["txt", "xlsx", "pdf"])

if arquivo_carregado is not None:
    nome_arquivo = arquivo_carregado.name
    
    # =========================================================================
    # CASO 1: FLUXO DE ARQUIVO TEXTO (.TXT)
    # =========================================================================
    if nome_arquivo.endswith('.txt'):
        texto = arquivo_carregado.read().decode("utf-8")
        
        with st.expander("Ver conteúdo do documento", expanded=True):
            st.text_area("Texto detectado:", texto, height=150, disabled=True)
        
        if st.button("Iniciar Leitura e Análise", type="primary", key="btn_txt"):
            with st.spinner("O spaCy está lendo o documento..."):
                doc = nlp(texto)
                polaridade = doc._.blob.polarity
                
                if polaridade > 0.1:
                    sentimento = "Positivo"
                    cor_box = st.success
                    emoji = "😊"
                elif polaridade < -0.1:
                    sentimento = "Negativo"
                    cor_box = st.error
                    emoji = "😢"
                else:
                    sentimento = "Neutro"
                    cor_box = st.info
                    emoji = "😐"
                
                st.markdown("---")
                st.subheader("📊 Resultado da Análise")
                cor_box(f"{emoji} Sentimento Predominante: **{sentimento}**")
                st.metric(label="Score de Polaridade (-1 a 1)", value=f"{polaridade:.2f}")

    # =========================================================================
    # CASO 2: FLUXO DE ARQUIVO PDF (.PDF) - NOVO!
    # =========================================================================
    elif nome_arquivo.endswith('.pdf'):
        # Inicializa o leitor de PDF
        leitor_pdf = PdfReader(arquivo_carregado)
        texto_extraido = ""
        
        # Percorre todas as páginas e extrai o texto de cada uma
        for pagina in leitor_pdf.pages:
            texto_pagina = pagina.extract_text()
            if texto_pagina:  # Garante que a página não está vazia ou é uma imagem
                texto_extraido += texto_pagina + "\n"
        
        with st.expander("Ver texto extraído do PDF", expanded=True):
            st.text_area("Texto detectado:", texto_extraido, height=150, disabled=True)
            
        if st.button("Iniciar Leitura e Análise do PDF", type="primary", key="btn_pdf"):
            with st.spinner("O spaCy está analisando o texto do PDF..."):
                # Passa o texto consolidado do PDF para o spaCy
                doc = nlp(texto_extraido)
                polaridade = doc._.blob.polarity
                
                if polaridade > 0.1:
                    sentimento = "Positivo"
                    cor_box = st.success
                    emoji = "😊"
                elif polaridade < -0.1:
                    sentimento = "Negativo"
                    cor_box = st.error
                    emoji = "😢"
                else:
                    sentimento = "Neutro"
                    cor_box = st.info
                    emoji = "😐"
                
                st.markdown("---")
                st.subheader("📊 Resultado da Análise do PDF")
                cor_box(f"{emoji} Sentimento Predominante: **{sentimento}**")
                st.metric(label="Score de Polaridade (-1 a 1)", value=f"{polaridade:.2f}")

    # =========================================================================
    # CASO 3: FLUXO DE PLANILHA EXCEL (.XLSX)
    # =========================================================================
    elif nome_arquivo.endswith('.xlsx'):
        df = pd.read_excel(arquivo_carregado)
        st.success("Planilha carregada com sucesso!")
        st.write("📋 **Visualização das primeiras linhas do seu arquivo:**")
        st.dataframe(df.head(5))
        
        coluna_texto = st.selectbox(
            "Selecione a coluna que contém os comentários/textos para análise:", 
            options=df.columns
        )
        
        if st.button("Iniciar Análise da Planilha", type="primary", key="btn_xlsx"):
            with st.spinner("O spaCy está processando linha por linha da planilha..."):
                lista_polaridades = []
                lista_sentimentos = []
                
                for index, linha in df.iterrows():
                    texto_celula = str(linha[coluna_texto])
                    
                    if texto_celula.strip() == "" or pd.isna(linha[coluna_texto]):
                        lista_polaridades.append(0.0)
                        lista_sentimentos.append("Neutro")
                    else:
                        doc = nlp(texto_celula)
                        pol = doc._.blob.polarity
                        lista_polaridades.append(pol)
                        
                        if pol > 0.1:
                            lista_sentimentos.append("Positivo")
                        elif pol < -0.1:
                            lista_sentimentos.append("Negativo")
                        else:
                            lista_sentimentos.append("Neutro")
                
                df['Polaridade_spaCy'] = lista_polaridades
                df['Sentimento_spaCy'] = lista_sentimentos
                
                st.markdown("---")
                st.subheader("📊 Resultados da Planilha")
                st.write("📈 **Distribuição de Sentimentos:**")
                contagem_sentimentos = df['Sentimento_spaCy'].value_counts()
                st.bar_chart(contagem_sentimentos)
                
                st.write("📋 **Tabela final processada:**")
                st.dataframe(df)
                
                buffer_excel = io.BytesIO()
                with pd.ExcelWriter(buffer_excel, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False, sheet_name='Sentimentos_spaCy')
                
                st.markdown("---")
                st.download_button(
                    label="📥 Baixar Planilha com os Resultados (.xlsx)",
                    data=buffer_excel.getvalue(),
                    file_name="planilha_sentimentos_final.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )