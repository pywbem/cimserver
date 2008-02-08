#!/usr/bin/env python
#
# (C) Copyright 2007 Novell, Inc. 
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#   
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#   
# You should have received a copy of the GNU Lesser General Public
# License along with this program; if not, write to the Free Software
# Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
#

# Author: Bart Whiteley <bwhiteley suse.de>

from twisted.web import http
import pywbem
from pywbem import tupleparse
import cimserver
from cStringIO import StringIO
import sys

cxd = None

class MyRequestHandler(http.Request):
    def process(self):
        print self.content.read()
        self.content.seek(0,0)
        try:
            tt = tupleparse.xml_to_tupletree(self.content.read())
            tt = tupleparse.parse_cim(tt)
            mid = tt[2][1]['ID']
            tt = tt[2][2][0][2]
            method = tt[0]
            rmethod = method == 'METHODCALL' and 'METHODRESPONSE' or \
                            'IMETHODRESPONSE'
            op = tt[1]['NAME']
            print 'operation:', op
            if method == 'METHODCALL':
                fn = 'invokemethod'
            else:
                fn = op.lower()
            try:
                fn = getattr(cxd, fn)
            except AttributeError:
                raise pywbem.CIMError(pywbem.CIM_ERR_FAILED, 
                        'Unknown operation: %s' % op)
            resp = """<?xml version="1.0" ?>
            <CIM CIMVERSION="2.0" DTDVERSION="2.0">
              <MESSAGE ID="%s" PROTOCOLVERSION="1.0">
                 <SIMPLERSP>
                    <%s NAME="%s">""" % (mid, rmethod, op)
            if method == 'IMETHODCALL':
                resp+= '<IRETURNVALUE>'
            output = StringIO()
            output.write(resp)
            fn(tt, output)
            if method == 'IMETHODCALL':
                resp = '</IRETURNVALUE>'
            else:
                resp = ''
            resp+= """</%s>
                </SIMPLERSP>
              </MESSAGE>
            </CIM>""" % rmethod
            output.write(resp)
            self.write(output.getvalue().encode('utf8'))
            output.close()

        except pywbem.CIMError, arg:
            num = arg.args[0]
            descr = ''
            if len(arg.args) > 1:
                descr = arg.args[1]
            import traceback
            traceback.print_exc(file=sys.stdout)
            print 'sending error', descr
            msg = """<?xml version="1.0" encoding="utf-8" ?>
                <CIM CIMVERSION="2.0" DTDVERSION="2.0">
                  <MESSAGE ID="%s" PROTOCOLVERSION="1.0">
                    <SIMPLERSP>
                      <%s NAME="%s">
                        <ERROR CODE="%s" DESCRIPTION="%s"/>
                      </%s>
                    </SIMPLERSP>
                  </MESSAGE>
                </CIM>""" % (mid, rmethod, op, num, descr, rmethod)
            self.write(msg.encode('utf8'))
                    
        print 'calling finish()'
        self.finish()

class MyHttp(http.HTTPChannel):
    requestFactory = MyRequestHandler

class MyHttpFactory(http.HTTPFactory):
    protocol = MyHttp

if __name__ == '__main__':
    global cxd
    cxd = cimserver.CIMXMLDispatch()
    from twisted.internet import reactor
    reactor.listenTCP(8000, MyHttpFactory())
    reactor.run()

