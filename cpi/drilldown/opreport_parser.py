# -*- coding: utf-8 -*-

"""
Copyright (C) 2017 IBM Corporation

Licensed under the Apache License, Version 2.0 (the “License”);
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an “AS IS” BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

    Contributors:
        * Roberto Oliveira <rdutra@br.ibm.com>
        * Rafael Peria de Sene <rpsene@br.ibm.com>
"""

import xml.etree.ElementTree as elemTree
import cpi.drilldown.opreport_model


class OpreportParser(object):
    """ Class to parse the xml generated by opreport """
    def __init__(self):
        # Init lists to hold opreport model
        self.binmodule_list = []
        self.symboldata_list = []
        self.symboldetail_list = []

    def parse(self, report_file):
        """ Parse the opreport xml """
        tree = elemTree.parse(report_file)
        self.root = tree.getroot()

        # Parse xml elements
        self.parse_symboldetail()
        self.parse_symboldata()
        self.parse_binmodule('module')
        self.parse_binmodule('binary')
        return self.binmodule_list

    def parse_binmodule(self, tag):
        """
        Parse 'binary' and 'module' tags from opreport xml depending
        on the 'tag' argument received.
        Binary tag contains samples of files inside the binary
        Module tag contains samples of libs/modules used by the binary
        """
        for binmodule in self.root.iter(tag):
            name = binmodule.attrib['name']
            # count tag is optional for binary, as may not have samples on it
            count = binmodule.find('count')
            if count is None:
                count = 0
            else:
                count = int(count.text)

            symbol_list = self.parse_symbol(binmodule)
            bmodule = opreport_model.BinModule(name, count, symbol_list)
            self.binmodule_list.append(bmodule)

    def parse_symbol(self, binmodule):
        """ Parse 'symbol' tag from opreport xml """
        symbol_list = []

        for symbol in binmodule.iter('symbol'):
            idref = symbol.attrib['idref']
            count = symbol.find('count')
            count = int(count.text)

            # Get the corresponding symboldata for the current symbol
            symboldata = None
            for sdata in self.symboldata_list:
                if idref == sdata.get_id():
                    symboldata = sdata

            sbl = opreport_model.Symbol(idref, count, symboldata)
            if not self.check_symbol(sbl):
                symbol_list.append(sbl)
        return symbol_list

    def check_symbol(self, symbol):
        """
        Check if the symbol is already added. This checking is necessary
        because the original 'binary' is parent for all symbols, so to not
        add duplicated symbols we need to check if symbol is already added.
        """
        for bmodule in self.binmodule_list:
            if symbol in bmodule.get_symbol_list():
                return True
        return False

    def parse_symboldata(self):
        """ Parse 'symboldata' tag from opreport xml """
        for sdata in self.root.iter('symboldata'):
            i = sdata.attrib['id']
            name = sdata.attrib['name']
            # File tag is optional
            if 'file' in sdata.attrib:
                file_name = sdata.attrib['file']
            else:
                file_name = "??"
            # Line tag is optional
            if 'line' in sdata.attrib:
                line = sdata.attrib['line']
            else:
                line = "0"

            # Get the corresponding symboldetails for the current symboldata
            symboldetails = None
            for sdetail in self.symboldetail_list:
                if i == sdetail.get_id():
                    symboldetails = sdetail

            sym_data = opreport_model.SymbolData(i, name, file_name, line,
                                                 symboldetails)
            self.symboldata_list.append(sym_data)

    def parse_symboldetail(self):
        """ Parse 'symboldetails' tag from opreport xml """
        for sdetails in self.root.iter('symboldetails'):
            detaildata_list = []
            i = sdetails.attrib['id']
            # Iterate over 'detaildata' tag
            for ddata in sdetails.iter('detaildata'):
                # line tag is optional
                if 'line' in ddata.attrib:
                    line = ddata.attrib['line']
                else:
                    line = "0"
                count = ddata.find('count')
                count = int(count.text)
                detaildata = opreport_model.DetailData(line, count)

                # If the element is aleady in the list, increment the
                # current count for the line
                if detaildata in detaildata_list:
                    index = detaildata_list.index(detaildata)
                    ddata = detaildata_list[index]
                    detaildata.set_count(count + ddata.get_count())
                    del detaildata_list[index]
                else:
                    symbol_details = opreport_model.SymbolDetails(i,
                                                                  detaildata_list)
                    self.symboldetail_list.append(symbol_details)

                detaildata_list.append(detaildata)
