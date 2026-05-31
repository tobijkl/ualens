import argparse
import asyncio
import logging
import random

from asyncua import Server, ua
from asyncua.server.user_managers import UserManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SimpleUserManager(UserManager):
    def __init__(self, username, password):
        self.username = username
        self.password = password

    def check_user_token(self, isession, token):
        if not token or token.UserName is None or token.UserName == "":
            logger.warning("Anonymous access rejected")
            return False

        if token.UserName == self.username and token.Password == self.password:
            logger.info(f"User '{token.UserName}' authenticated successfully")
            return True

        logger.warning(f"Authentication failed for user '{token.UserName}'")
        return False


async def run_server(username=None, password=None):
    server = Server()
    await server.init()

    url = "opc.tcp://127.0.0.1:4840/freeopcua/server/"
    server.set_endpoint(url)
    server.set_server_name("UaLens Test Server")

    if username and password:
        logger.info("Configuring authentication for user: %s", username)
        server.set_security_policy([ua.SecurityPolicyType.NoSecurity])
        user_manager = SimpleUserManager(username, password)
        server.user_manager = user_manager
    else:
        logger.info("Running in anonymous mode (no authentication)")

    uri = "http://github.com/ualens/mock-server"
    idx = await server.register_namespace(uri)

    my_obj = await server.nodes.objects.add_object(idx, "SimulationDevice")

    temp = await my_obj.add_variable(idx, "Temperature1", 20.0)
    temp2 = await my_obj.add_variable(idx, "Temperature2", 45.0)
    press = await my_obj.add_variable(idx, "Pressure", 1013.25)
    status = await my_obj.add_variable(idx, "Status", "Idle")
    counter = await my_obj.add_variable(idx, "Counter", 0)
    counter2 = await my_obj.add_variable(idx, "Counter2", 10)

    await temp.set_writable()
    await temp2.set_writable()
    await press.set_writable()
    await status.set_writable()
    await counter.set_writable()
    await counter2.set_writable()

    logger.info("Server started at %s", url)

    async with server:
        count = 0
        while True:
            await asyncio.sleep(1)

            new_temp = round(20.0 + random.uniform(-1.0, 1.0), 2)
            new_temp2 = round(45.0 + random.uniform(-3.0, 3.0), 2)
            new_press = round(1013.25 + random.uniform(-5.0, 5.0), 2)
            new_status = random.choice(["Running", "Idle", "Error", "Maintenance"])
            count += 1

            await temp.write_value(new_temp)
            await temp2.write_value(new_temp2)
            await press.write_value(new_press)
            await status.write_value(new_status)
            await counter.write_value(count)
            await counter2.write_value(count + 10)


def main() -> None:
    parser = argparse.ArgumentParser(description="OPC UA mock server for ualens development and testing")
    parser.add_argument("--username", "-u", type=str, help="Username for authentication")
    parser.add_argument("--password", "-p", type=str, help="Password for authentication")
    args = parser.parse_args()

    try:
        asyncio.run(run_server(username=args.username, password=args.password))
    except KeyboardInterrupt:
        logger.info("Server stopped")


if __name__ == "__main__":
    main()
