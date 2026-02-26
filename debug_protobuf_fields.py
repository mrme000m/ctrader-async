#!/usr/bin/env python3
"""
Comprehensive protobuf field audit tool.
Dumps all known protobuf message fields and cross-checks them against
actual cTrader API usage in the ctc codebase.
"""
import sys
import os
import types
import importlib.util


def _load_module(path: str, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module

ROOT = os.path.dirname(__file__)
sys.modules.setdefault("ctc", types.ModuleType("ctc"))
sys.modules.setdefault("ctc.messages", types.ModuleType("ctc.messages"))

CMM = _load_module(
    os.path.join(ROOT, "src", "ctc", "messages", "OpenApiCommonModelMessages_pb2.py"),
    "ctc.messages.OpenApiCommonModelMessages_pb2",
)
CM = _load_module(
    os.path.join(ROOT, "src", "ctc", "messages", "OpenApiCommonMessages_pb2.py"),
    "ctc.messages.OpenApiCommonMessages_pb2",
)
MM = _load_module(
    os.path.join(ROOT, "src", "ctc", "messages", "OpenApiModelMessages_pb2.py"),
    "ctc.messages.OpenApiModelMessages_pb2",
)
M = _load_module(
    os.path.join(ROOT, "src", "ctc", "messages", "OpenApiMessages_pb2.py"),
    "ctc.messages.OpenApiMessages_pb2",
)


def get_fields(cls):
    try:
        obj = cls()
        return [(f.name, f.type, f.label) for f in obj.DESCRIPTOR.fields]
    except Exception:
        return []


def dump_all_messages():
    """Print all protobuf messages with their fields."""
    all_mods = [
        ("OpenApiMessages", M),
        ("OpenApiModelMessages", MM),
        ("OpenApiCommonMessages", CM),
        ("OpenApiCommonModelMessages", CMM),
    ]

    print("=" * 80)
    print("COMPLETE PROTOBUF MESSAGE FIELD REFERENCE")
    print("=" * 80)

    for mod_name, mod in all_mods:
        print(f"\n{'='*60}")
        print(f"Module: {mod_name}")
        print(f"{'='*60}")
        for name in sorted(dir(mod)):
            cls = getattr(mod, name)
            try:
                if hasattr(cls, 'DESCRIPTOR') and hasattr(cls.DESCRIPTOR, 'fields'):
                    fields = get_fields(cls)
                    if fields:
                        field_names = [f[0] for f in fields]
                        print(f"  {name}: {field_names}")
            except Exception:
                pass


def check_key_messages():
    """Check specifically the messages we use in ctc."""
    print("\n" + "=" * 80)
    print("KEY MESSAGE FIELD VERIFICATION")
    print("=" * 80)

    checks = [
        # Trading
        ("ProtoOATrader", MM, ["ctidTraderAccountId", "balance", "moneyDigits",
                               "leverageInCents", "totalMarginCalculationType"]),
        ("ProtoOAPosition", MM, ["positionId", "tradeData", "positionStatus", "swap",
                                  "commission", "price", "stopLoss", "takeProfit",
                                  "usedMargin", "moneyDigits", "utcLastUpdateTimestamp"]),
        ("ProtoOAOrder", MM, ["orderId", "tradeData", "orderType", "orderStatus",
                               "limitPrice", "stopPrice", "stopLoss", "takeProfit",
                               "executionPrice", "clientOrderId", "closingOrder",
                               "isStopOut", "positionId", "expirationTimestamp",
                               "utcLastUpdateTimestamp"]),
        ("ProtoOADeal", MM, ["dealId", "orderId", "positionId", "symbolId",
                              "volume", "filledVolume", "executionPrice", "tradeSide",
                              "dealStatus", "commission", "moneyDigits",
                              "createTimestamp", "executionTimestamp",
                              "closePositionDetail"]),
        ("ProtoOAClosePositionDetail", MM, ["entryPrice", "grossProfit", "swap",
                                             "commission", "balance", "closedVolume",
                                             "moneyDigits", "quoteToDepositConversionRate",
                                             "pnlConversionFee"]),
        ("ProtoOATradeData", MM, ["symbolId", "volume", "tradeSide", "openTimestamp",
                                   "label", "guaranteedStopLoss", "comment"]),

        # Symbols
        ("ProtoOALightSymbol", MM, ["symbolId", "symbolName", "enabled", "baseAssetId",
                                     "quoteAssetId", "symbolCategoryId", "description"]),
        ("ProtoOASymbol", MM, ["symbolId", "digits", "pipPosition", "enableShortSelling",
                                "guaranteedStopLoss", "swapLong", "swapShort",
                                "stepVolume", "minVolume", "maxVolume", "lotSize",
                                "leverageId"]),
        ("ProtoOAAsset", MM, ["assetId", "name", "displayName", "digits"]),
        ("ProtoOAAssetClass", MM, ["id", "name"]),

        # Market data
        ("ProtoOATrendbar", MM, ["volume", "period", "low", "deltaOpen",
                                  "deltaClose", "deltaHigh", "utcTimestampInMinutes"]),
        ("ProtoOATickData", MM, ["timestamp", "tick"]),
        ("ProtoOASpotEvent", M, ["ctidTraderAccountId", "symbolId", "bid", "ask",
                                  "trendbar", "sessionClose", "timestamp"]),
        ("ProtoOADepthQuote", MM, ["id", "size", "bid", "ask"]),
        ("ProtoOADepthEvent", M, ["ctidTraderAccountId", "symbolId",
                                   "newQuotes", "deletedQuotes"]),

        # Dynamic leverage
        ("ProtoOADynamicLeverage", MM, ["leverageId", "tiers"]),
        ("ProtoOADynamicLeverageTier", MM, ["volume", "leverage"]),

        # Account / cash flow
        ("ProtoOADepositWithdraw", MM, ["operationType", "balanceHistoryId", "balance",
                                         "delta", "changeBalanceTimestamp",
                                         "externalNote", "balanceVersion", "equity",
                                         "moneyDigits"]),
        ("ProtoOABonusDepositWithdraw", MM, ["operationType", "bonusHistoryId",
                                              "managerBonus", "managerDelta",
                                              "ibBonus", "ibDelta",
                                              "changeBonusTimestamp"]),

        # Risk
        ("ProtoOAMarginCall", MM, ["marginCallType", "marginLevelThreshold",
                                    "utcLastUpdateTimestamp"]),
        ("ProtoOAExpectedMargin", MM, ["volume", "buyMargin", "sellMargin"]),
        ("ProtoOAPositionUnrealizedPnL", MM, ["positionId", "grossUnrealizedPnL",
                                               "netUnrealizedPnL"]),

        # Requests
        ("ProtoOAGetTrendbarsReq", M, ["ctidTraderAccountId", "fromTimestamp",
                                        "toTimestamp", "period", "symbolId", "count"]),
        ("ProtoOAGetTickDataReq", M, ["ctidTraderAccountId", "symbolId", "type",
                                       "fromTimestamp", "toTimestamp"]),
        ("ProtoOADealListReq", M, ["ctidTraderAccountId", "fromTimestamp",
                                    "toTimestamp", "maxRows"]),
        ("ProtoOAOrderListReq", M, ["ctidTraderAccountId", "fromTimestamp",
                                     "toTimestamp"]),
        ("ProtoOACashFlowHistoryListReq", M, ["ctidTraderAccountId",
                                               "fromTimestamp", "toTimestamp"]),
        ("ProtoOAGetDynamicLeverageByIDReq", M, ["ctidTraderAccountId", "leverageId"]),
        ("ProtoOAExpectedMarginReq", M, ["ctidTraderAccountId", "symbolId", "volume"]),
        ("ProtoOAGetPositionUnrealizedPnLReq", M, ["ctidTraderAccountId"]),
        ("ProtoOAMarginCallListReq", M, ["ctidTraderAccountId"]),
        ("ProtoOASubscribeDepthQuotesReq", M, ["ctidTraderAccountId", "symbolId"]),
        ("ProtoOAOrderListByPositionIdReq", M, ["ctidTraderAccountId", "positionId",
                                                  "fromTimestamp", "toTimestamp"]),
        ("ProtoOADealListByPositionIdReq", M, ["ctidTraderAccountId", "positionId",
                                                "fromTimestamp", "toTimestamp"]),
        ("ProtoOADealOffsetListReq", M, ["ctidTraderAccountId", "dealId"]),
        ("ProtoOAReconcileReq", M, ["ctidTraderAccountId"]),
        ("ProtoOASubscribeSpotsReq", M, ["ctidTraderAccountId", "symbolId",
                                          "subscribeToSpotTimestamp"]),
    ]

    all_ok = True
    for msg_name, mod, expected_fields in checks:
        cls = getattr(mod, msg_name, None)
        if cls is None:
            print(f"  ❌ {msg_name}: NOT FOUND IN MODULE")
            all_ok = False
            continue

        actual_fields = [f.name for f in cls().DESCRIPTOR.fields]
        missing = [f for f in expected_fields if f not in actual_fields]
        extra = [f for f in actual_fields if f not in expected_fields and f != 'payloadType']

        if missing:
            print(f"  ❌ {msg_name}: MISSING fields {missing}")
            print(f"     Actual: {actual_fields}")
            all_ok = False
        else:
            unexpected_note = f" (also has: {extra})" if extra else ""
            print(f"  ✅ {msg_name}: OK{unexpected_note}")

    print()
    if all_ok:
        print("✅ ALL KEY MESSAGE FIELDS VERIFIED CORRECTLY")
    else:
        print("⚠️  SOME FIELDS NEED ATTENTION (see above)")

    return all_ok


def check_enum_names():
    """Verify enum values used in the codebase."""
    print("\n" + "=" * 80)
    print("ENUM VALUE VERIFICATION")
    print("=" * 80)

    enums_to_check = [
        ("ProtoOATradeSide", MM, ["BUY", "SELL"]),
        ("ProtoOAOrderType", MM, ["MARKET", "LIMIT", "STOP",
                                   "STOP_LOSS_TAKE_PROFIT", "MARKET_RANGE", "STOP_LIMIT"]),
        ("ProtoOAOrderStatus", MM, ["ORDER_STATUS_ACCEPTED", "ORDER_STATUS_FILLED",
                                     "ORDER_STATUS_REJECTED", "ORDER_STATUS_EXPIRED",
                                     "ORDER_STATUS_CANCELLED"]),
        ("ProtoOADealStatus", MM, ["FILLED", "PARTIALLY_FILLED", "REJECTED",
                                    "INTERNALLY_REJECTED", "ERROR", "MISSED"]),
        ("ProtoOATrendbarPeriod", MM, ["M1", "M2", "M3", "M4", "M5", "M10", "M15",
                                       "M30", "H1", "H4", "H12", "D1", "W1", "MN1"]),
        ("ProtoOAQuoteType", MM, ["ASK", "BID"]),
        ("ProtoOAChangeBalanceType", MM, ["BALANCE_DEPOSIT", "BALANCE_WITHDRAW"]),
        # marginCallType field uses ProtoOANotificationType enum
        ("ProtoOANotificationType", MM, ["MARGIN_LEVEL_THRESHOLD_1",
                                          "MARGIN_LEVEL_THRESHOLD_2",
                                          "MARGIN_LEVEL_THRESHOLD_3"]),
    ]

    for enum_name, mod, expected_values in enums_to_check:
        enum_cls = getattr(mod, enum_name, None)
        if enum_cls is None:
            print(f"  ❌ {enum_name}: NOT FOUND")
            continue
        try:
            descriptor = enum_cls.DESCRIPTOR
            actual_values = [v.name for v in descriptor.values]
            missing = [v for v in expected_values if v not in actual_values]
            if missing:
                print(f"  ⚠️  {enum_name}: missing values {missing}")
                print(f"     Actual: {actual_values}")
            else:
                print(f"  ✅ {enum_name}: {actual_values}")
        except Exception as e:
            print(f"  ❌ {enum_name}: ERROR {e}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Protobuf field audit")
    parser.add_argument("--dump-all", action="store_true",
                        help="Dump all messages and fields")
    parser.add_argument("--check", action="store_true", default=True,
                        help="Check key message fields (default)")
    args = parser.parse_args()

    if args.dump_all:
        dump_all_messages()
    else:
        check_key_messages()
        check_enum_names()
