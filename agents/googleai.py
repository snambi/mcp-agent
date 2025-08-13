from mcp import ClientSession
from openai import OpenAI
import dotenv, os, logging

dotenv.load_dotenv()

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


def init() -> OpenAI:
    client = OpenAI(
        api_key=os.getenv("GOOGLE_API_KEY"),
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
    )
    return client


def chat(client:OpenAI):
    
    response = client.chat.completions.create(
        model="gemini-2.5-flash",
        reasoning_effort="low",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {
                "role": "user",
                "content": "What is the capital of russia and what is the weather there?"
            }
        ],
        stream=False
        # extra_body={
        #   'extra_body': {
        #     "google": {
        #       "thinking_config": {
        #         "thinking_budget": 800,
        #         "include_thoughts": True
        #       }
        #     }
        #   }
        # }
    )


    # for chunk in response:
    #     print(chunk.choices[0].delta)
        
        

if __name__ == "__main__":
    client = init()
    chat(client=client)