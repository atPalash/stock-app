import httpx


async def make_post(endpoint: str, data:dict, timeout=1*60*60):
    async with httpx.AsyncClient() as client:
        r = await client.post(f"http://localhost:9000/{endpoint}", json=data, timeout=timeout)
        return r