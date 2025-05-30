from langchain_community.vectorstores import Chroma
from langchain_openai import AzureOpenAIEmbeddings
from langchain_deepseek import ChatDeepSeek
import httpx
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import CharacterTextSplitter
from config import llm_model, llm_api_key, embedding_model, azure_embedding_model_endpoint, azure_embedding_model_api_key, embedding_openai_api_version



# Embed
embeddings = AzureOpenAIEmbeddings(
    model=embedding_model,
    # dimensions: Optional[int] = None, # Can specify dimensions with new text-embedding-3 models
    azure_endpoint= azure_embedding_model_endpoint,
    api_key=  azure_embedding_model_api_key,
    openai_api_version= embedding_openai_api_version,
    http_client=httpx.Client(verify=False),
    http_async_client=httpx.AsyncClient(verify=False)
)

loader = PyPDFLoader("./OnYourSidePlan_tc.pdf")
docs = loader.load_and_split()
text_splitter = CharacterTextSplitter(chunk_size=512, chunk_overlap=128)
documents = text_splitter.split_documents(docs)

db = Chroma.from_documents(
    documents,
    embedding=embeddings,
    persist_directory="./vectord-knowledge-base"
)

retriever = db.as_retriever()

# LLM
llm = ChatDeepSeek(
    model=llm_model,
    api_key=llm_api_key,
    http_client=httpx.Client(verify=False),
    http_async_client=httpx.AsyncClient(verify=False),
    temperature=1,
    max_tokens=500
)

query = "On Your Side Plan"
docs = retriever.get_relevant_documents(query)
print(docs)