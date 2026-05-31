"""Shared pytest configuration and fixtures."""

import pytest
from asyncua import Server
import pytest_asyncio


@pytest_asyncio.fixture
async def opcua_server():
    """Start an in-process OPC UA server for tests."""
    server = Server()
    await server.init()
    server.set_endpoint("opc.tcp://127.0.0.1:48401/freeopcua/server/")
    uri = "http://examples.freeopcua.github.io"
    idx = await server.register_namespace(uri)

    myobj = await server.nodes.objects.add_object(idx, "MyObject")
    myvar = await myobj.add_variable(idx, "MyVariable", 6.7)
    await myvar.set_writable()

    async with server:
        yield server
