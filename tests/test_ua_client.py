"""Tests for UaClient and SubscriptionHandler."""

import asyncio
import pytest
from ualens.ua_client import UaClient, SubscriptionHandler


async def test_connect_success(opcua_server):
    client = UaClient()
    success, message = await client.connect("opc.tcp://127.0.0.1:48401/freeopcua/server/")
    assert success is True
    assert client.is_connected is True
    await client.disconnect()
    assert client.is_connected is False


async def test_connect_failure():
    client = UaClient()
    success, message = await client.connect("opc.tcp://127.0.0.1:48402/freeopcua/server/")
    assert success is False
    assert client.is_connected is False
    assert isinstance(message, str)


async def test_connect_sets_url():
    client = UaClient()
    url = "opc.tcp://127.0.0.1:48402/freeopcua/server/"
    await client.connect(url)
    assert client.url == url


async def test_disconnect_when_not_connected():
    client = UaClient()
    await client.disconnect()
    assert client.is_connected is False
    assert client.client is None


async def test_get_children_when_disconnected():
    client = UaClient()
    result = await client.get_children()
    assert result == []


async def test_get_children_when_connected_none_returns_root_children(opcua_server):
    client = UaClient()
    await client.connect("opc.tcp://127.0.0.1:48401/freeopcua/server/")
    root_children = await client.get_children()
    assert len(root_children) > 0
    objects_node = next((c for c in root_children if c["display_name"] == "Objects"), None)
    assert objects_node is not None
    await client.disconnect()


async def test_get_children_with_node_id(opcua_server):
    client = UaClient()
    await client.connect("opc.tcp://127.0.0.1:48401/freeopcua/server/")
    root_children = await client.get_children()
    objects_node = next((c for c in root_children if c["display_name"] == "Objects"), None)
    assert objects_node is not None
    obj_children = await client.get_children(objects_node["node_id"])
    assert len(obj_children) > 0
    my_obj = next((c for c in obj_children if c["display_name"] == "MyObject"), None)
    assert my_obj is not None
    await client.disconnect()


async def test_get_children_result_structure(opcua_server):
    client = UaClient()
    await client.connect("opc.tcp://127.0.0.1:48401/freeopcua/server/")
    root_children = await client.get_children()
    for child in root_children:
        assert "node_id" in child
        assert "browse_name" in child
        assert "display_name" in child
        assert "node_class" in child
        assert "handle" in child
    await client.disconnect()


async def test_get_node_attributes_when_disconnected():
    client = UaClient()
    result = await client.get_node_attributes("ns=2;i=42")
    assert result == {}


async def test_get_node_attributes_when_connected(opcua_server):
    client = UaClient()
    await client.connect("opc.tcp://127.0.0.1:48401/freeopcua/server/")
    objects = await client.get_children()
    obj_node = next(c for c in objects if c["display_name"] == "Objects")
    obj_children = await client.get_children(obj_node["node_id"])
    my_obj = next(c for c in obj_children if c["display_name"] == "MyObject")
    my_obj_children = await client.get_children(my_obj["node_id"])
    my_var = next(c for c in my_obj_children if c["display_name"] == "MyVariable")

    attrs = await client.get_node_attributes(my_var["node_id"])
    assert "NodeId" in attrs
    assert "BrowseName" in attrs
    assert "DisplayName" in attrs
    assert "NodeClass" in attrs
    assert attrs["NodeClass"] == "Variable"
    assert "Value" in attrs
    await client.disconnect()


async def test_subscribe_when_disconnected():
    client = UaClient()
    result = await client.subscribe("ns=2;i=42", lambda n, v, d: None)
    assert result is None


async def test_subscription(opcua_server):
    client = UaClient()
    await client.connect("opc.tcp://127.0.0.1:48401/freeopcua/server/")

    objects = await client.get_children()
    obj_node = next(c for c in objects if c["display_name"] == "Objects")
    obj_children = await client.get_children(obj_node["node_id"])
    my_obj = next(c for c in obj_children if c["display_name"] == "MyObject")
    my_obj_children = await client.get_children(my_obj["node_id"])
    my_var = next(c for c in my_obj_children if c["display_name"] == "MyVariable")

    future = asyncio.get_running_loop().create_future()

    def callback(node, val, data):
        if not future.done() and val == 12.3:
            future.set_result(val)

    sub = await client.subscribe(my_var["node_id"], callback)
    assert sub is not None
    assert my_var["node_id"] in client.subscriptions

    server_var = await opcua_server.nodes.root.get_child(
        ["0:Objects", "2:MyObject", "2:MyVariable"]
    )
    await server_var.write_value(12.3)

    result = await asyncio.wait_for(future, timeout=5.0)
    assert result == 12.3

    await client.unsubscribe(my_var["node_id"])
    assert my_var["node_id"] not in client.subscriptions
    await client.disconnect()


async def test_unsubscribe_when_not_subscribed():
    client = UaClient()
    await client.unsubscribe("ns=2;i=999")
    assert "ns=2;i=999" not in client.subscriptions


async def test_subscription_handler_calls_callback():
    received = []

    def callback(node, val, data):
        received.append((node, val, data))

    handler = SubscriptionHandler(callback)
    handler.datachange_notification("node", 42, "data")
    assert received == [("node", 42, "data")]


async def test_subscription_handler_no_callback():
    handler = SubscriptionHandler(None)
    handler.datachange_notification("node", 42, "data")


async def test_read_node_value_when_disconnected():
    client = UaClient()
    result = await client.read_node_value("ns=2;i=42")
    assert result is None


async def test_read_node_value_when_connected(opcua_server):
    client = UaClient()
    await client.connect("opc.tcp://127.0.0.1:48401/freeopcua/server/")
    objects = await client.get_children()
    obj_node = next(c for c in objects if c["display_name"] == "Objects")
    obj_children = await client.get_children(obj_node["node_id"])
    my_obj = next(c for c in obj_children if c["display_name"] == "MyObject")
    my_obj_children = await client.get_children(my_obj["node_id"])
    my_var = next(c for c in my_obj_children if c["display_name"] == "MyVariable")

    val = await client.read_node_value(my_var["node_id"])
    assert val is not None
    assert isinstance(val, float)
    await client.disconnect()


async def test_read_node_value_invalid_node(opcua_server):
    client = UaClient()
    await client.connect("opc.tcp://127.0.0.1:48401/freeopcua/server/")
    result = await client.read_node_value("ns=99;i=99999")
    assert result is None
    await client.disconnect()


async def test_connect_timeout():
    """Connecting to a non-listening port fails with an error, not a timeout."""
    client = UaClient()
    success, message = await client.connect("opc.tcp://127.0.0.1:48403/freeopcua/server/")
    assert success is False
    assert isinstance(message, str)
