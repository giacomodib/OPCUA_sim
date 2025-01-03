from asyncua import Client
import asyncio
from concurrent.futures import ThreadPoolExecutor
import logging


class OPCUAClient:
    def __init__(self, url="opc.tcp://localhost:4841/freeopcua/server/"):
        self.url = url
        self.client = None
        self._lock = asyncio.Lock()  # Lock per evitare corse concorrenti
        self.executor = ThreadPoolExecutor(max_workers=1)  # Limita a una sola connessione
        self.loop = None

    async def _ensure_connection(self):
        """Garantisce che il client sia connesso al server OPCUA."""
        async with self._lock:
            if self.client is None:
                try:
                    self.client = Client(url=self.url)
                    await self.client.connect()
                    logging.info("Connesso al server OPCUA con successo!")
                except Exception as e:
                    logging.error(f"Errore durante la connessione al server OPCUA: {e}")
                    self.client = None
                    raise e

    async def get_node_value(self, node_id):
        """Ottiene il valore di un nodo specifico dal server OPCUA."""
        try:
            await self._ensure_connection()
            node = self.client.get_node(node_id)
            value = await node.read_value()
            return value
        except Exception as e:
            logging.error(f"Errore durante il recupero del valore del nodo {node_id}: {e}")
            self.client = None
            return None

    async def set_node_value(self, node_id, value):
        """Imposta un valore a un nodo specifico sul server OPCUA."""
        try:
            await self._ensure_connection()
            node = self.client.get_node(node_id)
            await node.write_value(value)
            return True
        except Exception as e:
            logging.error(f"Errore durante l'impostazione del valore del nodo {node_id}: {e}")
            self.client = None
            return False

    async def get_machine_status(self):
        """Recupera lo stato della macchina dal server OPCUA."""
        try:
            state = await self.get_node_value("ns=2;i=2")  # Stato della macchina
            cutting_speed = await self.get_node_value("ns=2;i=3")  # Velocità di taglio
            feed_rate = await self.get_node_value("ns=2;i=4")  # Velocità di avanzamento
            pieces = await self.get_node_value("ns=2;i=5")  # Pezzi tagliati
            power_consumption = await self.get_node_value("ns=2;i=6")  # Consumo di energia
            temperature = await self.get_node_value("ns=2;i=7")  # Temperatura

            return {
                'state': state,
                'cutting_speed': cutting_speed,
                'feed_rate': feed_rate,
                'pieces': pieces,
                'power_consumption': power_consumption,
                'temperature': temperature
            }
        except Exception as e:
            logging.error(f"Errore durante il recupero dello stato macchina: {e}")
            return {}

    def run_async(self, coro):
        """Esegue una coroutine asincrona nel thread principale (sincrono)."""
        if self.loop is None:  # Se manca un event loop ne crea uno nuovo
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
        return self.loop.run_until_complete(coro)
