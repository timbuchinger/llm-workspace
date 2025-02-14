from langchain.chains import RetrievalQA
from langchain_community.document_loaders import TextLoader
from langchain_community.vectorstores import Chroma
from langchain_core.prompts import PromptTemplate
from langchain_ollama import OllamaEmbeddings, OllamaLLM


def load_vector_store():
    embeddings = OllamaEmbeddings(
        base_url=f"https://{OLLAMA_ENDPOINT}", model="nomic-embed-text"
    )
    vector_store = Chroma(
        persist_directory="./vector_store", embedding_function=embeddings
    )
    return vector_store


def create_qa_chain():
    vector_store = load_vector_store()
    retriever = vector_store.as_retriever(
        search_type="similarity", search_kwargs={"k": 5}
    )
    llm = OllamaLLM(model="llama3", base_url=f"https://{OLLAMA_ENDPOINT}")

    prompt = PromptTemplate(
        template="Anser the question based on the context:\n\n{context}\n\nQuestion: {question}\n\nAnswer:",
        input_variables=["context", "question"],
    )
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        retriever=retriever,
        chain_type="stuff",
        return_source_documents=True,
        chain_type_kwargs={"prompt": prompt},
    )
    return qa_chain


def answer_question(query):
    qa_chain = create_qa_chain()
    result = qa_chain({"query": query})
    answer = result["result"]
    sources = [doc.metadata["source"] for doc in result["source_documents"]]
    return answer, sources
