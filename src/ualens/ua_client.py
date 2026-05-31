import asyncio
import logging

from asyncua import Client

logger = logging.getLogger(__name__)

# OPC UA built-in DataType NodeIds (namespace 0) → human-readable names
_BUILTIN_DATATYPES: dict[int, str] = {
    1: "Boolean", 2: "SByte", 3: "Byte", 4: "Int16", 5: "UInt16",
    6: "Int32", 7: "UInt32", 8: "Int64", 9: "UInt64", 10: "Float",
    11: "Double", 12: "String", 13: "DateTime", 14: "Guid",
    15: "ByteString", 17: "NodeId", 21: "Structure", 22: "DataValue",
}


class SubscriptionHandler:
    def __init__(self, callback):
        self.callback = callback

    def datachange_notification(self, node, val, data):
        if self.callback:
            self.callback(node, val, data)


class UaClient:
    def __init__(self):
        self.client = None
        self.url = None
        self.is_connected = False
        self.subscriptions = {}

    async def connect(self, url: str, username: str = None, password: str = None):
        self.url = url
        self.client = Client(url=self.url)

        if username and password:
            self.client.set_user(username)
            self.client.set_password(password)

        try:
            await asyncio.wait_for(self.client.connect(), timeout=10.0)
            self.is_connected = True
            return True, "Connected"
        except asyncio.TimeoutError:
            self.is_connected = False
            return False, "Connection timed out after 10 seconds"
        except Exception as e:
            self.is_connected = False
            err_msg = str(e) or type(e).__name__
            return False, err_msg

    async def disconnect(self):
        if self.client:
            try:
                await self.client.disconnect()
            except Exception:
                pass
        self.is_connected = False
        self.client = None
        self.subscriptions.clear()

    async def get_children(self, node_id=None):
        if not self.is_connected or not self.client:
            return []

        try:
            if node_id is None:
                node = self.client.get_root_node()
            else:
                node = self.client.get_node(node_id)

            from asyncua import ua
            child_descriptions = await node.get_children_descriptions()

            result = []
            for desc in child_descriptions:
                node_class_name = ua.NodeClass(desc.NodeClass).name
                result.append({
                    "node_id": desc.NodeId,
                    "browse_name": desc.BrowseName.Name,
                    "display_name": desc.DisplayName.Text,
                    "node_class": node_class_name,
                    "handle": self.client.get_node(desc.NodeId)
                })
            return result
        except Exception as e:
            logger.error("Error browsing node %s: %s", node_id, e)
            return []

    async def subscribe(self, node_id, callback):
        if not self.is_connected or not self.client:
            return None

        try:
            node = self.client.get_node(node_id)
            handler = SubscriptionHandler(callback)
            sub = await self.client.create_subscription(1000, handler)
            handle = await sub.subscribe_data_change(node)
            self.subscriptions[node_id] = (sub, handle)
            return sub
        except Exception as e:
            logger.error("Error subscribing to node %s: %s", node_id, e)
            return None

    async def unsubscribe(self, node_id):
        if node_id in self.subscriptions:
            sub, handle = self.subscriptions.pop(node_id)
            try:
                await sub.unsubscribe(handle)
                await sub.delete()
            except Exception as e:
                logger.error("Error unsubscribing from node %s: %s", node_id, e)

    async def read_node_value(self, node_id):
        """Read the current value of a node. Returns None on error or when disconnected."""
        if not self.is_connected or not self.client:
            return None
        try:
            return await self.client.get_node(node_id).read_value()
        except Exception as e:
            logger.error("Error reading value for node %s: %s", node_id, e)
            return None

    async def get_node_attributes(self, node_id) -> dict:
        if not self.is_connected or not self.client:
            return {}

        from asyncua import ua

        attrs_to_read = [
            ua.AttributeIds.NodeId,
            ua.AttributeIds.NodeClass,
            ua.AttributeIds.BrowseName,
            ua.AttributeIds.DisplayName,
            ua.AttributeIds.Description,
            ua.AttributeIds.Value,
            ua.AttributeIds.DataType,
            ua.AttributeIds.AccessLevel,
            ua.AttributeIds.ValueRank,
            ua.AttributeIds.MinimumSamplingInterval,
        ]
        attr_names = {
            ua.AttributeIds.NodeId: "NodeId",
            ua.AttributeIds.NodeClass: "NodeClass",
            ua.AttributeIds.BrowseName: "BrowseName",
            ua.AttributeIds.DisplayName: "DisplayName",
            ua.AttributeIds.Description: "Description",
            ua.AttributeIds.Value: "Value",
            ua.AttributeIds.DataType: "DataType",
            ua.AttributeIds.AccessLevel: "AccessLevel",
            ua.AttributeIds.ValueRank: "ValueRank",
            ua.AttributeIds.MinimumSamplingInterval: "MinimumSamplingInterval",
        }

        result = {}
        try:
            node = self.client.get_node(node_id)
            data_values = await node.read_attributes(attrs_to_read)
            for attr_id, dv in zip(attrs_to_read, data_values):
                if dv.StatusCode.is_good() and dv.Value is not None:
                    val = dv.Value.Value
                    if attr_id == ua.AttributeIds.NodeClass:
                        val = ua.NodeClass(val).name if val is not None else "N/A"
                    elif attr_id == ua.AttributeIds.AccessLevel:
                        val = ua.AccessLevel.parse_bitfield(val)
                        val = ", ".join(a.name for a in val) if val else "N/A"
                    elif attr_id == ua.AttributeIds.BrowseName:
                        val = val.Name if hasattr(val, "Name") else str(val)
                    elif attr_id == ua.AttributeIds.DisplayName:
                        val = val.Text if hasattr(val, "Text") else str(val)
                    elif attr_id == ua.AttributeIds.DataType and val is not None:
                        if val.NamespaceIndex == 0 and val.Identifier in _BUILTIN_DATATYPES:
                            val = _BUILTIN_DATATYPES[val.Identifier]
                        else:
                            val = str(val)
                    result[attr_names[attr_id]] = str(val) if val is not None else "N/A"
                else:
                    result[attr_names[attr_id]] = "(not available)"
        except Exception as e:
            logger.error("Error reading attributes for node %s: %s", node_id, e)
        return result
