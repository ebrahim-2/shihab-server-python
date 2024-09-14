import os
from langchain_community.graphs import Neo4jGraph
from langchain.chains import GraphCypherQAChain
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
from langchain_core.chat_history import (
    BaseChatMessageHistory,
    InMemoryChatMessageHistory,
)
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain.schema import HumanMessage


load_dotenv()  # Load environment variables from .env file

neo4j_uri = os.getenv("NEO4J_URI")
neo4j_username = os.getenv("NEO4J_USERNAME")
neo4j_password = os.getenv("NEO4J_PASSWORD")
openai_api_key = os.getenv("OPENAI_API_KEY")

llm = ChatOpenAI(model="gpt-4o", temperature=0)


graph = Neo4jGraph()

chain = GraphCypherQAChain.from_llm(graph=graph, llm=llm, verbose=True, validate_cypher=True, allow_dangerous_requests=True)

def queryGraph(query): 
    return chain.invoke({"query": query})
