#!/usr/bin/env python

import sys

import genipc
from indenter import Indenter

js_map = {
    "int": "number",
    "string": "string",
    "list": "array",
    "dictionary": "xmmsclient.Dict",
    "binary": "xmmsclient.Bindata",
    "collection": "xmmsclient.Collection",
}

def jstype(typ):
    if typ in js_map:
        typ = js_map[typ]
    else:
        typ = "object"
    return typ


def camel_case(s):
    return ''.join(x.capitalize() for x in s.split('_'))

def build(ipc):
    Indenter.printline("# This module is automatically generated by XMMS2. Do not edit.")
    Indenter.printline("if module?.exports?\n\txmmsclient = require \"./xmmsclient\"")
    Indenter.printline("else\n\txmmsclient = @xmmsclient")

    for object in ipc.objects:
        camel_name = camel_case(object.name)

        Indenter.printline("# %s" % camel_name)
        Indenter.printline("class %s" % camel_name)
        Indenter.enter("")
        Indenter.printline("object_id: %d" % object.id)
        Indenter.printline("constructor: (@client) ->")
        Indenter.printline()

        for method in object.methods:
            emit_method_code(object, method, "")

        for signal in object.signals:
            emit_method_code(object, signal, "signal_")

        for broadcast in object.broadcasts:
            emit_method_code(object, broadcast, "broadcast_")

        Indenter.leave()
        Indenter.printline("xmmsclient.Client.IPC.%s = %s" % (camel_name, camel_name))
        Indenter.printline()

    Indenter.printline("module.exports = xmmsclient")


def emit_method_code(object, method, name_prefix):
    method_name = name_prefix + method.name
    arguments = getattr(method, "arguments", [])


    s = ", ".join(a.name for a in arguments)
    if len(arguments) > 0:
        Indenter.enter("%s: (%s) ->" % (method_name, s))
    else:
        Indenter.enter("%s: ->" % method_name)

    Indenter.printline("### %s ###" % method.documentation)

    for a in arguments:
        if len(a.type) > 1:
            subtype = jstype(a.type[1])
            s = "%s = xmmsclient.Message.check_%s %s, \"%s\""
            Indenter.printline(s % (a.name, a.type[0], a.name, subtype))
        else:
            s = "%s = xmmsclient.Message.check_%s %s"
            Indenter.printline(s % (a.name, a.type[0], a.name))

    if arguments:
        Indenter.printline()

    Indenter.printline("message = new xmmsclient.Message()")

    if not name_prefix:
        Indenter.printline("message.object_id = @object_id")
        Indenter.printline("message.command_id = %i" % method.id)
        s = ", ".join(a.name for a in arguments)
        Indenter.printline("message.args = [%s]" % s)
    elif name_prefix == "signal_":
        Indenter.printline("message.object_id = 0")
        Indenter.printline("message.command_id = 32")
        Indenter.printline("message.args = [%i]" % method.id)
    elif name_prefix == "broadcast_":
        Indenter.printline("message.object_id = 0")
        Indenter.printline("message.command_id = 33")
        Indenter.printline("message.args = [%i]" % method.id)

    Indenter.printline()

    if name_prefix == "signal_":
        Indenter.printline("return @client.send_signal_message message, %i" % method.id)
    else:
        Indenter.printline("return @client.send_message message")
    Indenter.leave("")
    Indenter.printline()

ipc = genipc.parse_xml(sys.argv[1])
build(ipc)
