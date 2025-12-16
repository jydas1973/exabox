"""
 Copyright (c) 2014, 2024, Oracle and/or its affiliates.

NAME:
    Monitor - Basic functionality

FUNCTION:
    Provide basic/core API for Cluster Monitoring (Collect info/stats, HTML report...)

NOTE:
    None

History:
    mirivier    08/20/2015 - Create file
    mrajm       05/04/2017 - Bug 25869256: Add logs download link
    seha        01/25/2018 - Enh 27427661: Add diagnostic module logs download link
    oespinos    06/27/2018 - Bug 28250045: add AgentCtrl url params (refresh, cmdtype, clustername)
    oespinos    07/09/2018 - Bug 28314445: allow /AgentCtrl results to be paged
    ndesanto    06/12/2019 - Bug 29901307: AgentCtrl fix for Oracle DB
    gurkasin    06/05/2019 - Enh 29472639: Changed exacloud log file name
    araghave    07/02/2019 - ENH 29911293: POSTCHECK OPTION FOR ALL PATCH OPERATIONS.
    ndesanto    10/02/2019 - Enh 30374491: EXACC PYTHON 3 MIGRATION BATCH 02
    araghave    20/02/2020 - Enh 30908782: ksplice configuration on dom0 and cells
    araghave    28/02/2024 - Enh 36295801 - IMPLEMENT ONEOFFV2 PLUGIN EXACLOUD CHANGES
"""

try:
    from collections import OrderedDict
except ImportError:
    from collections.abc import OrderedDict

from exabox.core.Core import ebCoreContext
from exabox.core.Context import get_gcontext
from exabox.log.LogMgr import ebLogError, ebLogInfo, ebLogWarn, ebLogDebug, ebThreadLocalLog, ebLogAgent
from exabox.core.Node import exaBoxNode
from exabox.core.DBStore import ebGetDefaultDB
import time, re, os, sys
import json
import random
import ast

from exabox.core.Core import ebExit
from exabox.core.Error import build_error_string

class ebClusterNode(object):

    def __init__(self):

        self.__cluid     = None
        self.__hostname  = None
        self.__nodetype  = None
        self.__network   = None

        self.__pingable  = None
        self.__ssh_conn  = None
        self.__pwd_auth  = None
        self.__root_sshd = None
        self.__weak_pwd  = None

        self.__dict_data = {}

        self.__sw_default = None
        self.__sw_allcas  = None

    def mGetClusterId(self):
        return self.__cluid

    def mSetClusterId(self,aClusterId):
        self.__cluid = aClusterId

    def mSetHostname(self, aHostname):
        self.__hostname = aHostname

    def mGetHostname(self):
        return self.__hostname

    def mSetNodeType(self, aType):
        self.__nodetype = aType

    def mGetNodeType(self):
        return self.__nodetype

    def mSetNetworkIp(self, aNetwork):
        self.__network = aNetwork

    def mGetNetworkIp(self):
        return self.__network

    def mSetPingable(self, aMode):
        self.__pingable = aMode

    def mGetPingable(self):
        return self.__pingable

    def mSetSSHConnection(self, aMode):
        self.__ssh_conn = aMode

    def mGetSSHConnection(self):
        return self.__ssh_conn

    def mSetPwdAuthentication(self, aMode):
        self.__pwd_auth = aMode

    def mGetPwdAuthentication(self):
        return self.__pwd_auth

    def mSetRootSSHDMode(self, aMode):
        self.__root_sshd = aMode

    def mGetRootSSHDMode(self):
        return self.__root_sshd

    def mSetWeakPassword(self, aMode):
        self.__weak_pwd = aMode

    def mGetWeakPassword(self):
        return self.__weak_pwd

    def mSetSwitchDefault(self, aDefault):
        self.__sw_default = aDefault

    def mGetSwitchDefault(self):
        return self.__sw_default

    def mSetSwitchAllCas(self, aAllCas):
        self.__sw_allcas = aAllCas

    def mGetSwitchAllCas(self):
        return self.__sw_allcas

    def mGetDictData(self):
        return json.dumps(self.__dict_data)

    def mSetDictData(self,aData):
        self.__dict_data = aData

    def mPopulate(self,aReq):

        _req = aReq
        if _req:
            self.mSetClusterId(_req[0])
            self.mSetHostname(_req[1])
            self.mSetNodeType(_req[2])
            self.mSetNetworkIp(_req[3])
            self.mSetPingable(ast.literal_eval(_req[4]))
            self.mSetSSHConnection(ast.literal_eval(_req[5]))
            self.mSetPwdAuthentication(ast.literal_eval(_req[6]))
            self.mSetRootSSHDMode(ast.literal_eval(_req[7]))
            self.mSetWeakPassword(ast.literal_eval(_req[8]))
            self.mSetDictData(json.loads(_req[9]))

    def mToString(self):

        _out_str  = ' pingable: '+str(self.mGetPingable())
        _out_str += ' nodetype: '+str(self.mGetNodeType())
        _out_str += ' pwd_auth: '+str(self.mGetPwdAuthentication())
        _out_str += ' root_key_only: '+str(self.mGetRootSSHDMode())
        _out_str += ' weak_pwd: '+str(self.mGetWeakPassword())
        if self.mGetNodeType() == 'switch':
            _out_str += ' sw_default: '+str(self.mGetSwitchDefault())
            _out_str += ' sw_all_cas: '+str(self.mGetSwitchAllCas())
        return _out_str

    def mToStatusLabels(self):
        _html_labels   = ''
        _label = '<span class="label label-%s">%%s</span>\n'
        _boolean_to_label = {True  : _label % 'success',
                             False : _label % 'danger',
                             None  : _label % 'default'}
        _html_labels += _boolean_to_label[self.mGetPingable()]          % 'Ping'
        _html_labels += _boolean_to_label[self.mGetWeakPassword()]      % 'WeakPwd'
        _html_labels += _boolean_to_label[self.mGetPwdAuthentication()] % 'PwdAuth'
        _html_labels += _boolean_to_label[self.mGetRootSSHDMode()]      % 'RootKeyOnly'
        _html_labels += _boolean_to_label[self.mGetSSHConnection()]     % 'Connect'
        return _html_labels

    def mToHtml2(self):
        _html_lgrou = """<div class="tab-pane fade in %s"><div class="list-group">
          <a href="#" class="list-group-item">

            <div class="row">
                <div class="col-md-9"><h4><span class="badge">%s</span> %s</h4></div>
                <div class="col-md-3 text-right">
                    <div class="btn-group" data-toggle="buttons"><span><h4></h4></span>
                    <label class="btn btn-xs text-right" role="button" data-toggle="collapse" data-target="#%s">
                        <input type="checkbox" autocomplete="off"><span class="glyphicon glyphicon-menu-hamburger"></span>
                    </label>
                    </div>
                </div>
            </div>

            <div class="row">
                <div class="col-md-4">IP: %s</div>
                <div class="col-md-8 text-right">%s</div>
            </div>

          </a>
          <div class="collapse" id="%s">
            <div class="list-group-item collapse">
                %s
            </div>
          </div>
        </div>
        </div>
        """
        _html_hostname = self.mGetHostname()
        _html_ip       = self.mGetNetworkIp()
        _html_labels   = self.mToStatusLabels()

        _stats = ''
        _dict_data = self.mGetDictData()
        if _dict_data:
            _dict_data = json.loads(_dict_data)
            _tables = ''

            if 'top' in _dict_data:
                _tables += build_html_table('top', _dict_data['top'])

            if 'xentop' in _dict_data:
                _tables += build_html_table('xentop', list(zip(*_dict_data['xentop'])))

            if 'xminfo' in _dict_data:
                _tables += build_html_table('xm info', _dict_data['xminfo'])


        return _html_lgrou % ( self.mGetClusterId(), self.mGetNodeType(), _html_hostname, _html_hostname.split('.')[0],_html_ip, _html_labels, _html_hostname.split('.')[0], _tables)

# build html table based on a list of rows
def build_html_table(aName, aRows):
    if not aRows:
        return ''

    _table = """<table class="table table-striped">
                <thead>
                <tr class="info">
                    <th>
                    %s
                    </th>
                    %%s
                </tr>
                </thead>
                <tbody>
                    %%s
                </tbody>
                </table>
             """ % aName
    _tbody = """<tr>
                    %s
                </tr>
             """
    _html_rows = ''
    for _row in aRows:
        _tds = ''
        for _item in _row:
            _tds += '<td>%s</td>\n' % _item
        _html_rows += _tbody % _tds

    _header_padding = '<th></th>' * (len(aRows[0]) - 1)
    return _table % (_header_padding, _html_rows)

def build_clusterwide_status(aName, aNodes):
    _node_labels = {'dom0'   : 'label-default',
                    'domu'   : 'label-default',
                    'cell'   : 'label-default',
                    'switch' : 'label-default'}

    _list_view = ''

    for _type, _nodes in list(sorted_cluster_nodes(aNodes, aDict=True).items()):
        _list_view += '<div class="list-group-item list-group-item-info">%s</div>' % _type
        if _nodes:
            for _node in _nodes:
                if not _node.mGetPingable() or not _node.mGetSSHConnection():
                    _node_labels[_node.mGetNodeType()] = 'label-danger'
                elif _node_labels[_node.mGetNodeType()] == 'label-default':
                    _node_labels[_node.mGetNodeType()] = 'label-success'

                _list_view += '<div class="list-group-item">%s<span class="pull-right">%s</span></div>' % (_node.mGetHostname(), _node.mToStatusLabels())
        else:
            _list_view += '<div class="list-group-item">no information available in database</div>'



    _labels = ''
    for _type, _label in list(_node_labels.items()):
        _labels += '<span class="label %s">%s</span>\n' % (_label, _type)

    _toggle_id = aName + '_overview'

    _html_lgrou = """<div class="tab-pane fade in active cluster-node"><div class="list-group">

            <a href="#" class="list-group-item">
            <div class="row">
                <div class="col-md-9">
                    <h4 style="display:inline;margin-right:10px;margin-top:20px;">%s</h4>
                    %s

                </div>
                <div class="col-md-3 text-right">
                    <div class="btn-group" data-toggle="buttons"><span><h4></h4></span>
                    <label class="btn btn-xs text-right" role="button" data-toggle="collapse" data-target="#%s">
                        <input type="checkbox" autocomplete="off"><span class="glyphicon glyphicon-menu-hamburger"></span>
                    </label>
                    </div>
                </div>
             </div>

            <div class="row">
                <div class="col-md-12">%s</div>
            </div>
            </a>

            <div class="collapse" id="%s">
            <div class="list-group">
            %s
            </div>
            </div>

        </div>
        </div>
        """
    return _html_lgrou % (aName, aNodes[0].mGetClusterId(), _toggle_id, _labels, _toggle_id, _list_view)

def build_cluster_html_page(aClusterNodes):

    _clusters = {}
    for _cluster in list(aClusterNodes.values()):
        _cluster_id = _cluster.mGetClusterId()
        if _cluster_id in _clusters:
            _clusters[_cluster_id].append(_cluster)
        else:
            _clusters[_cluster_id] = [_cluster]


    _nav_tab   = '<li><a href=".%s" data-toggle="tab">%s</a></li>'
    _nav_tab_s = '<li class="active"><a href=".cluster-node" data-toggle="tab">overview</a></li>'

    _tab_content = """
                        <div class="jumbotron tab-pane fade in %s"><h1>%s<h1>
                        <h4>%s</h4>
                        </div>
                   """

    _cluster_id_l = []
    _clusters_l = os.listdir('clusters/')
    for _entry in _clusters_l:
        if _entry[:len('cluster-')] == 'cluster-':
            _cluster_id_l.append(_entry)

    _cluster_overview = ''
    _tab_content_s = ''
    for _id in sorted(_cluster_id_l):
        _full_path = os.path.join('clusters', _id)
        _cid = os.readlink(_full_path)
        if _cid[-1] == '/':
            _cid = _cid[:-1]
        _cid = _cid.split('/')[-1]
        _nav_tab_s += _nav_tab % (_cid,_id)
        _tab_content_s += _tab_content % (_cid, _id, _cid)
        if _cid in list(_clusters.keys()):
            _cluster_overview += build_clusterwide_status(_id, _clusters[_cid])
        else:
            ebLogWarn('*** cluster id: %s not in current cluster list skipping building html view.' % (_id))

    _html_page = build_html_page_header() + """
    <div class="container">

        <div class="row">
            <div class="col-sm-2">
                <div><h2>Clusters</h2></div>
                <ul class="nav nav-pills nav-stacked">
                    %s
                </ul>
            </div>

            <div class="col-sm-10">
                <div id="alert_placeholder"></div>

                <div class="tab-content">
                    %s

                    <div class="jumbotron tab-pane fade in active cluster-node"><h1>Overview</h1>
                        <h4>cluster wide operations
                            <button id="refresh_button" type="button" class="btn btn-default pull-right" onclick="refresh_state()">Refresh Status</button>
                        </h4>
                    </div>
                    %s
                    %s      <!-- :0 cluster configurations -->
                </div>
            </div>
        </div>
    </div>""" + build_html_page_footer()

    _html_panels = ''

    _sorted_list = sorted_cluster_nodes(list(aClusterNodes.values()))

    for _node in _sorted_list:
        _html_panels += _node.mToHtml2()

    return _html_page % (_nav_tab_s, _tab_content_s, _cluster_overview, _html_panels)

# sort cluster nodes by the order of dom0, domu, cell, switch
def sorted_cluster_nodes(aNodes, aDict=False):
    _dom0s    = []
    _domUs    = []
    _cells    = []
    _switches = []
    _nodes = sorted(aNodes, key=lambda x : x.mGetHostname())
    for _obj in _nodes:
        if _obj.mGetNodeType() == 'dom0':
            _dom0s.append(_obj)
        elif _obj.mGetNodeType() == 'domu':
            _domUs.append(_obj)
        elif _obj.mGetNodeType() == 'cell':
            _cells.append(_obj)
        elif _obj.mGetNodeType() == 'switch':
            _switches.append(_obj)

    if aDict:
        return {'dom0' : _dom0s, 'domu' : _domUs, 'cell' : _cells, 'switch' : _switches}
    else:
        return _dom0s + _domUs + _cells + _switches

def build_html_page_header(auto_refresh=True):

    _html_page_header = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
    """

    if auto_refresh:
        _html_page_header += """<meta http-equiv="refresh" content="60">"""

    _html_page_header += """
    <meta charset="utf-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <!-- The above 3 meta tags *must* come first in the head; any other head content must come *after* these tags -->
    <title>Cluster Info</title>
    <!-- inlined style -->
    <style>
        body { padding-top: 70px }
        .right .github-fork-ribbon { background-color: #090; }
    </style>
    </head>

    <body>
    <nav class="navbar navbar-default navbar-fixed-top navbar-inverse">
      <div class="container-fluid">
        <!-- Brand and toggle get grouped for better mobile display -->
        <div class="navbar-header">
          <button type="button" class="navbar-toggle collapsed" data-toggle="collapse" data-target="#bs-example-navbar-collapse-1">
            <span class="icon-bar"></span>
            <span class="icon-bar"></span>
            <span class="icon-bar"></span>
          </button>
          <a class="navbar-brand" href="/AgentHome">Exacloud Agent</a>
        </div>

        <!-- Collect the nav links, forms, and other content for toggling -->
        <div class="collapse navbar-collapse" id="bs-example-navbar-collapse-1">
          <ul class="nav navbar-nav">
            <li><a href="/AgentPortal"><span class="glyphicon glyphicon-cog"></span> Configuration</a></li>
            <li><a href="/AgentCluster"><span class="glyphicon glyphicon-tasks"></span> Cluster Status</a></li>
            <li><a href="/AgentWorkers"><span class="glyphicon glyphicon-user"></span> Workers</a></li>
            <li><a href="/AgentCtrl"><span class="glyphicon glyphicon-inbox"></span> Request Info</a></li>
          </ul>
          <ul class="nav navbar-nav navbar-right">
            <li><a href="#" id="btnAbout" data-toggle="modal" data-target="#aboutModal"">About</a></li>
          </ul>
        </div><!-- /.navbar-collapse -->
      </div><!-- /.container-fluid -->
    </nav>

    <!--about modal-->
    <div id="aboutModal" class="modal fade" role="dialog">
      <div class="modal-dialog">
      <div class="modal-content">
          <div class="modal-header">
              <button type="button" class="close" data-dismiss="modal">&times;</button>
              <h2 class="text-center">About Exacloud Agent</h2>
          </div>
          <div class="modal-body">
                <p>This release of the exacloud agent portal is still in beta and is known to have issues and limitations.</p>
                <p>However we believe that even with those it is still a usefull tool to help monitor and trouble shoot deployment and existing clusters.</p>
                <p>Make sure to voice your feature requirements since we care for this part of exacloud and want to make it as user friendly and usefull as possible.</p>
          </div>
          <div class="modal-footer">
              <button class="btn" data-dismiss="modal" aria-hidden="true">OK</button>
          </div>
      </div>
      </div>
    </div>

    <!-- TOP RIGHT RIBBON: START COPYING HERE -->
    <div class="github-fork-ribbon-wrapper right fixed">
        <div class="github-fork-ribbon">
            <a href="/AgentHome">%s</a>
        </div>
    </div>"""
    #
    # Populate html_page_header
    #
    try:
        with open('config/release.dat') as _f:
            _ribbon_data=_f.read()
    except IOError:
        _ribbon_data = 'Exacloud Agent'

    return _html_page_header % (_ribbon_data)

def build_html_page_footer(aLastpage=1):

    _html_page_footer = """
    <script>
    function set_alert(message, type) {
        $('#alert_placeholder').html('<div class="alert alert-' + type + '"><a href="#" class="close" data-dismiss="alert" aria-lable="close">&times;</a><strong>' + type + '!</strong> ' + message + '</div>');
    }
    function refresh_state() {
        try {
            $.ajax({
                type: "GET",
                dataType: "json",
                url: "/Monitor?cmd=refresh",
                success: function(data){
                    set_alert("refreshing all clusters", "success");
                }

            });
        } catch(err) {
            set_alert(err.message, "danger");
        }

    }

    MAXPAGE=%s
    function last_page() {
      var url = window.location.href
      var spliturl = url.split("?")
      var desturl = spliturl[0]
      pagenum = 1
      separator = "?"
      if (spliturl.length > 1) {
        params = spliturl.slice(1)
        for (var i in params) {
          if (params[i].startsWith("pagenum")) {
            pagenum = params[i].split('=')[1]
            pagenum = parseInt(pagenum)
          }
          else {
            desturl += separator + params[i]
            separator = "?"
          }
        }
      }
      pagenum = Math.min(MAXPAGE, pagenum)
      pagenum = Math.max(1, pagenum-1)
      desturl += separator + "pagenum=" + pagenum
      location.assign(desturl)
    }

    function next_page() {
      var url = window.location.href
      var spliturl = url.split("?")
      var desturl = spliturl[0]
      pagenum = 1
      separator = "?"
      if (spliturl.length > 1) {
        params = spliturl.slice(1)
        for (var i in params) {
          if (params[i].startsWith("pagenum")) {
            pagenum = params[i].split('=')[1]
            pagenum = parseInt(pagenum)
          }
          else {
            desturl += separator + params[i]
            separator = "?"
          }
        }
      }
      pagenum = Math.max(1, pagenum)
      pagenum = Math.min(MAXPAGE, pagenum+1)
      desturl += separator + "pagenum=" + pagenum
      location.assign(desturl)
    }

    </script>
    </body>
    </html>
    """
    return _html_page_footer % (aLastpage)

def build_requests_html_page(auto_refresh=True, aParams=None):

    if not aParams:
        aParams = dict()

    _default_pagesize = get_gcontext().mCheckConfigOption("agent_pagesize")
    _clustername = aParams.get("clustername")
    _cmdtype = aParams.get("cmdtype")
    _pagesize = aParams.get("pagesize")
    _pagenum = aParams.get("pagenum")

    if not isinstance(_pagenum, int):
        _pagenum = 1;

    if not isinstance(_pagesize, int):
        _pagesize = int(_default_pagesize)

    _offset = (_pagenum - 1) * _pagesize
    _db = ebGetDefaultDB()
    _body = _db.mGetUIRequests(aClustername=_clustername, aCmdtype=_cmdtype, aLimit=_pagesize, aOffset=_offset)
    _rowcount = _db.mGetUIRowCount(_clustername, _cmdtype)[0]
    _pagecount = _rowcount / _pagesize

    if _rowcount % _pagesize or _pagecount == 0:
        _pagecount += 1

    _error = None
    _list = []
    try:
        _list = ast.literal_eval(_body)
    except Exception as e:
        _error = "Error retrieving requests information from Database."
        ebLogError("Error retrieving requests from Database. Original exception:\n" + str(e))

    _idx_status = 1
    _idx_cmdtype = 4
    _idx_err = 8
    _idx_cname = 11

    # Order list by endtime descending

    def order_requests(request_row):

        starttime_idx = 2
        endtime_idx = 3

        if request_row[endtime_idx] == "Undef":
            return time.mktime(time.strptime(request_row[starttime_idx]))
        else:
            return time.mktime(time.strptime(request_row[endtime_idx]))

    _list = sorted(_list, key=order_requests, reverse=True)

    # Build HTML Table (one row at a time)

    _ecrequests = []

    for _row in _list:

        _cmdt_s = _row[4]
        _req_type = _cmdt_s
        _cluster_name = _row[11]

        # Compute _elapsed time(_elapsed_s)

        _start_t = time.mktime(time.strptime(_row[2]))

        if "Undef" not in [_row[2], _row[3]]:

            _end_t = time.mktime(time.strptime(_row[3]))
            _elapsed_t = _end_t - _start_t

            _h, _r = divmod(_elapsed_t, 3600)
        else:

            _ctime    = time.time()
            _celapsed = _ctime - _start_t

            _h, _r = divmod(_celapsed, 3600)

        _m, _s = divmod(_r, 60)
        _elapsed_s = "{:0>2}:{:0>2}:{:05.2f}".format(int(_h), int(_m), _s)

        # Build UUID link(_uuid_n)

        _uuid_n = _row[0]
        _cmdt_s = _row[4]

        _params = ast.literal_eval(_row[5])

        _requestID = "0000-0000-0000-0000"
        if ("request_id" in list(_params.keys())) and (_params["request_id"] is not None):
            _requestID = str(_params["request_id"])

        _step = ""
        if ("steplist" in list(_params.keys())) and (_params["steplist"] is not None):
            _step = "."+str(_params["steplist"])

        _undo = ""
        if ("undo" in list(_params.keys())) and (_params["undo"]=="True"):
            _undo = ".undo"

        _log_filename = _requestID+"/"+_uuid_n+"_"+_cmdt_s+_step+_undo

        if _cmdt_s == "cluctrl.collect_log":
            _link_s = "/AgentCtrl?file=log/diagnostic/"+_uuid_n+"_"+_cmdt_s+".log"
        else:
            _link_s = "/AgentCtrl?file=log/threads/"+_log_filename+".log"

        _uuid_s = '<a href="{}">{}</a>'.format(_uuid_n, _link_s)

        _cluster_name = _row[11]

        if _cluster_name == "Undef" and _row[4].startswith("patch"):
            _cluster_name = "Lead Patch Operation"

        _uuid_x = {
            "clustername": _cluster_name,
            "uuid": _uuid_n,
            "logfile": _link_s
        }

        # Cluster Configuration (_cluster_conf_s)

        _params_d = ast.literal_eval(_row[5])

        if "configpath" in list(_params_d.keys()):
            _link_s = "/AgentCtrl?ccluster="+_row[0]
            _cluster_conf_f = _params_d["configpath"].split("/")[-1]

            #clean up cluster conf string (usually includes trailing unnecessary characters)
            bpos = _cluster_conf_f.find(">")
            if bpos>-1:
                _cluster_conf_f = _cluster_conf_f[:bpos]

            _cluster_conf_s = {
                "config_link": _link_s,
                "config_file": _cluster_conf_f
            }
        else:
            _cluster_conf_s = "N/A" # Patch request doesn't have a specified cluster. Default value should be used.

        # Access Params/JSON configuration(_cmdt_s)

        _link_s = "/AgentCtrl?cparams="+_row[0]
        _req_type = _cmdt_s
        _cmdt_s = {
            "request_link": _link_s,
            "request_file": _row[4]
        }

        # change and reorder row contents

        _row = [ _uuid_s, _row[1], _row[10], _row[2], _row[3], _elapsed_s, _cmdt_s, _cluster_conf_s, _row[6], _row[7] ]

        # Error / Error Info

        if (_row[_idx_err]=="701-99") or (_row[_idx_err] in ["701-614","703-614"]) or (_row[_idx_err]!="0" and _row[_idx_err]!="Undef"):
            _error_info_s = {
                "err_code": _row[_idx_err],
                "err_text": _row[9]
            }
        elif _row[_idx_err]=="0":
            _error_info_s = {
                "err_code": _row[_idx_err],
                "err_text": ""
            }
        else:
            _error_info_s = {
                "err_code": "N/A",
                "err_text": "N/A"
            }

        # Status / Status Info / Progress Bar

        if _row[_idx_status]=="Done" or _row[_idx_status]=="Pending":
            _status_info_span_s = _row[_idx_status]
        else:
            _status_info_span_s = "N/A"

        # Progress Bar

        if len(_row[2].split(":"))!=3:
            uuid = re.search("/([\w\d\-]+)_", _row[0]).group(1)
            ebLogWarn("*** Status info for request {0} doesn't have a valid format".format(uuid))
            _row[2] = "000::No status info available"

        _pb_rc, _pb_percent, _pb_info = _row[2].split(":")
        #_pb_rc      [000|True|False]
        #_pb_percent [NULL|Percent]
        #_pb_info    DESCRIPTION

        if _pb_percent!="":
            _percent = str(int(_pb_percent))
        elif _pb_rc=="000":
            _percent = "0"
        else:
            _percent = "100"

        if _percent=="100":
            _pb_desc = "Done"
        else:
            _pb_desc = _percent+"%"

        if _row[4]!="Undef" and _pb_rc=="000" and _percent=="0":

            if _row[_idx_err]=="0":
                _status_info_sum_s = ("Success", _pb_info)
                _pb_desc = "Done"
            else:
                _status_info_sum_s = ("Failure", _pb_info)

        elif _pb_rc=="True" and (_row[_idx_err]=="0" or _row[_idx_err]=="Undef"):

            if _percent!="100":
                _status_info_sum_s = ("In Progress", _pb_info)
            else:
                _status_info_sum_s = ("Success", _pb_info)

        elif _pb_rc=="False" or (_row[_idx_err]!="0" and _row[_idx_err]!="Undef"):

            # Show info (blue) bar when we have error 0x0614. It means the patch request was done but no action was taken because nodes where already at the intended version.
            if _row[_idx_err]!="0" and _row[_idx_err].find("-614")>=0 and _percent=="100":
                _status_info_sum_s = ("Success", _pb_info)
            else:
                _status_info_sum_s = ("Failure", _pb_info)

        elif _pb_rc=="000" and _percent=="100":

            if _row[_idx_err]!="0" and _row[_idx_err]!="Undef":
                _status_info_sum_s = ("Failure", _pb_info)
            else:
                _status_info_sum_s = ("Success", _pb_info)

        else:
            _status_info_sum_s = ("In Progress", _pb_info)

        # Status Info

        _status_info_x = {
            "status": _status_info_span_s,
            "progress": {
                "progress_desc": _pb_desc,
                "percent": _percent
            },
            "description": {
                "status": _status_info_sum_s[0],
                "description": _status_info_sum_s[1]
            }
        }

        # OEDA Info/Logs

        _tar_link_s = "/logDownload?uuid=%s"

        if _req_type.startswith("patch."):
            _oeda_log_type = "patch logs"
            _oeda_log_s = "/PatchLogs?uuid=%s?patch=True"
        elif _req_type.startswith("cluctrl.") and _req_type.split(".")[1] in ["patch_prereq_check","postcheck", "backup_image", "patch", "rollback_prereq_check", "rollback", "oneoff", "oneoffv2" ]:
            _oeda_log_type = "cluctrl logs"
            _oeda_log_s = "/OedaLogs?uuid=%s"
        elif _req_type.startswith("bmcctrl."):
            _oeda_log_type = "bmcctrl logs"
            _oeda_log_s = "/BMCCtrlLogs?uuid=%s?bmcctrl=True"
        else:
            _oeda_log_type = "oeda logs"
            _oeda_log_s = "/OedaLogs?uuid=%s"

        _log_s = {
            "log_type": _oeda_log_type,
            "log_link": _oeda_log_s % (re.search(">.*<", _uuid_s)).group(0)[1:-1],
            "tar_link": _tar_link_s % (re.search(">.*<", _uuid_s)).group(0)[1:-1]
        }

        # Build Time Dictionary

        _tz  = " ("+time.strftime("%Z")+")"
        _tzs = ""
        _tze = ""

        if _row[3] != "Undef":
            _tzs = _tz
        if _row[4] != "Undef":
            _tze = _tz

        _time_info = {
            "start_time": _row[3]+_tzs,
            "end_time":   _row[4]+_tze,
        }

        # Build Final Dictionary for Request

        _ecrequests.append({
            "uuid":           _uuid_x,
            "status_info":    _status_info_x,
            "time_start_end": _time_info,
            "time_elapsed":   _elapsed_s,
            "request_type":   _cmdt_s,
            "cluster_config": _cluster_conf_s,
            "oeda_info_logs": _log_s,
            "error_info":     _error_info_s
        })

    return _ecrequests

#EOF
