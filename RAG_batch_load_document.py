import os
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import Chroma
from langchain_openai import AzureOpenAIEmbeddings
from langchain.text_splitter import CharacterTextSplitter
import httpx
from config import embedding_model, azure_embedding_model_endpoint, azure_embedding_model_api_key, embedding_openai_api_version


embeddings = AzureOpenAIEmbeddings(
    model= embedding_model,
    # dimensions: Optional[int] = None, # Can specify dimensions with new text-embedding-3 models
    azure_endpoint=azure_embedding_model_endpoint,
    api_key= azure_embedding_model_api_key,
    openai_api_version= embedding_openai_api_version ,
    http_client=httpx.Client(verify=False),
    http_async_client=httpx.AsyncClient(verify=False)
)

# Specify the folder containing your PDF documents
folder_path = './documents'  # Change this to your folder path

# List to hold the loaded PDF documents
pdf_docs = []

# Iterate through all files in the specified folder
for filename in os.listdir(folder_path):
    if filename.endswith('.pdf'):  # Check if the file is a PDF
        file_path = os.path.join(folder_path, filename)
        loader = PyPDFLoader(file_path)
        docs = loader.load_and_split()
        text_splitter = CharacterTextSplitter(chunk_size=512, chunk_overlap=128)
        documents = text_splitter.split_documents(docs)

        db = Chroma.from_documents(
            documents,
            embedding=embeddings,
            persist_directory="./vectord-knowledge-base"
        )
        pdf_docs.append(filename)

# Now you can use the loaded PDF documents in pdf_docs list
print(f"Loaded {pdf_docs} ")