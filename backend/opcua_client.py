# opcua_client.py
from asyncua import Client
import asyncio
from concurrent.futures import ThreadPoolExecutor


class OPCUAClient:
    def __init__(self, url="opc.tcp://localhost:4841/freeopcua/server/"):
        self.url = url
        self.client = None
        self._lock = asyncio.Lock()
        self.executor = ThreadPoolExecutor(max_workers=1)
        self.loop = None

    async def _ensure_connection(self):
        if self.client is None:
            try:
                self.client = Client(url=self.url)
                await self.client.connect()
            except Exception as e:
                print(f"Connection error: {e}")
                self.client = None
                raise

    async def get_node_value(self, node_id):
        try:
            await self._ensure_connection()
            node = self.client.get_node(node_id)
            value = await node.get_value()
            return value
        except Exception as e:
            print(f"Error getting node value: {e}")
            self.client = None  # Reset client on error
            return None

    async def set_node_value(self, node_id, value):
        try:
            await self._ensure_connection()
            node = self.client.get_node(node_id)
            await node.write_value(value)
            return True
        except Exception as e:
            print(f"Error setting node value: {e}")
            self.client = None  # Reset client on error
            return False

    def run_async(self, coro):
        if self.loop is None:
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
        return self.loop.run_until_complete(coro)

