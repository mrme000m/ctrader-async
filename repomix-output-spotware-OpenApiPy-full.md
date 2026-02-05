This file is a merged representation of the entire codebase, combined into a single document by Repomix.
The content has been processed where security check has been disabled.

# File Summary

## Purpose
This file contains a packed representation of the entire repository's contents.
It is designed to be easily consumable by AI systems for analysis, code review,
or other automated processes.

## File Format
The content is organized as follows:
1. This summary section
2. Repository information
3. Directory structure
4. Repository files (if enabled)
5. Multiple file entries, each consisting of:
  a. A header with the file path (## File: path/to/file)
  b. The full contents of the file in a code block

## Usage Guidelines
- This file should be treated as read-only. Any changes should be made to the
  original repository files, not this packed version.
- When processing this file, use the file path to distinguish
  between different files in the repository.
- Be aware that this file may contain sensitive information. Handle it with
  the same level of security as you would the original repository.

## Notes
- Some files may have been excluded based on .gitignore rules and Repomix's configuration
- Binary files are not included in this packed representation. Please refer to the Repository Structure section for a complete list of file paths, including binary files
- Files matching patterns in .gitignore are excluded
- Files matching default ignore patterns are excluded
- Security check has been disabled - content may contain sensitive information
- Files are sorted by Git change count (files with more changes are at the bottom)

# Directory Structure
```
.github/
  workflows/
    code_quality_checks.yml
    docs_publish.yml
    pypi_publish.yml
    test_pypi_publish.yml
ctrader_open_api/
  messages/
    __init__.py
    OpenApiCommonMessages_pb2.py
    OpenApiCommonModelMessages_pb2.py
    OpenApiMessages_pb2.py
    OpenApiModelMessages_pb2.py
  __init__.py
  auth.py
  client.py
  endpoints.py
  factory.py
  protobuf.py
  tcpProtocol.py
docs/
  css/
    extra.css
  fonts/
    TitilliumWeb-Black.ttf
    TitilliumWeb-Bold.ttf
    TitilliumWeb-BoldItalic.ttf
    TitilliumWeb-ExtraLight.ttf
    TitilliumWeb-ExtraLightItalic.ttf
    TitilliumWeb-Italic.ttf
    TitilliumWeb-Light.ttf
    TitilliumWeb-LightItalic.ttf
    TitilliumWeb-Regular.ttf
    TitilliumWeb-SemiBold.ttf
    TitilliumWeb-SemiBoldItalic.ttf
  img/
    favicon.ico
    logo.png
  js/
    extra.js
  authentication.md
  client.md
  index.md
overrides/
  main.html
samples/
  ConsoleSample/
    main.py
    README.md
  jupyter/
    credentials.json
    main.ipynb
    README.md
  KleinWebAppSample/
    css/
      site.css
    js/
      site.js
    markup/
      add_accounts.xml
      client_area.xml
    credentials.json
    main.py
    README.md
    screenshot.png
    templates.py
.editorconfig
.gitignore
AUTHORS.md
CONTRIBUTING.md
LICENSE
mkdocs.yml
poetry.toml
pyproject.toml
README.md
```

# Files

## File: .github/workflows/code_quality_checks.yml
````yaml
---
name: Code Quality Checks

on:
  push:
    branches: [main, dev]
  pull_request:
    branches: [main, dev]

jobs:
  build:

    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v2
      - name: Set up Python 3.8
        uses: actions/setup-python@v1
        with:
          python-version: 3.8
      - name: Install poetry
        run: pip install poetry
      - name: Install dependencies
        run: poetry update
````

## File: .github/workflows/docs_publish.yml
````yaml
---
name: Docs publish

on:
  push:
    branches:
      - main

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: 3.9
      - run: pip install mkdocs-material
      - run: pip install mkdocs-minify-plugin
      - run: mkdocs gh-deploy --force
````

## File: .github/workflows/pypi_publish.yml
````yaml
---
name: PyPI publish

on:
  release:
    types: [released]

jobs:
  build:

    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v2
      - name: Set up Python 3.9
        uses: actions/setup-python@v1
        with:
          python-version: 3.9
      - name: Install poetry
        run: pip install poetry
      - name: Bump version number
        run: poetry version ${{ github.event.release.tag_name }}
      - name: Build package
        run: poetry build
      - name: Publish package
        run: poetry publish -u ${{ secrets.PYPI_USERNAME }} -p ${{ secrets.PYPI_PASSWORD }}
````

## File: .github/workflows/test_pypi_publish.yml
````yaml
---
name: Test PyPI publish

on:
  release:
    types: [prereleased]

jobs:
  build:

    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v2
      - name: Set up Python 3.9
        uses: actions/setup-python@v1
        with:
          python-version: 3.9
      - name: Install poetry
        run: pip install poetry
      - name: Bump version number
        run: poetry version ${{ github.event.release.tag_name }}
      - name: Build package
        run: poetry build
      - name: Publish package
        run: poetry publish -r testpypi -u ${{ secrets.TEST_PYPI_USERNAME }} -p ${{ secrets.TEST_PYPI_PASSWORD }}
````

## File: ctrader_open_api/messages/__init__.py
````python

````

## File: ctrader_open_api/messages/OpenApiCommonMessages_pb2.py
````python
# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: OpenApiCommonMessages.proto
"""Generated protocol buffer code."""
from google.protobuf.internal import builder as _builder
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


from ctrader_open_api.messages import OpenApiCommonModelMessages_pb2 as OpenApiCommonModelMessages__pb2


DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x1bOpenApiCommonMessages.proto\x1a OpenApiCommonModelMessages.proto\"I\n\x0cProtoMessage\x12\x13\n\x0bpayloadType\x18\x01 \x02(\r\x12\x0f\n\x07payload\x18\x02 \x01(\x0c\x12\x13\n\x0b\x63lientMsgId\x18\x03 \x01(\t\"\x8b\x01\n\rProtoErrorRes\x12\x31\n\x0bpayloadType\x18\x01 \x01(\x0e\x32\x11.ProtoPayloadType:\tERROR_RES\x12\x11\n\terrorCode\x18\x02 \x02(\t\x12\x13\n\x0b\x64\x65scription\x18\x03 \x01(\t\x12\x1f\n\x17maintenanceEndTimestamp\x18\x04 \x01(\x04\"N\n\x13ProtoHeartbeatEvent\x12\x37\n\x0bpayloadType\x18\x01 \x01(\x0e\x32\x11.ProtoPayloadType:\x0fHEARTBEAT_EVENTBB\n\"com.xtrader.protocol.proto.commonsB\x17\x43ontainerCommonMessagesP\x01\xa0\x01\x01')

_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, globals())
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'OpenApiCommonMessages_pb2', globals())
if _descriptor._USE_C_DESCRIPTORS == False:

  DESCRIPTOR._options = None
  DESCRIPTOR._serialized_options = b'\n\"com.xtrader.protocol.proto.commonsB\027ContainerCommonMessagesP\001\240\001\001'
  _PROTOMESSAGE._serialized_start=65
  _PROTOMESSAGE._serialized_end=138
  _PROTOERRORRES._serialized_start=141
  _PROTOERRORRES._serialized_end=280
  _PROTOHEARTBEATEVENT._serialized_start=282
  _PROTOHEARTBEATEVENT._serialized_end=360
# @@protoc_insertion_point(module_scope)
````

## File: ctrader_open_api/messages/OpenApiCommonModelMessages_pb2.py
````python
# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: OpenApiCommonModelMessages.proto
"""Generated protocol buffer code."""
from google.protobuf.internal import builder as _builder
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n OpenApiCommonModelMessages.proto*I\n\x10ProtoPayloadType\x12\x11\n\rPROTO_MESSAGE\x10\x05\x12\r\n\tERROR_RES\x10\x32\x12\x13\n\x0fHEARTBEAT_EVENT\x10\x33*\xf0\x01\n\x0eProtoErrorCode\x12\x11\n\rUNKNOWN_ERROR\x10\x01\x12\x17\n\x13UNSUPPORTED_MESSAGE\x10\x02\x12\x13\n\x0fINVALID_REQUEST\x10\x03\x12\x11\n\rTIMEOUT_ERROR\x10\x05\x12\x14\n\x10\x45NTITY_NOT_FOUND\x10\x06\x12\x16\n\x12\x43\x41NT_ROUTE_REQUEST\x10\x07\x12\x12\n\x0e\x46RAME_TOO_LONG\x10\x08\x12\x11\n\rMARKET_CLOSED\x10\t\x12\x1b\n\x17\x43ONCURRENT_MODIFICATION\x10\n\x12\x18\n\x14\x42LOCKED_PAYLOAD_TYPE\x10\x0b\x42M\n(com.xtrader.protocol.proto.commons.modelB\x1c\x43ontainerCommonModelMessagesP\x01\xa0\x01\x01')

_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, globals())
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'OpenApiCommonModelMessages_pb2', globals())
if _descriptor._USE_C_DESCRIPTORS == False:

  DESCRIPTOR._options = None
  DESCRIPTOR._serialized_options = b'\n(com.xtrader.protocol.proto.commons.modelB\034ContainerCommonModelMessagesP\001\240\001\001'
  _PROTOPAYLOADTYPE._serialized_start=36
  _PROTOPAYLOADTYPE._serialized_end=109
  _PROTOERRORCODE._serialized_start=112
  _PROTOERRORCODE._serialized_end=352
# @@protoc_insertion_point(module_scope)
````

## File: ctrader_open_api/messages/OpenApiMessages_pb2.py
````python
# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: OpenApiMessages.proto
"""Generated protocol buffer code."""
from google.protobuf.internal import builder as _builder
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


from ctrader_open_api.messages import OpenApiModelMessages_pb2 as OpenApiModelMessages__pb2

DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x15OpenApiMessages.proto\x1a\x1aOpenApiModelMessages.proto\"\x8c\x01\n\x19ProtoOAApplicationAuthReq\x12G\n\x0bpayloadType\x18\x01 \x01(\x0e\x32\x13.ProtoOAPayloadType:\x1dPROTO_OA_APPLICATION_AUTH_REQ\x12\x10\n\x08\x63lientId\x18\x02 \x02(\t\x12\x14\n\x0c\x63lientSecret\x18\x03 \x02(\t\"d\n\x19ProtoOAApplicationAuthRes\x12G\n\x0bpayloadType\x18\x01 \x01(\x0e\x32\x13.ProtoOAPayloadType:\x1dPROTO_OA_APPLICATION_AUTH_RES\"\x8e\x01\n\x15ProtoOAAccountAuthReq\x12\x43\n\x0bpayloadType\x18\x01 \x01(\x0e\x32\x13.ProtoOAPayloadType:\x19PROTO_OA_ACCOUNT_AUTH_REQ\x12\x1b\n\x13\x63tidTraderAccountId\x18\x02 \x02(\x03\x12\x13\n\x0b\x61\x63\x63\x65ssToken\x18\x03 \x02(\t\"y\n\x15ProtoOAAccountAuthRes\x12\x43\n\x0bpayloadType\x18\x01 \x01(\x0e\x32\x13.ProtoOAPayloadType:\x19PROTO_OA_ACCOUNT_AUTH_RES\x12\x1b\n\x13\x63tidTraderAccountId\x18\x02 \x02(\x03\"\xb5\x01\n\x0fProtoOAErrorRes\x12<\n\x0bpayloadType\x18\x01 \x01(\x0e\x32\x13.ProtoOAPayloadType:\x12PROTO_OA_ERROR_RES\x12\x1b\n\x13\x63tidTraderAccountId\x18\x02 \x01(\x03\x12\x11\n\terrorCode\x18\x03 \x02(\t\x12\x13\n\x0b\x64\x65scription\x18\x04 \x01(\t\x12\x1f\n\x17maintenanceEndTimestamp\x18\x05 \x01(\x03\"z\n\x1cProtoOAClientDisconnectEvent\x12J\n\x0bpayloadType\x18\x01 \x01(\x0e\x32\x13.ProtoOAPayloadType: PROTO_OA_CLIENT_DISCONNECT_EVENT\x12\x0e\n\x06reason\x18\x02 \x01(\t\"\xa9\x01\n$ProtoOAAccountsTokenInvalidatedEvent\x12S\n\x0bpayloadType\x18\x01 \x01(\x0e\x32\x13.ProtoOAPayloadType:)PROTO_OA_ACCOUNTS_TOKEN_INVALIDATED_EVENT\x12\x1c\n\x14\x63tidTraderAccountIds\x18\x02 \x03(\x03\x12\x0e\n\x06reason\x18\x03 \x01(\t\"S\n\x11ProtoOAVersionReq\x12>\n\x0bpayloadType\x18\x01 \x01(\x0e\x32\x13.ProtoOAPayloadType:\x14PROTO_OA_VERSION_REQ\"d\n\x11ProtoOAVersionRes\x12>\n\x0bpayloadType\x18\x01 \x01(\x0e\x32\x13.ProtoOAPayloadType:\x14PROTO_OA_VERSION_RES\x12\x0f\n\x07version\x18\x02 \x02(\t\"\xb1\x05\n\x12ProtoOANewOrderReq\x12@\n\x0bpayloadType\x18\x01 \x01(\x0e\x32\x13.ProtoOAPayloadType:\x16PROTO_OA_NEW_ORDER_REQ\x12\x1b\n\x13\x63tidTraderAccountId\x18\x02 \x02(\x03\x12\x10\n\x08symbolId\x18\x03 \x02(\x03\x12$\n\torderType\x18\x04 \x02(\x0e\x32\x11.ProtoOAOrderType\x12$\n\ttradeSide\x18\x05 \x02(\x0e\x32\x11.ProtoOATradeSide\x12\x0e\n\x06volume\x18\x06 \x02(\x03\x12\x12\n\nlimitPrice\x18\x07 \x01(\x01\x12\x11\n\tstopPrice\x18\x08 \x01(\x01\x12:\n\x0btimeInForce\x18\t \x01(\x0e\x32\x13.ProtoOATimeInForce:\x10GOOD_TILL_CANCEL\x12\x1b\n\x13\x65xpirationTimestamp\x18\n \x01(\x03\x12\x10\n\x08stopLoss\x18\x0b \x01(\x01\x12\x12\n\ntakeProfit\x18\x0c \x01(\x01\x12\x0f\n\x07\x63omment\x18\r \x01(\t\x12\x19\n\x11\x62\x61seSlippagePrice\x18\x0e \x01(\x01\x12\x18\n\x10slippageInPoints\x18\x0f \x01(\x05\x12\r\n\x05label\x18\x10 \x01(\t\x12\x12\n\npositionId\x18\x11 \x01(\x03\x12\x15\n\rclientOrderId\x18\x12 \x01(\t\x12\x18\n\x10relativeStopLoss\x18\x13 \x01(\x03\x12\x1a\n\x12relativeTakeProfit\x18\x14 \x01(\x03\x12\x1a\n\x12guaranteedStopLoss\x18\x15 \x01(\x08\x12\x18\n\x10trailingStopLoss\x18\x16 \x01(\x08\x12<\n\x11stopTriggerMethod\x18\x17 \x01(\x0e\x32\x1a.ProtoOAOrderTriggerMethod:\x05TRADE\"\x9c\x03\n\x15ProtoOAExecutionEvent\x12\x42\n\x0bpayloadType\x18\x01 \x01(\x0e\x32\x13.ProtoOAPayloadType:\x18PROTO_OA_EXECUTION_EVENT\x12\x1b\n\x13\x63tidTraderAccountId\x18\x02 \x02(\x03\x12,\n\rexecutionType\x18\x03 \x02(\x0e\x32\x15.ProtoOAExecutionType\x12\"\n\x08position\x18\x04 \x01(\x0b\x32\x10.ProtoOAPosition\x12\x1c\n\x05order\x18\x05 \x01(\x0b\x32\r.ProtoOAOrder\x12\x1a\n\x04\x64\x65\x61l\x18\x06 \x01(\x0b\x32\x0c.ProtoOADeal\x12:\n\x14\x62onusDepositWithdraw\x18\x07 \x01(\x0b\x32\x1c.ProtoOABonusDepositWithdraw\x12\x30\n\x0f\x64\x65positWithdraw\x18\x08 \x01(\x0b\x32\x17.ProtoOADepositWithdraw\x12\x11\n\terrorCode\x18\t \x01(\t\x12\x15\n\risServerEvent\x18\n \x01(\x08\"\x8a\x01\n\x15ProtoOACancelOrderReq\x12\x43\n\x0bpayloadType\x18\x01 \x01(\x0e\x32\x13.ProtoOAPayloadType:\x19PROTO_OA_CANCEL_ORDER_REQ\x12\x1b\n\x13\x63tidTraderAccountId\x18\x02 \x02(\x03\x12\x0f\n\x07orderId\x18\x03 \x02(\x03\"\xc6\x03\n\x14ProtoOAAmendOrderReq\x12\x42\n\x0bpayloadType\x18\x01 \x01(\x0e\x32\x13.ProtoOAPayloadType:\x18PROTO_OA_AMEND_ORDER_REQ\x12\x1b\n\x13\x63tidTraderAccountId\x18\x02 \x02(\x03\x12\x0f\n\x07orderId\x18\x03 \x02(\x03\x12\x0e\n\x06volume\x18\x04 \x01(\x03\x12\x12\n\nlimitPrice\x18\x05 \x01(\x01\x12\x11\n\tstopPrice\x18\x06 \x01(\x01\x12\x1b\n\x13\x65xpirationTimestamp\x18\x07 \x01(\x03\x12\x10\n\x08stopLoss\x18\x08 \x01(\x01\x12\x12\n\ntakeProfit\x18\t \x01(\x01\x12\x18\n\x10slippageInPoints\x18\n \x01(\x05\x12\x18\n\x10relativeStopLoss\x18\x0b \x01(\x03\x12\x1a\n\x12relativeTakeProfit\x18\x0c \x01(\x03\x12\x1a\n\x12guaranteedStopLoss\x18\r \x01(\x08\x12\x18\n\x10trailingStopLoss\x18\x0e \x01(\x08\x12<\n\x11stopTriggerMethod\x18\x0f \x01(\x0e\x32\x1a.ProtoOAOrderTriggerMethod:\x05TRADE\"\xb8\x02\n\x1bProtoOAAmendPositionSLTPReq\x12J\n\x0bpayloadType\x18\x01 \x01(\x0e\x32\x13.ProtoOAPayloadType: PROTO_OA_AMEND_POSITION_SLTP_REQ\x12\x1b\n\x13\x63tidTraderAccountId\x18\x02 \x02(\x03\x12\x12\n\npositionId\x18\x03 \x02(\x03\x12\x10\n\x08stopLoss\x18\x04 \x01(\x01\x12\x12\n\ntakeProfit\x18\x05 \x01(\x01\x12\x1a\n\x12guaranteedStopLoss\x18\x07 \x01(\x08\x12\x18\n\x10trailingStopLoss\x18\x08 \x01(\x08\x12@\n\x15stopLossTriggerMethod\x18\t \x01(\x0e\x32\x1a.ProtoOAOrderTriggerMethod:\x05TRADE\"\xa1\x01\n\x17ProtoOAClosePositionReq\x12\x45\n\x0bpayloadType\x18\x01 \x01(\x0e\x32\x13.ProtoOAPayloadType:\x1bPROTO_OA_CLOSE_POSITION_REQ\x12\x1b\n\x13\x63tidTraderAccountId\x18\x02 \x02(\x03\x12\x12\n\npositionId\x18\x03 \x02(\x03\x12\x0e\n\x06volume\x18\x04 \x02(\x03\"\xe2\x01\n\x1dProtoOATrailingSLChangedEvent\x12L\n\x0bpayloadType\x18\x01 \x01(\x0e\x32\x13.ProtoOAPayloadType:\"PROTO_OA_TRAILING_SL_CHANGED_EVENT\x12\x1b\n\x13\x63tidTraderAccountId\x18\x02 \x02(\x03\x12\x12\n\npositionId\x18\x03 \x02(\x03\x12\x0f\n\x07orderId\x18\x04 \x02(\x03\x12\x11\n\tstopPrice\x18\x05 \x02(\x01\x12\x1e\n\x16utcLastUpdateTimestamp\x18\x06 \x02(\x03\"u\n\x13ProtoOAAssetListReq\x12\x41\n\x0bpayloadType\x18\x01 \x01(\x0e\x32\x13.ProtoOAPayloadType:\x17PROTO_OA_ASSET_LIST_REQ\x12\x1b\n\x13\x63tidTraderAccountId\x18\x02 \x02(\x03\"\x93\x01\n\x13ProtoOAAssetListRes\x12\x41\n\x0bpayloadType\x18\x01 \x01(\x0e\x32\x13.ProtoOAPayloadType:\x17PROTO_OA_ASSET_LIST_RES\x12\x1b\n\x13\x63tidTraderAccountId\x18\x02 \x02(\x03\x12\x1c\n\x05\x61sset\x18\x03 \x03(\x0b\x32\r.ProtoOAAsset\"\xa0\x01\n\x15ProtoOASymbolsListReq\x12\x43\n\x0bpayloadType\x18\x01 \x01(\x0e\x32\x13.ProtoOAPayloadType:\x19PROTO_OA_SYMBOLS_LIST_REQ\x12\x1b\n\x13\x63tidTraderAccountId\x18\x02 \x02(\x03\x12%\n\x16includeArchivedSymbols\x18\x03 \x01(\x08:\x05\x66\x61lse\"\xce\x01\n\x15ProtoOASymbolsListRes\x12\x43\n\x0bpayloadType\x18\x01 \x01(\x0e\x32\x13.ProtoOAPayloadType:\x19PROTO_OA_SYMBOLS_LIST_RES\x12\x1b\n\x13\x63tidTraderAccountId\x18\x02 \x02(\x03\x12#\n\x06symbol\x18\x03 \x03(\x0b\x32\x13.ProtoOALightSymbol\x12.\n\x0e\x61rchivedSymbol\x18\x04 \x03(\x0b\x32\x16.ProtoOAArchivedSymbol\"\x8a\x01\n\x14ProtoOASymbolByIdReq\x12\x43\n\x0bpayloadType\x18\x01 \x01(\x0e\x32\x13.ProtoOAPayloadType:\x19PROTO_OA_SYMBOL_BY_ID_REQ\x12\x1b\n\x13\x63tidTraderAccountId\x18\x02 \x02(\x03\x12\x10\n\x08symbolId\x18\x03 \x03(\x03\"\xc8\x01\n\x14ProtoOASymbolByIdRes\x12\x43\n\x0bpayloadType\x18\x01 \x01(\x0e\x32\x13.ProtoOAPayloadType:\x19PROTO_OA_SYMBOL_BY_ID_RES\x12\x1b\n\x13\x63tidTraderAccountId\x18\x02 \x02(\x03\x12\x1e\n\x06symbol\x18\x03 \x03(\x0b\x32\x0e.ProtoOASymbol\x12.\n\x0e\x61rchivedSymbol\x18\x04 \x03(\x0b\x32\x16.ProtoOAArchivedSymbol\"\xb7\x01\n\x1eProtoOASymbolsForConversionReq\x12M\n\x0bpayloadType\x18\x01 \x01(\x0e\x32\x13.ProtoOAPayloadType:#PROTO_OA_SYMBOLS_FOR_CONVERSION_REQ\x12\x1b\n\x13\x63tidTraderAccountId\x18\x02 \x02(\x03\x12\x14\n\x0c\x66irstAssetId\x18\x03 \x02(\x03\x12\x13\n\x0blastAssetId\x18\x04 \x02(\x03\"\xb1\x01\n\x1eProtoOASymbolsForConversionRes\x12M\n\x0bpayloadType\x18\x01 \x01(\x0e\x32\x13.ProtoOAPayloadType:#PROTO_OA_SYMBOLS_FOR_CONVERSION_RES\x12\x1b\n\x13\x63tidTraderAccountId\x18\x02 \x02(\x03\x12#\n\x06symbol\x18\x03 \x03(\x0b\x32\x13.ProtoOALightSymbol\"\x93\x01\n\x19ProtoOASymbolChangedEvent\x12G\n\x0bpayloadType\x18\x01 \x01(\x0e\x32\x13.ProtoOAPayloadType:\x1dPROTO_OA_SYMBOL_CHANGED_EVENT\x12\x1b\n\x13\x63tidTraderAccountId\x18\x02 \x02(\x03\x12\x10\n\x08symbolId\x18\x03 \x03(\x03\"\x80\x01\n\x18ProtoOAAssetClassListReq\x12G\n\x0bpayloadType\x18\x01 \x01(\x0e\x32\x13.ProtoOAPayloadType:\x1dPROTO_OA_ASSET_CLASS_LIST_REQ\x12\x1b\n\x13\x63tidTraderAccountId\x18\x02 \x02(\x03\"\xa8\x01\n\x18ProtoOAAssetClassListRes\x12G\n\x0bpayloadType\x18\x01 \x01(\x0e\x32\x13.ProtoOAPayloadType:\x1dPROTO_OA_ASSET_CLASS_LIST_RES\x12\x1b\n\x13\x63tidTraderAccountId\x18\x02 \x02(\x03\x12&\n\nassetClass\x18\x03 \x03(\x0b\x32\x12.ProtoOAAssetClass\"n\n\x10ProtoOATraderReq\x12=\n\x0bpayloadType\x18\x01 \x01(\x0e\x32\x13.ProtoOAPayloadType:\x13PROTO_OA_TRADER_REQ\x12\x1b\n\x13\x63tidTraderAccountId\x18\x02 \x02(\x03\"\x8e\x01\n\x10ProtoOATraderRes\x12=\n\x0bpayloadType\x18\x01 \x01(\x0e\x32\x13.ProtoOAPayloadType:\x13PROTO_OA_TRADER_RES\x12\x1b\n\x13\x63tidTraderAccountId\x18\x02 \x02(\x03\x12\x1e\n\x06trader\x18\x03 \x02(\x0b\x32\x0e.ProtoOATrader\"\xa0\x01\n\x19ProtoOATraderUpdatedEvent\x12\x46\n\x0bpayloadType\x18\x01 \x01(\x0e\x32\x13.ProtoOAPayloadType:\x1cPROTO_OA_TRADER_UPDATE_EVENT\x12\x1b\n\x13\x63tidTraderAccountId\x18\x02 \x02(\x03\x12\x1e\n\x06trader\x18\x03 \x02(\x0b\x32\x0e.ProtoOATrader\"t\n\x13ProtoOAReconcileReq\x12@\n\x0bpayloadType\x18\x01 \x01(\x0e\x32\x13.ProtoOAPayloadType:\x16PROTO_OA_RECONCILE_REQ\x12\x1b\n\x13\x63tidTraderAccountId\x18\x02 \x02(\x03\"\xb6\x01\n\x13ProtoOAReconcileRes\x12@\n\x0bpayloadType\x18\x01 \x01(\x0e\x32\x13.ProtoOAPayloadType:\x16PROTO_OA_RECONCILE_RES\x12\x1b\n\x13\x63tidTraderAccountId\x18\x02 \x02(\x03\x12\"\n\x08position\x18\x03 \x03(\x0b\x32\x10.ProtoOAPosition\x12\x1c\n\x05order\x18\x04 \x03(\x0b\x32\r.ProtoOAOrder\"\xc8\x01\n\x16ProtoOAOrderErrorEvent\x12\x44\n\x0bpayloadType\x18\x01 \x01(\x0e\x32\x13.ProtoOAPayloadType:\x1aPROTO_OA_ORDER_ERROR_EVENT\x12\x1b\n\x13\x63tidTraderAccountId\x18\x05 \x02(\x03\x12\x11\n\terrorCode\x18\x02 \x02(\t\x12\x0f\n\x07orderId\x18\x03 \x01(\x03\x12\x12\n\npositionId\x18\x06 \x01(\x03\x12\x13\n\x0b\x64\x65scription\x18\x07 \x01(\t\"\xb0\x01\n\x12ProtoOADealListReq\x12@\n\x0bpayloadType\x18\x01 \x01(\x0e\x32\x13.ProtoOAPayloadType:\x16PROTO_OA_DEAL_LIST_REQ\x12\x1b\n\x13\x63tidTraderAccountId\x18\x02 \x02(\x03\x12\x15\n\rfromTimestamp\x18\x03 \x02(\x03\x12\x13\n\x0btoTimestamp\x18\x04 \x02(\x03\x12\x0f\n\x07maxRows\x18\x05 \x01(\x05\"\xa0\x01\n\x12ProtoOADealListRes\x12@\n\x0bpayloadType\x18\x01 \x01(\x0e\x32\x13.ProtoOAPayloadType:\x16PROTO_OA_DEAL_LIST_RES\x12\x1b\n\x13\x63tidTraderAccountId\x18\x02 \x02(\x03\x12\x1a\n\x04\x64\x65\x61l\x18\x03 \x03(\x0b\x32\x0c.ProtoOADeal\x12\x0f\n\x07hasMore\x18\x04 \x02(\x08\"\xa1\x01\n\x13ProtoOAOrderListReq\x12\x41\n\x0bpayloadType\x18\x01 \x01(\x0e\x32\x13.ProtoOAPayloadType:\x17PROTO_OA_ORDER_LIST_REQ\x12\x1b\n\x13\x63tidTraderAccountId\x18\x02 \x02(\x03\x12\x15\n\rfromTimestamp\x18\x03 \x02(\x03\x12\x13\n\x0btoTimestamp\x18\x04 \x02(\x03\"\xa4\x01\n\x13ProtoOAOrderListRes\x12\x41\n\x0bpayloadType\x18\x01 \x01(\x0e\x32\x13.ProtoOAPayloadType:\x17PROTO_OA_ORDER_LIST_RES\x12\x1b\n\x13\x63tidTraderAccountId\x18\x02 \x02(\x03\x12\x1c\n\x05order\x18\x03 \x03(\x0b\x32\r.ProtoOAOrder\x12\x0f\n\x07hasMore\x18\x04 \x02(\x08\"\xa1\x01\n\x18ProtoOAExpectedMarginReq\x12\x46\n\x0bpayloadType\x18\x01 \x01(\x0e\x32\x13.ProtoOAPayloadType:\x1cPROTO_OA_EXPECTED_MARGIN_REQ\x12\x1b\n\x13\x63tidTraderAccountId\x18\x02 \x02(\x03\x12\x10\n\x08symbolId\x18\x03 \x02(\x03\x12\x0e\n\x06volume\x18\x04 \x03(\x03\"\xbc\x01\n\x18ProtoOAExpectedMarginRes\x12\x46\n\x0bpayloadType\x18\x01 \x01(\x0e\x32\x13.ProtoOAPayloadType:\x1cPROTO_OA_EXPECTED_MARGIN_RES\x12\x1b\n\x13\x63tidTraderAccountId\x18\x02 \x02(\x03\x12&\n\x06margin\x18\x03 \x03(\x0b\x32\x16.ProtoOAExpectedMargin\x12\x13\n\x0bmoneyDigits\x18\x04 \x01(\r\"\xbe\x01\n\x19ProtoOAMarginChangedEvent\x12G\n\x0bpayloadType\x18\x01 \x01(\x0e\x32\x13.ProtoOAPayloadType:\x1dPROTO_OA_MARGIN_CHANGED_EVENT\x12\x1b\n\x13\x63tidTraderAccountId\x18\x02 \x02(\x03\x12\x12\n\npositionId\x18\x03 \x02(\x04\x12\x12\n\nusedMargin\x18\x04 \x02(\x04\x12\x13\n\x0bmoneyDigits\x18\x05 \x01(\r\"\xb7\x01\n\x1dProtoOACashFlowHistoryListReq\x12M\n\x0bpayloadType\x18\x01 \x01(\x0e\x32\x13.ProtoOAPayloadType:#PROTO_OA_CASH_FLOW_HISTORY_LIST_REQ\x12\x1b\n\x13\x63tidTraderAccountId\x18\x02 \x02(\x03\x12\x15\n\rfromTimestamp\x18\x03 \x02(\x03\x12\x13\n\x0btoTimestamp\x18\x04 \x02(\x03\"\xbd\x01\n\x1dProtoOACashFlowHistoryListRes\x12M\n\x0bpayloadType\x18\x01 \x01(\x0e\x32\x13.ProtoOAPayloadType:#PROTO_OA_CASH_FLOW_HISTORY_LIST_RES\x12\x1b\n\x13\x63tidTraderAccountId\x18\x02 \x02(\x03\x12\x30\n\x0f\x64\x65positWithdraw\x18\x03 \x03(\x0b\x32\x17.ProtoOADepositWithdraw\"\x91\x01\n%ProtoOAGetAccountListByAccessTokenReq\x12S\n\x0bpayloadType\x18\x01 \x01(\x0e\x32\x13.ProtoOAPayloadType:)PROTO_OA_GET_ACCOUNTS_BY_ACCESS_TOKEN_REQ\x12\x13\n\x0b\x61\x63\x63\x65ssToken\x18\x02 \x02(\t\"\xff\x01\n%ProtoOAGetAccountListByAccessTokenRes\x12S\n\x0bpayloadType\x18\x01 \x01(\x0e\x32\x13.ProtoOAPayloadType:)PROTO_OA_GET_ACCOUNTS_BY_ACCESS_TOKEN_RES\x12\x13\n\x0b\x61\x63\x63\x65ssToken\x18\x02 \x02(\t\x12\x36\n\x0fpermissionScope\x18\x03 \x01(\x0e\x32\x1d.ProtoOAClientPermissionScope\x12\x34\n\x11\x63tidTraderAccount\x18\x04 \x03(\x0b\x32\x19.ProtoOACtidTraderAccount\"t\n\x16ProtoOARefreshTokenReq\x12\x44\n\x0bpayloadType\x18\x01 \x01(\x0e\x32\x13.ProtoOAPayloadType:\x1aPROTO_OA_REFRESH_TOKEN_REQ\x12\x14\n\x0crefreshToken\x18\x02 \x02(\t\"\xaf\x01\n\x16ProtoOARefreshTokenRes\x12\x44\n\x0bpayloadType\x18\x01 \x01(\x0e\x32\x13.ProtoOAPayloadType:\x1aPROTO_OA_REFRESH_TOKEN_RES\x12\x13\n\x0b\x61\x63\x63\x65ssToken\x18\x02 \x02(\t\x12\x11\n\ttokenType\x18\x03 \x02(\t\x12\x11\n\texpiresIn\x18\x04 \x02(\x03\x12\x14\n\x0crefreshToken\x18\x05 \x02(\t\"\xb3\x01\n\x18ProtoOASubscribeSpotsReq\x12\x46\n\x0bpayloadType\x18\x01 \x01(\x0e\x32\x13.ProtoOAPayloadType:\x1cPROTO_OA_SUBSCRIBE_SPOTS_REQ\x12\x1b\n\x13\x63tidTraderAccountId\x18\x02 \x02(\x03\x12\x10\n\x08symbolId\x18\x03 \x03(\x03\x12 \n\x18subscribeToSpotTimestamp\x18\x04 \x01(\x08\"\x7f\n\x18ProtoOASubscribeSpotsRes\x12\x46\n\x0bpayloadType\x18\x01 \x01(\x0e\x32\x13.ProtoOAPayloadType:\x1cPROTO_OA_SUBSCRIBE_SPOTS_RES\x12\x1b\n\x13\x63tidTraderAccountId\x18\x02 \x02(\x03\"\x95\x01\n\x1aProtoOAUnsubscribeSpotsReq\x12H\n\x0bpayloadType\x18\x01 \x01(\x0e\x32\x13.ProtoOAPayloadType:\x1ePROTO_OA_UNSUBSCRIBE_SPOTS_REQ\x12\x1b\n\x13\x63tidTraderAccountId\x18\x02 \x02(\x03\x12\x10\n\x08symbolId\x18\x03 \x03(\x03\"\x83\x01\n\x1aProtoOAUnsubscribeSpotsRes\x12H\n\x0bpayloadType\x18\x01 \x01(\x0e\x32\x13.ProtoOAPayloadType:\x1ePROTO_OA_UNSUBSCRIBE_SPOTS_RES\x12\x1b\n\x13\x63tidTraderAccountId\x18\x02 \x02(\x03\"\xe7\x01\n\x10ProtoOASpotEvent\x12=\n\x0bpayloadType\x18\x01 \x01(\x0e\x32\x13.ProtoOAPayloadType:\x13PROTO_OA_SPOT_EVENT\x12\x1b\n\x13\x63tidTraderAccountId\x18\x02 \x02(\x03\x12\x10\n\x08symbolId\x18\x03 \x02(\x03\x12\x0b\n\x03\x62id\x18\x04 \x01(\x04\x12\x0b\n\x03\x61sk\x18\x05 \x01(\x04\x12\"\n\x08trendbar\x18\x06 \x03(\x0b\x32\x10.ProtoOATrendbar\x12\x14\n\x0csessionClose\x18\x07 \x01(\x04\x12\x11\n\ttimestamp\x18\x08 \x01(\x03\"\xc8\x01\n\x1fProtoOASubscribeLiveTrendbarReq\x12N\n\x0bpayloadType\x18\x01 \x01(\x0e\x32\x13.ProtoOAPayloadType:$PROTO_OA_SUBSCRIBE_LIVE_TRENDBAR_REQ\x12\x1b\n\x13\x63tidTraderAccountId\x18\x02 \x02(\x03\x12&\n\x06period\x18\x03 \x02(\x0e\x32\x16.ProtoOATrendbarPeriod\x12\x10\n\x08symbolId\x18\x04 \x02(\x03\"\x8e\x01\n\x1fProtoOASubscribeLiveTrendbarRes\x12N\n\x0bpayloadType\x18\x01 \x01(\x0e\x32\x13.ProtoOAPayloadType:$PROTO_OA_SUBSCRIBE_LIVE_TRENDBAR_RES\x12\x1b\n\x13\x63tidTraderAccountId\x18\x02 \x02(\x03\"\xcc\x01\n!ProtoOAUnsubscribeLiveTrendbarReq\x12P\n\x0bpayloadType\x18\x01 \x01(\x0e\x32\x13.ProtoOAPayloadType:&PROTO_OA_UNSUBSCRIBE_LIVE_TRENDBAR_REQ\x12\x1b\n\x13\x63tidTraderAccountId\x18\x02 \x02(\x03\x12&\n\x06period\x18\x03 \x02(\x0e\x32\x16.ProtoOATrendbarPeriod\x12\x10\n\x08symbolId\x18\x04 \x02(\x03\"\x92\x01\n!ProtoOAUnsubscribeLiveTrendbarRes\x12P\n\x0bpayloadType\x18\x01 \x01(\x0e\x32\x13.ProtoOAPayloadType:&PROTO_OA_UNSUBSCRIBE_LIVE_TRENDBAR_RES\x12\x1b\n\x13\x63tidTraderAccountId\x18\x02 \x02(\x03\"\xf0\x01\n\x16ProtoOAGetTrendbarsReq\x12\x44\n\x0bpayloadType\x18\x01 \x01(\x0e\x32\x13.ProtoOAPayloadType:\x1aPROTO_OA_GET_TRENDBARS_REQ\x12\x1b\n\x13\x63tidTraderAccountId\x18\x02 \x02(\x03\x12\x15\n\rfromTimestamp\x18\x03 \x02(\x03\x12\x13\n\x0btoTimestamp\x18\x04 \x02(\x03\x12&\n\x06period\x18\x05 \x02(\x0e\x32\x16.ProtoOATrendbarPeriod\x12\x10\n\x08symbolId\x18\x06 \x02(\x03\x12\r\n\x05\x63ount\x18\x07 \x01(\r\"\xec\x01\n\x16ProtoOAGetTrendbarsRes\x12\x44\n\x0bpayloadType\x18\x01 \x01(\x0e\x32\x13.ProtoOAPayloadType:\x1aPROTO_OA_GET_TRENDBARS_RES\x12\x1b\n\x13\x63tidTraderAccountId\x18\x02 \x02(\x03\x12&\n\x06period\x18\x03 \x02(\x0e\x32\x16.ProtoOATrendbarPeriod\x12\x11\n\ttimestamp\x18\x04 \x02(\x03\x12\"\n\x08trendbar\x18\x05 \x03(\x0b\x32\x10.ProtoOATrendbar\x12\x10\n\x08symbolId\x18\x06 \x01(\x03\"\xd8\x01\n\x15ProtoOAGetTickDataReq\x12\x43\n\x0bpayloadType\x18\x01 \x01(\x0e\x32\x13.ProtoOAPayloadType:\x19PROTO_OA_GET_TICKDATA_REQ\x12\x1b\n\x13\x63tidTraderAccountId\x18\x02 \x02(\x03\x12\x10\n\x08symbolId\x18\x03 \x02(\x03\x12\x1f\n\x04type\x18\x04 \x02(\x0e\x32\x11.ProtoOAQuoteType\x12\x15\n\rfromTimestamp\x18\x05 \x02(\x03\x12\x13\n\x0btoTimestamp\x18\x06 \x02(\x03\"\xae\x01\n\x15ProtoOAGetTickDataRes\x12\x43\n\x0bpayloadType\x18\x01 \x01(\x0e\x32\x13.ProtoOAPayloadType:\x19PROTO_OA_GET_TICKDATA_RES\x12\x1b\n\x13\x63tidTraderAccountId\x18\x02 \x02(\x03\x12\"\n\x08tickData\x18\x03 \x03(\x0b\x32\x10.ProtoOATickData\x12\x0f\n\x07hasMore\x18\x04 \x02(\x08\"\x88\x01\n\x1fProtoOAGetCtidProfileByTokenReq\x12P\n\x0bpayloadType\x18\x01 \x01(\x0e\x32\x13.ProtoOAPayloadType:&PROTO_OA_GET_CTID_PROFILE_BY_TOKEN_REQ\x12\x13\n\x0b\x61\x63\x63\x65ssToken\x18\x02 \x02(\t\"\x99\x01\n\x1fProtoOAGetCtidProfileByTokenRes\x12P\n\x0bpayloadType\x18\x01 \x01(\x0e\x32\x13.ProtoOAPayloadType:&PROTO_OA_GET_CTID_PROFILE_BY_TOKEN_RES\x12$\n\x07profile\x18\x02 \x02(\x0b\x32\x13.ProtoOACtidProfile\"\xc4\x01\n\x11ProtoOADepthEvent\x12>\n\x0bpayloadType\x18\x01 \x01(\x0e\x32\x13.ProtoOAPayloadType:\x14PROTO_OA_DEPTH_EVENT\x12\x1b\n\x13\x63tidTraderAccountId\x18\x02 \x02(\x03\x12\x10\n\x08symbolId\x18\x03 \x02(\x04\x12%\n\tnewQuotes\x18\x04 \x03(\x0b\x32\x12.ProtoOADepthQuote\x12\x19\n\rdeletedQuotes\x18\x05 \x03(\x04\x42\x02\x10\x01\"\x9e\x01\n\x1eProtoOASubscribeDepthQuotesReq\x12M\n\x0bpayloadType\x18\x01 \x01(\x0e\x32\x13.ProtoOAPayloadType:#PROTO_OA_SUBSCRIBE_DEPTH_QUOTES_REQ\x12\x1b\n\x13\x63tidTraderAccountId\x18\x02 \x02(\x03\x12\x10\n\x08symbolId\x18\x03 \x03(\x03\"\x8c\x01\n\x1eProtoOASubscribeDepthQuotesRes\x12M\n\x0bpayloadType\x18\x01 \x01(\x0e\x32\x13.ProtoOAPayloadType:#PROTO_OA_SUBSCRIBE_DEPTH_QUOTES_RES\x12\x1b\n\x13\x63tidTraderAccountId\x18\x02 \x02(\x03\"\xa2\x01\n ProtoOAUnsubscribeDepthQuotesReq\x12O\n\x0bpayloadType\x18\x01 \x01(\x0e\x32\x13.ProtoOAPayloadType:%PROTO_OA_UNSUBSCRIBE_DEPTH_QUOTES_REQ\x12\x1b\n\x13\x63tidTraderAccountId\x18\x02 \x02(\x03\x12\x10\n\x08symbolId\x18\x03 \x03(\x03\"\x90\x01\n ProtoOAUnsubscribeDepthQuotesRes\x12O\n\x0bpayloadType\x18\x01 \x01(\x0e\x32\x13.ProtoOAPayloadType:%PROTO_OA_UNSUBSCRIBE_DEPTH_QUOTES_RES\x12\x1b\n\x13\x63tidTraderAccountId\x18\x02 \x02(\x03\"\x83\x01\n\x1cProtoOASymbolCategoryListReq\x12\x46\n\x0bpayloadType\x18\x01 \x01(\x0e\x32\x13.ProtoOAPayloadType:\x1cPROTO_OA_SYMBOL_CATEGORY_REQ\x12\x1b\n\x13\x63tidTraderAccountId\x18\x02 \x02(\x03\"\xb3\x01\n\x1cProtoOASymbolCategoryListRes\x12\x46\n\x0bpayloadType\x18\x01 \x01(\x0e\x32\x13.ProtoOAPayloadType:\x1cPROTO_OA_SYMBOL_CATEGORY_RES\x12\x1b\n\x13\x63tidTraderAccountId\x18\x02 \x02(\x03\x12.\n\x0esymbolCategory\x18\x03 \x03(\x0b\x32\x16.ProtoOASymbolCategory\"}\n\x17ProtoOAAccountLogoutReq\x12\x45\n\x0bpayloadType\x18\x01 \x01(\x0e\x32\x13.ProtoOAPayloadType:\x1bPROTO_OA_ACCOUNT_LOGOUT_REQ\x12\x1b\n\x13\x63tidTraderAccountId\x18\x02 \x02(\x03\"}\n\x17ProtoOAAccountLogoutRes\x12\x45\n\x0bpayloadType\x18\x01 \x01(\x0e\x32\x13.ProtoOAPayloadType:\x1bPROTO_OA_ACCOUNT_LOGOUT_RES\x12\x1b\n\x13\x63tidTraderAccountId\x18\x02 \x02(\x03\"\x89\x01\n\x1dProtoOAAccountDisconnectEvent\x12K\n\x0bpayloadType\x18\x01 \x01(\x0e\x32\x13.ProtoOAPayloadType:!PROTO_OA_ACCOUNT_DISCONNECT_EVENT\x12\x1b\n\x13\x63tidTraderAccountId\x18\x02 \x02(\x03\"\x80\x01\n\x18ProtoOAMarginCallListReq\x12G\n\x0bpayloadType\x18\x01 \x01(\x0e\x32\x13.ProtoOAPayloadType:\x1dPROTO_OA_MARGIN_CALL_LIST_REQ\x12\x1b\n\x13\x63tidTraderAccountId\x18\x02 \x02(\x03\"\x8b\x01\n\x18ProtoOAMarginCallListRes\x12G\n\x0bpayloadType\x18\x01 \x01(\x0e\x32\x13.ProtoOAPayloadType:\x1dPROTO_OA_MARGIN_CALL_LIST_RES\x12&\n\nmarginCall\x18\x02 \x03(\x0b\x32\x12.ProtoOAMarginCall\"\xac\x01\n\x1aProtoOAMarginCallUpdateReq\x12I\n\x0bpayloadType\x18\x01 \x01(\x0e\x32\x13.ProtoOAPayloadType:\x1fPROTO_OA_MARGIN_CALL_UPDATE_REQ\x12\x1b\n\x13\x63tidTraderAccountId\x18\x02 \x02(\x03\x12&\n\nmarginCall\x18\x03 \x02(\x0b\x32\x12.ProtoOAMarginCall\"g\n\x1aProtoOAMarginCallUpdateRes\x12I\n\x0bpayloadType\x18\x01 \x01(\x0e\x32\x13.ProtoOAPayloadType:\x1fPROTO_OA_MARGIN_CALL_UPDATE_RES\"\xb0\x01\n\x1cProtoOAMarginCallUpdateEvent\x12K\n\x0bpayloadType\x18\x01 \x01(\x0e\x32\x13.ProtoOAPayloadType:!PROTO_OA_MARGIN_CALL_UPDATE_EVENT\x12\x1b\n\x13\x63tidTraderAccountId\x18\x02 \x02(\x03\x12&\n\nmarginCall\x18\x03 \x02(\x0b\x32\x12.ProtoOAMarginCall\"\xb2\x01\n\x1dProtoOAMarginCallTriggerEvent\x12L\n\x0bpayloadType\x18\x01 \x01(\x0e\x32\x13.ProtoOAPayloadType:\"PROTO_OA_MARGIN_CALL_TRIGGER_EVENT\x12\x1b\n\x13\x63tidTraderAccountId\x18\x02 \x02(\x03\x12&\n\nmarginCall\x18\x03 \x02(\x0b\x32\x12.ProtoOAMarginCall\"\xa0\x01\n ProtoOAGetDynamicLeverageByIDReq\x12K\n\x0bpayloadType\x18\x01 \x01(\x0e\x32\x13.ProtoOAPayloadType:!PROTO_OA_GET_DYNAMIC_LEVERAGE_REQ\x12\x1b\n\x13\x63tidTraderAccountId\x18\x02 \x02(\x03\x12\x12\n\nleverageId\x18\x03 \x02(\x03\"\xb7\x01\n ProtoOAGetDynamicLeverageByIDRes\x12K\n\x0bpayloadType\x18\x01 \x01(\x0e\x32\x13.ProtoOAPayloadType:!PROTO_OA_GET_DYNAMIC_LEVERAGE_RES\x12\x1b\n\x13\x63tidTraderAccountId\x18\x02 \x02(\x03\x12)\n\x08leverage\x18\x03 \x02(\x0b\x32\x17.ProtoOADynamicLeverage\"\xce\x01\n\x1eProtoOADealListByPositionIdReq\x12O\n\x0bpayloadType\x18\x01 \x01(\x0e\x32\x13.ProtoOAPayloadType:%PROTO_OA_DEAL_LIST_BY_POSITION_ID_REQ\x12\x1b\n\x13\x63tidTraderAccountId\x18\x02 \x02(\x03\x12\x12\n\npositionId\x18\x03 \x02(\x03\x12\x15\n\rfromTimestamp\x18\x04 \x02(\x03\x12\x13\n\x0btoTimestamp\x18\x05 \x02(\x03\"\xbb\x01\n\x1eProtoOADealListByPositionIdRes\x12O\n\x0bpayloadType\x18\x01 \x01(\x0e\x32\x13.ProtoOAPayloadType:%PROTO_OA_DEAL_LIST_BY_POSITION_ID_RES\x12\x1b\n\x13\x63tidTraderAccountId\x18\x02 \x02(\x03\x12\x1a\n\x04\x64\x65\x61l\x18\x03 \x03(\x0b\x32\x0c.ProtoOADeal\x12\x0f\n\x07hasMore\x18\x04 \x01(\x03\"\x90\x01\n\x18ProtoOADealOffsetListReq\x12G\n\x0bpayloadType\x18\x01 \x01(\x0e\x32\x13.ProtoOAPayloadType:\x1dPROTO_OA_DEAL_OFFSET_LIST_REQ\x12\x1b\n\x13\x63tidTraderAccountId\x18\x02 \x02(\x03\x12\x0e\n\x06\x64\x65\x61lId\x18\x03 \x02(\x03\"\xce\x01\n\x18ProtoOADealOffsetListRes\x12G\n\x0bpayloadType\x18\x01 \x01(\x0e\x32\x13.ProtoOAPayloadType:\x1dPROTO_OA_DEAL_OFFSET_LIST_RES\x12\x1b\n\x13\x63tidTraderAccountId\x18\x02 \x02(\x03\x12$\n\x08offsetBy\x18\x03 \x03(\x0b\x32\x12.ProtoOADealOffset\x12&\n\noffsetting\x18\x04 \x03(\x0b\x32\x12.ProtoOADealOffset\"\x95\x01\n\"ProtoOAGetPositionUnrealizedPnLReq\x12R\n\x0bpayloadType\x18\x01 \x01(\x0e\x32\x13.ProtoOAPayloadType:(PROTO_OA_GET_POSITION_UNREALIZED_PNL_REQ\x12\x1b\n\x13\x63tidTraderAccountId\x18\x02 \x02(\x03\"\xe8\x01\n\"ProtoOAGetPositionUnrealizedPnLRes\x12R\n\x0bpayloadType\x18\x01 \x01(\x0e\x32\x13.ProtoOAPayloadType:(PROTO_OA_GET_POSITION_UNREALIZED_PNL_RES\x12\x1b\n\x13\x63tidTraderAccountId\x18\x02 \x02(\x03\x12<\n\x15positionUnrealizedPnL\x18\x03 \x03(\x0b\x32\x1d.ProtoOAPositionUnrealizedPnL\x12\x13\n\x0bmoneyDigits\x18\x04 \x02(\r\"\x8c\x01\n\x16ProtoOAOrderDetailsReq\x12\x44\n\x0bpayloadType\x18\x01 \x01(\x0e\x32\x13.ProtoOAPayloadType:\x1aPROTO_OA_ORDER_DETAILS_REQ\x12\x1b\n\x13\x63tidTraderAccountId\x18\x02 \x02(\x03\x12\x0f\n\x07orderId\x18\x03 \x02(\x03\"\xb5\x01\n\x16ProtoOAOrderDetailsRes\x12\x44\n\x0bpayloadType\x18\x01 \x01(\x0e\x32\x13.ProtoOAPayloadType:\x1aPROTO_OA_ORDER_DETAILS_RES\x12\x1b\n\x13\x63tidTraderAccountId\x18\x02 \x02(\x03\x12\x1c\n\x05order\x18\x03 \x02(\x0b\x32\r.ProtoOAOrder\x12\x1a\n\x04\x64\x65\x61l\x18\x04 \x03(\x0b\x32\x0c.ProtoOADeal\"\xd0\x01\n\x1fProtoOAOrderListByPositionIdReq\x12P\n\x0bpayloadType\x18\x01 \x01(\x0e\x32\x13.ProtoOAPayloadType:&PROTO_OA_ORDER_LIST_BY_POSITION_ID_REQ\x12\x1b\n\x13\x63tidTraderAccountId\x18\x02 \x02(\x03\x12\x12\n\npositionId\x18\x03 \x02(\x03\x12\x15\n\rfromTimestamp\x18\x04 \x01(\x03\x12\x13\n\x0btoTimestamp\x18\x05 \x01(\x03\"\xbf\x01\n\x1fProtoOAOrderListByPositionIdRes\x12P\n\x0bpayloadType\x18\x01 \x01(\x0e\x32\x13.ProtoOAPayloadType:&PROTO_OA_ORDER_LIST_BY_POSITION_ID_RES\x12\x1b\n\x13\x63tidTraderAccountId\x18\x02 \x02(\x03\x12\x1c\n\x05order\x18\x03 \x03(\x0b\x32\r.ProtoOAOrder\x12\x0f\n\x07hasMore\x18\x04 \x02(\x08\x42\x42\n\x1f\x63om.xtrader.protocol.openapi.v2B\x1a\x43ontainerOpenApiV2MessagesP\x01\xa0\x01\x01')

_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, globals())
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'OpenApiMessages_pb2', globals())
if _descriptor._USE_C_DESCRIPTORS == False:

  DESCRIPTOR._options = None
  DESCRIPTOR._serialized_options = b'\n\037com.xtrader.protocol.openapi.v2B\032ContainerOpenApiV2MessagesP\001\240\001\001'
  _PROTOOADEPTHEVENT.fields_by_name['deletedQuotes']._options = None
  _PROTOOADEPTHEVENT.fields_by_name['deletedQuotes']._serialized_options = b'\020\001'
  _PROTOOAAPPLICATIONAUTHREQ._serialized_start=54
  _PROTOOAAPPLICATIONAUTHREQ._serialized_end=194
  _PROTOOAAPPLICATIONAUTHRES._serialized_start=196
  _PROTOOAAPPLICATIONAUTHRES._serialized_end=296
  _PROTOOAACCOUNTAUTHREQ._serialized_start=299
  _PROTOOAACCOUNTAUTHREQ._serialized_end=441
  _PROTOOAACCOUNTAUTHRES._serialized_start=443
  _PROTOOAACCOUNTAUTHRES._serialized_end=564
  _PROTOOAERRORRES._serialized_start=567
  _PROTOOAERRORRES._serialized_end=748
  _PROTOOACLIENTDISCONNECTEVENT._serialized_start=750
  _PROTOOACLIENTDISCONNECTEVENT._serialized_end=872
  _PROTOOAACCOUNTSTOKENINVALIDATEDEVENT._serialized_start=875
  _PROTOOAACCOUNTSTOKENINVALIDATEDEVENT._serialized_end=1044
  _PROTOOAVERSIONREQ._serialized_start=1046
  _PROTOOAVERSIONREQ._serialized_end=1129
  _PROTOOAVERSIONRES._serialized_start=1131
  _PROTOOAVERSIONRES._serialized_end=1231
  _PROTOOANEWORDERREQ._serialized_start=1234
  _PROTOOANEWORDERREQ._serialized_end=1923
  _PROTOOAEXECUTIONEVENT._serialized_start=1926
  _PROTOOAEXECUTIONEVENT._serialized_end=2338
  _PROTOOACANCELORDERREQ._serialized_start=2341
  _PROTOOACANCELORDERREQ._serialized_end=2479
  _PROTOOAAMENDORDERREQ._serialized_start=2482
  _PROTOOAAMENDORDERREQ._serialized_end=2936
  _PROTOOAAMENDPOSITIONSLTPREQ._serialized_start=2939
  _PROTOOAAMENDPOSITIONSLTPREQ._serialized_end=3251
  _PROTOOACLOSEPOSITIONREQ._serialized_start=3254
  _PROTOOACLOSEPOSITIONREQ._serialized_end=3415
  _PROTOOATRAILINGSLCHANGEDEVENT._serialized_start=3418
  _PROTOOATRAILINGSLCHANGEDEVENT._serialized_end=3644
  _PROTOOAASSETLISTREQ._serialized_start=3646
  _PROTOOAASSETLISTREQ._serialized_end=3763
  _PROTOOAASSETLISTRES._serialized_start=3766
  _PROTOOAASSETLISTRES._serialized_end=3913
  _PROTOOASYMBOLSLISTREQ._serialized_start=3916
  _PROTOOASYMBOLSLISTREQ._serialized_end=4076
  _PROTOOASYMBOLSLISTRES._serialized_start=4079
  _PROTOOASYMBOLSLISTRES._serialized_end=4285
  _PROTOOASYMBOLBYIDREQ._serialized_start=4288
  _PROTOOASYMBOLBYIDREQ._serialized_end=4426
  _PROTOOASYMBOLBYIDRES._serialized_start=4429
  _PROTOOASYMBOLBYIDRES._serialized_end=4629
  _PROTOOASYMBOLSFORCONVERSIONREQ._serialized_start=4632
  _PROTOOASYMBOLSFORCONVERSIONREQ._serialized_end=4815
  _PROTOOASYMBOLSFORCONVERSIONRES._serialized_start=4818
  _PROTOOASYMBOLSFORCONVERSIONRES._serialized_end=4995
  _PROTOOASYMBOLCHANGEDEVENT._serialized_start=4998
  _PROTOOASYMBOLCHANGEDEVENT._serialized_end=5145
  _PROTOOAASSETCLASSLISTREQ._serialized_start=5148
  _PROTOOAASSETCLASSLISTREQ._serialized_end=5276
  _PROTOOAASSETCLASSLISTRES._serialized_start=5279
  _PROTOOAASSETCLASSLISTRES._serialized_end=5447
  _PROTOOATRADERREQ._serialized_start=5449
  _PROTOOATRADERREQ._serialized_end=5559
  _PROTOOATRADERRES._serialized_start=5562
  _PROTOOATRADERRES._serialized_end=5704
  _PROTOOATRADERUPDATEDEVENT._serialized_start=5707
  _PROTOOATRADERUPDATEDEVENT._serialized_end=5867
  _PROTOOARECONCILEREQ._serialized_start=5869
  _PROTOOARECONCILEREQ._serialized_end=5985
  _PROTOOARECONCILERES._serialized_start=5988
  _PROTOOARECONCILERES._serialized_end=6170
  _PROTOOAORDERERROREVENT._serialized_start=6173
  _PROTOOAORDERERROREVENT._serialized_end=6373
  _PROTOOADEALLISTREQ._serialized_start=6376
  _PROTOOADEALLISTREQ._serialized_end=6552
  _PROTOOADEALLISTRES._serialized_start=6555
  _PROTOOADEALLISTRES._serialized_end=6715
  _PROTOOAORDERLISTREQ._serialized_start=6718
  _PROTOOAORDERLISTREQ._serialized_end=6879
  _PROTOOAORDERLISTRES._serialized_start=6882
  _PROTOOAORDERLISTRES._serialized_end=7046
  _PROTOOAEXPECTEDMARGINREQ._serialized_start=7049
  _PROTOOAEXPECTEDMARGINREQ._serialized_end=7210
  _PROTOOAEXPECTEDMARGINRES._serialized_start=7213
  _PROTOOAEXPECTEDMARGINRES._serialized_end=7401
  _PROTOOAMARGINCHANGEDEVENT._serialized_start=7404
  _PROTOOAMARGINCHANGEDEVENT._serialized_end=7594
  _PROTOOACASHFLOWHISTORYLISTREQ._serialized_start=7597
  _PROTOOACASHFLOWHISTORYLISTREQ._serialized_end=7780
  _PROTOOACASHFLOWHISTORYLISTRES._serialized_start=7783
  _PROTOOACASHFLOWHISTORYLISTRES._serialized_end=7972
  _PROTOOAGETACCOUNTLISTBYACCESSTOKENREQ._serialized_start=7975
  _PROTOOAGETACCOUNTLISTBYACCESSTOKENREQ._serialized_end=8120
  _PROTOOAGETACCOUNTLISTBYACCESSTOKENRES._serialized_start=8123
  _PROTOOAGETACCOUNTLISTBYACCESSTOKENRES._serialized_end=8378
  _PROTOOAREFRESHTOKENREQ._serialized_start=8380
  _PROTOOAREFRESHTOKENREQ._serialized_end=8496
  _PROTOOAREFRESHTOKENRES._serialized_start=8499
  _PROTOOAREFRESHTOKENRES._serialized_end=8674
  _PROTOOASUBSCRIBESPOTSREQ._serialized_start=8677
  _PROTOOASUBSCRIBESPOTSREQ._serialized_end=8856
  _PROTOOASUBSCRIBESPOTSRES._serialized_start=8858
  _PROTOOASUBSCRIBESPOTSRES._serialized_end=8985
  _PROTOOAUNSUBSCRIBESPOTSREQ._serialized_start=8988
  _PROTOOAUNSUBSCRIBESPOTSREQ._serialized_end=9137
  _PROTOOAUNSUBSCRIBESPOTSRES._serialized_start=9140
  _PROTOOAUNSUBSCRIBESPOTSRES._serialized_end=9271
  _PROTOOASPOTEVENT._serialized_start=9274
  _PROTOOASPOTEVENT._serialized_end=9505
  _PROTOOASUBSCRIBELIVETRENDBARREQ._serialized_start=9508
  _PROTOOASUBSCRIBELIVETRENDBARREQ._serialized_end=9708
  _PROTOOASUBSCRIBELIVETRENDBARRES._serialized_start=9711
  _PROTOOASUBSCRIBELIVETRENDBARRES._serialized_end=9853
  _PROTOOAUNSUBSCRIBELIVETRENDBARREQ._serialized_start=9856
  _PROTOOAUNSUBSCRIBELIVETRENDBARREQ._serialized_end=10060
  _PROTOOAUNSUBSCRIBELIVETRENDBARRES._serialized_start=10063
  _PROTOOAUNSUBSCRIBELIVETRENDBARRES._serialized_end=10209
  _PROTOOAGETTRENDBARSREQ._serialized_start=10212
  _PROTOOAGETTRENDBARSREQ._serialized_end=10452
  _PROTOOAGETTRENDBARSRES._serialized_start=10455
  _PROTOOAGETTRENDBARSRES._serialized_end=10691
  _PROTOOAGETTICKDATAREQ._serialized_start=10694
  _PROTOOAGETTICKDATAREQ._serialized_end=10910
  _PROTOOAGETTICKDATARES._serialized_start=10913
  _PROTOOAGETTICKDATARES._serialized_end=11087
  _PROTOOAGETCTIDPROFILEBYTOKENREQ._serialized_start=11090
  _PROTOOAGETCTIDPROFILEBYTOKENREQ._serialized_end=11226
  _PROTOOAGETCTIDPROFILEBYTOKENRES._serialized_start=11229
  _PROTOOAGETCTIDPROFILEBYTOKENRES._serialized_end=11382
  _PROTOOADEPTHEVENT._serialized_start=11385
  _PROTOOADEPTHEVENT._serialized_end=11581
  _PROTOOASUBSCRIBEDEPTHQUOTESREQ._serialized_start=11584
  _PROTOOASUBSCRIBEDEPTHQUOTESREQ._serialized_end=11742
  _PROTOOASUBSCRIBEDEPTHQUOTESRES._serialized_start=11745
  _PROTOOASUBSCRIBEDEPTHQUOTESRES._serialized_end=11885
  _PROTOOAUNSUBSCRIBEDEPTHQUOTESREQ._serialized_start=11888
  _PROTOOAUNSUBSCRIBEDEPTHQUOTESREQ._serialized_end=12050
  _PROTOOAUNSUBSCRIBEDEPTHQUOTESRES._serialized_start=12053
  _PROTOOAUNSUBSCRIBEDEPTHQUOTESRES._serialized_end=12197
  _PROTOOASYMBOLCATEGORYLISTREQ._serialized_start=12200
  _PROTOOASYMBOLCATEGORYLISTREQ._serialized_end=12331
  _PROTOOASYMBOLCATEGORYLISTRES._serialized_start=12334
  _PROTOOASYMBOLCATEGORYLISTRES._serialized_end=12513
  _PROTOOAACCOUNTLOGOUTREQ._serialized_start=12515
  _PROTOOAACCOUNTLOGOUTREQ._serialized_end=12640
  _PROTOOAACCOUNTLOGOUTRES._serialized_start=12642
  _PROTOOAACCOUNTLOGOUTRES._serialized_end=12767
  _PROTOOAACCOUNTDISCONNECTEVENT._serialized_start=12770
  _PROTOOAACCOUNTDISCONNECTEVENT._serialized_end=12907
  _PROTOOAMARGINCALLLISTREQ._serialized_start=12910
  _PROTOOAMARGINCALLLISTREQ._serialized_end=13038
  _PROTOOAMARGINCALLLISTRES._serialized_start=13041
  _PROTOOAMARGINCALLLISTRES._serialized_end=13180
  _PROTOOAMARGINCALLUPDATEREQ._serialized_start=13183
  _PROTOOAMARGINCALLUPDATEREQ._serialized_end=13355
  _PROTOOAMARGINCALLUPDATERES._serialized_start=13357
  _PROTOOAMARGINCALLUPDATERES._serialized_end=13460
  _PROTOOAMARGINCALLUPDATEEVENT._serialized_start=13463
  _PROTOOAMARGINCALLUPDATEEVENT._serialized_end=13639
  _PROTOOAMARGINCALLTRIGGEREVENT._serialized_start=13642
  _PROTOOAMARGINCALLTRIGGEREVENT._serialized_end=13820
  _PROTOOAGETDYNAMICLEVERAGEBYIDREQ._serialized_start=13823
  _PROTOOAGETDYNAMICLEVERAGEBYIDREQ._serialized_end=13983
  _PROTOOAGETDYNAMICLEVERAGEBYIDRES._serialized_start=13986
  _PROTOOAGETDYNAMICLEVERAGEBYIDRES._serialized_end=14169
  _PROTOOADEALLISTBYPOSITIONIDREQ._serialized_start=14172
  _PROTOOADEALLISTBYPOSITIONIDREQ._serialized_end=14378
  _PROTOOADEALLISTBYPOSITIONIDRES._serialized_start=14381
  _PROTOOADEALLISTBYPOSITIONIDRES._serialized_end=14568
  _PROTOOADEALOFFSETLISTREQ._serialized_start=14670
  _PROTOOADEALOFFSETLISTREQ._serialized_end=14814
  _PROTOOADEALOFFSETLISTRES._serialized_start=14817
  _PROTOOADEALOFFSETLISTRES._serialized_end=15023
  _PROTOOAGETPOSITIONUNREALIZEDPNLREQ._serialized_start=15026
  _PROTOOAGETPOSITIONUNREALIZEDPNLREQ._serialized_end=15175
  _PROTOOAGETPOSITIONUNREALIZEDPNLRES._serialized_start=15178
  _PROTOOAGETPOSITIONUNREALIZEDPNLRES._serialized_end=15410
  _PROTOOAORDERDETAILSREQ._serialized_start=15413
  _PROTOOAORDERDETAILSREQ._serialized_end=15553
  _PROTOOAORDERDETAILSRES._serialized_start=15556
  _PROTOOAORDERDETAILSRES._serialized_end=15737
  _PROTOOAORDERLISTBYPOSITIONIDREQ._serialized_start=15740
  _PROTOOAORDERLISTBYPOSITIONIDREQ._serialized_end=15948
  _PROTOOAORDERLISTBYPOSITIONIDRES._serialized_start=15951
  _PROTOOAORDERLISTBYPOSITIONIDRES._serialized_end=16142
# @@protoc_insertion_point(module_scope)
````

## File: ctrader_open_api/messages/OpenApiModelMessages_pb2.py
````python
# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: OpenApiModelMessages.proto
"""Generated protocol buffer code."""
from google.protobuf.internal import builder as _builder
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x1aOpenApiModelMessages.proto\"R\n\x0cProtoOAAsset\x12\x0f\n\x07\x61ssetId\x18\x01 \x02(\x03\x12\x0c\n\x04name\x18\x02 \x02(\t\x12\x13\n\x0b\x64isplayName\x18\x03 \x01(\t\x12\x0e\n\x06\x64igits\x18\x04 \x01(\x05\"\xc8\t\n\rProtoOASymbol\x12\x10\n\x08symbolId\x18\x01 \x02(\x03\x12\x0e\n\x06\x64igits\x18\x02 \x02(\x05\x12\x13\n\x0bpipPosition\x18\x03 \x02(\x05\x12\x1a\n\x12\x65nableShortSelling\x18\x04 \x01(\x08\x12\x1a\n\x12guaranteedStopLoss\x18\x05 \x01(\x08\x12\x34\n\x11swapRollover3Days\x18\x06 \x01(\x0e\x32\x11.ProtoOADayOfWeek:\x06MONDAY\x12\x10\n\x08swapLong\x18\x07 \x01(\x01\x12\x11\n\tswapShort\x18\x08 \x01(\x01\x12\x11\n\tmaxVolume\x18\t \x01(\x03\x12\x11\n\tminVolume\x18\n \x01(\x03\x12\x12\n\nstepVolume\x18\x0b \x01(\x03\x12\x13\n\x0bmaxExposure\x18\x0c \x01(\x04\x12\"\n\x08schedule\x18\r \x03(\x0b\x32\x10.ProtoOAInterval\x12\x16\n\ncommission\x18\x0e \x01(\x03\x42\x02\x18\x01\x12\x43\n\x0e\x63ommissionType\x18\x0f \x01(\x0e\x32\x16.ProtoOACommissionType:\x13USD_PER_MILLION_USD\x12\x12\n\nslDistance\x18\x10 \x01(\r\x12\x12\n\ntpDistance\x18\x11 \x01(\r\x12\x13\n\x0bgslDistance\x18\x12 \x01(\r\x12\x11\n\tgslCharge\x18\x13 \x01(\x03\x12L\n\rdistanceSetIn\x18\x14 \x01(\x0e\x32\x1a.ProtoOASymbolDistanceType:\x19SYMBOL_DISTANCE_IN_POINTS\x12\x19\n\rminCommission\x18\x15 \x01(\x03\x42\x02\x18\x01\x12>\n\x11minCommissionType\x18\x16 \x01(\x0e\x32\x19.ProtoOAMinCommissionType:\x08\x43URRENCY\x12\x1f\n\x12minCommissionAsset\x18\x17 \x01(\t:\x03USD\x12\x1a\n\x12rolloverCommission\x18\x18 \x01(\x03\x12\x18\n\x10skipRolloverDays\x18\x19 \x01(\x05\x12\x18\n\x10scheduleTimeZone\x18\x1a \x01(\t\x12\x31\n\x0btradingMode\x18\x1b \x01(\x0e\x32\x13.ProtoOATradingMode:\x07\x45NABLED\x12:\n\x17rolloverCommission3Days\x18\x1c \x01(\x0e\x32\x11.ProtoOADayOfWeek:\x06MONDAY\x12>\n\x13swapCalculationType\x18\x1d \x01(\x0e\x32\x1b.ProtoOASwapCalculationType:\x04PIPS\x12\x0f\n\x07lotSize\x18\x1e \x01(\x03\x12$\n\x1cpreciseTradingCommissionRate\x18\x1f \x01(\x03\x12\x1c\n\x14preciseMinCommission\x18  \x01(\x03\x12 \n\x07holiday\x18! \x03(\x0b\x32\x0f.ProtoOAHoliday\x12\x1c\n\x14pnlConversionFeeRate\x18\" \x01(\x05\x12\x12\n\nleverageId\x18# \x01(\x03\x12\x12\n\nswapPeriod\x18$ \x01(\x05\x12\x10\n\x08swapTime\x18% \x01(\x05\x12\x17\n\x0fskipSWAPPeriods\x18& \x01(\x05\x12\x1c\n\x14\x63hargeSwapAtWeekends\x18\' \x01(\x08\"\xa5\x01\n\x12ProtoOALightSymbol\x12\x10\n\x08symbolId\x18\x01 \x02(\x03\x12\x12\n\nsymbolName\x18\x02 \x01(\t\x12\x0f\n\x07\x65nabled\x18\x03 \x01(\x08\x12\x13\n\x0b\x62\x61seAssetId\x18\x04 \x01(\x03\x12\x14\n\x0cquoteAssetId\x18\x05 \x01(\x03\x12\x18\n\x10symbolCategoryId\x18\x06 \x01(\x03\x12\x13\n\x0b\x64\x65scription\x18\x07 \x01(\t\"l\n\x15ProtoOAArchivedSymbol\x12\x10\n\x08symbolId\x18\x01 \x02(\x03\x12\x0c\n\x04name\x18\x02 \x02(\t\x12\x1e\n\x16utcLastUpdateTimestamp\x18\x03 \x02(\x03\x12\x13\n\x0b\x64\x65scription\x18\x04 \x01(\t\"G\n\x15ProtoOASymbolCategory\x12\n\n\x02id\x18\x01 \x02(\x03\x12\x14\n\x0c\x61ssetClassId\x18\x02 \x02(\x03\x12\x0c\n\x04name\x18\x03 \x02(\t\"9\n\x0fProtoOAInterval\x12\x13\n\x0bstartSecond\x18\x03 \x02(\r\x12\x11\n\tendSecond\x18\x04 \x02(\r\"\xa4\x05\n\rProtoOATrader\x12\x1b\n\x13\x63tidTraderAccountId\x18\x01 \x02(\x03\x12\x0f\n\x07\x62\x61lance\x18\x02 \x02(\x03\x12\x16\n\x0e\x62\x61lanceVersion\x18\x03 \x01(\x03\x12\x14\n\x0cmanagerBonus\x18\x04 \x01(\x03\x12\x0f\n\x07ibBonus\x18\x05 \x01(\x03\x12\x1c\n\x14nonWithdrawableBonus\x18\x06 \x01(\x03\x12\x37\n\x0c\x61\x63\x63\x65ssRights\x18\x07 \x01(\x0e\x32\x14.ProtoOAAccessRights:\x0b\x46ULL_ACCESS\x12\x16\n\x0e\x64\x65positAssetId\x18\x08 \x02(\x03\x12\x10\n\x08swapFree\x18\t \x01(\x08\x12\x17\n\x0fleverageInCents\x18\n \x01(\r\x12\x46\n\x1atotalMarginCalculationType\x18\x0b \x01(\x0e\x32\".ProtoOATotalMarginCalculationType\x12\x13\n\x0bmaxLeverage\x18\x0c \x01(\r\x12\x16\n\nfrenchRisk\x18\r \x01(\x08\x42\x02\x18\x01\x12\x13\n\x0btraderLogin\x18\x0e \x01(\x03\x12\x30\n\x0b\x61\x63\x63ountType\x18\x0f \x01(\x0e\x32\x13.ProtoOAAccountType:\x06HEDGED\x12\x12\n\nbrokerName\x18\x10 \x01(\t\x12\x1d\n\x15registrationTimestamp\x18\x11 \x01(\x03\x12\x15\n\risLimitedRisk\x18\x12 \x01(\x08\x12q\n$limitedRiskMarginCalculationStrategy\x18\x13 \x01(\x0e\x32,.ProtoOALimitedRiskMarginCalculationStrategy:\x15\x41\x43\x43ORDING_TO_LEVERAGE\x12\x13\n\x0bmoneyDigits\x18\x14 \x01(\r\"\xc4\x03\n\x0fProtoOAPosition\x12\x12\n\npositionId\x18\x01 \x02(\x03\x12$\n\ttradeData\x18\x02 \x02(\x0b\x32\x11.ProtoOATradeData\x12.\n\x0epositionStatus\x18\x03 \x02(\x0e\x32\x16.ProtoOAPositionStatus\x12\x0c\n\x04swap\x18\x04 \x02(\x03\x12\r\n\x05price\x18\x05 \x01(\x01\x12\x10\n\x08stopLoss\x18\x06 \x01(\x01\x12\x12\n\ntakeProfit\x18\x07 \x01(\x01\x12\x1e\n\x16utcLastUpdateTimestamp\x18\x08 \x01(\x03\x12\x12\n\ncommission\x18\t \x01(\x03\x12\x12\n\nmarginRate\x18\n \x01(\x01\x12\x1b\n\x13mirroringCommission\x18\x0b \x01(\x03\x12\x1a\n\x12guaranteedStopLoss\x18\x0c \x01(\x08\x12\x12\n\nusedMargin\x18\r \x01(\x04\x12@\n\x15stopLossTriggerMethod\x18\x0e \x01(\x0e\x32\x1a.ProtoOAOrderTriggerMethod:\x05TRADE\x12\x13\n\x0bmoneyDigits\x18\x0f \x01(\r\x12\x18\n\x10trailingStopLoss\x18\x10 \x01(\x08\"\xad\x01\n\x10ProtoOATradeData\x12\x10\n\x08symbolId\x18\x01 \x02(\x03\x12\x0e\n\x06volume\x18\x02 \x02(\x03\x12$\n\ttradeSide\x18\x03 \x02(\x0e\x32\x11.ProtoOATradeSide\x12\x15\n\ropenTimestamp\x18\x04 \x01(\x03\x12\r\n\x05label\x18\x05 \x01(\t\x12\x1a\n\x12guaranteedStopLoss\x18\x06 \x01(\x08\x12\x0f\n\x07\x63omment\x18\x07 \x01(\t\"\xa5\x05\n\x0cProtoOAOrder\x12\x0f\n\x07orderId\x18\x01 \x02(\x03\x12$\n\ttradeData\x18\x02 \x02(\x0b\x32\x11.ProtoOATradeData\x12$\n\torderType\x18\x03 \x02(\x0e\x32\x11.ProtoOAOrderType\x12(\n\x0borderStatus\x18\x04 \x02(\x0e\x32\x13.ProtoOAOrderStatus\x12\x1b\n\x13\x65xpirationTimestamp\x18\x06 \x01(\x03\x12\x16\n\x0e\x65xecutionPrice\x18\x07 \x01(\x01\x12\x16\n\x0e\x65xecutedVolume\x18\x08 \x01(\x03\x12\x1e\n\x16utcLastUpdateTimestamp\x18\t \x01(\x03\x12\x19\n\x11\x62\x61seSlippagePrice\x18\n \x01(\x01\x12\x18\n\x10slippageInPoints\x18\x0b \x01(\x03\x12\x14\n\x0c\x63losingOrder\x18\x0c \x01(\x08\x12\x12\n\nlimitPrice\x18\r \x01(\x01\x12\x11\n\tstopPrice\x18\x0e \x01(\x01\x12\x10\n\x08stopLoss\x18\x0f \x01(\x01\x12\x12\n\ntakeProfit\x18\x10 \x01(\x01\x12\x15\n\rclientOrderId\x18\x11 \x01(\t\x12=\n\x0btimeInForce\x18\x12 \x01(\x0e\x32\x13.ProtoOATimeInForce:\x13IMMEDIATE_OR_CANCEL\x12\x12\n\npositionId\x18\x13 \x01(\x03\x12\x18\n\x10relativeStopLoss\x18\x14 \x01(\x03\x12\x1a\n\x12relativeTakeProfit\x18\x15 \x01(\x03\x12\x11\n\tisStopOut\x18\x16 \x01(\x08\x12\x18\n\x10trailingStopLoss\x18\x17 \x01(\x08\x12<\n\x11stopTriggerMethod\x18\x18 \x01(\x0e\x32\x1a.ProtoOAOrderTriggerMethod:\x05TRADE\"\x99\x02\n\x1bProtoOABonusDepositWithdraw\x12.\n\roperationType\x18\x01 \x02(\x0e\x32\x17.ProtoOAChangeBonusType\x12\x16\n\x0e\x62onusHistoryId\x18\x02 \x02(\x03\x12\x14\n\x0cmanagerBonus\x18\x03 \x02(\x03\x12\x14\n\x0cmanagerDelta\x18\x04 \x02(\x03\x12\x0f\n\x07ibBonus\x18\x05 \x02(\x03\x12\x0f\n\x07ibDelta\x18\x06 \x02(\x03\x12\x1c\n\x14\x63hangeBonusTimestamp\x18\x07 \x02(\x03\x12\x14\n\x0c\x65xternalNote\x18\x08 \x01(\t\x12\x1b\n\x13introducingBrokerId\x18\t \x01(\x03\x12\x13\n\x0bmoneyDigits\x18\n \x01(\r\"\xf7\x01\n\x16ProtoOADepositWithdraw\x12\x30\n\roperationType\x18\x01 \x02(\x0e\x32\x19.ProtoOAChangeBalanceType\x12\x18\n\x10\x62\x61lanceHistoryId\x18\x02 \x02(\x03\x12\x0f\n\x07\x62\x61lance\x18\x03 \x02(\x03\x12\r\n\x05\x64\x65lta\x18\x04 \x02(\x03\x12\x1e\n\x16\x63hangeBalanceTimestamp\x18\x05 \x02(\x03\x12\x14\n\x0c\x65xternalNote\x18\x06 \x01(\t\x12\x16\n\x0e\x62\x61lanceVersion\x18\x07 \x01(\x03\x12\x0e\n\x06\x65quity\x18\x08 \x01(\x03\x12\x13\n\x0bmoneyDigits\x18\t \x01(\r\"\xcd\x03\n\x0bProtoOADeal\x12\x0e\n\x06\x64\x65\x61lId\x18\x01 \x02(\x03\x12\x0f\n\x07orderId\x18\x02 \x02(\x03\x12\x12\n\npositionId\x18\x03 \x02(\x03\x12\x0e\n\x06volume\x18\x04 \x02(\x03\x12\x14\n\x0c\x66illedVolume\x18\x05 \x02(\x03\x12\x10\n\x08symbolId\x18\x06 \x02(\x03\x12\x17\n\x0f\x63reateTimestamp\x18\x07 \x02(\x03\x12\x1a\n\x12\x65xecutionTimestamp\x18\x08 \x02(\x03\x12\x1e\n\x16utcLastUpdateTimestamp\x18\t \x01(\x03\x12\x16\n\x0e\x65xecutionPrice\x18\n \x01(\x01\x12$\n\ttradeSide\x18\x0b \x02(\x0e\x32\x11.ProtoOATradeSide\x12&\n\ndealStatus\x18\x0c \x02(\x0e\x32\x12.ProtoOADealStatus\x12\x12\n\nmarginRate\x18\r \x01(\x01\x12\x12\n\ncommission\x18\x0e \x01(\x03\x12\x1f\n\x17\x62\x61seToUsdConversionRate\x18\x0f \x01(\x01\x12\x38\n\x13\x63losePositionDetail\x18\x10 \x01(\x0b\x32\x1b.ProtoOAClosePositionDetail\x12\x13\n\x0bmoneyDigits\x18\x11 \x01(\r\"\xfb\x01\n\x1aProtoOAClosePositionDetail\x12\x12\n\nentryPrice\x18\x01 \x02(\x01\x12\x13\n\x0bgrossProfit\x18\x02 \x02(\x03\x12\x0c\n\x04swap\x18\x03 \x02(\x03\x12\x12\n\ncommission\x18\x04 \x02(\x03\x12\x0f\n\x07\x62\x61lance\x18\x05 \x02(\x03\x12$\n\x1cquoteToDepositConversionRate\x18\x06 \x01(\x01\x12\x14\n\x0c\x63losedVolume\x18\x07 \x01(\x03\x12\x16\n\x0e\x62\x61lanceVersion\x18\x08 \x01(\x03\x12\x13\n\x0bmoneyDigits\x18\t \x01(\r\x12\x18\n\x10pnlConversionFee\x18\n \x01(\x03\"\xb3\x01\n\x0fProtoOATrendbar\x12\x0e\n\x06volume\x18\x03 \x02(\x03\x12*\n\x06period\x18\x04 \x01(\x0e\x32\x16.ProtoOATrendbarPeriod:\x02M1\x12\x0b\n\x03low\x18\x05 \x01(\x03\x12\x11\n\tdeltaOpen\x18\x06 \x01(\x04\x12\x12\n\ndeltaClose\x18\x07 \x01(\x04\x12\x11\n\tdeltaHigh\x18\x08 \x01(\x04\x12\x1d\n\x15utcTimestampInMinutes\x18\t \x01(\r\"N\n\x15ProtoOAExpectedMargin\x12\x0e\n\x06volume\x18\x01 \x02(\x03\x12\x11\n\tbuyMargin\x18\x02 \x02(\x03\x12\x12\n\nsellMargin\x18\x03 \x02(\x03\"2\n\x0fProtoOATickData\x12\x11\n\ttimestamp\x18\x01 \x02(\x03\x12\x0c\n\x04tick\x18\x02 \x02(\x03\"$\n\x12ProtoOACtidProfile\x12\x0e\n\x06userId\x18\x01 \x02(\x03\"\xa2\x01\n\x18ProtoOACtidTraderAccount\x12\x1b\n\x13\x63tidTraderAccountId\x18\x01 \x02(\x04\x12\x0e\n\x06isLive\x18\x02 \x01(\x08\x12\x13\n\x0btraderLogin\x18\x03 \x01(\x03\x12 \n\x18lastClosingDealTimestamp\x18\x04 \x01(\x03\x12\"\n\x1alastBalanceUpdateTimestamp\x18\x05 \x01(\x03\"-\n\x11ProtoOAAssetClass\x12\n\n\x02id\x18\x01 \x01(\x03\x12\x0c\n\x04name\x18\x02 \x01(\t\"G\n\x11ProtoOADepthQuote\x12\n\n\x02id\x18\x01 \x02(\x04\x12\x0c\n\x04size\x18\x03 \x02(\x04\x12\x0b\n\x03\x62id\x18\x04 \x01(\x04\x12\x0b\n\x03\x61sk\x18\x05 \x01(\x04\"\x83\x01\n\x11ProtoOAMarginCall\x12\x30\n\x0emarginCallType\x18\x01 \x02(\x0e\x32\x18.ProtoOANotificationType\x12\x1c\n\x14marginLevelThreshold\x18\x02 \x02(\x01\x12\x1e\n\x16utcLastUpdateTimestamp\x18\x03 \x01(\x03\"\xb2\x01\n\x0eProtoOAHoliday\x12\x11\n\tholidayId\x18\x01 \x02(\x03\x12\x0c\n\x04name\x18\x02 \x02(\t\x12\x13\n\x0b\x64\x65scription\x18\x03 \x01(\t\x12\x18\n\x10scheduleTimeZone\x18\x04 \x02(\t\x12\x13\n\x0bholidayDate\x18\x05 \x02(\x03\x12\x13\n\x0bisRecurring\x18\x06 \x02(\x08\x12\x13\n\x0bstartSecond\x18\x07 \x01(\x05\x12\x11\n\tendSecond\x18\x08 \x01(\x05\"X\n\x16ProtoOADynamicLeverage\x12\x12\n\nleverageId\x18\x01 \x02(\x03\x12*\n\x05tiers\x18\x02 \x03(\x0b\x32\x1b.ProtoOADynamicLeverageTier\">\n\x1aProtoOADynamicLeverageTier\x12\x0e\n\x06volume\x18\x01 \x02(\x03\x12\x10\n\x08leverage\x18\x02 \x02(\x03\"g\n\x11ProtoOADealOffset\x12\x0e\n\x06\x64\x65\x61lId\x18\x01 \x02(\x03\x12\x0e\n\x06volume\x18\x02 \x02(\x03\x12\x1a\n\x12\x65xecutionTimestamp\x18\x03 \x01(\x03\x12\x16\n\x0e\x65xecutionPrice\x18\x04 \x01(\x01\"h\n\x1cProtoOAPositionUnrealizedPnL\x12\x12\n\npositionId\x18\x01 \x02(\x03\x12\x1a\n\x12grossUnrealizedPnL\x18\x02 \x02(\x03\x12\x18\n\x10netUnrealizedPnL\x18\x03 \x02(\x05*\xb1\x19\n\x12ProtoOAPayloadType\x12\"\n\x1dPROTO_OA_APPLICATION_AUTH_REQ\x10\xb4\x10\x12\"\n\x1dPROTO_OA_APPLICATION_AUTH_RES\x10\xb5\x10\x12\x1e\n\x19PROTO_OA_ACCOUNT_AUTH_REQ\x10\xb6\x10\x12\x1e\n\x19PROTO_OA_ACCOUNT_AUTH_RES\x10\xb7\x10\x12\x19\n\x14PROTO_OA_VERSION_REQ\x10\xb8\x10\x12\x19\n\x14PROTO_OA_VERSION_RES\x10\xb9\x10\x12\x1b\n\x16PROTO_OA_NEW_ORDER_REQ\x10\xba\x10\x12\'\n\"PROTO_OA_TRAILING_SL_CHANGED_EVENT\x10\xbb\x10\x12\x1e\n\x19PROTO_OA_CANCEL_ORDER_REQ\x10\xbc\x10\x12\x1d\n\x18PROTO_OA_AMEND_ORDER_REQ\x10\xbd\x10\x12%\n PROTO_OA_AMEND_POSITION_SLTP_REQ\x10\xbe\x10\x12 \n\x1bPROTO_OA_CLOSE_POSITION_REQ\x10\xbf\x10\x12\x1c\n\x17PROTO_OA_ASSET_LIST_REQ\x10\xc0\x10\x12\x1c\n\x17PROTO_OA_ASSET_LIST_RES\x10\xc1\x10\x12\x1e\n\x19PROTO_OA_SYMBOLS_LIST_REQ\x10\xc2\x10\x12\x1e\n\x19PROTO_OA_SYMBOLS_LIST_RES\x10\xc3\x10\x12\x1e\n\x19PROTO_OA_SYMBOL_BY_ID_REQ\x10\xc4\x10\x12\x1e\n\x19PROTO_OA_SYMBOL_BY_ID_RES\x10\xc5\x10\x12(\n#PROTO_OA_SYMBOLS_FOR_CONVERSION_REQ\x10\xc6\x10\x12(\n#PROTO_OA_SYMBOLS_FOR_CONVERSION_RES\x10\xc7\x10\x12\"\n\x1dPROTO_OA_SYMBOL_CHANGED_EVENT\x10\xc8\x10\x12\x18\n\x13PROTO_OA_TRADER_REQ\x10\xc9\x10\x12\x18\n\x13PROTO_OA_TRADER_RES\x10\xca\x10\x12!\n\x1cPROTO_OA_TRADER_UPDATE_EVENT\x10\xcb\x10\x12\x1b\n\x16PROTO_OA_RECONCILE_REQ\x10\xcc\x10\x12\x1b\n\x16PROTO_OA_RECONCILE_RES\x10\xcd\x10\x12\x1d\n\x18PROTO_OA_EXECUTION_EVENT\x10\xce\x10\x12!\n\x1cPROTO_OA_SUBSCRIBE_SPOTS_REQ\x10\xcf\x10\x12!\n\x1cPROTO_OA_SUBSCRIBE_SPOTS_RES\x10\xd0\x10\x12#\n\x1ePROTO_OA_UNSUBSCRIBE_SPOTS_REQ\x10\xd1\x10\x12#\n\x1ePROTO_OA_UNSUBSCRIBE_SPOTS_RES\x10\xd2\x10\x12\x18\n\x13PROTO_OA_SPOT_EVENT\x10\xd3\x10\x12\x1f\n\x1aPROTO_OA_ORDER_ERROR_EVENT\x10\xd4\x10\x12\x1b\n\x16PROTO_OA_DEAL_LIST_REQ\x10\xd5\x10\x12\x1b\n\x16PROTO_OA_DEAL_LIST_RES\x10\xd6\x10\x12)\n$PROTO_OA_SUBSCRIBE_LIVE_TRENDBAR_REQ\x10\xd7\x10\x12+\n&PROTO_OA_UNSUBSCRIBE_LIVE_TRENDBAR_REQ\x10\xd8\x10\x12\x1f\n\x1aPROTO_OA_GET_TRENDBARS_REQ\x10\xd9\x10\x12\x1f\n\x1aPROTO_OA_GET_TRENDBARS_RES\x10\xda\x10\x12!\n\x1cPROTO_OA_EXPECTED_MARGIN_REQ\x10\xdb\x10\x12!\n\x1cPROTO_OA_EXPECTED_MARGIN_RES\x10\xdc\x10\x12\"\n\x1dPROTO_OA_MARGIN_CHANGED_EVENT\x10\xdd\x10\x12\x17\n\x12PROTO_OA_ERROR_RES\x10\xde\x10\x12(\n#PROTO_OA_CASH_FLOW_HISTORY_LIST_REQ\x10\xdf\x10\x12(\n#PROTO_OA_CASH_FLOW_HISTORY_LIST_RES\x10\xe0\x10\x12\x1e\n\x19PROTO_OA_GET_TICKDATA_REQ\x10\xe1\x10\x12\x1e\n\x19PROTO_OA_GET_TICKDATA_RES\x10\xe2\x10\x12.\n)PROTO_OA_ACCOUNTS_TOKEN_INVALIDATED_EVENT\x10\xe3\x10\x12%\n PROTO_OA_CLIENT_DISCONNECT_EVENT\x10\xe4\x10\x12.\n)PROTO_OA_GET_ACCOUNTS_BY_ACCESS_TOKEN_REQ\x10\xe5\x10\x12.\n)PROTO_OA_GET_ACCOUNTS_BY_ACCESS_TOKEN_RES\x10\xe6\x10\x12+\n&PROTO_OA_GET_CTID_PROFILE_BY_TOKEN_REQ\x10\xe7\x10\x12+\n&PROTO_OA_GET_CTID_PROFILE_BY_TOKEN_RES\x10\xe8\x10\x12\"\n\x1dPROTO_OA_ASSET_CLASS_LIST_REQ\x10\xe9\x10\x12\"\n\x1dPROTO_OA_ASSET_CLASS_LIST_RES\x10\xea\x10\x12\x19\n\x14PROTO_OA_DEPTH_EVENT\x10\xeb\x10\x12(\n#PROTO_OA_SUBSCRIBE_DEPTH_QUOTES_REQ\x10\xec\x10\x12(\n#PROTO_OA_SUBSCRIBE_DEPTH_QUOTES_RES\x10\xed\x10\x12*\n%PROTO_OA_UNSUBSCRIBE_DEPTH_QUOTES_REQ\x10\xee\x10\x12*\n%PROTO_OA_UNSUBSCRIBE_DEPTH_QUOTES_RES\x10\xef\x10\x12!\n\x1cPROTO_OA_SYMBOL_CATEGORY_REQ\x10\xf0\x10\x12!\n\x1cPROTO_OA_SYMBOL_CATEGORY_RES\x10\xf1\x10\x12 \n\x1bPROTO_OA_ACCOUNT_LOGOUT_REQ\x10\xf2\x10\x12 \n\x1bPROTO_OA_ACCOUNT_LOGOUT_RES\x10\xf3\x10\x12&\n!PROTO_OA_ACCOUNT_DISCONNECT_EVENT\x10\xf4\x10\x12)\n$PROTO_OA_SUBSCRIBE_LIVE_TRENDBAR_RES\x10\xf5\x10\x12+\n&PROTO_OA_UNSUBSCRIBE_LIVE_TRENDBAR_RES\x10\xf6\x10\x12\"\n\x1dPROTO_OA_MARGIN_CALL_LIST_REQ\x10\xf7\x10\x12\"\n\x1dPROTO_OA_MARGIN_CALL_LIST_RES\x10\xf8\x10\x12$\n\x1fPROTO_OA_MARGIN_CALL_UPDATE_REQ\x10\xf9\x10\x12$\n\x1fPROTO_OA_MARGIN_CALL_UPDATE_RES\x10\xfa\x10\x12&\n!PROTO_OA_MARGIN_CALL_UPDATE_EVENT\x10\xfb\x10\x12\'\n\"PROTO_OA_MARGIN_CALL_TRIGGER_EVENT\x10\xfc\x10\x12\x1f\n\x1aPROTO_OA_REFRESH_TOKEN_REQ\x10\xfd\x10\x12\x1f\n\x1aPROTO_OA_REFRESH_TOKEN_RES\x10\xfe\x10\x12\x1c\n\x17PROTO_OA_ORDER_LIST_REQ\x10\xff\x10\x12\x1c\n\x17PROTO_OA_ORDER_LIST_RES\x10\x80\x11\x12&\n!PROTO_OA_GET_DYNAMIC_LEVERAGE_REQ\x10\x81\x11\x12&\n!PROTO_OA_GET_DYNAMIC_LEVERAGE_RES\x10\x82\x11\x12*\n%PROTO_OA_DEAL_LIST_BY_POSITION_ID_REQ\x10\x83\x11\x12*\n%PROTO_OA_DEAL_LIST_BY_POSITION_ID_RES\x10\x84\x11\x12\x1f\n\x1aPROTO_OA_ORDER_DETAILS_REQ\x10\x85\x11\x12\x1f\n\x1aPROTO_OA_ORDER_DETAILS_RES\x10\x86\x11\x12+\n&PROTO_OA_ORDER_LIST_BY_POSITION_ID_REQ\x10\x87\x11\x12+\n&PROTO_OA_ORDER_LIST_BY_POSITION_ID_RES\x10\x88\x11\x12\"\n\x1dPROTO_OA_DEAL_OFFSET_LIST_REQ\x10\x89\x11\x12\"\n\x1dPROTO_OA_DEAL_OFFSET_LIST_RES\x10\x8a\x11\x12-\n(PROTO_OA_GET_POSITION_UNREALIZED_PNL_REQ\x10\x8b\x11\x12-\n(PROTO_OA_GET_POSITION_UNREALIZED_PNL_RES\x10\x8c\x11*x\n\x10ProtoOADayOfWeek\x12\x08\n\x04NONE\x10\x00\x12\n\n\x06MONDAY\x10\x01\x12\x0b\n\x07TUESDAY\x10\x02\x12\r\n\tWEDNESDAY\x10\x03\x12\x0c\n\x08THURSDAY\x10\x04\x12\n\n\x06\x46RIDAY\x10\x05\x12\x0c\n\x08SATURDAY\x10\x06\x12\n\n\x06SUNDAY\x10\x07*q\n\x15ProtoOACommissionType\x12\x17\n\x13USD_PER_MILLION_USD\x10\x01\x12\x0f\n\x0bUSD_PER_LOT\x10\x02\x12\x17\n\x13PERCENTAGE_OF_VALUE\x10\x03\x12\x15\n\x11QUOTE_CCY_PER_LOT\x10\x04*]\n\x19ProtoOASymbolDistanceType\x12\x1d\n\x19SYMBOL_DISTANCE_IN_POINTS\x10\x01\x12!\n\x1dSYMBOL_DISTANCE_IN_PERCENTAGE\x10\x02*<\n\x18ProtoOAMinCommissionType\x12\x0c\n\x08\x43URRENCY\x10\x01\x12\x12\n\x0eQUOTE_CURRENCY\x10\x02*\x85\x01\n\x12ProtoOATradingMode\x12\x0b\n\x07\x45NABLED\x10\x00\x12\'\n#DISABLED_WITHOUT_PENDINGS_EXECUTION\x10\x01\x12$\n DISABLED_WITH_PENDINGS_EXECUTION\x10\x02\x12\x13\n\x0f\x43LOSE_ONLY_MODE\x10\x03*6\n\x1aProtoOASwapCalculationType\x12\x08\n\x04PIPS\x10\x00\x12\x0e\n\nPERCENTAGE\x10\x01*T\n\x13ProtoOAAccessRights\x12\x0f\n\x0b\x46ULL_ACCESS\x10\x00\x12\x0e\n\nCLOSE_ONLY\x10\x01\x12\x0e\n\nNO_TRADING\x10\x02\x12\x0c\n\x08NO_LOGIN\x10\x03*>\n!ProtoOATotalMarginCalculationType\x12\x07\n\x03MAX\x10\x00\x12\x07\n\x03SUM\x10\x01\x12\x07\n\x03NET\x10\x02*@\n\x12ProtoOAAccountType\x12\n\n\x06HEDGED\x10\x00\x12\n\n\x06NETTED\x10\x01\x12\x12\n\x0eSPREAD_BETTING\x10\x02*\x85\x01\n\x15ProtoOAPositionStatus\x12\x18\n\x14POSITION_STATUS_OPEN\x10\x01\x12\x1a\n\x16POSITION_STATUS_CLOSED\x10\x02\x12\x1b\n\x17POSITION_STATUS_CREATED\x10\x03\x12\x19\n\x15POSITION_STATUS_ERROR\x10\x04*%\n\x10ProtoOATradeSide\x12\x07\n\x03\x42UY\x10\x01\x12\x08\n\x04SELL\x10\x02*p\n\x10ProtoOAOrderType\x12\n\n\x06MARKET\x10\x01\x12\t\n\x05LIMIT\x10\x02\x12\x08\n\x04STOP\x10\x03\x12\x19\n\x15STOP_LOSS_TAKE_PROFIT\x10\x04\x12\x10\n\x0cMARKET_RANGE\x10\x05\x12\x0e\n\nSTOP_LIMIT\x10\x06*}\n\x12ProtoOATimeInForce\x12\x12\n\x0eGOOD_TILL_DATE\x10\x01\x12\x14\n\x10GOOD_TILL_CANCEL\x10\x02\x12\x17\n\x13IMMEDIATE_OR_CANCEL\x10\x03\x12\x10\n\x0c\x46ILL_OR_KILL\x10\x04\x12\x12\n\x0eMARKET_ON_OPEN\x10\x05*\x99\x01\n\x12ProtoOAOrderStatus\x12\x19\n\x15ORDER_STATUS_ACCEPTED\x10\x01\x12\x17\n\x13ORDER_STATUS_FILLED\x10\x02\x12\x19\n\x15ORDER_STATUS_REJECTED\x10\x03\x12\x18\n\x14ORDER_STATUS_EXPIRED\x10\x04\x12\x1a\n\x16ORDER_STATUS_CANCELLED\x10\x05*[\n\x19ProtoOAOrderTriggerMethod\x12\t\n\x05TRADE\x10\x01\x12\x0c\n\x08OPPOSITE\x10\x02\x12\x10\n\x0c\x44OUBLE_TRADE\x10\x03\x12\x13\n\x0f\x44OUBLE_OPPOSITE\x10\x04*\xfb\x01\n\x14ProtoOAExecutionType\x12\x12\n\x0eORDER_ACCEPTED\x10\x02\x12\x10\n\x0cORDER_FILLED\x10\x03\x12\x12\n\x0eORDER_REPLACED\x10\x04\x12\x13\n\x0fORDER_CANCELLED\x10\x05\x12\x11\n\rORDER_EXPIRED\x10\x06\x12\x12\n\x0eORDER_REJECTED\x10\x07\x12\x19\n\x15ORDER_CANCEL_REJECTED\x10\x08\x12\x08\n\x04SWAP\x10\t\x12\x14\n\x10\x44\x45POSIT_WITHDRAW\x10\n\x12\x16\n\x12ORDER_PARTIAL_FILL\x10\x0b\x12\x1a\n\x16\x42ONUS_DEPOSIT_WITHDRAW\x10\x0c*?\n\x16ProtoOAChangeBonusType\x12\x11\n\rBONUS_DEPOSIT\x10\x00\x12\x12\n\x0e\x42ONUS_WITHDRAW\x10\x01*\xb8\n\n\x18ProtoOAChangeBalanceType\x12\x13\n\x0f\x42\x41LANCE_DEPOSIT\x10\x00\x12\x14\n\x10\x42\x41LANCE_WITHDRAW\x10\x01\x12-\n)BALANCE_DEPOSIT_STRATEGY_COMMISSION_INNER\x10\x03\x12.\n*BALANCE_WITHDRAW_STRATEGY_COMMISSION_INNER\x10\x04\x12\"\n\x1e\x42\x41LANCE_DEPOSIT_IB_COMMISSIONS\x10\x05\x12)\n%BALANCE_WITHDRAW_IB_SHARED_PERCENTAGE\x10\x06\x12\x34\n0BALANCE_DEPOSIT_IB_SHARED_PERCENTAGE_FROM_SUB_IB\x10\x07\x12\x34\n0BALANCE_DEPOSIT_IB_SHARED_PERCENTAGE_FROM_BROKER\x10\x08\x12\x1a\n\x16\x42\x41LANCE_DEPOSIT_REBATE\x10\t\x12\x1b\n\x17\x42\x41LANCE_WITHDRAW_REBATE\x10\n\x12-\n)BALANCE_DEPOSIT_STRATEGY_COMMISSION_OUTER\x10\x0b\x12.\n*BALANCE_WITHDRAW_STRATEGY_COMMISSION_OUTER\x10\x0c\x12\'\n#BALANCE_WITHDRAW_BONUS_COMPENSATION\x10\r\x12\x33\n/BALANCE_WITHDRAW_IB_SHARED_PERCENTAGE_TO_BROKER\x10\x0e\x12\x1d\n\x19\x42\x41LANCE_DEPOSIT_DIVIDENDS\x10\x0f\x12\x1e\n\x1a\x42\x41LANCE_WITHDRAW_DIVIDENDS\x10\x10\x12\x1f\n\x1b\x42\x41LANCE_WITHDRAW_GSL_CHARGE\x10\x11\x12\x1d\n\x19\x42\x41LANCE_WITHDRAW_ROLLOVER\x10\x12\x12)\n%BALANCE_DEPOSIT_NONWITHDRAWABLE_BONUS\x10\x13\x12*\n&BALANCE_WITHDRAW_NONWITHDRAWABLE_BONUS\x10\x14\x12\x18\n\x14\x42\x41LANCE_DEPOSIT_SWAP\x10\x15\x12\x19\n\x15\x42\x41LANCE_WITHDRAW_SWAP\x10\x16\x12\"\n\x1e\x42\x41LANCE_DEPOSIT_MANAGEMENT_FEE\x10\x1b\x12#\n\x1f\x42\x41LANCE_WITHDRAW_MANAGEMENT_FEE\x10\x1c\x12#\n\x1f\x42\x41LANCE_DEPOSIT_PERFORMANCE_FEE\x10\x1d\x12#\n\x1f\x42\x41LANCE_WITHDRAW_FOR_SUBACCOUNT\x10\x1e\x12!\n\x1d\x42\x41LANCE_DEPOSIT_TO_SUBACCOUNT\x10\x1f\x12$\n BALANCE_WITHDRAW_FROM_SUBACCOUNT\x10 \x12#\n\x1f\x42\x41LANCE_DEPOSIT_FROM_SUBACCOUNT\x10!\x12\x1d\n\x19\x42\x41LANCE_WITHDRAW_COPY_FEE\x10\"\x12#\n\x1f\x42\x41LANCE_WITHDRAW_INACTIVITY_FEE\x10#\x12\x1c\n\x18\x42\x41LANCE_DEPOSIT_TRANSFER\x10$\x12\x1d\n\x19\x42\x41LANCE_WITHDRAW_TRANSFER\x10%\x12#\n\x1f\x42\x41LANCE_DEPOSIT_CONVERTED_BONUS\x10&\x12/\n+BALANCE_DEPOSIT_NEGATIVE_BALANCE_PROTECTION\x10\'*s\n\x11ProtoOADealStatus\x12\n\n\x06\x46ILLED\x10\x02\x12\x14\n\x10PARTIALLY_FILLED\x10\x03\x12\x0c\n\x08REJECTED\x10\x04\x12\x17\n\x13INTERNALLY_REJECTED\x10\x05\x12\t\n\x05\x45RROR\x10\x06\x12\n\n\x06MISSED\x10\x07*\x8c\x01\n\x15ProtoOATrendbarPeriod\x12\x06\n\x02M1\x10\x01\x12\x06\n\x02M2\x10\x02\x12\x06\n\x02M3\x10\x03\x12\x06\n\x02M4\x10\x04\x12\x06\n\x02M5\x10\x05\x12\x07\n\x03M10\x10\x06\x12\x07\n\x03M15\x10\x07\x12\x07\n\x03M30\x10\x08\x12\x06\n\x02H1\x10\t\x12\x06\n\x02H4\x10\n\x12\x07\n\x03H12\x10\x0b\x12\x06\n\x02\x44\x31\x10\x0c\x12\x06\n\x02W1\x10\r\x12\x07\n\x03MN1\x10\x0e*$\n\x10ProtoOAQuoteType\x12\x07\n\x03\x42ID\x10\x01\x12\x07\n\x03\x41SK\x10\x02*?\n\x1cProtoOAClientPermissionScope\x12\x0e\n\nSCOPE_VIEW\x10\x00\x12\x0f\n\x0bSCOPE_TRADE\x10\x01*s\n\x17ProtoOANotificationType\x12\x1c\n\x18MARGIN_LEVEL_THRESHOLD_1\x10=\x12\x1c\n\x18MARGIN_LEVEL_THRESHOLD_2\x10>\x12\x1c\n\x18MARGIN_LEVEL_THRESHOLD_3\x10?*\xde\x08\n\x10ProtoOAErrorCode\x12\x19\n\x15OA_AUTH_TOKEN_EXPIRED\x10\x01\x12\x1a\n\x16\x41\x43\x43OUNT_NOT_AUTHORIZED\x10\x02\x12\x15\n\x11\x41LREADY_LOGGED_IN\x10\x0e\x12\x1a\n\x16\x43H_CLIENT_AUTH_FAILURE\x10\x65\x12\x1f\n\x1b\x43H_CLIENT_NOT_AUTHENTICATED\x10\x66\x12#\n\x1f\x43H_CLIENT_ALREADY_AUTHENTICATED\x10g\x12\x1b\n\x17\x43H_ACCESS_TOKEN_INVALID\x10h\x12\x1b\n\x17\x43H_SERVER_NOT_REACHABLE\x10i\x12$\n CH_CTID_TRADER_ACCOUNT_NOT_FOUND\x10j\x12\x1a\n\x16\x43H_OA_CLIENT_NOT_FOUND\x10k\x12\x1e\n\x1aREQUEST_FREQUENCY_EXCEEDED\x10l\x12\x1f\n\x1bSERVER_IS_UNDER_MAINTENANCE\x10m\x12\x16\n\x12\x43HANNEL_IS_BLOCKED\x10n\x12\x1e\n\x1a\x43ONNECTIONS_LIMIT_EXCEEDED\x10\x43\x12\x19\n\x15WORSE_GSL_NOT_ALLOWED\x10\x44\x12\x16\n\x12SYMBOL_HAS_HOLIDAY\x10\x45\x12\x1b\n\x17NOT_SUBSCRIBED_TO_SPOTS\x10p\x12\x16\n\x12\x41LREADY_SUBSCRIBED\x10q\x12\x14\n\x10SYMBOL_NOT_FOUND\x10r\x12\x12\n\x0eUNKNOWN_SYMBOL\x10s\x12\x18\n\x14INCORRECT_BOUNDARIES\x10#\x12\r\n\tNO_QUOTES\x10u\x12\x14\n\x10NOT_ENOUGH_MONEY\x10v\x12\x18\n\x14MAX_EXPOSURE_REACHED\x10w\x12\x16\n\x12POSITION_NOT_FOUND\x10x\x12\x13\n\x0fORDER_NOT_FOUND\x10y\x12\x15\n\x11POSITION_NOT_OPEN\x10z\x12\x13\n\x0fPOSITION_LOCKED\x10{\x12\x16\n\x12TOO_MANY_POSITIONS\x10|\x12\x16\n\x12TRADING_BAD_VOLUME\x10}\x12\x15\n\x11TRADING_BAD_STOPS\x10~\x12\x16\n\x12TRADING_BAD_PRICES\x10\x7f\x12\x16\n\x11TRADING_BAD_STAKE\x10\x80\x01\x12&\n!PROTECTION_IS_TOO_CLOSE_TO_MARKET\x10\x81\x01\x12 \n\x1bTRADING_BAD_EXPIRATION_DATE\x10\x82\x01\x12\x16\n\x11PENDING_EXECUTION\x10\x83\x01\x12\x15\n\x10TRADING_DISABLED\x10\x84\x01\x12\x18\n\x13TRADING_NOT_ALLOWED\x10\x85\x01\x12\x1b\n\x16UNABLE_TO_CANCEL_ORDER\x10\x86\x01\x12\x1a\n\x15UNABLE_TO_AMEND_ORDER\x10\x87\x01\x12\x1e\n\x19SHORT_SELLING_NOT_ALLOWED\x10\x88\x01*\x81\x01\n+ProtoOALimitedRiskMarginCalculationStrategy\x12\x19\n\x15\x41\x43\x43ORDING_TO_LEVERAGE\x10\x00\x12\x14\n\x10\x41\x43\x43ORDING_TO_GSL\x10\x01\x12!\n\x1d\x41\x43\x43ORDING_TO_GSL_AND_LEVERAGE\x10\x02\x42M\n%com.xtrader.protocol.openapi.v2.modelB\x1f\x43ontainerOpenApiV2ModelMessagesP\x01\xa0\x01\x01')

_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, globals())
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'OpenApiModelMessages_pb2', globals())
if _descriptor._USE_C_DESCRIPTORS == False:

  DESCRIPTOR._options = None
  DESCRIPTOR._serialized_options = b'\n%com.xtrader.protocol.openapi.v2.modelB\037ContainerOpenApiV2ModelMessagesP\001\240\001\001'
  _PROTOOASYMBOL.fields_by_name['commission']._options = None
  _PROTOOASYMBOL.fields_by_name['commission']._serialized_options = b'\030\001'
  _PROTOOASYMBOL.fields_by_name['minCommission']._options = None
  _PROTOOASYMBOL.fields_by_name['minCommission']._serialized_options = b'\030\001'
  _PROTOOATRADER.fields_by_name['frenchRisk']._options = None
  _PROTOOATRADER.fields_by_name['frenchRisk']._serialized_options = b'\030\001'
  _PROTOOAPAYLOADTYPE._serialized_start=6100
  _PROTOOAPAYLOADTYPE._serialized_end=9349
  _PROTOOADAYOFWEEK._serialized_start=9351
  _PROTOOADAYOFWEEK._serialized_end=9471
  _PROTOOACOMMISSIONTYPE._serialized_start=9473
  _PROTOOACOMMISSIONTYPE._serialized_end=9586
  _PROTOOASYMBOLDISTANCETYPE._serialized_start=9588
  _PROTOOASYMBOLDISTANCETYPE._serialized_end=9681
  _PROTOOAMINCOMMISSIONTYPE._serialized_start=9683
  _PROTOOAMINCOMMISSIONTYPE._serialized_end=9743
  _PROTOOATRADINGMODE._serialized_start=9746
  _PROTOOATRADINGMODE._serialized_end=9879
  _PROTOOASWAPCALCULATIONTYPE._serialized_start=9881
  _PROTOOASWAPCALCULATIONTYPE._serialized_end=9935
  _PROTOOAACCESSRIGHTS._serialized_start=9937
  _PROTOOAACCESSRIGHTS._serialized_end=10021
  _PROTOOATOTALMARGINCALCULATIONTYPE._serialized_start=10023
  _PROTOOATOTALMARGINCALCULATIONTYPE._serialized_end=10085
  _PROTOOAACCOUNTTYPE._serialized_start=10087
  _PROTOOAACCOUNTTYPE._serialized_end=10151
  _PROTOOAPOSITIONSTATUS._serialized_start=10154
  _PROTOOAPOSITIONSTATUS._serialized_end=10287
  _PROTOOATRADESIDE._serialized_start=10289
  _PROTOOATRADESIDE._serialized_end=10326
  _PROTOOAORDERTYPE._serialized_start=10328
  _PROTOOAORDERTYPE._serialized_end=10440
  _PROTOOATIMEINFORCE._serialized_start=10442
  _PROTOOATIMEINFORCE._serialized_end=10567
  _PROTOOAORDERSTATUS._serialized_start=10570
  _PROTOOAORDERSTATUS._serialized_end=10723
  _PROTOOAORDERTRIGGERMETHOD._serialized_start=10725
  _PROTOOAORDERTRIGGERMETHOD._serialized_end=10816
  _PROTOOAEXECUTIONTYPE._serialized_start=10819
  _PROTOOAEXECUTIONTYPE._serialized_end=11070
  _PROTOOACHANGEBONUSTYPE._serialized_start=11072
  _PROTOOACHANGEBONUSTYPE._serialized_end=11135
  _PROTOOACHANGEBALANCETYPE._serialized_start=11138
  _PROTOOACHANGEBALANCETYPE._serialized_end=12474
  _PROTOOADEALSTATUS._serialized_start=12476
  _PROTOOADEALSTATUS._serialized_end=12591
  _PROTOOATRENDBARPERIOD._serialized_start=12594
  _PROTOOATRENDBARPERIOD._serialized_end=12734
  _PROTOOAQUOTETYPE._serialized_start=12736
  _PROTOOAQUOTETYPE._serialized_end=12772
  _PROTOOACLIENTPERMISSIONSCOPE._serialized_start=12774
  _PROTOOACLIENTPERMISSIONSCOPE._serialized_end=12837
  _PROTOOANOTIFICATIONTYPE._serialized_start=12839
  _PROTOOANOTIFICATIONTYPE._serialized_end=12954
  _PROTOOAERRORCODE._serialized_start=12957
  _PROTOOAERRORCODE._serialized_end=14075
  _PROTOOALIMITEDRISKMARGINCALCULATIONSTRATEGY._serialized_start=14078
  _PROTOOALIMITEDRISKMARGINCALCULATIONSTRATEGY._serialized_end=14207
  _PROTOOAASSET._serialized_start=30
  _PROTOOAASSET._serialized_end=112
  _PROTOOASYMBOL._serialized_start=115
  _PROTOOASYMBOL._serialized_end=1339
  _PROTOOALIGHTSYMBOL._serialized_start=1342
  _PROTOOALIGHTSYMBOL._serialized_end=1507
  _PROTOOAARCHIVEDSYMBOL._serialized_start=1509
  _PROTOOAARCHIVEDSYMBOL._serialized_end=1617
  _PROTOOASYMBOLCATEGORY._serialized_start=1619
  _PROTOOASYMBOLCATEGORY._serialized_end=1690
  _PROTOOAINTERVAL._serialized_start=1692
  _PROTOOAINTERVAL._serialized_end=1749
  _PROTOOATRADER._serialized_start=1752
  _PROTOOATRADER._serialized_end=2428
  _PROTOOAPOSITION._serialized_start=2431
  _PROTOOAPOSITION._serialized_end=2883
  _PROTOOATRADEDATA._serialized_start=2886
  _PROTOOATRADEDATA._serialized_end=3059
  _PROTOOAORDER._serialized_start=3062
  _PROTOOAORDER._serialized_end=3739
  _PROTOOABONUSDEPOSITWITHDRAW._serialized_start=3742
  _PROTOOABONUSDEPOSITWITHDRAW._serialized_end=4023
  _PROTOOADEPOSITWITHDRAW._serialized_start=4026
  _PROTOOADEPOSITWITHDRAW._serialized_end=4273
  _PROTOOADEAL._serialized_start=4276
  _PROTOOADEAL._serialized_end=4737
  _PROTOOACLOSEPOSITIONDETAIL._serialized_start=4740
  _PROTOOACLOSEPOSITIONDETAIL._serialized_end=4991
  _PROTOOATRENDBAR._serialized_start=4994
  _PROTOOATRENDBAR._serialized_end=5173
  _PROTOOAEXPECTEDMARGIN._serialized_start=5175
  _PROTOOAEXPECTEDMARGIN._serialized_end=5253
  _PROTOOATICKDATA._serialized_start=5255
  _PROTOOATICKDATA._serialized_end=5305
  _PROTOOACTIDPROFILE._serialized_start=5307
  _PROTOOACTIDPROFILE._serialized_end=5343
  _PROTOOACTIDTRADERACCOUNT._serialized_start=5346
  _PROTOOACTIDTRADERACCOUNT._serialized_end=5508
  _PROTOOAASSETCLASS._serialized_start=5510
  _PROTOOAASSETCLASS._serialized_end=5555
  _PROTOOADEPTHQUOTE._serialized_start=5557
  _PROTOOADEPTHQUOTE._serialized_end=5628
  _PROTOOAMARGINCALL._serialized_start=5631
  _PROTOOAMARGINCALL._serialized_end=5762
  _PROTOOAHOLIDAY._serialized_start=5765
  _PROTOOAHOLIDAY._serialized_end=5943
  _PROTOOADYNAMICLEVERAGE._serialized_start=5945
  _PROTOOADYNAMICLEVERAGE._serialized_end=6033
  _PROTOOADYNAMICLEVERAGETIER._serialized_start=6035
  _PROTOOADYNAMICLEVERAGETIER._serialized_end=6097
# @@protoc_insertion_point(module_scope)
````

## File: ctrader_open_api/__init__.py
````python
"""Top-level package for Spotware OpenApiPy."""
from .client import Client
from .protobuf import Protobuf
from .tcpProtocol import TcpProtocol
from .auth import Auth
from .endpoints import EndPoints
__author__ = """Spotware"""
__email__ = 'connect@spotware.com'
````

## File: ctrader_open_api/auth.py
````python
from ctrader_open_api.endpoints import EndPoints
import requests

class Auth:
    def __init__(self, appClientId, appClientSecret, redirectUri):
        self.appClientId = appClientId
        self.appClientSecret = appClientSecret
        self.redirectUri = redirectUri
    def getAuthUri(self, scope = "trading", baseUri = EndPoints.AUTH_URI):
        return f"{baseUri}?client_id={self.appClientId}&redirect_uri={self.redirectUri}&scope={scope}"
    def getToken(self, authCode, baseUri = EndPoints.TOKEN_URI):
        request = requests.get(baseUri, params=
                               {"grant_type": "authorization_code",
                               "code": authCode,
                              "redirect_uri": self.redirectUri,
                             "client_id": self.appClientId,
                            "client_secret": self.appClientSecret})
        return request.json()
    def refreshToken(self, refreshToken, baseUri = EndPoints.TOKEN_URI):
        request = requests.get(baseUri, params=
                               {"grant_type": "refresh_token",
                               "refresh_token": refreshToken,
                             "client_id": self.appClientId,
                            "client_secret": self.appClientSecret})
        return request.json()
````

## File: ctrader_open_api/client.py
````python
#!/usr/bin/env python

from twisted.internet.endpoints import clientFromString
from twisted.application.internet import ClientService
from ctrader_open_api.protobuf import Protobuf
from ctrader_open_api.factory import Factory
from twisted.internet import reactor, defer

class Client(ClientService):
    def __init__(self, host, port, protocol, retryPolicy=None, clock=None, prepareConnection=None, numberOfMessagesToSendPerSecond=5):
        self._runningReactor = reactor
        self.numberOfMessagesToSendPerSecond = numberOfMessagesToSendPerSecond
        endpoint = clientFromString(self._runningReactor, f"ssl:{host}:{port}")
        factory = Factory.forProtocol(protocol, client=self)
        super().__init__(endpoint, factory, retryPolicy=retryPolicy, clock=clock, prepareConnection=prepareConnection)
        self._events = dict()
        self._responseDeferreds = dict()
        self.isConnected = False

    def startService(self):
        if self.running:
            return
        ClientService.startService(self)

    def stopService(self):
        if self.running and self.isConnected:
            ClientService.stopService(self)

    def _connected(self, protocol):
        self.isConnected = True
        if hasattr(self, "_connectedCallback"):
            self._connectedCallback(self)

    def _disconnected(self, reason):
        self.isConnected = False
        self._responseDeferreds.clear()
        if hasattr(self, "_disconnectedCallback"):
            self._disconnectedCallback(self, reason)

    def _received(self, message):
        if hasattr(self, "_messageReceivedCallback"):
            self._messageReceivedCallback(self, message)
        if (message.clientMsgId is not None and message.clientMsgId in self._responseDeferreds):
            responseDeferred = self._responseDeferreds[message.clientMsgId]
            self._responseDeferreds.pop(message.clientMsgId)
            responseDeferred.callback(message)

    def send(self, message, clientMsgId=None, responseTimeoutInSeconds=5, **params):
        if type(message) in [str, int]:
            message = Protobuf.get(message, **params)
        responseDeferred = defer.Deferred(self._cancelMessageDiferred)
        if clientMsgId is None:
            clientMsgId = str(id(responseDeferred))
        if clientMsgId is not None:
            self._responseDeferreds[clientMsgId] = responseDeferred
        responseDeferred.addErrback(lambda failure: self._onResponseFailure(failure, clientMsgId))
        responseDeferred.addTimeout(responseTimeoutInSeconds, self._runningReactor)
        protocolDiferred = self.whenConnected(failAfterFailures=1)       
        protocolDiferred.addCallbacks(lambda protocol: protocol.send(message, clientMsgId=clientMsgId, isCanceled=lambda: clientMsgId not in self._responseDeferreds), responseDeferred.errback)
        return responseDeferred

    def setConnectedCallback(self, callback):
        self._connectedCallback = callback

    def setDisconnectedCallback(self, callback):
        self._disconnectedCallback = callback

    def setMessageReceivedCallback(self, callback):
        self._messageReceivedCallback = callback

    def _onResponseFailure(self, failure, msgId):
        if (msgId is not None and msgId in self._responseDeferreds):
            self._responseDeferreds.pop(msgId)
        return failure

    def _cancelMessageDiferred(self, deferred):
        deferredIdString = str(id(deferred))
        if (deferredIdString in self._responseDeferreds):
            self._responseDeferreds.pop(deferredIdString)
````

## File: ctrader_open_api/endpoints.py
````python
class EndPoints:
    AUTH_URI = "https://openapi.ctrader.com/apps/auth"
    TOKEN_URI = "https://openapi.ctrader.com/apps/token"
    PROTOBUF_DEMO_HOST = "demo.ctraderapi.com"
    PROTOBUF_LIVE_HOST = "live.ctraderapi.com"
    PROTOBUF_PORT = 5035
````

## File: ctrader_open_api/factory.py
````python
#!/usr/bin/env python

from twisted.internet.protocol import ClientFactory

class Factory(ClientFactory):
    def __init__(self, *args, **kwargs):
        super().__init__()
        self.client = kwargs['client']
        self.numberOfMessagesToSendPerSecond = self.client.numberOfMessagesToSendPerSecond
    def connected(self, protocol):
        self.client._connected(protocol)
    def disconnected(self, reason):
        self.client._disconnected(reason)
    def received(self, message):
        self.client._received(message)
````

## File: ctrader_open_api/protobuf.py
````python
#!/usr/bin/env python

class Protobuf(object):
    _protos = dict()
    _names = dict()
    _abbr_names = dict()

    @classmethod
    def populate(cls):
        import re
        from .messages import OpenApiCommonMessages_pb2 as o1
        from .messages import OpenApiMessages_pb2 as o2

        for name in dir(o1) + dir(o2):
            if not name.startswith("Proto"):
                continue

            m = o1 if hasattr(o1, name) else o2
            klass = getattr(m, name)
            cls._protos[klass().payloadType] = klass
            cls._names[klass.__name__] = klass().payloadType
            abbr_name = re.sub(r'^Proto(OA)?(.*)', r'\2', klass.__name__)
            cls._names[abbr_name] = klass().payloadType
        return cls._protos

    @classmethod
    def get(cls, payload, fail=True, **params):
        if not cls._protos:
            cls.populate()

        if payload in cls._protos:
            return cls._protos[payload](**params)

        for d in [cls._names, cls._abbr_names]:
            if payload in d:
                payload = d[payload]
                return cls._protos[payload](**params)
        if fail:  # pragma: nocover
            raise IndexError("Invalid payload: " + str(payload))
        return None  # pragma: nocover

    @classmethod
    def get_type(cls, payload, **params):
        p = cls.get(payload, **params)
        return p.payloadType

    @classmethod
    def extract(cls, message):
        payload = cls.get(message.payloadType)
        payload.ParseFromString(message.payload)
        return payload
````

## File: ctrader_open_api/tcpProtocol.py
````python
#!/usr/bin/env python

from collections import deque
from twisted.protocols.basic import Int32StringReceiver
from twisted.internet import task
from ctrader_open_api.messages.OpenApiCommonMessages_pb2 import ProtoMessage, ProtoHeartbeatEvent
import datetime

class TcpProtocol(Int32StringReceiver):
    MAX_LENGTH = 15000000
    _send_queue = deque([])
    _send_task = None
    _lastSendMessageTime = None

    def connectionMade(self):
        super().connectionMade()

        if not self._send_task:
            self._send_task = task.LoopingCall(self._sendStrings)
        self._send_task.start(1)
        self.factory.connected(self)

    def connectionLost(self, reason):
        super().connectionLost(reason)
        if self._send_task.running:
            self._send_task.stop()
        self.factory.disconnected(reason)

    def heartbeat(self):
        self.send(ProtoHeartbeatEvent(), True)

    def send(self, message, instant=False, clientMsgId=None, isCanceled = None):
        data = b''

        if isinstance(message, ProtoMessage):
            data = message.SerializeToString()

        if isinstance(message, bytes):
            data = message

        if isinstance(message, ProtoMessage.__base__):
            msg = ProtoMessage(payload=message.SerializeToString(),
                               clientMsgId=clientMsgId,
                               payloadType=message.payloadType)
            data = msg.SerializeToString()

        if instant:
            self.sendString(data)
            self._lastSendMessageTime = datetime.datetime.now()
        else:
            self._send_queue.append((isCanceled, data))

    def _sendStrings(self):
        size = len(self._send_queue)

        if not size:
            if self._lastSendMessageTime is None or (datetime.datetime.now() - self._lastSendMessageTime).total_seconds() > 20:
                self.heartbeat()
            return

        for _ in range(min(size, self.factory.numberOfMessagesToSendPerSecond)):
            isCanceled, data = self._send_queue.popleft()
            if isCanceled is not None and isCanceled():
                continue;
            self.sendString(data)
        self._lastSendMessageTime = datetime.datetime.now()

    def stringReceived(self, data):
        msg = ProtoMessage()
        msg.ParseFromString(data)

        if msg.payloadType == ProtoHeartbeatEvent().payloadType:
            self.heartbeat()
        self.factory.received(msg)
        return data
````

## File: docs/css/extra.css
````css
@font-face {
    font-family: "TitilliumWeb-Regular";
    src: url(../fonts/TitilliumWeb-Regular.ttf);
}

@font-face {
    font-family: "TitilliumWeb-SemiBold";
    src: url(../fonts/TitilliumWeb-SemiBold.ttf);
}

h1 {
    font-family: "TitilliumWeb-SemiBold";
}

h2 {
    font-family: "TitilliumWeb-SemiBold";
}

:root > * {
    --md-primary-fg-color: #292929;
    --md-primary-fg-color--light: #292929;
    --md-primary-fg-color--dark: #3C3C3C;
    --md-primary-bg-color: hsla(0, 0%, 100%, 1);
    --md-primary-bg-color--light: hsla(0, 0%, 100%, 0.7);
    --md-typeset-a-color: #009345;
    --md-text-font: "TitilliumWeb-Regular";
}

[data-md-color-scheme="slate"] {
    --md-hue: 232;
    --md-default-fg-color: hsla(var(--md-hue),75%,95%,1);
    --md-default-fg-color--light: hsla(var(--md-hue),75%,90%,0.62);
    --md-default-fg-color--lighter: hsla(var(--md-hue),75%,90%,0.32);
    --md-default-fg-color--lightest: hsla(var(--md-hue),75%,90%,0.12);
    --md-default-bg-color: hsl(0, 0%, 24%);
    --md-default-bg-color--light: hsla(var(--md-hue),15%,21%,0.54);
    --md-default-bg-color--lighter: hsla(var(--md-hue),15%,21%,0.26);
    --md-default-bg-color--lightest: hsla(var(--md-hue),15%,21%,0.07);
    --md-code-fg-color: hsla(var(--md-hue),18%,86%,1);
    --md-code-bg-color: hsla(var(--md-hue),15%,15%,1);
    --md-code-hl-color: rgba(66,135,255,.15);
    --md-code-hl-number-color: #e6695b;
    --md-code-hl-special-color: #f06090;
    --md-code-hl-function-color: #c973d9;
    --md-code-hl-constant-color: #9383e2;
    --md-code-hl-keyword-color: #6791e0;
    --md-code-hl-string-color: #2fb170;
    --md-code-hl-name-color: var(--md-code-fg-color);
    --md-code-hl-operator-color: var(--md-default-fg-color--light);
    --md-code-hl-punctuation-color: var(--md-default-fg-color--light);
    --md-code-hl-comment-color: var(--md-default-fg-color--light);
    --md-code-hl-generic-color: var(--md-default-fg-color--light);
    --md-code-hl-variable-color: var(--md-default-fg-color--light);
    --md-typeset-color: var(--md-default-fg-color);
    --md-typeset-a-color: #009345;
    --md-typeset-mark-color: rgba(66,135,255,.3);
    --md-typeset-kbd-color: hsla(var(--md-hue),15%,94%,0.12);
    --md-typeset-kbd-accent-color: hsla(var(--md-hue),15%,94%,0.2);
    --md-typeset-kbd-border-color: hsla(var(--md-hue),15%,14%,1);
    --md-typeset-table-color: hsla(var(--md-hue),75%,95%,0.12);
    --md-admonition-bg-color: hsla(var(--md-hue),0%,100%,0.025);
    --md-footer-bg-color: #292929;
    --md-footer-bg-color--dark: #3C3C3C;
    
}
````

## File: docs/js/extra.js
````javascript
document.addEventListener("scroll", function (event) {
    copyrightYear = document.querySelector('#copyright-year');
    copyrightYear.innerText = new Date().getUTCFullYear();
});
````

## File: docs/authentication.md
````markdown
### Auth Class

For authentication you can use the package Auth class, first create an instance of it:

```python
from ctrader_open_api import Auth

auth = Auth("Your App ID", "Your App Secret", "Your App redirect URI")
```

### Auth URI

The first step for authentication is sending user to the cTrader Open API authentication web page, there the user will give access to your API application to manage the user trading accounts on behalf of him.

To get the cTrader Open API authentication web page URL you can use the Auth class getAuthUri method:

```python
authUri = auth.getAuthUri()
```
The getAuthUri has two optional parameters:

* scope: Allows you to set the scope of authentication, the default value is trading which means you will have full access to user trading accounts, if you want to just have access to user trading account data then use accounts

* baseUri: The base URI for authentication, the default value is EndPoints.AUTH_URI which is https://connect.spotware.com/apps/auth

### Getting Token

After user authenticated your Application he will be redirected to your provided redirect URI with an authentication code appended at the end of your redirect URI:

```
https://redirect-uri.com/?code={authorization-code-will-be-here}
```

You can use this authentication code to get an access token from API, for that you can use the Auth class getToken method:

```python
# This method uses EndPoints.TOKEN_URI as a base URI to get token
# you can change it by passing another URI via optional baseUri parameter
token = auth.getToken("auth_code")
```

Pass the received auth code to getToken method and it will give you a token JSON object, the object will have these properties:

* accessToken: This is the access token that you will use for authentication

* refreshToken: This is the token that you will use for refreshing the accessToken onces it expired

* expiresIn: The expiry of token in seconds from the time it generated

* tokenType: The type of token, standard OAuth token type parameter (bearer)

* errorCode: This will have the error code if something went wrong

* description: The error description

### Refreshing Token

API access tokens have an expiry time, you can only use it until that time and once it expired you have to refresh it by using the refresh token you received previously.

To refresh an access token you can use the Auth class refreshToken method:

```python
# This method uses EndPoints.TOKEN_URI as a base URI to refresh token
# you can change it by passing another URI via optional baseUri parameter
newToken = auth.refreshToken("refresh_Token")
```

You have to pass the refresh token to "refreshToken" method, and it will return a new token JSON object which will have all the previously mentioned token properties.

You can always refresh a token, even before it expires and the refresh token has no expiry, but you can only use it once.
````

## File: docs/client.md
````markdown
### Client Class

You will use an instance of this class to interact with API.

Each instance of this class will have one connection to API, either live or demo endpoint.

The client class is driven from Twisted ClientService class, and it abstracts away all the connection / reconnection complexities from you.

### Creating a Client

Let's create an isntance of Client class:

```python

from ctrader_open_api import Client, Protobuf, TcpProtocol, Auth, EndPoints

client = Client(EndPoints.PROTOBUF_DEMO_HOST, EndPoints.PROTOBUF_PORT, TcpProtocol)

```

It's constructor has several parameters that you can use for controling it behavior:

* host: The API host endpoint, you can use either EndPoints.PROTOBUF_DEMO_HOST or EndPoints.PROTOBUF_LIVE_HOST

* port: The API host port number, you can use EndPoints.PROTOBUF_PORT

* protocol: The protocol that will be used by client for making connections, use imported TcpProtocol

* numberOfMessagesToSendPerSecond: This is the number of messages that will be sent to API per second, set it based on API limitations or leave the default value

There are three other optional parameters which are from Twisted client service, you can find their detail here: https://twistedmatrix.com/documents/current/api/twisted.application.internet.ClientService.html 

### Sending Message

To send a message you have to first create the proto message, ex:

```python
# Import all message types
from ctrader_open_api.messages.OpenApiCommonMessages_pb2 import *
from ctrader_open_api.messages.OpenApiCommonMessages_pb2 import *
from ctrader_open_api.messages.OpenApiMessages_pb2 import *
from ctrader_open_api.messages.OpenApiModelMessages_pb2 import *

# ProtoOAApplicationAuthReq message
applicationAuthReq = ProtoOAApplicationAuthReq()
applicationAuthReq.clientId = "Your App Client ID"
applicationAuthReq.clientSecret = "Your App Client secret"

```

After you created the message and populated its fields, you can send it by using Client send method:

```python
deferred = client.send(applicationAuthReq)
```

The client send method returns a Twisted deferred, it will be called when the message response arrived, the callback result will be the response proto message.

If the message send failed, the returned deferred error callback will be called, to handle both cases you can attach two callbacks for getting response or error:

```python
def onProtoOAApplicationAuthRes(result):
	print(result)

def onError(failure):
	print(failure)

deferred.addCallbacks(onProtoOAApplicationAuthRes, onError)
```
For more about Twisted deferreds please check their documentation: https://docs.twistedmatrix.com/en/twisted-16.2.0/core/howto/defer-intro.html

### Canceling Message

You can cancel a message by calling the returned deferred from Client send method Cancel method.

If the message is not sent yet, it will be removed from the messages queue and the deferred Errback method will be called with CancelledError.

If the message is already sent but the response is not received yet, then you will not receive the response and the deferred Errback method will be called with CancelledError.

If the message is already sent and the reponse is received then canceling it's deferred will not have any effect.

### Other Callbacks

The client class has some other optional general purpose callbacks that you can use:

* ConnectedCallback(client): This callback will be called when client gets connected, use client setConnectedCallback method to assign a callback for it

* DisconnectedCallback(client, reason): This callback will be called when client gets disconnected, use client setDisconnectedCallback method to assign a callback for it

* MessageReceivedCallback(client, message): This callback will be called when a message is received, it's called for all message types, use setMessageReceivedCallback to assign a callback for it
````

## File: docs/index.md
````markdown
### Introduction

A Python package for interacting with cTrader Open API.

This package is developed and maintained by Spotware.

You can use OpenApiPy on all kinds of Python apps, it uses Twisted to send and receive messages asynchronously.

Github Repository: https://github.com/spotware/OpenApiPy

### Installation

You can install OpenApiPy from pip:

```
pip install ctrader-open-api
```

### Usage

```python

from ctrader_open_api import Client, Protobuf, TcpProtocol, Auth, EndPoints
from ctrader_open_api.messages.OpenApiCommonMessages_pb2 import *
from ctrader_open_api.messages.OpenApiCommonMessages_pb2 import *
from ctrader_open_api.messages.OpenApiMessages_pb2 import *
from ctrader_open_api.messages.OpenApiModelMessages_pb2 import *
from twisted.internet import reactor

hostType = input("Host (Live/Demo): ")
host = EndPoints.PROTOBUF_LIVE_HOST if hostType.lower() == "live" else EndPoints.PROTOBUF_DEMO_HOST
client = Client(host, EndPoints.PROTOBUF_PORT, TcpProtocol)

def onError(failure): # Call back for errors
    print("Message Error: ", failure)

def connected(client): # Callback for client connection
    print("\nConnected")
    # Now we send a ProtoOAApplicationAuthReq
    request = ProtoOAApplicationAuthReq()
    request.clientId = "Your application Client ID"
    request.clientSecret = "Your application Client secret"
    # Client send method returns a Twisted deferred
    deferred = client.send(request)
    # You can use the returned Twisted deferred to attach callbacks
    # for getting message response or error backs for getting error if something went wrong
    # deferred.addCallbacks(onProtoOAApplicationAuthRes, onError)
    deferred.addErrback(onError)

def disconnected(client, reason): # Callback for client disconnection
    print("\nDisconnected: ", reason)

def onMessageReceived(client, message): # Callback for receiving all messages
    print("Message received: \n", Protobuf.extract(message))

# Setting optional client callbacks
client.setConnectedCallback(connected)
client.setDisconnectedCallback(disconnected)
client.setMessageReceivedCallback(onMessageReceived)
# Starting the client service
client.startService()
# Run Twisted reactor
reactor.run()

```
````

## File: overrides/main.html
````html
{% extends "base.html" %}

{% block content %}
{{ super() }}

<!-- Giscus -->
<h2 id="__comments">{{ lang.t("meta.comments") }}</h2>
<!-- Replace with generated snippet -->

<script src="https://giscus.app/client.js"
        data-repo="spotware/OpenApiPy"
        data-repo-id="R_kgDOGZc_9A"
        data-category="Announcements"
        data-category-id="DIC_kwDOGZc_9M4CAPRV"
        data-mapping="pathname"
        data-reactions-enabled="1"
        data-emit-metadata="0"
        data-input-position="top"
        data-theme="light"
        data-lang="en"
        crossorigin="anonymous"
        async>
</script>

<!-- Reload on palette change -->
<script>
    var palette = __md_get("__palette")
    if (palette && typeof palette.color === "object")
        if (palette.color.scheme === "slate") {
            var giscus = document.querySelector("script[src*=giscus]")
            giscus.setAttribute("data-theme", "dark")
        }

    /* Register event handlers after documented loaded */
    document.addEventListener("DOMContentLoaded", function () {
        var ref = document.querySelector("[data-md-component=palette]")
        ref.addEventListener("change", function () {
            var palette = __md_get("__palette")
            if (palette && typeof palette.color === "object") {
                var theme = palette.color.scheme === "slate" ? "dark_dimmed" : "light"

                /* Instruct Giscus to change theme */
                var frame = document.querySelector(".giscus-frame")
                frame.contentWindow.postMessage(
                    { giscus: { setConfig: { theme } } },
                    "https://giscus.app"
                )
            }
        })
    })
</script>
{% endblock %}
````

## File: samples/ConsoleSample/main.py
````python
#!/usr/bin/env python

from ctrader_open_api import Client, Protobuf, TcpProtocol, Auth, EndPoints
from ctrader_open_api.endpoints import EndPoints
from ctrader_open_api.messages.OpenApiCommonMessages_pb2 import *
from ctrader_open_api.messages.OpenApiMessages_pb2 import *
from ctrader_open_api.messages.OpenApiModelMessages_pb2 import *
from twisted.internet import reactor
from inputimeout import inputimeout, TimeoutOccurred
import webbrowser
import datetime
import calendar

if __name__ == "__main__":
    currentAccountId = None
    hostType = input("Host (Live/Demo): ")
    hostType = hostType.lower()

    while hostType != "live" and  hostType != "demo":
        print(f"{hostType} is not a valid host type.")
        hostType = input("Host (Live/Demo): ")

    appClientId = input("App Client ID: ")
    appClientSecret = input("App Client Secret: ")
    isTokenAvailable = input("Do you have an access token? (Y/N): ").lower() == "y"

    accessToken = None
    if isTokenAvailable == False:
        appRedirectUri = input("App Redirect URI: ")
        auth = Auth(appClientId, appClientSecret, appRedirectUri)
        authUri = auth.getAuthUri()
        print(f"Please continue the authentication on your browser:\n {authUri}")
        webbrowser.open_new(authUri)
        print("\nThen enter the auth code that is appended to redirect URI immediatly (the code is after ?code= in URI)")
        authCode = input("Auth Code: ")
        token = auth.getToken(authCode)
        if "accessToken" not in token:
            raise KeyError(token)
        print("Token: \n", token)
        accessToken = token["accessToken"]
    else:
        accessToken = input("Access Token: ")

    client = Client(EndPoints.PROTOBUF_LIVE_HOST if hostType.lower() == "live" else EndPoints.PROTOBUF_DEMO_HOST, EndPoints.PROTOBUF_PORT, TcpProtocol)

    def connected(client): # Callback for client connection
        print("\nConnected")
        request = ProtoOAApplicationAuthReq()
        request.clientId = appClientId
        request.clientSecret = appClientSecret
        deferred = client.send(request)
        deferred.addErrback(onError)

    def disconnected(client, reason): # Callback for client disconnection
        print("\nDisconnected: ", reason)

    def onMessageReceived(client, message): # Callback for receiving all messages
        if message.payloadType in [ProtoOASubscribeSpotsRes().payloadType, ProtoOAAccountLogoutRes().payloadType, ProtoHeartbeatEvent().payloadType]:
            return
        elif message.payloadType == ProtoOAApplicationAuthRes().payloadType:
            print("API Application authorized\n")
            print("Please use setAccount command to set the authorized account before sending any other command, try help for more detail\n")
            print("To get account IDs use ProtoOAGetAccountListByAccessTokenReq command")
            if currentAccountId is not None:
                sendProtoOAAccountAuthReq()
                return
        elif message.payloadType == ProtoOAAccountAuthRes().payloadType:
            protoOAAccountAuthRes = Protobuf.extract(message)
            print(f"Account {protoOAAccountAuthRes.ctidTraderAccountId} has been authorized\n")
            print("This acccount will be used for all future requests\n")
            print("You can change the account by using setAccount command")
        else:
            print("Message received: \n", Protobuf.extract(message))
        reactor.callLater(3, callable=executeUserCommand)

    def onError(failure): # Call back for errors
        print("Message Error: ", failure)
        reactor.callLater(3, callable=executeUserCommand)

    def showHelp():
        print("Commands (Parameters with an * are required), ignore the description inside ()")
        print("setAccount(For all subsequent requests this account will be used) *accountId")
        print("ProtoOAVersionReq clientMsgId")
        print("ProtoOAGetAccountListByAccessTokenReq clientMsgId")
        print("ProtoOAAssetListReq clientMsgId")
        print("ProtoOAAssetClassListReq clientMsgId")
        print("ProtoOASymbolCategoryListReq clientMsgId")
        print("ProtoOASymbolsListReq includeArchivedSymbols(True/False) clientMsgId")
        print("ProtoOATraderReq clientMsgId")
        print("ProtoOASubscribeSpotsReq *symbolId *timeInSeconds(Unsubscribes after this time) subscribeToSpotTimestamp(True/False) clientMsgId")
        print("ProtoOAReconcileReq clientMsgId")
        print("ProtoOAGetTrendbarsReq *weeks *period *symbolId clientMsgId")
        print("ProtoOAGetTickDataReq *days *type *symbolId clientMsgId")
        print("NewMarketOrder *symbolId *tradeSide *volume clientMsgId")
        print("NewLimitOrder *symbolId *tradeSide *volume *price clientMsgId")
        print("NewStopOrder *symbolId *tradeSide *volume *price clientMsgId")
        print("ClosePosition *positionId *volume clientMsgId")
        print("CancelOrder *orderId clientMsgId")
        print("DealOffsetList *dealId clientMsgId")
        print("GetPositionUnrealizedPnL clientMsgId")
        print("OrderDetails clientMsgId")
        print("OrderListByPositionId *positionId fromTimestamp toTimestamp clientMsgId")

        reactor.callLater(3, callable=executeUserCommand)

    def setAccount(accountId):
        global currentAccountId
        if currentAccountId is not None:
            sendProtoOAAccountLogoutReq()
        currentAccountId = int(accountId)
        sendProtoOAAccountAuthReq()

    def sendProtoOAVersionReq(clientMsgId = None):
        request = ProtoOAVersionReq()
        deferred = client.send(request, clientMsgId = clientMsgId)
        deferred.addErrback(onError)

    def sendProtoOAGetAccountListByAccessTokenReq(clientMsgId = None):
        request = ProtoOAGetAccountListByAccessTokenReq()
        request.accessToken = accessToken
        deferred = client.send(request, clientMsgId = clientMsgId)
        deferred.addErrback(onError)

    def sendProtoOAAccountLogoutReq(clientMsgId = None):
        request = ProtoOAAccountLogoutReq()
        request.ctidTraderAccountId = currentAccountId
        deferred = client.send(request, clientMsgId = clientMsgId)
        deferred.addErrback(onError)

    def sendProtoOAAccountAuthReq(clientMsgId = None):
        request = ProtoOAAccountAuthReq()
        request.ctidTraderAccountId = currentAccountId
        request.accessToken = accessToken
        deferred = client.send(request, clientMsgId = clientMsgId)
        deferred.addErrback(onError)

    def sendProtoOAAssetListReq(clientMsgId = None):
        request = ProtoOAAssetListReq()
        request.ctidTraderAccountId = currentAccountId
        deferred = client.send(request, clientMsgId = clientMsgId)
        deferred.addErrback(onError)

    def sendProtoOAAssetClassListReq(clientMsgId = None):
        request = ProtoOAAssetClassListReq()
        request.ctidTraderAccountId = currentAccountId
        deferred = client.send(request, clientMsgId = clientMsgId)
        deferred.addErrback(onError)

    def sendProtoOASymbolCategoryListReq(clientMsgId = None):
        request = ProtoOASymbolCategoryListReq()
        request.ctidTraderAccountId = currentAccountId
        deferred = client.send(request, clientMsgId = clientMsgId)
        deferred.addErrback(onError)

    def sendProtoOASymbolsListReq(includeArchivedSymbols = False, clientMsgId = None):
        request = ProtoOASymbolsListReq()
        request.ctidTraderAccountId = currentAccountId
        request.includeArchivedSymbols = includeArchivedSymbols if type(includeArchivedSymbols) is bool else bool(includeArchivedSymbols)
        deferred = client.send(request)
        deferred.addErrback(onError)

    def sendProtoOATraderReq(clientMsgId = None):
        request = ProtoOATraderReq()
        request.ctidTraderAccountId = currentAccountId
        deferred = client.send(request, clientMsgId = clientMsgId)
        deferred.addErrback(onError)

    def sendProtoOAUnsubscribeSpotsReq(symbolId, clientMsgId = None):
        request = ProtoOAUnsubscribeSpotsReq()
        request.ctidTraderAccountId = currentAccountId
        request.symbolId.append(int(symbolId))
        deferred = client.send(request, clientMsgId = clientMsgId)
        deferred.addErrback(onError)

    def sendProtoOASubscribeSpotsReq(symbolId, timeInSeconds, subscribeToSpotTimestamp	= False, clientMsgId = None):
        request = ProtoOASubscribeSpotsReq()
        request.ctidTraderAccountId = currentAccountId
        request.symbolId.append(int(symbolId))
        request.subscribeToSpotTimestamp = subscribeToSpotTimestamp if type(subscribeToSpotTimestamp) is bool else bool(subscribeToSpotTimestamp)
        deferred = client.send(request, clientMsgId = clientMsgId)
        deferred.addErrback(onError)
        reactor.callLater(int(timeInSeconds), sendProtoOAUnsubscribeSpotsReq, symbolId)

    def sendProtoOAReconcileReq(clientMsgId = None):
        request = ProtoOAReconcileReq()
        request.ctidTraderAccountId = currentAccountId
        deferred = client.send(request, clientMsgId = clientMsgId)
        deferred.addErrback(onError)

    def sendProtoOAGetTrendbarsReq(weeks, period, symbolId, clientMsgId = None):
        request = ProtoOAGetTrendbarsReq()
        request.ctidTraderAccountId = currentAccountId
        request.period = ProtoOATrendbarPeriod.Value(period)
        request.fromTimestamp = int(calendar.timegm((datetime.datetime.utcnow() - datetime.timedelta(weeks=int(weeks))).utctimetuple())) * 1000
        request.toTimestamp = int(calendar.timegm(datetime.datetime.utcnow().utctimetuple())) * 1000
        request.symbolId = int(symbolId)
        deferred = client.send(request, clientMsgId = clientMsgId)
        deferred.addErrback(onError)

    def sendProtoOAGetTickDataReq(days, quoteType, symbolId, clientMsgId = None):
        request = ProtoOAGetTickDataReq()
        request.ctidTraderAccountId = currentAccountId
        request.type = ProtoOAQuoteType.Value(quoteType.upper())
        request.fromTimestamp = int(calendar.timegm((datetime.datetime.utcnow() - datetime.timedelta(days=int(days))).utctimetuple())) * 1000
        request.toTimestamp = int(calendar.timegm(datetime.datetime.utcnow().utctimetuple())) * 1000
        request.symbolId = int(symbolId)
        deferred = client.send(request, clientMsgId = clientMsgId)
        deferred.addErrback(onError)

    def sendProtoOANewOrderReq(symbolId, orderType, tradeSide, volume, price = None, clientMsgId = None):
        request = ProtoOANewOrderReq()
        request.ctidTraderAccountId = currentAccountId
        request.symbolId = int(symbolId)
        request.orderType = ProtoOAOrderType.Value(orderType.upper())
        request.tradeSide = ProtoOATradeSide.Value(tradeSide.upper())
        request.volume = int(volume) * 100
        if request.orderType == ProtoOAOrderType.LIMIT:
            request.limitPrice = float(price)
        elif request.orderType == ProtoOAOrderType.STOP:
            request.stopPrice = float(price)
        deferred = client.send(request, clientMsgId = clientMsgId)
        deferred.addErrback(onError)

    def sendNewMarketOrder(symbolId, tradeSide, volume, clientMsgId = None):
        sendProtoOANewOrderReq(symbolId, "MARKET", tradeSide, volume, clientMsgId = clientMsgId)

    def sendNewLimitOrder(symbolId, tradeSide, volume, price, clientMsgId = None):
        sendProtoOANewOrderReq(symbolId, "LIMIT", tradeSide, volume, price, clientMsgId)

    def sendNewStopOrder(symbolId, tradeSide, volume, price, clientMsgId = None):
        sendProtoOANewOrderReq(symbolId, "STOP", tradeSide, volume, price, clientMsgId)

    def sendProtoOAClosePositionReq(positionId, volume, clientMsgId = None):
        request = ProtoOAClosePositionReq()
        request.ctidTraderAccountId = currentAccountId
        request.positionId = int(positionId)
        request.volume = int(volume) * 100
        deferred = client.send(request, clientMsgId = clientMsgId)
        deferred.addErrback(onError)

    def sendProtoOACancelOrderReq(orderId, clientMsgId = None):
        request = ProtoOACancelOrderReq()
        request.ctidTraderAccountId = currentAccountId
        request.orderId = int(orderId)
        deferred = client.send(request, clientMsgId = clientMsgId)
        deferred.addErrback(onError)

    def sendProtoOADealOffsetListReq(dealId, clientMsgId=None):
        request = ProtoOADealOffsetListReq()
        request.ctidTraderAccountId = currentAccountId
        request.dealId = int(dealId)
        deferred = client.send(request, clientMsgId=clientMsgId)
        deferred.addErrback(onError)

    def sendProtoOAGetPositionUnrealizedPnLReq(clientMsgId=None):
        request = ProtoOAGetPositionUnrealizedPnLReq()
        request.ctidTraderAccountId = currentAccountId
        deferred = client.send(request, clientMsgId=clientMsgId)
        deferred.addErrback(onError)

    def sendProtoOAOrderDetailsReq(orderId, clientMsgId=None):
        request = ProtoOAOrderDetailsReq()
        request.ctidTraderAccountId = currentAccountId
        request.orderId = int(orderId)
        deferred = client.send(request, clientMsgId=clientMsgId)
        deferred.addErrback(onError)

    def sendProtoOAOrderListByPositionIdReq(positionId, fromTimestamp=None, toTimestamp=None, clientMsgId=None):
        request = ProtoOAOrderListByPositionIdReq()
        request.ctidTraderAccountId = currentAccountId
        request.positionId = int(positionId)
        deferred = client.send(request, fromTimestamp=fromTimestamp, toTimestamp=toTimestamp, clientMsgId=clientMsgId)
        deferred.addErrback(onError)

    commands = {
        "help": showHelp,
        "setAccount": setAccount,
        "ProtoOAVersionReq": sendProtoOAVersionReq,
        "ProtoOAGetAccountListByAccessTokenReq": sendProtoOAGetAccountListByAccessTokenReq,
        "ProtoOAAssetListReq": sendProtoOAAssetListReq,
        "ProtoOAAssetClassListReq": sendProtoOAAssetClassListReq,
        "ProtoOASymbolCategoryListReq": sendProtoOASymbolCategoryListReq,
        "ProtoOASymbolsListReq": sendProtoOASymbolsListReq,
        "ProtoOATraderReq": sendProtoOATraderReq,
        "ProtoOASubscribeSpotsReq": sendProtoOASubscribeSpotsReq,
        "ProtoOAReconcileReq": sendProtoOAReconcileReq,
        "ProtoOAGetTrendbarsReq": sendProtoOAGetTrendbarsReq,
        "ProtoOAGetTickDataReq": sendProtoOAGetTickDataReq,
        "NewMarketOrder": sendNewMarketOrder,
        "NewLimitOrder": sendNewLimitOrder,
        "NewStopOrder": sendNewStopOrder,
        "ClosePosition": sendProtoOAClosePositionReq,
        "CancelOrder": sendProtoOACancelOrderReq,
        "DealOffsetList": sendProtoOADealOffsetListReq,
        "GetPositionUnrealizedPnL": sendProtoOAGetPositionUnrealizedPnLReq,
        "OrderDetails": sendProtoOAOrderDetailsReq,
        "OrderListByPositionId": sendProtoOAOrderListByPositionIdReq,
    }

    def executeUserCommand():
        try:
            print("\n")
            userInput = inputimeout("Command (ex help): ", timeout=18)
        except TimeoutOccurred:
            print("Command Input Timeout")
            reactor.callLater(3, callable=executeUserCommand)
            return
        userInputSplit = userInput.split(" ")
        if not userInputSplit:
            print("Command split error: ", userInput)
            reactor.callLater(3, callable=executeUserCommand)
            return
        command = userInputSplit[0]
        try:
            parameters = [parameter if parameter[0] != "*" else parameter[1:] for parameter in userInputSplit[1:]]
        except:
            print("Invalid parameters: ", userInput)
            reactor.callLater(3, callable=executeUserCommand)
        if command in commands:
            commands[command](*parameters)
        else:
            print("Invalid Command: ", userInput)
            reactor.callLater(3, callable=executeUserCommand)

    # Setting optional client callbacks
    client.setConnectedCallback(connected)
    client.setDisconnectedCallback(disconnected)
    client.setMessageReceivedCallback(onMessageReceived)
    # Starting the client service
    client.startService()
    reactor.run()
````

## File: samples/ConsoleSample/README.md
````markdown
# Console Sample

This is the console sample for Spotware OpenApiPy Python package.

It uses a single thread which is the Python main execution thread for both getting user inputs and sending/receiving messages to/from API.

Because it uses only the Python main execution thread the user input command has a time out, and if you don't enter your command on that specific time period it will block for few seconds and then it starts accepting user command again.

This sample uses [inputimeout](https://pypi.org/project/inputimeout/) Python package, you have to install it before running the sample.
````

## File: samples/jupyter/credentials.json
````json
{
  "ClientId": "",
  "Secret": "",
  "HostType": "demo",
  "AccessToken": "",
  "AccountId": 0
}
````

## File: samples/jupyter/main.ipynb
````
{
 "cells": [
  {
   "cell_type": "markdown",
   "id": "56f1559b",
   "metadata": {},
   "source": [
    "# OpenApiPy Jupyter Sample\n",
    "\n",
    "In this Jupyter notebook we will use the Python package \"ctrader-open-api\" to get daily trend bars data from cTrader Open API.\n",
    "\n",
    "Let's start."
   ]
  },
  {
   "cell_type": "markdown",
   "id": "cca68e74",
   "metadata": {},
   "source": [
    "If you haven't already installed the \"ctrader-open-api\" package, run the next code cell to install it via pip:"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "id": "c53bfd78",
   "metadata": {},
   "outputs": [],
   "source": [
    "!pip install ctrader-open-api"
   ]
  },
  {
   "cell_type": "markdown",
   "id": "ca2b39c1",
   "metadata": {},
   "source": [
    "Then we have to import all necessary types:"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "id": "4ab2a19d",
   "metadata": {},
   "outputs": [],
   "source": [
    "from ctrader_open_api import Client, Protobuf, TcpProtocol, Auth, EndPoints\n",
    "from ctrader_open_api.messages.OpenApiCommonMessages_pb2 import *\n",
    "from ctrader_open_api.messages.OpenApiMessages_pb2 import *\n",
    "from ctrader_open_api.messages.OpenApiModelMessages_pb2 import *\n",
    "from twisted.internet import reactor\n",
    "import json\n",
    "import datetime\n",
    "import calendar"
   ]
  },
  {
   "cell_type": "markdown",
   "id": "d91f78fe",
   "metadata": {},
   "source": [
    "Now we use the \"credentials-dev.json\" file to get your Open API application credentials.\n",
    "Be sure to populate it with your API application credentials and access token before running next cell:"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "id": "2e67ade6",
   "metadata": {},
   "outputs": [],
   "source": [
    "credentialsFile = open(\"credentials-dev.json\")\n",
    "credentials = json.load(credentialsFile)"
   ]
  },
  {
   "cell_type": "markdown",
   "id": "f40aa449",
   "metadata": {},
   "source": [
    "Then we will create a client based our selected host type:"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "id": "a81eaee2",
   "metadata": {},
   "outputs": [],
   "source": [
    "host = EndPoints.PROTOBUF_LIVE_HOST if credentials[\"HostType\"].lower() == \"live\" else EndPoints.PROTOBUF_DEMO_HOST\n",
    "client = Client(host, EndPoints.PROTOBUF_PORT, TcpProtocol)"
   ]
  },
  {
   "cell_type": "markdown",
   "id": "9e722b92",
   "metadata": {},
   "source": [
    "Now let's set the symbol name that you want to use, it must match to one of your trading account symbol names:"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "id": "8718a36a",
   "metadata": {},
   "outputs": [],
   "source": [
    "symbolName = \"EURUSD\""
   ]
  },
  {
   "cell_type": "markdown",
   "id": "60d68c75",
   "metadata": {},
   "source": [
    "We will use the below list to store the daily bars data:"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "id": "cae2d042",
   "metadata": {},
   "outputs": [],
   "source": [
    "dailyBars = []"
   ]
  },
  {
   "cell_type": "markdown",
   "id": "dce5fdcd",
   "metadata": {},
   "source": [
    "We will use below method to transform the Open API trend bar to a tuple with bar open time, open price, high price, low price, and close price:"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "id": "1735a39c",
   "metadata": {},
   "outputs": [],
   "source": [
    "def transformTrendbar(trendbar):\n",
    "    openTime = datetime.datetime.fromtimestamp(trendbar.utcTimestampInMinutes * 60, datetime.timezone.utc)\n",
    "    openPrice = (trendbar.low + trendbar.deltaOpen) / 100000.0\n",
    "    highPrice = (trendbar.low + trendbar.deltaHigh) / 100000.0\n",
    "    lowPrice = trendbar.low / 100000.0\n",
    "    closePrice = (trendbar.low + trendbar.deltaClose) / 100000.0\n",
    "    return [openTime, openPrice, highPrice, lowPrice, closePrice, trendbar.volume]"
   ]
  },
  {
   "cell_type": "markdown",
   "id": "52058cf3",
   "metadata": {},
   "source": [
    "OpenApiPy uses Twisted to work asynchronously, so the execution flow is not sequential, we have to use a series of callbacks.\n",
    "\n",
    "The first callback we will use is the client \"Connected\" callback, its got triggered when client is connected and we should use it to send the Application authentication request.\n",
    "\n",
    "We will then use the Application authentication request returned Twisted deferred to set response callbacks, when we received the \"ProtoOAApplicationAuthRes\" the deferred assigned callback chain will be triggered.\n",
    "\n",
    "After we authenticated our API application then we will send an account authentication response, for the account ID you set on credentials file.\n",
    "\n",
    "Be sure your account type and host type match, otherwise account authentication will fail.\n",
    "\n",
    "Then we continue by using the retuned deferred to get trend bars data."
   ]
  },
  {
   "cell_type": "markdown",
   "id": "cc492670",
   "metadata": {},
   "source": [
    "Now lets set the client callbacks:"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "id": "a41a6f36",
   "metadata": {},
   "outputs": [],
   "source": [
    "def trendbarsResponseCallback(result):\n",
    "    print(\"\\nTrendbars received\")\n",
    "    trendbars = Protobuf.extract(result)\n",
    "    barsData = list(map(transformTrendbar, trendbars.trendbar))\n",
    "    global dailyBars\n",
    "    dailyBars.clear()\n",
    "    dailyBars.extend(barsData)\n",
    "    print(\"\\ndailyBars length:\", len(dailyBars))\n",
    "    print(\"\\Stopping reactor...\")\n",
    "    reactor.stop()\n",
    "    \n",
    "def symbolsResponseCallback(result):\n",
    "    print(\"\\nSymbols received\")\n",
    "    symbols = Protobuf.extract(result)\n",
    "    global symbolName\n",
    "    symbolsFilterResult = list(filter(lambda symbol: symbol.symbolName == symbolName, symbols.symbol))\n",
    "    if len(symbolsFilterResult) == 0:\n",
    "        raise Exception(f\"There is symbol that matches to your defined symbol name: {symbolName}\")\n",
    "    elif len(symbolsFilterResult) > 1:\n",
    "        raise Exception(f\"More than one symbol matched with your defined symbol name: {symbolName}, match result: {symbolsFilterResult}\")\n",
    "    symbol = symbolsFilterResult[0]\n",
    "    request = ProtoOAGetTrendbarsReq()\n",
    "    request.symbolId = symbol.symbolId\n",
    "    request.ctidTraderAccountId = credentials[\"AccountId\"]\n",
    "    request.period = ProtoOATrendbarPeriod.D1\n",
    "    # We set the from/to time stamps to 50 weeks, you can load more data by sending multiple requests\n",
    "    # Please check the ProtoOAGetTrendbarsReq documentation for more detail\n",
    "    request.fromTimestamp = int(calendar.timegm((datetime.datetime.utcnow() - datetime.timedelta(weeks=50)).utctimetuple())) * 1000\n",
    "    request.toTimestamp = int(calendar.timegm(datetime.datetime.utcnow().utctimetuple())) * 1000\n",
    "    deferred = client.send(request)\n",
    "    deferred.addCallbacks(trendbarsResponseCallback, onError)\n",
    "    \n",
    "def accountAuthResponseCallback(result):\n",
    "    print(\"\\nAccount authenticated\")\n",
    "    request = ProtoOASymbolsListReq()\n",
    "    request.ctidTraderAccountId = credentials[\"AccountId\"]\n",
    "    request.includeArchivedSymbols = False\n",
    "    deferred = client.send(request)\n",
    "    deferred.addCallbacks(symbolsResponseCallback, onError)\n",
    "    \n",
    "def applicationAuthResponseCallback(result):\n",
    "    print(\"\\nApplication authenticated\")\n",
    "    request = ProtoOAAccountAuthReq()\n",
    "    request.ctidTraderAccountId = credentials[\"AccountId\"]\n",
    "    request.accessToken = credentials[\"AccessToken\"]\n",
    "    deferred = client.send(request)\n",
    "    deferred.addCallbacks(accountAuthResponseCallback, onError)\n",
    "\n",
    "def onError(client, failure): # Call back for errors\n",
    "    print(\"\\nMessage Error: \", failure)\n",
    "\n",
    "def disconnected(client, reason): # Callback for client disconnection\n",
    "    print(\"\\nDisconnected: \", reason)\n",
    "\n",
    "def onMessageReceived(client, message): # Callback for receiving all messages\n",
    "    if message.payloadType in [ProtoHeartbeatEvent().payloadType, ProtoOAAccountAuthRes().payloadType, ProtoOAApplicationAuthRes().payloadType, ProtoOASymbolsListRes().payloadType, ProtoOAGetTrendbarsRes().payloadType]:\n",
    "        return\n",
    "    print(\"\\nMessage received: \\n\", Protobuf.extract(message))\n",
    "    \n",
    "def connected(client): # Callback for client connection\n",
    "    print(\"\\nConnected\")\n",
    "    request = ProtoOAApplicationAuthReq()\n",
    "    request.clientId = credentials[\"ClientId\"]\n",
    "    request.clientSecret = credentials[\"Secret\"]\n",
    "    deferred = client.send(request)\n",
    "    deferred.addCallbacks(applicationAuthResponseCallback, onError)\n",
    "    \n",
    "# Setting optional client callbacks\n",
    "client.setConnectedCallback(connected)\n",
    "client.setDisconnectedCallback(disconnected)\n",
    "client.setMessageReceivedCallback(onMessageReceived)"
   ]
  },
  {
   "cell_type": "markdown",
   "id": "fbcde03f",
   "metadata": {},
   "source": [
    "The last step is to run our client service, it will run inside Twisted reactor loop asynchronously:"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "id": "98c9510e",
   "metadata": {},
   "outputs": [],
   "source": [
    "# Starting the client service\n",
    "client.startService()\n",
    "# Run Twisted reactor, we imported it earlier\n",
    "reactor.run()"
   ]
  },
  {
   "cell_type": "markdown",
   "id": "c8e4a97b",
   "metadata": {},
   "source": [
    "If the above cell code executed without any error and the daily bars length printed as last message with more than 0 elements then it means we were able to successfully get the daily trend bars data."
   ]
  },
  {
   "cell_type": "markdown",
   "id": "a7835d65",
   "metadata": {},
   "source": [
    "Now we have the price data, let's do some cool stuff with it, we will transform it to a pandas DataFrame:"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "id": "5a75f17c",
   "metadata": {},
   "outputs": [],
   "source": [
    "import pandas as pd\n",
    "import numpy as np"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "id": "6f6bdcd7",
   "metadata": {},
   "outputs": [],
   "source": [
    "df = pd.DataFrame(np.array(dailyBars),\n",
    "                   columns=['Time', 'Open', 'High', 'Low', 'Close', 'Volume'])\n",
    "df[\"Open\"] = pd.to_numeric(df[\"Open\"])\n",
    "df[\"High\"] = pd.to_numeric(df[\"High\"])\n",
    "df[\"Low\"] = pd.to_numeric(df[\"Low\"])\n",
    "df[\"Close\"] = pd.to_numeric(df[\"Close\"])\n",
    "df[\"Volume\"] = pd.to_numeric(df[\"Volume\"])"
   ]
  },
  {
   "cell_type": "markdown",
   "id": "63eda941",
   "metadata": {},
   "source": [
    "Now let's create a labels series, we will use it later for our ML model.\n",
    "This will have a 1 if the close price was higher than open price and 0 otherwise.\n",
    "We will use the today price data to predict the tomorrow bar type."
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "id": "02856070",
   "metadata": {},
   "outputs": [],
   "source": [
    "df[\"Labels\"] = (df[\"Close\"] > df[\"Open\"]).astype(int)\n",
    "df[\"Labels\"] = df[\"Labels\"].shift(-1)\n",
    "df.drop(df.tail(1).index,inplace=True)"
   ]
  },
  {
   "cell_type": "markdown",
   "id": "46ad4ae2",
   "metadata": {},
   "source": [
    "Let's take a look on our data frame: "
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "id": "cb75ff4f",
   "metadata": {},
   "outputs": [],
   "source": [
    "df.tail()"
   ]
  },
  {
   "cell_type": "markdown",
   "id": "5d5ce793",
   "metadata": {},
   "source": [
    "Now let's create a sklearn LogisticRegression model and use our data to train and test it:"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "id": "fc9f1fe5",
   "metadata": {},
   "outputs": [],
   "source": [
    "from sklearn.linear_model import LogisticRegression\n",
    "from sklearn.model_selection import train_test_split\n",
    "from sklearn.metrics import accuracy_score\n",
    "\n",
    "model = LogisticRegression()\n",
    "\n",
    "x = df.loc[:, [\"Open\", \"High\", \"Low\", \"Close\", \"Volume\"]]\n",
    "y = df.Labels\n",
    "\n",
    "x_train, x_test, y_train, y_test = train_test_split(x, y, train_size=0.7)\n",
    "\n",
    "model.fit(x_train, y_train)\n",
    "\n",
    "y_pred= model.predict(x_test)\n",
    "\n",
    "print(\"Our Model accuracy score is: \", accuracy_score(y_test, y_pred))"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "id": "75402129",
   "metadata": {},
   "outputs": [],
   "source": []
  }
 ],
 "metadata": {
  "kernelspec": {
   "display_name": "Python 3 (ipykernel)",
   "language": "python",
   "name": "python3"
  },
  "language_info": {
   "codemirror_mode": {
    "name": "ipython",
    "version": 3
   },
   "file_extension": ".py",
   "mimetype": "text/x-python",
   "name": "python",
   "nbconvert_exporter": "python",
   "pygments_lexer": "ipython3",
   "version": "3.9.6"
  }
 },
 "nbformat": 4,
 "nbformat_minor": 5
}
````

## File: samples/jupyter/README.md
````markdown
# Jupyter Sample

This is sample that will show you how to use the OpenApiPy Python package on a Jupyter notebook.

In the notebook we get the daily bars data from cTrader Open API, then we use it to train a sklearn model.

To use the sample you have to create a copy of "credentials.json" file and rename it to "credentials-dev.json".

Then fill the file with your Open API application credentials, access token, and a trading account ID.
````

## File: samples/KleinWebAppSample/css/site.css
````css

````

## File: samples/KleinWebAppSample/js/site.js
````javascript
$(document).ready(function () {
    const queryString = window.location.search;
    const urlParams = new URLSearchParams(queryString);
    const token = urlParams.get("token");

    $("#sendButton").click(function () {
        $.getJSON(`/get-data?token=${token}&command=${$('#commandInput').val()}`, function (data, status, xhr) {
            response = "result" in data ? data["result"] : JSON.stringify(data)
            if ($("#outputTextarea").val() == "") {
                $("#outputTextarea").val(response + "\n").change()
            }
            else {
                $("#outputTextarea").val($("#outputTextarea").val() + "\n" + response + "\n").change()
            }
        });
    });
});
````

## File: samples/KleinWebAppSample/markup/add_accounts.xml
````xml
<!DOCTYPE html>
<html lang="en" xmlns:t="http://twistedmatrix.com/ns/twisted.web.template/0.1">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />

  <title>Open API Web App Sample</title>

  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.0.1/dist/css/bootstrap.min.css" />
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.3/css/all.min.css" />
  <link rel="stylesheet" href="/css/site.css" asp-append-version="true" />

  <script src="https://cdn.jsdelivr.net/npm/jquery@3.6.0/dist/jquery.min.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.0.1/dist/js/bootstrap.bundle.min.js"></script>
  <script src="/js/site.js"></script>
</head>
<body class="container-fluid bg-dark">
  <div tabindex="-1" role="dialog">
    <div class="modal-dialog" role="document">
      <div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title">Authentication</h5>
        </div>
        <div class="modal-body">
          <p>Please click on Add Trading Account(s) button</p>
        </div>
        <div class="modal-footer">
          <a class="btn btn-primary" t:render="addAccountButton">
            <t:attr name="href">
              <t:slot name="addAccountLink" />
            </t:attr>
            Add Trading Account(s)</a>
        </div>
      </div>
    </div>
  </div>
</body>
</html>
````

## File: samples/KleinWebAppSample/markup/client_area.xml
````xml
<!DOCTYPE html>
<html lang="en" xmlns:t="http://twistedmatrix.com/ns/twisted.web.template/0.1">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />

  <title>Open API Web App Sample</title>

  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.0.1/dist/css/bootstrap.min.css" />
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.3/css/all.min.css" />
  <link rel="stylesheet" href="/css/site.css" />

  <script src="https://cdn.jsdelivr.net/npm/jquery@3.6.0/dist/jquery.min.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.0.1/dist/js/bootstrap.bundle.min.js"></script>
  <script src="/js/site.js"></script>
</head>
<body class="container-fluid bg-dark text-white">
	<div class="row">
		<div class="col">
			<div class="row form-group mt-1">
				<div class="col-11">
					<input type="text" class="form-control" id="commandInput" placeholder="Command" />
				</div>
				<div class="col">
					<button type="button" class="btn btn-primary" id="sendButton">Send</button>
				</div>
			</div>
			<div class="row form-group mt-1">
				<div class="col">
					<textarea class="form-control" type="submit" id="outputTextarea" style="height: 92vh;"></textarea>
				</div>
			</div>
		</div>
		<div class="col mt-1">
			<h1 class="text-center">
				Welcome to cTrader Open API Pyhton Web App Sample
			</h1>
			<p>This is a sample web app built based on Twisted Klein framework.</p>
			<p>You can send Open API commands and receive back the responses from API.</p>
			<p>Commands (Parameters with an * are required):</p>
			<ul>
				<li>
					ProtoOAVersionReq: Returns the API server version
				</li>
				<li>
					setAccount *accountId: For all subsequent requests this account will be used
				</li>
				<li>
					ProtoOAGetAccountListByAccessTokenReq: Returns the list of authorized accounts for the token
				</li>
				<li>
					ProtoOAAssetListReq: Returns the list of account assets list
				</li>
				<li>
					ProtoOAAssetClassListReq: Returns the list of account asset classes
				</li>
				<li>
					ProtoOASymbolCategoryListReq: Returns the list of account symbol categories
				</li>
				<li>
					ProtoOASymbolsListReq: Returns the list of account symbols
				</li>
				<li>
					ProtoOATraderReq: Returns the token trader profile
				</li>
				<li>
					ProtoOAReconcileReq: Returns the account open positions/orders
				</li>
				<li>
					ProtoOAGetTrendbarsReq *weeks *period *symbolId: Returns the trend bar data of a symbol
				</li>
				<li>
					ProtoOAGetTickDataReq *days *type *symbolId: Returns the tick data of a symbol
				</li>
				<li>
					NewMarketOrder *symbolId *tradeSide *volume: Creates a new market order
				</li>
				<li>
					NewLimitOrder *symbolId *tradeSide *volume *price: Creates a new limit order
				</li>
				<li>
					NewStopOrder *symbolId *tradeSide *volume *price: Creates a new stop order
				</li>
				<li>
					ClosePosition *positionId *volume: Closes a position x amount of volume
				</li>
				<li>
					CancelOrder *orderId: Cancels a pending order
				</li>
			</ul>
		</div>
	</div>
</body>
</html>
````

## File: samples/KleinWebAppSample/credentials.json
````json
{
  "ClientId": "",
  "Secret": "",
  "Host":  "demo"
}
````

## File: samples/KleinWebAppSample/main.py
````python
#!/usr/bin/env python

from klein import Klein
from ctrader_open_api import Client, Protobuf, TcpProtocol, Auth, EndPoints
from ctrader_open_api.endpoints import EndPoints
from ctrader_open_api.messages.OpenApiCommonMessages_pb2 import *
from ctrader_open_api.messages.OpenApiMessages_pb2 import *
from ctrader_open_api.messages.OpenApiModelMessages_pb2 import *
from templates import AddAccountsElement, ClientAreaElement
import json
from twisted.internet import endpoints, reactor
from twisted.web.server import Site
import sys
from twisted.python import log
from twisted.web.static import File
import datetime
from google.protobuf.json_format import MessageToJson
import calendar

host = "localhost"
port = 8080

credentialsFile = open("credentials-dev.json")
credentials = json.load(credentialsFile)
token = ""
currentAccountId = None

auth = Auth(credentials["ClientId"], credentials["Secret"], f"http://{host}:{port}/redirect")
authUri = auth.getAuthUri()
app = Klein()

@app.route('/')
def root(request):
    return AddAccountsElement(authUri)

@app.route('/redirect')
def redirect(request):
    authCode = request.args.get(b"code", [None])[0]
    if (authCode is not None and authCode != b""):
        token = auth.getToken(authCode)
        if "errorCode" in token and token["errorCode"] is not None:
            return f'Error: {token["description"]}'
        else:
            return request.redirect(f'/client-area?token={token["access_token"]}')
    else:
        return "Error: Invalid/Empty Auth Code"

@app.route('/client-area')
def clientArea(request):
    global token
    token = request.args.get(b"token", [None])[0]
    if (token is None or token == b""):
        return "Error: Invalid/Empty Token"
    return ClientAreaElement()

@app.route('/css/', branch=True)
def css(request):
    return File("./css")

@app.route('/js/', branch=True)
def js(request):
    return File("./js")

def onError(failure):
    print("Message Error: \n", failure)

def connected(client):
    print("Client Connected")
    request = ProtoOAApplicationAuthReq()
    request.clientId = credentials["ClientId"]
    request.clientSecret = credentials["Secret"]
    deferred = client.send(request)
    deferred.addErrback(onError)

def disconnected(client, reason):
    print("Client Disconnected, reason: \n", reason)

def onMessageReceived(client, message):
    if message.payloadType == ProtoHeartbeatEvent().payloadType:
        return
    print("Client Received a Message: \n", message)

authorizedAccounts = []

def setAccount(accountId):
    global currentAccountId
    currentAccountId = int(accountId)
    if accountId not in authorizedAccounts:
        return sendProtoOAAccountAuthReq(accountId)
    return "Account changed successfully"

def sendProtoOAVersionReq(clientMsgId = None):
    request = ProtoOAVersionReq()
    deferred = client.send(request, clientMsgId = clientMsgId)
    deferred.addErrback(onError)
    return deferred

def sendProtoOAGetAccountListByAccessTokenReq(clientMsgId = None):
    request = ProtoOAGetAccountListByAccessTokenReq()
    request.accessToken = token
    deferred = client.send(request, clientMsgId = clientMsgId)
    deferred.addErrback(onError)
    return deferred

def sendProtoOAAccountLogoutReq(clientMsgId = None):
    request = ProtoOAAccountLogoutReq()
    request.ctidTraderAccountId = currentAccountId
    deferred = client.send(request, clientMsgId = clientMsgId)
    deferred.addErrback(onError)
    return deferred

def sendProtoOAAccountAuthReq(clientMsgId = None):
    request = ProtoOAAccountAuthReq()
    request.ctidTraderAccountId = currentAccountId
    request.accessToken = token
    deferred = client.send(request, clientMsgId = clientMsgId)
    deferred.addErrback(onError)
    return deferred

def sendProtoOAAssetListReq(clientMsgId = None):
    request = ProtoOAAssetListReq()
    request.ctidTraderAccountId = currentAccountId
    deferred = client.send(request, clientMsgId = clientMsgId)
    deferred.addErrback(onError)
    return deferred

def sendProtoOAAssetClassListReq(clientMsgId = None):
    request = ProtoOAAssetClassListReq()
    request.ctidTraderAccountId = currentAccountId
    deferred = client.send(request, clientMsgId = clientMsgId)
    deferred.addErrback(onError)
    return deferred

def sendProtoOASymbolCategoryListReq(clientMsgId = None):
    request = ProtoOASymbolCategoryListReq()
    request.ctidTraderAccountId = currentAccountId
    deferred = client.send(request, clientMsgId = clientMsgId)
    deferred.addErrback(onError)
    return deferred

def sendProtoOASymbolsListReq(includeArchivedSymbols = False, clientMsgId = None):
    request = ProtoOASymbolsListReq()
    request.ctidTraderAccountId = currentAccountId
    request.includeArchivedSymbols = includeArchivedSymbols if type(includeArchivedSymbols) is bool else bool(includeArchivedSymbols)
    deferred = client.send(request)
    deferred.addErrback(onError)
    return deferred

def sendProtoOATraderReq(clientMsgId = None):
    request = ProtoOATraderReq()
    request.ctidTraderAccountId = currentAccountId
    deferred = client.send(request, clientMsgId = clientMsgId)
    deferred.addErrback(onError)
    return deferred

def sendProtoOAUnsubscribeSpotsReq(symbolId, clientMsgId = None):
    request = ProtoOAUnsubscribeSpotsReq()
    request.ctidTraderAccountId = currentAccountId
    request.symbolId.append(int(symbolId))
    deferred = client.send(request, clientMsgId = clientMsgId)
    deferred.addErrback(onError)
    return deferred

def sendProtoOAReconcileReq(clientMsgId = None):
    request = ProtoOAReconcileReq()
    request.ctidTraderAccountId = currentAccountId
    deferred = client.send(request, clientMsgId = clientMsgId)
    deferred.addErrback(onError)
    return deferred

def sendProtoOAGetTrendbarsReq(weeks, period, symbolId, clientMsgId = None):
    request = ProtoOAGetTrendbarsReq()
    request.ctidTraderAccountId = currentAccountId
    request.period = ProtoOATrendbarPeriod.Value(period)
    request.fromTimestamp = int(calendar.timegm((datetime.datetime.utcnow() - datetime.timedelta(weeks=int(weeks))).utctimetuple())) * 1000
    request.toTimestamp = int(calendar.timegm(datetime.datetime.utcnow().utctimetuple())) * 1000
    request.symbolId = int(symbolId)
    deferred = client.send(request, clientMsgId = clientMsgId)
    deferred.addErrback(onError)
    return deferred

def sendProtoOAGetTickDataReq(days, quoteType, symbolId, clientMsgId = None):
    request = ProtoOAGetTickDataReq()
    request.ctidTraderAccountId = currentAccountId
    request.type = ProtoOAQuoteType.Value(quoteType.upper())
    request.fromTimestamp = int(calendar.timegm((datetime.datetime.utcnow() - datetime.timedelta(days=int(days))).utctimetuple())) * 1000
    request.toTimestamp = int(calendar.timegm(datetime.datetime.utcnow().utctimetuple())) * 1000
    request.symbolId = int(symbolId)
    deferred = client.send(request, clientMsgId = clientMsgId)
    deferred.addErrback(onError)
    return deferred

def sendProtoOANewOrderReq(symbolId, orderType, tradeSide, volume, price = None, clientMsgId = None):
    request = ProtoOANewOrderReq()
    request.ctidTraderAccountId = currentAccountId
    request.symbolId = int(symbolId)
    request.orderType = ProtoOAOrderType.Value(orderType.upper())
    request.tradeSide = ProtoOATradeSide.Value(tradeSide.upper())
    request.volume = int(volume) * 100
    if request.orderType == ProtoOAOrderType.LIMIT:
        request.limitPrice = float(price)
    elif request.orderType == ProtoOAOrderType.STOP:
        request.stopPrice = float(price)
    deferred = client.send(request, clientMsgId = clientMsgId)
    deferred.addErrback(onError)
    return deferred

def sendNewMarketOrder(symbolId, tradeSide, volume, clientMsgId = None):
    return sendProtoOANewOrderReq(symbolId, "MARKET", tradeSide, volume, clientMsgId = clientMsgId)

def sendNewLimitOrder(symbolId, tradeSide, volume, price, clientMsgId = None):
    return sendProtoOANewOrderReq(symbolId, "LIMIT", tradeSide, volume, price, clientMsgId)

def sendNewStopOrder(symbolId, tradeSide, volume, price, clientMsgId = None):
    return sendProtoOANewOrderReq(symbolId, "STOP", tradeSide, volume, price, clientMsgId)

def sendProtoOAClosePositionReq(positionId, volume, clientMsgId = None):
    request = ProtoOAClosePositionReq()
    request.ctidTraderAccountId = currentAccountId
    request.positionId = int(positionId)
    request.volume = int(volume) * 100
    deferred = client.send(request, clientMsgId = clientMsgId)
    deferred.addErrback(onError)
    return deferred

def sendProtoOACancelOrderReq(orderId, clientMsgId = None):
    request = ProtoOACancelOrderReq()
    request.ctidTraderAccountId = currentAccountId
    request.orderId = int(orderId)
    deferred = client.send(request, clientMsgId = clientMsgId)
    deferred.addErrback(onError)
    return deferred

def sendProtoOADealOffsetListReq(dealId, clientMsgId=None):
    request = ProtoOADealOffsetListReq()
    request.ctidTraderAccountId = currentAccountId
    request.dealId = int(dealId)
    deferred = client.send(request, clientMsgId=clientMsgId)
    deferred.addErrback(onError)

def sendProtoOAGetPositionUnrealizedPnLReq(clientMsgId=None):
    request = ProtoOAGetPositionUnrealizedPnLReq()
    request.ctidTraderAccountId = currentAccountId
    deferred = client.send(request, clientMsgId=clientMsgId)
    deferred.addErrback(onError)

def sendProtoOAOrderDetailsReq(orderId, clientMsgId=None):
    request = ProtoOAOrderDetailsReq()
    request.ctidTraderAccountId = currentAccountId
    request.orderId = int(orderId)
    deferred = client.send(request, clientMsgId=clientMsgId)
    deferred.addErrback(onError)

def sendProtoOAOrderListByPositionIdReq(positionId, fromTimestamp=None, toTimestamp=None, clientMsgId=None):
    request = ProtoOAOrderListByPositionIdReq()
    request.ctidTraderAccountId = currentAccountId
    request.positionId = int(positionId)
    deferred = client.send(request, fromTimestamp=fromTimestamp, toTimestamp=toTimestamp, clientMsgId=clientMsgId)
    deferred.addErrback(onError)

commands = {
    "setAccount": setAccount,
    "ProtoOAVersionReq": sendProtoOAVersionReq,
    "ProtoOAGetAccountListByAccessTokenReq": sendProtoOAGetAccountListByAccessTokenReq,
    "ProtoOAAssetListReq": sendProtoOAAssetListReq,
    "ProtoOAAssetClassListReq": sendProtoOAAssetClassListReq,
    "ProtoOASymbolCategoryListReq": sendProtoOASymbolCategoryListReq,
    "ProtoOASymbolsListReq": sendProtoOASymbolsListReq,
    "ProtoOATraderReq": sendProtoOATraderReq,
    "ProtoOAReconcileReq": sendProtoOAReconcileReq,
    "ProtoOAGetTrendbarsReq": sendProtoOAGetTrendbarsReq,
    "ProtoOAGetTickDataReq": sendProtoOAGetTickDataReq,
    "NewMarketOrder": sendNewMarketOrder,
    "NewLimitOrder": sendNewLimitOrder,
    "NewStopOrder": sendNewStopOrder,
    "ClosePosition": sendProtoOAClosePositionReq,
    "CancelOrder": sendProtoOACancelOrderReq,
    "DealOffsetList": sendProtoOADealOffsetListReq,
    "GetPositionUnrealizedPnL": sendProtoOAGetPositionUnrealizedPnLReq,
    "OrderDetails": sendProtoOAOrderDetailsReq,
    "OrderListByPositionId": sendProtoOAOrderListByPositionIdReq,
}

def encodeResult(result):
    if type(result) is str:
        return f'{{"result": "{result}"}}'.encode(encoding = 'UTF-8')
    else:
        return MessageToJson(Protobuf.extract(result)).encode(encoding = 'UTF-8')

@app.route('/get-data')
def getData(request):
    request.responseHeaders.addRawHeader(b"content-type", b"application/json")
    token = request.args.get(b"token", [None])[0]
    result = ""
    if (token is None or token == b""):
        result = "Invalid Token"
    command = request.args.get(b"command", [None])[0]
    if (command is None or command == b""):
        result = f"Invalid Command: {command}"
    commandSplit = command.decode('UTF-8').split(" ")
    print(commandSplit)
    if (commandSplit[0] not in commands):
        result = f"Invalid Command: {commandSplit[0]}"
    else:
        parameters = commandSplit[1:]
        print(parameters)
        result = commands[commandSplit[0]](*parameters)
        result.addCallback(encodeResult)
    if type(result) is str:
        result = encodeResult(result)
    print(result)
    return result

log.startLogging(sys.stdout)

client = Client(EndPoints.PROTOBUF_LIVE_HOST if credentials["Host"].lower() == "live" else EndPoints.PROTOBUF_DEMO_HOST, EndPoints.PROTOBUF_PORT, TcpProtocol)
client.setConnectedCallback(connected)
client.setDisconnectedCallback(disconnected)
client.setMessageReceivedCallback(onMessageReceived)
client.startService()

endpoint_description = f"tcp6:port={port}:interface={host}"
endpoint = endpoints.serverFromString(reactor, endpoint_description)
site = Site(app.resource())
site.displayTracebacks = True

endpoint.listen(site)
reactor.run()
````

## File: samples/KleinWebAppSample/README.md
````markdown
# Klein Web App Sample

This is the web sample for Spotware OpenApiPy Python package.

It's based on Twisted [Klein](https://github.com/twisted/klein) web framework.

You can send and receive API commands by using this sample, it's very similar to Console sample.

To use the sample you have to create a copy of "credentials.json" file and rename it to "credentials-dev.json".

Then fill the file with your Open API application credentials.

After that install Klein with pip:
```
pip install klein
```

Then run the "main.py" file.

Open the "localhost:8080" on your web browser.

You can escape the account authentication if you have already an access token, go to: "localhost:8080/client-area?token=your-access-token"

![Screenshot](screenshot.png)
````

## File: samples/KleinWebAppSample/templates.py
````python
from twisted.web.template import Element, renderer, XMLFile
from twisted.python.filepath import FilePath

class AddAccountsElement(Element):
    loader = XMLFile(FilePath('./markup/add_accounts.xml'))

    def __init__(self, addAccountLink):
        self.addAccountLink = addAccountLink
        super().__init__()

    @renderer
    def addAccountButton(self, request, tag):
        tag.fillSlots(addAccountLink=self.addAccountLink)
        return tag

class ClientAreaElement(Element):
    loader = XMLFile(FilePath('./markup/client_area.xml'))
````

## File: .editorconfig
````
# http://editorconfig.org

root = true

[*]
charset = utf-8
end_of_line = lf
insert_final_newline = true
trim_trailing_whitespace = true

[*.{py,rst,ini}]
indent_style = space
indent_size = 4

[*.{html,css,scss,json,yml}]
indent_style = space
indent_size = 2

[*.md]
trim_trailing_whitespace = false
````

## File: .gitignore
````
# Byte-compiled / optimized / DLL files
__pycache__/
*.py[cod]
*$py.class

# C extensions
*.so

# Distribution / packaging
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
pip-wheel-metadata/
share/python-wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# PyInstaller
#  Usually these files are written by a python script from a template
#  before PyInstaller builds the exe, so as to inject date/other infos into it.
*.manifest
*.spec

# Installer logs
pip-log.txt
pip-delete-this-directory.txt

# Unit test / coverage reports
htmlcov/
.tox/
.nox/
.coverage
.coverage.*
.cache
nosetests.xml
coverage.xml
*.cover
*.py,cover
.hypothesis/
.pytest_cache/

# Translations
*.mo
*.pot

# Django stuff:
*.log
local_settings.py
db.sqlite3
db.sqlite3-journal

# Flask stuff:
instance/
.webassets-cache

# Scrapy stuff:
.scrapy

# Sphinx documentation
docs/_build/

# PyBuilder
target/

# Jupyter Notebook
.ipynb_checkpoints

# IPython
profile_default/
ipython_config.py

# pyenv
.python-version

# pipenv
#   According to pypa/pipenv#598, it is recommended to include Pipfile.lock in version control.
#   However, in case of collaboration, if having platform-specific dependencies or dependencies
#   having no cross-platform support, pipenv may install dependencies that don't work, or not
#   install all needed dependencies.
#Pipfile.lock

# PEP 582; used by e.g. github.com/David-OConnor/pyflow
__pypackages__/

# Celery stuff
celerybeat-schedule
celerybeat.pid

# SageMath parsed files
*.sage.py

# Environments
.env
.venv
env/
venv/
ENV/
env.bak/
venv.bak/

# Spyder project settings
.spyderproject
.spyproject

# Rope project settings
.ropeproject

# mkdocs documentation
/site

# mypy
.mypy_cache/
.dmypy.json
dmypy.json

# Pyre type checker
.pyre/
/.vs
/samples/ConsoleSample/ConsoleSample-dev.py
/samples/KleinWebAppSample/credentials-dev.json
/samples/jupyter/credentials-dev.json
````

## File: AUTHORS.md
````markdown
# Credits


## Development Lead

* Spotware <connect@spotware.com>

## Contributors

None yet. Why not be the first?
````

## File: CONTRIBUTING.md
````markdown
# Contributing

Contributions are welcome, and they are greatly appreciated! Every little bit
helps, and credit will always be given.

You can contribute in many ways:

## Types of Contributions

### Report Bugs

Report bugs at https://github.com/spotware/spotware_openApiPy/issues.

If you are reporting a bug, please include:

* Your operating system name and version.
* Any details about your local setup that might be helpful in troubleshooting.
* Detailed steps to reproduce the bug.

### Fix Bugs

Look through the GitHub issues for bugs. Anything tagged with "bug" and "help
wanted" is open to whoever wants to implement it.

### Implement Features

Look through the GitHub issues for features. Anything tagged with "enhancement"
and "help wanted" is open to whoever wants to implement it.

### Write Documentation

OpenApiPy could always use more documentation, whether as part of the
official OpenApiPy docs, in docstrings, or even on the web in blog posts,
articles, and such.

### Submit Feedback

The best way to send feedback is to file an issue at https://github.com/spotware/spotware_openApiPy/issues.

If you are proposing a feature:

* Explain in detail how it would work.
* Keep the scope as narrow as possible, to make it easier to implement.
* Remember that this is a volunteer-driven project, and that contributions
  are welcome :)
````

## File: LICENSE
````
MIT License

Copyright (c) 2021, Spotware

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
````

## File: mkdocs.yml
````yaml
---
# Project Information
site_name: OpenApiPy
site_author: Spotware
site_url: https://openapinet.readthedocs.io/en/latest/
site_description: cTrader Open API Python package documentation

# Repository information
repo_name: spotware/openApiPy
repo_url: https://github.com/spotware/openApiPy
edit_uri: "https://github.com/spotware/openApiPy/tree/master/docs"

copyright: "Copyright &copy; <span id='copyright-year'></span> <a href='https://www.spotware.com/' target='_blank'>Spotware Systems Ltd.</a> cTrader, cAlgo, cBroker, cMirror. All rights reserved."

theme:
    name: material
    favicon: img/favicon.ico
    logo: img/logo.png
    include_search_page: false
    search_index_only: true
    language: en
    custom_dir: overrides
    features:
        - navigation.instant
        - navigation.top
        - navigation.tracking
        - search.highlight
        - search.share
        - search.suggest
        #- navigation.instant
        #- navigation.top
        #- navigation.tracking
        #- navigation.tabs
        #- navigation.sections
        ##- navigation.indexes
        ##- content.code.annotate
        ## - content.tabs.link
        ## - header.autohide
        ## - navigation.expand
        ## - navigation.instant
        ## - toc.integrate
    palette:
    - scheme: default
      primary: indigo
      accent: indigo
      toggle:
        icon: material/toggle-switch-off-outline
        name: Switch to dark mode
    - scheme: slate
      primary: indigo
      accent: indigo
      toggle:
        icon: material/toggle-switch
        name: Switch to light mode
    font:
        text: Roboto
        code: Roboto Mono
    static_templates:
    - 404.html

plugins:
  - search
  - minify:
      minify_html: true

extra:
  generator: false

extra_css:
  - css/extra.css
  
extra_javascript:
  - js/extra.js

markdown_extensions:
  - admonition
  - abbr
  - attr_list
  - def_list
  - footnotes
  - meta
  - md_in_html
  - toc:
      permalink: true
  - pymdownx.arithmatex:
      generic: true
  - pymdownx.betterem:
      smart_enable: all
  - pymdownx.caret
  - pymdownx.critic
  - pymdownx.details
  - pymdownx.emoji:
      emoji_index: !!python/name:materialx.emoji.twemoji
      emoji_generator: !!python/name:materialx.emoji.to_svg
  - pymdownx.highlight
  - pymdownx.inlinehilite
  - pymdownx.keys
  - pymdownx.magiclink:
      repo_url_shorthand: true
      user: squidfunk
      repo: mkdocs-material
  - pymdownx.mark
  - pymdownx.smartsymbols
  - pymdownx.superfences:
      custom_fences:
        - name: mermaid
          class: mermaid
          format: !!python/name:pymdownx.superfences.fence_code_format
  - pymdownx.tasklist:
      custom_checkbox: true
  - pymdownx.tilde
  - pymdownx.tabbed:
      alternate_style: true 

# Page tree
nav:
    - Getting Started: index.md
    - Authentication: 'authentication.md' 
    - Client: 'client.md'
    - Samples: "https://github.com/spotware/OpenApiPy/tree/main/samples"
````

## File: poetry.toml
````toml
[virtualenvs]
in-project = true
[repositories]
[repositories.testpypi]
url = "https://test.pypi.org/legacy/"
````

## File: pyproject.toml
````toml
[tool]

[tool.poetry]
name = "ctrader_open_api"
version = "0.0.0"
homepage = "https://github.com/spotware/openApiPy"
description = "A Python package for interacting with cTrader Open API"
authors = ["Spotware <connect@spotware.com>"]
documentation = "https://spotware.github.io/OpenApiPy"
readme = "README.md"
license =  "MIT"
classifiers=[
    'License :: OSI Approved :: MIT License',
    'Natural Language :: English',
    'Programming Language :: Python :: 3.8',
]
include = [
    "LICENSE"
]

[tool.poetry.dependencies]
python = "^3.8"
Twisted = "24.3.0"
pyOpenSSL = "24.1.0"
protobuf = "3.20.1"
requests = "2.32.3"
inputimeout = "1.0.4"

[tool.poetry.dev-dependencies]
Twisted = "24.3.0"
pyOpenSSL = "24.1.0"
protobuf = "3.20.1"
requests = "2.32.3"
inputimeout = "1.0.4"

[tool.black]
line-length=100

[tool.pylint.reports]
output-format="colorized"
reports="y"
include-ids="yes"
msg-template="{msg_id}:{line:3d},{column}: {obj}: {msg}"

[tool.pytest.ini_options]
addopts = "--cov=ctrader_openApiPy --cov-branch --cov-report term-missing  -vv --color=yes --cov-fail-under 100"
python_files = "tests.py test_*.py *_tests.py"

[build-system]
requires = ["poetry-core>=1.0.8"]
build-backend = "poetry.core.masonry.api"
````

## File: README.md
````markdown
# OpenApiPy


[![PyPI version](https://badge.fury.io/py/ctrader-open-api.svg)](https://badge.fury.io/py/ctrader-open-api)
![versions](https://img.shields.io/pypi/pyversions/ctrader-open-api.svg)
[![GitHub license](https://img.shields.io/github/license/spotware/OpenApiPy.svg)](https://github.com/spotware/OpenApiPy/blob/main/LICENSE)

A Python package for interacting with cTrader Open API.

This package uses Twisted and it works asynchronously.

- Free software: MIT
- Documentation: https://spotware.github.io/OpenApiPy/.


## Features

* Works asynchronously by using Twisted

* Methods return Twisted deferreds

* It contains the Open API messages files so you don't have to do the compilation

* Makes handling request responses easy by using Twisted deferreds

## Insallation

```
pip install ctrader-open-api
```

# Usage

```python

from ctrader_open_api import Client, Protobuf, TcpProtocol, Auth, EndPoints
from ctrader_open_api.messages.OpenApiCommonMessages_pb2 import *
from ctrader_open_api.messages.OpenApiCommonMessages_pb2 import *
from ctrader_open_api.messages.OpenApiMessages_pb2 import *
from ctrader_open_api.messages.OpenApiModelMessages_pb2 import *
from twisted.internet import reactor

hostType = input("Host (Live/Demo): ")
host = EndPoints.PROTOBUF_LIVE_HOST if hostType.lower() == "live" else EndPoints.PROTOBUF_DEMO_HOST
client = Client(host, EndPoints.PROTOBUF_PORT, TcpProtocol)

def onError(failure): # Call back for errors
    print("Message Error: ", failure)

def connected(client): # Callback for client connection
    print("\nConnected")
    # Now we send a ProtoOAApplicationAuthReq
    request = ProtoOAApplicationAuthReq()
    request.clientId = "Your application Client ID"
    request.clientSecret = "Your application Client secret"
    # Client send method returns a Twisted deferred
    deferred = client.send(request)
    # You can use the returned Twisted deferred to attach callbacks
    # for getting message response or error backs for getting error if something went wrong
    # deferred.addCallbacks(onProtoOAApplicationAuthRes, onError)
    deferred.addErrback(onError)

def disconnected(client, reason): # Callback for client disconnection
    print("\nDisconnected: ", reason)

def onMessageReceived(client, message): # Callback for receiving all messages
    print("Message received: \n", Protobuf.extract(message))

# Setting optional client callbacks
client.setConnectedCallback(connected)
client.setDisconnectedCallback(disconnected)
client.setMessageReceivedCallback(onMessageReceived)
# Starting the client service
client.startService()
# Run Twisted reactor
reactor.run()

```

Please check documentation or samples for a complete example.

## Dependencies

* <a href="https://pypi.org/project/twisted/">Twisted</a>
* <a href="https://pypi.org/project/protobuf/">Protobuf</a>
````
