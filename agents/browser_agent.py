import asyncio
import os
from typing import Optional
from dotenv import load_dotenv
import logging
from langchain_core.messages import HumanMessage
from langchain_core.runnables import Runnable
from langchain_google_genai import ChatGoogleGenerativeAI
from mcp import ClientSession, ListToolsResult
from mcp.client.streamable_http import streamablehttp_client

# Basic configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

class BrowserSession:
    def __init__(self, readstrem, writestream, session:ClientSession, stream_http_client) -> None:
        self.readstrem = readstrem
        self.writestream = writestream
        self.session = session
        self.stream_http_client = stream_http_client

    async def close(self):
        await self.session.__aexit__(None, None, None)
        await self.readstrem.aclose()
        await self.writestream.aclose()
        await self.stream_http_client.__aexit__(None, None, None)


class ToolExecutor(Runnable):
    
    def __init__(self, browser_session:BrowserSession ) -> None:
        self.browser_session = browser_session
        
    async def invoke(self, input, config=None ):
        if "function_call" in input.additional_kwargs:
            tool_call = input.additional_kwargs["function_call"]
            name = tool_call["name"]
            args = eval(tool_call["arguments"])  # use safer parse in real code
            # call the tool
            result = await self.browser_session.session.call_tool(name, args)
            return result
        return input.content


class BrowserAgent:
    """_summary_
    Uses a model and playright MCP client to visit various pages and scrape the deatils.
    """
    
    def __init__(self, model, playrightServerUrl:str):
        """_summary_
        take
        """
        self.llm = model
        self.playright_mcp_server_url = playrightServerUrl
        
    
    async def connect_to_streamable_http_server(self, server_url: str, 
                                                headers: Optional[dict] = None) -> BrowserSession:
        """Connect to an MCP server running with HTTP Streamable transport"""
        
        stream_http_client = streamablehttp_client(  # pylint: disable=W0201
            url=server_url,
            headers=headers or {},
        )
        
        read_stream, write_stream, _ = await stream_http_client.__aenter__()  # pylint: disable=E1101

        _session_context = ClientSession(read_stream, write_stream)  # pylint: disable=W0201
        session: ClientSession = await _session_context.__aenter__()  # pylint: disable=C2801

        await session.initialize()
        
        browser_session = BrowserSession(read_stream, write_stream, session, stream_http_client)
        return browser_session
    
    
    async def processQueries(self, query:str, ) -> str :
        """_summary_

        Args:
            query (str): _description_

        Returns:
            str: _description_
        """
        messages = [{"role": "user", "content": query}]
        
        playright_session = await self.connect_to_streamable_http_server(self.playright_mcp_server_url)        
        
        tools = await self.getTools(playright_session)    
        # [logger.info(x) for x in tools]
    
        llm_with_tools = self.llm.bind_tools(tools)
        
        chain =  llm_with_tools | ToolExecutor(browser_session=playright_session) 
        result = await chain.invoke(messages)

        await playright_session.close()
        
        return "done"


    async def getTools(self, browser_session:BrowserSession) -> list:
        
        # it should be in the following format
        #[{ 
        #     "name": tool.name,
        #     "description": tool.description,
        #     "input_schema": tool.inputSchema
        # }] 
        
        result = []
        tools =  await browser_session.session.list_tools()
        for t in tools:
            if isinstance(t, tuple) and (len(t) == 2 and t[0]=='tools' ) :
                # logger.info(f"tools = {t[1]}, {type(t[1])}")
                if isinstance(t[1], list):
                    for n, x in enumerate(t[1]):
                        # logger.info(f"tool[{n}] = {x}")
                        o1 = {
                                "name": x.name,
                                "description": x.description,
                                "input_schema": x.inputSchema
                              }
                        
                        result.append(o1)
                    
        return result
    
        
    async def fetchDetails(self):
        await self.processQueries("find the capital of qatar, by going to https://www.google.com")



    
    

def initModel() -> ChatGoogleGenerativeAI:
    
    load_dotenv()
    # Your API keys are now available as environment variables
    googleapi_key = os.getenv("GOOGLE_API_KEY")
    logger.info(f"Google Api Key = {googleapi_key}")
    
    llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash-001")
    
    # Create a simple human message
    message = HumanMessage(content="What is the capital of France?")

    # Invoke the model
    response = llm.invoke([message])

    # Print the response
    logger.info(f"query={message.content}, response={response.content}")
    
    logger.info(f"model successfully initialized")

    return llm
        

if __name__ == "__main__" :
    
    model = initModel()
    agent = BrowserAgent(model=model, playrightServerUrl="http://localhost:9876/mcp")
    
    #asyncio.run( agent.connect("http://localhost:9876/mcp", "browser"))
    asyncio.run( agent.fetchDetails() )