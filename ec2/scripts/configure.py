########
# Copyright (c) 2015 GigaSpaces Technologies Ltd. All rights reserved
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
#    * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    * See the License for the specific language governing permissions and
#    * limitations under the License.

# Built-in Imports
import json
import tempfile

# Third Party Imports
import fabric.api

# Cloudify Imports
from cloudify import ctx
from ec2 import configure
from ec2 import constants


def configure_manager(config_path, agents_security_group, agents_keypair):
    _upload_credentials(config_path)
    _set_provider_config(agents_security_group, agents_keypair)


def _upload_credentials(config_path):
    temp = configure.BotoConfig().get_temp_file()
    fabric.api.put(temp, config_path)


def _set_provider_config(agents_security_group, agents_keypair):

    resources = dict()
    node_instances = ctx._endpoint.storage.get_node_instances()
    nodes_by_id = \
        {node.id: node for node in ctx._endpoint.storage.get_nodes()}

    node_id_to_provider_context_field = {
        'agents_security_group': 'agents_security_group',
        'management_security_group': 'management_security_group',
        'manager_server_ip': 'elastic_ip',
        'management_keypair': 'management_keypair',
        'agent_keypair': 'agents_keypair'
    }

    for node_instance in node_instances:
        if node_instance.node_id in node_id_to_provider_context_field:
            run_props = node_instance.runtime_properties
            props = nodes_by_id[node_instance.node_id].properties
            provider_context_field = \
                node_id_to_provider_context_field[node_instance.node_id]
            resources[provider_context_field] = {
                'external_resource': props['use_external_resource'],
                'id': run_props[constants.EXTERNAL_RESOURCE_ID],
            }

    provider = {
        'resources': resources
    }

    ctx.instance.runtime_properties['provider_context'] = provider

    temp_config = tempfile.mktemp()

    with open(temp_config, 'w') as provider_context_file:
        json.dump(provider, provider_context_file)

    fabric.api.put(temp_config, constants.AWS_DEFAULT_CONFIG_PATH)