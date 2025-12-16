<?xml version="1.0" ?>
<engineeredSystem xmlns="model">
    <actions examigrate="nothing">
        <action>
            <subCommand/>
        </action>
    </actions>
    <configKeys>
        <configKey/>
    </configKeys>
    <customerName xmlgen="rackname_callback"/>
    <databases>
        <database cmdfx="databaseFx" cname="DATABASE" xmlgen="db_callback">
            <cdbId xmlType="v1"/>
            <characterset cname="CHARSET"/>
            <databaseBlockSize cname="BLOCKSIZE"/>
            <databaseHome cname="DBHOMEID" pk="True"/>
            <databaseOwner/>
            <databaseSid cname="DBNAME"/>
            <databaseStyle/>
            <databaseTemplate cname="DBTEMPLATE"/>
            <databaseType xmlType="v1" cname="DBTYPE"/>
            <diskGroups>
                <diskGroup cname="DG"/>
            </diskGroups>
            <language cname="DBLANG"/>
            <machines>
                <machine cname="HOSTNAMES"/>
            </machines>
            <version/>
        </database>
    </databases>
    <departmentName/>
    <esPrefix/>
    <esRacks>
        <esRack xmlgen="es_rack_callback">
            <esRackItem>
                <rackItemDescription/>
                <rackItemFamily/>
                <rackItemSerialNumber/>
                <rackLocation/>
                <uHeight/>
                <uLocation/>
                <version/>
            </esRackItem>
            <rackDescription/>
            <rackType/>
            <rackUSize/>
            <version/>
        </esRack>
    </esRacks>
    <exacloud_signature cmdfx="colorpatching">
        <exacloud_server/>
        <exacloud_version/>
        <last_update/>
        <operation/>
    </exacloud_signature>
    <groups>
        <group xmlgen="group_callback">
            <groupId/>
            <groupName/>
            <groupType/>
            <version/>
        </group>
    </groups>
    <iloms>
        <ilom xmlgen="ilom_callback">
            <dnsServers>
                <dnsServer>
                    <ipAddress examigrate="overrideParentFx" cname="DNSSERVERS"/>
                </dnsServer>
            </dnsServers>
            <ilomName/>
            <ilomTimeZone/>
            <networks>
                <network/>
            </networks>
            <ntpServers>
                <ntpServer>
                    <ipAddress examigrate="overrideParentFx" cname="NTPSERVERS"/>
                </ntpServer>
            </ntpServers>
            <version/>
        </ilom>
        <version xmlType="v1"/>
    </iloms>
    <machines>
        <machine cmdfx='machineFx' cname="MACHINE" xmlgen="machine_callback">
            <DefaultGatewayNet cname="GATEWAYADAPTER"/>
            <DomUImageName/>
            <ImageVersion/>
            <TimeZone cname="TIMEZONE"/>
            <dnsServers>
                <dnsServer>
                    <ipAddress examigrate="overrideParentFx" cname="DNSSERVERS"/>
                </dnsServer>
            </dnsServers>
            <guestCores examigrate="vmSizeFx" xmlType="v2" cmdfx="vmSizeFx"/>
            <guestLocalDiskSize examigrate="vmSizeFx" xmlType="v2" cmdfx="vmSizeFx"/>
            <guestMemory examigrate="vmSizeFx" xmlType="v2" cmdfx="vmSizeFx"/>
            <hostName/>
            <iloms>
                <ilom/>
            </iloms>
            <machine/>
            <machineSubType/>
            <machineType/>
            <networks>
                <network/>
            </networks>
            <storageType/>
            <excVolProtocol/>
            <edvVolumes>
                <edvVolume/>                                                                                                                                                                                                                                       
            </edvVolumes>
            <ntpServers>
                <ntpServer>
                    <ipAddress examigrate="overrideParentFx" cname="NTPSERVERS"/>
                </ntpServer>
            </ntpServers>
            <osType/>
            <software>
                <clusters>
                    <cluster/>
                </clusters>
                <databaseHomes cmdfx="nothing">
                    <databaseHome/>
                </databaseHomes>
            </software>
            <storage>
                <localDisks>
                    <localDisk/>
                </localDisks>
            </storage>
            <users>
                <user/>
            </users>
            <version/>
            <virtual/>
            <vmSizeName cmdfx='nothing' xmlType="v1"/>
            <writeBackFlashCache/>
        </machine>
    </machines>
    <networks>
        <network cname="NETWORK" cmdfx="networkFx" xmlgen="network_callback">
            <domainName cname="DOMAINNAME"/>
            <gateway cname="GATEWAY"/>
            <hostName cname="HOSTNAME" pk="True"/>
            <interfaceName/>
            <ipAddress cname="IP"/>
            <lacp/>
            <acceleratedNetwork/>
            <linkSpeed/>
            <macAddress xmlType="v1" cname="MAC"/>
            <master cname="MASTER"/>
            <mtu cname="MTU"/>
            <natdomainName xmlType="v1" cname="NATDOMAINNAME"/>
            <nategressipaddresses>
                <nategressipaddress/>
            </nategressipaddresses>
            <natGateway cname="NATGATEWAY"/>
            <nathostName xmlType="v1" cname="NATHOSTNAME"/>
            <natipAddress xmlType="v1" cname="NATIP"/>
            <natnetMask xmlType="v1" cname="NATNETMASK"/>
            <natVlanId cname="NATVLANID"/>
            <netMask cname="NETMASK"/>
            <networkName/>
            <networkType cname="NETWORKTYPE" pk="True"/>
            <pkey cname="PKEY"/>
            <pkeyName cname="PKEYNAME"/>
            <slave cname="SLAVE"/>
            <version/>
            <vlanId cname="VLANID"/>
            <interfaceName cname="INTERFACENAME"/>
            <vswitchNetworkParams xmlType="v1" cname="VSWITCHNETWORKPARAMS"/>
        </network>
    </networks>
    <platinum>
        <platinumEnabled/>
        <version/>
    </platinum>
    <software>
        <clusters>
            <cluster cname="CLUSTER" cmdfx="clusterFx" xmlgen="cluster_callback">
                <asmScopedSecurity cname="ASMSCOPEDSECURITY"/>
                <backupLocation/>
                <basedir cname="BASEDIR"/>
                <clusterHome cname="GIHOMELOC"/>
                <clusterName cname="CLUSTERNAME" pk="True"/>
                <clusterOwner/>
                <clusterScans>
                    <clusterScan/>
                </clusterScans>
                <clusterVersion cname="GIVERSION"/>
                <clusterVips>
                    <clusterVip cmdfx="vipFx" cname="VIP" xmlgen="cluster_vips_callback">
                        <domainName cname="DOMAINNAME"/>
                        <machines>
                            <machine cname="HOSTNAME" pk="True"/>
                        </machines>
                        <vipIpAddress cname="IP"/>
                        <vipName cname="NAME"/>
                    </clusterVip>
                </clusterVips>
                <diskGroups>
                    <diskGroup/>
                </diskGroups>
                <vault cmdfx="vaultFx" cname="VAULT" xmlgen="vault_callback"/>
                <inventoryLocation cname="INVLOC"/>
                <language/>
                <patches>
                    <patch>
                        <patchNumber cname="PATCHLIST"/>
                    </patch>
                </patches>
                <scanIps/>
                <version/>
            </cluster>
            <clusterScans>
                <clusterScan cmdfx="scanFx" cname="SCAN" xmlgen="scans_callback">
                    <scanIps>
                        <scanIp>
                            <ipAddress examigrate="overrideParentFx" cname="SCANIPS"/>
                        </scanIp>
                    </scanIps>
                    <scanName cname="SCANNAME"/>
                    <scanPort cname="SCANPORT"/>
                    <scanType/>
                </clusterScan>
            </clusterScans>
        </clusters>
        <databaseHomes>
            <databaseHome cname="DATABASEHOME" cmdfx="databaseHomeFx" xmlgen="dbhome_callback">
                <basedir cname="BASEDIR"/>
                <cluster cname="CLUSTERID" pk="True"/>
                <databaseHomeLoc cname="DBHOMELOC"/>
                <databaseHomeName cname="DBHOMENAME"/>
                <databaseSwOwner cname="OWNER"/>
                <databaseVersion cname="DBVERSION"/>
                <inventoryLocation cname="INVLOC"/>
                <language cname="DBLANG"/>
                <machines cmdfx="nothing">
                    <machine/>
                </machines>
                <patches>
                    <patch>
                        <patchNumber examigrate="overrideParentFx" cname="PATCHLIST"/>
                    </patch>
                </patches>
                <useZfs cmdfx="nothing"/>
                <version cmdfx="nothing"/>
            </databaseHome>
        </databaseHomes>
    </software>
    <storage>
        <diskGroups>
            <diskGroup cmdfx="diskGroupFx" cname="DISKGROUP" xmlgen="diskgroup_callback">
                <cellDisks/>
                <diskGroupName cname="DISKGROUPNAME" examigrate="diskgroupFx"/>
                <diskGroupSize cname="DISKGROUPSIZE"/>
                <machines>
                    <machine cname="CELLLIST"/>
                </machines>
                <ocrVote cname="OCRVOTE"/>
                <quorumDisk cname="QUORUMDISK"/>
                <redundancy cname="REDUNDANCY"/>
                <sliceSize cname="SLICESIZE"/>
                <version/>
                <acfsVolumeName cname="ACFSNAME"/>
                <acfsVolumeSize cname="ACFSSIZE"/>
                <acfsMountPath cname="ACFSPATH"/>
                <sparse cname="SPARSE"/>
                <sparseVirtualSize cname="SPARSEVIRTUALSIZE"/>
                <diskGroupType/>
            </diskGroup>
            <version/>
        </diskGroups>
        <storagePools cmdfx="storagePoolsFx" cname="STORAGEPOOLS" xmlgen="storagepools_callback">
            <storagePool cmdfx="storagePoolFx" cname="STORAGEPOOL" xmlgen="storagepool_callback">
                <version/>
                <storagePoolName cname="STORAGEPOOLNAME" examigrate="storagePoolFx"/>
                <storagePoolSize cname="STORAGEPOOLSIZE"/>
                <machines>
                    <machine cname="CELLLIST"/>
                </machines>
                <uiSize cname="UISIZE"/>
                <uiSizeType/>
                <storagePoolType/>
            </storagePool>
            <version/>
        </storagePools>
        <localDisks>
            <localDisk xmlgen="local_disk_callback">
                <localDiskName/>
                <localDiskSize/>
                <version/>
            </localDisk>
        </localDisks>
        <edvVolumes>
            <edvVolume xmlgen="edvVolume_callback">
                <edvVolumeName/>
                <edvVolumeSize/>
                <edvVolumeType/>
                <edvDevicePath/>
                <edvMountPath/>
                <vault/>
            </edvVolume>
        </edvVolumes>
        <version/>
        <volumeGroups>
            <volumeGroup xmlgen="volumeGroup_callback">
                <volumeGroupName/>
                <resourceSharing/>
                <edvVolumes>
                    <edvVolume cname="edvVolume"/>
                </edvVolumes>
            </volumeGroup>
        </volumeGroups>
    </storage>
    <storageDesc cmdfx="colorpatching">
        <stAttribute/>
    </storageDesc>
    <switches>
        <switch xmlgen="switch_callback">
            <ibPartitionMembership/>
            <networks>
                <network/>
            </networks>
            <switchDescription/>
            <version/>
        </switch>
    </switches>
    <users>
        <user xmlgen="user_callback">
            <groups>
                <group/>
            </groups>
            <homedir/>
            <userType/>
            <userid/>
            <username/>
            <version/>
        </user>
    </users>
    <version/>
    <vmSizes xmlType="v1">
        <vmSizeName xmlType="v1" xmlgen="vmsize_callback">
            <vmAttribute xmlType="v1" cmdfx="vmSizeFx"/>
        </vmSizeName>
    </vmSizes>
    <exascale cmdfx="exascaleFx" cname="EXASCALE" xmlgen="exascale_callback">
        <exascaleClusters cmdfx="exascaleClustersFx" cname="EXASCALECLUSTERS" xmlgen="exascaleclusters_callback">
            <version/>
            <exascaleCluster cmdfx="exascaleClusterFx" cname="EXASCALECLUSTER" xmlgen="exascale_callback">
                <version/>
                <clusterName cname="CLUSTERNAME" examigrate="clusterNameFx"/>
                <storagePools>
                    <storagePool cname="CELLLIST"/>
                </storagePools>
                <networks>
                    <network cname="ERSIP"/>
                </networks>
            </exascaleCluster>
        </exascaleClusters>
        <vaults cmdfx="vaultsFx" cname="VAULTS" xmlgen="vaults_callback">
            <version/>
            <vault cmdfx="vaultFx" cname="VAULT" xmlgen="vault_callback">
            <version/>
            <storagePools>
                <storagePool cmdfx="storagePoolFx" cname="STORAGEPOOL" xmlgen="storagepool_callback">
                   <storagePoolSize cname="STORAGEPOOLSIZE"/>
                   <storagePoolType/>
                </storagePool>
                <version/>
            </storagePools>
            </vault>
            <vault xmlgen="sysvault_callback">
                <name/>
                <vaultType/>
            </vault>
        </vaults>
    </exascale>
</engineeredSystem>
