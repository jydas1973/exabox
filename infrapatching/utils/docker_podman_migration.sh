#!/bin/sh
#
# $Header: ecs/exacloud/exabox/infrapatching/utils/docker_podman_migration.sh /main/1 2023/06/13 04:49:25 josedelg Exp $
#
# docker_podman_migration.sh
#
# Copyright (c) 2023, Oracle and/or its affiliates. 
#
#    NAME
#      docker_podman_migration.sh - fix podman bridge config file
#
#    DESCRIPTION
#      This script is requires only for migration from ol7 to ol8
#      Podman is the new container engine used in ol8, podman requires fix the next config file
#      /etc/cni/net.d/87-podman-bridge.conflist
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    josedelg    03/01/23 - Enh 34989435 - Migration docker to podman
#                           (ol7 to ol8)
#    josedelg    03/01/23 - Creation
#

SUCCESS=0
FAILURE=1

# Podman config file
CONFLIST_FILE="/etc/cni/net.d/87-podman-bridge.conflist"

# Podman bridge config file content
CONFLIST_CONTENT=$(cat <<EOF
{
  "cniVersion": "0.4.0",
  "name": "podman",
  "plugins": [
    {
      "type": "bridge",
      "bridge": "cni-podman0",
      "isGateway": true,
      "ipMasq": true,
      "hairpinMode": true,
      "ipam": {
        "type": "host-local",
        "routes": [{ "dst": "0.0.0.0/0" }],
        "ranges": [
          [
            {
              "subnet": "169.254.10.0/24",
              "gateway": "169.254.10.1"
            }
          ]
        ]
      }
    },
    {
      "type": "portmap",
      "capabilities": {
        "portMappings": true
      }
    },
    {
      "type": "firewall"
    },
    {
      "type": "tuning"
    }
  ]
}
EOF
)

#################
# Main function.
#
#################
main() {
  _result="$SUCCESS"

  # Stop all podman containers
  sudo podman kill $(sudo podman ps -q)

  # Remove cni-podman0 network interface
  sudo ip link del cni-podman0

  # Create podman config file
  sudo echo "$CONFLIST_CONTENT" | sudo tee "$CONFLIST_FILE"

  exit "$_result"
}

main "$@"
