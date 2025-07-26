
import asyncio
from dotenv import load_dotenv
import os

from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from mcp_use import MCPAgent, MCPClient
import openai

def init() -> MCPAgent:
    load_dotenv()
    
    # Your API keys are now available as environment variables
    openai_key = os.getenv("OPENAI_API_KEY")
    
    config = {
      "mcpServers": {
        "playwright": {
          "command": "npx",
          "args": ["@playwright/mcp@latest"],
        }
      }
    }

    try:
        client = MCPClient.from_dict(config)
        print("✅ MCPClient created successfully")

        llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash-001")
        #llm = ChatOpenAI(model="gpt-4")
        print("✅ LLM initialized successfully")

        #global agent
        agent = MCPAgent(llm=llm, client=client, max_steps=30)
        print("✅ MCPAgent created successfully")

        print("\n🎉 Installation verified! You're ready to use mcp_use.")
        
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        print("Please check your installation and API keys.")
        
    return agent


async def find_states(agent:MCPAgent) -> list[str]:
    query = """
    Go to the following URL: https://en.wikipedia.org/wiki/States_and_union_territories_of_India#States_and_Union_territories
    Perform the following steps:
    Extract the table entries under both the "States" and "Union territories" sections. 
    For each entry, collect the following fields:
        "name": Name of the state or union territory
        "isoCode": ISO 3166-2 code (if available)
        "type": "state" or "union territory"
    Return the results as a JSON only
    Send the intermediate steps separately
    """
    
    #result = await agent.run(query)
    
    async for item in agent.stream(query):
        if isinstance(item, str):
            # Final result
            result = item
            print(f"\n✅ Final Result:\n{item}")
        else:
            # Intermediate step (action, observation)
            action, observation = item
            print(f"\n🔧 Tool: {action.tool}")
            print(f"📝 Input: {action.tool_input}")
            print(f"📄 Result: {observation[:100]}{'...' if len(observation) > 100 else ''}")

    
    print(f"output {result}")
    
    return []

async def main(agent:MCPAgent):
    
    query = """Navigate to https://google.com?ui=html, search for the 'mayor of sunnyvale, ca'.
        explore the first 5 links and fetch the name of the Mayor.
        After finding the name of the Mayor, find his official website, email, phone and twitter handle.
        
        provide the output in a JSON format.
        """
        
    async for item in agent.stream(query):
        if isinstance(item, str):
            # Final result
            print(f"\n✅ Final Result:\n{item}")
        else:
            # Intermediate step (action, observation)
            action, observation = item
            print(f"\n🔧 Tool: {action.tool}")
            print(f"📝 Input: {action.tool_input}")
            print(f"📄 Result: {observation[:100]}{'...' if len(observation) > 100 else ''}")

    # result = await agent.run(query,)
    # print(f"\nResult: {result}")
    
def check_openai():
    openai_key = os.getenv("OPENAI_API_KEY")
    print(f"open ai key {openai_key}")
    
    client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY"),)
    
    response = client.responses.create(
        model="gpt-4o",
        instructions="You are a coding assistant that talks like a pirate.",
        input="How do I check if a Python object is an instance of a class?",
        )

    print(response.output_text)



if __name__ == "__main__":
   agent = init()
   #check_openai()
   asyncio.run(main(agent))
   #asyncio.run(find_states(agent))
