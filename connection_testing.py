from asyncua import Client


async def main():
    host = "input_host_name_here"
    port = "input_port_here"
    host_path = "/"
    username = "username"
    password = "password"

    client_url = f"opc.tcp://{host}:{port}{host_path}"
    opc_client = Client(url=client_url)
    opc_client.set_user(username)
    opc_client.set_password(password)

    await opc_client.connect()
    node = opc_client.nodes.server_state
    node_value = node.get_value()
    print(f"{node_value}")

    await opc_client.disconnect()


if __name__ == "__main__":
    await main()