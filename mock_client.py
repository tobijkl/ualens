import asyncio
import logging
from asyncua import Client

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SubscriptionHandler:
    """
    Handler for OPC UA subscriptions.
    """
    def datachange_notification(self, node, val, data):
        logger.info(f"Data change notification: Node {node} value is now: {val}")

async def browse_recursive(node, depth=0):
    """
    Recursively browse nodes and print their names.
    """
    indent = "  " * depth
    try:
        browse_name = await node.read_browse_name()
        display_name = await node.read_display_name()
        node_class = await node.read_node_class()
        
        logger.info(f"{indent}Node: {display_name.Text} ({browse_name.Name}), Class: {node_class.name}, ID: {node.nodeid}")
        
        # Limit depth to avoid infinite recursion or too much output
        if depth < 3:
            children = await node.get_children()
            for child in children:
                await browse_recursive(child, depth + 1)
    except Exception as e:
        logger.error(f"Error browsing node: {e}")

async def main():
    url = "opc.tcp://127.0.0.1:4840/freeopcua/server/"
    client = Client(url=url)
    
    try:
        logger.info(f"Connecting to {url}...")
        await client.connect()
        logger.info("Connected!")

        # 1. Browse the address space
        logger.info("Browsing address space...")
        objects = client.get_objects_node()
        await browse_recursive(objects)

        # 2. Find the Temperature node
        # We can find it by path or by browsing. 
        # In ualens.mock_server it's under SimulationDevice in our custom namespace.
        idx = await client.get_namespace_index("http://github.com/ualens/mock-server")
        logger.info(f"Namespace index for our mock server: {idx}")
        
        # Try to get the node by path
        # Objects -> SimulationDevice -> Temperature1
        temp_node = await objects.get_child([f"{idx}:SimulationDevice", f"{idx}:Temperature1"])
        logger.info(f"Found Temperature node: {temp_node.nodeid}")

        # 3. Subscribe to data changes
        logger.info("Subscribing to Temperature updates...")
        handler = SubscriptionHandler()
        sub = await client.create_subscription(1000, handler)
        handle = await sub.subscribe_data_change(temp_node)
        
        logger.info("Subscription created. Press Ctrl+C to stop.")
        
        # Keep the script running to receive updates
        while True:
            await asyncio.sleep(1)
            
    except asyncio.CancelledError:
        logger.info("Task cancelled")
    except Exception as e:
        logger.error(f"An error occurred: {e}")
    finally:
        logger.info("Disconnecting...")
        await client.disconnect()
        logger.info("Disconnected.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
