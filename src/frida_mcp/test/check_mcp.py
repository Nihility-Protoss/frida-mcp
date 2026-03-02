import asyncio
from fastmcp import Client

async def main():
    async with Client("http://127.0.0.1:8032/mcp") as client:
        result = await client.call_tool(
            name="config_get",
            arguments={}
        )
    print(result.content[0].text)

asyncio.run(main())