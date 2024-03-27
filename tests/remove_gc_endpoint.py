#!/usr/bin/env python

import sys

from globus_compute_sdk import Client

c = Client()

c.delete_endpoint(sys.argv[1])
