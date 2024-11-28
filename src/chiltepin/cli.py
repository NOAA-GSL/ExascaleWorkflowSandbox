import argparse

import chiltepin.endpoint as endpoint


def cli_list(config_dir=None):
    ep_list = endpoint.list(config_dir=config_dir)
    if ep_list:
        name_len = max(len(key) for key in ep_list)
        for name, props in ep_list.items():
            print(f"{name:<{name_len}} {props['id']:<36} {props['state']}")
    else:
        print("No endpoints are configured")


# Create root level parser
root_parser = argparse.ArgumentParser(prog="chiltepin")

# Add subparsers for the chiltepin subcommands
cmd_parsers = root_parser.add_subparsers(
    title="chiltepin commands",
    help="Chiltepin commands",
)

# Add parser for the endpoint command
endpoint_parser = cmd_parsers.add_parser(
    "endpoint",
    help="endpoint commands",
)
endpoint_parser.add_argument(
    "-c",
    "--config",
    dest="config_dir",
    help="configuration directory",
)

# Add subparsers for the endpoint subcommands
endpoint_parsers = endpoint_parser.add_subparsers(
    title="endpoint commands",
    help="endpoint commands",
)

# Add parser for endpoint configure command
configure_parser = endpoint_parsers.add_parser(
    "configure",
    help="configure an endpoint",
)
configure_parser.add_argument("name", help="name of endpoint to configure")
configure_parser.add_argument(
    "-m",
    "--multi",
    action="store_true",
    help="configure a multi templatable endpoint",
)
configure_parser.set_defaults(func=endpoint.configure)

# Add parser for endpoint list command
list_parser = endpoint_parsers.add_parser("list", help="List endpoints")
list_parser.set_defaults(func=cli_list)

# Add parser for endpoint start command
start_parser = endpoint_parsers.add_parser("start", help="start an endpoint")
start_parser.add_argument("name", help="name of endpoint to start")
start_parser.set_defaults(func=endpoint.start)

# Add parser for endpoint stop command
stop_parser = endpoint_parsers.add_parser("stop", help="stop an endpoint")
stop_parser.add_argument("name", help="name of endpoint to stop")
stop_parser.set_defaults(func=endpoint.stop)

# Add parser for endpoint delete command
delete_parser = endpoint_parsers.add_parser("delete", help="delete an endpoint")
delete_parser.add_argument("name", help="name of endpoint to delete")
delete_parser.set_defaults(func=endpoint.delete)


def main():
    args = vars(root_parser.parse_args())
    func = args.pop("func")
    func(**args)
